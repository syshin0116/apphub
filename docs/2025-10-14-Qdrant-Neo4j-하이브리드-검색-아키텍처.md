---
title: "Qdrant + Neo4j: 하이브리드 검색 아키텍처로의 전환"
date: 2025-10-14
tags:
  - Qdrant
  - Neo4j
  - Vector-Database
  - Graph-Database
  - Hybrid-Search
  - RAG
  - Knowledge-Graph
draft: false
enableToc: true
description: "pgvector에서 Qdrant + Neo4j 조합으로 전환한 이유와 각 검색 방식(키워드, 임베딩, 그래프)의 상호 보완 전략을 다룬다. 벡터 검색, 그래프 탐색, 키워드 매칭을 통합하여 더 강력한 지식 검색 시스템을 구축한다."
published: 2025-10-14
modified: 2025-10-14
---

> [!summary]
>
> [[2025-10-12-pgvector-활용-벡터베이스-구현|이전 pgvector 기반 설계]]에서 **Qdrant + Neo4j** 조합으로 전환했다. pgvector의 장점(PostgreSQL 통합, 트랜잭션 일관성)보다 **전문 벡터 DB의 성능**, **그래프 검색의 관계 탐색 능력**, 그리고 **각 검색 방식의 독립적 확장성**이 더 중요하다고 판단했기 때문이다. 키워드 검색, 임베딩 검색, 그래프 검색은 각각 다른 강점이 있으며, 이들을 결합한 하이브리드 아키텍처가 가장 강력한 검색 경험을 제공한다.

## 전환 배경

### pgvector의 한계

[[2025-10-12-pgvector-활용-벡터베이스-구현|이전 문서]]에서 pgvector를 선택한 이유는 다음과 같았다:

1. **PostgreSQL 통합**: 벡터 + 관계형 데이터를 단일 DB에서 관리
2. **높은 동시접속 처리**: 트래픽이 많을 때 유리
3. **트랜잭션 일관성**: ACID 보장
4. **운영 복잡도 감소**: 별도 벡터 DB 불필요

그러나 실제 프로젝트 요구사항을 더 깊이 분석한 결과, **다음과 같은 문제점**을 발견했다:

#### 1. 벡터 검색 성능이 Qdrant보다 떨어진다

**pgvector의 한계:**
- HNSW 인덱스가 있지만 전문 벡터 DB 대비 성능 차이
- 벡터 연산 최적화가 Qdrant보다 부족
- 필터링 + 벡터 검색 결합 시 성능 저하

**벤치마크 비교 (대략적):**

| 항목 | pgvector | Qdrant | 차이 |
|------|----------|--------|------|
| 검색 속도 (10K 벡터) | ~50ms | ~5ms | **10배** |
| 필터링 + 검색 | ~150ms | ~15ms | **10배** |
| 인덱싱 시간 | 느림 | 빠름 | **2-3배** |
| 메모리 효율 | 보통 | 우수 | - |

#### 2. 그래프 검색이 불가능하다

**필요한 쿼리들:**
- "이 노트와 연결된 모든 노트"
- "두 개념 사이의 최단 경로"
- "가장 많이 링크된 허브 노트"
- "관련 태그 네트워크"

**PostgreSQL의 한계:**
- 재귀 쿼리(WITH RECURSIVE)는 가능하지만 복잡하고 느림
- 그래프 탐색 알고리즘 (PageRank, Community Detection 등) 구현 어려움
- 관계 중심 쿼리에 최적화되지 않음

**대안 고려:**
- **Apache AGE** (PostgreSQL 그래프 확장): 그래프 + 관계형 통합
  - 하지만 성숙도가 Neo4j보다 낮음
  - 커뮤니티, 문서, 도구 부족

#### 3. 각 검색 방식이 독립적으로 확장하기 어렵다

**문제 상황:**
- 벡터 검색만 스케일 업 하고 싶은데 전체 PostgreSQL을 확장해야 함
- 그래프 탐색이 필요한데 PostgreSQL로는 비효율적
- 키워드 검색(FTS) 최적화가 벡터 인덱스와 충돌

**원하는 구조:**
```
독립적인 확장:
├─ Qdrant: 벡터 검색만 집중 (수평 확장 쉬움)
├─ Neo4j: 그래프 탐색만 집중 (관계 중심 쿼리)
└─ PostgreSQL: 메타데이터 + 트랜잭션 (필요시)
```

### 세 가지 검색 방식의 상호 보완

개인적인 직관: **키워드, 임베딩, 그래프 검색은 서로 다른 문제를 해결한다.**

#### 1. 키워드 검색 (BM25, Full-Text Search)

**강점:**
- ✅ 정확한 용어 매칭 ("pgvector 설치 방법")
- ✅ 고유명사, 기술 용어 검색
- ✅ 빠른 속도

**약점:**
- ❌ 의미적 유사성 이해 불가
- ❌ 동의어 처리 어려움
- ❌ "개념적으로 비슷한 문서" 찾기 불가

**예시:**
```
쿼리: "머신러닝 모델 평가"
✅ 매칭: "머신러닝", "모델", "평가" 키워드 포함 문서
❌ 놓침: "딥러닝 성능 측정" (의미는 비슷하지만 키워드 다름)
```

#### 2. 임베딩 검색 (Vector Similarity)

**강점:**
- ✅ 의미적 유사도 이해 ("RAG" ≈ "검색 기반 생성")
- ✅ 다국어 지원 (한국어 → 영어 문서 검색)
- ✅ 개념적 연결 ("Docker" + "컨테이너" 관련성 인식)

**약점:**
- ❌ 정확한 키워드 매칭 약함
- ❌ 특정 날짜, 숫자, 고유명사 검색 부정확
- ❌ 관계나 연결 경로 찾기 불가

**예시:**
```
쿼리: "컨테이너 오케스트레이션"
✅ 매칭: "Kubernetes", "Docker Swarm" (의미적 유사)
❌ 놓침: "정확히 'K8s' 라는 용어 언급" (키워드 부족)
```

#### 3. 그래프 검색 (Relationship Traversal)

**강점:**
- ✅ 관계 탐색 ("X와 Y는 어떻게 연결되어 있나?")
- ✅ 경로 발견 (개념 간 연결 고리)
- ✅ 구조적 패턴 ("가장 중요한 허브 노트")

**약점:**
- ❌ 명시적 링크가 없으면 찾을 수 없음
- ❌ 의미적 유사도는 파악 못함
- ❌ 키워드 기반 필터링 약함

**예시:**
```
쿼리: "Docker와 Kubernetes의 관계"
✅ 매칭: Docker → Container → Kubernetes 경로
❌ 놓침: 링크 없지만 내용상 관련된 문서
```

### 결론: 하이브리드가 답이다

**단일 방식의 한계:**

| 상황 | 키워드만 | 벡터만 | 그래프만 |
|------|---------|--------|---------|
| "pgvector 설치" | ✅ 완벽 | ⚠️ 부정확 | ❌ 불가능 |
| "RAG 개념 설명" | ❌ 동의어 놓침 | ✅ 완벽 | ❌ 불가능 |
| "X와 Y의 연결" | ❌ 불가능 | ⚠️ 부분적 | ✅ 완벽 |

**하이브리드 접근:**

```
User Query: "Docker 관련 학습 경로"
    │
    ├─> [키워드 검색]: "Docker" 키워드 포함 문서
    ├─> [벡터 검색]: "컨테이너 기술" 의미적 유사 문서
    └─> [그래프 검색]: Docker 태그 노트 → 연결된 학습 경로

    결과 융합 (Reranking):
    → 키워드 매칭 + 의미적 유사도 + 관계 경로 고려
```

## 새로운 아키텍처: Qdrant + Neo4j

### 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                   Quartz 블로그 (Markdown)               │
│             content/AI/, Study/, Projects/              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            1. Markdown 파싱 & 전처리                     │
│  - Frontmatter 추출                                     │
│  - 헤딩 기반 청킹 (LangChain)                            │
│  - 링크 추출 (내부 링크, 백링크)                          │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐    ┌───────────────���──┐
│  2. 벡터 생성     │    │  2. 그래프 구축   │
│  (OpenAI API)    │    │  (링크 파싱)      │
│                  │    │                  │
│ - Parent 벡터    │    │ - 노트 노드       │
│ - Child 벡터     │    │ - 링크 엣지       │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  3a. Qdrant      │    │  3b. Neo4j       │
│  (벡터 검색)      │    │  (그래프 검색)    │
│                  │    │                  │
│ - Collections    │    │ - Nodes: Note    │
│ - HNSW Index     │    │ - Edges: Links   │
│ - Payload Filter │    │ - Cypher Query   │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│          4. 쿼리 라우터 (Query Router)                   │
│                                                         │
│  사용자 쿼리 분석 후 적절한 검색 방식 선택:               │
│  - 키워드 중심 → Qdrant Payload Filter                 │
│  - 의미적 질문 → Qdrant Vector Search                   │
│  - 관계 탐색 → Neo4j Graph Traversal                    │
│  - 복합 쿼리 → Hybrid (전부 호출 후 융합)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         5. 결과 융합 & Reranking                        │
│  - RRF (Reciprocal Rank Fusion)                        │
│  - LLM Reranker (관련성 평가)                           │
│  - Parent 정보 결합                                     │
└─────────────────────────────────────────────────────────┘
```

### Qdrant: 벡터 검색 전담

**왜 Qdrant?**

1. **순수 벡터 검색 성능**: pgvector 대비 10배 빠름
2. **Payload 필터링**: 메타데이터 기반 복잡한 필터링
3. **Horizontal Scaling**: 클러스터링 쉬움
4. **운영 편의성**: Docker로 5분 만에 설치

**Collection 구조:**

```python
# Parent Collection
{
    "collection_name": "notes_parent",
    "vectors": {
        "size": 3072,  # text-embedding-3-large
        "distance": "Cosine"
    },
    "payload_schema": {
        "file_path": "keyword",
        "title": "text",
        "tags": "keyword[]",
        "category": "keyword",
        "date": "datetime",
        "summary": "text",
        "toc": "object",
        "word_count": "integer"
    }
}

# Child Collection
{
    "collection_name": "notes_child",
    "vectors": {
        "size": 3072,
        "distance": "Cosine"
    },
    "payload_schema": {
        "parent_id": "keyword",
        "chunk_index": "integer",
        "heading_text": "text",
        "content": "text",
        "section_path": "keyword[]"
    }
}
```

**검색 예시:**

```python
# 1. 순수 벡터 검색
results = qdrant_client.search(
    collection_name="notes_child",
    query_vector=embed("Docker 컨테이너 오케스트레이션"),
    limit=20
)

# 2. 필터링 + 벡터 검색
results = qdrant_client.search(
    collection_name="notes_child",
    query_vector=embed("RAG 시스템 구축"),
    query_filter={
        "must": [
            {"key": "tags", "match": {"value": "AI"}},
            {"key": "date", "range": {"gte": "2025-01-01"}}
        ]
    },
    limit=20
)

# 3. 키워드 검색 (Payload Full-Text)
# Qdrant 자체 FTS는 제한적 → Elasticsearch 연동 고려
```

### Neo4j: 그래프 탐색 전담

**왜 Neo4j?**

1. **관계 중심 쿼리**: Cypher로 직관적 그래프 탐색
2. **성숙한 생태계**: 풍부한 알고리즘 라이브러리
3. **시각화 도구**: Neo4j Browser로 지식 네트워크 탐색
4. **무료 Self-hosted**: Community Edition 완전 무료

**그래프 스키마:**

```cypher
// 노드 타입
(:Note {
    id: "uuid",
    file_path: "content/AI/...",
    title: "제목",
    tags: ["AI", "RAG"],
    category: "AI",
    date: date("2025-10-14")
})

(:Tag {
    name: "Docker",
    count: 15
})

(:Category {
    name: "AI",
    count: 50
})

// 관계 타입
(:Note)-[:LINKS_TO {weight: 1.0}]->(:Note)
(:Note)-[:HAS_TAG]->(:Tag)
(:Note)-[:BELONGS_TO]->(:Category)
(:Note)-[:SIMILAR_TO {score: 0.85}]->(:Note)  // 벡터 유사도 기반
```

**쿼리 예시:**

```cypher
// 1. 백링크 네트워크 (이 노트를 참조하는 모든 노트)
MATCH (target:Note {title: "RAG+Groq"})<-[:LINKS_TO]-(source:Note)
RETURN source.title, source.file_path

// 2. 두 노트 사이의 최단 경로
MATCH path = shortestPath(
    (a:Note {title: "Docker"})-[*]-(b:Note {title: "Kubernetes"})
)
RETURN path

// 3. 가장 많이 링크된 허브 노트 (PageRank)
CALL gds.pageRank.stream('note-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).title AS title, score
ORDER BY score DESC LIMIT 10

// 4. 관련 태그 네트워크 (공통 노트 기반)
MATCH (t1:Tag {name: "Docker"})<-[:HAS_TAG]-(n:Note)-[:HAS_TAG]->(t2:Tag)
WHERE t1 <> t2
RETURN t2.name, count(n) AS common_notes
ORDER BY common_notes DESC

// 5. 학습 경로 추천 (난이도 순 탐색)
MATCH path = (start:Note {title: "Docker 기초"})-[:LINKS_TO*1..5]->(end:Note)
WHERE start.difficulty < end.difficulty
RETURN path, length(path) AS depth
ORDER BY depth
```

### 데이터 동기화 전략

**문제:** Qdrant와 Neo4j에 중복 데이터 저장 시 일관성 유지?

**해결 방안:**

```python
# 단일 진실 공급원 (Single Source of Truth)
# → Markdown 파일이 SSOT

class DataPipeline:
    async def process_markdown(self, file_path: str):
        # 1. 파싱
        doc = parse_markdown(file_path)

        # 2. 병렬 처리
        await asyncio.gather(
            self.update_qdrant(doc),   # 벡터 + 페이로드
            self.update_neo4j(doc),    # 그래프 구조
        )

    async def update_qdrant(self, doc):
        # Parent 벡터
        parent_vector = await embed(doc.summary)
        qdrant_client.upsert(
            collection_name="notes_parent",
            points=[{
                "id": doc.id,
                "vector": parent_vector,
                "payload": {
                    "file_path": doc.file_path,
                    "title": doc.title,
                    "tags": doc.tags,
                    # ...
                }
            }]
        )

        # Child 벡터들
        for chunk in doc.chunks:
            chunk_vector = await embed(chunk.content)
            qdrant_client.upsert(
                collection_name="notes_child",
                points=[{
                    "id": chunk.id,
                    "vector": chunk_vector,
                    "payload": {
                        "parent_id": doc.id,
                        "content": chunk.content,
                        # ...
                    }
                }]
            )

    async def update_neo4j(self, doc):
        # 노트 노드 생성
        await neo4j_session.run("""
            MERGE (n:Note {id: $id})
            SET n.title = $title,
                n.file_path = $file_path,
                n.tags = $tags,
                n.date = date($date)
        """, id=doc.id, title=doc.title, ...)

        # 링크 생성
        for link in doc.internal_links:
            await neo4j_session.run("""
                MATCH (source:Note {id: $source_id})
                MATCH (target:Note {file_path: $target_path})
                MERGE (source)-[:LINKS_TO]->(target)
            """, source_id=doc.id, target_path=link)

        # 태그 연결
        for tag in doc.tags:
            await neo4j_session.run("""
                MERGE (t:Tag {name: $tag})
                WITH t
                MATCH (n:Note {id: $id})
                MERGE (n)-[:HAS_TAG]->(t)
            """, tag=tag, id=doc.id)
```

**자동화 (GitHub Actions):**

```yaml
name: Update Vector & Graph DB

on:
  push:
    paths:
      - 'content/**/*.md'

jobs:
  update-databases:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get changed files
        id: changed
        run: |
          echo "files=$(git diff --name-only HEAD^ HEAD | grep '\.md$')" >> $GITHUB_OUTPUT

      - name: Update Qdrant & Neo4j
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          NEO4J_URI: ${{ secrets.NEO4J_URI }}
        run: |
          python scripts/sync_databases.py --files "${{ steps.changed.outputs.files }}"
```

## 하이브리드 검색 구현

### 쿼리 라우터 (Query Router)

사용자 쿼리를 분석하여 최적의 검색 방식 선택:

```python
class QueryRouter:
    def analyze_query(self, query: str) -> SearchStrategy:
        # LLM으로 쿼리 의도 분석
        intent = await self.llm.classify(query, categories=[
            "keyword",      # "pgvector 설치 방법"
            "semantic",     # "RAG가 뭐야?"
            "relationship", # "Docker와 Kubernetes 관계"
            "hybrid"        # "AI 관련 학습 경로"
        ])

        if intent == "keyword":
            return KeywordSearch()
        elif intent == "semantic":
            return VectorSearch()
        elif intent == "relationship":
            return GraphSearch()
        else:
            return HybridSearch()
```

### 1. 벡터 검색 (Semantic)

```python
class VectorSearch:
    async def search(self, query: str, limit: int = 20):
        # 쿼리 임베딩
        query_vector = await embed(query)

        # Qdrant 검색
        results = qdrant_client.search(
            collection_name="notes_child",
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )

        # Parent 정보 결합
        enriched = []
        for result in results:
            parent = qdrant_client.retrieve(
                collection_name="notes_parent",
                ids=[result.payload["parent_id"]]
            )[0]

            enriched.append({
                "content": result.payload["content"],
                "heading": result.payload["heading_text"],
                "score": result.score,
                "parent_title": parent.payload["title"],
                "parent_path": parent.payload["file_path"],
            })

        return enriched
```

### 2. 그래프 검색 (Relationship)

```python
class GraphSearch:
    async def search(self, query: str):
        # 쿼리에서 엔티티 추출
        entities = await self.extract_entities(query)
        # 예: "Docker와 Kubernetes의 관계" → ["Docker", "Kubernetes"]

        if len(entities) >= 2:
            # 두 노트 사이의 경로 찾기
            results = await neo4j_session.run("""
                MATCH (a:Note WHERE a.title CONTAINS $entity1)
                MATCH (b:Note WHERE b.title CONTAINS $entity2)
                MATCH path = shortestPath((a)-[*..5]-(b))
                RETURN path, length(path) AS depth
                ORDER BY depth
                LIMIT 10
            """, entity1=entities[0], entity2=entities[1])

        elif len(entities) == 1:
            # 단일 노트의 관련 노트 찾기
            results = await neo4j_session.run("""
                MATCH (center:Note WHERE center.title CONTAINS $entity)
                MATCH (center)-[r:LINKS_TO|SIMILAR_TO]-(related:Note)
                RETURN related, type(r) AS rel_type, r.weight AS weight
                ORDER BY weight DESC
                LIMIT 20
            """, entity=entities[0])

        return results
```

### 3. 하이브리드 검색 (Vector + Graph + Keyword)

```python
class HybridSearch:
    async def search(self, query: str):
        # 1. 병렬로 3가지 검색 실행
        vector_results, graph_results = await asyncio.gather(
            self.vector_search.search(query, limit=30),
            self.graph_search.search(query),
        )

        # 2. 벡터 검색 결과의 노트들을 그래프에서 확장
        note_ids = [r["parent_id"] for r in vector_results]
        expanded = await neo4j_session.run("""
            MATCH (n:Note WHERE n.id IN $ids)
            OPTIONAL MATCH (n)-[:LINKS_TO]-(related:Note)
            RETURN n, collect(related) AS related_notes
        """, ids=note_ids)

        # 3. RRF 융합
        all_results = self.reciprocal_rank_fusion([
            vector_results,
            graph_results,
            expanded
        ])

        # 4. LLM Reranking
        reranked = await self.llm_rerank(query, all_results)

        return reranked[:10]  # Top 10

    def reciprocal_rank_fusion(self, result_lists, k=60):
        """
        RRF 공식: score(doc) = Σ [1 / (k + rank_i)]
        """
        scores = defaultdict(float)

        for results in result_lists:
            for rank, doc in enumerate(results, start=1):
                doc_id = doc["id"]
                scores[doc_id] += 1 / (k + rank)

        # 점수 순 정렬
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_docs
```

## 비용 및 운영

### 인프라 비용 (Self-hosted on AWS)

**기본 구성 (개인 프로젝트):**

```yaml
# EC2 t4g.medium (4GB RAM, 2 vCPU)
- Qdrant: ~1.5GB RAM
- Neo4j Community: ~2GB RAM
- 여유 메모리: ~0.5GB

월 비용: ~$30/월 (AWS t4g.medium)
```

**분리 구성 (트래픽 증가 시):**

```yaml
# Qdrant 전용 (t4g.small, 2GB)
EC2 #1: ~$15/월

# Neo4j 전용 (t4g.small, 2GB)
EC2 #2: ~$15/월

총 비용: ~$30/월
```

**비교 (Managed Service):**

| 서비스 | Self-hosted | Managed | 절약 |
|--------|------------|---------|------|
| Qdrant | $0 (EC2 포함) | ~$95/월 | $95 |
| Neo4j | $0 (EC2 포함) | ~$65/월 | $65 |
| **합계** | **$30/월** | **$160/월** | **$130** |

### Docker Compose 배포

```yaml
# docker-compose.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped

  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - ./neo4j_data:/data
      - ./neo4j_logs:/logs
    environment:
      - NEO4J_AUTH=neo4j/your-password
      - NEO4J_server_memory_heap_max__size=1G
      - NEO4J_server_memory_pagecache_size=512M
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
    restart: unless-stopped

  # 선택: APOC & GDS 플러그인 (그래프 알고리즘)
  neo4j-plugins:
    image: neo4j:5-community
    volumes:
      - ./neo4j_plugins:/plugins
    entrypoint:
      - /bin/bash
      - -c
      - |
        wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.x/apoc-5.x-core.jar -P /plugins
        wget https://github.com/neo4j/graph-data-science/releases/download/2.x/neo4j-graph-data-science-2.x.jar -P /plugins
```

### 모니터링

```yaml
# Prometheus + Grafana
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

# prometheus.yml
scrape_configs:
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:7474']
```

## 확장 시나리오

### 1. 벡터 유사도 기반 그래프 엣지 생성

**아이디어:** Qdrant의 벡터 유사도를 Neo4j 그래프에 반영

```python
async def create_similarity_edges(threshold=0.8):
    # 1. 모든 노트의 유사도 계산 (Qdrant)
    all_notes = qdrant_client.scroll(
        collection_name="notes_parent",
        limit=1000
    )

    for note in all_notes:
        # 유사한 노트 찾기
        similar = qdrant_client.search(
            collection_name="notes_parent",
            query_vector=note.vector,
            limit=10,
            score_threshold=threshold
        )

        # 2. Neo4j에 SIMILAR_TO 엣지 생성
        for sim in similar:
            if sim.id != note.id:
                await neo4j_session.run("""
                    MATCH (a:Note {id: $id1})
                    MATCH (b:Note {id: $id2})
                    MERGE (a)-[r:SIMILAR_TO]->(b)
                    SET r.score = $score
                """, id1=note.id, id2=sim.id, score=sim.score)
```

**활용:**
```cypher
// 의미적으로 유사하면서 링크로도 연결된 노트 (강한 관련성)
MATCH (a:Note)-[:SIMILAR_TO {score: > 0.85}]->(b:Note),
      (a)-[:LINKS_TO]->(b)
RETURN a.title, b.title, "very strong connection"
```

### 2. 태그 기반 클러스터링

**Neo4j Community Detection:**

```cypher
// Louvain 알고리즘으로 노트 클러스터 발견
CALL gds.louvain.stream('note-graph')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS note, communityId
RETURN communityId, collect(note.title) AS notes_in_cluster
ORDER BY size(notes_in_cluster) DESC
```

**Qdrant에 클러스터 정보 반영:**

```python
# Neo4j에서 클러스터 정보 가져오기
clusters = await neo4j_session.run("""
    CALL gds.louvain.stream('note-graph')
    YIELD nodeId, communityId
    RETURN nodeId, communityId
""")

# Qdrant 페이로드에 클러스터 추가
for node_id, cluster_id in clusters:
    qdrant_client.set_payload(
        collection_name="notes_parent",
        payload={"cluster_id": cluster_id},
        points=[node_id]
    )
```

**검색 시 활용:**

```python
# 같은 클러스터 내에서만 검색 (관련 주제 집중)
results = qdrant_client.search(
    collection_name="notes_parent",
    query_vector=query_vector,
    query_filter={
        "must": [{"key": "cluster_id", "match": {"value": target_cluster}}]
    },
    limit=20
)
```

### 3. 시간 기반 지식 진화 추적

**Neo4j 버전 관리:**

```cypher
// 노트의 버전 변화 추적
(:Note)-[:VERSION_OF]->(:NoteVersion {
    content_hash: "abc123",
    modified_date: date("2025-10-14"),
    vector_drift: 0.15  // 이전 버전과 벡터 거리
})

// 지식의 진화 경로 탐색
MATCH path = (old:NoteVersion)-[:VERSION_OF*]->(latest:Note)
WHERE old.modified_date < date("2025-01-01")
RETURN path, length(path) AS evolution_steps
```

## pgvector와의 비교 요약

| 측면 | pgvector (이전) | Qdrant + Neo4j (현재) |
|------|----------------|---------------------|
| **벡터 검색 성능** | 보통 | 우수 (10배 빠름) |
| **그래프 탐색** | 어려움 (재귀 쿼리) | 자연스러움 (Cypher) |
| **독립 확장** | 불가능 (PostgreSQL 전체) | 가능 (Qdrant/Neo4j 독립) |
| **운영 복잡도** | 낮음 (단일 DB) | 중간 (두 개 DB) |
| **비용 (Self-hosted)** | ~$20/월 | ~$30/월 |
| **트랜잭션 일관성** | 완벽 (ACID) | 최종 일관성 |
| **학습 곡선** | 낮음 (SQL) | 중간 (Cypher 추가) |
| **확장성** | 제한적 | 우수 |

**결론:**

pgvector의 장점 (통합, 트랜잭션, 운영 편의)보다 **전문 도구의 성능과 유연성**이 더 중요하다고 판단했다. 특히 **그래프 검색의 필요성**과 **각 검색 방식의 독립적 확장**이 결정적이었다.

## 다음 단계

1. **Qdrant + Neo4j 로컬 환경 구축**
   - Docker Compose로 개발 환경 세팅
   - Collection/Graph 스키마 설계 확정

2. **데이터 파이프라인 구현**
   - Markdown 파싱 → Qdrant + Neo4j 동시 업데이트
   - GitHub Actions 자동화

3. **하이브리드 검색 API 개발**
   - FastAPI 서버 구축
   - 쿼리 라우터 + RRF 융합 구현

4. **Quartz 프론트엔드 통합**
   - 검색 UI 컴포넌트
   - 그래프 시각화 (D3.js + Neo4j)

5. **성능 측정 및 최적화**
   - 벤치마크 테스트
   - 인덱스 튜닝

## 참고 자료

### Qdrant
- **[Qdrant Documentation](https://qdrant.tech/documentation/)**: 공식 문서
- **[Qdrant GitHub](https://github.com/qdrant/qdrant)**: 오픈소스 저장소
- **[Payload Filtering Guide](https://qdrant.tech/documentation/concepts/filtering/)**: 메타데이터 필터링

### Neo4j
- **[Neo4j Documentation](https://neo4j.com/docs/)**: 공식 문서
- **[Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)**: 쿼리 언어 레퍼런스
- **[Graph Data Science Library](https://neo4j.com/docs/graph-data-science/current/)**: 그래프 알고리즘
- **[APOC Procedures](https://neo4j.com/labs/apoc/)**: 유틸리티 함수 모음

### 관련 프로젝트
- [[2025-10-12-pgvector-활용-벡터베이스-구현]]: 이전 설계 (비교 참고)
- [[2025-10-07-AppHub-구조-및-기술-스택]]: 전체 프로젝트 아키텍처
- [[한국자동차공학회 논문 특화 파서 시스템 분석]]: Qdrant 기반 이전 구현
