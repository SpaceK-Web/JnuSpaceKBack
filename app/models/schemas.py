from pydantic import BaseModel
from typing import Optional


class EntryResponse(BaseModel):
    key: str
    value: str
    detail: Optional[str] = None
    time: Optional[str] = None
    sentiment: str
    is_system: bool = False
    description: Optional[str] = None


# ── ABSA (측면 기반 감성 분석) 스키마 ──────────────────────────

class AspectAnalysis(BaseModel):
    aspect: str
    sentiment: str          # "positive" | "negative" | "neutral"
    target_keyword: str
    nuance_note: Optional[str] = None  # 뉘앙스 감지 시만 포함


class TextAnalysisResult(BaseModel):
    text: str
    overall_sentiment: str  # "positive" | "negative" | "neutral" | "warning"
    aspects: list[AspectAnalysis]


class AudioProcessResponse(BaseModel):
    user_id: str
    analysis: TextAnalysisResult
