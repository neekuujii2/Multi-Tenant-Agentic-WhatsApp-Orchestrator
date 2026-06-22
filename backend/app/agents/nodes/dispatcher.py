"""
Node 4: Dispatcher
Responsibilities:
  - Send the LLM-generated response via Meta WhatsApp API
  - Insert outbound Message record with timing metadata
  - Update session status (RESOLVED or NEEDS_HUMAN)
  - Detect frustrated customers based on sentiment threshold
"""
from datetime import datetime

from app.agents.state import AgentState
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.message_repo import MessageRepository
from app.services.whatsapp import WhatsAppService
from app.utils.logger import get_logger

log = get_logger(__name__)

session_repo = SessionRepository()
message_repo = MessageRepository()


def _build_outbound_message(
    state: AgentState,
    wa_result: dict,
    typing_started: datetime,
    typing_ended: datetime,
) -> dict:
    """Construct the outbound message document for MongoDB."""
    wa_msg_id = None
    try:
        wa_msg_id = wa_result.get("messages", [{}])[0].get("id")
    except (IndexError, AttributeError):
        pass

    return {
        "message_id": f"msg_out_{int(typing_ended.timestamp())}",
        "session_id": state["session_id"],
        "tenant_id": state["tenant_id"],
        "direction": "OUTBOUND",
        "sender": "BOT",
        "created_at": typing_ended,
        "content": {
            "type": state["response_type"],
            "text": state.get("response_text", ""),
            "media_url": state.get("response_media_url"),
            "media_mime_type": (
                "application/pdf"
                if state["response_type"] == "document"
                else (
                    "image/jpeg" if state["response_type"] == "image" else None
                )
            ),
            "media_filename": state.get("response_media_filename"),
            "caption": None,
        },
        "meta": {
            "wa_message_id": wa_msg_id,
            "wa_timestamp": str(int(typing_ended.timestamp())),
            "read_at": None,
            "delivered_at": typing_ended,
        },
        "agent_meta": {
            "node": "dispatcher",
            "llm_tokens_used": None,  # tracked in llm_reasoning node
            "processing_ms": int(
                (typing_ended - typing_started).total_seconds() * 1000
            ),
            "sentiment_score": state.get("sentiment_score"),
            "typing_started_at": typing_started,
            "typing_ended_at": typing_ended,
            "detected_language": state.get("detected_language"),
        },
    }


async def dispatcher_node(state: AgentState) -> AgentState:
    """
    Final node in the LangGraph pipeline.
    Sends the response to the customer and updates session state.
    """
    typing_started = datetime.utcnow()
    wa = WhatsAppService(state["phone_number_id"], state["access_token"])
    customer_phone = state["customer_phone"]

    wa_result = {}

    try:
        if state["response_type"] == "text":
            wa_result = await wa.send_text(customer_phone, state["response_text"])

        elif state["response_type"] == "image":
            # Send caption text first, then the image
            if state.get("response_text"):
                await wa.send_text(customer_phone, state["response_text"])
            wa_result = await wa.send_image(
                customer_phone,
                state["response_media_url"],
            )

        elif state["response_type"] == "document":
            # Send caption text first, then the document
            if state.get("response_text"):
                await wa.send_text(customer_phone, state["response_text"])
            wa_result = await wa.send_document(
                customer_phone,
                state["response_media_url"],
                state.get("response_media_filename", "document.pdf"),
            )

    except Exception as e:
        log.error(
            "dispatcher_send_failed",
            tenant_id=state.get("tenant_id"),
            session_id=state.get("session_id"),
            response_type=state.get("response_type"),
            error=str(e),
        )
        # Attempt fallback text
        try:
            await wa.send_text(
                customer_phone,
                "Maafi chahta hoon! Thoda technical issue aa gaya. Please try again! 🙏",
            )
        except Exception:
            pass

    typing_ended = datetime.utcnow()

    # ── Determine session status based on sentiment ────────────────────────────
    sentiment = state.get("sentiment_score", 0.0) or 0.0
    threshold = state.get("sentiment_threshold", -0.5)
    new_status = "NEEDS_HUMAN" if sentiment < threshold else "RESOLVED"

    outbound_doc = _build_outbound_message(state, wa_result, typing_started, typing_ended)

    # ── Persist outbound message and update session ────────────────────────────
    import asyncio
    await asyncio.gather(
        message_repo.insert(outbound_doc),
        session_repo.update_status(
            state["session_id"],
            new_status,
            sentiment,
            state.get("detected_language"),
        ),
        return_exceptions=True,
    )

    # ── Publish real-time notification to Redis ──────────────────────────────
    try:
        from app.db.redis_client import get_redis
        import json
        redis = get_redis()
        await redis.publish(
            f"updates:{state['tenant_id']}",
            json.dumps({
                "event": "outbound_message",
                "tenant_id": state["tenant_id"],
                "session_id": state["session_id"],
                "status": new_status,
                "message": outbound_doc,
            }, default=str)
        )
    except Exception as re:
        log.warning("redis_publish_failed", error=str(re))

    elapsed = int((typing_ended - typing_started).total_seconds() * 1000)
    log.info(
        "dispatcher_complete",
        tenant_id=state.get("tenant_id"),
        session_id=state.get("session_id"),
        response_type=state.get("response_type"),
        new_status=new_status,
        sentiment_score=sentiment,
        detected_language=state.get("detected_language"),
        elapsed_ms=elapsed,
    )

    return {**state, "session_status": new_status}
