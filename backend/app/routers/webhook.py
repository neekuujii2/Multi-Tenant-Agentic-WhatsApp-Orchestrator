"""
Meta WhatsApp webhook router.
Handles GET for verification and POST for inbound message notifications.
Validates HMAC signature and runs the LangGraph pipeline asynchronously in the background.
"""
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, Query, Response, BackgroundTasks
from app.config import settings
from app.utils.logger import get_logger
from app.utils.signature import validate_signature
from app.utils.payload_parser import extract_message_data
from app.services.whatsapp import WhatsAppService
from app.db.repositories.tenant_repo import TenantRepository
from app.db.repositories.message_repo import MessageRepository
from app.agents.graph import run_agent_workflow

log = get_logger(__name__)
router = APIRouter(prefix="", tags=["Webhooks"])

tenant_repo = TenantRepository()
message_repo = MessageRepository()


@router.get("/webhook")
async def verify_webhook(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Webhook verification endpoint required by Meta.
    Validates the mode and verification token and echoes back the challenge.
    """
    log.info("webhook_verification_request", mode=mode, verify_token=verify_token)
    if mode == "subscribe" and verify_token == settings.meta_verify_token:
        log.info("webhook_verification_success")
        return Response(content=challenge, media_type="text/plain")
    log.warning("webhook_verification_failed", mode=mode, token=verify_token)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    Receives incoming webhook payloads from Meta.
    Verifies signature, extracts message details, ensures deduplication, and schedules agent execution.
    """
    body = await request.body()
    body_str = body.decode("utf-8")

    # Validate HMAC signature (always verified in production, optional in dev if header missing)
    if settings.environment != "development" or x_hub_signature_256:
        if not x_hub_signature_256:
            log.error("webhook_missing_signature")
            raise HTTPException(status_code=401, detail="Missing signature header")
        if not validate_signature(body, x_hub_signature_256, settings.meta_app_secret):
            log.error("webhook_invalid_signature")
            raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    # Parse JSON
    try:
        import json
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Extract message data
    data = extract_message_data(payload)
    if not data:
        # Ignore non-message events (status reports, etc.) silently
        return {"status": "ignored"}

    phone_number_id = data["phone_number_id"]
    customer_phone = data["customer_phone"]
    wa_message_id = data["wa_message_id"]

    # 1. Fetch tenant context
    tenant = await tenant_repo.get_by_phone_number_id(phone_number_id)
    if not tenant:
        log.error("webhook_unknown_tenant", phone_number_id=phone_number_id)
        # Return 200 to prevent Meta from retrying indefinitely
        return {"status": "unknown_tenant"}

    # 2. Check for deduplication
    already_processed = await message_repo.exists_by_wa_id(wa_message_id)
    if already_processed:
        log.info("webhook_duplicate_skipped", wa_message_id=wa_message_id)
        return {"status": "duplicate"}

    # 3. Resolve Media URL if inbound message has media
    media_url = None
    if data.get("media_id"):
        try:
            wa_service = WhatsAppService(phone_number_id, tenant["whatsapp"]["access_token"])
            media_url = await wa_service.get_media_url(data["media_id"])
            log.info("resolved_media_url", media_id=data["media_id"], url=media_url)
        except Exception as e:
            log.error("failed_resolving_media_url", media_id=data["media_id"], error=str(e))

    # 4. Construct Agent State
    initial_state = {
        "tenant_id": tenant["tenant_id"],
        "phone_number_id": phone_number_id,
        "access_token": tenant["whatsapp"]["access_token"],
        "customer_phone": customer_phone,
        "inbound_message_id": wa_message_id,
        "inbound_message_type": data["message_type"],
        "inbound_text": data["text"],
        "inbound_media_id": data["media_id"],
        "inbound_media_url": media_url,
        "inbound_media_mime_type": data["media_mime_type"],
    }

    # 5. Execute in background (under 3s response time for Meta)
    background_tasks.add_task(run_agent_workflow, initial_state)

    return {"status": "processing"}
