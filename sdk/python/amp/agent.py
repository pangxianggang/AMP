"""
AMP Agent — AI agents with persistent identity and memory.

An Agent is the core building block of AMP. Each agent has:
- A persistent identity (survives across sessions)
- A memory system (learns from experience)
- Capabilities (can execute tasks)
- Communication (can talk to other agents)
- Skills (can call OpenClaw skills)

Example:
    from amp.memory import MemoryType

    agent = Agent(name="Ali", role="project_manager")
    await agent.memory.remember("User prefers Chinese", type=MemoryType.SEMANTIC)
    result = await agent.act({"description": "Plan the project"})

    # 使用技能
    search_result = await agent.use_skill("serper", query="Python 异步编程")
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from amp.memory import AgentMemory, MemoryType

if TYPE_CHECKING:
    from amp.openclaw import OpenClawIntegration

logger = logging.getLogger(__name__)


@dataclass
class AgentIdentity:
    """
    Persistent identity for an AMP agent.

    Once created, the agent_id never changes. Statistics
    accumulate over the agent's lifetime.

    Attributes:
        name: Human-readable name
        role: Agent's primary role
        version: Agent version (semver)
        created_at: Creation timestamp
        personality: Behavioral traits
        capabilities: List of skills
        language: Preferred language
        reporting_to: Parent agent or human identifier
        tasks_completed: Successful task count
        tasks_failed: Failed task count
        experience_points: Accumulated XP
        level: Agent level (XP / 100 + 1)
    """

    name: str
    role: str
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Personality and capabilities
    personality: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    language: str = "zh"  # Default to Chinese
    reporting_to: Optional[str] = None

    # Lifetime statistics
    tasks_completed: int = 0
    tasks_failed: int = 0
    experience_points: int = 0
    level: int = 1

    @property
    def agent_id(self) -> str:
        """Deterministic unique identifier (基于 name 和 role，确保持久化)."""
        raw = f"{self.name}:{self.role}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @property
    def success_rate(self) -> float:
        """Task success rate."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.0
        return round(self.tasks_completed / total, 4)

    def gain_experience(self, points: int) -> None:
        """Award experience points and level up if needed."""
        self.experience_points += points
        new_level = (self.experience_points // 100) + 1
        if new_level > self.level:
            logger.info(
                f"🎉 Agent '{self.name}' leveled up! "
                f"Level {self.level} → {new_level}"
            )
            self.level = new_level

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = asdict(self)
        data["agent_id"] = self.agent_id
        data["success_rate"] = self.success_rate
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        """Deserialize from dictionary."""
        # Remove computed fields
        data.pop("agent_id", None)
        data.pop("success_rate", None)
        return cls(**data)


class Agent:
    """
    AMP Agent — An AI agent with identity, memory, and learning.

    This is the core class of AMP. An Agent can:
    - Remember experiences and learn from them
    - Execute tasks and track success/failure
    - Communicate with other agents
    - Learn from other agents' experiences
    - Consolidate memories (like human sleep)
    - Use OpenClaw skills (serper, github, etc.)

    Example:
        from amp.memory import MemoryType

        agent = Agent(name="Ali", role="project_manager")
        await agent.memory.remember("Python 3.12 is faster", type=MemoryType.SEMANTIC)
        result = await agent.act({"description": "Find best framework"})

        # 使用技能
        search_result = await agent.use_skill("serper", query="Python 异步编程")
    """

    def __init__(
        self,
        name: str,
        role: str,
        storage_dir: Optional[str] = None,
        language: str = "zh",
        capabilities: Optional[List[str]] = None,
        enable_fm: bool = False,  # 启用火星文件管理
        enable_memory_bank: bool = False,  # 启用 Memory Bank 同步
        enable_openclaw: bool = False,  # 启用 OpenClaw 集成
        **kwargs,
    ):
        # Determine storage directory
        if storage_dir is None:
            storage_dir = str(Path.home() / ".amp" / "agents")

        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 集成开关
        self._enable_fm = enable_fm
        self._enable_memory_bank = enable_memory_bank
        self._enable_openclaw = enable_openclaw
        
        # 集成模块（延迟初始化）
        self._fm_storage = None
        self._memory_bank = None
        self._openclaw = None

        # Try to load existing identity
        self.identity = self._load_or_create_identity(
            name=name,
            role=role,
            language=language,
            capabilities=capabilities or [],
            **kwargs,
        )
        
        # 初始化 FM 存储后端
        fm_storage = None
        if enable_fm:
            from amp.fm_storage import FMStorage
            fm_storage = FMStorage(workspace=str(self._storage_dir))
        
        # 初始化记忆后端
        memory_bank_url = kwargs.get("memory_bank_url", "http://localhost:8100")
        backend = "local"
        if enable_fm:
            backend = "fm"
        elif enable_memory_bank:
            backend = "memory_bank"
        
        # Initialize memory system (with auto-load on creation)
        self.memory = AgentMemory(
            agent_id=self.identity.agent_id,
            storage_dir=str(self._storage_dir),
            backend=backend,
            fm_storage=fm_storage,
            memory_bank_url=memory_bank_url,
            auto_load=True,  # ✅ 创建时自动加载记忆
        )
        
        # 同步加载记忆（如果后端支持）
        if backend == "local":
            self.memory._load_memories_sync()
            logger.debug(f"📂 Loaded {self.memory.count()} memories for {self.identity.name}")

        # Task handlers (registered capabilities)
        self._task_handlers: Dict[str, Callable] = {}

        # 初始化 OpenClaw 集成
        if enable_openclaw:
            self._init_openclaw_integration()

        logger.info(f"🤖 Agent initialized: {self.identity.name} ({self.identity.role})")
        logger.info(f"   Features: FM={enable_fm}, MemoryBank={enable_memory_bank}, OpenClaw={enable_openclaw}")

    async def initialize(self) -> None:
        """异步初始化 Agent（加载记忆等）

        Example:
            agent = Agent(name="Ali", role="manager", enable_fm=True)
            await agent.initialize()
        """
        await self.memory.initialize()
        logger.info(f"Agent async initialized: {self.identity.name}")
    
    def _init_openclaw_integration(self):
        """初始化 OpenClaw 集成"""
        try:
            from amp.openclaw import OpenClawIntegration
            self._openclaw = OpenClawIntegration()
            logger.info("OpenClaw integration enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenClaw integration: {e}")
            self._openclaw = None
    
    async def use_skill(
        self,
        skill_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        使用 OpenClaw 技能
        
        Args:
            skill_name: 技能名称 (如 "serper", "github", "weather")
            **kwargs: 技能参数
            
        Returns:
            技能执行结果
            
        Example:
            # 联网搜索
            result = await agent.use_skill("serper", query="Python 异步编程")
            
            # GitHub 操作
            result = await agent.use_skill("github", command="issues", repo="user/repo")
        """
        if not self._openclaw:
            logger.warning("OpenClaw integration not enabled")
            return {
                "status": "error",
                "message": "OpenClaw integration not enabled. Use enable_openclaw=True when creating agent."
            }
        
        logger.info(f"Using skill: {skill_name}")
        
        # 记录使用技能到情景记忆
        await self.memory.remember(
            content=f"Used skill '{skill_name}' with args: {kwargs}",
            type=MemoryType.EPISODIC,
            importance=4,
            tags=["skill", "openclaw", skill_name],
        )
        
        result = await self._openclaw.use_skill(skill_name, **kwargs)
        
        if result.get("status") == "success":
            # 记录成功经验
            await self.memory.remember(
                content=f"Successfully used {skill_name}: {str(result.get('result', ''))[:100]}",
                type=MemoryType.EMOTIONAL,
                importance=6,
                emotion="positive",
                tags=["skill", "success", skill_name],
            )
        else:
            # 记录失败教训
            await self.memory.remember(
                content=f"Failed to use {skill_name}: {result.get('error', 'unknown error')}",
                type=MemoryType.EMOTIONAL,
                importance=7,
                emotion="negative",
                tags=["skill", "failure", "lesson", skill_name],
            )
        
        return result

    def _load_or_create_identity(
        self,
        name: str,
        role: str,
        language: str = "zh",
        capabilities: Optional[List[str]] = None,
        **kwargs,
    ) -> AgentIdentity:
        """Load existing identity or create new one."""
        identity_file = self._storage_dir / f"{name.lower()}.json"

        if identity_file.exists():
            try:
                data = json.loads(identity_file.read_text(encoding="utf-8"))
                # Check if it matches
                if data.get("name", "").lower() == name.lower() and data.get("role", "").lower() == role.lower():
                    identity = AgentIdentity.from_dict(data)
                    logger.info(f"Loaded existing agent: {name}")
                    return identity
            except Exception as e:
                logger.warning(f"Failed to load identity: {e}")

        # Create new identity
        identity = AgentIdentity(
            name=name,
            role=role,
            language=language,
            capabilities=capabilities or [],
            **kwargs,
        )
        self._save_identity(identity)
        logger.info(f"✨ Created new agent: {name}")
        return identity

    def _save_identity(self, identity: AgentIdentity) -> None:
        """Save identity to disk."""
        identity_file = self._storage_dir / f"{identity.name.lower()}.json"
        identity_file.write_text(
            json.dumps(identity.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def register_capability(
        self,
        name: str,
        handler: Callable,
    ) -> None:
        """
        Register a task handler (capability).

        Args:
            name: Capability name
            handler: Async function to handle tasks
        """
        self._task_handlers[name] = handler
        if name not in self.identity.capabilities:
            self.identity.capabilities.append(name)
            self._save_identity(self.identity)

    async def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task.

        Args:
            task: Task description with 'description' and optional metadata

        Returns:
            Task result
        """
        description = task.get("description", "")
        capability = task.get("capability")

        logger.info(f"⚡ Agent '{self.identity.name}' acting on: {description[:50]}...")

        try:
            # If specific capability requested
            if capability and capability in self._task_handlers:
                result = await self._task_handlers[capability](task)
            else:
                # General task — store as episodic memory
                await self.memory.remember(
                    content=f"Task: {description}",
                    type=MemoryType.EPISODIC,
                    importance=task.get("importance", 5),
                    tags=task.get("tags", []),
                )
                result = {"status": "completed", "description": description}

            # Check result status and create appropriate memory
            if result.get("status") == "failed":
                # Record failure (问题解决记忆)
                self.identity.tasks_failed += 1
                self.identity.gain_experience(3)  # +3 XP for lesson learned
                self._save_identity(self.identity)

                # Store as emotional memory (lesson from failure)
                await self.memory.remember(
                    content=f"Failed: {description} — {result.get('error', 'unknown error')}",
                    type=MemoryType.EMOTIONAL,
                    importance=8,
                    emotion="negative",
                    tags=task.get("tags", []),
                )
            elif result.get("status") == "completed":
                # Record success
                self.identity.tasks_completed += 1
                self.identity.gain_experience(10)  # +10 XP for completed task
                self._save_identity(self.identity)

                # Store as procedural memory
                await self.memory.remember(
                    content=f"Successfully completed: {description}",
                    type=MemoryType.PROCEDURAL,
                    importance=6,
                    emotion="positive",
                    tags=task.get("tags", []),
                )

            return result

        except Exception as e:
            # Record failure
            self.identity.tasks_failed += 1
            self.identity.gain_experience(3)  # +3 XP for lesson learned
            self._save_identity(self.identity)

            # Store as emotional memory (lesson from failure)
            await self.memory.remember(
                content=f"Failed: {description} — Error: {str(e)}",
                type=MemoryType.EMOTIONAL,
                importance=8,
                emotion="negative",
                tags=task.get("tags", []),
            )

            return {"status": "failed", "error": str(e)}

    async def think(self, topic: str) -> Optional[str]:
        """
        Think about a topic — recall relevant memories and reason.

        In v1.0, this is a framework for future LLM integration.

        Args:
            topic: Topic to think about

        Returns:
            Reasoned response (or None if not enough information)
        """
        # Recall relevant memories
        memories = await self.memory.recall(topic, limit=5)

        if not memories:
            return None

        # Build context from memories
        context_parts = []
        for mem in memories:
            context_parts.append(f"- [{mem.type.value}] {mem.content}")

        context = "\n".join(context_parts)

        logger.debug(f"🧠 Agent '{self.identity.name}' thinking about: {topic}")
        logger.debug(f"   Context:\n{context}")

        # In v2.0: Call LLM with context for reasoning
        # For now, return the retrieved context
        return context

    async def learn_from(
        self,
        other_agent: "Agent",
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,  # ✅ 提高上限从 20 到 100
    ) -> int:
        """
        Learn from another agent's experiences (optimized version).

        Args:
            other_agent: Agent to learn from
            topic: Optional topic filter (loose matching)
            tags: Optional tags filter
            limit: Maximum memories to learn

        Returns:
            Number of memories learned
        """
        memories_to_share = []

        if topic:
            # Step 1: 使用 recall 搜索 topic
            memories_to_share = await other_agent.memory.recall(topic, limit=limit)

            # Step 2: 如果 recall 结果不足，尝试直接遍历所有记忆进行宽松匹配
            if len(memories_to_share) < limit:
                # 对 topic 分词（支持中英文）
                topic_keywords = self._extract_keywords(topic)

                for memory in other_agent.memory._memories.values():
                    if memory in memories_to_share:
                        continue

                    # 多维度匹配
                    match_score = 0

                    # 内容匹配（检查关键词）
                    content_lower = memory.content.lower()
                    for keyword in topic_keywords:
                        if keyword.lower() in content_lower:
                            match_score += 1

                    # 标签匹配（检查关键词）
                    for tag in memory.tags:
                        tag_lower = tag.lower()
                        for keyword in topic_keywords:
                            if keyword.lower() in tag_lower:
                                match_score += 1

                    # 上下文匹配
                    if memory.context:
                        context_lower = memory.context.lower()
                        for keyword in topic_keywords:
                            if keyword.lower() in context_lower:
                                match_score += 1

                    if match_score > 0:
                        memories_to_share.append(memory)

                    if len(memories_to_share) >= limit:
                        break

            # Step 3: 如果还是没有结果，返回对方最近的记忆（友好降级）
            if not memories_to_share:
                logger.info(f"No memories found for topic '{topic}', returning recent memories")
                memories_to_share = sorted(
                    other_agent.memory._memories.values(),
                    key=lambda m: m.created_at,
                    reverse=True
                )[:limit]

        elif tags:
            # Tag matching (支持子串匹配)
            memories_to_share = [
                m for m in other_agent.memory._memories.values()
                if any(search_tag.lower() in memory_tag.lower() or memory_tag.lower() in search_tag.lower()
                       for search_tag in tags for memory_tag in m.tags)
            ][:limit]
        else:
            # No filter: share recent memories
            memories_to_share = sorted(
                other_agent.memory._memories.values(),
                key=lambda m: m.created_at,
                reverse=True
            )[:limit]

        learned_count = 0
        for memory in memories_to_share:
            # Copy memory with source attribution
            await self.memory.remember(
                content=memory.content,
                type=memory.type,
                importance=memory.importance,
                context=memory.context,
                tags=memory.tags,
                emotion=memory.emotion,
                source_agent=other_agent.identity.agent_id,
            )
            learned_count += 1

        if learned_count > 0:
            self.identity.gain_experience(learned_count * 5)  # +5 XP per memory
            self._save_identity(self.identity)
            logger.info(
                f"📚 Agent '{self.identity.name}' learned {learned_count} "
                f"memories from '{other_agent.identity.name}'"
            )

        return learned_count

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词（支持中英文简单分词）

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        # 简单分词：按空格、标点符号分割
        import re
        # 移除常见停用词
        stopwords = {'的', '了', '在', '是', '和', '与', '及', '等', '一个', '这个', '那个'}

        # 按空格和常见标点分割
        words = re.split(r'[\s,，.。;；:：!！?？]+', text.strip())

        # 过滤空字符串和停用词
        keywords = [w for w in words if w and w not in stopwords and len(w) > 1]

        # 如果没有有效分词，返回原文本（长度>1 时）
        if not keywords and len(text) > 1:
            keywords = [text]

        return keywords

    async def sleep(self) -> Dict[str, int]:
        """
        Consolidate memories (like human sleep).

        Should be called periodically (e.g., daily or after many tasks).

        Returns:
            Consolidation statistics
        """
        logger.info(f"Agent '{self.identity.name}' sleeping (consolidating memories)...")
        stats = await self.memory.consolidate()
        
        # Bonus XP for consolidation
        if stats["promoted"] > 0:
            self.identity.gain_experience(stats["promoted"] * 2)
            self._save_identity(self.identity)

        return stats

    def status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "identity": self.identity.to_dict(),
            "memory_stats": self.memory.stats(),
            "capabilities": self.identity.capabilities,
        }

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.identity.name!r}, role={self.identity.role!r}, "
            f"level={self.identity.level}, xp={self.identity.experience_points})"
        )
