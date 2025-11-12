"""
Level 1: Atomic Functions Core Implementation

진짜 원자적인 4개 함수만!
- 더 이상 분해 불가능
- Linux 명령어 수준
- 모든 복잡한 기능은 Level 2/3로 오프로드
"""

import subprocess
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from ..sandbox import SessionSandbox


def create_atomic_tools(sandbox: 'SessionSandbox'):
    """
    세션별 격리된 atomic tools 생성

    Args:
        sandbox: SessionSandbox 인스턴스

    Returns:
        4개의 atomic tools 리스트

    Example:
        >>> from agent_tools.sandbox import SessionSandbox
        >>> from agent_tools.level1 import create_atomic_tools
        >>>
        >>> sandbox = SessionSandbox(user_id="alice", session_id="test")
        >>> tools = create_atomic_tools(sandbox)
        >>> len(tools)
        4
    """

    @tool
    def file_read(path: str) -> str:
        """
        파일 읽기 (샌드박스 내부만)

        Args:
            path: 읽을 파일 경로 (절대 또는 상대)

        Returns:
            파일 내용 또는 에러 메시지

        Example:
            file_read("data.json")
            file_read("/tmp/output.txt")
        """
        safe_path = sandbox.get_safe_path(path)
        if safe_path is None:
            return f"❌ Access denied: {path} is outside sandbox ({sandbox.sandbox_dir})"

        if not safe_path.exists():
            return f"❌ File not found: {path}"

        try:
            content = safe_path.read_text(encoding='utf-8')
            return content
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"

    @tool
    def file_write(path: str, content: str) -> str:
        """
        파일 쓰기 (샌드박스 내부만)

        Args:
            path: 쓸 파일 경로 (절대 또는 상대)
            content: 파일 내용

        Returns:
            성공 메시지 또는 에러 메시지

        Example:
            file_write("output.txt", "Hello World")
            file_write("data.json", '{"key": "value"}')
        """
        safe_path = sandbox.get_safe_path(path)
        if safe_path is None:
            return f"❌ Access denied: {path} is outside sandbox ({sandbox.sandbox_dir})"

        try:
            # 부모 디렉토리 생성
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding='utf-8')
            return f"✓ File written: {path} ({len(content)} bytes)"
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"

    @tool
    def file_list(directory: str = ".", pattern: str = "*") -> str:
        """
        파일 목록 조회 (glob)

        Args:
            directory: 조회할 디렉토리 (기본: 현재 디렉토리)
            pattern: glob 패턴 (기본: "*")

        Returns:
            파일 목록 (줄바꿈으로 구분) 또는 에러 메시지

        Example:
            file_list()
            file_list(".", "*.json")
            file_list("data", "**/*.txt")
        """
        safe_dir = sandbox.get_safe_path(directory)
        if safe_dir is None:
            return f"❌ Access denied: {directory} is outside sandbox ({sandbox.sandbox_dir})"

        if not safe_dir.exists():
            return f"❌ Directory not found: {directory}"

        if not safe_dir.is_dir():
            return f"❌ Not a directory: {directory}"

        try:
            # glob 패턴으로 파일 검색
            files = list(safe_dir.glob(pattern))

            if not files:
                return f"No files found matching '{pattern}' in {directory}"

            # 상대 경로로 변환하여 출력
            relative_files = []
            for f in sorted(files):
                try:
                    rel_path = f.relative_to(sandbox.sandbox_dir)
                    relative_files.append(str(rel_path))
                except ValueError:
                    relative_files.append(str(f))

            return "\n".join(relative_files)
        except Exception as e:
            return f"❌ Error listing files: {str(e)}"

    @tool
    def shell_execute(command: str) -> str:
        """
        셸 명령 실행 - Level 2/3로 가는 유일한 관문!

        보안:
        - 샌드박스 디렉토리에서만 실행
        - 60초 타임아웃
        - 환경 변수 제한

        Context Offloading:
        - 출력이 1000자 초과 시 파일로 저장
        - 파일 경로만 반환 (컨텍스트 최소화)

        Args:
            command: 실행할 셸 명령

        Returns:
            명령 출력 또는 파일 경로

        Examples:
            # Linux 명령어
            shell_execute("ls -la")
            shell_execute("grep -r 'TODO' .")
            shell_execute("find . -name '*.py' | wc -l")

            # Level 2 CLI
            shell_execute("knowledge-search search --query 'AI' --collection blog")

            # Level 3 Python 스크립트
            shell_execute("python analyze.py --input data.json")
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(sandbox.sandbox_dir),
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin",
                    "HOME": str(sandbox.sandbox_dir),
                    "TMPDIR": str(sandbox.sandbox_dir),
                }
            )

            # stdout + stderr 결합
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            if not output:
                return "✓ Command executed (no output)" if result.returncode == 0 else f"❌ Command failed with exit code {result.returncode}"

            # Context offloading: 큰 출력은 파일로 저장
            if len(output) > 1000:
                output_file = sandbox.sandbox_dir / f"output_{uuid.uuid4().hex[:8]}.txt"
                output_file.write_text(output, encoding='utf-8')

                # 파일 경로만 반환
                return (
                    f"Output saved to file (too large: {len(output)} bytes)\n\n"
                    f"File: {output_file.relative_to(sandbox.sandbox_dir)}\n\n"
                    f"Use file_read('{output_file.relative_to(sandbox.sandbox_dir)}') to view contents.\n\n"
                    f"Preview (first 500 chars):\n{output[:500]}..."
                )

            return output

        except subprocess.TimeoutExpired:
            return "❌ Command timed out (60s limit)"
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"

    # 이게 전부! 4개만!
    return [file_read, file_write, file_list, shell_execute]
