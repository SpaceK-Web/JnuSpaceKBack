from pydantic import BaseModel
from typing import Optional


class ConversationInput(BaseModel):
    user_id: str
    conversation: str


class EntryResponse(BaseModel):
    key: str
    value: str
    detail: Optional[str] = None
    time: Optional[str] = None
    sentiment: str
    is_custom: bool = False
    description: Optional[str] = None


class ExtractionResponse(BaseModel):
    user_id: str
    entries: list[EntryResponse]
    total: int


class DailyRecord(BaseModel):
    user_id: str
    date: str
    entries: list[dict]
