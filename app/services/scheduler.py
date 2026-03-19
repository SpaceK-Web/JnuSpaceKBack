import json
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.redis_client import get_redis
from app.database.mongodb import get_db
from app.services.preferred_keys import promote_custom_key

scheduler = AsyncIOScheduler()


async def flush_daily_records():
    """매일 23:50 - Redis 일일 버퍼를 MongoDB로 이동"""

    r = get_redis()
    db = get_db()
    today = date.today().isoformat()

    # 모든 daily:*:오늘날짜 키 스캔
    cursor = 0
    pattern = f"daily:*:{today}"

    while True:
        cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)

        for key in keys:
            try:
                data = await r.get(key)
                if not data:
                    continue

                record = json.loads(data)
                # daily:user123:2026-03-19 → user123
                user_id = key.split(":")[1]

                # MongoDB에 저장
                document = {
                    "user_id": user_id,
                    "date": today,
                    "entries": record["entries"],
                    "flushed_at": date.today().isoformat()
                }

                # upsert: 같은 날짜에 이미 있으면 업데이트
                await db.daily_records.update_one(
                    {"user_id": user_id, "date": today},
                    {"$set": document},
                    upsert=True
                )

                # ── 자유 키 승격 처리 ──
                for entry in record["entries"]:
                    if entry.get("is_custom") and entry.get("description"):
                        promote_custom_key(entry["key"], entry["description"])

                # Redis에서 삭제
                await r.delete(key)
                print(f"✅ Flush 완료: {user_id} / {today}")

            except Exception as e:
                print(f"❌ Flush 실패: {key} - {e}")

        if cursor == 0:
            break


def start_scheduler():
    """스케줄러 시작"""
    scheduler.add_job(
        flush_daily_records,
        trigger="cron",
        hour=23,
        minute=50,
        id="daily_flush",
        replace_existing=True
    )
    scheduler.start()
    print("⏰ 스케줄러 시작 (매일 23:50 flush)")


def stop_scheduler():
    """스케줄러 종료"""
    scheduler.shutdown()
