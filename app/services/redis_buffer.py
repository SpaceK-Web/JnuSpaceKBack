import json
from datetime import date
from app.database.redis_client import get_redis


def _daily_key(user_id: str) -> str:
    """오늘 날짜 기반 Redis 키"""
    today = date.today().isoformat()
    return f"daily:{user_id}:{today}"


async def save_to_buffer(user_id: str, entries: list[dict]):
    """추출된 엔트리를 Redis 일일 버퍼에 누적"""
    r = get_redis()
    key = _daily_key(user_id)

    # 기존 데이터 가져오기
    existing = await r.get(key)
    if existing:
        current = json.loads(existing)
    else:
        current = {"entries": []}

    # ── 딥 머지: 같은 키가 있으면 덮어쓰기 ──
    existing_map = {e["key"]: e for e in current["entries"]}

    for new_entry in entries:
        entry_key = new_entry["key"]

        if entry_key in existing_map:
            # 같은 키 → 최신 값으로 업데이트
            existing_map[entry_key] = {
                **existing_map[entry_key],
                **new_entry
            }
        else:
            # 새 키 → 추가
            existing_map[entry_key] = new_entry

    current["entries"] = list(existing_map.values())

    # Redis에 저장 (TTL: 48시간 - 자정 flush 실패 대비)
    await r.set(key, json.dumps(current, ensure_ascii=False), ex=172800)


async def get_daily_buffer(user_id: str) -> dict | None:
    """오늘의 일일 버퍼 조회"""
    r = get_redis()
    key = _daily_key(user_id)
    data = await r.get(key)
    return json.loads(data) if data else None


async def get_buffer_by_date(user_id: str, target_date: str) -> dict | None:
    """특정 날짜의 버퍼 조회"""
    r = get_redis()
    key = f"daily:{user_id}:{target_date}"
    data = await r.get(key)
    return json.loads(data) if data else None


async def delete_buffer(user_id: str, target_date: str):
    """flush 완료 후 버퍼 삭제"""
    r = get_redis()
    key = f"daily:{user_id}:{target_date}"
    await r.delete(key)
