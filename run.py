import asyncio
import os
from hypercorn.config import Config
from hypercorn.asyncio import serve

from app.main import app

async def main():
    port = int(os.environ.get("PORT", 8080))
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]  # ← PORT 환경변수 사용!
    await serve(app, config)

asyncio.run(main())