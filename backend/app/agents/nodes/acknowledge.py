"""
Node 1: Acknowledge
Responsibilities:
  - Guard: skip if session is NEEDS_HUMAN
  - Send read receipt to Meta (non-blocking)
  - Send typing indicator to Meta (non-blocking)
  - Upsert ChatSession with status=AGENT_RESPONDING
  - Insert inbound Message record

All I/O runs in parallel via asyncio.gather for maximum throughput.
"""
import asyncio
from datetime import datetime

from app.agents.state import AgentState
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.message_repo import MessageRepository
from app.services.whatsapp import WhatsAppService
from app.utils.logger import get_logger

log = get_logger(__name__)

session_repo = SessionRepository()
message_repo = MessageRepository()


def _build_inbound_message(state: AgentState, session_id: str) -> dict:
    """Construct the inbound message document for MongoDB."""
    now = datetime.utcnow()
    return {
        "message_id": f"msg_{state['inbound_message_id']}",
        "session_id": session_id,
        "tenant_id": state["tenant_id"],
        "direction": "INBOUND",
        "sender": state["customer_phone"],
        "created_at": now,
        "content": {
            "type": state["inbound_message_type"],
            "text": state["inbound_text"],
            "media_url": state.get("inbound_media_url"),
            "media_mime_type": state.get("inbound_media_mime_type"),
            "media_filename": None,
            "caption": None,
        },
        "meta": {
            "wa_message_id": state["inbound_message_id"],
            "wa_timestamp": None,
            "read_at": now,
            "delivered_at": None,
        },
        "agent_meta": {
            "node": "acknowledge",
            "llm_tokens_used": None,
            "processing_ms": None,
            "sentiment_score": None,
            "typing_started_at": now,
            "typing_ended_at": None,
            "detected_language": None,
        },
    }


async def acknowledge_node(state: AgentState) -> AgentState:
    """
    First node in the LangGraph pipeline.
    Sends acknowledgements to Meta and persists the inbound message.
    """
    start = datetime.utcnow()
    tenant_id = state["tenant_id"]
    customer_phone = state["customer_phone"]
    session_id = f"sess_{tenant_id}_{customer_phone}"

    # ── Guard: Skip if this session requires human intervention ───────────────
    existing = await session_repo.get_by_phone(tenant_id, customer_phone)
    if existing and existing.get("status") == "NEEDS_HUMAN":
        log.info(
            "session_needs_human_skip",
            session_id=session_id,
            tenant_id=tenant_id,
        )
        raise InterruptedError(
            f"Session {session_id} requires human intervention — skipping bot pipeline."
        )

    wa = WhatsAppService(state["phone_number_id"], state["access_token"])
    inbound_doc = _build_inbound_message(state, session_id)

    # ── Parallel I/O: all 4 operations run concurrently ──────────────────────
    results = await asyncio.gather(
        wa.send_read_receipt(state["inbound_message_id"]),
        wa.send_typing_indicator(customer_phone),
        session_repo.upsert(session_id, tenant_id, customer_phone, "AGENT_RESPONDING"),
        message_repo.insert(inbound_doc),
        return_exceptions=True,  # Don't crash if one non-critical op fails
    )

    # ── Publish real-time notification to Redis ──────────────────────────────
    try:
        from app.db.redis_client import get_redis
        import json
        redis = get_redis()
        await redis.publish(
            f"updates:{tenant_id}",
            json.dumps({
                "event": "inbound_message",
                "tenant_id": tenant_id,
                "session_id": session_id,
                "status": "AGENT_RESPONDING",
                "message": inbound_doc,
            }, default=str)
        )
    except Exception as re:
        log.warning("redis_publish_failed", error=str(re))

    elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

    log.info(
        "acknowledge_complete",
        session_id=session_id,
        tenant_id=tenant_id,
        elapsed_ms=elapsed,
        read_receipt=results[0],
        typing_sent=results[1],
    )

    return {
        **state,
        "session_id": session_id,
        "session_status": "AGENT_RESPONDING",
    }
