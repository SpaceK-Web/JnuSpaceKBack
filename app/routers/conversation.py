from fastapi import APIRouter
from app.models.schemas import ConversationInput, ExtractionResponse
from app.services.extractor import extract_all
from app.services.validator import validate_critical
from app.services.sentiment import adjust_sentiments
from app.services.redis_buffer import save_to_buffer
from app.services.storage import save_conversation, save_entries

router = APIRouter(prefix="/api/conversation", tags=["대화"])


@router.post("/process", response_model=ExtractionResponse)
async def process_conversation(input_data: ConversationInput):
    """
    대화를 받아서 4단계 파이프라인 실행:
    STEP 1: 선호 키 추출 (enum 강제)
    STEP 2: 자유 키 추출
    STEP 3: 크리티컬 항목 검증
    STEP 4: 감정 후처리
    → MongoDB에 저장
    """

    # STEP 0: 원본 대화 저장
    conversation_id = await save_conversation(
        user_id=input_data.user_id, 
        conversation=input_data.conversation
    )

    # STEP 1 + 2: 추출
    entries = await extract_all(input_data.conversation)

    # STEP 3: 크리티컬 검증
    entries = await validate_critical(entries, input_data.conversation)

    # STEP 4: 감정 후처리
    entries = adjust_sentiments(entries, input_data.conversation)

    # 시스템 알림 분리
    system_alerts = [e for e in entries if e.get("is_system")]
    user_entries = [e for e in entries if not e.get("is_system")]

    # STEP 5: MongoDB에 저장
    await save_entries(
        user_id=input_data.user_id, 
        entries=user_entries, 
        conversation_id=conversation_id
    )

    # TODO: system_alerts가 있으면 보호자에게 즉시 푸시 알림

    return ExtractionResponse(
        user_id=input_data.user_id,
        entries=user_entries,
        total=len(user_entries)
    )
