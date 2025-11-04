---
title: "Neo4j + Qdrant 하이브리드 아키텍처: 그래프와 벡터의 시너지"
date: 2025-11-03
tags:
  - Neo4j
  - Qdrant
  - Vector-Database
  - Graph-Database
  - Hybrid-Search
  - RAG
  - Architecture
draft: false
enableToc: true
description: Neo4j 그래프 데이터베이스와 Qdrant 벡터 데이터베이스를 결합한 하이브리드 검색 아키텍처. 의미 기반 벡터 검색의 정확성과 그래프 관계 탐색의 맥락을 동시에 활용하여 차세대 지식 검색 시스템을 구축한다.
---

> [!summary] **왜 Neo4j + Qdrant인가?**
> pgvector의 성능 한계를 극복하고, 단순 벡터 검색을 넘어 **그래프 관계**까지 활용하기 위해 Neo4j와 Qdrant의 하이브리드 아키텍처를 선택했다. Qdrant는 최고 성능의 벡터 검색을, Neo4j는 백링크와 태그 네트워크 같은 그래프 관계 탐색을 담당한다.

## 아키텍처 개요

### 하이브리드 구조

```
┌────────────────────────────────────────────────────┐
│              사용자 질의                           │
│         "LangChain v1.0에 대한 글"                 │
└────────────────────────────────────────────────────┘
                      ↓
        ┌─────────────┴─────────────┐
        │                           │
        ↓                           ↓
┌───────────────┐          ┌────────────────┐
│    Qdrant     │          │     Neo4j      │
│ ─────────────│          │ ──────────────│
│ 벡터 검색     │          │ 그래프 검색    │
│ (의미 유사도) │          │ (키워드/관계)  │
└───────────────┘          └────────────────┘
        │                           │
        └─────────────┬─────────────┘
                      ↓
        ┌──────────────────────────┐
        │   Hybrid Fusion          │
        │ ──────────────────────── │
        │ • RRF (Reciprocal Rank)  │
        │ • 가중치 조합             │
        │ • 그래프 확장             │
        └──────────────────────────┘
                      ↓
        ┌──────────────────────────┐
        │   최종 결과               │
        │ ──────────────────────── │
        │ 1. 벡터 유사도 높은 글    │
        │ 2. 관련된 백링크 글       │
        │ 3. 같은 태그 글           │
        └──────────────────────────┘
```

### 역할 분담

| 컴포넌트 | 역할 | 강점 | 사용 시나리오 |
|---------|------|------|--------------|
| **Qdrant** | 벡터 검색 | • 5-15ms 레이턴시<br>• 의미 기반 검색<br>• 메타데이터 필터링 | "AI 에이전트 개발" 같은 개념 검색 |
| **Neo4j** | 그래프 검색 | • 관계 탐색<br>• Full-text 검색<br>• 네트워크 분석 | "이 글이 참조한 글", "같은 태그 글" |

---

## 데이터 모델 설계

### Qdrant: 벡터 컬렉션

```python
# Qdrant Collection 스키마

{
  "collection_name": "blog_posts",
  "vectors": {
    "size": 1536,           # OpenAI text-embedding-3-small
    "distance": "Cosine"
  },
  "payload_schema": {
    "id": "keyword",        # Neo4j와 공유하는 고유 ID
    "title": "text",
    "slug": "keyword",
    "date": "datetime",
    "tags": "keyword[]",
    "content": "text",      # 전체 내용 (검색용)
    "excerpt": "text",      # 요약 (표시용)
    "url": "keyword"
  }
}
```

**포인트 추가 예시:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

client = QdrantClient(host="localhost", port=6333)

client.upsert(
    collection_name="blog_posts",
    points=[
        PointStruct(
            id="langchain-v1-update",  # 문자열 ID
            vector=[0.1, 0.2, ...],     # 1536차원 임베딩
            payload={
                "id": "langchain-v1-update",
                "title": "LangChain v1.0 업데이트",
                "slug": "langchain-v1-update",
                "date": "2025-11-02T00:00:00Z",
                "tags": ["AI", "LangChain", "LangGraph"],
                "content": "...",
                "excerpt": "LangChain v1.0 정식 출시...",
                "url": "/blog/langchain-v1-update"
            }
        )
    ]
)
```

### Neo4j: 그래프 노드 & 관계

```cypher
// 노드 스키마

(:BlogPost {
  id: "langchain-v1-update",  // Qdrant와 동일한 ID
  title: "LangChain v1.0 업데이트",
  slug: "langchain-v1-update",
  date: datetime("2025-11-02"),
  content: "...",             // Full-text 검색용
  embedding: [0.1, 0.2, ...]  // 선택적 (Neo4j 벡터 인덱스)
})

(:Tag {
  name: "AI"
})
```

```cypher
// 관계 스키마

(:BlogPost)-[:REFERENCES]->(:BlogPost)      // 명시적 참조
(:BlogPost)-[:TAGGED_WITH]->(:Tag)          // 태그 관계
(:BlogPost)-[:SIMILAR_TO {score: 0.85}]->(:BlogPost)  // 벡터 유사도 (선택적)
```

**노드 & 관계 생성:**
```cypher
// 블로그 포스트 생성
CREATE (p:BlogPost {
  id: "langchain-v1-update",
  title: "LangChain v1.0 업데이트",
  slug: "langchain-v1-update",
  date: datetime("2025-11-02"),
  content: "..."
})

// 태그 생성 & 연결
MERGE (t:Tag {name: "AI"})
CREATE (p)-[:TAGGED_WITH]->(t)

// 백링크 (참조) 생성
MATCH (p1:BlogPost {id: "langchain-v1-update"})
MATCH (p2:BlogPost {id: "context-engineering"})
CREATE (p1)-[:REFERENCES]->(p2)

// Full-text 인덱스 생성
CREATE FULLTEXT INDEX blog_fulltext
FOR (p:BlogPost)
ON EACH [p.title, p.content]

// 벡터 인덱스 생성 (선택적)
CREATE VECTOR INDEX blog_embeddings
FOR (p:BlogPost)
ON (p.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

---

## 하이브리드 검색 전략

### 4단계 검색 파이프라인

#### Stage 1: 벡터 검색 (Qdrant)

**목적:** 의미적으로 유사한 글 찾기

```python
async def vector_search(query: str, top_k: int = 10) -> List[SearchResult]:
    """Qdrant 벡터 검색"""
    from openai import OpenAI

    # 1. 쿼리 임베딩
    client = OpenAI()
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    # 2. Qdrant 검색
    results = qdrant_client.search(
        collection_name="blog_posts",
        query_vector=embedding,
        limit=top_k,
        with_payload=True
    )

    # 3. 결과 정규화
    return [
        SearchResult(
            id=r.id,
            score=r.score,
            source="vector",
            metadata=r.payload
        )
        for r in results
    ]
```

**특징:**
- ✅ 동의어, 유사 개념 찾기 ("AI agent" ≈ "intelligent automation")
- ✅ 다국어 지원 (임베딩 모델 성능)
- ✅ 빠른 속도 (HNSW 인덱스)

#### Stage 2: 키워드 검색 (Neo4j)

**목적:** 정확한 키워드 매칭

```python
async def keyword_search(keywords: str, top_k: int = 10) -> List[SearchResult]:
    """Neo4j Full-text 검색"""

    with neo4j_driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('blog_fulltext', $keywords)
            YIELD node, score
            RETURN node.id as id,
                   node.title as title,
                   node.content as content,
                   score
            ORDER BY score DESC
            LIMIT $top_k
        """, keywords=keywords, top_k=top_k)

        return [
            SearchResult(
                id=record['id'],
                score=record['score'],
                source="keyword",
                metadata={
                    'title': record['title'],
                    'content': record['content']
                }
            )
            for record in result
        ]
```

**특징:**
- ✅ 정확한 용어 매칭 ("LangChain v1.0" 정확히 찾기)
- ✅ 빠른 속도 (Lucene 인덱스)
- ✅ 한국어 형태소 분석 가능 (Neo4j 플러그인)

#### Stage 3: 하이브리드 융합 (RRF)

**목적:** 벡터 + 키워드 결과 병합

```python
def reciprocal_rank_fusion(
    vector_results: List[SearchResult],
    keyword_results: List[SearchResult],
    k: int = 60,
    semantic_weight: float = 0.7
) -> List[SearchResult]:
    """
    RRF (Reciprocal Rank Fusion) 알고리즘

    score = semantic_weight / (k + rank_vector) +
            (1 - semantic_weight) / (k + rank_keyword)
    """
    from collections import defaultdict

    scores = defaultdict(float)
    contents = {}

    # 벡터 검색 점수
    for rank, result in enumerate(vector_results):
        rrf_score = semantic_weight / (k + rank)
        scores[result.id] += rrf_score
        contents[result.id] = result

    # 키워드 검색 점수
    for rank, result in enumerate(keyword_results):
        rrf_score = (1 - semantic_weight) / (k + rank)
        scores[result.id] += rrf_score
        if result.id not in contents:
            contents[result.id] = result

    # 정렬
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    return [
        SearchResult(
            id=id,
            score=scores[id],
            source="hybrid",
            metadata=contents[id].metadata
        )
        for id in sorted_ids
    ]
```

**RRF 특징:**
- ✅ 순위 기반 (점수 정규화 불필요)
- ✅ 견고함 (이상치에 덜 민감)
- ✅ 가중치 조정 가능 (semantic_weight)

#### Stage 4: 그래프 확장 (Neo4j)

**목적:** 백링크, 태그 네트워크로 확장

```python
async def graph_expand(
    post_ids: List[str],
    depth: int = 1,
    limit: int = 10
) -> List[SearchResult]:
    """Neo4j 그래프 확장"""

    with neo4j_driver.session() as session:
        # 백링크 & 태그 확장
        result = session.run("""
            // 검색된 포스트들
            MATCH (origin:BlogPost)
            WHERE origin.id IN $post_ids

            // 1-hop 확장 (백링크 또는 같은 태그)
            MATCH (origin)-[r:REFERENCES|TAGGED_WITH*1..$depth]-(related:BlogPost)
            WHERE related.id NOT IN $post_ids

            // 연결 강도 계산
            WITH related, COUNT(DISTINCT r) as connection_strength

            RETURN related.id as id,
                   related.title as title,
                   related.content as content,
                   connection_strength
            ORDER BY connection_strength DESC
            LIMIT $limit
        """, post_ids=post_ids, depth=depth, limit=limit)

        return [
            SearchResult(
                id=record['id'],
                score=record['connection_strength'] / 10.0,
                source="graph",
                metadata={
                    'title': record['title'],
                    'connection_strength': record['connection_strength']
                }
            )
            for record in result
        ]
```

**그래프 확장 시나리오:**

1. **백링크 (References)**
   ```
   사용자: "LangChain v1.0 업데이트"
   → Qdrant: 해당 글 찾음
   → Neo4j: 이 글이 참조한 글들 확장
   → 결과: "Context Engineering", "기술 스택 선택" 등
   ```

2. **태그 네트워크**
   ```
   사용자: "AI 에이전트"
   → Qdrant: AI 관련 글들
   → Neo4j: 같은 태그 가진 다른 글들
   → 결과: "LangGraph", "Tool 설계" 등
   ```

3. **유사도 그래프** (선택적)
   ```
   Qdrant 검색 후 상위 결과들 간의
   유사도를 Neo4j 관계로 저장
   → 클러스터 시각화 가능
   ```

---

## 통합 검색 API

### 최종 하이브리드 검색

```python
# packages/agent-tools/src/level3/blog/hybrid_retriever.py

from typing import List, Optional, Dict, Any
from agent_tools.base.retriever import BaseRetriever, SearchResult

class BlogHybridRetriever(BaseRetriever):
    """블로그 하이브리드 검색 시스템"""

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        expand_graph: bool = True
    ) -> List[SearchResult]:
        """
        4단계 하이브리드 검색

        Args:
            query: 검색 쿼리
            top_k: 최종 반환 개수
            filters: Qdrant 필터 (날짜, 태그 등)
            expand_graph: 그래프 확장 여부

        Returns:
            통합 검색 결과
        """

        # Stage 1: Qdrant 벡터 검색
        vector_results = await self.vector_search(
            query, top_k=top_k*2, filters=filters
        )

        # Stage 2: Neo4j 키워드 검색
        keyword_results = await self.keyword_search(
            query, top_k=top_k*2
        )

        # Stage 3: RRF 융합
        hybrid_results = self.reciprocal_rank_fusion(
            vector_results,
            keyword_results,
            semantic_weight=0.7
        )

        # 상위 결과 선택
        final_results = hybrid_results[:top_k]

        # Stage 4: 그래프 확장 (선택적)
        if expand_graph:
            post_ids = [r.id for r in final_results]
            graph_results = await self.graph_expand(
                post_ids, depth=1, limit=5
            )

            # 그래프 결과 추가 (중복 제거)
            existing_ids = set(post_ids)
            for r in graph_results:
                if r.id not in existing_ids:
                    final_results.append(r)
                    existing_ids.add(r.id)

        return final_results

    async def get_related_posts(
        self,
        post_id: str,
        relation_types: List[str] = ["REFERENCES", "TAGGED_WITH"],
        limit: int = 5
    ) -> List[SearchResult]:
        """
        특정 글의 관련 글 찾기

        Args:
            post_id: 기준 포스트 ID
            relation_types: 관계 타입 리스트
            limit: 반환 개수

        Returns:
            관련 포스트 리스트
        """
        with self.neo4j.session() as session:
            query = f"""
                MATCH (origin:BlogPost {{id: $post_id}})
                MATCH (origin)-[r:{"|".join(relation_types)}]-(related:BlogPost)
                RETURN DISTINCT related.id as id,
                       related.title as title,
                       related.content as content,
                       type(r) as relation_type,
                       COUNT(r) as strength
                ORDER BY strength DESC
                LIMIT $limit
            """

            result = session.run(query, post_id=post_id, limit=limit)

            return [
                SearchResult(
                    id=record['id'],
                    score=record['strength'] / 10.0,
                    source=f"graph_{record['relation_type']}",
                    metadata={
                        'title': record['title'],
                        'relation_type': record['relation_type']
                    }
                )
                for record in result
            ]

    async def analyze_tag_network(self, min_posts: int = 3) -> Dict[str, Any]:
        """
        태그 네트워크 분석

        Returns:
            태그별 포스트 수, 연결 강도 등
        """
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (t:Tag)<-[:TAGGED_WITH]-(p:BlogPost)
                WITH t, COUNT(p) as post_count
                WHERE post_count >= $min_posts

                // 태그 간 공통 포스트
                MATCH (t)<-[:TAGGED_WITH]-(p)-[:TAGGED_WITH]->(other:Tag)
                WHERE t.name < other.name

                RETURN t.name as tag,
                       post_count,
                       COLLECT({tag: other.name, strength: COUNT(DISTINCT p)}) as connections
                ORDER BY post_count DESC
            """, min_posts=min_posts)

            return {
                'tags': [dict(record) for record in result]
            }
```

---

## Docker Compose 설정

### 업데이트된 compose.yaml

```yaml
# apphub/compose.yaml

services:
  postgres:
    image: pgvector/pgvector:pg18-bookworm
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: apphub
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # pgvector는 메인 DB로만 사용 (벡터 검색은 Qdrant)

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
    volumes:
      - qdrant_data:/qdrant/storage

  neo4j:
    image: neo4j:5.15-community
    ports:
      - "7474:7474"  # HTTP (Browser)
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc"]'  # APOC 플러그인
      NEO4J_dbms_security_procedures_unrestricted: apoc.*
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  ai-service:
    build: ./apps/ai-service
    ports:
      - "2024:2024"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/apphub
      REDIS_URL: redis://redis:6379
      QDRANT_URL: http://qdrant:6333
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: password
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LANGSMITH_API_KEY: ${LANGSMITH_API_KEY}
      LANGSMITH_TRACING: "true"
    depends_on:
      - postgres
      - redis
      - qdrant
      - neo4j

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  neo4j_data:
  neo4j_logs:
```

---

## 데이터 동기화 전략

### 초기 인덱싱

```python
# scripts/index_blog_posts.py

async def index_blog_posts(posts: List[BlogPost]):
    """
    블로그 포스트를 Qdrant와 Neo4j에 동시 인덱싱
    """
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from neo4j import GraphDatabase

    openai_client = OpenAI()
    qdrant_client = QdrantClient(host="localhost", port=6333)
    neo4j_driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )

    for post in posts:
        # 1. 임베딩 생성
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=post.content
        ).data[0].embedding

        # 2. Qdrant에 추가
        qdrant_client.upsert(
            collection_name="blog_posts",
            points=[PointStruct(
                id=post.id,
                vector=embedding,
                payload={
                    "id": post.id,
                    "title": post.title,
                    "slug": post.slug,
                    "date": post.date.isoformat(),
                    "tags": post.tags,
                    "content": post.content,
                    "excerpt": post.excerpt,
                    "url": f"/blog/{post.slug}"
                }
            )]
        )

        # 3. Neo4j에 추가
        with neo4j_driver.session() as session:
            # 노드 생성
            session.run("""
                MERGE (p:BlogPost {id: $id})
                SET p.title = $title,
                    p.slug = $slug,
                    p.date = datetime($date),
                    p.content = $content
            """, **post.dict())

            # 태그 생성 & 연결
            for tag in post.tags:
                session.run("""
                    MATCH (p:BlogPost {id: $id})
                    MERGE (t:Tag {name: $tag})
                    MERGE (p)-[:TAGGED_WITH]->(t)
                """, id=post.id, tag=tag)

            # 백링크 생성 (마크다운 [[링크]] 파싱)
            references = extract_wiki_links(post.content)
            for ref_slug in references:
                session.run("""
                    MATCH (p1:BlogPost {id: $id})
                    MATCH (p2:BlogPost {slug: $ref_slug})
                    MERGE (p1)-[:REFERENCES]->(p2)
                """, id=post.id, ref_slug=ref_slug)

    print(f"Indexed {len(posts)} posts to Qdrant and Neo4j")
```

### 증분 업데이트

```python
async def update_blog_post(post: BlogPost):
    """
    단일 포스트 업데이트 (Qdrant + Neo4j)
    """
    # 1. 임베딩 재생성
    embedding = generate_embedding(post.content)

    # 2. Qdrant 업데이트
    qdrant_client.upsert(...)

    # 3. Neo4j 업데이트
    with neo4j_driver.session() as session:
        session.run("""
            MATCH (p:BlogPost {id: $id})
            SET p.title = $title,
                p.content = $content,
                p.date = datetime($date)
        """, **post.dict())

        # 기존 관계 삭제 후 재생성
        session.run("""
            MATCH (p:BlogPost {id: $id})-[r:REFERENCES|TAGGED_WITH]->()
            DELETE r
        """, id=post.id)

        # 새 관계 생성
        # ... (태그, 백링크)
```

---

## 성능 최적화

### Qdrant 최적화

```python
# Quantization으로 메모리 절약
from qdrant_client.models import VectorParams, QuantizationConfig

qdrant_client.create_collection(
    collection_name="blog_posts",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    ),
    quantization_config=QuantizationConfig(
        scalar=ScalarQuantization(
            type=ScalarType.INT8,
            quantile=0.99,
            always_ram=True
        )
    )
)
```

**효과:**
- 메모리 사용량 75% 감소
- 검색 속도 2-3배 향상
- 정확도 손실 < 1%

### Neo4j 최적화

```cypher
// 인덱스 생성
CREATE INDEX post_id_index FOR (p:BlogPost) ON (p.id)
CREATE INDEX post_slug_index FOR (p:BlogPost) ON (p.slug)
CREATE INDEX post_date_index FOR (p:BlogPost) ON (p.date)
CREATE INDEX tag_name_index FOR (t:Tag) ON (t.name)

// Full-text 인덱스
CREATE FULLTEXT INDEX blog_fulltext
FOR (p:BlogPost)
ON EACH [p.title, p.content]
OPTIONS {indexConfig: {`fulltext.analyzer`: "korean"}}

// 벡터 인덱스 (선택적)
CREATE VECTOR INDEX blog_embeddings
FOR (p:BlogPost)
ON (p.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

---

## 사용 예시

### CLI에서 사용

```bash
# Qdrant 벡터 검색
$ knowledge-search search \
    --query "LangChain v1.0" \
    --collection blog_posts \
    --top-k 5
/tmp/search_results_abc123.json

# Neo4j 그래프 확장
$ knowledge-search graph-expand \
    --post-id "langchain-v1-update" \
    --depth 2 \
    --limit 10
/tmp/graph_results_xyz789.json

# 하이브리드 검색
$ knowledge-search hybrid \
    --query "AI agents context engineering" \
    --collection blog_posts \
    --semantic-weight 0.7
/tmp/hybrid_results_def456.json
```

### Agent에서 사용

```
User: "컨텍스트 엔지니어링에 대한 내 블로그 글 찾아줘"

Agent (내부):
  1. semantic_search("context engineering", "blog_posts", 5)
     → /tmp/search_results.json

  2. file_read("/tmp/search_results.json")
     → 3개 결과 확인

  3. graph_expand(["context-engineering", ...], depth=1)
     → /tmp/graph_results.json (백링크 5개)

  4. 통합 분석 후 답변

Agent Response:
  "컨텍스트 엔지니어링 관련 글 3개를 찾았습니다:

  1. Context Engineering for AI Agents (2025-10-26) ⭐
     - Manus의 5가지 핵심 기법 소개

  2. 범용 Agent Tool 아키텍처 (2025-11-03)
     - 3계층 액션 공간 적용

  3. LangChain v1.0 업데이트 (2025-11-02)
     - 컨텍스트 엔지니어링 언급

  이 글들은 서로 참조 관계가 있으며, 'AI', 'Agent', 'LangChain' 태그를 공유합니다."
```

---

## 다음 단계

### 1주차: 인프라 구축
- [ ] Docker Compose 설정
- [ ] Qdrant 컬렉션 생성
- [ ] Neo4j 스키마 & 인덱스 설정

### 2주차: 데이터 인덱싱
- [ ] 블로그 포스트 파싱 스크립트
- [ ] 임베딩 생성 파이프라인
- [ ] Qdrant + Neo4j 동시 인덱싱

### 3주차: 검색 API 구현
- [ ] BlogHybridRetriever 구현
- [ ] RRF 알고리즘 테스트
- [ ] 그래프 확장 쿼리 최적화

### 4주차: Tool 통합
- [ ] Level 2 CLI 통합
- [ ] LangGraph Agent 연결
- [ ] End-to-end 테스트

---

## 참고 자료

- [[2025-11-03-범용-Agent-Tool-아키텍처-설계]] - Tool 아키텍처
- [[2025-10-07-AppHub-구조-및-기술-스택]] - 전체 기술 스택
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Neo4j Vector Index](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/)
- [Hybrid Search Best Practices](https://qdrant.tech/articles/hybrid-search/)

---

> [!tip] 하이브리드의 힘
> Qdrant의 속도와 Neo4j의 관계 탐색을 결합하면, 단순 벡터 검색으로는 불가능한 맥락 인식 검색이 가능해진다. "이 글과 연결된 글"을 자연스럽게 찾아주는 것이 진짜 지능형 검색이다.
