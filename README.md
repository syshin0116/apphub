# AppHub

A unified platform for personal projects with integrated AI services, authentication, and shared infrastructure.

## Overview

AppHub is a comprehensive infrastructure platform designed to eliminate repetitive development tasks across multiple personal projects. Instead of building authentication, databases, RAG systems, and chatbots from scratch for each project, AppHub provides a centralized foundation that all future projects can build upon.

## Architecture

### Core Components

**LangGraph Platform (Python)**
- Centralized AI services for all projects
- RAG systems and chatbot workflows
- Agent-based interactions and workflows
- RESTful API and WebSocket support
- Project-specific namespacing

**Web Platform (NextJS/React)**
- Unified dashboard for all projects
- Common UI/UX components with ShadCN
- Administrative interface
- Project management system
- Responsive design

**Database & Infrastructure (Supabase)**
- PostgreSQL database with real-time features
- Unified authentication system (SSO)
- Role-based access control (RBAC)
- File storage and Edge Functions
- Redis caching for sessions and API responses

## Key Features

### Shared Infrastructure
- Single Sign-On (SSO) across all projects
- Centralized user management and permissions
- Common database and caching layer
- Integrated monitoring and logging

### AI Services
- Unified RAG system for all projects
- Customizable chatbot platform
- Shared agent workflows
- LangGraph CLI for API deployment

### Development Benefits
- DRY principle implementation
- Reduced development time
- Consistent user experience
- Cost optimization through shared resources
- Simplified maintenance and updates

## Technology Stack

- **AI/ML Backend**: Python, LangGraph, LangChain, uv
- **Web Frontend**: NextJS, React, TypeScript, ShadCN UI, pnpm
- **Database**: Supabase (PostgreSQL), Redis
- **Authentication**: Supabase Auth
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Build Tools**: Turborepo, Make, pnpm workspaces
- **Deployment**: Docker containers, GCP (initial), Home Server (future)

## Project Structure

```
AppHub
├── langgraph-server/     # Python AI services
├── web-platform/         # NextJS frontend
├── shared/              # Common utilities and types
├── projects/            # Individual project modules
│   ├── project-a/
│   ├── project-b/
│   └── ...
└── docs/               # Documentation
```

## Development Roadmap

### Phase 1: GCP Infrastructure Setup
- GCP project setup with free tier
- Basic LangGraph server deployment
- NextJS platform foundation
- Supabase integration

### Phase 2: Core Services Development
- Authentication system implementation
- Dashboard UI development
- Basic RAG system setup
- Project management interface

### Phase 3: Production Readiness
- Performance optimization
- Security hardening
- Monitoring and logging
- First project migration

### Phase 4: Home Server Migration
- Hardware preparation
- Network configuration
- Gradual migration from cloud

## Why This Architecture

### Technical Decision
While JavaScript/TypeScript-based LLM services (Vercel AI SDK, LangChain.js) offer excellent web integration, the latest AI features and research typically debut in the Python ecosystem first. LangGraph CLI enables clean separation between AI services and web applications while leveraging the most advanced capabilities.

### Scalability Strategy
This microservices approach allows each component to be optimized for its specific purpose:
- AI logic utilizes Python's rich ecosystem
- Web interface leverages NextJS's performance
- Database operations benefit from Supabase's managed services

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Supabase account
- GCP account (for initial deployment)

### Installation

1. Clone the repository
```bash
git clone https://github.com/[username]/apphub.git
cd apphub
```

2. Install dependencies
```bash
# Frontend
cd web-platform
npm install

# Backend
cd ../langgraph-server
pip install -r requirements.txt
```

3. Environment setup
```bash
cp .env.example .env
# Configure your environment variables
```

=======
├── apps/
│   ├── ai-service/          # LangGraph AI 서비스
│   │   ├── src/agent/       # LangGraph 에이전트
│   │   ├── tests/           # 테스트
│   │   ├── pyproject.toml   # Python 의존성
│   │   ├── uv.lock          # uv 잠금 파일
│   │   ├── langgraph.json   # LangGraph 설정
│   │   ├── Dockerfile       # Docker 설정
│   │   └── .venv/           # 가상환경
│   └── web/                # Next.js + shadcn-ui 프론트엔드
│       ├── app/             # Next.js App Router
│       ├── components/      # React 컴포넌트
│       ├── package.json     # Node.js 의존성
│       ├── Dockerfile       # Docker 설정
│       └── ...
├── packages/
│   ├── eslint-config/      # 공유 ESLint 설정
│   ├── typescript-config/  # 공유 TypeScript 설정
│   └── ui/                 # shadcn-ui 컴포넌트
├── docker/                 # Docker 관련 파일들
│   ├── docker-compose.yml      # 개발용 docker-compose
│   ├── docker-compose.prod.yml # 프로덕션용 docker-compose
│   ├── nginx/                  # Nginx 설정
│   └── scripts/                # Docker 스크립트
├── logs/                   # 로그 디렉토리
│   ├── ai-service/
│   ├── web/
│   └── nginx/
├── docs/                   # 프로젝트 문서
├── README.md
├── Makefile                # 프로젝트 관리 명령어
├── package.json            # 루트 package.json
├── pnpm-workspace.yaml     # pnpm workspace 설정
└── turbo.json              # Turborepo 설정
```

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- uv (Python package manager)
- pnpm (Node.js package manager)
- Docker & Docker Compose
- Make (optional, but recommended)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/[username]/apphub.git
cd apphub
```

2. **Quick Start (권장)**
```bash
# 전체 개발 환경 시작 (Docker 사용)
make start

# 또는 개별 명령어로
make install  # 의존성 설치
make dev      # Docker로 전체 환경 실행
```

3. **로컬 개발 (선택사항)**
```bash
# 의존성 설치
pnpm install

# 개별 서비스 실행
make web          # 웹 앱 (http://localhost:3000)
make ai-service   # AI 서비스 (http://localhost:8000)
```

### 🔧 Available Commands

```bash
# 도움말
make help

# 개발 환경
make dev          # Docker로 전체 환경 실행
make start        # 설치 + Docker 환경 실행
make web          # 웹 앱만 실행
make ai-service   # AI 서비스만 실행

# Docker 관리
make docker-dev   # Docker 개발 환경 (compose.yaml)
make docker-prod  # Docker 프로덕션 환경 (compose.prod.yaml)
make docker-down  # Docker 환경 중지
make logs         # Docker 로그 확인

# 프로젝트 관리
make build        # 전체 프로젝트 빌드
make test         # 테스트 실행
make clean        # 빌드 파일 정리
```

### pnpm 스크립트 사용
```bash
# 의존성 설치
pnpm install

# 개발 환경
pnpm dev          # 웹 앱 개발 서버
pnpm docker:dev   # Docker로 전체 환경 실행
pnpm docker:logs  # Docker 로그 확인
```

## Features

### Infrastructure
- Monorepo structure with Turborepo + pnpm workspaces
- LangGraph AI service foundation
- NextJS + ShadCN UI web platform
- Docker containerization and development environment
- Traefik reverse proxy with automatic service discovery

### Planned
- Supabase database integration
- Authentication system
- Dashboard UI
- RAG system
- Project management interface

## Why This Architecture

### Technical Decision
While JavaScript/TypeScript-based LLM services (Vercel AI SDK, LangChain.js) offer excellent web integration, the latest AI features and research typically debut in the Python ecosystem first. LangGraph CLI enables clean separation between AI services and web applications while leveraging the most advanced capabilities.

### Scalability Strategy
This microservices approach allows each component to be optimized for its specific purpose:
- AI logic utilizes Python's rich ecosystem
- Web interface leverages NextJS's performance
- Database operations benefit from Supabase's managed services

## 🏗️ Architecture Overview

![](https://i.imgur.com/sg4zOY1.png)


### Service Communication
- **Web App**: Serves UI, handles authentication, makes API calls
- **AI Service**: Processes LangGraph workflows, handles AI logic
- **Traefik**: Reverse proxy, automatic service discovery, SSL termination
- **Supabase**: Database, authentication, real-time features

## Contributing

This is primarily a personal infrastructure project, but contributions and suggestions are welcome through issues and pull requests.

## License

MIT License - see LICENSE file for details.



