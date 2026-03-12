"""
AMP Memory System — Four types of memory inspired by cognitive science.

Memory Types:
- Episodic: What happened (events and experiences)
- Semantic: What I know (facts and concepts)
- Procedural: How to do things (skills and methods)
- Emotional: What worked and what didn't (valenced experiences)

Each memory follows the Ebbinghaus forgetting curve — frequently accessed
and important memories stay strong, while trivial details naturally fade.

Storage Backends:
- Local JSON files (default)
- FM-Engine (火星文件管理系统) - 支持事务/版本控制/回滚
- Memory Bank (Qdrant 向量数据库) - 支持语义搜索
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
import math

if TYPE_CHECKING:
    from amp.fm_storage import FMStorage

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Four types of memory inspired by cognitive science."""
    EPISODIC = "episodic"      # What happened
    SEMANTIC = "semantic"      # What I know
    PROCEDURAL = "procedural"  # How to do things
    EMOTIONAL = "emotional"    # What worked/failed


@dataclass
class Memory:
    """
    A single memory unit.

    Attributes:
        id: Unique memory identifier
        type: Memory type (episodic/semantic/procedural/emotional)
        content: Memory content
        created_at: When the memory was formed
        importance: Importance level (1-10)
        context: Surrounding context
        tags: Categorization tags
        emotion: Emotional valence (positive/negative/neutral)
        source_agent: If learned from another agent
        connections: IDs of related memories
        accessed_count: How often recalled
        last_accessed: Last recall time
        strength: Computed memory strength (0.0-1.0)
    """
    id: str
    type: MemoryType
    content: str
    created_at: str
    importance: int = 5
    context: str = ""
    tags: List[str] = field(default_factory=list)
    emotion: str = "neutral"  # positive, negative, neutral
    source_agent: Optional[str] = None
    connections: List[str] = field(default_factory=list)
    accessed_count: int = 0
    last_accessed: Optional[str] = None
    strength: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = asdict(self)
        data["type"] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Deserialize from dictionary."""
        if "type" in data:
            data["type"] = MemoryType(data["type"])
        return cls(**data)

    def compute_strength(self) -> float:
        """
        Compute memory strength using Ebbinghaus forgetting curve.

        strength = (importance / 10) + min(accessed_count * 0.1, 0.5) × time_decay
        where: time_decay = 1.0 / (1.0 + age_hours / 24.0)
        """
        now = datetime.now()
        created = datetime.fromisoformat(self.created_at)
        age_hours = (now - created).total_seconds() / 3600

        # Time decay factor
        time_decay = 1.0 / (1.0 + age_hours / 24.0)

        # Base strength from importance
        base_strength = self.importance / 10.0

        # Access bonus (capped at 0.5)
        access_bonus = min(self.accessed_count * 0.1, 0.5)

        # Final strength
        self.strength = (base_strength + access_bonus) * time_decay
        return self.strength

    def is_candidate_for_forgetting(self) -> bool:
        """Check if this memory should be forgotten (strength < 0.1)."""
        return self.compute_strength() < 0.1


class AgentMemory:
    """
    Agent Memory System — Manages all four types of memory.

    Features:
    - Store and retrieve memories by type
    - Semantic search (keyword-based in v1.0)
    - Memory consolidation (strengthen/fade/merge)
    - Cross-agent memory sharing
    - Persistence to local storage
    - FM-Engine 事务支持（可选）
    - Memory Bank 集成（可选）

    Storage Backends:
    - local: 本地 JSON 文件（默认）
    - fm: 火星文件管理系统（支持事务/回滚）
    - memory_bank: Memory Bank（Qdrant 向量数据库）

    Example:
        memory = AgentMemory(agent_id="ali-123")
        await memory.remember(
            "User prefers Chinese responses",
            type=MemoryType.SEMANTIC,
            importance=8
        )
        memories = await memory.recall("user preferences")
    """

    def __init__(
        self,
        agent_id: str,
        storage_dir: Optional[str] = None,
        backend: str = "local",  # "local", "fm", "memory_bank"
        fm_storage: Optional["FMStorage"] = None,
        memory_bank_url: Optional[str] = None,
        auto_load: bool = True,  # ✅ 创建时自动加载记忆
    ):
        self.agent_id = agent_id
        self._storage_dir = Path(storage_dir) if storage_dir else None
        self._backend = backend
        self._fm_storage = fm_storage
        self._memory_bank_url = memory_bank_url or "http://localhost:8100"

        self._memories: Dict[str, Memory] = {}
        self._index: Dict[MemoryType, Set[str]] = {t: set() for t in MemoryType}

        # 事务管理
        self._current_transaction: Optional[str] = None

        if self._storage_dir:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            # ✅ 使用 auto_load 参数控制是否自动加载
            if auto_load:
                # 同步加载（仅本地存储）
                if backend == "local":
                    self._load_memories_sync()
                # FM 后端也支持同步加载
                elif backend == "fm" and fm_storage:
                    self._load_memories_sync()

    async def initialize(self) -> None:
        """异步初始化 AgentMemory（推荐用法）

        Example:
            memory = AgentMemory(agent_id="test", backend="fm")
            await memory.initialize()
        """
        if self._storage_dir:
            await self._load_memories()

    def _load_memories_sync(self) -> None:
        """同步加载记忆（仅用于本地存储后端）"""
        if self._backend != "local":
            logger.warning("Sync load only supports local backend, use initialize() for async backends")
            return

        mem_dir = self._get_memory_dir()
        if not mem_dir.exists():
            return

        for mem_type in MemoryType:
            type_dir = mem_dir / mem_type.value
            if not type_dir.exists():
                continue

            for mem_file in type_dir.glob("*.json"):
                try:
                    data = json.loads(mem_file.read_text(encoding="utf-8"))
                    memory = Memory.from_dict(data)
                    self._memories[memory.id] = memory
                    self._index[mem_type].add(memory.id)
                except Exception as e:
                    logger.warning(f"Failed to load memory {mem_file}: {e}")

    def _get_memory_dir(self) -> Path:
        """Get memory storage directory."""
        if not self._storage_dir:
            raise ValueError("storage_dir not set")
        return self._storage_dir / self.agent_id / "memories"

    async def _load_memories(self) -> None:
        """Load memories from disk."""
        # 如果使用 FM 存储后端
        if self._backend == "fm" and self._fm_storage:
            memories = await self._fm_storage.load_memories(self.agent_id)
            self._memories = memories
            for memory in memories.values():
                self._index[memory.type].add(memory.id)
            return

        # 本地存储后端
        mem_dir = self._get_memory_dir()
        if not mem_dir.exists():
            return

        for mem_type in MemoryType:
            type_dir = mem_dir / mem_type.value
            if not type_dir.exists():
                continue

            for mem_file in type_dir.glob("*.json"):
                try:
                    data = json.loads(mem_file.read_text(encoding="utf-8"))
                    memory = Memory.from_dict(data)
                    self._memories[memory.id] = memory
                    self._index[mem_type].add(memory.id)
                except Exception as e:
                    logger.warning(f"Failed to load memory {mem_file}: {e}")

    async def _save_memory(self, memory: Memory) -> None:
        """Save a single memory to disk."""
        if not self._storage_dir and not self._fm_storage:
            return

        # 使用 FM 存储后端
        if self._backend == "fm" and self._fm_storage:
            await self._fm_storage.save_memory(
                self.agent_id,
                memory,
                self._current_transaction
            )
            return

        # 本地存储后端
        mem_dir = self._get_memory_dir()
        type_dir = mem_dir / memory.type.value
        type_dir.mkdir(parents=True, exist_ok=True)

        mem_file = type_dir / f"{memory.id}.json"
        mem_file.write_text(
            json.dumps(memory.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    async def remember(
        self,
        content: str,
        type: MemoryType = MemoryType.EPISODIC,
        importance: int = 5,
        context: str = "",
        tags: Optional[List[str]] = None,
        emotion: str = "neutral",
        source_agent: Optional[str] = None,
        connections: Optional[List[str]] = None,
    ) -> Memory:
        """
        Store a new memory.

        Args:
            content: Memory content
            type: Memory type
            importance: Importance level (1-10)
            context: Surrounding context
            tags: Categorization tags
            emotion: Emotional valence
            source_agent: If learned from another agent
            connections: Related memory IDs

        Returns:
            The created Memory object
        """
        # Generate memory ID
        timestamp = datetime.now().isoformat()
        raw = f"{self.agent_id}:{content}:{timestamp}"
        mem_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        memory = Memory(
            id=mem_id,
            type=type,
            content=content,
            created_at=timestamp,
            importance=importance,
            context=context,
            tags=tags or [],
            emotion=emotion,
            source_agent=source_agent,
            connections=connections or [],
        )

        # Store in memory and disk
        self._memories[mem_id] = memory
        self._index[type].add(mem_id)
        await self._save_memory(memory)
        
        # 同步到 Memory Bank（如果启用）
        if self._backend == "memory_bank":
            await self._sync_to_memory_bank(memory)

        logger.debug(f"💾 Stored {type.value} memory: {content[:50]}...")
        return memory

    async def recall(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        limit: int = 10,
        min_strength: float = 0.1,
        tags: Optional[List[str]] = None,
    ) -> List[Memory]:
        """
        Recall relevant memories.

        Args:
            query: Search query
            type: Filter by memory type
            limit: Maximum results
            min_strength: Minimum memory strength
            tags: Filter by tags

        Returns:
            List of relevant memories, sorted by relevance
        """
        results = []

        for mem_id, memory in self._memories.items():
            # Update access time
            memory.last_accessed = datetime.now().isoformat()
            memory.accessed_count += 1

            # Compute current strength
            strength = memory.compute_strength()
            if strength < min_strength:
                continue

            # Type filter
            if type and memory.type != type:
                continue

            # Tag filter
            if tags and not any(t in memory.tags for t in tags):
                continue

            # Keyword search (v1.0 — semantic search in future)
            query_lower = query.lower()
            content_match = query_lower in memory.content.lower()
            context_match = query_lower in memory.context.lower()
            tags_match = any(query_lower in t.lower() for t in memory.tags)

            if content_match or context_match or tags_match:
                results.append((strength, memory))

        # Sort by strength (descending)
        results.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in results[:limit]]

    async def consolidate(self) -> Dict[str, int]:
        """
        Consolidate memories (like human sleep).

        Operations:
        1. Strengthen important memories
        2. Fade old, unaccessed memories
        3. Merge similar memories
        4. Discover patterns

        Returns:
            Statistics about consolidation
        """
        stats = {
            "promoted": 0,
            "decayed": 0,
            "merged": 0,
            "patterns_found": 0,
        }

        # Process each memory
        to_remove = []
        for mem_id, memory in list(self._memories.items()):
            strength = memory.compute_strength()

            # Fade weak memories
            if memory.is_candidate_for_forgetting():
                to_remove.append(mem_id)
                stats["decayed"] += 1
                continue

            # Strengthen high-importance memories
            if memory.importance >= 8 and memory.accessed_count >= 3:
                memory.strength = min(memory.strength * 1.1, 1.0)
                stats["promoted"] += 1

        # Remove decayed memories
        for mem_id in to_remove:
            memory = self._memories.pop(mem_id)
            self._index[memory.type].discard(mem_id)
            
            # 如果使用 FM 存储，需要删除文件
            if self._backend == "fm" and self._fm_storage:
                await self._fm_storage.delete_memory(
                    self.agent_id,
                    mem_id,
                    memory.type,
                    self._current_transaction
                )

        # Save updated memories
        for memory in self._memories.values():
            await self._save_memory(memory)

        logger.info(
            f"💤 Consolidation complete: "
            f"promoted={stats['promoted']}, decayed={stats['decayed']}"
        )
        return stats
    
    async def _sync_to_memory_bank(self, memory: Memory) -> None:
        """同步记忆到 Memory Bank"""
        try:
            import aiohttp
            
            payload = {
                "content": memory.content,
                "memory_type": memory.type.value,
                "agent_id": self.agent_id,
                "scope": "agent",
                "importance": memory.importance,
                "tags": memory.tags,
                "metadata": {
                    "emotion": memory.emotion,
                    "context": memory.context,
                    "source_agent": memory.source_agent,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._memory_bank_url}/memory/write",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.debug(f"Synced memory to Memory Bank: {memory.id}")
                    else:
                        logger.warning(f"Failed to sync memory to Memory Bank: {resp.status}")
        except ImportError:
            logger.debug("aiohttp not available, skipping Memory Bank sync")
        except Exception as e:
            logger.debug(f"Memory Bank sync failed: {e}")
    
    def begin_transaction(self) -> str:
        """
        开始一个事务
        
        Returns:
            事务 ID
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self._current_transaction = f"tx-{timestamp}-{id(self)}"
        logger.debug(f"Begin transaction: {self._current_transaction}")
        return self._current_transaction
    
    async def commit_transaction(self) -> bool:
        """
        提交当前事务

        Returns:
            是否成功
        """
        if not self._current_transaction:
            logger.warning("No active transaction to commit")
            return False

        if self._backend == "fm" and self._fm_storage:
            result = await self._fm_storage.commit(self._current_transaction)
            success = result.success

            if success:
                logger.info(f"✅ Transaction {self._current_transaction} committed")
            else:
                logger.error(f"❌ Transaction {self._current_transaction} failed: {result.error}")
        else:
            success = True
            logger.info(f"Transaction {self._current_transaction} committed (no FM backend)")

        self._current_transaction = None
        return success
    
    async def rollback_transaction(self) -> bool:
        """
        回滚当前事务
        
        Returns:
            是否成功
        """
        if not self._current_transaction:
            logger.warning("No active transaction to rollback")
            return False
        
        if self._backend == "fm" and self._fm_storage:
            import asyncio
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                self._fm_storage.rollback(self._current_transaction)
            )
            success = result.success
        else:
            success = True
        
        status_msg = "Success" if success else "Failed"
        logger.warning(f"Rollback transaction: {self._current_transaction} - {status_msg}")
        self._current_transaction = None
        return success

    async def share_to(
        self,
        target_memory: "AgentMemory",
        memory_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Share memories with another agent.

        Args:
            target_memory: Target agent's memory system
            memory_ids: Specific memories to share
            tags: Share all memories with matching tags

        Returns:
            Number of memories shared
        """
        shared_count = 0

        for mem_id, memory in self._memories.items():
            # Check if this memory should be shared
            should_share = False

            if memory_ids and mem_id in memory_ids:
                should_share = True
            if tags and any(t in memory.tags for t in tags):
                should_share = True

            if should_share:
                # Create copy with source attribution
                await target_memory.remember(
                    content=memory.content,
                    type=memory.type,
                    importance=memory.importance,
                    context=memory.context,
                    tags=memory.tags,
                    emotion=memory.emotion,
                    source_agent=self.agent_id,
                )
                shared_count += 1

        logger.info(f"Shared {shared_count} memories to {target_memory.agent_id}")
        return shared_count

    def count(self) -> int:
        """Get total memory count."""
        return len(self._memories)

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        by_type = {t.value: 0 for t in MemoryType}
        by_emotion = {"positive": 0, "negative": 0, "neutral": 0}

        for memory in self._memories.values():
            by_type[memory.type.value] += 1
            by_emotion[memory.emotion] += 1

        return {
            "total": len(self._memories),
            "by_type": by_type,
            "by_emotion": by_emotion,
            "agent_id": self.agent_id,
        }
