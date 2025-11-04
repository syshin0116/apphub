---
title: "범용 Agent Tool 아키텍처 설계: Manus 3계층 패턴 적용"
date: 2025-11-03
tags:
  - Agent
  - Tool
  - Architecture
  - LangGraph
  - Domain-Agnostic
  - Manus
  - Context-Engineering
draft: false
enableToc: true
description: Manus의 계층형 액션 공간을 적용한 도메인 독립적 Agent Tool 아키텍처 설계. Level 1 원자적 함수, Level 2 CLI 유틸리티, Level 3 도메인 구현의 3계층 구조로 재사용성과 확장성을 극대화한다.
---

> [!summary] **범용 Tool 아키텍처의 목표**
> [[2025-10-26-context-engineering-for-ai-agents|Manus의 Context Engineering]] 원칙을 기반으로, **어떤 도메인에도 적용 가능한** Agent Tool 아키텍처를 설계한다. 블로그 검색이 첫 번째 구현 사례이지만, 향후 전자상거래, 헬스케어, 금융 등 어떤 도메인에도 적용할 수 있는 base 설계를 목표로 한다.

## 설계 철학

### Manus의 핵심 원칙 적용

> [!quote] Build less, understand more
> Manus의 가장 중요한 교훈: 과잉 엔지니어링을 피하고, 단순하면서도 강력한 아키텍처를 유지한다.

**적용 원칙:**
1. **도구는 컨텍스트를 차지한다** - 함수 호출 공간 최소화
2. **압축 우선, 요약은 최후** - 가역적 압축 먼저 시도
3. **격리를 통한 제어** - 컨텍스트 공유 최소화
4. **캐싱 효율 극대화** - KV 캐시 무효화 방지
5. **자가 문서화** - CLI `--help` 패턴

---

## 3계층 아키텍처 설계

### 전체 구조

```
┌─────────────────────────────────────────────────┐
│  Level 1: Atomic Functions                      │
│  ─────────────────────────────────              │
│  LangGraph @tool 데코레이터                     │
│  10-20개 고정된 원자적 함수                     │
│  • 컨텍스트 최소화                              │
│  • 스키마 안전 (constraint decoding)            │
│  • KV 캐시 친화적                               │
└─────────────────────────────────────────────────┘
              ↓ offload
┌─────────────────────────────────────────────────┐
│  Level 2: CLI Utilities                         │
│  ─────────────────────────────────              │
│  셸 명령으로 호출 가능한 유틸리티               │
│  • MCP 통합 지점                                │
│  • --help로 자가 문서화                         │
│  • 함수 공간을 건드리지 않음                    │
│  • 출력 → 파일 → grep/cat 처리                  │
└─────────────────────────────────────────────────┘
              ↓ offload
┌─────────────────────────────────────────────────┐
│  Level 3: Domain Implementations                │
│  ─────────────────────────────────              │
│  Python 런타임 활용                             │
│  • 대량 데이터 처리                             │
│  • 도메인별 비즈니스 로직                       │
│  • 외부 서비스 통합 (Neo4j, Qdrant)             │
└─────────────────────────────────────────────────┘
```

### 계층별 책임

| 계층 | 책임 | 노출 방식 | 컨텍스트 영향 |
|------|------|-----------|--------------|
| **Level 1** | 원자적 작업 | LangGraph `@tool` | 고정 10-20개 |
| **Level 2** | 복잡한 유틸리티 | CLI (`shell_execute`) | 0개 (함수 공간 X) |
| **Level 3** | 도메인 로직 | Python 스크립트 | 0개 (런타임만) |

---

## Level 1: Atomic Functions (원자적 함수)

### 설계 원칙

> [!important] Level 1의 철학
> - **최소성**: 10-20개만 유지 (절대 30개 초과 금지)
> - **원자성**: 분해 불가능한 기본 단위
> - **조합성**: 다른 함수와 조합 가능
> - **불변성**: 함수 시그니처 변경 최소화 (KV 캐시)

### 범용 Tool 추상화

```python
# packages/agent-tools/src/base/tool.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ToolMetadata(BaseModel):
    """도구 메타데이터"""
    name: str
    description: str
    level: int = Field(ge=1, le=3)  # 1, 2, 3
    domain_agnostic: bool = True
    tags: list[str] = []

class BaseTool(ABC):
    """
    모든 도구의 기본 추상 클래스

    Level 1 도구는 이를 직접 상속
    Level 2/3는 래퍼를 통해 간접 사용
    """

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """도구 메타데이터 반환"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """도구 실행 (비동기)"""
        pass

    def to_langchain_tool(self):
        """LangChain Tool 형식으로 변환"""
        from langchain_core.tools import tool

        @tool(name=self.metadata.name, description=self.metadata.description)
        async def wrapper(**kwargs):
            return await self.execute(**kwargs)

        return wrapper
```

### 도메인 독립적 Level 1 함수 설계

```python
# packages/agent-tools/src/level1/file_ops.py

from langchain_core.tools import tool
from pathlib import Path
from typing import Optional

@tool
async def file_read(
    path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
) -> str:
    """
    파일 읽기 (도메인 독립적)

    Args:
        path: 파일 경로
        start_line: 시작 라인 (선택)
        end_line: 종료 라인 (선택)

    Returns:
        파일 내용 또는 라인 범위
    """
    content = Path(path).read_text()

    if start_line or end_line:
        lines = content.splitlines()
        start = start_line or 0
        end = end_line or len(lines)
        return "\n".join(lines[start:end])

    return content

@tool
async def file_write(path: str, content: str, mode: str = "w") -> str:
    """
    파일 쓰기 (도메인 독립적)

    Args:
        path: 파일 경로
        content: 파일 내용
        mode: 쓰기 모드 ('w', 'a')

    Returns:
        성공 메시지
    """
    Path(path).write_text(content)
    return f"File written successfully: {path}"

@tool
async def file_list(directory: str, pattern: str = "*") -> list[str]:
    """
    디렉토리 파일 목록 (도메인 독립적)

    Args:
        directory: 디렉토리 경로
        pattern: glob 패턴

    Returns:
        파일 경로 리스트
    """
    return [str(p) for p in Path(directory).glob(pattern)]
```

### 검색 추상화

```python
# packages/agent-tools/src/level1/search.py

from langchain_core.tools import tool
from typing import List, Dict, Any

@tool
async def semantic_search(
    query: str,
    collection: str,
    top_k: int = 5,
    filters: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    """
    의미 기반 검색 (도메인 독립적)

    Args:
        query: 검색 쿼리
        collection: 검색 대상 컬렉션
        top_k: 반환 개수
        filters: 필터 조건 (선택)

    Returns:
        검색 결과 리스트 (id, score, metadata 포함)

    Note:
        실제 구현은 Level 3에서 주입됨 (DI 패턴)
    """
    # CLI 호출로 위임
    import subprocess
    import json

    cmd = [
        "knowledge-search",
        "--query", query,
        "--collection", collection,
        "--top-k", str(top_k)
    ]

    if filters:
        cmd.extend(["--filters", json.dumps(filters)])

    result = subprocess.run(cmd, capture_output=True, text=True)

    # 결과 파일 경로 반환 (컨텍스트 최소화!)
    output_file = result.stdout.strip()
    return f"Search results saved to: {output_file}. Use file_read to access."

@tool
async def keyword_search(
    keywords: str,
    collection: str,
    top_k: int = 5
) -> str:
    """
    키워드 검색 (도메인 독립적)

    Returns:
        검색 결과 파일 경로
    """
    # Level 2 CLI로 위임
    pass

@tool
async def hybrid_search(
    query: str,
    collection: str,
    top_k: int = 5,
    semantic_weight: float = 0.7
) -> str:
    """
    하이브리드 검색 (의미 + 키워드)

    Returns:
        검색 결과 파일 경로
    """
    # Level 2 CLI로 위임
    pass
```

### 실행 추상화

```python
# packages/agent-tools/src/level1/execute.py

from langchain_core.tools import tool

@tool
async def shell_execute(command: str, timeout: int = 30) -> str:
    """
    셸 명령 실행 (도메인 독립적)

    이것이 Level 2/3로 가는 관문!

    Args:
        command: 실행할 명령
        timeout: 타임아웃 (초)

    Returns:
        명령 출력 또는 출력 파일 경로
    """
    import subprocess
    import tempfile

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    # 출력이 크면 파일로 저장
    if len(result.stdout) > 1000:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(result.stdout)
            return f"Output saved to: {f.name}"

    return result.stdout

@tool
async def python_execute(script_path: str, args: list[str] | None = None) -> str:
    """
    Python 스크립트 실행 (Level 3 진입점)

    Args:
        script_path: 스크립트 경로
        args: 명령행 인자

    Returns:
        실행 결과
    """
    cmd = f"python {script_path}"
    if args:
        cmd += " " + " ".join(args)

    return await shell_execute(cmd)
```

---

## Level 2: CLI Utilities (셸 유틸리티)

### 설계 원칙

> [!tip] Level 2의 핵심
> - **함수 공간을 건드리지 않는다**: Level 1의 `shell_execute`로만 호출
> - **자가 문서화**: `--help`로 사용법 제공
> - **파일 기반 출력**: 큰 결과는 파일로 저장
> - **MCP 통합 지점**: MCP 도구를 여기서 래핑

### CLI 프레임워크

```python
# packages/agent-tools/src/level2/cli/base_cli.py

import click
from abc import ABC, abstractmethod
from pathlib import Path
import json

class BaseCLI(ABC):
    """
    모든 CLI 유틸리티의 기본 클래스
    """

    @abstractmethod
    def get_commands(self) -> list[click.Command]:
        """CLI 명령 리스트 반환"""
        pass

    def save_result(self, result: any, output_path: str | None = None) -> str:
        """
        결과를 파일로 저장 (컨텍스트 오프로드)

        Returns:
            파일 경로
        """
        if output_path is None:
            output_path = f"/tmp/agent_output_{hash(str(result))}.json"

        Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return output_path
```

### Knowledge Search CLI (범용 검색)

```python
# packages/agent-tools/src/level2/cli/knowledge_cli.py

import click
from typing import Optional
import json

@click.group()
def knowledge():
    """Knowledge base search utilities"""
    pass

@knowledge.command()
@click.option('--query', required=True, help='Search query')
@click.option('--collection', required=True, help='Collection name')
@click.option('--top-k', default=5, help='Number of results')
@click.option('--filters', type=str, help='JSON filters')
@click.option('--output', help='Output file path')
def search(query: str, collection: str, top_k: int, filters: Optional[str], output: Optional[str]):
    """
    Semantic search in knowledge base

    Example:
        knowledge-search search --query "LangChain" --collection blog_posts --top-k 5
    """
    from agent_tools.level3 import get_retriever

    # Level 3 구현체 가져오기 (DI)
    retriever = get_retriever(collection)

    # 검색 실행
    filter_dict = json.loads(filters) if filters else None
    results = retriever.search(query, top_k=top_k, filters=filter_dict)

    # 파일로 저장
    output_path = output or f"/tmp/search_results_{hash(query)}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 파일 경로만 출력 (컨텍스트 최소화!)
    click.echo(output_path)

@knowledge.command()
@click.option('--collection', required=True, help='Collection name')
def stats(collection: str):
    """Show collection statistics"""
    from agent_tools.level3 import get_retriever

    retriever = get_retriever(collection)
    stats = retriever.get_stats()

    click.echo(json.dumps(stats, indent=2))

@knowledge.command()
@click.argument('query')
@click.option('--collection', required=True)
@click.option('--output', help='Output file')
def hybrid(query: str, collection: str, output: Optional[str]):
    """
    Hybrid search (semantic + keyword)

    Example:
        knowledge-search hybrid "AI agents" --collection blog_posts
    """
    from agent_tools.level3 import get_hybrid_retriever

    retriever = get_hybrid_retriever(collection)
    results = retriever.hybrid_search(query)

    output_path = output or f"/tmp/hybrid_results_{hash(query)}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    click.echo(output_path)

if __name__ == '__main__':
    knowledge()
```

### MCP Wrapper CLI

```python
# packages/agent-tools/src/level2/cli/mcp_wrapper.py

import click
import subprocess
import json

@click.group()
def mcp():
    """MCP (Model Context Protocol) tools wrapper"""
    pass

@mcp.command()
def list_servers():
    """List all available MCP servers"""
    # MCP 서버 목록 조회
    pass

@mcp.command()
@click.argument('server')
def list_tools(server: str):
    """List tools in a specific MCP server"""
    pass

@mcp.command()
@click.argument('server')
@click.argument('tool')
@click.option('--args', type=str, help='JSON arguments')
@click.option('--output', help='Output file')
def call(server: str, tool: str, args: str, output: str):
    """
    Call an MCP tool

    Example:
        mcp-cli call github create-issue --args '{"title":"Bug","body":"..."}'
    """
    # MCP 도구 호출
    args_dict = json.loads(args) if args else {}
    result = call_mcp_tool(server, tool, args_dict)

    output_path = output or f"/tmp/mcp_result_{server}_{tool}.json"
    with open(output_path, 'w') as f:
        json.dump(result, f)

    click.echo(output_path)

if __name__ == '__main__':
    mcp()
```

---

## Level 3: Domain Implementations (도메인 구현)

### 설계 원칙

> [!important] Level 3의 역할
> - **도메인별 비즈니스 로직**: 블로그, 전자상거래, 헬스케어 등
> - **외부 서비스 통합**: Neo4j, Qdrant, Milvus 등
> - **대량 데이터 처리**: Python 런타임 메모리 활용
> - **컨텍스트 오프로드**: 결과는 파일이나 요약으로

### 검색 추상화 인터페이스

```python
# packages/agent-tools/src/base/retriever.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    """검색 결과 표준 형식"""
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    source: str  # 'vector', 'keyword', 'hybrid', 'graph'

class BaseRetriever(ABC):
    """
    모든 검색 시스템의 추상 인터페이스

    도메인에 관계없이 동일한 인터페이스 제공
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """의미 기반 검색"""
        pass

    @abstractmethod
    async def keyword_search(
        self,
        keywords: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """키워드 검색"""
        pass

    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """하이브리드 검색 (의미 + 키워드)"""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """컬렉션 통계"""
        return {}
```

### Neo4j + Qdrant 하이브리드 구현 (블로그 도메인)

```python
# packages/agent-tools/src/level3/blog/hybrid_retriever.py

from agent_tools.base.retriever import BaseRetriever, SearchResult
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from neo4j import GraphDatabase

class BlogHybridRetriever(BaseRetriever):
    """
    블로그 검색 시스템: Neo4j (그래프) + Qdrant (벡터)

    - Qdrant: 의미 기반 벡터 검색
    - Neo4j: 그래프 관계 탐색 (백링크, 태그 네트워크)
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        neo4j_driver: GraphDatabase.driver,
        collection_name: str = "blog_posts"
    ):
        self.qdrant = qdrant_client
        self.neo4j = neo4j_driver
        self.collection = collection_name

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        1단계: Qdrant 벡터 검색
        """
        from openai import OpenAI

        # 쿼리 임베딩
        client = OpenAI()
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding

        # Qdrant 검색
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=embedding,
            limit=top_k,
            query_filter=filters
        )

        # 표준 형식으로 변환
        return [
            SearchResult(
                id=r.id,
                score=r.score,
                content=r.payload.get('content', ''),
                metadata=r.payload,
                source='vector'
            )
            for r in results
        ]

    async def keyword_search(
        self,
        keywords: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        2단계: Neo4j Full-text 검색
        """
        with self.neo4j.session() as session:
            result = session.run("""
                CALL db.index.fulltext.queryNodes('blog_fulltext', $keywords)
                YIELD node, score
                RETURN node.id as id, node.title as title,
                       node.content as content, score
                LIMIT $top_k
            """, keywords=keywords, top_k=top_k)

            return [
                SearchResult(
                    id=record['id'],
                    score=record['score'],
                    content=record['content'],
                    metadata={'title': record['title']},
                    source='keyword'
                )
                for record in result
            ]

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        3단계: 하이브리드 (Qdrant + Neo4j)
        """
        # 병렬 검색
        vector_results = await self.search(query, top_k=top_k*2)
        keyword_results = await self.keyword_search(query, top_k=top_k*2)

        # 점수 정규화 및 병합
        combined = self._merge_results(
            vector_results,
            keyword_results,
            semantic_weight
        )

        return combined[:top_k]

    async def graph_expand(
        self,
        post_ids: List[str],
        depth: int = 1
    ) -> List[SearchResult]:
        """
        4단계: 그래프 확장 (Neo4j 백링크)

        벡터 검색 결과를 Neo4j로 확장
        """
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (p:BlogPost)-[r:REFERENCES|TAGGED_WITH*1..{depth}]-(related:BlogPost)
                WHERE p.id IN $post_ids
                RETURN DISTINCT related.id as id,
                       related.title as title,
                       related.content as content,
                       COUNT(r) as connection_strength
                ORDER BY connection_strength DESC
                LIMIT 10
            """, post_ids=post_ids, depth=depth)

            return [
                SearchResult(
                    id=record['id'],
                    score=record['connection_strength'] / 10.0,
                    content=record['content'],
                    metadata={
                        'title': record['title'],
                        'connection_strength': record['connection_strength']
                    },
                    source='graph'
                )
                for record in result
            ]

    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        semantic_weight: float
    ) -> List[SearchResult]:
        """점수 정규화 및 병합"""
        # RRF (Reciprocal Rank Fusion) 알고리즘
        from collections import defaultdict

        scores = defaultdict(float)
        contents = {}

        # Vector 점수
        for rank, result in enumerate(vector_results):
            scores[result.id] += semantic_weight / (rank + 60)
            contents[result.id] = result

        # Keyword 점수
        for rank, result in enumerate(keyword_results):
            scores[result.id] += (1 - semantic_weight) / (rank + 60)
            if result.id not in contents:
                contents[result.id] = result

        # 정렬
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        return [
            SearchResult(
                **contents[id].dict(),
                score=scores[id],
                source='hybrid'
            )
            for id in sorted_ids
        ]
```

### Python 스크립트 예시 (Level 3)

```python
# packages/agent-tools/src/level3/blog/scripts/analyze_blog_network.py

"""
블로그 포스트 네트워크 분석 스크립트

Level 1에서 호출:
    python_execute("analyze_blog_network.py", ["--output", "network_stats.json"])
"""

import click
import json
from neo4j import GraphDatabase

@click.command()
@click.option('--output', default='network_stats.json', help='Output file')
def analyze(output: str):
    """블로그 포스트 네트워크 분석"""

    driver = GraphDatabase.driver("bolt://localhost:7687")

    with driver.session() as session:
        # 네트워크 통계 계산
        result = session.run("""
            MATCH (p:BlogPost)
            OPTIONAL MATCH (p)-[r:REFERENCES]->(other)
            RETURN
                COUNT(DISTINCT p) as total_posts,
                COUNT(r) as total_links,
                AVG(SIZE((p)-[:REFERENCES]->()) as avg_outbound_links,
                AVG(SIZE((p)<-[:REFERENCES]-()) as avg_inbound_links
        """)

        stats = result.single()

        # 중심성 높은 포스트
        central_posts = session.run("""
            MATCH (p:BlogPost)
            RETURN p.id, p.title,
                   SIZE((p)<-[:REFERENCES]-()) as inbound_count
            ORDER BY inbound_count DESC
            LIMIT 10
        """)

        output_data = {
            'network_stats': dict(stats),
            'central_posts': [dict(r) for r in central_posts]
        }

        # 파일로 저장
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2)

        click.echo(f"Analysis saved to: {output}")

if __name__ == '__main__':
    analyze()
```

---

## 의존성 주입 (DI) 패턴

### Retriever Factory

```python
# packages/agent-tools/src/level3/__init__.py

from typing import Dict, Type
from agent_tools.base.retriever import BaseRetriever

# 도메인별 Retriever 등록
_RETRIEVER_REGISTRY: Dict[str, Type[BaseRetriever]] = {}

def register_retriever(collection: str, retriever_class: Type[BaseRetriever]):
    """Retriever 등록"""
    _RETRIEVER_REGISTRY[collection] = retriever_class

def get_retriever(collection: str) -> BaseRetriever:
    """Retriever 가져오기 (DI)"""
    if collection not in _RETRIEVER_REGISTRY:
        raise ValueError(f"No retriever registered for collection: {collection}")

    return _RETRIEVER_REGISTRY[collection]()

# 블로그 도메인 등록
from agent_tools.level3.blog.hybrid_retriever import BlogHybridRetriever

register_retriever("blog_posts", BlogHybridRetriever)
```

---

## 프로젝트 구조 최종 확정

### Monorepo 구조 (추천)

```
apphub/
├── apps/
│   ├── web/                      # Next.js
│   └── ai-service/               # LangGraph Agent
│       ├── src/
│       │   └── agent/
│       │       └── graph.py      # Level 1 도구 등록
│       └── pyproject.toml
│
├── packages/
│   └── agent-tools/              # 새로 추가! ⭐
│       ├── src/
│       │   ├── agent_tools/
│       │   │   ├── __init__.py
│       │   │   │
│       │   │   ├── base/         # 추상 기본 클래스
│       │   │   │   ├── __init__.py
│       │   │   │   ├── tool.py
│       │   │   │   ├── retriever.py
│       │   │   │   └── storage.py
│       │   │   │
│       │   │   ├── level1/       # Atomic Functions
│       │   │   │   ├── __init__.py
│       │   │   │   ├── file_ops.py
│       │   │   │   ├── search.py
│       │   │   │   └── execute.py
│       │   │   │
│       │   │   ├── level2/       # CLI Utilities
│       │   │   │   ├── __init__.py
│       │   │   │   └── cli/
│       │   │   │       ├── base_cli.py
│       │   │   │       ├── knowledge_cli.py
│       │   │   │       └── mcp_wrapper.py
│       │   │   │
│       │   │   └── level3/       # Domain Implementations
│       │   │       ├── __init__.py
│       │   │       └── blog/
│       │   │           ├── __init__.py
│       │   │           ├── hybrid_retriever.py
│       │   │           ├── neo4j_ops.py
│       │   │           ├── qdrant_ops.py
│       │   │           └── scripts/
│       │   │               └── analyze_blog_network.py
│       │   │
│       │   └── bin/              # CLI 진입점
│       │       ├── knowledge-search
│       │       └── mcp-cli
│       │
│       ├── tests/
│       ├── pyproject.toml
│       └── README.md
│
├── compose.yaml
└── docs/
```

### pyproject.toml 설정

```toml
# packages/agent-tools/pyproject.toml

[project]
name = "apphub-agent-tools"
version = "0.1.0"
description = "Domain-agnostic Agent Tools with 3-tier architecture (Manus pattern)"
authors = [{ name = "AppHub Team", email = "syshin0116@gmail.com" }]
requires-python = ">=3.11"

dependencies = [
    # LangChain/LangGraph
    "langchain>=1.0.0",
    "langgraph>=1.0.2",
    "langchain-openai>=0.3.35",

    # CLI
    "click>=8.1.0",

    # Vector DB
    "qdrant-client>=1.7.0",

    # Graph DB
    "neo4j>=5.14.0",

    # Utils
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8.0",
    "ruff>=0.1.0",
]

[project.scripts]
knowledge-search = "agent_tools.level2.cli.knowledge_cli:knowledge"
mcp-cli = "agent_tools.level2.cli.mcp_wrapper:mcp"

[build-system]
requires = ["setuptools>=70.0.0", "wheel"]
build-backend = "setuptools.build_meta"
```

---

## 사용 예시

### LangGraph Agent에서 사용

```python
# apps/ai-service/src/agent/graph.py

from langgraph.graph import StateGraph, MessagesState
from agent_tools.level1 import (
    file_read, file_write, file_list,
    semantic_search, hybrid_search,
    shell_execute, python_execute
)

# Level 1 도구만 등록 (10-20개)
TOOLS = [
    file_read,
    file_write,
    file_list,
    semantic_search,
    hybrid_search,
    shell_execute,
    python_execute,
]

# Agent 정의
def create_agent():
    workflow = StateGraph(MessagesState)

    # ... (agent 로직)

    return workflow.compile()
```

### CLI 사용 (Level 2)

```bash
# 블로그 검색
$ knowledge-search search --query "LangChain v1.0" --collection blog_posts --top-k 5
/tmp/search_results_12345.json

# 결과 확인 (Level 1 file_read 사용)
$ cat /tmp/search_results_12345.json
[
  {
    "id": "langchain-v1-update",
    "score": 0.92,
    "content": "...",
    "metadata": {"title": "LangChain v1.0 업데이트", "date": "2025-11-02"}
  },
  ...
]

# 하이브리드 검색
$ knowledge-search hybrid "AI agents" --collection blog_posts
/tmp/hybrid_results_67890.json

# 네트워크 분석 (Level 3 Python 스크립트)
$ python packages/agent-tools/src/level3/blog/scripts/analyze_blog_network.py
Analysis saved to: network_stats.json
```

### Agent가 사용하는 모습

```
User: "LangChain v1.0에 대한 내 블로그 글 찾아줘"

Agent (내부 사고):
  1. semantic_search 호출 (Level 1)
     → query="LangChain v1.0", collection="blog_posts"

  2. 파일 경로 반환받음
     → /tmp/search_results_12345.json

  3. file_read 호출 (Level 1)
     → path="/tmp/search_results_12345.json"

  4. 검색 결과 분석 후 답변

Agent Response: "네, 3개의 관련 글을 찾았습니다:
1. LangChain v1.0 & LangGraph v1.0 업데이트 (2025-11-02)
2. AppHub 기술 스택 (2025-10-07)
3. Context Engineering for AI Agents (2025-10-26)

가장 최근 글은 'LangChain v1.0 & LangGraph v1.0 업데이트'입니다."
```

---

## 다음 단계

### 1주차: 기본 구조 구축
- [ ] `packages/agent-tools` 디렉토리 생성
- [ ] Base 클래스 구현 (BaseTool, BaseRetriever)
- [ ] Level 1 원자적 함수 10개 구현
- [ ] pyproject.toml 설정

### 2주차: CLI & Level 2
- [ ] knowledge-search CLI 구현
- [ ] mcp-cli 래퍼 구현
- [ ] 파일 기반 출력 테스트

### 3주차: 블로그 도메인 (Level 3)
- [ ] BlogHybridRetriever 구현
- [ ] Neo4j + Qdrant 통합
- [ ] 네트워크 분석 스크립트

### 4주차: 통합 & 테스트
- [ ] LangGraph Agent 통합
- [ ] End-to-end 테스트
- [ ] 성능 측정 및 최적화

---

## 참고 자료

- [[2025-10-26-context-engineering-for-ai-agents]] - Manus 3계층 패턴
- [[2025-11-02-LangChain-LangGraph-v1-업데이트]] - 최신 기술 스택
- [[2025-10-07-AppHub-구조-및-기술-스택]] - 전체 아키텍처

---

> [!quote] Build less, understand more
> 과잉 엔지니어링을 피하고, 단순하면서도 강력한 아키텍처를 유지한다. 도구는 컨텍스트를 차지한다는 사실을 항상 기억하라.
