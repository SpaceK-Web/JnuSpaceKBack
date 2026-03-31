import json
from datetime import date
from app.database.redis_client import get_redis, is_redis_available

# Redis 없을 때 사용할 메모리 버퍼
_memory_buffer: dict[str, dict] = {}


def _daily_key(user_id: str) -> str:
    """오늘 날짜 기반 키"""
    today = date.today().isoformat()
    return f"daily:{user_id}:{today}"


async def save_to_buffer(user_id: str, entries: list[dict]):
    """추출된 엔트리를 버퍼에 누적 (Redis 또는 메모리)"""
    key = _daily_key(user_id)

    # Redis 사용 가능하면 Redis에 저장
    if is_redis_available():
        r = get_redis()
        
        # 기존 데이터 가져오기
        existing = await r.get(key)
        if existing:
            current = json.loads(existing)
        else:
            current = {"entries": []}

        # 딥 머지
        existing_map = {e["key"]: e for e in current["entries"]}

        for new_entry in entries:
            entry_key = new_entry["key"]
            if entry_key in existing_map:
                existing_map[entry_key] = {**existing_map[entry_key], **new_entry}
            else:
                existing_map[entry_key] = new_entry

        current["entries"] = list(existing_map.values())
        await r.set(key, json.dumps(current, ensure_ascii=False), ex=172800)
    else:
        # Redis 없으면 메모리 버퍼 사용
        if key not in _memory_buffer:
            _memory_buffer[key] = {"entries": []}

        existing_map = {e["key"]: e for e in _memory_buffer[key]["entries"]}

        for new_entry in entries:
            entry_key = new_entry["key"]
            if entry_key in existing_map:
                existing_map[entry_key] = {**existing_map[entry_key], **new_entry}
            else:
                existing_map[entry_key] = new_entry

        _memory_buffer[key]["entries"] = list(existing_map.values())


async def get_daily_buffer(user_id: str) -> dict | None:
    """오늘의 버퍼 조회"""
    key = _daily_key(user_id)

    if is_redis_available():
        r = get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    else:
        return _memory_buffer.get(key)


async def get_buffer_by_date(user_id: str, target_date: str) -> dict | None:
    """특정 날짜의 버퍼 조회"""
    key = f"daily:{user_id}:{target_date}"

    if is_redis_available():
        r = get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    else:
        return _memory_buffer.get(key)


async def delete_buffer(user_id: str, target_date: str):
    """버퍼 삭제"""
    key = f"daily:{user_id}:{target_date}"

    if is_redis_available():
        r = get_redis()
        await r.delete(key)
    else:
        if key in _memory_buffer:
            del _memory_buffer[key]
