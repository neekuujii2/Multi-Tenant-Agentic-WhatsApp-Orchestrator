"""
All Pydantic models for the WhatsApp Orchestrator.
These define the data contracts for MongoDB documents and API responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime
from enum import Enum


# ─── Tenant Models ────────────────────────────────────────────────────────────

class WhatsAppConfig(BaseModel):
    phone_number_id: str
    access_token: str
    business_account_id: Optional[str] = None


class AgentConfig(BaseModel):
    system_prompt: str
    llm_model: str = "claude-sonnet-4-6"
    max_history_messages: int = 5
    temperature: float = 0.7
    supported_languages: List[str] = ["en", "hi", "hinglish"]


class CampaignTemplate(BaseModel):
    template_id: str
    name: str
    body: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # "document" | "image"


class BusinessHours(BaseModel):
    enabled: bool = False
    timezone: str = "Asia/Kolkata"
    open: str = "09:00"
    close: str = "21:00"


class TenantSettings(BaseModel):
    auto_reply_enabled: bool = True
    sentiment_threshold: float = -0.5
    typing_indicator_enabled: bool = True
    business_hours: BusinessHours = Field(default_factory=BusinessHours)


class Tenant(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    tenant_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    whatsapp: WhatsAppConfig
    agent: AgentConfig
    media_library: Dict[str, str] = {}
    campaign_templates: List[CampaignTemplate] = []
    settings: TenantSettings = Field(default_factory=TenantSettings)

    class Config:
        populate_by_name = True


# ─── Session Models ────────────────────────────────────────────────────────────

class SessionStatus(str, Enum):
    WAITING_FOR_BOT = "WAITING_FOR_BOT"
    AGENT_RESPONDING = "AGENT_RESPONDING"
    RESOLVED = "RESOLVED"
    NEEDS_HUMAN = "NEEDS_HUMAN"


class ContextVars(BaseModel):
    customer_name: Optional[str] = None
    last_intent: Optional[str] = None
    products_shown: List[str] = []
    sentiment_score: Optional[float] = None
    language: str = "en"  # detected language code


class SessionFlags(BaseModel):
    needs_human: bool = False
    is_frustrated: bool = False
    broadcast_eligible: bool = True


class ChatSession(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    session_id: str
    tenant_id: str
    customer_phone: str
    status: SessionStatus = SessionStatus.WAITING_FOR_BOT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    context_vars: ContextVars = Field(default_factory=ContextVars)
    flags: SessionFlags = Field(default_factory=SessionFlags)
    metadata: Dict[str, Any] = {}

    class Config:
        populate_by_name = True


# ─── Message Models ────────────────────────────────────────────────────────────

class MessageContent(BaseModel):
    type: Literal["text", "image", "document", "audio", "video", "sticker"]
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_mime_type: Optional[str] = None
    media_filename: Optional[str] = None
    caption: Optional[str] = None


class MessageMeta(BaseModel):
    wa_message_id: Optional[str] = None
    wa_timestamp: Optional[str] = None
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class AgentMeta(BaseModel):
    node: Optional[str] = None
    llm_tokens_used: Optional[int] = None
    processing_ms: Optional[int] = None
    sentiment_score: Optional[float] = None
    typing_started_at: Optional[datetime] = None
    typing_ended_at: Optional[datetime] = None
    detected_language: Optional[str] = None


class Message(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    message_id: str
    session_id: str
    tenant_id: str
    direction: Literal["INBOUND", "OUTBOUND"]
    sender: str  # phone number or "BOT"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    content: MessageContent
    meta: MessageMeta = Field(default_factory=MessageMeta)
    agent_meta: AgentMeta = Field(default_factory=AgentMeta)

    class Config:
        populate_by_name = True


# ─── API Request/Response Models ──────────────────────────────────────────────

class BroadcastRequest(BaseModel):
    tenant_id: str
    template_id: str
    cohort: Literal["active_7days", "all_sessions", "resolved_only"]
