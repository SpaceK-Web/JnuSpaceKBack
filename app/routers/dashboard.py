import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Query

from app.database.postgres import get_pool
from app.services.storage import get_daily_record

router = APIRouter(prefix="/api/dashboard", tags=["대시보드"])


def _parse_entries(raw) -> list:
    """asyncpg JSONB는 Python list로 반환되지만, 혹시 문자열일 경우 파싱."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


def _fmt_dt(dt) -> str | None:
    """datetime → ISO 문자열 변환 (프론트 타입: string)."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


@router.get("/today/{user_id}", summary="오늘 상태 조회")
async def get_today_summary(user_id: str):
    """
    오늘 날짜의 daily_records 에서 entries 를 읽어 반환합니다.

    반환 형식:
    {
        "user_id": str,
        "date": "YYYY-MM-DD",
        "entries": [ EntryResponse, ... ],
        "total": int
    }
    """
    record = await get_daily_record(user_id)

    if not record:
        return {
            "user_id": user_id,
            "date": date.today().isoformat(),
            "entries": [],
            "total": 0,
        }

    entries = _parse_entries(record.get("entries", []))
    return {
        "user_id": user_id,
        "date": date.today().isoformat(),
        "entries": entries,
        "total": len(entries),
    }


@router.get("/history/{user_id}", summary="기간별 기록 조회")
async def get_history(
    user_id: str,
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)"),
):
    """
    start_date ~ end_date 범위의 daily_records 를 반환합니다.

    반환 형식:
    {
        "user_id": str,
        "records": [
            {
                "user_id": str,
                "date": "YYYY-MM-DD",
                "entries": [ EntryResponse, ... ],
                "updated_at": "ISO datetime string"
            },
            ...
        ]
    }
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, date, entries, updated_at
            FROM daily_records
            WHERE user_id = $1 AND date >= $2 AND date <= $3
            ORDER BY date DESC
            LIMIT 100
            """,
            user_id, start_date, end_date,
        )

    records = [
        {
            "user_id": row["user_id"],
            "date": row["date"],
            "entries": _parse_entries(row["entries"]),
            "updated_at": _fmt_dt(row["updated_at"]),
        }
        for row in rows
    ]
    return {"user_id": user_id, "records": records}


@router.get("/debug/{user_id}", summary="[디버그] DB 저장 상태 확인")
async def debug_user_data(user_id: str):
    """
    daily_records / conversations 실제 저장 상태를 확인합니다.
    대시보드가 0으로 보일 때 원인 파악에 사용하세요.
    """
    pool = get_pool()
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async with pool.acquire() as conn:
        daily_rows = await conn.fetch(
            "SELECT id, user_id, date, entries, updated_at FROM daily_records WHERE user_id = $1 ORDER BY date DESC LIMIT 5",
            user_id,
        )
        conv_count = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE user_id = $1", user_id
        )

    records_info = []
    for row in daily_rows:
        raw = row["entries"]
        entries = _parse_entries(raw)
        records_info.append({
            "id": row["id"],
            "date": str(row["date"]),
            "entries_count": len(entries),
            "entries_type_from_db": type(raw).__name__,
            "updated_at": _fmt_dt(row["updated_at"]),
        })

    return {
        "user_id": user_id,
        "today_utc": today_utc,
        "conversations_total": conv_count,
        "daily_records_found": len(daily_rows),
        "daily_records": records_info,
    }


@router.get("/search/{user_id}", summary="키워드 검색")
async def search_entries(
    user_id: str,
    keyword: str = Query(..., description="검색 키워드 (키 이름 또는 값)"),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, date, entries, updated_at
            FROM daily_records
            WHERE user_id = $1
              AND EXISTS (
                SELECT 1 FROM jsonb_array_elements(entries) e
                WHERE e->>'key'    ILIKE $2
                   OR e->>'value'  ILIKE $2
                   OR e->>'detail' ILIKE $2
              )
            ORDER BY date DESC
            LIMIT 50
            """,
            user_id, f"%{keyword}%",
        )
    records = [
        {
            "user_id": row["user_id"],
            "date": row["date"],
            "entries": _parse_entries(row["entries"]),
            "updated_at": _fmt_dt(row["updated_at"]),
        }
        for row in rows
    ]
    return {"user_id": user_id, "keyword": keyword, "records": records}
