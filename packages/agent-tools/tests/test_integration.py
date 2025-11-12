"""Integration tests for agent-tools with real agent usage"""

import pytest
from agent_tools import SessionSandbox, create_atomic_tools


def test_full_workflow():
    """전체 워크플로우 테스트: 파일 생성 → 검색 → 읽기"""
    # 1. 샌드박스 생성
    sandbox = SessionSandbox(user_id="integration_test", session_id="workflow")

    # 2. 도구 생성
    tools = create_atomic_tools(sandbox)
    file_write = next(t for t in tools if t.name == "file_write")
    file_list = next(t for t in tools if t.name == "file_list")
    file_read = next(t for t in tools if t.name == "file_read")
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # 3. 여러 파일 생성
    file_write.invoke({"path": "note1.txt", "content": "First note"})
    file_write.invoke({"path": "note2.txt", "content": "Second note"})
    file_write.invoke({"path": "data.json", "content": '{"key": "value"}'})

    # 4. 파일 목록 확인
    result = file_list.invoke({"directory": ".", "pattern": "*.txt"})
    assert "note1.txt" in result
    assert "note2.txt" in result
    assert "data.json" not in result

    # 5. grep으로 검색
    result = shell_execute.invoke({"command": "grep -r 'Second' ."})
    assert "Second" in result
    assert "note2.txt" in result

    # 6. 파일 읽기
    result = file_read.invoke({"path": "note2.txt"})
    assert result == "Second note"

    # Cleanup
    sandbox.cleanup()


def test_shell_execute_data_processing():
    """셸 명령으로 데이터 처리"""
    sandbox = SessionSandbox(user_id="test", session_id="dataproc")
    tools = create_atomic_tools(sandbox)

    file_write = next(t for t in tools if t.name == "file_write")
    shell_execute = next(t for t in tools if t.name == "shell_execute")
    file_read = next(t for t in tools if t.name == "file_read")

    # CSV 데이터 생성
    csv_data = """name,age,city
Alice,30,Seoul
Bob,25,Busan
Charlie,35,Seoul"""

    file_write.invoke({"path": "data.csv", "content": csv_data})

    # awk로 Seoul만 필터링
    result = shell_execute.invoke({
        "command": "awk -F',' '$3 == \"Seoul\"' data.csv"
    })

    assert "Alice" in result
    assert "Charlie" in result
    assert "Bob" not in result

    # Cleanup
    sandbox.cleanup()


def test_python_script_execution():
    """Python 스크립트 실행 (Level 3 시뮬레이션)"""
    sandbox = SessionSandbox(user_id="test", session_id="python")
    tools = create_atomic_tools(sandbox)

    file_write = next(t for t in tools if t.name == "file_write")
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # Python 스크립트 작성
    script = """
import json

data = {
    "message": "Hello from Python",
    "numbers": [1, 2, 3, 4, 5],
    "sum": sum([1, 2, 3, 4, 5])
}

print(json.dumps(data, indent=2))
"""

    file_write.invoke({"path": "analyze.py", "content": script})

    # 스크립트 실행
    result = shell_execute.invoke({"command": "python3 analyze.py"})

    assert "Hello from Python" in result
    assert '"sum": 15' in result

    # Cleanup
    sandbox.cleanup()


def test_context_offloading_large_output():
    """큰 출력은 파일로 저장되는지 확인"""
    sandbox = SessionSandbox(user_id="test", session_id="offload")
    tools = create_atomic_tools(sandbox)

    shell_execute = next(t for t in tools if t.name == "shell_execute")
    file_read = next(t for t in tools if t.name == "file_read")

    # 큰 출력 생성 (2000자)
    result = shell_execute.invoke({
        "command": "python3 -c 'print(\"A\" * 2000)'"
    })

    # 파일로 저장되었는지 확인
    assert "Output saved to file" in result
    assert "output_" in result
    assert ".txt" in result

    # file_read 사용법 안내
    assert "file_read" in result

    # Cleanup
    sandbox.cleanup()


def test_security_isolation():
    """보안 격리 확인"""
    sandbox1 = SessionSandbox(user_id="alice", session_id="sec1")
    sandbox2 = SessionSandbox(user_id="bob", session_id="sec2")

    tools1 = create_atomic_tools(sandbox1)
    tools2 = create_atomic_tools(sandbox2)

    file_write1 = next(t for t in tools1 if t.name == "file_write")
    file_read2 = next(t for t in tools2 if t.name == "file_read")

    # Alice가 비밀 파일 생성
    file_write1.invoke({"path": "secret.txt", "content": "Alice's secret"})

    # Bob이 Alice 파일 읽기 시도 (절대 경로)
    alice_file = str(sandbox1.sandbox_dir / "secret.txt")
    result = file_read2.invoke({"path": alice_file})

    # 접근 거부되어야 함
    assert "❌" in result
    assert "Access denied" in result

    # Cleanup
    sandbox1.cleanup()
    sandbox2.cleanup()


def test_real_world_scenario_log_analysis():
    """실전 시나리오: 로그 분석"""
    sandbox = SessionSandbox(user_id="test", session_id="logs")
    tools = create_atomic_tools(sandbox)

    file_write = next(t for t in tools if t.name == "file_write")
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # 로그 파일 생성
    log_data = """2025-11-12 10:00:00 INFO User login: alice
2025-11-12 10:05:00 ERROR Database connection failed
2025-11-12 10:10:00 INFO User logout: alice
2025-11-12 10:15:00 ERROR API timeout: /api/search
2025-11-12 10:20:00 INFO User login: bob
2025-11-12 10:25:00 ERROR Database connection failed"""

    file_write.invoke({"path": "app.log", "content": log_data})

    # 1. ERROR만 필터링
    result = shell_execute.invoke({"command": "grep ERROR app.log"})
    assert result.count("ERROR") == 3

    # 2. ERROR 개수 세기
    result = shell_execute.invoke({"command": "grep -c ERROR app.log"})
    assert "3" in result

    # 3. Database ERROR만 필터링
    result = shell_execute.invoke({
        "command": "grep ERROR app.log | grep Database"
    })
    assert result.count("Database connection failed") == 2

    # Cleanup
    sandbox.cleanup()
