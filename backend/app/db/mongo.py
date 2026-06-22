"""
MongoDB async client using Motor.
Handles connection lifecycle, index creation, and provides database access.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Initialize MongoDB connection and verify connectivity."""
    global _client
    _client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
        minPoolSize=2,
    )
    await _client.admin.command("ping")
    log.info("mongodb_connected")
    await init_indexes()


async def disconnect_db() -> None:
    """Close MongoDB connection cleanly."""
    global _client
    if _client:
        _client.close()
        log.info("mongodb_disconnected")


async def get_db() -> AsyncIOMotorDatabase:
    """Return the application database instance."""
    return _client["orchestrator"]


async def init_indexes() -> None:
    """Create all required indexes. Idempotent — safe to call on every startup."""
    db = await get_db()

    # tenants collection
    await db["tenants"].create_index("tenant_id", unique=True)
    await db["tenants"].create_index("whatsapp.phone_number_id", unique=True)

    # chat_sessions collection
    await db["chat_sessions"].create_index(
        [("tenant_id", 1), ("customer_phone", 1)], unique=True
    )
    await db["chat_sessions"].create_index([("tenant_id", 1), ("status", 1)])
    await db["chat_sessions"].create_index([("last_message_at", -1)])
    await db["chat_sessions"].create_index("flags.needs_human")

    # messages collection
    await db["messages"].create_index([("session_id", 1), ("created_at", -1)])
    await db["messages"].create_index([("tenant_id", 1), ("created_at", -1)])
    await db["messages"].create_index(
        "meta.wa_message_id", unique=True, sparse=True
    )

    log.info("mongodb_indexes_created")
