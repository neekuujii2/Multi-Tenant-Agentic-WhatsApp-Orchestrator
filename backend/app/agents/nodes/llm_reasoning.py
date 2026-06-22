"""
Node 3: LLM Reasoning
Responsibilities:
  - Build system prompt with tenant context + media library
  - Detect language (Hinglish, Hindi, English, etc.)
  - Call Claude claude-sonnet-4-6 with tool use
  - Handle multimodal input (images via Claude Vision)
  - Parse tool call response into AgentState fields

Language Support:
  - English: standard response
  - Hindi: responds in Hindi (Devanagari or Roman)
  - Hinglish: responds in natural Hindi-English mix (most common in India)
  - Auto-detected from customer message
"""
import json
import base64
from datetime import datetime
from typing import Optional

from anthropic import AsyncAnthropic

from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# ── Tool Definitions for Claude ────────────────────────────────────────────────

TOOLS = [
    {
        "name": "send_text",
        "description": (
            "Send a plain text reply to the customer. "
            "Supports WhatsApp markdown: *bold*, _italic_, ~strikethrough~. "
            "If customer wrote in Hinglish or Hindi, respond in the same language naturally."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The response text in the customer's language",
                },
                "sentiment_score": {
                    "type": "number",
                    "minimum": -1.0,
                    "maximum": 1.0,
                    "description": (
                        "Sentiment of the CUSTOMER's message: "
                        "-1.0=very frustrated/angry, 0=neutral, 1.0=very happy/positive"
                    ),
                },
                "detected_language": {
                    "type": "string",
                    "enum": ["en", "hi", "hinglish", "other"],
                    "description": "Language detected in the customer's message",
                },
            },
            "required": ["text", "sentiment_score", "detected_language"],
        },
    },
    {
        "name": "send_media",
        "description": (
            "Send an image or document from the tenant's media library. "
            "Use this when the customer asks for a product photo, catalog, invoice, "
            "price list, or any visual asset. "
            "Always include a friendly caption text in the customer's language."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "media_key": {
                    "type": "string",
                    "description": "Key from the media_library (e.g. 'catalog', 'sofa')",
                },
                "caption": {
                    "type": "string",
                    "description": "Accompanying text message in the customer's language",
                },
                "sentiment_score": {
                    "type": "number",
                    "minimum": -1.0,
                    "maximum": 1.0,
                },
                "detected_language": {
                    "type": "string",
                    "enum": ["en", "hi", "hinglish", "other"],
                },
            },
            "required": ["media_key", "caption", "sentiment_score", "detected_language"],
        },
    },
]


def _build_system_prompt(state: AgentState) -> str:
    """Construct the full system prompt with tenant context and language instructions."""
    media_json = json.dumps(state["media_library"], indent=2, ensure_ascii=False)

    return f"""{state['tenant_system_prompt']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 MULTI-LANGUAGE INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Detect the customer's language from their message.
- If they write in English → respond in English.
- If they write in Hindi (Devanagari) → respond in Hindi.
- If they write in Hinglish (Hindi-English mix, Roman script) → respond naturally in Hinglish.
  Example Hinglish: "Haan bilkul! Hamara catalog aapko abhi bhej dete hain 📚"
- Always mirror the customer's communication style and formality level.
- Supported languages: {", ".join(state.get("supported_languages", ["en", "hi", "hinglish"]))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 MEDIA LIBRARY (send these assets when relevant):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{media_json}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ RESPONSE RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ALWAYS respond by calling one of the provided tools (send_text or send_media).
- NEVER respond without a tool call.
- Assess the customer's sentiment from their message tone.
- If customer seems frustrated (anger, complaints, CAPS), set sentiment_score below -0.4.
- If a customer sends an image, analyze it and respond helpfully about what you see.
- Keep responses concise and conversational (max 3-4 sentences for text).
"""


def _build_messages(state: AgentState) -> list[dict]:
    """Build the messages array for the Anthropic API call."""
    messages = list(state.get("chat_history", []))

    # Build user message — may be multimodal (text + image)
    user_content: list = []

    # Add image if present (Claude Vision)
    media_bytes = state.get("inbound_media_bytes")
    media_mime = state.get("inbound_media_mime_type", "image/jpeg")

    if media_bytes and media_mime and media_mime.startswith("image/"):
        b64_data = base64.standard_b64encode(media_bytes).decode("utf-8")
        user_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_mime,
                "data": b64_data,
            },
        })

    # Add text content
    text = state.get("inbound_text", "").strip()
    if not text and media_bytes:
        text = "Please analyze this image and help me."

    user_content.append({"type": "text", "text": text or "Hello"})

    # If only one content item, unwrap from list for cleaner API call
    messages.append({
        "role": "user",
        "content": user_content if len(user_content) > 1 else user_content[0]["text"],
    })

    return messages


def _parse_response(state: AgentState, response) -> AgentState:
    """Extract tool use results from Claude's response and update AgentState."""
    for block in response.content:
        if block.type == "tool_use":
            tool_input = block.input
            sentiment = float(tool_input.get("sentiment_score", 0.0))
            detected_lang = tool_input.get("detected_language", "en")

            if block.name == "send_text":
                return {
                    **state,
                    "response_type": "text",
                    "response_text": tool_input.get("text", ""),
                    "response_media_url": None,
                    "response_media_filename": None,
                    "sentiment_score": sentiment,
                    "detected_language": detected_lang,
                }

            elif block.name == "send_media":
                media_key = tool_input.get("media_key", "")
                media_url = state["media_library"].get(media_key, "")

                # Determine media type from URL extension
                url_lower = media_url.lower()
                if any(url_lower.endswith(ext) for ext in [".pdf", ".doc", ".docx"]):
                    response_type = "document"
                    filename = media_url.split("/")[-1]
                else:
                    response_type = "image"
                    filename = None

                return {
                    **state,
                    "response_type": response_type,
                    "response_text": tool_input.get("caption", ""),
                    "response_media_url": media_url,
                    "response_media_filename": filename,
                    "sentiment_score": sentiment,
                    "detected_language": detected_lang,
                }

    # Fallback if no tool use block found
    log.warning("no_tool_use_in_response", tenant_id=state.get("tenant_id"))
    fallback = "I'll be right with you! / Main abhi aapki madad karta hoon!"
    return {
        **state,
        "response_type": "text",
        "response_text": fallback,
        "response_media_url": None,
        "response_media_filename": None,
        "sentiment_score": 0.0,
        "detected_language": "en",
    }


async def llm_reasoning_node(state: AgentState) -> AgentState:
    """
    Third node in the LangGraph pipeline.
    Calls Claude claude-sonnet-4-6 with tool use for structured responses.
    Supports multimodal (images) and Hinglish/Hindi language detection.
    """
    start = datetime.utcnow()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    system_prompt = _build_system_prompt(state)
    messages = _build_messages(state)

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=TOOLS,
            tool_choice={"type": "any"},  # Force tool use
        )
    except Exception as e:
        log.error(
            "llm_call_failed",
            tenant_id=state.get("tenant_id"),
            error=str(e),
        )
        # Graceful fallback message (bilingual)
        return {
            **state,
            "response_type": "text",
            "response_text": (
                "Ek second! Main aapki query check kar raha hoon. "
                "Please hold on a moment!"
            ),
            "response_media_url": None,
            "response_media_filename": None,
            "sentiment_score": 0.0,
            "detected_language": "hinglish",
            "error": str(e),
        }

    elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
    tokens_used = response.usage.input_tokens + response.usage.output_tokens

    log.info(
        "llm_reasoning_complete",
        tenant_id=state.get("tenant_id"),
        session_id=state.get("session_id"),
        stop_reason=response.stop_reason,
        tokens_used=tokens_used,
        elapsed_ms=elapsed,
    )

    return _parse_response(state, response)
