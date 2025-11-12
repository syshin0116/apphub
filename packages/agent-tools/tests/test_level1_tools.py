"""Tests for Level 1 Atomic Tools"""

import pytest
from agent_tools import SessionSandbox, create_atomic_tools


@pytest.fixture
def sandbox():
    """테스트용 샌드박스 생성"""
    sb = SessionSandbox(user_id="test", session_id="level1")
    yield sb
    sb.cleanup()


@pytest.fixture
def tools(sandbox):
    """테스트용 도구 생성"""
    return create_atomic_tools(sandbox)


def test_create_atomic_tools(tools):
    """4개 도구 생성 확인"""
    assert len(tools) == 4

    tool_names = [t.name for t in tools]
    assert "file_read" in tool_names
    assert "file_write" in tool_names
    assert "file_list" in tool_names
    assert "shell_execute" in tool_names


def test_file_write_and_read(tools, sandbox):
    """파일 쓰기 및 읽기"""
    file_write = next(t for t in tools if t.name == "file_write")
    file_read = next(t for t in tools if t.name == "file_read")

    # 파일 쓰기
    result = file_write.invoke({"path": "test.txt", "content": "Hello World"})
    assert "✓" in result
    assert "test.txt" in result

    # 파일 읽기
    result = file_read.invoke({"path": "test.txt"})
    assert result == "Hello World"


def test_file_write_creates_directories(tools, sandbox):
    """중첩 디렉토리 자동 생성"""
    file_write = next(t for t in tools if t.name == "file_write")
    file_read = next(t for t in tools if t.name == "file_read")

    # 중첩 디렉토리에 파일 쓰기
    result = file_write.invoke({
        "path": "a/b/c/deep.txt",
        "content": "Deep file"
    })
    assert "✓" in result

    # 읽기 확인
    result = file_read.invoke({"path": "a/b/c/deep.txt"})
    assert result == "Deep file"


def test_file_read_nonexistent(tools):
    """존재하지 않는 파일 읽기"""
    file_read = next(t for t in tools if t.name == "file_read")

    result = file_read.invoke({"path": "nonexistent.txt"})
    assert "❌" in result
    assert "not found" in result.lower()


def test_file_read_path_traversal(tools):
    """Path traversal 공격 차단"""
    file_read = next(t for t in tools if t.name == "file_read")

    result = file_read.invoke({"path": "../../../etc/passwd"})
    assert "❌" in result
    assert "Access denied" in result


def test_file_list_default(tools, sandbox):
    """파일 목록 조회 (기본)"""
    file_write = next(t for t in tools if t.name == "file_write")
    file_list = next(t for t in tools if t.name == "file_list")

    # 파일 생성
    file_write.invoke({"path": "file1.txt", "content": "A"})
    file_write.invoke({"path": "file2.json", "content": "{}"})
    file_write.invoke({"path": "file3.md", "content": "# Title"})

    # 모든 파일 조회
    result = file_list.invoke({"directory": ".", "pattern": "*"})
    assert "file1.txt" in result
    assert "file2.json" in result
    assert "file3.md" in result


def test_file_list_pattern(tools, sandbox):
    """파일 목록 조회 (패턴)"""
    file_write = next(t for t in tools if t.name == "file_write")
    file_list = next(t for t in tools if t.name == "file_list")

    # 파일 생성
    file_write.invoke({"path": "data1.json", "content": "{}"})
    file_write.invoke({"path": "data2.json", "content": "{}"})
    file_write.invoke({"path": "readme.txt", "content": "text"})

    # JSON 파일만 조회
    result = file_list.invoke({"directory": ".", "pattern": "*.json"})
    assert "data1.json" in result
    assert "data2.json" in result
    assert "readme.txt" not in result


def test_shell_execute_simple(tools):
    """간단한 셸 명령 실행"""
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    result = shell_execute.invoke({"command": "echo 'Hello from shell'"})
    assert "Hello from shell" in result


def test_shell_execute_with_file(tools, sandbox):
    """셸 명령으로 파일 생성 및 확인"""
    shell_execute = next(t for t in tools if t.name == "shell_execute")
    file_read = next(t for t in tools if t.name == "file_read")

    # echo로 파일 생성
    result = shell_execute.invoke({"command": "echo 'Shell output' > shell.txt"})

    # 파일 읽기
    content = file_read.invoke({"path": "shell.txt"})
    assert "Shell output" in content


def test_shell_execute_large_output(tools):
    """큰 출력은 파일로 저장 (Context Offloading)"""
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # 큰 출력 생성 (1000자 초과)
    result = shell_execute.invoke({"command": "python3 -c 'print(\"A\" * 2000)'"})

    # 파일로 저장되었는지 확인
    assert "Output saved to file" in result
    assert "file_read" in result
    assert ".txt" in result


def test_shell_execute_grep(tools, sandbox):
    """grep 명령 테스트"""
    file_write = next(t for t in tools if t.name == "file_write")
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # 테스트 파일 생성
    file_write.invoke({"path": "code.py", "content": "# TODO: implement\nprint('hello')\n# FIXME: bug"})
    file_write.invoke({"path": "readme.md", "content": "# README\nNo todos here"})

    # grep으로 TODO 검색
    result = shell_execute.invoke({"command": "grep -r 'TODO' ."})
    assert "TODO" in result
    assert "code.py" in result


def test_shell_execute_find(tools, sandbox):
    """find 명령 테스트"""
    file_write = next(t for t in tools if t.name == "file_write")
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # 파일 생성
    file_write.invoke({"path": "test.py", "content": "pass"})
    file_write.invoke({"path": "main.py", "content": "pass"})
    file_write.invoke({"path": "readme.txt", "content": "text"})

    # find로 .py 파일 검색
    result = shell_execute.invoke({"command": "find . -name '*.py'"})
    assert "test.py" in result
    assert "main.py" in result
    assert "readme.txt" not in result
