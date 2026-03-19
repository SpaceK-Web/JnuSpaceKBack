import json
import re
import httpx
from typing import Optional
from app.config import settings
from app.services.preferred_keys import get_key_names, get_keys_with_descriptions


# ──────────────────────────────────────
# 한국 고령자 표현 사전
# ──────────────────────────────────────
ELDERLY_EXPRESSIONS = """
다음은 한국 고령자가 자주 쓰는 표현과 실제 의미입니다:

[건강]
- "띵하다", "멍하다" → 두통, 어지러움
- "쑤시다", "결린다" → 관절통, 근통
- "입맛이 없다" → 식욕부진 (주의 필요)
- "기운이 없다", "맥이 없다" → 무기력감 (주의 필요)
- "가슴이 답답하다" → 흉통 또는 불안

[감정]
- "괜찮아", "혼자가 편해" → 외로움 가능성
- "뭐 그냥 그래" → 우울감 가능성
- "자식들 바쁘지 뭐" → 서운함
- "죽고 싶다", "살아서 뭐하나" → 위험 (즉시 알림)

[약/건강]
- "그거", "그 알약" → 처방약 가능성
- "안 먹었나? 기억이..." → 미복용 가능성 높음
- "깜빡했네" → 미복용
"""


async def _call_ollama(system_prompt: str, user_content: str, temperature: float = 0.3) -> str:
    """Ollama API 호출 (공통 함수)"""

    if settings.LLM_PROVIDER != "ollama":
        # OpenAI fallback (선택사항)
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

    # Ollama 호출
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": temperature,
                "stream": False
            }
        )
        result = response.json()
        return result.get("message", {}).get("content", "")


def _extract_json_from_text(text: str) -> dict:
    """텍스트에서 JSON 추출 (정규식 사용)"""
    # JSON 블록 찾기
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return {"items": []}


async def extract_preferred(conversation: str) -> list[dict]:
    """STEP 1: 선호 키 강제 추출"""

    preferred_keys = get_key_names()
    key_descriptions = get_keys_with_descriptions()
    key_list = ", ".join(f'"{k}"' for k in preferred_keys)

    system_prompt = f"""
당신은 독거노인 돌봄 시스템의 정보 추출기입니다.
어르신과의 대화에서 아래 항목에 해당하는 정보가 있는지 판단하세요.

{ELDERLY_EXPRESSIONS}

## 선호 키 설명
{key_descriptions}

## 규칙
1. 대화에서 직접 언급된 것만 반환하세요.
2. 추측하지 마세요.
3. "깜빡했다", "안 먹었다" 등은 "미복용"으로 기록하세요.
4. value는 핵심 내용만 간결하게 쓰세요.
5. time은 언급된 시간이 있으면 기록하세요.

## 가능한 키 목록
{key_list}

## 응답 형식 (JSON만 반환, 설명은 하지 마세요)
{{
    "items": [
        {{
            "key": "medication_morning",
            "mentioned": true,
            "value": "고혈압약",
            "detail": "식후 30분",
            "time": "09:00",
            "sentiment": "정상"
        }}
    ]
}}
"""

    user_content = f"대화 내용:\n{conversation}"

    response_text = await _call_ollama(system_prompt, user_content, temperature=0.1)
    result = _extract_json_from_text(response_text)

    return [
        {
            "key": item["key"],
            "value": item["value"],
            "detail": item.get("detail") or None,
            "time": item.get("time") or None,
            "sentiment": item.get("sentiment", "정상"),
            "is_custom": False
        }
        for item in result.get("items", [])
        if item.get("mentioned") is True
    ]


async def extract_custom(conversation: str) -> list[dict]:
    """STEP 2: 자유 키 추출 (선호 키에 없는 새 정보)"""

    preferred_keys = get_key_names()
    key_list = ", ".join(f'"{k}"' for k in preferred_keys)

    system_prompt = f"""
당신은 독거노인 돌봄 시스템의 정보 추출기입니다.

{ELDERLY_EXPRESSIONS}

아래 기존 키에 해당하지 않는 새로운 정보만 추출하세요.

## 기존 키 (이미 처리됨, 무시):
{key_list}

## 규칙
1. 위 키로 분류 가능한 것은 절대 추출하지 마세요.
2. 새로운 정보가 없으면 items를 빈 배열로 반환하세요.
3. key는 짧은 한국어 (예: "보일러_고장", "가스비_비쌈")
4. description은 이 키가 무엇을 의미하는지 한 문장 설명

## 응답 형식 (JSON만 반환)
{{
    "items": [
        {{
            "key": "보일러_고장",
            "description": "보일러가 고장 났거나 난방이 안 됨",
            "value": "보일러에서 소리 나고 물이 안 나옴",
            "detail": "수리 필요",
            "time": null,
            "sentiment": "주의"
        }}
    ]
}}
"""

    user_content = f"대화 내용:\n{conversation}"

    response_text = await _call_ollama(system_prompt, user_content, temperature=0.2)
    result = _extract_json_from_text(response_text)

    return [
        {
            "key": item["key"],
            "value": item["value"],
            "detail": item.get("detail") or None,
            "time": item.get("time") or None,
            "sentiment": item.get("sentiment", "정상"),
            "description": item.get("description", ""),
            "is_custom": True
        }
        for item in result.get("items", [])
    ]


async def extract_all(conversation: str) -> list[dict]:
    """STEP 1 + STEP 2 통합 실행"""
    preferred = await extract_preferred(conversation)
    custom = await extract_custom(conversation)
    return preferred + custom


async def validate_critical(extracted_items: list[dict]) -> list[dict]:
    """STEP 3: 위험 항목 검증 (False Positive 제거)"""

    critical_keys = ["medication", "blood_pressure", "fall"]
    critical_items = [item for item in extracted_items if any(k in item["key"] for k in critical_keys)]

    if not critical_items:
        return extracted_items

    # 높은 confidence를 위해 다시 한 번 검증
    system_prompt = f"""
당신은 의료 정보 검증 전문가입니다.
아래 정보가 정말로 맞는지 확인하세요. False Positive를 제거하세요.

예시:
- "약을 안 먹었나? 기억이 안 나는데" → 미복용 (맞음)
- "약을 먹지 말라고 했나?" → 먹지 말라는 지시 (약복용 아님)
- "우울해서 죽고 싶어" → 위험 (맞음)
- "죽고 싶으면 죽어야지, 난 안 그래" → 농담/거부 (위험 아님)

검증할 항목: {json.dumps(critical_items, ensure_ascii=False)}
"""

    user_content = "위의 항목들이 정말 맞는지 검증해주세요. 확신이 없으면 False Positive로 표시하세요."

    response_text = await _call_ollama(system_prompt, user_content, temperature=0.0)
    # 검증 결과는 자유 형식이므로 신뢰도 점수 추가

    return extracted_items
