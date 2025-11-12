"""
Session-based Sandbox for multi-user isolation

각 사용자/세션은 독립된 작업 공간을 가지며, 다른 세션의 파일에 접근할 수 없습니다.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional


class SessionSandbox:
    """
    세션별 격리된 작업 공간

    - 각 사용자/세션은 독립된 /tmp/session-{user_id}-{session_id}/ 디렉토리
    - 다른 세션 파일 접근 불가 (경로 검증)
    - 세션 종료 시 자동 정리 가능

    Example:
        >>> sandbox = SessionSandbox(user_id="alice", session_id="abc123")
        >>> sandbox.sandbox_dir
        PosixPath('/tmp/session-alice-abc123')

        >>> safe_path = sandbox.get_safe_path("data.json")
        >>> # Returns: /tmp/session-alice-abc123/data.json

        >>> safe_path = sandbox.get_safe_path("../../../etc/passwd")
        >>> # Returns: None (샌드박스 밖)
    """

    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        base_dir: str = "/tmp"
    ):
        """
        Args:
            user_id: 사용자 ID
            session_id: 세션 ID (없으면 UUID 자동 생성)
            base_dir: 샌드박스 베이스 디렉토리 (기본: /tmp)
        """
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())

        # 세션 전용 디렉토리 생성
        self.sandbox_dir = Path(base_dir) / f"session-{user_id}-{self.session_id}"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        # 권한 설정 (소유자만 읽기/쓰기/실행)
        os.chmod(self.sandbox_dir, 0o700)

    def get_safe_path(self, requested_path: str) -> Optional[Path]:
        """
        요청된 경로가 샌드박스 안에 있는지 검증

        보안 검증:
        - 상대 경로: 샌드박스 기준으로 변환
        - 절대 경로: 샌드박스 안에 있는지 확인
        - Path traversal 공격 차단 (../../../etc/passwd)

        Args:
            requested_path: 사용자가 요청한 경로

        Returns:
            안전한 경로 (Path) 또는 None (샌드박스 밖)
        """
        # 상대 경로면 샌드박스 기준으로 변환
        if not Path(requested_path).is_absolute():
            full_path = (self.sandbox_dir / requested_path).resolve()
        else:
            full_path = Path(requested_path).resolve()

        # 샌드박스 디렉토리 안에 있는지 확인
        try:
            full_path.relative_to(self.sandbox_dir)
            return full_path
        except ValueError:
            # 샌드박스 밖으로 나가려는 시도!
            # 예: /etc/passwd, ../../../etc/passwd
            return None

    def cleanup(self):
        """
        세션 종료 시 임시 파일 삭제

        주의: 세션이 완전히 종료될 때만 호출하세요!
        """
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)

    def get_stats(self) -> dict:
        """
        샌드박스 통계 (디버깅용)

        Returns:
            {
                "user_id": "alice",
                "session_id": "abc123",
                "sandbox_dir": "/tmp/session-alice-abc123",
                "total_size_bytes": 1024,
                "file_count": 5
            }
        """
        total_size = 0
        file_count = 0

        if self.sandbox_dir.exists():
            for f in self.sandbox_dir.rglob('*'):
                if f.is_file():
                    total_size += f.stat().st_size
                    file_count += 1

        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "sandbox_dir": str(self.sandbox_dir),
            "total_size_bytes": total_size,
            "file_count": file_count,
        }
