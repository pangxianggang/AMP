"""
AMP Memory Types — Core data structures for the memory system.

Memory Types (inspired by cognitive science):
- Episodic: What happened (events and experiences)
- Semantic: What I know (facts and concepts)
- Procedural: How to do things (skills and methods)
- Emotional: What worked and what didn't (valenced experiences)

Memory Tiers:
- Working: Current task context (fast, small, auto-clear)
- ShortTerm: Current session (medium, auto-archive)
- LongTerm: Persistent storage (slow, large, permanent)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Four types of memory inspired by cognitive science."""
    EPISODIC = "episodic"      # What happened
    SEMANTIC = "semantic"      # What I know
    PROCEDURAL = "procedural"  # How to do things
    EMOTIONAL = "emotional"    # What worked / failed


class MemoryTier(str, Enum):
    """Memory storage tiers with different lifecycles."""
    WORKING = "working"            # Current task, auto-clear after 1 hour
    SHORT_TERM = "short_term"      # Current session, auto-archive after 7 days
    LONG_TERM = "long_term"        # Persistent, never auto-delete


# Confidence thresholds
CANDIDATE_CONFIDENCE = 0.50     # New memories start here
VERIFIED_THRESHOLD = 0.80       # Above this = verified
HIGH_CONFIDENCE = 0.90          # Above this = high confidence
ARCHIVE_THRESHOLD = 0.20        # Below this = candidate for archiving
DELETE_THRESHOLD = 0.10         # Below this = candidate for deletion

# Tier thresholds
WORKING_CAPACITY = 10
WORKING_PROMOTE_MIN_IMPORTANCE = 6
SHORT_TERM_CAPACITY = 100
SHORT_TERM_PROMOTE_MIN_IMPORTANCE = 8
SHORT_TERM_PROMOTE_MIN_ACCESSES = 5

# Tier TTL
WORKING_TTL_HOURS = 1
SHORT_TERM_TTL_DAYS = 7


@dataclass
class Memory:
    """
    A single memory unit with quality assurance.

    Attributes:
        id: Unique memory identifier
        type: Memory type (episodic/semantic/procedural/emotional)
        tier: Memory tier (working/short_term/long_term)
        content: Memory content
        created_at: When the memory was formed
        updated_at: Last modification time
        importance: Importance level (1-10)
        confidence: Quality confidence (0.0-1.0), starts at 0.50
        context: Surrounding context
        tags: Categorization tags
        emotion: Emotional valence (positive/negative/neutral)
        source_agent: If learned from another agent
        source_type: Where this memory came from (self/external/import)
        connections: IDs of related memories
        accessed_count: How often recalled
        last_accessed: Last recall time
        strength: Computed memory strength (0.0-1.0)
        verify_count: Times confirmed correct
        reject_count: Times confirmed incorrect
    """

    id: str
    type: MemoryType
    content: str
    created_at: str
    updated_at: str = ""
    tier: MemoryTier = MemoryTier.LONG_TERM
    importance: int = 5
    confidence: float = CANDIDATE_CONFIDENCE
    context: str = ""
    tags: List[str] = field(default_factory=list)
    emotion: str = "neutral"
    source_agent: Optional[str] = None
    source_type: str = "self"  # self / external / import
    connections: List[str] = field(default_factory=list)
    accessed_count: int = 0
    last_accessed: Optional[str] = None
    strength: float = 1.0
    verify_count: int = 0
    reject_count: int = 0

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = asdict(self)
        data["type"] = self.type.value
        data["tier"] = self.tier.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Deserialize from dictionary."""
        if "type" in data:
            data["type"] = MemoryType(data["type"])
        if "tier" in data:
            data["tier"] = MemoryTier(data["tier"])
        return cls(**data)

    def is_candidate(self) -> bool:
        """Whether this memory is still a candidate (unverified)."""
        return self.confidence < VERIFIED_THRESHOLD

    def is_verified(self) -> bool:
        """Whether this memory has been verified through usage."""
        return self.confidence >= VERIFIED_THRESHOLD

    def is_high_confidence(self) -> bool:
        """Whether this memory has high confidence."""
        return self.confidence >= HIGH_CONFIDENCE

    def confirm(self, correct: bool = True) -> float:
        """
        Confirm or reject this memory, updating confidence.

        Confidence progression for correct confirmations:
        0.50 → 0.64 → 0.80 → 0.92

        For incorrect rejections, confidence decreases.

        Args:
            correct: True if the memory was correctly used

        Returns:
            New confidence value
        """
        self.updated_at = datetime.now().isoformat()

        if correct:
            self.verify_count += 1
            # Confidence progression curve
            progressions = [0.50, 0.64, 0.80, 0.92, 0.96, 0.98]
            if self.confidence < progressions[-1]:
                # Find next level
                for i, level in enumerate(progressions):
                    if self.confidence < level:
                        self.confidence = level
                        break
            else:
                # Already high, small boost
                self.confidence = min(self.confidence + 0.01, 1.0)
        else:
            self.reject_count += 1
            # Confidence decrease based on rejection count
            self.confidence = max(
                self.confidence - (0.15 * (1 + self.reject_count * 0.1)),
                0.0
            )

        return self.confidence

    def touch(self) -> None:
        """Record that this memory was accessed."""
        self.accessed_count += 1
        self.last_accessed = datetime.now().isoformat()
