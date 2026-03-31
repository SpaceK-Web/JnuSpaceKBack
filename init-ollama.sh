#!/bin/bash
# Ollama 모델 초기화 스크립트
# Docker Compose 실행 후 한 번만 실행

echo "🦙 Ollama 모델 다운로드 시작..."

# mistral 모델 다운로드
ollama pull mistral

# 필요시 다른 모델도 추가
# ollama pull llama3
# ollama pull qwen2

echo "✅ 모델 다운로드 완료!"

# 설치된 모델 목록 확인
ollama list