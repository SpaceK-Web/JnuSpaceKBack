import json
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# 2차 검증이 필요한 크리티컬 키
CRITICAL_KEYS = {
    "아침약복용", "점심약복용", "저녁약복용",
    "혈압", "혈당", "낙상", "통증"
}


async def validate_critical(
        entries: list[dict],
        conversation: str
) -> list[dict]:
    """STEP 3: 크리티컬 항목 2차 검증"""

    critical_items = [e for e in entries if e["key"] in CRITICAL_KEYS]

    if not critical_items:
        return entries

    items_json = json.dumps(critical_items, ensure_ascii=False, indent=2)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""
당신은 독거노인 돌봄 시스템의 검증기입니다.
원본 대화와 추출 결과를 비교해서 정확성을 검증하세요.

## 특히 주의할 점
- "약을 먹었다" vs "약을 먹어야 하는데 깜빡했다" 구분
- "혈압이 높다" vs "혈압을 쟀다" 구분
- "넘어졌다" vs "넘어질 뻔했다" 구분
- 실제로 한 것과 할 예정인 것 구분

원본 대화:
{conversation}

검증 대상:
{items_json}
"""
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "validation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key": {"type": "string"},
                                    "original_value": {"type": "string"},
                                    "is_correct": {"type": "boolean"},
                                    "corrected_value": {"type": "string"},
                                    "reason": {"type": "string"}
                                },
                                "required": [
                                    "key", "original_value",
                                    "is_correct", "corrected_value",
                                    "reason"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["results"],
                    "additionalProperties": False
                }
            }
        },
        temperature=0.0
    )

    validations = json.loads(response.choices[0].message.content)

    # 교정 맵 생성
    correction_map = {
        v["key"]: {
            "value": v["corrected_value"],
            "reason": v["reason"]
        }
        for v in validations["results"]
        if not v["is_correct"]
    }

    # 교정 적용
    for entry in entries:
        if entry["key"] in correction_map:
            entry["value"] = correction_map[entry["key"]]["value"]
            entry["_corrected"] = True
            entry["_correction_reason"] = correction_map[entry["key"]]["reason"]

    return entries
