from fastapi import APIRouter, Query
from datetime import date
from app.services.redis_buffer import get_daily_buffer, get_buffer_by_date
from app.database.mongodb import get_db

router = APIRouter(prefix="/api/dashboard", tags=["대시보드"])


@router.get("/today/{user_id}")
async def get_today_summary(user_id: str):
    """오늘의 실시간 요약 (Redis에서 조회)"""
    buffer = await get_daily_buffer(user_id)

    if not buffer:
        return {"user_id": user_id, "date": date.today().isoformat(), "entries": []}

    return {
        "user_id": user_id,
        "date": date.today().isoformat(),
        "entries": buffer["entries"],
        "total": len(buffer["entries"])
    }


@router.get("/history/{user_id}")
async def get_history(
        user_id: str,
        start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
        end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """과거 기록 조회 (MongoDB에서 조회)"""
    db = get_db()

    cursor = db.daily_records.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        },
        {"_id": 0}
    ).sort("date", -1)

    records = await cursor.to_list(length=100)
    return {"user_id": user_id, "records": records}


@router.get("/search/{user_id}")
async def search_entries(
        user_id: str,
        keyword: str = Query(..., description="검색 키워드 (키 이름 또는 값)")
):
    """키워드 기반 기록 검색"""
    db = get_db()

    cursor = db.daily_records.find(
        {
            "user_id": user_id,
            "$or": [
                {"entries.key": {"$regex": keyword, "$options": "i"}},
                {"entries.value": {"$regex": keyword, "$options": "i"}},
                {"entries.detail": {"$regex": keyword, "$options": "i"}}
            ]
        },
        {"_id": 0}
    ).sort("date", -1)

    records = await cursor.to_list(length=50)
    return {"user_id": user_id, "keyword": keyword, "records": records}
