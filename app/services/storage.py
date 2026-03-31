"""
데이터 저장 서비스
- 원본 대화 저장
- 추출된 entries 저장
- 일일 기록 관리
"""
from datetime import datetime
from app.database.mongodb import get_db


async def save_conversation(user_id: str, conversation: str, metadata: dict = None) -> str:
    """
    원본 대화를 MongoDB에 저장
    
    Args:
        user_id: 사용자 ID
        conversation: 대화 텍스트
        metadata: 추가 메타데이터 (선택)
    
    Returns:
        저장된 문서 ID
    """
    db = get_db()
    
    document = {
        "user_id": user_id,
        "conversation": conversation,
        "timestamp": datetime.utcnow(),
        "metadata": metadata or {}
    }
    
    result = await db.conversations.insert_one(document)
    return str(result.inserted_id)


async def save_entries(user_id: str, entries: list[dict], conversation_id: str = None) -> str:
    """
    추출된 entries를 MongoDB에 저장
    
    Args:
        user_id: 사용자 ID
        entries: 추출된 정보 리스트
        conversation_id: 원본 대화 ID (선택)
    
    Returns:
        저장된 문서 ID
    """
    db = get_db()
    
    document = {
        "user_id": user_id,
        "entries": entries,
        "conversation_id": conversation_id,
        "timestamp": datetime.utcnow(),
        "date": datetime.utcnow().strftime("%Y-%m-%d")
    }
    
    result = await db.extracted_entries.insert_one(document)
    return str(result.inserted_id)


async def save_to_daily_record(user_id: str, entries: list[dict], date_str: str = None) -> str:
    """
    일일 기록으로 저장 (upsert)
    같은 날짜에 이미 기록이 있으면 append
    
    Args:
        user_id: 사용자 ID
        entries: 추출된 정보 리스트
        date_str: 날짜 (YYYY-MM-DD), 기본값은 오늘
    
    Returns:
        저장된 문서 ID
    """
    db = get_db()
    
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    # 같은 날짜의 기록이 있는지 확인 후 append 또는 새로 생성
    result = await db.daily_records.update_one(
        {"user_id": user_id, "date": date_str},
        {
            "$push": {"entries": {"$each": entries}},
            "$setOnInsert": {"created_at": datetime.utcnow()},
            "$set": {"updated_at": datetime.utcnow()}
        },
        upsert=True
    )
    
    return str(result.upserted_id) if result.upserted_id else "updated"


async def get_user_conversations(
    user_id: str, 
    limit: int = 100, 
    skip: int = 0
) -> list[dict]:
    """
    사용자의 대화 기록 조회
    
    Args:
        user_id: 사용자 ID
        limit: 최대 개수
        skip: 건너뛸 개수
    
    Returns:
        대화 기록 리스트
    """
    db = get_db()
    
    cursor = db.conversations.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).skip(skip).limit(limit)
    
    return await cursor.to_list(length=limit)


async def get_user_entries_by_date(
    user_id: str, 
    start_date: str, 
    end_date: str
) -> list[dict]:
    """
    날짜 범위로 사용자의 entries 조회
    
    Args:
        user_id: 사용자 ID
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
    
    Returns:
        일일 기록 리스트
    """
    db = get_db()
    
    cursor = db.daily_records.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }
    ).sort("date", -1)
    
    return await cursor.to_list(length=100)


async def search_entries_by_key(user_id: str, key: str) -> list[dict]:
    """
    특정 키로 entries 검색
    
    Args:
        user_id: 사용자 ID
        key: 검색할 키 (예: "아침식사", "혈압")
    
    Returns:
        검색 결과 리스트
    """
    db = get_db()
    
    cursor = db.daily_records.find(
        {
            "user_id": user_id,
            "entries.key": key
        }
    ).sort("date", -1)
    
    return await cursor.to_list(length=50)


async def get_recent_sentiments(user_id: str, days: int = 7) -> list[dict]:
    """
    최근 N일간의 감정 데이터 조회
    
    Args:
        user_id: 사용자 ID
        days: 조회할 일수
    
    Returns:
        감정 데이터 리스트
    """
    db = get_db()
    
    from datetime import timedelta
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor = db.daily_records.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_date}
        }
    ).sort("date", 1)
    
    records = await cursor.to_list(length=days)
    
    # 감정 데이터 추출
    sentiments = []
    for record in records:
        for entry in record.get("entries", []):
            if "sentiment" in entry:
                sentiments.append({
                    "date": record["date"],
                    "key": entry.get("key"),
                    "sentiment": entry.get("sentiment")
                })
    
    return sentiments