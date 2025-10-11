# AsyncPostgresSaver Checkpointer 설정 완료

## ✅ 완료된 작업

### 1. Checkpointer 테이블 생성
AsyncPostgresSaver가 필요로 하는 4개의 테이블이 PostgreSQL 18에 성공적으로 생성되었습니다:

- ✅ **checkpoints** - 메인 checkpoint 데이터 저장 (JSONB)
- ✅ **checkpoint_blobs** - 큰 바이너리 데이터 저장 (BYTEA)
- ✅ **checkpoint_writes** - checkpoint 쓰기 작업 추적
- ✅ **checkpoint_migrations** - 마이그레이션 버전 관리 (10개 완료)

### 2. 초기화 스크립트 생성
`scripts/init_checkpointer.py` 스크립트가 생성되었습니다:
- AsyncPostgresSaver.setup()을 실행하여 테이블 생성
- 10개의 마이그레이션 자동 실행
- 테이블 생성 확인 및 검증

### 3. graph.py 수정
LangGraph Platform/Server에 맞게 수정되었습니다:
- ❌ 수동 setup() 호출 제거 (잘못된 방법)
- ✅ `checkpointer_conn_string` 파라미터 사용 (올바른 방법)
- ✅ LangGraph Platform이 자동으로 checkpointer 관리

### 4. 문서화
- `CHECKPOINTER.md`: 상세한 설정 가이드 및 참고 자료
- 이 파일: 설정 완료 요약

## 📊 테이블 구조 확인

```bash
# 테이블 목록 확인
docker exec apphub-postgres psql -U apphub -d apphub -c "\dt checkpoint*"

# 결과:
                 List of tables
 Schema |         Name          | Type  | Owner
--------+-----------------------+-------+--------
 public | checkpoint_blobs      | table | apphub
 public | checkpoint_migrations | table | apphub
 public | checkpoint_writes     | table | apphub
 public | checkpoints           | table | apphub
```

## 🎯 사용 방법

### 신규 설정 시 (한 번만 실행)

```bash
cd apps/ai-service
uv run python scripts/init_checkpointer.py
```

### LangGraph Server 실행

```bash
cd apps/ai-service
uv run langgraph dev
```

LangGraph Platform이 자동으로:
1. `checkpointer_conn_string`을 사용하여 AsyncPostgresSaver 연결
2. 각 대화를 `thread_id`로 구분하여 checkpoint 저장
3. 대화 재개 시 이전 상태를 자동으로 로드

## 🔍 동작 확인

### 1. 마이그레이션 버전 확인

```bash
docker exec apphub-postgres psql -U apphub -d apphub -c "SELECT * FROM checkpoint_migrations ORDER BY v"
```

**기대 결과**: v=0부터 v=9까지 10개의 행

### 2. Checkpoint 데이터 확인

LangGraph Server 실행 후 대화를 진행하면:

```bash
docker exec apphub-postgres psql -U apphub -d apphub -c "
SELECT
    thread_id,
    checkpoint_id,
    jsonb_pretty(metadata) as metadata
FROM checkpoints
LIMIT 5"
```

## 💡 핵심 개념

### AsyncPostgresSaver 사용 시 주의사항

1. **자동 초기화**
   - LangGraph Platform을 사용할 때는 `checkpointer.setup()`을 수동 호출하지 않음
   - 초기화 스크립트로 한 번만 테이블 생성
   - 이후 LangGraph가 자동으로 관리

2. **Connection String 전달**
   ```python
   graph = create_agent(
       model="openai:gpt-4.1",
       tools=tools,
       checkpointer_conn_string=database_url,  # ← 이 방법 사용
       # checkpointer=checkpointer  # ← 이 방법 사용 안 함
   )
   ```

3. **Context Manager**
   - `AsyncPostgresSaver.from_conn_string()`은 async context manager
   - 직접 사용할 때는 `async with` 필수
   - LangGraph Platform이 내부적으로 처리

## 🚀 PostgreSQL 18 비동기 I/O

Checkpointer는 PostgreSQL 18의 비동기 I/O를 활용합니다:

- **io_method**: `worker` (기본값) 또는 `io_uring` (Linux 5.1+)
- **effective_io_concurrency**: 16 (기본값, 이전 버전은 1)
- **성능 향상**: 최대 2.8배 빠른 디스크 읽기

이는 대화 기록이 많아질수록 더욱 효과적입니다.

## 📁 관련 파일

```
apps/ai-service/
├── src/agent/graph.py              # LangGraph 에이전트 정의 (checkpointer 설정)
├── scripts/init_checkpointer.py    # Checkpointer 테이블 초기화 스크립트
├── CHECKPOINTER.md                 # 상세 가이드
└── SETUP_SUMMARY.md                # 이 파일
```

## 🔗 참고 자료

- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [AsyncPostgresSaver API](https://langchain-ai.github.io/langgraph/reference/checkpoints/)
- [PostgreSQL 18 Async I/O](https://digitalbourgeois.tistory.com/1218)

---

**작성일**: 2025-10-11
**PostgreSQL 버전**: 18 (pgvector/pgvector:pg18-bookworm)
**LangGraph 버전**: >=1.0.0a4
