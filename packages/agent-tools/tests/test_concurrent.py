"""Concurrent access tests for agent-tools"""

import pytest
import asyncio
import concurrent.futures
from agent_tools import SessionSandbox, create_atomic_tools


def test_multiple_sandboxes_concurrent():
    """여러 샌드박스 동시 생성"""
    sandboxes = []

    def create_sandbox(user_id):
        sandbox = SessionSandbox(user_id=user_id, session_id=f"concurrent_{user_id}")
        sandboxes.append(sandbox)
        return sandbox.sandbox_dir

    # 10개 샌드박스 동시 생성
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_sandbox, f"user_{i}") for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 모두 다른 디렉토리
    assert len(set(results)) == 10

    # 모두 존재
    for sandbox in sandboxes:
        assert sandbox.sandbox_dir.exists()

    # Cleanup
    for sandbox in sandboxes:
        sandbox.cleanup()


def test_concurrent_file_operations():
    """동일 샌드박스 내 동시 파일 작업"""
    sandbox = SessionSandbox(user_id="concurrent", session_id="ops")
    tools = create_atomic_tools(sandbox)
    file_write = next(t for t in tools if t.name == "file_write")

    def write_file(file_num):
        return file_write.invoke({
            "path": f"file_{file_num}.txt",
            "content": f"Content {file_num}"
        })

    # 20개 파일 동시 쓰기
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(write_file, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 모두 성공
    assert all("✓" in result for result in results)

    # 파일 개수 확인
    stats = sandbox.get_stats()
    assert stats["file_count"] == 20

    sandbox.cleanup()


def test_concurrent_read_write():
    """동시 읽기/쓰기"""
    sandbox = SessionSandbox(user_id="concurrent", session_id="rw")
    tools = create_atomic_tools(sandbox)
    file_write = next(t for t in tools if t.name == "file_write")
    file_read = next(t for t in tools if t.name == "file_read")

    # 초기 파일 생성
    file_write.invoke({"path": "shared.txt", "content": "initial"})

    results = []

    def read_file():
        result = file_read.invoke({"path": "shared.txt"})
        results.append(("read", result))
        return result

    def write_file(iteration):
        result = file_write.invoke({
            "path": "shared.txt",
            "content": f"iteration_{iteration}"
        })
        results.append(("write", iteration))
        return result

    # 동시에 읽기 5개, 쓰기 5개
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        read_futures = [executor.submit(read_file) for _ in range(5)]
        write_futures = [executor.submit(write_file, i) for i in range(5)]

        all_futures = read_futures + write_futures
        for f in concurrent.futures.as_completed(all_futures):
            f.result()

    # 모든 작업 완료 확인
    assert len(results) == 10

    sandbox.cleanup()


def test_concurrent_shell_execute():
    """동시 셸 명령 실행"""
    sandbox = SessionSandbox(user_id="concurrent", session_id="shell")
    tools = create_atomic_tools(sandbox)
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    def run_command(cmd_num):
        return shell_execute.invoke({
            "command": f"echo 'Command {cmd_num}'"
        })

    # 10개 명령 동시 실행
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_command, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 모두 성공
    assert len(results) == 10
    assert all("Command" in result for result in results)

    sandbox.cleanup()


def test_multiple_users_isolation():
    """여러 사용자의 격리된 동시 작업"""

    def user_workflow(user_id):
        """각 사용자의 워크플로우"""
        sandbox = SessionSandbox(user_id=user_id, session_id="workflow")
        tools = create_atomic_tools(sandbox)

        file_write = next(t for t in tools if t.name == "file_write")
        file_read = next(t for t in tools if t.name == "file_read")
        shell_execute = next(t for t in tools if t.name == "shell_execute")

        # 각자의 파일 생성
        file_write.invoke({
            "path": "my_data.txt",
            "content": f"Data from {user_id}"
        })

        # grep으로 검색
        grep_result = shell_execute.invoke({
            "command": "grep 'Data' my_data.txt"
        })

        # 읽기
        read_result = file_read.invoke({"path": "my_data.txt"})

        sandbox.cleanup()

        return {
            "user_id": user_id,
            "grep": user_id in grep_result,
            "read": user_id in read_result
        }

    # 5명의 사용자 동시 작업
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        users = [f"user_{i}" for i in range(5)]
        futures = [executor.submit(user_workflow, user) for user in users]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 모든 사용자가 자신의 데이터만 볼 수 있음
    assert len(results) == 5
    for result in results:
        assert result["grep"] is True
        assert result["read"] is True


def test_sandbox_cleanup_race_condition():
    """샌드박스 정리 시 race condition 테스트"""
    sandboxes = []

    def create_and_use(user_id):
        sandbox = SessionSandbox(user_id=user_id, session_id="cleanup")
        tools = create_atomic_tools(sandbox)
        file_write = next(t for t in tools if t.name == "file_write")

        # 파일 생성
        file_write.invoke({"path": "test.txt", "content": "test"})

        sandboxes.append(sandbox)
        return sandbox.sandbox_dir

    # 동시에 샌드박스 생성 및 사용
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_and_use, f"user_{i}") for i in range(5)]
        dirs = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 모두 존재
    for d in dirs:
        assert d.exists()

    # 동시에 정리
    def cleanup_sandbox(sandbox):
        sandbox.cleanup()
        return not sandbox.sandbox_dir.exists()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(cleanup_sandbox, sb) for sb in sandboxes]
        cleanup_results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 모두 정리됨
    assert all(cleanup_results)


@pytest.mark.asyncio
async def test_async_concurrent_operations():
    """비동기 동시 작업"""
    sandbox = SessionSandbox(user_id="async_test", session_id="concurrent")
    tools = create_atomic_tools(sandbox)
    file_write = next(t for t in tools if t.name == "file_write")

    async def write_async(file_num):
        # 실제로는 동기 함수지만 async로 래핑
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            file_write.invoke,
            {"path": f"async_{file_num}.txt", "content": f"Async {file_num}"}
        )

    # 10개 파일 비동기로 동시 쓰기
    tasks = [write_async(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    # 모두 성공
    assert len(results) == 10
    assert all("✓" in result for result in results)

    # 파일 개수 확인
    stats = sandbox.get_stats()
    assert stats["file_count"] == 10

    sandbox.cleanup()


def test_stress_test_many_operations():
    """스트레스 테스트: 많은 작업"""
    sandbox = SessionSandbox(user_id="stress", session_id="test")
    tools = create_atomic_tools(sandbox)
    file_write = next(t for t in tools if t.name == "file_write")
    file_list = next(t for t in tools if t.name == "file_list")

    # 100개 파일 생성
    for i in range(100):
        file_write.invoke({
            "path": f"stress_{i}.txt",
            "content": f"Content {i}"
        })

    # 파일 목록 조회
    result = file_list.invoke({"directory": ".", "pattern": "stress_*.txt"})
    assert result.count("stress_") == 100

    # 통계 확인
    stats = sandbox.get_stats()
    assert stats["file_count"] == 100

    sandbox.cleanup()
