"""
AMP Agent — AI agents with persistent identity, memory, and growth.

Simplified v2.0:
- Zero external dependencies
- Clean memory management via memory package
- Standard export/import for portability
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from amp.memory.types import (
    Memory, MemoryType, MemoryTier,
    CANDIDATE_CONFIDENCE,
)
from amp.memory.store import MemoryStore
from amp.memory.recall import MemoryRecaller, RecallResult
from amp.memory.forgetting import (
    MemoryConsolidator,
    ForgettingConfig,
    compute_strength,
    DEFAULT_CONFIG,
)
from amp.memory.quality import QualityManager, ConflictResult
from amp.export.json_export import (
    export_memories,
    import_memories,
    save_amp_file,
    load_amp_file,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentIdentity:
    """
    Persistent identity for an AMP agent.

    Attributes:
        name: Human-readable name
        role: Agent's primary role
        version: Agent version
        created_at: Creation timestamp
        language: Preferred language
        capabilities: List of skills
        tasks_completed: Successful task count
        tasks_failed: Failed task count
        experience_points: Accumulated XP
        level: Agent level
    """

    name: str
    role: str
    version: str = "2.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    language: str = "zh"
    capabilities: List[str] = field(default_factory=list)
    tasks_completed: int = 0
    tasks_failed: int = 0
    experience_points: int = 0
    level: int = 1

    @property
    def agent_id(self) -> str:
        """Deterministic unique identifier."""
        raw = f"{self.name}:{self.role}:{self.created_at}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @property
    def success_rate(self) -> float:
        """Task success rate."""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.0
        return round(self.tasks_completed / total, 4)

    def gain_xp(self, points: int) -> None:
        """Award XP and level up if needed."""
        self.experience_points += points
        new_level = (self.experience_points // 100) + 1
        if new_level > self.level:
            logger.info(f"Agent '{self.name}' leveled up! {self.level} -> {new_level}")
            self.level = new_level

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["agent_id"] = self.agent_id
        data["success_rate"] = self.success_rate
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        data.pop("agent_id", None)
        data.pop("success_rate", None)
        return cls(**data)


class AgentMemory:
    """
    Agent Memory System — the public API for memory operations.

    Wraps store, recaller, quality manager, and consolidator.
    """

    def __init__(
        self,
        agent_id: str,
        storage_dir: str,
        forgetting_config: Optional[ForgettingConfig] = None,
    ):
        self.agent_id = agent_id
        self._store = MemoryStore(agent_id, storage_dir)
        self._memories: Dict[str, Memory] = self._store.load_all()
        self._recaller = MemoryRecaller(self._memories)
        self._quality = QualityManager(self._memories)
        self._config = forgetting_config or DEFAULT_CONFIG

        # Recompute strengths on load
        for m in self._memories.values():
            m.strength = compute_strength(m, self._config)

    async def initialize(self) -> None:
        """Async initialization (compatibility). Memories loaded in __init__."""
        pass

    async def remember(
        self,
        content: str,
        type: Any = MemoryType.EPISODIC,
        importance: int = 5,
        context: str = "",
        tags: Optional[List[str]] = None,
        emotion: str = "neutral",
        source_agent: Optional[str] = None,
        source_type: str = "self",
        tier: Optional[MemoryTier] = None,
    ) -> Memory:
        """Store a new memory."""
        timestamp = datetime.now().isoformat()
        raw = f"{self.agent_id}:{content}:{timestamp}"
        mem_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        # Normalize type
        if isinstance(type, str):
            type = MemoryType(type)

        # Auto-assign tier based on importance
        if tier is None:
            if importance >= 8:
                tier = MemoryTier.LONG_TERM
            elif importance >= 5:
                tier = MemoryTier.SHORT_TERM
            else:
                tier = MemoryTier.WORKING

        memory = Memory(
            id=mem_id,
            type=type,
            content=content,
            created_at=timestamp,
            tier=tier,
            importance=importance,
            confidence=CANDIDATE_CONFIDENCE,
            context=context,
            tags=tags or [],
            emotion=emotion,
            source_agent=source_agent,
            source_type=source_type,
        )

        # Check for conflicts
        conflicts = self._quality.check_conflicts(content, type, tags)
        for conflict in conflicts:
            logger.info(f"Conflict detected: {conflict.description}")

        self._memories[mem_id] = memory
        self._store.save(memory)
        return memory

    async def recall(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        tier: Optional[MemoryTier] = None,
        min_confidence: float = 0.0,
        min_strength: float = 0.0,
        tags: Optional[List[str]] = None,
        include_candidates: bool = True,
        limit: int = 10,
    ) -> List[Memory]:
        """Recall relevant memories."""
        results = self._recaller.search(
            query=query,
            type=type,
            tier=tier,
            min_confidence=min_confidence,
            min_strength=min_strength,
            tags=tags,
            include_candidates=include_candidates,
            limit=limit,
        )
        return [r.memory for r in results]

    async def recall_with_scores(
        self,
        query: str,
        **kwargs,
    ) -> List[RecallResult]:
        """Recall with score details."""
        return self._recaller.search(query=query, **kwargs)

    def confirm(self, memory_id: str, correct: bool = True) -> Optional[float]:
        """Verify or reject a memory."""
        result = self._quality.verify(memory_id, correct)
        if result is not None:
            memory = self._memories.get(memory_id)
            if memory:
                self._store.save(memory)
        return result

    async def forget(self, memory_id: str) -> bool:
        """Explicitly delete a memory."""
        memory = self._memories.pop(memory_id, None)
        if memory:
            self._store.delete(memory)
            return True
        return False

    async def sleep(self) -> Dict[str, int]:
        """Consolidate memories (like human sleep)."""
        consolidator = MemoryConsolidator(self._store, self._memories, self._config)
        stats = consolidator.consolidate()
        # Bonus XP
        if stats["promoted"] > 0:
            # Caller handles XP — we return stats
            pass
        return stats

    def promote(self, memory_id: str) -> bool:
        """Manually promote a memory to a higher tier."""
        memory = self._memories.get(memory_id)
        if not memory:
            return False
        tier_order = [MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.LONG_TERM]
        current_idx = tier_order.index(memory.tier)
        if current_idx < len(tier_order) - 1:
            new_tier = tier_order[current_idx + 1]
            self._store.move_tier(memory, new_tier)
            return True
        return False

    def demote(self, memory_id: str) -> bool:
        """Manually demote a memory to a lower tier."""
        memory = self._memories.get(memory_id)
        if not memory:
            return False
        tier_order = [MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.LONG_TERM]
        current_idx = tier_order.index(memory.tier)
        if current_idx > 0:
            new_tier = tier_order[current_idx - 1]
            self._store.move_tier(memory, new_tier)
            return True
        return False

    def get_candidates(self) -> List[Memory]:
        """Get unverified candidate memories."""
        return self._quality.get_candidates()

    def get_conflicts(self, content: str, type: MemoryType, tags=None) -> List[ConflictResult]:
        """Check for conflicts before adding a memory."""
        return self._quality.check_conflicts(content, type, tags)

    def count(self) -> int:
        return len(self._memories)

    def stats(self) -> Dict[str, Any]:
        by_tier = {t.value: 0 for t in MemoryTier}
        by_type = {t.value: 0 for t in MemoryType}
        candidates = 0

        for m in self._memories.values():
            by_tier[m.tier.value] += 1
            by_type[m.type.value] += 1
            if m.is_candidate():
                candidates += 1

        return {
            "total": len(self._memories),
            "by_tier": by_tier,
            "by_type": by_type,
            "candidates": candidates,
            "verified": len(self._memories) - candidates,
            "agent_id": self.agent_id,
        }

    def export(
        self,
        filepath: Optional[str] = None,
        agent_name: str = "",
        agent_role: str = "",
        include_tiers: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        include_candidates: bool = False,
    ) -> str:
        """Export memories to AMP format."""
        content = export_memories(
            self._memories,
            agent_name=agent_name,
            agent_role=agent_role,
            include_tiers=include_tiers,
            min_confidence=min_confidence,
            include_candidates=include_candidates,
        )
        if filepath:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info(f"Exported to {filepath}")
        return content

    def import_from(
        self,
        filepath: str,
        mode: str = "candidate",
    ) -> int:
        """Import memories from an .amp file."""
        memories = load_amp_file(filepath, mode=mode)
        for memory in memories:
            if memory.id not in self._memories:
                self._memories[memory.id] = memory
                self._store.save(memory)
            elif mode == "replace":
                self._memories[memory.id] = memory
                self._store.save(memory)
        return len(memories)


class Agent:
    """
    AMP Agent — An AI agent with identity, memory, and growth.

    Simplified v2.0: zero external dependencies.

    Example:
        agent = Agent(name="Ali", role="project_manager")

        # Store memories
        await agent.remember("User prefers Chinese", type=MemoryType.SEMANTIC)

        # Recall
        memories = await agent.recall("user preferences")

        # Task execution with automatic memory recording
        await agent.act({"description": "Plan project"})

        # Export/Import
        agent.memory.export("ali_memory.amp")
    """

    def __init__(
        self,
        name: str,
        role: str,
        storage_dir: Optional[str] = None,
        language: str = "zh",
    ):
        self._storage_dir = Path(storage_dir) if storage_dir else Path.home() / ".amp" / "agents"

        # Load or create identity
        self.identity = self._load_or_create_identity(name, role, language)

        # Initialize memory system
        self.memory = AgentMemory(
            agent_id=self.identity.agent_id,
            storage_dir=str(self._storage_dir),
        )

        logger.info(f"Agent '{name}' ready (level={self.identity.level}, memories={self.memory.count()})")

    def _load_or_create_identity(self, name: str, role: str, language: str) -> AgentIdentity:
        # Search existing agent directories by name
        if self._storage_dir.exists():
            for agent_dir in self._storage_dir.iterdir():
                if agent_dir.is_dir():
                    identity_file = agent_dir / "identity.json"
                    if identity_file.exists():
                        try:
                            data = json.loads(identity_file.read_text(encoding="utf-8"))
                            if data.get("name", "").lower() == name.lower() and data.get("role", "").lower() == role.lower():
                                identity = AgentIdentity.from_dict(data)
                                # Update storage to use found agent's directory
                                logger.info(f"Loaded existing agent: {name} (id={identity.agent_id})")
                                return identity
                        except Exception:
                            pass

        identity = AgentIdentity(name=name, role=role, language=language)

        # Save identity to agent-specific directory
        temp_store = MemoryStore(identity.agent_id, str(self._storage_dir))
        temp_store.save_identity(identity.to_dict())

        logger.info(f"Created new agent: {name} (id={identity.agent_id})")
        return identity

    def _save_identity(self) -> None:
        store = MemoryStore(self.identity.agent_id, str(self._storage_dir))
        store.save_identity(self.identity.to_dict())

    async def remember(self, content: str, **kwargs) -> Memory:
        """Store a new memory."""
        return await self.memory.remember(content, **kwargs)

    async def recall(self, query: str, **kwargs) -> List[Memory]:
        """Recall relevant memories."""
        return await self.memory.recall(query, **kwargs)

    async def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with automatic memory recording."""
        description = task.get("description", "")

        # Record task as episodic memory
        await self.memory.remember(
            content=f"Task: {description}",
            type=MemoryType.EPISODIC,
            importance=task.get("importance", 5),
            tags=task.get("tags", []),
        )

        try:
            result = await self._execute_task(task)

            if result.get("status") == "completed":
                self.identity.tasks_completed += 1
                self.identity.gain_xp(10)
                # Record success as procedural memory
                await self.memory.remember(
                    content=f"Successfully completed: {description}",
                    type=MemoryType.PROCEDURAL,
                    importance=6,
                    emotion="positive",
                    tags=task.get("tags", []),
                )
            elif result.get("status") == "failed":
                self.identity.tasks_failed += 1
                self.identity.gain_xp(3)
                # Record failure as emotional memory
                await self.memory.remember(
                    content=f"Failed: {description} — {result.get('error', 'unknown')}",
                    type=MemoryType.EMOTIONAL,
                    importance=8,
                    emotion="negative",
                    tags=task.get("tags", []),
                )

            self._save_identity()
            return result

        except Exception as e:
            self.identity.tasks_failed += 1
            self.identity.gain_xp(3)
            self._save_identity()

            await self.memory.remember(
                content=f"Failed: {description} — Error: {e}",
                type=MemoryType.EMOTIONAL,
                importance=8,
                emotion="negative",
            )

            return {"status": "failed", "error": str(e)}

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task (can be overridden by subclasses)."""
        return {"status": "completed", "description": task.get("description", "")}

    async def confirm_memory(self, memory_id: str, correct: bool = True) -> Optional[float]:
        """Verify or reject a memory."""
        return self.memory.confirm(memory_id, correct)

    async def forget(self, memory_id: str) -> bool:
        """Delete a memory."""
        return await self.memory.forget(memory_id)

    async def sleep(self) -> Dict[str, int]:
        """Consolidate memories."""
        stats = await self.memory.sleep()
        if stats["promoted"] > 0:
            self.identity.gain_xp(stats["promoted"] * 2)
            self._save_identity()
        return stats

    async def learn_from(
        self,
        other_agent: "Agent",
        topic: Optional[str] = None,
        limit: int = 20,
    ) -> int:
        """Learn from another agent's experiences."""
        if topic:
            memories = await other_agent.memory.recall(topic, limit=limit)
        else:
            memories = sorted(
                other_agent.memory._memories.values(),
                key=lambda m: m.accessed_count,
                reverse=True,
            )[:limit]

        count = 0
        for memory in memories:
            await self.memory.remember(
                content=memory.content,
                type=memory.type,
                importance=memory.importance,
                context=memory.context,
                tags=memory.tags,
                emotion=memory.emotion,
                source_agent=other_agent.identity.agent_id,
                source_type="external",
            )
            count += 1

        if count > 0:
            self.identity.gain_xp(count * 5)
            self._save_identity()
            logger.info(f"Learned {count} memories from '{other_agent.identity.name}'")

        return count

    async def export_knowledge(
        self,
        topic: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> str:
        """Export knowledge as AMP format string."""
        return self.memory.export(
            min_confidence=min_confidence,
            include_candidates=True,
        )

    async def import_knowledge(self, amp_data: str, mode: str = "candidate") -> int:
        """Import knowledge from AMP format."""
        from amp.export.json_export import import_memories
        memories = import_memories(amp_data, mode=mode)
        for memory in memories:
            if memory.id not in self.memory._memories:
                self.memory._memories[memory.id] = memory
                self.memory._store.save(memory)
        return len(memories)

    def status(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "memory_stats": self.memory.stats(),
        }

    def __repr__(self):
        return (
            f"Agent(name={self.identity.name!r}, role={self.identity.role!r}, "
            f"level={self.identity.level}, memories={self.memory.count()})"
        )
