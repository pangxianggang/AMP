"""
AMP — Agent Memory Protocol

The open protocol for AI agents that remember, learn, and collaborate.

Usage:
    import amp

    # 基础用法
    agent = amp.Agent(name="Ali", role="project_manager")
    await agent.memory.remember("User prefers Chinese", type=amp.MemoryType.SEMANTIC)
    memories = await agent.memory.recall("user preferences")

    # 启用高级功能
    agent = amp.Agent(
        name="Ali",
        role="project_manager",
        enable_fm=True,              # 火星文件管理
        enable_memory_bank=True,     # Memory Bank 同步
        enable_openclaw=True,        # OpenClaw 集成
    )

    # 使用技能
    result = await agent.use_skill("serper", query="Python 异步编程")

Every AI deserves to remember.
"""

__version__ = "1.0.0"
__author__ = "Pang & AMP Contributors"
__license__ = "MIT"

from amp.agent import Agent, AgentIdentity
from amp.memory import AgentMemory, Memory, MemoryType
from amp.mesh import AgentMesh, Message

# 存储后端
from amp.fm_storage import FMStorage

# 集成模块
from amp.memory_bank import MemoryBankIntegration
from amp.openclaw import OpenClawIntegration
from amp.heartbeat import HeartbeatManager

# 配置
from amp.config import AMPConfig, load_config, get_config

__all__ = [
    # Core
    "Agent",
    "AgentIdentity",
    "AgentMemory",
    "Memory",
    "MemoryType",
    "AgentMesh",
    "Message",

    # Storage Backends
    "FMStorage",

    # Integrations
    "MemoryBankIntegration",
    "OpenClawIntegration",
    "HeartbeatManager",

    # Configuration
    "AMPConfig",
    "load_config",
    "get_config",
]
