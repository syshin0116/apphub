"""Tests for SessionSandbox"""

import pytest
from pathlib import Path
from agent_tools.sandbox import SessionSandbox


def test_sandbox_creation():
    """샌드박스 디렉토리 생성 확인"""
    sandbox = SessionSandbox(user_id="test_user", session_id="test_session")

    assert sandbox.user_id == "test_user"
    assert sandbox.session_id == "test_session"
    assert sandbox.sandbox_dir.exists()
    assert sandbox.sandbox_dir.name == "session-test_user-test_session"

    # Cleanup
    sandbox.cleanup()
    assert not sandbox.sandbox_dir.exists()


def test_get_safe_path_relative():
    """상대 경로가 샌드박스 안에 있는지 확인"""
    sandbox = SessionSandbox(user_id="test", session_id="rel")

    # 상대 경로 - 안전
    safe_path = sandbox.get_safe_path("data.json")
    assert safe_path is not None
    assert safe_path.is_relative_to(sandbox.sandbox_dir)

    # Cleanup
    sandbox.cleanup()


def test_get_safe_path_traversal_attack():
    """Path traversal 공격 차단"""
    sandbox = SessionSandbox(user_id="test", session_id="attack")

    # Path traversal 시도 - 차단되어야 함
    dangerous_paths = [
        "../../../etc/passwd",
        "../../etc/shadow",
        "/etc/passwd",
        "/root/.ssh/id_rsa",
    ]

    for dangerous_path in dangerous_paths:
        safe_path = sandbox.get_safe_path(dangerous_path)
        assert safe_path is None, f"Path traversal attack not blocked: {dangerous_path}"

    # Cleanup
    sandbox.cleanup()


def test_get_safe_path_absolute_inside():
    """샌드박스 안의 절대 경로는 허용"""
    sandbox = SessionSandbox(user_id="test", session_id="abs")

    # 샌드박스 안의 절대 경로
    abs_path = str(sandbox.sandbox_dir / "data.json")
    safe_path = sandbox.get_safe_path(abs_path)

    assert safe_path is not None
    assert safe_path == sandbox.sandbox_dir / "data.json"

    # Cleanup
    sandbox.cleanup()


def test_sandbox_stats():
    """샌드박스 통계 확인"""
    sandbox = SessionSandbox(user_id="test", session_id="stats")

    # 파일 생성
    (sandbox.sandbox_dir / "file1.txt").write_text("Hello")
    (sandbox.sandbox_dir / "file2.txt").write_text("World")

    stats = sandbox.get_stats()

    assert stats["user_id"] == "test"
    assert stats["session_id"] == "stats"
    assert stats["file_count"] == 2
    assert stats["total_size_bytes"] == 10  # "Hello" (5) + "World" (5)

    # Cleanup
    sandbox.cleanup()


def test_multiple_sandboxes_isolated():
    """여러 샌드박스가 서로 격리되는지 확인"""
    sandbox1 = SessionSandbox(user_id="alice", session_id="s1")
    sandbox2 = SessionSandbox(user_id="bob", session_id="s2")

    # 서로 다른 디렉토리
    assert sandbox1.sandbox_dir != sandbox2.sandbox_dir

    # Alice의 파일
    (sandbox1.sandbox_dir / "alice_secret.txt").write_text("Alice's data")

    # Bob은 Alice 파일에 접근 불가
    alice_file_path = str(sandbox1.sandbox_dir / "alice_secret.txt")
    safe_path = sandbox2.get_safe_path(alice_file_path)
    assert safe_path is None, "Bob should not access Alice's files"

    # Cleanup
    sandbox1.cleanup()
    sandbox2.cleanup()
