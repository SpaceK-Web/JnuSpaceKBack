import json
import httpx
from app.config import settings

# 2차 검증이 필요한 크리티컬 키
CRITICAL_KEYS = {
    "아침약복용", "점심약복용", "저녁약복용",
    "혈압", "혈당", "낙상", "통증"
}


async def _call_ollama(system_prompt: str, user_content: str) -> str:
    """Ollama API 호출"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.0,
                "stream": False
            }
        )
        result = response.json()
        return result.get("message", {}).get("content", "")


async def validate_critical(
        entries: list[dict],
        conversation: str
) -> list[dict]:
    """STEP 3: 크리티컬 항목 2차 검증"""

    critical_items = [e for e in entries if e["key"] in CRITICAL_KEYS]

    if not critical_items:
        return entries

    items_json = json.dumps(critical_items, ensure_ascii=False, indent=2)

    system_prompt = f"""
당신은 독거노인 돌봄 시스템의 검증기입니다.
원본 대화와 추출 결과를 비교해서 정확성을 검증하세요.

## 특히 주의할 점
- "약을 먹었다" vs "약을 먹어야 하는데 깜빡했다" 구분
- "혈압이 높다" vs "혈압을 쟀다" 구분
- "넘어졌다" vs "넘어질 뻔했다" 구분
- 실제로 한 것과 할 예정인 것 구분

## 응답 형식 (JSON만 반환)
{{
    "results": [
        {{
            "key": "아침약복용",
            "original_value": "혈압약",
            "is_correct": false,
            "corrected_value": "미복용",
            "reason": "깜빡했다고 언급됨"
        }}
    ]
}}
"""

    user_content = f"""원본 대화:
{conversation}

검증 대상:
{items_json}

위의 검증 대상들이 원본 대화와 일치하는지 검증하고 JSON 형식으로 반환하세요."""

    response_text = await _call_ollama(system_prompt, user_content)

    # JSON 추출
    import re
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        validations = json.loads(json_match.group())
    else:
        return entries  # JSON 파싱 실패 시 원본 반환

    # 교정 맵 생성
    correction_map = {}
    for v in validations.get("results", []):
        if not v.get("is_correct", True):
            correction_map[v["key"]] = {
                "value": v.get("corrected_value", ""),
                "reason": v.get("reason", "")
            }

    # 교정 적용
    for entry in entries:
        if entry["key"] in correction_map:
            entry["value"] = correction_map[entry["key"]]["value"]
            entry["_corrected"] = True
            entry["_correction_reason"] = correction_map[entry["key"]]["reason"]

    return entries
