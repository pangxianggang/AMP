"""
AMP Memory Quality — Confidence management and conflict detection.

Quality assurance features:
- Candidate mechanism (new memories need verification)
- Conflict detection (contradictory memories)
- Confidence decay for rejected memories
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from amp.memory.types import Memory, MemoryType, VERIFIED_THRESHOLD

logger = logging.getLogger(__name__)


class ConflictResult:
    """Result of a conflict detection check."""

    def __init__(
        self,
        existing: Memory,
        new_content: str,
        conflict_type: str,
        description: str,
    ):
        self.existing = existing
        self.new_content = new_content
        self.conflict_type = conflict_type  # "contradiction" / "supersede" / "duplicate"
        self.description = description

    def __repr__(self):
        return f"ConflictResult({self.conflict_type}: {self.description[:50]})"


class QualityManager:
    """
    Memory quality assurance manager.

    Responsibilities:
    - Detect conflicts when adding new memories
    - Verify/reject memories
    - Track confidence changes
    """

    def __init__(self, memories: Dict[str, Memory]):
        self._memories = memories

    def check_conflicts(
        self,
        content: str,
        memory_type: MemoryType,
        tags: Optional[List[str]] = None,
    ) -> List[ConflictResult]:
        """
        Check if a new memory conflicts with existing memories.

        Conflict types:
        - duplicate: Very similar content already exists
        - supersede: Same topic, new info is more recent/confident
        - contradiction: Same topic, but contradictory information

        Args:
            content: New memory content
            memory_type: Type of the new memory
            tags: Tags of the new memory

        Returns:
            List of ConflictResult (empty if no conflicts)
        """
        conflicts: List[ConflictResult] = []

        content_lower = content.lower().strip()

        for mem_id, existing in self._memories.items():
            # Skip memories of very different types
            # (semantic conflicts with semantic, etc.)
            if existing.type != memory_type:
                continue

            existing_lower = existing.content.lower().strip()

            # 1. Exact duplicate check
            if existing_lower == content_lower:
                conflicts.append(ConflictResult(
                    existing=existing,
                    new_content=content,
                    conflict_type="duplicate",
                    description=f"Exact duplicate of existing memory: {existing.id[:8]}"
                ))
                continue

            # 2. High similarity check (substring overlap)
            if (content_lower in existing_lower or existing_lower in content_lower):
                # If existing is more confident, it's a potential duplicate
                if existing.confidence > 0.8:
                    conflicts.append(ConflictResult(
                        existing=existing,
                        new_content=content,
                        conflict_type="duplicate",
                        description=f"Similar to verified memory: {existing.id[:8]}"
                    ))
                    continue

            # 3. Same-tag conflict check
            if tags and existing.tags:
                common_tags = set(t.lower() for t in tags) & set(t.lower() for t in existing.tags)
                if len(common_tags) >= 2:
                    # Check for potential contradiction
                    # Simple heuristic: if key terms differ
                    conflicts.append(ConflictResult(
                        existing=existing,
                        new_content=content,
                        conflict_type="supersede",
                        description=f"Same topic (tags: {', '.join(common_tags)}), may supersede: {existing.id[:8]}"
                    ))

        return conflicts

    def verify(self, memory_id: str, correct: bool = True) -> Optional[float]:
        """
        Verify or reject a memory, updating its confidence.

        Args:
            memory_id: ID of the memory to verify
            correct: True if the memory was correctly used

        Returns:
            New confidence value, or None if memory not found
        """
        memory = self._memories.get(memory_id)
        if not memory:
            return None

        new_confidence = memory.confirm(correct)

        if correct and new_confidence >= VERIFIED_THRESHOLD:
            logger.info(
                f"Memory {memory_id[:8]} verified (confidence={new_confidence:.2f}): "
                f"{memory.content[:40]}..."
            )
        elif not correct:
            logger.warning(
                f"Memory {memory_id[:8]} rejected (confidence={new_confidence:.2f}): "
                f"{memory.content[:40]}..."
            )

        return new_confidence

    def get_candidates(self) -> List[Memory]:
        """Get all unverified candidate memories."""
        return [
            m for m in self._memories.values()
            if m.is_candidate()
        ]

    def get_low_confidence(self, threshold: float = 0.3) -> List[Memory]:
        """Get memories with low confidence that may need review."""
        return [
            m for m in self._memories.values()
            if m.confidence < threshold and m.accessed_count > 0
        ]
