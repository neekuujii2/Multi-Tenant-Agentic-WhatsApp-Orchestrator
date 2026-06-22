"""
Dashboard API Router.
Provides administrative endpoints for the dashboard frontend:
- Tenant listing and analytics
- Session status management (resolve, takeover)
- Thread retrieval and manual outbound replies
- Server-Sent Events (SSE) for real-time dashboard updates
- Campaign broadcast dispatching
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.db.mongo import get_db
from app.db.redis_client import get_redis
from app.db.repositories.tenant_repo import TenantRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.message_repo import MessageRepository
from app.services.whatsapp import WhatsAppService
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

tenant_repo = TenantRepository()
session_repo = SessionRepository()
message_repo = MessageRepository()


# ─── Pydantic Request Models ──────────────────────────────────────────────────

class ReplyRequest(BaseModel):
    text: str
    status: Literal["RESOLVED", "NEEDS_HUMAN"] = "RESOLVED"


class TenantUpsertRequest(BaseModel):
    tenant_id: str
    name: str
    phone_number_id: str
    access_token: str
    system_prompt: str
    media_library: dict = {}


class BroadcastRequest(BaseModel):
    template_id: str
    cohort: Literal["active_7days", "all_sessions", "resolved_only"]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/tenants")
async def list_tenants():
    """List all configured tenants (public properties only)."""
    return await tenant_repo.list_all()


@router.post("/tenants")
async def upsert_tenant(data: TenantUpsertRequest):
    """Create or update a tenant configuration."""
    tenant_doc = {
        "tenant_id": data.tenant_id,
        "name": data.name,
        "whatsapp": {
            "phone_number_id": data.phone_number_id,
            "access_token": data.access_token,
        },
        "agent": {
            "system_prompt": data.system_prompt,
            "llm_model": "claude-sonnet-4-6",
            "max_history_messages": 10,
            "temperature": 0.7,
            "supported_languages": ["en", "hi", "hinglish"],
        },
        "media_library": data.media_library,
        "campaign_templates": [
            {
                "template_id": "welcome_promo",
                "name": "Welcome Promo",
                "body": "Namaste! Hamare store par visit karne ke liye dhanyavad. Aapke liye ek special 10% discount coupon code: WELCOME10 🎁",
            },
            {
                "template_id": "product_restock",
                "name": "Product Restock Alert",
                "body": "Good news! Aapka favourite product stock mein wapas aa chuka hai. Order karne ke liye reply karein.",
            }
        ],
        "settings": {
            "auto_reply_enabled": True,
            "sentiment_threshold": -0.5,
            "typing_indicator_enabled": True,
            "business_hours": {
                "enabled": False,
                "timezone": "Asia/Kolkata",
                "open": "09:00",
                "close": "21:00",
            }
        }
    }
    success = await tenant_repo.upsert(data.tenant_id, tenant_doc)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upsert tenant configuration")
    return {"status": "success", "tenant_id": data.tenant_id}


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Retrieve full configuration details of a specific tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    # Hide sensitive access token
    if "whatsapp" in tenant and "access_token" in tenant["whatsapp"]:
        tenant["whatsapp"]["access_token"] = "••••••••"
    return tenant


@router.get("/tenants/{tenant_id}/sessions")
async def list_sessions(
    tenant_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """List sessions associated with a tenant, with optional status filtering."""
    return await session_repo.list_by_tenant(tenant_id, status=status, limit=limit)


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, limit: int = Query(100, ge=1, le=200)):
    """Retrieve the full chat history thread for a given session."""
    return await message_repo.get_thread(session_id, limit=limit)


@router.post("/sessions/{session_id}/resolve")
async def resolve_session(session_id: str):
    """Mark a session status as RESOLVED."""
    success = await session_repo.update_status(session_id, "RESOLVED", sentiment=0.0)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    # Publish status update to Redis
    try:
        redis = get_redis()
        session = await session_repo.get_by_id(session_id)
        if session:
            await redis.publish(
                f"updates:{session['tenant_id']}",
                json.dumps({
                    "event": "session_status_changed",
                    "tenant_id": session["tenant_id"],
                    "session_id": session_id,
                    "status": "RESOLVED",
                })
            )
    except Exception:
        pass

    return {"status": "success"}


@router.post("/sessions/{session_id}/takeover")
async def takeover_session(session_id: str):
    """Manually take over a session, marking it as NEEDS_HUMAN to mute the bot agent."""
    success = await session_repo.update_status(session_id, "NEEDS_HUMAN", sentiment=-1.0)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    # Publish status update to Redis
    try:
        redis = get_redis()
        session = await session_repo.get_by_id(session_id)
        if session:
            await redis.publish(
                f"updates:{session['tenant_id']}",
                json.dumps({
                    "event": "session_status_changed",
                    "tenant_id": session["tenant_id"],
                    "session_id": session_id,
                    "status": "NEEDS_HUMAN",
                })
            )
    except Exception:
        pass

    return {"status": "success"}


@router.post("/sessions/{session_id}/reply")
async def manual_reply(session_id: str, request: ReplyRequest):
    """Send a manual outbound response from an agent to the customer."""
    # 1. Retrieve session
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    tenant_id = session["tenant_id"]

    # 2. Retrieve tenant config for keys
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant config not found")

    phone_number_id = tenant["whatsapp"]["phone_number_id"]
    access_token = tenant["whatsapp"]["access_token"]

    # 3. Send message via WhatsApp Cloud API
    wa = WhatsAppService(phone_number_id, access_token)
    try:
        wa_result = await wa.send_text(session["customer_phone"], request.text)
    except Exception as e:
        log.error("manual_reply_send_failed", session_id=session_id, error=str(e))
        raise HTTPException(status_code=502, detail=f"WhatsApp API call failed: {str(e)}")

    wa_msg_id = None
    try:
        wa_msg_id = wa_result.get("messages", [{}])[0].get("id")
    except (IndexError, AttributeError):
        pass

    # 4. Save outbound message to DB
    now = datetime.utcnow()
    outbound_doc = {
        "message_id": f"msg_out_{int(now.timestamp())}",
        "session_id": session_id,
        "tenant_id": tenant_id,
        "direction": "OUTBOUND",
        "sender": "BOT",  # Marked as bot direction, sent by human agent
        "created_at": now,
        "content": {
            "type": "text",
            "text": request.text,
            "media_url": None,
            "media_mime_type": None,
            "media_filename": None,
            "caption": None,
        },
        "meta": {
            "wa_message_id": wa_msg_id,
            "wa_timestamp": str(int(now.timestamp())),
            "read_at": None,
            "delivered_at": now,
        },
        "agent_meta": {
            "node": "manual_reply",
            "llm_tokens_used": None,
            "processing_ms": 0,
            "sentiment_score": None,
            "typing_started_at": now,
            "typing_ended_at": now,
            "detected_language": "manual",
        },
    }

    await message_repo.insert(outbound_doc)

    # 5. Update session status
    await session_repo.update_status(session_id, request.status)

    # 6. Publish update to Redis Pub/Sub for frontend UI sync
    try:
        redis = get_redis()
        await redis.publish(
            f"updates:{tenant_id}",
            json.dumps({
                "event": "outbound_message",
                "tenant_id": tenant_id,
                "session_id": session_id,
                "status": request.status,
                "message": outbound_doc,
            }, default=str)
        )
    except Exception as e:
        log.warning("redis_publish_failed", error=str(e))

    return {"status": "success", "message_id": outbound_doc["message_id"]}


@router.get("/tenants/{tenant_id}/analytics")
async def get_analytics(tenant_id: str):
    """Retrieve operational dashboard metrics for the tenant using MongoDB aggregates."""
    db = await get_db()
    sessions_col = db["chat_sessions"]
    messages_col = db["messages"]

    # 1. Counts by status
    status_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_cursor = await sessions_col.aggregate(status_pipeline).to_list(10)
    status_counts = {item["_id"]: item["count"] for item in status_cursor}

    # Ensure all statuses are represented
    total_sessions = sum(status_counts.values())
    needs_human = status_counts.get("NEEDS_HUMAN", 0)
    resolved = status_counts.get("RESOLVED", 0)
    waiting_bot = status_counts.get("WAITING_FOR_BOT", 0)
    agent_responding = status_counts.get("AGENT_RESPONDING", 0)

    # 2. Messages counts by direction
    msg_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$direction", "count": {"$sum": 1}}}
    ]
    msg_cursor = await messages_col.aggregate(msg_pipeline).to_list(5)
    msg_counts = {item["_id"]: item["count"] for item in msg_cursor}

    inbound_msgs = msg_counts.get("INBOUND", 0)
    outbound_msgs = msg_counts.get("OUTBOUND", 0)
    total_messages = inbound_msgs + outbound_msgs

    # 3. Customer languages breakdown
    lang_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$context_vars.language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    lang_cursor = await sessions_col.aggregate(lang_pipeline).to_list(5)
    languages = {item["_id"] or "unknown": item["count"] for item in lang_cursor}

    # 4. Sentiment average
    sentiment_pipeline = [
        {
            "$match": {
                "tenant_id": tenant_id,
                "context_vars.sentiment_score": {"$ne": None}
            }
        },
        {"$group": {"_id": None, "avg_sentiment": {"$avg": "$context_vars.sentiment_score"}}}
    ]
    sentiment_cursor = await sessions_col.aggregate(sentiment_pipeline).to_list(1)
    avg_sentiment = sentiment_cursor[0]["avg_sentiment"] if sentiment_cursor else 0.0

    return {
        "sessions": {
            "total": total_sessions,
            "needs_human": needs_human,
            "resolved": resolved,
            "waiting_for_bot": waiting_bot,
            "agent_responding": agent_responding,
        },
        "messages": {
            "total": total_messages,
            "inbound": inbound_msgs,
            "outbound": outbound_msgs,
        },
        "languages": languages,
        "average_sentiment": round(avg_sentiment, 2),
    }


@router.post("/tenants/{tenant_id}/broadcast")
async def trigger_broadcast(
    tenant_id: str,
    request: BroadcastRequest,
    background_tasks: BackgroundTasks = None,
):
    """
    Triggers a template campaign broadcast to selected customer cohorts.
    Sends template messages via WhatsApp API in parallel.
    """
    # 1. Fetch tenant context
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant config not found")

    phone_number_id = tenant["whatsapp"]["phone_number_id"]
    access_token = tenant["whatsapp"]["access_token"]

    # Retrieve template details
    template = next((t for t in tenant.get("campaign_templates", []) if t["template_id"] == request.template_id), None)
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")

    # 2. Query target cohorts
    db = await get_db()
    sessions_col = db["chat_sessions"]

    query = {"tenant_id": tenant_id, "flags.broadcast_eligible": True}
    if request.cohort == "resolved_only":
        query["status"] = "RESOLVED"
    elif request.cohort == "active_7days":
        # Sessions active in the last 7 days
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=7)
        query["last_message_at"] = {"$gte": cutoff}

    cursor = sessions_col.find(query, {"customer_phone": 1, "session_id": 1})
    sessions = await cursor.to_list(1000)

    if not sessions:
        return {"status": "success", "sent_count": 0, "message": "No matching subscribers found"}

    # 3. Define actual broadcast task (asynchronous batch sending)
    async def dispatch_broadcast_batch():
        wa = WhatsAppService(phone_number_id, access_token)
        for s in sessions:
            phone = s["customer_phone"]
            session_id = s["session_id"]
            try:
                # Meta template message API trigger
                # For always-free / simple fallback, we send as standard text message
                wa_result = await wa.send_text(phone, template["body"])

                wa_msg_id = None
                try:
                    wa_msg_id = wa_result.get("messages", [{}])[0].get("id")
                except (IndexError, AttributeError):
                    pass

                now = datetime.utcnow()
                # Insert outbound record
                outbound_doc = {
                    "message_id": f"msg_broadcast_{int(now.timestamp())}_{phone}",
                    "session_id": session_id,
                    "tenant_id": tenant_id,
                    "direction": "OUTBOUND",
                    "sender": "BOT",
                    "created_at": now,
                    "content": {
                        "type": "text",
                        "text": template["body"],
                        "media_url": template.get("media_url"),
                        "media_mime_type": template.get("media_type"),
                        "media_filename": None,
                        "caption": None,
                    },
                    "meta": {
                        "wa_message_id": wa_msg_id,
                        "wa_timestamp": str(int(now.timestamp())),
                        "read_at": None,
                        "delivered_at": now,
                    },
                    "agent_meta": {
                        "node": "broadcast",
                        "llm_tokens_used": None,
                        "processing_ms": 0,
                        "sentiment_score": None,
                        "typing_started_at": now,
                        "typing_ended_at": now,
                        "detected_language": "en",
                    },
                }
                await message_repo.insert(outbound_doc)

                # Update session
                await session_repo.upsert(session_id, tenant_id, phone, "RESOLVED")

                # Notify dashboard
                redis = get_redis()
                await redis.publish(
                    f"updates:{tenant_id}",
                    json.dumps({
                        "event": "outbound_message",
                        "tenant_id": tenant_id,
                        "session_id": session_id,
                        "status": "RESOLVED",
                        "message": outbound_doc,
                    }, default=str)
                )
            except Exception as ex:
                log.error("broadcast_send_failed", phone=phone, error=str(ex))
            # Sleep slightly to avoid Meta rate limits (80 TPS is limit, we do a safe pace)
            await asyncio.sleep(0.05)

    if background_tasks:
        background_tasks.add_task(dispatch_broadcast_batch)
    else:
        asyncio.create_task(dispatch_broadcast_batch())

    return {"status": "success", "sent_count": len(sessions)}


@router.get("/tenants/{tenant_id}/events")
async def sse_events(tenant_id: str, request: Request):
    """
    Real-time push endpoint via Server-Sent Events (SSE).
    Subscribes to Redis Pub/Sub for the tenant's updates channel.
    """
    log.info("sse_client_connected", tenant_id=tenant_id)

    async def event_generator():
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"updates:{tenant_id}")

        try:
            while True:
                # Disconnect check
                if await request.is_disconnected():
                    log.info("sse_client_disconnected", tenant_id=tenant_id)
                    break

                # Non-blocking check for new pubsub messages
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    yield f"data: {data}\n\n"

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            log.info("sse_connection_cancelled", tenant_id=tenant_id)

        finally:
            await pubsub.unsubscribe(f"updates:{tenant_id}")
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Prevents Nginx/Cloudflare buffering SSE
        }
    )
