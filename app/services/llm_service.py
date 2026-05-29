from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings


async def _call_ollama(system_prompt: str, user_content: str, temp: float) -> str:

    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=temp,
        num_predict=2048,
        client_kwargs={"timeout": 60.0}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        ("user", "{user_content}")
    ])

    chain = prompt | llm | StrOutputParser()

    try:
        return await chain.ainvoke({
            "system_prompt": system_prompt,
            "user_content": user_content
        })
    except Exception as e:
        print(f"Ollama 호출 중 오류 발생: {e}")
        return ""
