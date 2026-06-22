"""Message repository — CRUD operations for the messages collection."""
from app.db.mongo import get_db
from app.utils.logger import get_logger

log = get_logger(__name__)


class MessageRepository:
    async def _col(self):
        db = await get_db()
        return db["messages"]

    async def insert(self, message: dict) -> str:
        col = await self._col()
        result = await col.insert_one(message)
        return str(result.inserted_id)

    async def get_last_n(self, session_id: str, n: int = 5) -> list[dict]:
        """Fetch last N messages for LLM chat history, oldest-first."""
        col = await self._col()
        cursor = col.find(
            {"session_id": session_id},
            {
                "_id": 0,
                "direction": 1,
                "content.text": 1,
                "content.type": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1).limit(n)
        docs = await cursor.to_list(n)
        return list(reversed(docs))  # oldest-first for LLM context

    async def get_thread(self, session_id: str, limit: int = 100) -> list[dict]:
        """Fetch full message thread for dashboard display, oldest-first."""
        col = await self._col()
        cursor = col.find(
            {"session_id": session_id}, {"_id": 0}
        ).sort("created_at", 1).limit(limit)
        return await cursor.to_list(limit)

    async def exists_by_wa_id(self, wa_message_id: str) -> bool:
        """Check if a WhatsApp message has already been processed."""
        col = await self._col()
        doc = await col.find_one({"meta.wa_message_id": wa_message_id}, {"_id": 1})
        return doc is not None
