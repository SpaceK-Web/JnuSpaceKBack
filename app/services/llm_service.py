from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from app.config import settings

class PreferredKeys(BaseModel):
    medication: list = Field(default_factory=list, description="복용 약물 목록")
    meals: list = Field(default_factory=list, description="식사 기록 목록")
    health: dict = Field(default_factory=dict, description="건강 상태 세부 정보")
    emotion: str = Field(default="", description="대화에서 나타난 감정 상태")


async def _call_ollama(system_prompt: str, user_content: str, temp: float) -> str:

    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=temp,
        client_kwargs={"timeout": 60.0}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("user", "{user_content}")
    ])

    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser

    try:
        response_text = await chain.ainvoke({
            "system_prompt": system_prompt,
            "user_content": user_content
        })
        return response_text

    except Exception as e:
        print(f"Ollama 호출 중 오류 발생: {e}")
        return ""

class LLMService:

    @staticmethod
    async def extract_preferred_keys(conversation: str) -> dict:

        llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.7,
            format="json"
        )

        parser = JsonOutputParser(pydantic_object=PreferredKeys)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "다음 대화에서 필요한 정보를 추출하여 지정된 JSON 형식으로 응답하세요.\n{format_instructions}"),
            ("user", "대화내용:\n{conversation}")
        ])

        chain = prompt | llm | parser

        try:
            result = await chain.ainvoke({
                "conversation": conversation,
                "format_instructions": parser.get_format_instructions()
            })
            return result

        except Exception as e:
            print(f"LLM 추출 중 오류 발생: {e}")
            return {
                "medication": [],
                "meals": [],
                "health": {},
                "emotion": ""
            }
