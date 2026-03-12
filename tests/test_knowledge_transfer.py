"""
知识传递效果测试

验证 learn_from() 方法改进后的效果
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent, MemoryType


async def test_learn_from_keywords():
    """测试关键词匹配 - 模拟实际场景"""
    print("\n" + "=" * 60)
    print("测试：关键词匹配（改进后）")
    print("=" * 60)

    # 创建老师和学生
    teacher = Agent(name="测试老师", role="instructor")
    student = Agent(name="测试学生", role="learner")

    # 老师学习一些知识（模拟真实场景）
    await teacher.memory.remember(
        "Python 异步编程使用 asyncio 库",
        type=MemoryType.SEMANTIC,
        importance=8,
        tags=["python", "async"]
    )

    await teacher.memory.remember(
        "FastAPI 是异步 Web 框架",
        type=MemoryType.SEMANTIC,
        importance=7,
        tags=["python", "web"]
    )

    await teacher.memory.remember(
        "数据库优化需要建立索引",
        type=MemoryType.SEMANTIC,
        importance=9,
        tags=["database", "optimization"]
    )

    print(f"\n老师记忆数：{teacher.memory.count()}")

    # 测试 1: 使用 "Python" 作为 topic（应该匹配 2 条）
    print("\n--- 测试 1: learn_from(topic='Python') ---")
    learned = await student.learn_from(teacher, topic="Python")
    print(f"学生学习到的记忆数：{learned}")
    print(f"学生当前记忆数：{student.memory.count()}")

    if learned >= 2:
        print("[OK] 测试 1 通过：成功匹配到 Python 相关记忆")
    else:
        print(f"[WARN] 测试 1 未达预期：期望>=2, 实际={learned}")

    # 测试 2: 使用 "异步" 作为 topic（应该匹配 2 条）
    student2 = Agent(name="测试学生 2", role="learner")
    print("\n--- 测试 2: learn_from(topic='异步') ---")
    learned2 = await student2.learn_from(teacher, topic="异步")
    print(f"学生学习到的记忆数：{learned2}")

    if learned2 >= 2:
        print("[OK] 测试 2 通过：成功匹配到异步相关记忆")
    else:
        print(f"[WARN] 测试 2 未达预期：期望>=2, 实际={learned2}")

    # 测试 3: 使用 "database" 作为 topic（应该匹配 1 条）
    student3 = Agent(name="测试学生 3", role="learner")
    print("\n--- 测试 3: learn_from(topic='database') ---")
    learned3 = await student3.learn_from(teacher, topic="database")
    print(f"学生学习到的记忆数：{learned3}")

    if learned3 >= 1:
        print("[OK] 测试 3 通过：成功匹配到 database 相关记忆")
    else:
        print(f"[WARN] 测试 3 未达预期：期望>=1, 实际={learned3}")

    # 测试 4: 不带 topic（应该返回最近的记忆）
    student4 = Agent(name="测试学生 4", role="learner")
    print("\n--- 测试 4: learn_from() 不带 topic ---")
    learned4 = await student4.learn_from(teacher)
    print(f"学生学习到的记忆数：{learned4}")

    if learned4 > 0:
        print("[OK] 测试 4 通过：返回了记忆")
    else:
        print(f"[FAIL] 测试 4 失败：应该返回记忆")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


async def test_keyword_extraction():
    """测试关键词提取功能"""
    print("\n" + "=" * 60)
    print("测试：关键词提取")
    print("=" * 60)

    from amp.agent import Agent

    agent = Agent(name="测试", role="test")

    # 测试中文
    keywords = agent._extract_keywords("Python 异步编程")
    print(f"\n输入：'Python 异步编程' -> 关键词：{keywords}")

    # 测试英文
    keywords = agent._extract_keywords("machine learning")
    print(f"输入：'machine learning' -> 关键词：{keywords}")

    # 测试带标点的
    keywords = agent._extract_keywords("数据库，优化和索引")
    print(f"输入：'数据库，优化和索引' -> 关键词：{keywords}")


async def main():
    await test_keyword_extraction()
    await test_learn_from_keywords()


if __name__ == "__main__":
    asyncio.run(main())
