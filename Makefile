# AppHub Makefile
.PHONY: help install dev build test clean docker-dev docker-prod logs

# Default settings
DOCKER_COMPOSE_DEV = docker/compose.yaml
DOCKER_COMPOSE_PROD = docker/compose.prod.yaml

# Help
help: ## Show available commands
	@echo "AppHub project management commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Install dependencies
install: ## Install all dependencies
	@echo "📦 Installing dependencies..."
	pnpm install
	@echo "✅ Dependencies installed!"

# Development environment (Docker recommended)
dev: ## Start development environment (using Docker)
	@echo "🚀 Starting development environment..."
	@echo "💡 Using Docker to run the entire environment..."
	make docker-dev

# Local development (individual services)
dev-local: ## Run individual services locally
	@echo "🚀 Starting local development environment..."
	@echo ""
	@echo "📋 Available commands:"
	@echo "  - make web        : Run web app only (http://localhost:3000)"
	@echo "  - make ai-service : Run AI service only (http://localhost:8000)"
	@echo "  - make dev        : Run entire environment with Docker (recommended)"
	@echo ""
	@echo "💡 To run both services:"
	@echo "  1. Terminal 1: make ai-service"
	@echo "  2. Terminal 2: make web"

# Build
build: ## Build the entire project
	@echo "🔨 Building project..."
	pnpm build

# Build Docker images with cache optimization
build-docker: ## Build Docker images with optimized caching
	@echo "🐳 Building Docker images with cache optimization..."
	docker buildx build --cache-from type=gha --cache-to type=gha,mode=max -f apps/ai-service/Dockerfile -t apphub-ai-service:latest apps/ai-service/
	@echo "✅ Docker images built successfully!"

# Test
test: ## Run tests
	@echo "🧪 Running tests..."
	pnpm test

# Clean
clean: ## Clean build files
	@echo "🧹 Cleaning..."
	pnpm clean
	rm -rf node_modules
	rm -rf apps/*/node_modules
	rm -rf packages/*/node_modules

# Docker development environment
docker-dev: ## Start Docker development environment
	@echo "🐳 Starting Docker development environment..."
	docker compose -f $(DOCKER_COMPOSE_DEV) up --build -d
	@echo "✅ Docker development environment started!"
	@echo "📱 Web app: http://localhost"
	@echo "🤖 AI API: http://localhost/api"
	@echo "🔧 Traefik dashboard: http://localhost:8080"
	@echo "🔧 Traefik dashboard (separate host): http://traefik.localhost"

# Docker production environment
docker-prod: ## Start Docker production environment
	@echo "🐳 Starting Docker production environment..."
	docker compose -f $(DOCKER_COMPOSE_PROD) up --build -d
	@echo "✅ Docker production environment started!"

# Stop Docker
docker-down: ## Stop Docker environment
	@echo "🛑 Stopping Docker environment..."
	docker compose -f $(DOCKER_COMPOSE_DEV) down
	docker compose -f $(DOCKER_COMPOSE_PROD) down

# View logs
logs: ## View Docker logs
	@echo "📋 Docker logs:"
	docker compose -f $(DOCKER_COMPOSE_DEV) logs -f

# Run LangGraph service
ai-service: ## Run LangGraph AI service
	@echo "🤖 Starting LangGraph AI service..."
	cd apps/ai-service && uv run langgraph dev --host 0.0.0.0 --port 8000

# Run web app
web: ## Run web application
	@echo "🌐 Starting web application..."
	cd apps/web && pnpm dev

# Add new shadcn-ui component
add-component: ## Add new shadcn-ui component
	@echo "➕ Adding shadcn-ui component..."
	cd apps/web && pnpm dlx shadcn@latest add $(COMPONENT)

# Database migration (if needed)
migrate: ## Run database migration
	@echo "🗄️ Running database migration..."
	# Add migration commands here

# Environment setup
setup: ## Initialize development environment
	@echo "⚙️ Setting up development environment..."
	make install
	@echo "✅ Setup complete!"

# Start full development environment
start: ## Start full development environment (using Docker)
	@echo "🚀 Starting full development environment..."
	make install
	make docker-dev
	@echo "✅ All services started!"
	@echo "📱 Web app: http://localhost"
	@echo "🤖 AI service: http://localhost/api"
	@echo "📋 View logs: make logs"

# Start local full development environment
start-local: ## Start full development environment locally
	@echo "🚀 Starting local full development environment..."
	make install
	@echo ""
	@echo "📋 Run services with these commands:"
	@echo "  Terminal 1: make ai-service"
	@echo "  Terminal 2: make web"
	@echo ""
	@echo "💡 Or use Docker: make dev" 