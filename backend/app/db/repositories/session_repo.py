"""Session repository — CRUD operations for the chat_sessions collection."""
from datetime import datetime
from app.db.mongo import get_db
from app.utils.logger import get_logger

log = get_logger(__name__)


class SessionRepository:
    async def _col(self):
        db = await get_db()
        return db["chat_sessions"]

    async def upsert(
        self,
        session_id: str,
        tenant_id: str,
        customer_phone: str,
        status: str,
    ) -> dict:
        col = await self._col()
        now = datetime.utcnow()
        result = await col.find_one_and_update(
            {"session_id": session_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": now,
                    "last_message_at": now,
                },
                "$setOnInsert": {
                    "session_id": session_id,
                    "tenant_id": tenant_id,
                    "customer_phone": customer_phone,
                    "created_at": now,
                    "message_count": 0,
                    "context_vars": {
                        "customer_name": None,
                        "last_intent": None,
                        "products_shown": [],
                        "sentiment_score": None,
                        "language": "en",
                    },
                    "flags": {
                        "needs_human": False,
                        "is_frustrated": False,
                        "broadcast_eligible": True,
                    },
                    "metadata": {},
                },
                "$inc": {"message_count": 1},
            },
            upsert=True,
            return_document=True,
        )
        return result or {}

    async def update_status(
        self,
        session_id: str,
        status: str,
        sentiment: float | None = None,
        detected_language: str | None = None,
    ) -> bool:
        col = await self._col()
        update: dict = {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow(),
                "flags.needs_human": status == "NEEDS_HUMAN",
                "flags.is_frustrated": status == "NEEDS_HUMAN",
            }
        }
        if sentiment is not None:
            update["$set"]["context_vars.sentiment_score"] = sentiment
        if detected_language:
            update["$set"]["context_vars.language"] = detected_language

        result = await col.update_one({"session_id": session_id}, update)
        return result.modified_count > 0

    async def list_by_tenant(
        self,
        tenant_id: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        col = await self._col()
        query: dict = {"tenant_id": tenant_id}
        if status:
            query["status"] = status
        cursor = col.find(query, {"_id": 0}).sort("last_message_at", -1).limit(limit)
        return await cursor.to_list(limit)

    async def get_by_phone(
        self, tenant_id: str, customer_phone: str
    ) -> dict | None:
        col = await self._col()
        return await col.find_one(
            {"tenant_id": tenant_id, "customer_phone": customer_phone}, {"_id": 0}
        )

    async def get_by_id(self, session_id: str) -> dict | None:
        col = await self._col()
        return await col.find_one({"session_id": session_id}, {"_id": 0})
