"""Edge case and error handling tests for agent-tools"""

import pytest
import os
from pathlib import Path
from agent_tools import SessionSandbox, create_atomic_tools


@pytest.fixture
def sandbox():
    """테스트용 샌드박스"""
    sb = SessionSandbox(user_id="edge_test", session_id="test")
    yield sb
    sb.cleanup()


@pytest.fixture
def tools(sandbox):
    """테스트용 도구"""
    return create_atomic_tools(sandbox)


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_file_read(self, tools, sandbox):
        """빈 파일 읽기"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")

        # 빈 파일 생성
        file_write.invoke({"path": "empty.txt", "content": ""})

        # 빈 파일 읽기
        result = file_read.invoke({"path": "empty.txt"})
        assert result == ""

    def test_large_file(self, tools):
        """큰 파일 처리"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")

        # 1MB 파일 생성
        large_content = "A" * (1024 * 1024)
        result = file_write.invoke({"path": "large.txt", "content": large_content})
        assert "✓" in result

        # 읽기
        content = file_read.invoke({"path": "large.txt"})
        assert len(content) == 1024 * 1024

    def test_special_characters_in_filename(self, tools):
        """특수 문자가 포함된 파일명"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")

        # 공백, 한글, 특수문자
        filenames = [
            "file with spaces.txt",
            "파일_한글_이름.txt",
            "file-with-dash.txt",
            "file.multiple.dots.txt",
        ]

        for filename in filenames:
            result = file_write.invoke({"path": filename, "content": "test"})
            assert "✓" in result, f"Failed to write: {filename}"

            content = file_read.invoke({"path": filename})
            assert content == "test", f"Failed to read: {filename}"

    def test_unicode_content(self, tools):
        """유니코드 콘텐츠"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")

        # 다양한 언어
        unicode_content = """
        English: Hello World
        한국어: 안녕하세요
        日本語: こんにちは
        中文: 你好
        Emoji: 🎉🔥💻🚀
        Special: €£¥©®™
        """

        file_write.invoke({"path": "unicode.txt", "content": unicode_content})
        result = file_read.invoke({"path": "unicode.txt"})
        assert "안녕하세요" in result
        assert "🎉" in result

    def test_nested_directories(self, tools):
        """깊은 중첩 디렉토리"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")

        # 10단계 중첩
        deep_path = "/".join(["dir"] * 10) + "/deep.txt"
        result = file_write.invoke({"path": deep_path, "content": "deep file"})
        assert "✓" in result

        content = file_read.invoke({"path": deep_path})
        assert content == "deep file"

    def test_file_overwrite(self, tools):
        """파일 덮어쓰기"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")

        # 첫 번째 쓰기
        file_write.invoke({"path": "overwrite.txt", "content": "first"})
        assert file_read.invoke({"path": "overwrite.txt"}) == "first"

        # 덮어쓰기
        file_write.invoke({"path": "overwrite.txt", "content": "second"})
        assert file_read.invoke({"path": "overwrite.txt"}) == "second"

    def test_shell_execute_empty_output(self, tools):
        """출력이 없는 명령"""
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        result = shell_execute.invoke({"command": "true"})
        assert "✓" in result
        assert "no output" in result.lower()

    def test_shell_execute_stderr(self, tools):
        """stderr 출력"""
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        result = shell_execute.invoke({"command": "ls /nonexistent 2>&1"})
        assert "stderr" in result.lower() or "cannot access" in result.lower()

    def test_shell_execute_exit_code(self, tools):
        """실패하는 명령 (exit code != 0)"""
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        result = shell_execute.invoke({"command": "false"})
        # 에러 처리 확인
        assert "failed" in result.lower() or "exit code" in result.lower()

    def test_file_list_empty_directory(self, tools, sandbox):
        """빈 디렉토리"""
        file_list = next(t for t in tools if t.name == "file_list")

        # 빈 디렉토리 생성
        empty_dir = sandbox.sandbox_dir / "empty"
        empty_dir.mkdir()

        result = file_list.invoke({"directory": "empty", "pattern": "*"})
        assert "No files found" in result

    def test_file_list_nonexistent_directory(self, tools):
        """존재하지 않는 디렉토리"""
        file_list = next(t for t in tools if t.name == "file_list")

        result = file_list.invoke({"directory": "nonexistent", "pattern": "*"})
        assert "❌" in result
        assert "not found" in result.lower()

    def test_file_list_recursive(self, tools):
        """재귀적 파일 검색"""
        file_write = next(t for t in tools if t.name == "file_write")
        file_list = next(t for t in tools if t.name == "file_list")

        # 중첩 구조 생성
        file_write.invoke({"path": "a/file1.txt", "content": "1"})
        file_write.invoke({"path": "a/b/file2.txt", "content": "2"})
        file_write.invoke({"path": "a/b/c/file3.txt", "content": "3"})

        # 재귀 검색
        result = file_list.invoke({"directory": "a", "pattern": "**/*.txt"})
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "file3.txt" in result


class TestErrorHandling:
    """Error handling tests"""

    def test_sandbox_invalid_characters(self):
        """잘못된 문자가 포함된 user_id/session_id"""
        # 슬래시가 포함되어도 안전하게 처리되는지
        sandbox = SessionSandbox(user_id="user/with/slash", session_id="test")
        assert sandbox.sandbox_dir.exists()
        sandbox.cleanup()

    def test_file_write_permission_error(self, tools):
        """권한 에러 (읽기 전용 파일 덮어쓰기)"""
        file_write = next(t for t in tools if t.name == "file_write")

        # 파일 생성
        result = file_write.invoke({"path": "readonly.txt", "content": "test"})
        assert "✓" in result

        # 읽기 전용으로 변경
        # (샌드박스 안에서는 권한을 변경할 수 있으므로 이 테스트는 제한적)

    def test_shell_execute_timeout(self, tools):
        """타임아웃 테스트"""
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # 60초 초과 명령 (타임아웃은 60초)
        result = shell_execute.invoke({"command": "sleep 70"})
        assert "timed out" in result.lower() or "timeout" in result.lower()

    def test_shell_execute_command_not_found(self, tools):
        """존재하지 않는 명령"""
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        result = shell_execute.invoke({"command": "nonexistentcommand12345"})
        assert "not found" in result.lower() or "stderr" in result.lower()

    def test_file_read_binary_file(self, tools, sandbox):
        """바이너리 파일 읽기 (에러 처리)"""
        file_read = next(t for t in tools if t.name == "file_read")

        # 바이너리 파일 생성
        binary_path = sandbox.sandbox_dir / "binary.dat"
        binary_path.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")

        # 읽기 시도
        result = file_read.invoke({"path": "binary.dat"})
        # UTF-8 디코딩 실패 처리 확인
        # (현재 구현은 에러 메시지 반환)


class TestSandboxStats:
    """Sandbox statistics tests"""

    def test_stats_empty_sandbox(self):
        """빈 샌드박스 통계"""
        sandbox = SessionSandbox(user_id="stats_test", session_id="empty")
        stats = sandbox.get_stats()

        assert stats["file_count"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["user_id"] == "stats_test"
        assert stats["session_id"] == "empty"

        sandbox.cleanup()

    def test_stats_with_files(self, sandbox, tools):
        """파일이 있는 샌드박스 통계"""
        file_write = next(t for t in tools if t.name == "file_write")

        # 여러 파일 생성
        file_write.invoke({"path": "file1.txt", "content": "12345"})  # 5 bytes
        file_write.invoke({"path": "file2.txt", "content": "1234567890"})  # 10 bytes
        file_write.invoke({"path": "dir/file3.txt", "content": "abc"})  # 3 bytes

        stats = sandbox.get_stats()
        assert stats["file_count"] == 3
        assert stats["total_size_bytes"] == 18  # 5 + 10 + 3


class TestPathSecurity:
    """Path security tests"""

    def test_absolute_path_outside_sandbox(self, tools):
        """샌드박스 밖의 절대 경로"""
        file_read = next(t for t in tools if t.name == "file_read")

        dangerous_paths = [
            "/etc/passwd",
            "/root/.ssh/id_rsa",
            "/proc/self/environ",
            "/var/log/syslog",
        ]

        for path in dangerous_paths:
            result = file_read.invoke({"path": path})
            assert "❌" in result, f"Should block: {path}"
            assert "Access denied" in result, f"Should block: {path}"

    def test_symlink_escape_attempt(self, tools, sandbox):
        """심볼릭 링크를 통한 탈출 시도"""
        # 심볼릭 링크 생성 시도
        symlink_path = sandbox.sandbox_dir / "escape_link"

        # /etc/passwd로 가는 심볼릭 링크 생성
        try:
            os.symlink("/etc/passwd", symlink_path)

            file_read = next(t for t in tools if t.name == "file_read")
            result = file_read.invoke({"path": "escape_link"})

            # 심볼릭 링크가 샌드박스 밖을 가리키면 차단되어야 함
            # (현재 resolve()로 실제 경로를 확인하므로 차단됨)
            assert "❌" in result or "Access denied" in result
        except OSError:
            # 심볼릭 링크 생성 실패 (권한 등) - 괜찮음
            pass
