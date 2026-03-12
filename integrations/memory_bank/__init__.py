"""
AMP + Memory Bank Integration

Deep integration between AMP and Agent Memory Bank.
Provides bidirectional sync and unified memory access.

Usage:
    from amp.integrations.memory_bank import MemoryBankIntegration

    mb = MemoryBankIntegration()
    await mb.sync_agent_to_bank(agent)
    await mb.load_agent_from_bank(agent)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import requests

from amp.agent import Agent
from amp.memory import MemoryType, AgentMemory

logger = logging.getLogger(__name__)


class MemoryBankIntegration:
    """
    Integration between AMP and Agent Memory Bank.

    Features:
    - Bidirectional memory sync
    - Unified search across both systems
    - Experience sharing
    - Conversation history storage
    """

    def __init__(
        self,
        memory_bank_url: str = "http://localhost:8100",
        amp_storage: Optional[str] = None,
    ):
        self.memory_bank_url = memory_bank_url
        self.amp_storage = amp_storage
        self._health_cache = False

        logger.info(f"🔗 Memory Bank Integration initialized")
        logger.info(f"   Memory Bank URL: {memory_bank_url}")

    def check_health(self) -> bool:
        """Check if Memory Bank is available."""
        try:
            response = requests.get(f"{self.memory_bank_url}/health", timeout=5)
            self._health_cache = response.status_code == 200
        except Exception:
            self._health_cache = False

        if not self._health_cache:
            logger.warning("Memory Bank is not available")
        return self._health_cache

    async def save_conversation(
        self,
        agent: Agent,
        messages: List[Dict[str, str]],
        summary: str,
        scope: str = "session",
        session_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Save a conversation to Memory Bank.

        Args:
            agent: Agent involved in conversation
            messages: List of {role, content} messages
            summary: Conversation summary
            scope: user/session/workspace
            session_id: Session identifier
            workspace_id: Workspace identifier
            tags: Optional tags

        Returns:
            True if saved successfully
        """
        if not self.check_health():
            logger.warning("Cannot save conversation - Memory Bank unavailable")
            return False

        try:
            payload = {
                "agent_id": f"amp-{agent.identity.agent_id}",
                "scope": scope,
                "summary": summary,
                "messages": messages,
                "tags": tags or ["conversation", "amp"],
            }

            if session_id:
                payload["session_id"] = session_id
            if workspace_id:
                payload["workspace_id"] = workspace_id

            response = requests.post(
                f"{self.memory_bank_url}/memory-bank/chat-history",
                json=payload,
                timeout=15,
            )

            if response.status_code == 200:
                # Also store as AMP episodic memory
                await agent.memory.remember(
                    content=f"Conversation: {summary}",
                    type=MemoryType.EPISODIC,
                    importance=7,
                    context="\n".join([m["content"] for m in messages[-3:]]),
                    tags=tags or ["conversation"],
                )

                logger.info(f"✅ Saved conversation to Memory Bank: {summary[:50]}...")
                return True
            else:
                logger.warning(f"Failed to save conversation: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False

    async def sync_agent_to_bank(
        self,
        agent: Agent,
        memory_types: Optional[List[MemoryType]] = None,
        min_importance: int = 4,
    ) -> Dict[str, int]:
        """
        Sync all agent memories to Memory Bank.

        Args:
            agent: Agent to sync
            memory_types: Types to sync (or all)
            min_importance: Minimum importance threshold

        Returns:
            Statistics about synced memories
        """
        if not self.check_health():
            return {"synced": 0, "skipped": 0}

        memory_types = memory_types or list(MemoryType)
        stats = {"synced": 0, "skipped": 0}

        for memory in agent.memory._memories.values():
            # Filter by type and importance
            if memory.type not in memory_types:
                stats["skipped"] += 1
                continue
            if memory.importance < min_importance:
                stats["skipped"] += 1
                continue

            try:
                response = requests.post(
                    f"{self.memory_bank_url}/memory/write",
                    json={
                        "content": memory.content,
                        "memory_type": memory.type.value,
                        "agent_id": f"amp-{agent.identity.agent_id}",
                        "scope": "agent",
                        "tags": memory.tags,
                        "metadata": {
                            "amp_memory_id": memory.id,
                            "importance": memory.importance,
                            "emotion": memory.emotion,
                            "strength": memory.strength,
                        },
                    },
                    timeout=10,
                )

                if response.status_code == 200:
                    stats["synced"] += 1
                else:
                    stats["skipped"] += 1

            except Exception as e:
                logger.debug(f"Failed to sync memory: {e}")
                stats["skipped"] += 1

        logger.info(
            f"🔄 Synced {stats['synced']} memories to Memory Bank "
            f"({stats['skipped']} skipped)"
        )
        return stats

    async def load_agent_from_bank(
        self,
        agent: Agent,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> int:
        """
        Load memories from Memory Bank into agent.

        Args:
            agent: Agent to load memories into
            query: Search query
            tags: Filter by tags
            limit: Maximum memories to load

        Returns:
            Number of memories loaded
        """
        if not self.check_health():
            return 0

        try:
            # Search Memory Bank
            search_payload = {"query": query or "", "limit": limit}
            if tags:
                search_payload["tags"] = tags

            response = requests.post(
                f"{self.memory_bank_url}/memory/search",
                json=search_payload,
                timeout=10,
            )

            if response.status_code != 200:
                logger.warning(f"Memory Bank search failed: {response.status_code}")
                return 0

            memories_data = response.json().get("memories", [])

            # Import into AMP
            loaded = 0
            for mem in memories_data:
                # Skip AMP memories already loaded
                content = mem.get("content", "")
                existing = await agent.memory.recall(content[:50], limit=1)
                if existing and content in existing[0].content:
                    continue

                # Create AMP memory
                await agent.memory.remember(
                    content=content,
                    type=MemoryType(mem.get("memory_type", "episodic")),
                    importance=mem.get("metadata", {}).get("importance", 5),
                    tags=mem.get("tags", []),
                    emotion=mem.get("metadata", {}).get("emotion", "neutral"),
                )
                loaded += 1

            logger.info(f"📥 Loaded {loaded} memories from Memory Bank")
            return loaded

        except Exception as e:
            logger.error(f"Error loading from Memory Bank: {e}")
            return 0

    async def save_experience(
        self,
        agent: Agent,
        topic: str,
        lesson: str,
        experience_type: str = "lesson",
        domain: str = "general",
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Save an experience/lesson to Memory Bank.

        Args:
            agent: Agent that learned the experience
            topic: Experience topic
            lesson: The lesson learned
            experience_type: lesson/trick/pattern
            domain: Domain/field
            tags: Optional tags

        Returns:
            True if saved successfully
        """
        if not self.check_health():
            return False

        try:
            payload = {
                "topic": topic,
                "lesson": lesson,
                "type": experience_type,
                "agent_id": f"amp-{agent.identity.agent_id}",
                "domain": domain,
                "tags": tags or [],
            }

            response = requests.post(
                f"{self.memory_bank_url}/experience/write",
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                # Also store as AMP emotional/procedural memory
                mem_type = MemoryType.EMOTIONAL if experience_type == "lesson" else MemoryType.PROCEDURAL
                await agent.memory.remember(
                    content=f"{topic}: {lesson}",
                    type=mem_type,
                    importance=8,
                    emotion="positive" if experience_type == "trick" else "neutral",
                    tags=tags or ["experience", domain],
                )

                logger.info(f"✅ Saved experience to Memory Bank: {topic}")
                return True
            else:
                logger.warning(f"Failed to save experience: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error saving experience: {e}")
            return False

    async def search_unified(
        self,
        query: str,
        agent: Optional[Agent] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search both AMP and Memory Bank memories.

        Args:
            query: Search query
            agent: Optional agent to search (or search all)
            limit: Maximum results

        Returns:
            Combined search results
        """
        results = []

        # Search AMP agent memories
        if agent:
            amp_results = await agent.memory.recall(query, limit=limit)
            for mem in amp_results:
                results.append({
                    "source": "amp",
                    "agent": agent.identity.name,
                    "memory": mem.to_dict(),
                })

        # Search Memory Bank
        if self.check_health():
            try:
                response = requests.post(
                    f"{self.memory_bank_url}/memory/search",
                    json={"query": query, "limit": limit},
                    timeout=10,
                )

                if response.status_code == 200:
                    mb_memories = response.json().get("memories", [])
                    for mem in mb_memories:
                        results.append({
                            "source": "memory_bank",
                            "memory": mem,
                        })
            except Exception as e:
                logger.debug(f"Memory Bank search failed: {e}")

        # Sort by importance/relevance
        results.sort(
            key=lambda x: x["memory"].get("importance", 5),
            reverse=True
        )

        return results[:limit]

    def status(self) -> Dict[str, Any]:
        """Get integration status."""
        return {
            "memory_bank_url": self.memory_bank_url,
            "health": self.check_health(),
            "amp_storage": self.amp_storage,
        }
