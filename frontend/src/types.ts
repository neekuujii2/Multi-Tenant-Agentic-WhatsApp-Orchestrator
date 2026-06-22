export interface Tenant {
  tenant_id: string;
  name: string;
  whatsapp: {
    phone_number_id: string;
    business_account_id?: string;
  };
  agent: {
    llm_model: string;
    max_history_messages: number;
    supported_languages: string[];
  };
  media_library?: Record<string, string>;
  campaign_templates?: Array<{
    template_id: string;
    name: string;
    body: string;
    media_url?: string;
    media_type?: string;
  }>;
}

export type SessionStatus = "WAITING_FOR_BOT" | "AGENT_RESPONDING" | "RESOLVED" | "NEEDS_HUMAN";

export interface ContextVars {
  customer_name?: string;
  last_intent?: string;
  products_shown?: string[];
  sentiment_score?: number;
  language?: string;
}

export interface SessionFlags {
  needs_human: boolean;
  is_frustrated: boolean;
  broadcast_eligible: boolean;
}

export interface ChatSession {
  session_id: string;
  tenant_id: string;
  customer_phone: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  message_count: number;
  context_vars: ContextVars;
  flags: SessionFlags;
}

export interface MessageContent {
  type: "text" | "image" | "document" | "audio" | "video" | "sticker";
  text?: string;
  media_url?: string;
  media_mime_type?: string;
  media_filename?: string;
  caption?: string;
}

export interface Message {
  message_id: string;
  session_id: string;
  tenant_id: string;
  direction: "INBOUND" | "OUTBOUND";
  sender: string;
  created_at: string;
  content: MessageContent;
  agent_meta?: {
    node?: string;
    llm_tokens_used?: number;
    processing_ms?: number;
    sentiment_score?: number;
    detected_language?: string;
  };
}

export interface AnalyticsData {
  sessions: {
    total: number;
    needs_human: number;
    resolved: number;
    waiting_for_bot: number;
    agent_responding: number;
  };
  messages: {
    total: number;
    inbound: number;
    outbound: number;
  };
  languages: Record<string, number>;
  average_sentiment: number;
}

export interface DashboardEvent {
  event: "inbound_message" | "outbound_message" | "session_status_changed";
  tenant_id: string;
  session_id: string;
  status: SessionStatus;
  message?: Message;
}
