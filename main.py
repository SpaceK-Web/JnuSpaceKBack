from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jnu-space-k.vercel.app"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Database:
    datas = {}

    def write(id: int, text: str):
        Database.datas[id] = text

    def read(id: int):
        return Database.datas[id]

class Text(BaseModel): #오디오가 텍스트로 전환
    text: str

@app.get("/")
def read_root():
    return "Main Page"

@app.put("/module/audio/{data_id}")
def write_audio(data_id: int, text: Text):
    Database.write(data_id, text.text)
    return {"text": text.text}

@app.get("/module/audio/{data_id}")
def response(data_id: int):
    return {"text": Database.read(data_id)}


@app.get("/interface/request/{days}")
async def get_data(days: int):
    # 데이터 반환 로직
    return {
        "20260317093817": "example data 1",
        "20260317093902": "example data 2"
    }