"""
AMP — Agent Memory Protocol v2.0

The open protocol for AI agents that remember, learn, and grow.

Core design principles:
- Zero-dependency core (pure Python stdlib)
- Memory portability (.amp standard format)
- Memory quality assurance (confidence + candidate mechanism)
- Cognitive forgetting (Ebbinghaus curve)
- Memory tiers (Working → Short-term → Long-term)

Usage:
    import amp

    agent = amp.Agent(name="Ali", role="project_manager")
    await agent.remember("User prefers Chinese", type=amp.MemoryType.SEMANTIC)
    memories = await agent.recall("user preferences")

Every AI deserves to remember.
"""

__version__ = "2.0.0"
__author__ = "Pang Xianggang & AMP Contributors"
__license__ = "MIT"

from amp.agent import Agent
from amp.memory.types import Memory, MemoryType, MemoryTier

__all__ = [
    "Agent",
    "Memory",
    "MemoryType",
    "MemoryTier",
]
