"""
Meta WhatsApp Cloud API webhook payload parser.
Extracts message data from the nested webhook structure.
Handles all message types: text, image, document, audio, video, sticker.
Skips status update events (read, delivered, sent).
"""
from app.utils.logger import get_logger

log = get_logger(__name__)


def extract_message_data(payload: dict) -> dict | None:
    """
    Parse Meta webhook payload and extract actionable message data.

    Returns None for:
    - Non-message events (status updates, reactions)
    - Malformed payloads

    Returns dict with:
    - phone_number_id: str (identifies the tenant)
    - customer_phone: str
    - wa_message_id: str
    - message_type: str (text|image|document|audio|video|sticker)
    - text: str | None
    - media_id: str | None (for downloading media from Meta)
    - media_mime_type: str | None
    - timestamp: str
    """
    try:
        entry = payload.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0]
        value = change.get("value", {})

        # Skip if no messages array (e.g. status update webhooks)
        messages = value.get("messages")
        if not messages:
            return None

        msg = messages[0]
        msg_type = msg.get("type", "")

        # Skip status update messages
        if msg_type == "status":
            return None

        phone_number_id = value.get("metadata", {}).get("phone_number_id", "")
        customer_phone = msg.get("from", "")
        wa_message_id = msg.get("id", "")
        timestamp = msg.get("timestamp", "")

        # Extract content based on type
        text = None
        media_id = None
        media_mime_type = None
        media_filename = None

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")

        elif msg_type == "image":
            image_data = msg.get("image", {})
            media_id = image_data.get("id")
            media_mime_type = image_data.get("mime_type", "image/jpeg")
            text = image_data.get("caption", "")  # Optional caption

        elif msg_type == "document":
            doc_data = msg.get("document", {})
            media_id = doc_data.get("id")
            media_mime_type = doc_data.get("mime_type", "application/pdf")
            media_filename = doc_data.get("filename")
            text = doc_data.get("caption", "")

        elif msg_type == "audio":
            audio_data = msg.get("audio", {})
            media_id = audio_data.get("id")
            media_mime_type = audio_data.get("mime_type", "audio/ogg")
            text = "[Audio message received]"

        elif msg_type == "video":
            video_data = msg.get("video", {})
            media_id = video_data.get("id")
            media_mime_type = video_data.get("mime_type", "video/mp4")
            text = video_data.get("caption", "[Video message received]")

        elif msg_type == "sticker":
            text = "[Sticker received]"

        else:
            log.warning("unsupported_message_type", msg_type=msg_type)
            text = f"[{msg_type} message]"

        if not phone_number_id or not customer_phone or not wa_message_id:
            log.warning("incomplete_message_data", payload_keys=list(payload.keys()))
            return None

        return {
            "phone_number_id": phone_number_id,
            "customer_phone": customer_phone,
            "wa_message_id": wa_message_id,
            "message_type": msg_type,
            "text": text or "",
            "media_id": media_id,
            "media_mime_type": media_mime_type,
            "media_filename": media_filename,
            "timestamp": timestamp,
        }

    except (KeyError, IndexError, TypeError) as e:
        log.error("payload_parse_error", error=str(e))
        return None
