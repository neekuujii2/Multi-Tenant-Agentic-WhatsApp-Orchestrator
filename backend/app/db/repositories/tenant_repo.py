"""Tenant repository — CRUD operations for the tenants collection."""
from app.db.mongo import get_db
from app.utils.logger import get_logger

log = get_logger(__name__)


class TenantRepository:
    async def _col(self):
        db = await get_db()
        return db["tenants"]

    async def get_by_id(self, tenant_id: str) -> dict | None:
        col = await self._col()
        doc = await col.find_one({"tenant_id": tenant_id}, {"_id": 0})
        return doc

    async def get_by_phone_number_id(self, phone_number_id: str) -> dict | None:
        col = await self._col()
        doc = await col.find_one(
            {"whatsapp.phone_number_id": phone_number_id}, {"_id": 0}
        )
        return doc

    async def list_all(self) -> list[dict]:
        col = await self._col()
        # Return safe fields only (exclude access tokens from list view)
        cursor = col.find(
            {},
            {
                "_id": 0,
                "tenant_id": 1,
                "name": 1,
                "campaign_templates": 1,
                "settings": 1,
                "whatsapp.phone_number_id": 1,
                "whatsapp.business_account_id": 1,
                "agent.llm_model": 1,
                "agent.max_history_messages": 1,
                "agent.supported_languages": 1,
            },
        )
        return await cursor.to_list(100)

    async def upsert(self, tenant_id: str, data: dict) -> bool:
        col = await self._col()
        from datetime import datetime
        data["updated_at"] = datetime.utcnow()
        result = await col.update_one(
            {"tenant_id": tenant_id}, {"$set": data}, upsert=True
        )
        return result.acknowledged
