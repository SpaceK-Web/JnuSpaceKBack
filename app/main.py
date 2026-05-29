from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.postgres import init_db, close_db
from app.routers import dashboard, chat, audio, test
from app.services.rag_service import build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    await init_db()

    try:
        chunk_count = await build_index()
        print(f"📚 RAG 인덱스 준비 완료: {chunk_count}개 청크")
    except Exception as e:
        print(f"⚠️  RAG 초기화 실패 (Ollama 실행 여부 확인): {e}")

    print("🚀 서버 시작 완료")

    yield

    # ── Shutdown ──
    await close_db()
    print("🛑 서버 종료 완료")


app = FastAPI(
    title="독거노인 돌봄인형 API",
    description="대화에서 의미 있는 정보를 추출하고 보호자에게 제공합니다.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(audio.router)
app.include_router(test.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "독거노인 돌봄 시스템 정상 작동 중"}
