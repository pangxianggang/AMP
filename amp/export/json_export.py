"""
AMP Export — Memory portability in standard format.

AMP files (.amp) are the standard interchange format for AI agent memories.
They can be:
- Exported from any AMP-compatible system
- Imported into any other AMP-compatible system
- Inspected and edited by humans (JSON-based)
- Version-controlled alongside code

Format:
    {
        "protocol": "amp/2.0",
        "exported_at": "2026-03-18T15:00:00Z",
        "agent": { "name": "...", "role": "...", ... },
        "memories": [
            {
                "id": "abc123",
                "type": "semantic",
                "content": "...",
                ...
            }
        ]
    }
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from amp.memory.types import Memory, MemoryType, MemoryTier

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "amp/2.0"


def export_memories(
    memories: Dict[str, Memory],
    agent_name: str = "",
    agent_role: str = "",
    include_tiers: Optional[List[str]] = None,
    min_confidence: float = 0.0,
    min_importance: int = 0,
    include_candidates: bool = False,
) -> str:
    """
    Export memories to AMP standard format (.amp JSON).

    Args:
        memories: Dict of memory_id -> Memory
        agent_name: Agent name for the export
        agent_role: Agent role for the export
        include_tiers: Only include memories in these tiers (None = all)
        min_confidence: Minimum confidence filter
        min_importance: Minimum importance filter
        include_candidates: Include unverified memories

    Returns:
        JSON string in AMP format
    """
    filtered = []

    for mem_id, memory in memories.items():
        # Filter by tier
        if include_tiers and memory.tier.value not in include_tiers:
            continue

        # Filter by confidence
        if not include_candidates and memory.is_candidate():
            continue
        if memory.confidence < min_confidence:
            continue

        # Filter by importance
        if memory.importance < min_importance:
            continue

        filtered.append(memory.to_dict())

    export_data = {
        "protocol": PROTOCOL_VERSION,
        "exported_at": datetime.now().isoformat(),
        "agent": {
            "name": agent_name,
            "role": agent_role,
        },
        "memory_count": len(filtered),
        "memories": filtered,
    }

    return json.dumps(export_data, indent=2, ensure_ascii=False)


def import_memories(
    amp_data: str,
    mode: str = "candidate",
    existing_memories: Optional[Dict[str, Memory]] = None,
) -> List[Memory]:
    """
    Import memories from AMP standard format.

    Args:
        amp_data: JSON string in AMP format
        mode: Import mode
            - "candidate": Import as unverified (confidence starts at 0.50)
            - "merge": Import with original confidence
            - "replace": Replace existing memories with same ID
        existing_memories: Existing memories dict for conflict checking

    Returns:
        List of imported Memory objects
    """
    data = json.loads(amp_data)

    # Validate protocol version
    protocol = data.get("protocol", "")
    if not protocol.startswith("amp/"):
        raise ValueError(f"Not an AMP format file (protocol: {protocol})")

    imported: List[Memory] = []

    for mem_data in data.get("memories", []):
        memory = Memory.from_dict(mem_data)

        # Set import metadata
        memory.source_type = "import"

        if mode == "candidate":
            # Reset confidence for untrusted import
            memory.confidence = 0.50
            memory.verify_count = 0
            memory.reject_count = 0
        elif mode == "merge":
            # Keep original confidence
            pass
        elif mode == "replace":
            # Check for ID conflicts with existing
            if existing_memories and memory.id in existing_memories:
                logger.info(f"Replacing existing memory: {memory.id[:8]}")

        imported.append(memory)

    logger.info(f"Imported {len(imported)} memories (mode={mode}, protocol={protocol})")
    return imported


def save_amp_file(
    filepath: str,
    memories: Dict[str, Memory],
    agent_name: str = "",
    agent_role: str = "",
    **kwargs,
) -> None:
    """Export memories and save to a .amp file."""
    content = export_memories(
        memories, agent_name=agent_name, agent_role=agent_role, **kwargs
    )
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info(f"Exported to {filepath} ({len(content)} chars)")


def load_amp_file(filepath: str, mode: str = "candidate") -> List[Memory]:
    """Load memories from a .amp file."""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")
    return import_memories(content, mode=mode)
