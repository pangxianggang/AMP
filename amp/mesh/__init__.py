"""
AMP Agent Mesh — Multi-agent collaboration and knowledge sharing.

v2.0: Knowledge export/import with quality guarantees.
"""

from __future__ import annotations

import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from amp.agent import Agent

logger = logging.getLogger(__name__)


class AgentMesh:
    """
    Agent Mesh Network for multi-agent collaboration.

    Features:
    - Register and discover agents
    - Coordinate team tasks
    - Share knowledge with quality guarantees

    Example:
        mesh = AgentMesh()
        await mesh.register(researcher)
        await mesh.register(writer)

        # Share knowledge
        await mesh.share_knowledge(researcher, [writer], topic="AI")
    """

    def __init__(self):
        self._agents: Dict[str, "Agent"] = {}

    async def register(self, agent: "Agent") -> bool:
        agent_id = agent.identity.agent_id
        if agent_id in self._agents:
            logger.warning(f"Agent {agent.identity.name} already registered")
            return False
        self._agents[agent_id] = agent
        logger.info(f"Registered: {agent.identity.name} ({agent.identity.role})")
        return True

    async def unregister(self, agent_id: str) -> bool:
        if agent_id not in self._agents:
            return False
        agent = self._agents.pop(agent_id)
        logger.info(f"Unregistered: {agent.identity.name}")
        return True

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": a.identity.agent_id,
                "name": a.identity.name,
                "role": a.identity.role,
                "level": a.identity.level,
            }
            for a in self._agents.values()
        ]

    async def team_task(
        self,
        task: Dict[str, Any],
        agents: Optional[List["Agent"]] = None,
    ) -> Dict[str, Any]:
        """Coordinate a team task across multiple agents."""
        if agents is None:
            agents = list(self._agents.values())

        if not agents:
            return {"status": "failed", "error": "No agents available"}

        description = task.get("description", "Team task")

        # All agents record the task
        for agent in agents:
            await agent.memory.remember(
                content=f"Team task: {description}",
                type="episodic",
                importance=task.get("importance", 7),
                tags=task.get("tags", []),
            )

        # Execute subtasks
        results = []
        for i, agent in enumerate(agents):
            subtask = {
                **task,
                "description": f"{description} (part {i+1}/{len(agents)})",
            }
            result = await agent.act(subtask)
            results.append(result)

        # Record success for all
        all_ok = all(r.get("status") == "completed" for r in results)
        if all_ok:
            for agent in agents:
                agent.identity.tasks_completed += 1
                agent.identity.gain_xp(15)
                agent._save_identity()

        return {
            "status": "completed" if all_ok else "partial",
            "team_size": len(agents),
            "subtask_results": results,
        }

    async def share_knowledge(
        self,
        from_agent: "Agent",
        to_agents: List["Agent"],
        topic: Optional[str] = None,
        mode: str = "candidate",
    ) -> Dict[str, int]:
        """
        Share knowledge between agents.

        Args:
            from_agent: Source agent
            to_agents: Target agents
            topic: Optional topic filter
            mode: "candidate" (unverified) or "merge" (trusted)
        """
        # Export from source
        knowledge = await from_agent.export_knowledge(topic=topic)

        results = {}
        for to_agent in to_agents:
            count = await to_agent.import_knowledge(knowledge, mode=mode)
            results[to_agent.identity.name] = count

        logger.info(
            f"Shared knowledge: {from_agent.identity.name} -> "
            f"{[a.identity.name for a in to_agents]}"
        )
        return results

    def status(self) -> Dict[str, Any]:
        return {
            "registered_agents": len(self._agents),
            "agents": self.list_agents(),
        }

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"AgentMesh(agents={len(self._agents)})"
