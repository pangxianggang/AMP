"""
AMP Memory Store — Unified storage interface.

Supports local JSON file storage (zero dependencies).
Optional: vector database storage via amp.transport.vector.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from amp.memory.types import Memory, MemoryType, MemoryTier

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Local JSON file-based memory storage.

    Storage layout:
        <storage_dir>/<agent_id>/
            memories/
                working/
                    <id>.json
                short_term/
                    <id>.json
                long_term/
                    <id>.json
            identity.json

    Zero external dependencies — uses only Python stdlib.
    """

    def __init__(self, agent_id: str, storage_dir: str):
        self.agent_id = agent_id
        self.base_dir = Path(storage_dir) / agent_id
        self.memories_dir = self.base_dir / "memories"

        # Ensure directories exist
        for tier in MemoryTier:
            tier_dir = self.memories_dir / tier.value
            tier_dir.mkdir(parents=True, exist_ok=True)

    def save(self, memory: Memory) -> None:
        """Save a single memory to disk."""
        tier_dir = self.memories_dir / memory.tier.value
        tier_dir.mkdir(parents=True, exist_ok=True)
        file_path = tier_dir / f"{memory.id}.json"
        file_path.write_text(
            json.dumps(memory.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def delete(self, memory: Memory) -> None:
        """Delete a memory from disk."""
        file_path = self.memories_dir / memory.tier.value / f"{memory.id}.json"
        if file_path.exists():
            file_path.unlink()

    def move_tier(self, memory: Memory, new_tier: MemoryTier) -> None:
        """Move a memory to a different tier."""
        old_path = self.memories_dir / memory.tier.value / f"{memory.id}.json"
        if old_path.exists():
            old_path.unlink()
        memory.tier = new_tier
        memory.updated_at = datetime.now().isoformat()
        self.save(memory)

    def load_all(self) -> Dict[str, Memory]:
        """Load all memories from disk."""
        memories: Dict[str, Memory] = {}
        for tier in MemoryTier:
            tier_dir = self.memories_dir / tier.value
            if not tier_dir.exists():
                continue
            for mem_file in tier_dir.glob("*.json"):
                try:
                    data = json.loads(mem_file.read_text(encoding="utf-8"))
                    memory = Memory.from_dict(data)
                    memories[memory.id] = memory
                except Exception as e:
                    logger.warning(f"Failed to load {mem_file}: {e}")
        return memories

    def load_tier(self, tier: MemoryTier) -> Dict[str, Memory]:
        """Load memories from a specific tier."""
        memories: Dict[str, Memory] = {}
        tier_dir = self.memories_dir / tier.value
        if not tier_dir.exists():
            return memories
        for mem_file in tier_dir.glob("*.json"):
            try:
                data = json.loads(mem_file.read_text(encoding="utf-8"))
                memory = Memory.from_dict(data)
                memories[memory.id] = memory
            except Exception as e:
                logger.warning(f"Failed to load {mem_file}: {e}")
        return memories

    def save_identity(self, identity_data: dict) -> None:
        """Save agent identity."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        identity_path = self.base_dir / "identity.json"
        identity_path.write_text(
            json.dumps(identity_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def load_identity(self) -> Optional[dict]:
        """Load agent identity."""
        identity_path = self.base_dir / "identity.json"
        if identity_path.exists():
            return json.loads(identity_path.read_text(encoding="utf-8"))
        return None
