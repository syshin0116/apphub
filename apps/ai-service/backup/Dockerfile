# Python LangGraph 서비스용 Dockerfile
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# uv를 사용하여 의존성 설치
RUN pip install uv && uv sync --frozen

# 소스 코드 복사
COPY . .

# 포트 노출 (LangGraph 서비스 포트)
EXPOSE 8000

# 서비스 실행
CMD ["uv", "run", "python", "main.py"] 