import httpx
from typing import Optional
from app.config import settings


class LLMService:
    """OpenAI 또는 Ollama를 추상화한 LLM 서비스"""

    @staticmethod
    async def extract_preferred_keys(conversation: str) -> dict:
        """Preferred keys 추출"""
        if settings.LLM_PROVIDER == "ollama":
            return await LLMService._ollama_extract(conversation)
        else:
            return await LLMService._openai_extract(conversation)

    @staticmethod
    async def _ollama_extract(conversation: str) -> dict:
        """Ollama를 사용한 추출"""
        prompt = f"""다음 대화에서 JSON 형식으로 정보를 추출하세요.
        
대화:
{conversation}

응답은 반드시 유효한 JSON이어야 합니다:
{{
    "medication": [],
    "meals": [],
    "health": {{}},
    "emotion": ""
}}
"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                }
            )
            result = response.json()
            # Ollama의 응답에서 JSON 추출
            import json
            import re
            text = result.get("response", "")
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

    @staticmethod
    async def _openai_extract(conversation: str) -> dict:
        """OpenAI를 사용한 추출 (기존 코드)"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        # 기존 OpenAI 호출 로직...
        pass
