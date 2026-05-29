import datetime
import json

from app.database.postgres import get_pool
from app.models.schemas import EntryResponse


def _to_dict(entry) -> dict:
    if isinstance(entry, dict):
        return entry
    return entry.model_dump()


def _parse_jsonb_list(raw) -> list:
    """asyncpg JSONB 컬럼을 항상 Python list로 반환."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            result = json.loads(raw)
            return result if isinstance(result, list) else []
        except Exception:
            return []
    return []


async def save_conversation(user_id: str, conversation: str, metadata: dict = None) -> str:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO conversations (user_id, conversation, metadata)
            VALUES ($1, $2, $3::jsonb)
            RETURNING id
            """,
            user_id,
            conversation,
            json.dumps(metadata or {}, ensure_ascii=False),
        )
    return str(row["id"])


async def save_entries(user_id: str, entries: list[EntryResponse], conversation_id: str = None) -> str:
    pool = get_pool()
    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    entries_data = [_to_dict(e) for e in entries]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO extracted_entries (user_id, conversation_id, entries, date)
            VALUES ($1, $2, $3::jsonb, $4)
            RETURNING id
            """,
            user_id,
            int(conversation_id) if conversation_id else None,
            json.dumps(entries_data, ensure_ascii=False),
            today,
        )
    return str(row["id"])


async def save_to_daily_record(user_id: str, entries: list[EntryResponse], date_str: str = None) -> str:
    pool = get_pool()
    if date_str is None:
        date_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    entries_data = [_to_dict(e) for e in entries]

    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id, entries FROM daily_records WHERE user_id = $1 AND date = $2",
            user_id, date_str,
        )

        if existing:
            current = _parse_jsonb_list(existing["entries"])
            merged = {e["key"]: e for e in current}
            for entry in entries_data:
                key = entry["key"]
                merged[key] = {**merged[key], **entry} if key in merged else entry

            await conn.execute(
                """
                UPDATE daily_records
                SET entries = $1::jsonb, updated_at = NOW()
                WHERE user_id = $2 AND date = $3
                """,
                json.dumps(list(merged.values()), ensure_ascii=False),
                user_id, date_str,
            )
            return "updated"
        else:
            row = await conn.fetchrow(
                """
                INSERT INTO daily_records (user_id, date, entries)
                VALUES ($1, $2, $3::jsonb)
                RETURNING id
                """,
                user_id, date_str,
                json.dumps(entries_data, ensure_ascii=False),
            )
            return str(row["id"])


async def get_daily_record(user_id: str, date_str: str = None) -> dict | None:
    pool = get_pool()
    if date_str is None:
        date_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT entries FROM daily_records WHERE user_id = $1 AND date = $2",
            user_id, date_str,
        )
    if not row:
        return None
    return {"entries": _parse_jsonb_list(row["entries"])}


async def get_user_conversations(user_id: str, limit: int = 100, skip: int = 0) -> list[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, conversation, metadata, timestamp
            FROM conversations
            WHERE user_id = $1
            ORDER BY timestamp DESC
            OFFSET $2 LIMIT $3
            """,
            user_id, skip, limit,
        )
    return [dict(row) for row in rows]


