FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

# 설치된 라이브러리 확인
RUN pkg-config --list-all | grep -i av

WORKDIR /app

COPY requirements.txt .

# av만 먼저 설치해서 에러 확인
RUN pip install --verbose av

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run.py"]
