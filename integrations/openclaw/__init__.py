"""
AMP + OpenClaw Integration

Integrates AMP agents with OpenClaw's subagent system.
Allows OpenClaw to spawn AMP agents with persistent memory.

Usage:
    from amp.integrations.openclaw import OpenClawAMPBridge

    bridge = OpenClawAMPBridge()
    agent = await bridge.create_agent("Ali", "project_manager")
    result = await agent.act({"description": "Coordinate the project"})
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from amp.agent import Agent
from amp.memory import MemoryType, AgentMemory
from amp.mesh import AgentMesh

logger = logging.getLogger(__name__)


class OpenClawAMPBridge:
    """
    Bridge between AMP and OpenClaw.

    Features:
    - Create AMP agents from OpenClaw
    - Sync memories between AMP and Memory Bank
    - Execute tasks via OpenClaw subagents
    - Store results in AMP memory
    """

    def __init__(
        self,
        openclaw_gateway: str = "http://localhost:18789",
        memory_bank: str = "http://localhost:8100",
        amp_storage: Optional[str] = None,
    ):
        self.openclaw_gateway = openclaw_gateway
        self.memory_bank = memory_bank
        self.amp_storage = amp_storage

        # AMP Mesh for multi-agent coordination
        self.mesh = AgentMesh()

        logger.info(f"🔗 OpenClaw-AMP Bridge initialized")
        logger.info(f"   OpenClaw Gateway: {openclaw_gateway}")
        logger.info(f"   Memory Bank: {memory_bank}")

    async def create_agent(
        self,
        name: str,
        role: str,
        capabilities: Optional[List[str]] = None,
        language: str = "zh",
    ) -> Agent:
        """
        Create an AMP agent for use with OpenClaw.

        Args:
            name: Agent name
            role: Agent role
            capabilities: List of capabilities
            language: Preferred language

        Returns:
            Created Agent
        """
        agent = Agent(
            name=name,
            role=role,
            storage_dir=self.amp_storage,
            language=language,
            capabilities=capabilities or [],
        )

        # Register in mesh
        await self.mesh.register(agent)

        logger.info(f"✅ Created AMP agent: {name} ({role})")
        return agent

    async def spawn_subagent(
        self,
        name: str,
        role: str,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Spawn an OpenClaw subagent and create AMP memory.

        Args:
            name: Subagent name
            role: Subagent role
            task: Task to execute

        Returns:
            Task result
        """
        # Create AMP agent first
        agent = await self.create_agent(name, role)

        # Store task as episodic memory
        await agent.memory.remember(
            content=f"Spawned as subagent for: {task.get('description', 'task')}",
            type=MemoryType.EPISODIC,
            importance=7,
            tags=["openclaw", "subagent"],
        )

        # Execute task
        result = await agent.act(task)

        # Store result
        if result.get("status") == "completed":
            await agent.memory.remember(
                content=f"Successfully completed subagent task: {task.get('description', '')}",
                type=MemoryType.PROCEDURAL,
                importance=6,
                emotion="positive",
                tags=["openclaw", "success"],
            )
        else:
            await agent.memory.remember(
                content=f"Failed subagent task: {task.get('description', '')} — {result.get('error', '')}",
                type=MemoryType.EMOTIONAL,
                importance=8,
                emotion="negative",
                tags=["openclaw", "failure"],
            )

        return result

    async def sync_to_memory_bank(
        self,
        agent: Agent,
        memory_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Sync AMP agent memories to Memory Bank.

        Args:
            agent: Agent to sync
            memory_id: Specific memory to sync (or all)
            tags: Filter by tags

        Returns:
            Number of memories synced
        """
        synced = 0

        if memory_id:
            memories = [agent.memory._memories.get(memory_id)]
            memories = [m for m in memories if m]
        elif tags:
            memories = [
                m for m in agent.memory._memories.values()
                if any(t in m.tags for t in tags)
            ]
        else:
            memories = list(agent.memory._memories.values())

        for memory in memories:
            try:
                # Sync to Memory Bank
                response = requests.post(
                    f"{self.memory_bank}/memory/write",
                    json={
                        "content": memory.content,
                        "memory_type": memory.type.value,
                        "agent_id": f"amp-{agent.identity.agent_id}",
                        "scope": "agent",
                        "tags": memory.tags,
                        "metadata": {
                            "importance": memory.importance,
                            "emotion": memory.emotion,
                            "source": "amp",
                        },
                    },
                    timeout=10,
                )

                if response.status_code == 200:
                    synced += 1
                    logger.debug(f"✅ Synced memory to Memory Bank: {memory.content[:50]}...")
                else:
                    logger.warning(f"Failed to sync memory: {response.status_code}")

            except Exception as e:
                logger.warning(f"Error syncing memory: {e}")

        logger.info(f"🔄 Synced {synced} memories to Memory Bank")
        return synced

    async def sync_from_memory_bank(
        self,
        agent: Agent,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> int:
        """
        Load memories from Memory Bank into AMP agent.

        Args:
            agent: Agent to load memories into
            query: Search query
            tags: Filter by tags
            limit: Maximum memories to load

        Returns:
            Number of memories loaded
        """
        try:
            # Search Memory Bank
            search_payload = {"query": query or "", "limit": limit}
            if tags:
                search_payload["tags"] = tags

            response = requests.post(
                f"{self.memory_bank}/memory/search",
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
                # Skip if already exists
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

    async def team_coordinate(
        self,
        task: str,
        domain: str,
        preferred_role: str,
        agent_limit: int = 3,
    ) -> Dict[str, Any]:
        """
        Coordinate a team of AMP agents for OpenClaw task.

        This mimics OpenClaw's agent routing but uses AMP agents.

        Args:
            task: Task description
            domain: Task domain
            preferred_role: Preferred agent role
            agent_limit: Maximum agents to involve

        Returns:
            Execution result
        """
        # Create coordinator agent
        coordinator = await self.create_agent(
            name=f"coordinator-{domain}",
            role=preferred_role,
            capabilities=["coordination", "planning"],
        )

        # Store task context
        await coordinator.memory.remember(
            content=f"Coordinating {domain} task: {task}",
            type=MemoryType.EPISODIC,
            importance=8,
            tags=["coordination", domain],
        )

        # Create team members based on domain
        team_roles = {
            "incident-response": ["analyst", "responder", "communicator"],
            "development": ["developer", "reviewer", "tester"],
            "research": ["researcher", "analyst", "writer"],
            "general": ["assistant", "specialist", "reviewer"],
        }

        roles = team_roles.get(domain, ["assistant"])
        team = [coordinator]

        for i, role in enumerate(roles[:agent_limit - 1]):
            member = await self.create_agent(
                name=f"team-{role}-{i}",
                role=role,
            )
            team.append(member)

        # Execute team task
        result = await self.mesh.team_task(
            task={
                "description": task,
                "domain": domain,
                "importance": 8,
                "tags": ["team", domain],
            },
            agents=team,
            coordinator=coordinator,
        )

        # Sync all team memories to Memory Bank
        for member in team:
            await self.sync_to_memory_bank(member, tags=[domain])

        return result

    def status(self) -> Dict[str, Any]:
        """Get bridge status."""
        return {
            "openclaw_gateway": self.openclaw_gateway,
            "memory_bank": self.memory_bank,
            "mesh_status": self.mesh.status(),
        }
