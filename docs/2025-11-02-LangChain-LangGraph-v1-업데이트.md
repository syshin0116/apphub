---
title: LangChain v1.0 & LangGraph v1.0 정식 릴리스 적용
date: 2025-11-02
tags:
  - AppHub
  - LangChain
  - LangGraph
  - LangSmith
  - AI
  - v1.0
  - 업데이트
draft: false
enableToc: true
description: LangChain v1.0, LangGraph v1.0 정식 릴리스 및 LangSmith 최신 기능을 AppHub 프로젝트에 적용. 실험적 alpha 버전에서 프로덕션 stable 버전으로 업그레이드
---

> [!success] **프로덕션 레디! LangChain & LangGraph v1.0 Stable**
> 2025년 10월 22일, LangChain과 LangGraph가 동시에 정식 v1.0 stable 릴리스를 달성했다! 이제 프로덕션 환경에서 안심하고 사용할 수 있다.

## 업데이트 배경

### 이전 상태 (Alpha 버전)
- **LangChain**: v1.0.0a14 (alpha, 실험적)
- **LangGraph**: v1.0.0a4 (alpha, 실험적)
- **문서**: "아직 완전히 안정화되지 않았지만..." 표현
- **LangSmith**: 언급 없음

### 현재 상태 (Stable 버전)
- **LangChain**: v1.0.0+ (정식 stable)
- **LangGraph**: v1.0.2 (최신 안정 버전)
- **LangSmith**: Latest (AI 모니터링 필수 도구)
- **출시일**: 2025년 10월 22일
- **검증**: Uber, LinkedIn, Klarna 등 1년 이상 프로덕션 검증 완료

---

## 주요 변경사항

### 1. LangChain v1.0 정식 릴리스

**새로운 기능:**
- ✅ `create_agent`: 표준 Agent 생성 방식
- ✅ `content_blocks`: 통합 LLM 기능 접근
- ✅ 간소화된 namespace (레거시는 `langchain-classic`으로 이동)
- ✅ **프로덕션 안정성 보장**: v2.0까지 breaking change 없음

**마이그레이션:**
```python
# 이전 (alpha)
from langchain import ...  # 복잡한 import

# 현재 (v1.0 stable)
from langchain.agents import create_agent  # 간결하고 명확
```

### 2. LangGraph v1.0.2 안정화

**버전 히스토리:**
- v1.0.0 (2025-10-17) - 첫 stable 릴리스
- v1.0.1 (2025-10-20) - 버그 수정
- **v1.0.2 (2025-10-29)** - 최신 안정 버전 ⭐

**주요 개선:**
- ✅ 완전한 하위 호환성
- ✅ `langgraph.prebuilt` deprecated → `langchain.agents`로 이동
- ✅ 엔터프라이즈 검증 완료 (1년+ 프로덕션)
- ✅ Durable State Management
- ✅ Human-in-the-loop 패턴

**마이그레이션:**
```python
# 이전 (alpha)
from langgraph.prebuilt import create_react_agent

# 현재 (v1.0 stable)
from langchain.agents import create_agent  # 통합된 방식
```

### 3. LangSmith 통합 추가 (NEW!)

> [!rocket] **2025년 AI 개발 필수 도구**
> LangSmith는 LangGraph/LangChain 기반 AI 에이전트 개발 시 필수적인 Observability 도구다.

**2025년 최신 기능:**
- **Insights Agent** (2025-10): 자동 패턴 분석 및 카테고리화
- **Multi-turn Evals** (2025-10): 멀티턴 대화 품질 평가
- **Cost Tracking**: 실시간 LLM API 비용 추적
- **Trace Logging**: 모든 LLM 호출 자동 추적
- **Thread Concept**: 멀티턴 대화 컨텍스트 관리
- **Auto Export**: 자동 trace 백업
- **Media Support**: 이미지/PDF/오디오 추적

**통합 방법:**
```python
# .env 파일
LANGSMITH_API_KEY=your-api-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=apphub

# Python 코드 (자동 추적)
import os
os.environ["LANGSMITH_TRACING"] = "true"

# LangGraph/LangChain이 자동으로 모든 호출 추적
```

**프로젝트 가치:**
- 🐛 디버깅: 실패한 쿼리 원인 즉시 파악
- 💰 비용 관리: OpenAI/Anthropic API 비용 실시간 모니터링
- 📊 품질 개선: 사용자 피드백 기반 프롬프트 최적화
- 🚀 성능 추적: 응답 시간, 토큰 사용량 분석

---

## 업데이트 내역

### 📄 문서 업데이트

**1. 기술 스택 문서 (2025-10-07-AppHub-구조-및-기술-스택.md)**
- ✅ "실험적" → "정식 stable" 표현 변경
- ✅ v1.0 릴리스 날짜 추가 (2025-10-22)
- ✅ 주요 개선사항 상세 설명
- ✅ LangSmith 섹션 신규 추가
- ✅ 최종 기술 스택 테이블 업데이트

**2. 프로젝트 구조 문서 (2025-10-08-AppHub-프로젝트-구조-설계.md)**
- ✅ 버전 정보 업데이트 (v1.0.2)
- ✅ LangSmith 통합 정보 추가
- ✅ 기술 스택 테이블 업데이트

### 🐍 Python 프로젝트 설정

**pyproject.toml 업데이트:**
```toml
# 이전 (Alpha)
dependencies = [
    "langchain>=1.0.0a14",  # alpha
    "langgraph>=1.0.0a4",   # alpha
    # LangSmith 없음
]

# 현재 (Stable)
dependencies = [
    # Core AI Framework (v1.0 Stable - Released 2025-10-22)
    "langchain>=1.0.0",
    "langgraph>=1.0.2",

    # AI Monitoring & Observability (2025 Latest)
    "langsmith>=0.2.0",

    # LLM Providers
    "langchain-anthropic>=0.3.22",
    "langchain-openai>=0.3.35",
    "openai>=2.2.0",

    # Database & Vector Store
    "asyncpg>=0.30.0",
    "langgraph-checkpoint-postgres>=2.0.0",
    "pgvector>=0.4.1",
    "psycopg[binary]>=3.2.10",

    # Utilities
    "python-dotenv>=1.0.1",
]
```

**프로젝트 메타데이터:**
- 이름: `agent` → `apphub-ai-service`
- 버전: `0.0.1` → `0.1.0`
- 설명: AppHub 맞춤형 설명으로 변경
- 저자: AppHub Team 정보로 업데이트

---

## 마이그레이션 가이드

### 단계 1: 의존성 업데이트

```bash
cd apps/ai-service

# 의존성 재설치
uv sync

# 버전 확인
uv pip list | grep -E "langchain|langgraph|langsmith"
```

**예상 출력:**
```
langchain            1.0.0
langgraph            1.0.2
langsmith            0.2.0
langchain-anthropic  0.3.22
langchain-openai     0.3.35
```

### 단계 2: LangSmith 설정

**환경 변수 추가 (.env):**
```bash
# LangSmith API 키 (https://smith.langchain.com에서 발급)
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=apphub

# 기존 설정
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 단계 3: 코드 업데이트 (필요 시)

**deprecated API 교체:**
```python
# 이전 방식 (deprecated)
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=model,
    tools=tools
)

# 새로운 방식 (v1.0)
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=tools
)
```

**자동 추적 활성화:**
```python
# src/agent/main.py
import os
from dotenv import load_dotenv

load_dotenv()

# LangSmith 자동 추적 (환경변수만 설정하면 됨)
# 모든 LangGraph/LangChain 호출이 자동으로 추적됨
```

### 단계 4: 테스트

```bash
# 개발 서버 실행
uv run langgraph dev

# 테스트
curl http://localhost:2024/health

# LangSmith에서 trace 확인
# https://smith.langchain.com
```

---

## 기대 효과

### 🚀 프로덕션 준비 완료
- ✅ **안정성 보장**: v2.0까지 breaking change 없음
- ✅ **엔터프라이즈 검증**: 대기업 1년+ 프로덕션 검증
- ✅ **장기 지원**: 안심하고 사용 가능

### 🔍 관찰성 향상 (LangSmith)
- 📊 **실시간 모니터링**: 모든 AI 호출 추적
- 🐛 **빠른 디버깅**: 실패 원인 즉시 파악
- 💰 **비용 최적화**: API 비용 실시간 추적
- 📈 **품질 개선**: 데이터 기반 프롬프트 최적화

### 📚 학습 가치
- 🎓 **최신 표준**: 업계 표준 프레임워크 경험
- 🛠️ **프로덕션 패턴**: 실무 베스트 프랙티스 적용
- 🔬 **실험 정신**: 최신 기술 빠른 적용 경험

---

## 다음 단계

### 즉시 적용 가능
1. ✅ 의존성 업데이트 (`uv sync`)
2. ✅ LangSmith 설정 (환경 변수)
3. ✅ 개발 서버 재시작
4. ✅ LangSmith 대시보드 확인

### 향후 계획
- [ ] LangSmith Insights Agent 활용
- [ ] Multi-turn Evals로 대화 품질 평가
- [ ] 비용 최적화 (프롬프트 캐싱, 모델 선택)
- [ ] 프로덕션 배포 (Vercel + Railway)

---

## 참고 자료

### 공식 문서
- [LangChain v1.0 Release Blog](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangChain v1 What's New](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [LangGraph Releases](https://github.com/langchain-ai/langgraph/releases)
- [LangSmith Documentation](https://www.langchain.com/langsmith)
- [Insights Agent & Multi-turn Evals](https://blog.langchain.com/insights-agent-multiturn-evals-langsmith/)

### 업데이트된 프로젝트 문서
- [[2025-10-07-AppHub-구조-및-기술-스택]] - 기술 스택 상세
- [[2025-10-08-AppHub-프로젝트-구조-설계]] - 프로젝트 구조
- [[2025-10-06-AppHub-개인-프로젝트-플랫폼-기획]] - 전체 기획

---

## 회고

### 잘한 점
- ✅ 빠른 업데이트: stable 릴리스 직후 바로 적용
- ✅ 체계적 문서화: 모든 변경사항 상세 기록
- ✅ LangSmith 추가: 필수 도구 선제적 도입

### 배운 점
- 📚 Alpha → Stable 마이그레이션 경험
- 🔍 Observability의 중요성 (LangSmith)
- 🎯 "최신 기술 체험" 철학의 가치

### 다음 목표
**1주일 내 목표:**
- 기본 블로그 검색 RAG 구현
- LangSmith로 품질 모니터링
- 프로덕션 배포 준비

> [!tip] **프로덕션 레디!**
> LangChain v1.0 & LangGraph v1.0의 stable 릴리스로, 이제 AppHub는 엔터프라이즈급 AI 프레임워크 위에서 자신있게 개발할 수 있다. 🚀
