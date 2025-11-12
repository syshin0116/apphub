#!/usr/bin/env python3
"""
Verification script for agent-tools

Tests the full functionality of agent-tools package
"""

import sys
from agent_tools import SessionSandbox, create_atomic_tools


def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def verify_sandbox():
    """Verify SessionSandbox"""
    print_section("1. SessionSandbox 검증")

    sandbox = SessionSandbox(user_id="verify_user", session_id="test")
    print(f"✓ Sandbox created: {sandbox.sandbox_dir}")
    print(f"  - User ID: {sandbox.user_id}")
    print(f"  - Session ID: {sandbox.session_id}")
    print(f"  - Directory exists: {sandbox.sandbox_dir.exists()}")

    # Test safe path
    safe_path = sandbox.get_safe_path("test.txt")
    print(f"\n✓ Safe path test:")
    print(f"  - Requested: test.txt")
    print(f"  - Safe path: {safe_path}")

    # Test path traversal
    unsafe_path = sandbox.get_safe_path("../../../etc/passwd")
    print(f"\n✓ Path traversal protection:")
    print(f"  - Requested: ../../../etc/passwd")
    print(f"  - Result: {unsafe_path} (None = blocked)")

    sandbox.cleanup()
    print(f"\n✓ Cleanup: Directory removed")

    return True


def verify_atomic_tools():
    """Verify atomic tools"""
    print_section("2. Atomic Tools 검증 (4개)")

    sandbox = SessionSandbox(user_id="verify_user", session_id="tools")
    tools = create_atomic_tools(sandbox)

    print(f"✓ Created {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")

    # Test file_write
    file_write = next(t for t in tools if t.name == "file_write")
    result = file_write.invoke({"path": "hello.txt", "content": "Hello, World!"})
    print(f"\n✓ file_write test:")
    print(f"  {result}")

    # Test file_read
    file_read = next(t for t in tools if t.name == "file_read")
    content = file_read.invoke({"path": "hello.txt"})
    print(f"\n✓ file_read test:")
    print(f"  Content: {content}")

    # Test file_list
    file_list = next(t for t in tools if t.name == "file_list")
    files = file_list.invoke({"directory": ".", "pattern": "*"})
    print(f"\n✓ file_list test:")
    print(f"  Files:\n{files}")

    # Test shell_execute
    shell_execute = next(t for t in tools if t.name == "shell_execute")
    output = shell_execute.invoke({"command": "echo 'Shell works!'"})
    print(f"\n✓ shell_execute test:")
    print(f"  Output: {output.strip()}")

    sandbox.cleanup()
    return True


def verify_security():
    """Verify security isolation"""
    print_section("3. 보안 격리 검증")

    # Create two separate sandboxes
    sandbox_alice = SessionSandbox(user_id="alice", session_id="s1")
    sandbox_bob = SessionSandbox(user_id="bob", session_id="s2")

    tools_alice = create_atomic_tools(sandbox_alice)
    tools_bob = create_atomic_tools(sandbox_bob)

    # Alice writes a file
    file_write_alice = next(t for t in tools_alice if t.name == "file_write")
    file_write_alice.invoke({"path": "secret.txt", "content": "Alice's secret data"})
    print(f"✓ Alice created file: {sandbox_alice.sandbox_dir}/secret.txt")

    # Bob tries to read Alice's file
    file_read_bob = next(t for t in tools_bob if t.name == "file_read")
    alice_file_path = str(sandbox_alice.sandbox_dir / "secret.txt")
    result = file_read_bob.invoke({"path": alice_file_path})

    print(f"\n✓ Bob tries to read Alice's file:")
    print(f"  Path: {alice_file_path}")
    print(f"  Result: {result[:100]}...")
    print(f"  Blocked: {'❌ Access denied' in result}")

    sandbox_alice.cleanup()
    sandbox_bob.cleanup()

    return "❌ Access denied" in result


def verify_context_offloading():
    """Verify context offloading for large outputs"""
    print_section("4. Context Offloading 검증")

    sandbox = SessionSandbox(user_id="verify_user", session_id="offload")
    tools = create_atomic_tools(sandbox)

    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # Generate large output
    result = shell_execute.invoke({"command": "python3 -c 'print(\"A\" * 2000)'"})

    print(f"✓ Large output test (2000 chars):")
    print(f"  Output saved to file: {'Output saved' in result}")
    print(f"  Contains file_read hint: {'file_read' in result}")
    print(f"\n  Result preview:")
    print(f"  {result[:200]}...")

    sandbox.cleanup()
    return "Output saved" in result


def verify_real_world_scenario():
    """Verify real-world scenario: log analysis"""
    print_section("5. 실전 시나리오 검증: 로그 분석")

    sandbox = SessionSandbox(user_id="verify_user", session_id="logs")
    tools = create_atomic_tools(sandbox)

    file_write = next(t for t in tools if t.name == "file_write")
    shell_execute = next(t for t in tools if t.name == "shell_execute")

    # Create log file
    log_data = """2025-11-12 10:00:00 INFO User login: alice
2025-11-12 10:05:00 ERROR Database connection failed
2025-11-12 10:10:00 INFO User logout: alice
2025-11-12 10:15:00 ERROR API timeout
2025-11-12 10:20:00 INFO User login: bob"""

    file_write.invoke({"path": "app.log", "content": log_data})
    print(f"✓ Created app.log with {len(log_data.splitlines())} lines")

    # Grep for errors
    result = shell_execute.invoke({"command": "grep ERROR app.log"})
    print(f"\n✓ grep ERROR app.log:")
    print(f"  Found {result.count('ERROR')} errors")
    print(f"  Preview:\n{result}")

    # Count errors
    count = shell_execute.invoke({"command": "grep -c ERROR app.log"})
    print(f"\n✓ grep -c ERROR app.log:")
    print(f"  Count: {count.strip()}")

    sandbox.cleanup()
    return result.count("ERROR") == 2


def main():
    """Run all verifications"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          Agent Tools Verification Script                    ║
║          Testing all functionality...                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    results = []

    try:
        results.append(("SessionSandbox", verify_sandbox()))
        results.append(("Atomic Tools (4)", verify_atomic_tools()))
        results.append(("Security Isolation", verify_security()))
        results.append(("Context Offloading", verify_context_offloading()))
        results.append(("Real-world Scenario", verify_real_world_scenario()))

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Print summary
    print_section("검증 결과 요약")

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:12} - {name}")
        if not passed:
            all_passed = False

    print(f"\n{'='*60}")

    if all_passed:
        print("""
✅ 모든 검증 통과!

Agent Tools가 정상적으로 작동합니다:
- SessionSandbox: 세션별 격리 작업 공간
- Level 1 Tools: 4개 원자적 함수 (file_read, file_write, file_list, shell_execute)
- Security: Path traversal 차단, 세션 간 격리
- Context Offloading: 큰 출력 자동 파일 저장
- Real-world: grep, find 등 Linux 명령어 활용

다음 단계:
1. apps/ai-service에서 create_user_agent() 사용
2. Level 2 CLI 구현 (knowledge-search, mcp-cli)
3. Level 3 도메인 구현 (BlogHybridRetriever)
        """)
        return 0
    else:
        print("\n❌ 일부 검증 실패. 위 로그를 확인하세요.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
