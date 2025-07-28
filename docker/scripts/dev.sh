#!/bin/bash

# 개발 환경 실행 스크립트

set -e

echo "🚀 AppHub 개발 환경을 시작합니다..."

# Docker Compose로 서비스 시작
cd "$(dirname "$0")/.."
docker-compose -f docker/docker-compose.yml up --build -d

echo "✅ 모든 서비스가 시작되었습니다!"
echo ""
echo "📱 접속 정보:"
echo "  - 웹 앱: http://localhost"
echo "  - AI 서비스 API: http://localhost/api"
echo "  - 헬스 체크: http://localhost/health"
echo ""
echo "📋 로그 확인:"
echo "  - 전체 로그: docker-compose -f docker/docker-compose.yml logs -f"
echo "  - 웹 앱 로그: docker-compose -f docker/docker-compose.yml logs -f web"
echo "  - AI 서비스 로그: docker-compose -f docker/docker-compose.yml logs -f ai-service"
echo ""
echo "🛑 서비스 중지: docker-compose -f docker/docker-compose.yml down" 