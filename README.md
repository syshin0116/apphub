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

- **AI/ML Backend**: Python, LangGraph, LangChain
- **Web Frontend**: NextJS, React, TypeScript, ShadCN UI
- **Database**: Supabase (PostgreSQL), Redis
- **Authentication**: Supabase Auth
- **Deployment**: GCP (initial), Home Server (future)

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

4. Development setup
```bash
# Start frontend
npm run dev

# Start LangGraph server
langgraph dev
```

## Contributing

This is primarily a personal infrastructure project, but contributions and suggestions are welcome through issues and pull requests.

## License

MIT License - see LICENSE file for details.

## Documentation

Detailed documentation is available in the `/docs` directory, including:
- API specifications
- Deployment guides
- Architecture decisions
- Project integration examples

