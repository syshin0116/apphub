# AppHub Makefile
.PHONY: help install dev build test clean docker-dev docker-prod logs

# 기본값 설정
DOCKER_COMPOSE_DEV = docker/docker-compose.yml
DOCKER_COMPOSE_PROD = docker/docker-compose.prod.yml

# 도움말
help: ## 사용 가능한 명령어들을 보여줍니다
	@echo "AppHub 프로젝트 관리 명령어:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 의존성 설치
install: ## 모든 의존성을 설치합니다
	@echo "📦 의존성 설치 중..."
	pnpm install
	@echo "✅ 의존성 설치 완료!"

# 개발 환경 (Docker 권장)
dev: ## 개발 환경을 시작합니다 (Docker 사용)
	@echo "🚀 개발 환경 시작 중..."
	@echo "💡 Docker를 사용하여 전체 환경을 실행합니다..."
	make docker-dev

# 로컬 개발 (개별 서비스)
dev-local: ## 로컬에서 개별 서비스를 실행합니다
	@echo "🚀 로컬 개발 환경 시작 중..."
	@echo ""
	@echo "📋 사용 가능한 명령어:"
	@echo "  - make web        : 웹 앱만 실행 (http://localhost:3000)"
	@echo "  - make ai-service : AI 서비스만 실행 (http://localhost:8000)"
	@echo "  - make dev        : Docker로 전체 환경 실행 (권장)"
	@echo ""
	@echo "💡 두 서비스를 모두 실행하려면:"
	@echo "  1. 터미널 1: make ai-service"
	@echo "  2. 터미널 2: make web"

# 빌드
build: ## 전체 프로젝트를 빌드합니다
	@echo "🔨 프로젝트 빌드 중..."
	pnpm build

# 테스트
test: ## 테스트를 실행합니다
	@echo "🧪 테스트 실행 중..."
	pnpm test

# 정리
clean: ## 빌드 파일들을 정리합니다
	@echo "🧹 정리 중..."
	pnpm clean
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf packages/*/node_modules

# Docker 개발 환경
docker-dev: ## Docker로 개발 환경을 시작합니다
	@echo "🐳 Docker 개발 환경 시작 중..."
	docker-compose -f $(DOCKER_COMPOSE_DEV) up --build -d
	@echo "✅ Docker 개발 환경이 시작되었습니다!"
	@echo "📱 접속: http://localhost"

# Docker 프로덕션 환경
docker-prod: ## Docker로 프로덕션 환경을 시작합니다
	@echo "🐳 Docker 프로덕션 환경 시작 중..."
	docker-compose -f $(DOCKER_COMPOSE_PROD) up --build -d
	@echo "✅ Docker 프로덕션 환경이 시작되었습니다!"

# Docker 중지
docker-down: ## Docker 환경을 중지합니다
	@echo "🛑 Docker 환경 중지 중..."
	docker-compose -f $(DOCKER_COMPOSE_DEV) down
	docker-compose -f $(DOCKER_COMPOSE_PROD) down

# 로그 확인
logs: ## Docker 로그를 확인합니다
	@echo "📋 Docker 로그:"
	docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f

# LangGraph 서비스 실행
ai-service: ## LangGraph AI 서비스를 실행합니다
	@echo "🤖 LangGraph AI 서비스 시작 중..."
	cd apps/ai-service && uv run langgraph dev --host 0.0.0.0 --port 8000

# 웹 앱 실행
web: ## 웹 앱을 실행합니다
	@echo "🌐 웹 앱 시작 중..."
	cd apps/web && pnpm dev

# 새 shadcn-ui 컴포넌트 추가
add-component: ## 새로운 shadcn-ui 컴포넌트를 추가합니다
	@echo "➕ shadcn-ui 컴포넌트 추가 중..."
	cd apps/web && pnpm dlx shadcn@latest add $(COMPONENT)

# 데이터베이스 마이그레이션 (필요시)
migrate: ## 데이터베이스 마이그레이션을 실행합니다
	@echo "🗄️ 데이터베이스 마이그레이션 중..."
	# 여기에 마이그레이션 명령어 추가

# 환경 설정
setup: ## 개발 환경을 초기 설정합니다
	@echo "⚙️ 개발 환경 설정 중..."
	make install
	@echo "✅ 설정 완료!"

# 전체 개발 환경 시작
start: ## 전체 개발 환경을 시작합니다 (Docker 사용)
	@echo "🚀 전체 개발 환경 시작 중..."
	make install
	make docker-dev
	@echo "✅ 모든 서비스가 시작되었습니다!"
	@echo "📱 웹 앱: http://localhost"
	@echo "🤖 AI 서비스: http://localhost/api"
	@echo "📋 로그 확인: make logs"

# 로컬 전체 개발 환경 시작
start-local: ## 로컬에서 전체 개발 환경을 시작합니다
	@echo "🚀 로컬 전체 개발 환경 시작 중..."
	make install
	@echo ""
	@echo "📋 다음 명령어로 서비스를 실행하세요:"
	@echo "  터미널 1: make ai-service"
	@echo "  터미널 2: make web"
	@echo ""
	@echo "💡 또는 Docker를 사용하려면: make dev" 