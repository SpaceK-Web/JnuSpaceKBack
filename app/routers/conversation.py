from fastapi import APIRouter
from app.models.schemas import ConversationInput, ExtractionResponse
from app.services.extractor import extract_all
from app.services.validator import validate_critical
from app.services.sentiment import adjust_sentiments
from app.services.storage import save_conversation, save_entries

router = APIRouter(prefix="/api/conversation", tags=["대화"])


@router.post("/process", response_model=ExtractionResponse)
async def process_conversation(input_data: ConversationInput):

    conversation_id = await save_conversation(
        user_id=input_data.user_id, 
        conversation=input_data.conversation
    )

    entries = await extract_all(input_data.conversation)
    print(entries)

    entries = await validate_critical(entries, input_data.conversation)
    print(entries)

    entries = adjust_sentiments(entries, input_data.conversation)
    print(entries)

    system_alerts = [e for e in entries if e.get("is_system")]
    user_entries = [e for e in entries if not e.get("is_system")]

    await save_entries(
        user_id=input_data.user_id, 
        entries=user_entries, 
        conversation_id=conversation_id
    )

    # TODO: system_alerts 있으면 보호자 푸시 알람 보내기

    return ExtractionResponse(
        user_id=input_data.user_id,
        entries=user_entries,
        total=len(user_entries)
    )
