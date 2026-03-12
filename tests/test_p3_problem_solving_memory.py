"""
P3 问题解决记忆修复验证测试

验证当 act() 返回 {"status": "failed"} 时，是否正确创建情感记忆（问题解决记忆）
"""

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent, MemoryType


async def test_problem_solving_memory_with_failed_status():
    """测试当任务返回 failed 状态时，是否创建问题解决记忆"""
    print("\n" + "=" * 60)
    print("测试：问题解决记忆创建（failed 状态）")
    print("=" * 60)

    with TemporaryDirectory() as tmp_dir:
        # 创建 Agent
        agent = Agent(name="P3 测试助手", role="tester", storage_dir=tmp_dir)

        # 注册一个会返回失败的任务处理器
        async def failing_task_handler(task: dict) -> dict:
            return {"status": "failed", "error": "模拟失败：功能未实现"}

        agent.register_capability("failing_task", failing_task_handler)

        # 执行会失败的任务
        result = await agent.act({
            "description": "实现功能 X",
            "capability": "failing_task",
            "tags": ["test", "p3"]
        })

        print(f"\n任务执行结果：{result}")
        print(f"Agent 统计：完成={agent.identity.tasks_completed}, 失败={agent.identity.tasks_failed}")

        # 检查情感记忆（问题解决记忆）
        emotional_memories = await agent.memory.recall("Failed", type=MemoryType.EMOTIONAL)
        print(f"情感记忆数量：{len(emotional_memories)}")

        for mem in emotional_memories:
            print(f"  - {mem.content[:80]}...")

        # 验证
        assert result.get("status") == "failed", "任务应该返回失败状态"
        assert agent.identity.tasks_failed >= 1, "失败计数应该增加"
        assert len(emotional_memories) >= 1, "应该创建至少 1 条情感记忆（问题解决记忆）"

        # 验证记忆内容包含关键信息
        problem_memory = emotional_memories[0]
        assert "Failed" in problem_memory.content, "记忆内容应该包含 'Failed'"
        assert "实现功能 X" in problem_memory.content, "记忆内容应该包含任务描述"
        assert problem_memory.emotion == "negative", "情感记忆应该是 negative"
        assert problem_memory.type == MemoryType.EMOTIONAL, "应该是情感记忆类型"

        print("\n[OK] 测试通过：问题解决记忆创建成功")


async def test_problem_solving_memory_with_success():
    """测试当任务成功时，是否创建程序性记忆"""
    print("\n" + "=" * 60)
    print("测试：程序性记忆创建（成功状态）")
    print("=" * 60)

    with TemporaryDirectory() as tmp_dir:
        # 创建 Agent
        agent = Agent(name="P3 成功测试", role="tester", storage_dir=tmp_dir)

        # 注册一个会返回成功的任务处理器
        async def success_task_handler(task: dict) -> dict:
            return {"status": "completed", "result": "功能已实现"}

        agent.register_capability("success_task", success_task_handler)

        # 执行成功的任务
        result = await agent.act({
            "description": "实现功能 Y",
            "capability": "success_task",
            "tags": ["test", "success"]
        })

        print(f"\n任务执行结果：{result}")
        print(f"Agent 统计：完成={agent.identity.tasks_completed}, 失败={agent.identity.tasks_failed}")

        # 检查程序性记忆
        procedural_memories = await agent.memory.recall("Successfully completed", type=MemoryType.PROCEDURAL)
        print(f"程序性记忆数量：{len(procedural_memories)}")

        for mem in procedural_memories:
            print(f"  - {mem.content[:80]}...")

        # 验证
        assert result.get("status") == "completed", "任务应该返回成功状态"
        assert agent.identity.tasks_completed >= 1, "成功计数应该增加"
        assert len(procedural_memories) >= 1, "应该创建至少 1 条程序性记忆"

        # 验证记忆内容
        success_memory = procedural_memories[0]
        assert "Successfully completed" in success_memory.content, "记忆内容应该包含 'Successfully completed'"
        assert "实现功能 Y" in success_memory.content, "记忆内容应该包含任务描述"
        assert success_memory.emotion == "positive", "情感应该是 positive"

        print("\n[OK] 测试通过：程序性记忆创建成功")


async def test_exception_also_creates_problem_memory():
    """测试当任务抛出异常时，是否也创建问题解决记忆"""
    print("\n" + "=" * 60)
    print("测试：异常处理创建问题解决记忆")
    print("=" * 60)

    with TemporaryDirectory() as tmp_dir:
        # 创建 Agent
        agent = Agent(name="P3 异常测试", role="tester", storage_dir=tmp_dir)

        # 注册一个会抛出异常的任务处理器
        async def exception_task_handler(task: dict) -> dict:
            raise ValueError("模拟异常：除零错误")

        agent.register_capability("exception_task", exception_task_handler)

        # 执行会抛出异常的任务
        result = await agent.act({
            "description": "执行危险操作",
            "capability": "exception_task",
            "tags": ["test", "exception"]
        })

        print(f"\n任务执行结果：{result}")
        print(f"Agent 统计：完成={agent.identity.tasks_completed}, 失败={agent.identity.tasks_failed}")

        # 检查情感记忆
        emotional_memories = await agent.memory.recall("Failed", type=MemoryType.EMOTIONAL)
        print(f"情感记忆数量：{len(emotional_memories)}")

        for mem in emotional_memories:
            print(f"  - {mem.content[:80]}...")

        # 验证
        assert result.get("status") == "failed", "任务应该返回失败状态"
        assert "error" in result, "结果应该包含 error 字段"
        assert agent.identity.tasks_failed >= 1, "失败计数应该增加"
        assert len(emotional_memories) >= 1, "应该创建至少 1 条情感记忆"

        # 验证记忆内容包含异常信息
        problem_memory = emotional_memories[0]
        assert "Error" in problem_memory.content or "模拟异常" in problem_memory.content, "记忆内容应该包含异常信息"
        assert problem_memory.emotion == "negative", "情感记忆应该是 negative"

        print("\n[OK] 测试通过：异常处理创建问题解决记忆成功")


async def main():
    await test_problem_solving_memory_with_failed_status()
    await test_problem_solving_memory_with_success()
    await test_exception_also_creates_problem_memory()

    print("\n" + "=" * 60)
    print("所有 P3 问题解决记忆测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
