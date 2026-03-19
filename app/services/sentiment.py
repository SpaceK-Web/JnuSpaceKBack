import re


# 규칙 기반 감정 보정 패턴
CONCERN_PATTERNS = [
    (r"혼자.*(편하|좋아|괜찮)", "주의", "고독감 가능성"),
    (r"자식.*바쁘", "주의", "서운함 가능성"),
    (r"뭐.*그냥.*그래", "주의", "우울감 가능성"),
    (r"아무것도.*아니", "주의", "감정 억제 가능성"),
    (r"안\s*아[파프]", "주의", "통증 부정 가능성"),
    (r"죽고\s*싶", "위험", "자살 관련 표현"),
    (r"살아서\s*뭐\s*하", "위험", "자살 관련 표현"),
    (r"없어지고\s*싶", "위험", "자살 관련 표현"),
]


def adjust_sentiments(
        entries: list[dict],
        conversation: str
) -> list[dict]:
    """STEP 4: 규칙 기반 감정 후처리"""

    for entry in entries:
        for pattern, forced_sentiment, reason in CONCERN_PATTERNS:
            if re.search(pattern, conversation):
                current = entry.get("sentiment", "정상")

                # 더 심각한 방향으로만 보정
                severity = {"정상": 0, "주의": 1, "위험": 2}
                if severity.get(forced_sentiment, 0) > severity.get(current, 0):
                    entry["sentiment"] = forced_sentiment
                    entry["_sentiment_adjusted"] = True
                    entry["_adjustment_reason"] = reason

    # ── 위험 감지 시 즉시 알림 플래그 ──
    has_danger = any(e.get("sentiment") == "위험" for e in entries)
    if has_danger:
        entries.append({
            "key": "_시스템알림",
            "value": "위험 감정 감지됨 - 보호자 즉시 알림 필요",
            "sentiment": "위험",
            "is_system": True
        })

    return entries
