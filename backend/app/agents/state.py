"""
AgentState TypedDict — the single state object passed through the LangGraph pipeline.
Each node reads from and writes to this state.
"""
from typing import TypedDict, Optional, Literal, List


class AgentState(TypedDict):
    # ── Inbound message fields ────────────────────────────────────────────────
    tenant_id: str
    phone_number_id: str          # Identifies which tenant this message belongs to
    customer_phone: str           # Customer's WhatsApp number (E.164 format)
    inbound_message_id: str       # WhatsApp message ID (for read receipt)
    inbound_text: str             # Text body of the message (or caption)
    inbound_message_type: str     # text|image|document|audio|video|sticker
    inbound_media_id: Optional[str]   # Media ID for downloading from Meta
    inbound_media_url: Optional[str]  # Downloaded media URL (for Claude Vision)
    inbound_media_bytes: Optional[bytes]  # Raw media bytes for multimodal
    inbound_media_mime_type: Optional[str]

    # ── Tenant context ────────────────────────────────────────────────────────
    access_token: str             # Tenant's Meta access token
    tenant_name: str
    tenant_system_prompt: str
    media_library: dict           # {"catalog": "https://...", "sofa": "https://..."}
    chat_history: List[dict]      # [{role: user|assistant, content: str}]
    sentiment_threshold: float    # From tenant settings (default: -0.5)
    supported_languages: List[str]

    # ── LLM output ───────────────────────────────────────────────────────────
    response_type: Literal["text", "image", "document"]
    response_text: str
    response_media_url: Optional[str]
    response_media_filename: Optional[str]
    detected_language: Optional[str]   # e.g. "en", "hi", "hinglish"

    # ── Session tracking ──────────────────────────────────────────────────────
    session_id: str
    session_status: str
    sentiment_score: Optional[float]   # -1.0 (very negative) to 1.0 (very positive)

    # ── Internal / error handling ─────────────────────────────────────────────
    error: Optional[str]
