"""
AMP Agent Mesh — Multi-agent collaboration and communication.

Agents don't work in isolation. The Mesh enables:
- Task delegation based on expertise
- Knowledge sharing across agents
- Team coordination for complex tasks
- Collective learning from shared experiences

Example:
    mesh = AgentMesh()
    await mesh.register(researcher)
    await mesh.register(writer)
    result = await mesh.team_task(...)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from amp.agent import Agent

from amp.memory import MemoryType

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages between agents."""
    TASK = "task"
    RESPONSE = "response"
    QUERY = "query"
    ANNOUNCEMENT = "announcement"
    LEARNING = "learning"


@dataclass
class Message:
    """
    Message between agents.

    Attributes:
        id: Unique message ID
        type: Message type
        from_agent: Sender agent ID
        to_agent: Recipient agent ID (or None for broadcast)
        content: Message content
        timestamp: When sent
        metadata: Additional metadata
        in_reply_to: Parent message ID (if response)
    """
    id: str
    type: MessageType
    from_agent: str
    to_agent: Optional[str]
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    in_reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "id": self.id,
            "type": self.type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "in_reply_to": self.in_reply_to,
        }
        return data


class AgentMesh:
    """
    Agent Mesh Network — Enables multi-agent collaboration.

    Features:
    - Register and discover agents
    - Send messages between agents
    - Coordinate team tasks
    - Share knowledge across agents

    Example:
        mesh = AgentMesh()
        await mesh.register(alice)
        await mesh.register(bob)
        await mesh.send_task(alice, {"description": "Research AI"})
    """

    def __init__(self):
        self._agents: Dict[str, "Agent"] = {}
        self._message_queue: List[Message] = []
        self._message_history: List[Message] = []

    async def register(self, agent: "Agent") -> bool:
        """
        Register an agent in the mesh.

        Args:
            agent: Agent to register

        Returns:
            True if registered, False if already exists
        """
        agent_id = agent.identity.agent_id
        if agent_id in self._agents:
            logger.warning(f"Agent {agent.identity.name} already registered")
            return False

        self._agents[agent_id] = agent
        logger.info(f"Registered agent: {agent.identity.name} ({agent.identity.role})")
        return True

    async def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent from the mesh.

        Args:
            agent_id: Agent ID to remove

        Returns:
            True if unregistered, False if not found
        """
        if agent_id not in self._agents:
            return False

        agent = self._agents.pop(agent_id)
        logger.info(f"Unregistered agent: {agent.identity.name}")
        return True

    def get_agent(self, agent_id: str) -> Optional["Agent"]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "id": a.identity.agent_id,
                "name": a.identity.name,
                "role": a.identity.role,
                "level": a.identity.level,
                "capabilities": a.identity.capabilities,
            }
            for a in self._agents.values()
        ]

    async def send_message(self, message: Message) -> None:
        """
        Send a message to an agent.

        Args:
            message: Message to send
        """
        self._message_queue.append(message)
        self._message_history.append(message)
        logger.debug(
            f"📨 Message {message.type.value}: "
            f"{message.from_agent} → {message.to_agent}"
        )

    async def send_task(
        self,
        agent: "Agent",
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send a task to an agent.

        Args:
            agent: Target agent
            task: Task description

        Returns:
            Task result
        """
        message = Message(
            id=f"msg_{datetime.now().timestamp()}",
            type=MessageType.TASK,
            from_agent="mesh",
            to_agent=agent.identity.agent_id,
            content=task,
        )
        await self.send_message(message)
        return await agent.act(task)

    async def team_task(
        self,
        task: Dict[str, Any],
        agents: Optional[List["Agent"]] = None,
        coordinator: Optional["Agent"] = None,
    ) -> Dict[str, Any]:
        """
        Coordinate a team task across multiple agents.

        Args:
            task: Task description
            agents: List of agents to involve
            coordinator: Coordinator agent (or self)

        Returns:
            Combined team result
        """
        if agents is None:
            agents = list(self._agents.values())

        if not agents:
            return {"status": "failed", "error": "No agents available"}

        logger.info(f"👥 Starting team task with {len(agents)} agents")

        # Store task as episodic memory for all agents
        task_description = task.get("description", "Team task")
        for agent in agents:
            await agent.memory.remember(
                content=f"Team task: {task_description}",
                type=MemoryType.EPISODIC,
                importance=task.get("importance", 7),
                tags=task.get("tags", []),
            )

        # If coordinator specified, let them handle it
        if coordinator:
            result = await coordinator.act({
                **task,
                "team": [a.identity.name for a in agents],
            })
        else:
            # Parallel execution (simplified — each agent does part)
            results = []
            for i, agent in enumerate(agents):
                subtask = {
                    **task,
                    "description": f"{task_description} (part {i+1}/{len(agents)})",
                    "team_member": i + 1,
                }
                result = await agent.act(subtask)
                results.append(result)

            # Combine results
            result = {
                "status": "completed",
                "team_size": len(agents),
                "subtask_results": results,
            }

        # Record success for all agents
        if result.get("status") == "completed":
            for agent in agents:
                agent.identity.tasks_completed += 1
                agent.identity.gain_experience(15)  # +15 XP for team task

        logger.info(f"Team task completed: {task_description[:50]}...")
        return result

    async def share_knowledge(
        self,
        from_agent: "Agent",
        to_agents: List["Agent"],
        topic: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """
        Share knowledge from one agent to others.

        Args:
            from_agent: Source agent
            to_agents: Target agents
            topic: Optional topic filter
            tags: Optional tags filter

        Returns:
            Number of memories shared to each agent
        """
        results = {}

        for to_agent in to_agents:
            count = await from_agent.learn_from(
                to_agent,
                topic=topic,
                tags=tags,
            )
            results[to_agent.identity.name] = count

            # Send learning message
            if count > 0:
                message = Message(
                    id=f"msg_{datetime.now().timestamp()}",
                    type=MessageType.LEARNING,
                    from_agent=from_agent.identity.agent_id,
                    to_agent=to_agent.identity.agent_id,
                    content={
                        "topic": topic,
                        "memories_shared": count,
                    },
                )
                await self.send_message(message)

        return results

    async def broadcast(
        self,
        announcement: Dict[str, Any],
        exclude: Optional[List[str]] = None,
    ) -> int:
        """
        Broadcast an announcement to all agents.

        Args:
            announcement: Announcement content
            exclude: Agent IDs to exclude

        Returns:
            Number of agents notified
        """
        exclude = exclude or []
        count = 0

        for agent_id, agent in self._agents.items():
            if agent_id in exclude:
                continue

            message = Message(
                id=f"msg_{datetime.now().timestamp()}",
                type=MessageType.ANNOUNCEMENT,
                from_agent="mesh",
                to_agent=agent_id,
                content=announcement,
            )
            await self.send_message(message)
            count += 1

        logger.info(f"📢 Broadcast to {count} agents")
        return count

    def status(self) -> Dict[str, Any]:
        """Get mesh status."""
        return {
            "registered_agents": len(self._agents),
            "agents": self.list_agents(),
            "message_queue_size": len(self._message_queue),
            "total_messages": len(self._message_history),
        }

    def __len__(self) -> int:
        """Number of registered agents."""
        return len(self._agents)

    def __repr__(self) -> str:
        return f"AgentMesh(agents={len(self._agents)})"
