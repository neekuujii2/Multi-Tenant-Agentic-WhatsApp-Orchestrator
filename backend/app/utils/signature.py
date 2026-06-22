"""
HMAC-SHA256 webhook signature validation for Meta WhatsApp Cloud API.
Uses constant-time comparison to prevent timing attacks.
"""
import hmac
import hashlib


def validate_signature(body: bytes, signature_header: str, secret: str) -> bool:
    """
    Validate X-Hub-Signature-256 header from Meta webhook.

    Args:
        body: Raw request body bytes
        signature_header: Value of X-Hub-Signature-256 header
        secret: Meta App Secret (META_APP_SECRET env var)

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    # Constant-time comparison prevents timing oracle attacks
    return hmac.compare_digest(expected, signature_header)
