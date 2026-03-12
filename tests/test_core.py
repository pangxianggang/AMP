"""
AMP 核心功能测试

运行方式:
    python -m pytest tests/test_core.py -v
"""

import asyncio
import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent, AgentMesh, MemoryType
from amp.memory import AgentMemory


class TestAgentIdentity:
    """测试 Agent 身份系统"""

    def test_agent_creation(self):
        """测试 Agent 创建"""
        agent = Agent(
            name="TestAgent",
            role="tester",
            language="zh",
        )

        assert agent.identity.name == "TestAgent"
        assert agent.identity.role == "tester"
        assert agent.identity.language == "zh"
        assert agent.identity.level == 1
        assert len(agent.identity.agent_id) == 16

    def test_agent_persistence(self, tmp_path):
        """测试 Agent 持久化"""
        storage_dir = str(tmp_path)

        # 创建 Agent
        agent1 = Agent(
            name="PersistentAgent",
            role="tester",
            storage_dir=storage_dir,
        )
        original_id = agent1.identity.agent_id
        original_xp = agent1.identity.experience_points

        # 获得经验并保存
        agent1.identity.gain_experience(50)
        agent1._save_identity(agent1.identity)  # 保存身份

        # 重新加载（模拟重启）
        agent2 = Agent(
            name="PersistentAgent",
            role="tester",
            storage_dir=storage_dir,
        )

        # 应该保留相同的 ID 和 XP
        assert agent2.identity.agent_id == original_id
        assert agent2.identity.experience_points == original_xp + 50

    def test_agent_leveling(self):
        """测试 Agent 升级系统"""
        agent = Agent(name="Leveler", role="learner")

        # 初始等级
        assert agent.identity.level == 1
        assert agent.identity.experience_points == 0

        # 获得经验
        agent.identity.gain_experience(100)
        assert agent.identity.level == 2
        assert agent.identity.experience_points == 100

        agent.identity.gain_experience(150)
        assert agent.identity.level == 3
        assert agent.identity.experience_points == 250


class TestMemory:
    """测试记忆系统"""

    @pytest.mark.asyncio
    async def test_remember_and_recall(self, tmp_path):
        """测试记忆存储和回忆"""
        storage_dir = str(tmp_path)
        agent = Agent(name="MemAgent", role="tester", storage_dir=storage_dir)

        # 存储记忆
        await agent.memory.remember(
            "测试内容",
            type=MemoryType.SEMANTIC,
            importance=8,
            tags=["test"],
        )

        # 回忆
        memories = await agent.memory.recall("测试", limit=5)
        assert len(memories) >= 1
        assert "测试内容" in memories[0].content

    @pytest.mark.asyncio
    async def test_memory_types(self, tmp_path):
        """测试四种记忆类型"""
        agent = Agent(name="MultiMemory", role="tester", storage_dir=str(tmp_path))

        # 情景记忆
        await agent.memory.remember(
            "事件",
            type=MemoryType.EPISODIC,
        )

        # 语义记忆
        await agent.memory.remember(
            "事实",
            type=MemoryType.SEMANTIC,
        )

        # 程序记忆
        await agent.memory.remember(
            "方法",
            type=MemoryType.PROCEDURAL,
        )

        # 情感记忆
        await agent.memory.remember(
            "经验",
            type=MemoryType.EMOTIONAL,
            emotion="positive",
        )

        # 验证
        stats = agent.memory.stats()
        assert stats["by_type"]["episodic"] == 1
        assert stats["by_type"]["semantic"] == 1
        assert stats["by_type"]["procedural"] == 1
        assert stats["by_type"]["emotional"] == 1

    @pytest.mark.asyncio
    async def test_memory_strength(self, tmp_path):
        """测试记忆强度计算"""
        agent = Agent(name="StrengthAgent", role="tester", storage_dir=str(tmp_path))

        # 高重要性记忆
        await agent.memory.remember(
            "重要内容",
            type=MemoryType.SEMANTIC,
            importance=10,
        )

        # 低重要性记忆
        await agent.memory.remember(
            "琐碎内容",
            type=MemoryType.SEMANTIC,
            importance=1,
        )

        memories = await agent.memory.recall("内容", limit=5)

        # 高重要性记忆应该强度更高
        important = [m for m in memories if "重要" in m.content][0]
        trivial = [m for m in memories if "琐碎" in m.content][0]

        assert important.strength > trivial.strength


class TestAgentMesh:
    """测试 Agent Mesh 网络"""

    @pytest.mark.asyncio
    async def test_mesh_registration(self, tmp_path):
        """测试 Agent 注册"""
        mesh = AgentMesh()

        agent1 = Agent(name="Agent1", role="tester", storage_dir=str(tmp_path))
        agent2 = Agent(name="Agent2", role="tester", storage_dir=str(tmp_path))

        await mesh.register(agent1)
        await mesh.register(agent2)

        assert len(mesh) == 2
        assert mesh.get_agent(agent1.identity.agent_id) == agent1

    @pytest.mark.asyncio
    async def test_team_task(self, tmp_path):
        """测试团队任务"""
        mesh = AgentMesh()

        agent1 = Agent(name="Team1", role="worker", storage_dir=str(tmp_path))
        agent2 = Agent(name="Team2", role="worker", storage_dir=str(tmp_path))

        await mesh.register(agent1)
        await mesh.register(agent2)

        result = await mesh.team_task(
            task={
                "description": "团队任务测试",
                "importance": 7,
            },
            agents=[agent1, agent2],
        )

        assert result["status"] == "completed"
        assert result["team_size"] == 2

    @pytest.mark.asyncio
    async def test_knowledge_sharing(self, tmp_path):
        """测试知识共享"""
        storage_dir = str(tmp_path)

        teacher = Agent(name="Teacher", role="instructor", storage_dir=storage_dir)
        student = Agent(name="Student", role="learner", storage_dir=storage_dir)

        # 老师学习知识
        await teacher.memory.remember(
            "Python 异步编程技巧",
            type=MemoryType.PROCEDURAL,
            importance=9,
            tags=["python", "async"],
        )

        # 学生向老师学习
        learned = await student.learn_from(teacher, tags=["python"])

        assert learned >= 1


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """测试完整工作流程"""
        storage_dir = str(tmp_path)

        # 创建 Agent
        agent = Agent(
            name="Worker",
            role="worker",
            storage_dir=storage_dir,
            capabilities=["task_execution"],
        )

        # 存储记忆
        await agent.memory.remember(
            "工作偏好",
            type=MemoryType.SEMANTIC,
            importance=7,
            tags=["preference"],
        )

        # 执行任务
        result = await agent.act({
            "description": "执行测试任务",
            "importance": 6,
        })

        assert result["status"] == "completed"

        # 睡眠巩固
        stats = await agent.sleep()
        assert "promoted" in stats
        assert "decayed" in stats

        # 验证状态
        status = agent.status()
        assert status["identity"]["tasks_completed"] == 1
        assert status["memory_stats"]["total"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
