"""
Node 2: Context Retriever
Responsibilities:
  - Fetch tenant config (Redis cache → MongoDB fallback)
  - Fetch last N chat messages for history
  - Download inbound media if present (for multimodal)

Tenant fetch and history fetch run in parallel for performance.
"""
import asyncio
import json
import base64
from datetime import datetime

import httpx

from app.agents.state import AgentState
from app.db.redis_client import get_redis
from app.db.repositories.tenant_repo import TenantRepository
from app.db.repositories.message_repo import MessageRepository
from app.utils.logger import get_logger

log = get_logger(__name__)

tenant_repo = TenantRepository()
message_repo = MessageRepository()

TENANT_CACHE_TTL = 300  # 5 minutes


def _format_history_for_llm(messages: list[dict]) -> list[dict]:
    """Convert DB message docs to Anthropic messages format."""
    history = []
    for msg in messages:
        role = "user" if msg.get("direction") == "INBOUND" else "assistant"
        text = msg.get("content", {}).get("text") or ""
        if text:
            history.append({"role": role, "content": text})
    return history


async def _fetch_tenant(tenant_id: str) -> dict:
    """Fetch tenant from Redis cache or MongoDB."""
    redis = get_redis()
    cache_key = f"tenant:{tenant_id}"

    # Try Redis first (< 5ms)
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss — fetch from MongoDB (~50ms)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if tenant:
        await redis.setex(cache_key, TENANT_CACHE_TTL, json.dumps(tenant, default=str))

    return tenant or {}


async def _download_media_bytes(media_url: str, access_token: str) -> bytes | None:
    """Download media bytes for Claude Vision multimodal input."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        log.warning("media_download_failed", error=str(e), url=media_url)
        return None


async def context_retriever_node(state: AgentState) -> AgentState:
    """
    Second node in the LangGraph pipeline.
    Loads all context needed for LLM reasoning.
    """
    start = datetime.utcnow()

    # ── Parallel fetch: tenant config + chat history + media (if any) ─────────
    tasks = [
        _fetch_tenant(state["tenant_id"]),
        message_repo.get_last_n(
            state["session_id"],
            n=5,  # configurable per tenant, defaulting to 5
        ),
    ]

    # If inbound message contains media, resolve + download in parallel
    media_download_task = None
    if state.get("inbound_media_id") and state.get("inbound_media_url"):
        media_download_task = _download_media_bytes(
            state["inbound_media_url"], state["access_token"]
        )
        tasks.append(media_download_task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    tenant = results[0] if not isinstance(results[0], Exception) else {}
    history_docs = results[1] if not isinstance(results[1], Exception) else []
    media_bytes = None
    if len(results) > 2 and not isinstance(results[2], Exception):
        media_bytes = results[2]

    chat_history = _format_history_for_llm(history_docs)
    elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

    log.info(
        "context_retrieved",
        tenant_id=state["tenant_id"],
        session_id=state["session_id"],
        history_count=len(chat_history),
        media_downloaded=media_bytes is not None,
        elapsed_ms=elapsed,
    )

    return {
        **state,
        "tenant_name": tenant.get("name", ""),
        "tenant_system_prompt": tenant.get("agent", {}).get("system_prompt", ""),
        "media_library": tenant.get("media_library", {}),
        "chat_history": chat_history,
        "sentiment_threshold": tenant.get("settings", {}).get("sentiment_threshold", -0.5),
        "supported_languages": tenant.get("agent", {}).get("supported_languages", ["en"]),
        "access_token": tenant.get("whatsapp", {}).get("access_token", state["access_token"]),
        "inbound_media_bytes": media_bytes,
    }
