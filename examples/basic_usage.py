"""
AMP 使用示例 - 展示核心功能

运行方式:
    python examples/basic_usage.py
"""

import asyncio
import sys
from pathlib import Path

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent, AgentMesh, MemoryType


async def example_1_basic_agent():
    """示例 1: 创建和使用 Agent"""
    print("\n" + "=" * 60)
    print("示例 1: 创建和使用 Agent")
    print("=" * 60)

    # 创建 Agent
    agent = Agent(
        name="Ali",
        role="project_manager",
        language="zh",
        capabilities=["coordination", "planning"],
    )

    print(f"\n[OK] 创建 Agent: {agent.identity.name}")
    print(f"   角色：{agent.identity.role}")
    print(f"   等级：{agent.identity.level}")
    print(f"   ID: {agent.identity.agent_id}")

    # 存储记忆
    await agent.memory.remember(
        "用户喜欢中文回复",
        type=MemoryType.SEMANTIC,
        importance=8,
        tags=["user_preference", "language"],
    )

    await agent.memory.remember(
        "项目使用 FastAPI 框架",
        type=MemoryType.SEMANTIC,
        importance=7,
        tags=["project", "technology"],
    )

    print(f"\n[MEM] 已存储 {agent.memory.count()} 条记忆")

    # 回忆
    memories = await agent.memory.recall("用户偏好", limit=5)
    print(f"\n[READ] 回忆'用户偏好':")
    for mem in memories:
        print(f"   - {mem.content} (强度：{mem.strength:.2f})")

    # 执行任务
    result = await agent.act({
        "description": "规划项目结构",
        "importance": 7,
        "tags": ["planning"],
    })
    print(f"\n[ACT] 任务结果：{result}")

    # 查看状态
    status = agent.status()
    print(f"\n[STATS] Agent 状态:")
    print(f"   完成任务：{status['identity']['tasks_completed']}")
    print(f"   记忆数量：{status['memory_stats']['total']}")

    return agent


async def example_2_multi_agent_collaboration():
    """示例 2: 多 Agent 协作"""
    print("\n" + "=" * 60)
    print("示例 2: 多 Agent 协作")
    print("=" * 60)

    # 创建多个 Agent
    researcher = Agent(name="探索者", role="researcher")
    writer = Agent(name="记录员", role="writer")
    reviewer = Agent(name="评审员", role="reviewer")

    # 创建 Mesh 网络
    mesh = AgentMesh()
    await mesh.register(researcher)
    await mesh.register(writer)
    await mesh.register(reviewer)

    print(f"\n[OK] 注册了 {len(mesh)} 个 Agent")

    # 团队任务
    result = await mesh.team_task(
        task={
            "description": "研究并记录 AI 记忆系统",
            "importance": 8,
            "tags": ["research", "documentation"],
        },
        agents=[researcher, writer, reviewer],
    )

    print(f"\n[TEAM] 团队任务完成:")
    print(f"   状态：{result.get('status')}")
    print(f"   团队规模：{result.get('team_size', 'N/A')}")

    # Agent 之间互相学习
    learned = await writer.learn_from(researcher, topic="AI")
    print(f"\n[LRN] 记录员从探索者学习了 {learned} 条记忆")

    # 广播消息
    count = await mesh.broadcast({
        "type": "announcement",
        "content": "项目会议将在 3 点后开始",
    })
    print(f"\n[MSG] 广播消息给 {count} 个 Agent")

    return mesh


async def example_3_memory_types():
    """示例 3: 四种记忆类型"""
    print("\n" + "=" * 60)
    print("示例 3: 四种记忆类型")
    print("=" * 60)

    agent = Agent(name="测试员", role="tester")

    # 1. 情景记忆 - 发生了什么
    await agent.memory.remember(
        "2026-03-12 与庞先生讨论了 AMP 项目架构",
        type=MemoryType.EPISODIC,
        importance=7,
        tags=["meeting", "project"],
    )
    print("[EPISODIC] 情景记忆：记录了事件")

    # 2. 语义记忆 - 知道什么
    await agent.memory.remember(
        "庞先生喜欢直接高效的沟通方式",
        type=MemoryType.SEMANTIC,
        importance=8,
        tags=["user_preference"],
    )
    print("[LRN] 语义记忆：记录了事实")

    # 3. 程序记忆 - 如何做
    await agent.memory.remember(
        "部署 AMP 项目的步骤：1) 安装依赖 2) 配置环境 3) 启动服务",
        type=MemoryType.PROCEDURAL,
        importance=6,
        tags=["deployment", "procedure"],
    )
    print("[PROCEDURAL] 程序记忆：记录了方法")

    # 4. 情感记忆 - 什么有效/无效
    await agent.memory.remember(
        "使用异步编程大幅提升了性能，这个方案很好",
        type=MemoryType.EMOTIONAL,
        importance=9,
        emotion="positive",
        tags=["optimization", "lesson"],
    )
    print("[EMOTIONAL] 情感记忆：记录了经验")

    # 记忆统计
    stats = agent.memory.stats()
    print(f"\n[STATS] 记忆统计:")
    for mem_type, count in stats["by_type"].items():
        print(f"   {mem_type}: {count}")

    return agent


async def example_4_sleep_consolidation():
    """示例 4: 睡眠和记忆巩固"""
    print("\n" + "=" * 60)
    print("示例 4: 睡眠和记忆巩固")
    print("=" * 60)

    agent = Agent(name="学习者", role="learner")

    # 创建一些记忆
    for i in range(10):
        await agent.memory.remember(
            f"学习内容 {i+1}",
            type=MemoryType.SEMANTIC,
            importance=(i % 10) + 1,
        )

    print(f"[MEM] 创建了 {agent.memory.count()} 条记忆")

    # 睡眠（记忆巩固）
    print("\n[SLEEP] 开始睡眠（记忆巩固）...")
    stats = await agent.sleep()

    print(f"\n[STATS] 巩固结果:")
    print(f"   强化：{stats['promoted']}")
    print(f"   衰减：{stats['decayed']}")
    print(f"   合并：{stats['merged']}")

    return agent


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("AMP 使用示例 - Agent Memory Protocol")
    print("=" * 60)

    # 运行示例
    agent1 = await example_1_basic_agent()
    mesh = await example_2_multi_agent_collaboration()
    agent3 = await example_3_memory_types()
    agent4 = await example_4_sleep_consolidation()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)
    print("\n提示:")
    print("   - 使用 'amp agent list' 查看所有创建的 Agent")
    print("   - 使用 'amp memory stats' 查看记忆统计")
    print("   - 使用 'amp status' 查看系统状态")
    print()


if __name__ == "__main__":
    asyncio.run(main())
