# from fastapi import FastAPI
# from pydantic import BaseModel
# from fastapi.middleware.cors import CORSMiddleware
#
# from ollama import chat
# from ollama import ChatResponse
#
# app = FastAPI()
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://jnu-space-k.vercel.app"],  # React 개발 서버
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# @app.get("/")
# def read_root():
#     return "Main Page"
#
# @app.put("/module/audio/{data_id}")
# def write_audio(data_id: int):
#     return {"text": ""}
#
# @app.get("/module/audio/{data_id}")
# def response(data_id: int):
#     return {"text": ""}
#
#
# @app.get("/interface/request/{days}")
# async def get_data(days: int):
#     # 데이터 반환 로직
#     return {
#         "20260317093817": "example data 1",
#         "20260317093902": "example data 2"
#     }

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.mongodb import connect_mongodb, close_mongodb
from app.database.redis_client import connect_redis, close_redis
from app.database.postgres import connect_postgres, close_postgres
from app.services.scheduler import start_scheduler, stop_scheduler
from app.routers import conversation, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    # await connect_mongodb()
    # await connect_redis()
    await connect_postgres()
    start_scheduler()
    print("🚀 서버 시작 완료")

    yield

    # ── Shutdown ──
    stop_scheduler()
    await close_postgres()
    # await close_redis()
    # await close_mongodb()
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
    allow_origins=["https://jnu-space-k.vercel.app"],  # 프로덕션에서는 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(conversation.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "독거노인 돌봄 시스템 정상 작동 중"}
