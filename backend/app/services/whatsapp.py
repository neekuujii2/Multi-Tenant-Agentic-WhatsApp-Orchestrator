"""
Meta WhatsApp Cloud API service.
Provides a singleton httpx.AsyncClient per phone_number_id.
All methods use tenacity for automatic retry with exponential backoff.
"""
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from app.utils.logger import get_logger

log = get_logger(__name__)

BASE_URL = "https://graph.facebook.com/v20.0"

# Singleton client pool — one AsyncClient per phone_number_id
_clients: dict[str, httpx.AsyncClient] = {}


def _get_client(phone_number_id: str, access_token: str) -> httpx.AsyncClient:
    """Return singleton httpx client for the given phone_number_id."""
    if phone_number_id not in _clients:
        _clients[phone_number_id] = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _clients[phone_number_id]


class WhatsAppService:
    """
    Wraps Meta WhatsApp Cloud API calls for a specific tenant.
    Handles: read receipts, typing indicators, text/image/document messages.
    """

    def __init__(self, phone_number_id: str, access_token: str):
        self.messages_url = f"{BASE_URL}/{phone_number_id}/messages"
        self.media_url_base = BASE_URL
        self.client = _get_client(phone_number_id, access_token)
        self.phone_number_id = phone_number_id

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        reraise=True,
    )
    async def _post(self, body: dict) -> dict:
        resp = await self.client.post(self.messages_url, json=body)
        resp.raise_for_status()
        return resp.json()

    async def send_read_receipt(self, message_id: str) -> bool:
        """Mark a customer's message as read (shows double blue ticks)."""
        try:
            await self._post({
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            })
            return True
        except Exception as e:
            log.warning("read_receipt_failed", error=str(e), message_id=message_id)
            return False

    async def send_typing_indicator(self, to: str) -> bool:
        """Show the 'typing...' indicator in customer's chat."""
        try:
            await self._post({
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "typing_indicator",
                "typing_indicator": {"type": "text"},
            })
            return True
        except Exception as e:
            log.warning("typing_indicator_failed", error=str(e), to=to)
            return False

    async def send_text(self, to: str, text: str) -> dict:
        """Send a plain text message (supports WhatsApp markdown: *bold*, _italic_)."""
        return await self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text, "preview_url": False},
        })

    async def send_image(self, to: str, url: str, caption: str = "") -> dict:
        """Send an image via public URL with optional caption."""
        body: dict = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": url},
        }
        if caption:
            body["image"]["caption"] = caption
        return await self._post(body)

    async def send_document(
        self, to: str, url: str, filename: str, caption: str = ""
    ) -> dict:
        """Send a document (PDF) via public URL with filename."""
        body: dict = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"link": url, "filename": filename},
        }
        if caption:
            body["document"]["caption"] = caption
        return await self._post(body)

    async def get_media_url(self, media_id: str) -> str:
        """
        Retrieve temporary download URL for an inbound media message.
        URL expires after ~5 minutes — download immediately.
        """
        resp = await self.client.get(
            f"{self.media_url_base}/{media_id}",
        )
        resp.raise_for_status()
        return resp.json()["url"]

    async def download_media(self, media_url: str) -> bytes:
        """Download media bytes from Meta's temporary URL."""
        resp = await self.client.get(media_url)
        resp.raise_for_status()
        return resp.content
