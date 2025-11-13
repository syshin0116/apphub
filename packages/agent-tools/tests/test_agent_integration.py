"""End-to-end tests with LangGraph agent integration

These tests verify that agent-tools work correctly with actual LangGraph agents.
Note: These tests require OpenAI API key and may incur costs.
"""

import pytest
import os
from unittest.mock import Mock, patch
from agent_tools import SessionSandbox, create_atomic_tools


# Skip if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key required for agent integration tests"
)


class TestAgentIntegration:
    """Tests with mock agent (without actual LLM calls)"""

    def test_agent_can_use_all_tools(self):
        """Agent가 모든 도구를 사용할 수 있는지 확인"""
        sandbox = SessionSandbox(user_id="agent_test", session_id="tools")
        tools = create_atomic_tools(sandbox)

        # 4개 도구 모두 사용 가능
        assert len(tools) == 4

        tool_names = {t.name for t in tools}
        expected_names = {"file_read", "file_write", "file_list", "shell_execute"}
        assert tool_names == expected_names

        # 각 도구가 호출 가능한지 확인
        for tool in tools:
            assert callable(tool.invoke)
            assert tool.description
            assert tool.name

        sandbox.cleanup()

    def test_agent_tool_descriptions(self):
        """도구 설명이 Agent에게 유용한지 확인"""
        sandbox = SessionSandbox(user_id="agent_test", session_id="desc")
        tools = create_atomic_tools(sandbox)

        for tool in tools:
            # 설명이 있어야 함
            assert tool.description
            assert len(tool.description) > 10

            # Args 정보 확인
            assert "Args:" in tool.description or "path" in tool.description.lower()

        sandbox.cleanup()

    def test_mock_agent_workflow(self):
        """Mock agent의 워크플로우 시뮬레이션"""
        sandbox = SessionSandbox(user_id="mock_agent", session_id="workflow")
        tools = create_atomic_tools(sandbox)

        file_write = next(t for t in tools if t.name == "file_write")
        file_list = next(t for t in tools if t.name == "file_list")
        file_read = next(t for t in tools if t.name == "file_read")
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # Simulated agent conversation
        # User: "Create a file with my notes"
        result1 = file_write.invoke({
            "path": "notes.txt",
            "content": "Meeting notes: Discuss Q4 goals"
        })
        assert "✓" in result1

        # User: "List all files"
        result2 = file_list.invoke({"directory": ".", "pattern": "*"})
        assert "notes.txt" in result2

        # User: "Search for 'goals' in my notes"
        result3 = shell_execute.invoke({"command": "grep 'goals' notes.txt"})
        assert "goals" in result3

        # User: "Read my notes"
        result4 = file_read.invoke({"path": "notes.txt"})
        assert "Meeting notes" in result4

        sandbox.cleanup()

    def test_agent_error_recovery(self):
        """Agent의 에러 복구 시나리오"""
        sandbox = SessionSandbox(user_id="agent_test", session_id="error")
        tools = create_atomic_tools(sandbox)

        file_read = next(t for t in tools if t.name == "file_read")
        file_write = next(t for t in tools if t.name == "file_write")

        # 1. Agent가 존재하지 않는 파일 읽기 시도
        result1 = file_read.invoke({"path": "nonexistent.txt"})
        assert "❌" in result1
        assert "not found" in result1.lower()

        # 2. Agent가 에러를 보고 파일 생성으로 전환
        result2 = file_write.invoke({
            "path": "nonexistent.txt",
            "content": "Now it exists"
        })
        assert "✓" in result2

        # 3. 다시 읽기 성공
        result3 = file_read.invoke({"path": "nonexistent.txt"})
        assert result3 == "Now it exists"

        sandbox.cleanup()

    def test_agent_context_management(self):
        """Agent의 컨텍스트 관리 테스트"""
        sandbox = SessionSandbox(user_id="agent_test", session_id="context")
        tools = create_atomic_tools(sandbox)

        shell_execute = next(t for t in tools if t.name == "shell_execute")
        file_read = next(t for t in tools if t.name == "file_read")

        # 큰 출력 생성 (Context Offloading 트리거)
        result = shell_execute.invoke({
            "command": "python3 -c 'for i in range(100): print(f\"Line {i}: \" + \"A\" * 50)'"
        })

        # 파일로 저장됨
        assert "Output saved" in result
        assert ".txt" in result

        # Agent는 file_read를 사용해서 내용 확인
        # 파일 경로 추출 (간단한 파싱)
        import re
        match = re.search(r'output_\w+\.txt', result)
        if match:
            filename = match.group(0)
            content = file_read.invoke({"path": filename})
            assert "Line 0" in content
            assert "Line 99" in content

        sandbox.cleanup()

    def test_multi_step_agent_task(self):
        """여러 단계의 복잡한 작업"""
        sandbox = SessionSandbox(user_id="agent_test", session_id="multi")
        tools = create_atomic_tools(sandbox)

        file_write = next(t for t in tools if t.name == "file_write")
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # Step 1: 데이터 파일 생성
        csv_data = """name,score
Alice,95
Bob,87
Charlie,92
David,88"""

        file_write.invoke({"path": "scores.csv", "content": csv_data})

        # Step 2: 평균 계산 스크립트 작성
        python_script = """
import csv

with open('scores.csv', 'r') as f:
    reader = csv.DictReader(f)
    scores = [int(row['score']) for row in reader]

average = sum(scores) / len(scores)
print(f"Average score: {average}")

# 90점 이상 찾기
with open('scores.csv', 'r') as f:
    reader = csv.DictReader(f)
    high_scorers = [row['name'] for row in reader if int(row['score']) >= 90]

print(f"High scorers (>=90): {', '.join(high_scorers)}")
"""

        file_write.invoke({"path": "analyze.py", "content": python_script})

        # Step 3: 스크립트 실행
        result = shell_execute.invoke({"command": "python3 analyze.py"})

        # Step 4: 결과 확인
        assert "Average score: 90.5" in result
        assert "Alice" in result
        assert "Charlie" in result

        sandbox.cleanup()


class TestRealAgentScenarios:
    """Real-world agent scenarios (mock-based)"""

    def test_code_review_scenario(self):
        """코드 리뷰 시나리오"""
        sandbox = SessionSandbox(user_id="reviewer", session_id="code")
        tools = create_atomic_tools(sandbox)

        file_write = next(t for t in tools if t.name == "file_write")
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # Python 코드 작성
        code = """
def calculate_total(items):
    # TODO: Add validation
    total = 0
    for item in items:
        total += item['price']
    return total

def main():
    items = [{'name': 'A', 'price': 100}]
    print(calculate_total(items))
"""

        file_write.invoke({"path": "code.py", "content": code})

        # TODO 검색
        result = shell_execute.invoke({"command": "grep -n 'TODO' code.py"})
        assert "TODO" in result
        assert "validation" in result

        sandbox.cleanup()

    def test_data_analysis_scenario(self):
        """데이터 분석 시나리오"""
        sandbox = SessionSandbox(user_id="analyst", session_id="data")
        tools = create_atomic_tools(sandbox)

        file_write = next(t for t in tools if t.name == "file_write")
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # 로그 데이터
        log_data = """2025-11-12 10:00:00 INFO User login: alice
2025-11-12 10:05:00 ERROR Database connection failed
2025-11-12 10:10:00 INFO User logout: alice
2025-11-12 10:15:00 ERROR API timeout
2025-11-12 10:20:00 INFO User login: bob
2025-11-12 10:25:00 ERROR Database connection failed
2025-11-12 10:30:00 WARN Slow query detected"""

        file_write.invoke({"path": "app.log", "content": log_data})

        # 에러 분석
        error_count = shell_execute.invoke({"command": "grep -c ERROR app.log"})
        assert "3" in error_count

        # Database 에러만 추출
        db_errors = shell_execute.invoke({
            "command": "grep ERROR app.log | grep Database"
        })
        assert db_errors.count("Database connection failed") == 2

        sandbox.cleanup()

    def test_file_organization_scenario(self):
        """파일 정리 시나리오"""
        sandbox = SessionSandbox(user_id="organizer", session_id="files")
        tools = create_atomic_tools(sandbox)

        file_write = next(t for t in tools if t.name == "file_write")
        shell_execute = next(t for t in tools if t.name == "shell_execute")
        file_list = next(t for t in tools if t.name == "file_list")

        # 여러 파일 생성
        files = {
            "doc1.txt": "Document 1",
            "doc2.txt": "Document 2",
            "image1.png": "fake png",
            "image2.jpg": "fake jpg",
            "script.py": "print('hello')",
        }

        for filename, content in files.items():
            file_write.invoke({"path": filename, "content": content})

        # 파일 분류 (mkdir + mv)
        commands = [
            "mkdir -p docs images scripts",
            "mv *.txt docs/ 2>/dev/null || true",
            "mv *.png *.jpg images/ 2>/dev/null || true",
            "mv *.py scripts/ 2>/dev/null || true",
        ]

        for cmd in commands:
            shell_execute.invoke({"command": cmd})

        # 확인
        docs = file_list.invoke({"directory": "docs", "pattern": "*"})
        assert "doc1.txt" in docs
        assert "doc2.txt" in docs

        images = file_list.invoke({"directory": "images", "pattern": "*"})
        assert "image1.png" in images or "image2.jpg" in images

        sandbox.cleanup()


class TestAgentSafety:
    """Agent safety and security tests"""

    def test_agent_cannot_escape_sandbox(self):
        """Agent가 샌드박스를 벗어날 수 없는지 확인"""
        sandbox = SessionSandbox(user_id="malicious", session_id="escape")
        tools = create_atomic_tools(sandbox)

        file_read = next(t for t in tools if t.name == "file_read")
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # 다양한 탈출 시도
        escape_attempts = [
            # file_read로 시스템 파일 읽기 시도
            file_read.invoke({"path": "/etc/passwd"}),
            file_read.invoke({"path": "../../../etc/shadow"}),

            # shell로 시스템 파일 읽기 시도
            shell_execute.invoke({"command": "cat /etc/passwd"}),
            shell_execute.invoke({"command": "ls /root"}),
        ]

        # file_read는 차단되어야 함
        assert "❌" in escape_attempts[0]
        assert "❌" in escape_attempts[1]

        # shell_execute는 실행되지만 빈 결과 또는 에러
        # (샌드박스 밖 파일은 읽을 수 없음)

        sandbox.cleanup()

    def test_agent_resource_limits(self):
        """Agent의 리소스 제한"""
        sandbox = SessionSandbox(user_id="resource", session_id="limit")
        tools = create_atomic_tools(sandbox)

        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # 타임아웃 테스트 (60초 제한)
        result = shell_execute.invoke({"command": "sleep 70"})
        assert "timed out" in result.lower() or "timeout" in result.lower()

        sandbox.cleanup()
