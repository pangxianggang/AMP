"""
AMP Memory Forgetting — Cognitive forgetting based on Ebbinghaus curve.

v2.0 improvements over v1.0:
- Configurable weights for importance, access frequency, recency, context
- Time-aware decay (hours, not just days)
- Soft forgetting (archive) vs hard forgetting (delete)
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Dict, List, Optional

from amp.memory.types import (
    Memory, MemoryTier,
    ARCHIVE_THRESHOLD, DELETE_THRESHOLD,
    WORKING_TTL_HOURS, SHORT_TERM_TTL_DAYS,
)

logger = logging.getLogger(__name__)


class ForgettingConfig:
    """Configurable forgetting curve parameters."""

    def __init__(
        self,
        importance_weight: float = 0.4,
        access_weight: float = 0.25,
        recency_weight: float = 0.25,
        confidence_weight: float = 0.1,
        time_decay_half_life_hours: float = 336,  # 14 days
    ):
        self.importance_weight = importance_weight
        self.access_weight = access_weight
        self.recency_weight = recency_weight
        self.confidence_weight = confidence_weight
        self.time_decay_half_life = time_decay_half_life_hours


DEFAULT_CONFIG = ForgettingConfig()


def compute_strength(
    memory: Memory,
    config: Optional[ForgettingConfig] = None,
) -> float:
    """
    Compute memory strength using improved Ebbinghaus forgetting curve.

    Formula:
        strength = (
            importance_w * (importance / 10) +
            access_w * min(accessed * 0.08, 0.5) +
            recency_w * recency_score +
            confidence_w * confidence
        ) * time_decay

    Where:
        time_decay = 0.5 ^ (age_hours / half_life)

    Args:
        memory: The memory to evaluate
        config: Forgetting configuration (uses default if None)

    Returns:
        Strength value between 0.0 and 1.0
    """
    if config is None:
        config = DEFAULT_CONFIG

    now = datetime.now()

    # Time decay (exponential, configurable half-life)
    try:
        created = datetime.fromisoformat(memory.created_at)
        age_hours = max((now - created).total_seconds() / 3600, 0)
    except (ValueError, TypeError):
        age_hours = 0

    time_decay = math.pow(0.5, age_hours / config.time_decay_half_life)

    # Importance component (0.0 - 1.0)
    importance_score = memory.importance / 10.0

    # Access frequency component (0.0 - 0.5, capped)
    access_score = min(memory.accessed_count * 0.08, 0.5)

    # Recency component (0.0 - 1.0)
    recency_score = 0.0
    if memory.last_accessed:
        try:
            last = datetime.fromisoformat(memory.last_accessed)
            hours_since = (now - last).total_seconds() / 3600
            recency_score = math.exp(-hours_since / 168)  # 7-day e-fold
        except (ValueError, TypeError):
            pass

    # Confidence component (already 0.0 - 1.0)
    confidence_score = memory.confidence

    # Weighted sum
    base_strength = (
        config.importance_weight * importance_score +
        config.access_weight * access_score +
        config.recency_weight * recency_score +
        config.confidence_weight * confidence_score
    )

    # Apply time decay
    strength = base_strength * time_decay

    # Clamp to [0, 1]
    strength = max(0.0, min(strength, 1.0))

    return strength


def compute_all_strengths(
    memories: Dict[str, Memory],
    config: Optional[ForgettingConfig] = None,
) -> Dict[str, float]:
    """Compute strength for all memories."""
    strengths = {}
    for mem_id, memory in memories.items():
        memory.strength = compute_strength(memory, config)
        strengths[mem_id] = memory.strength
    return strengths


class MemoryConsolidator:
    """
    Memory consolidation — like human sleep.

    Operations:
    1. Recompute all memory strengths
    2. Auto-promote high-importance memories between tiers
    3. Auto-demote weak memories
    4. Archive (soft forget) very weak memories
    5. Delete (hard forget) dead memories
    6. Clean up expired working memory
    """

    def __init__(
        self,
        store,  # MemoryStore instance
        memories: Dict[str, Memory],
        config: Optional[ForgettingConfig] = None,
    ):
        self.store = store
        self.memories = memories
        self.config = config or DEFAULT_CONFIG

    def consolidate(self) -> Dict[str, int]:
        """
        Run full consolidation cycle.

        Returns:
            Statistics dict with counts of each operation.
        """
        stats = {
            "strengths_recomputed": 0,
            "promoted": 0,
            "demoted": 0,
            "archived": 0,
            "deleted": 0,
            "working_expired": 0,
        }

        now = datetime.now()

        # Step 1: Recompute strengths
        for mem_id, memory in self.memories.items():
            memory.strength = compute_strength(memory, self.config)
            stats["strengths_recomputed"] += 1

        # Step 2: Process each memory
        to_archive: List[str] = []
        to_delete: List[str] = []

        for mem_id, memory in list(self.memories.items()):
            # Working memory TTL check
            if memory.tier == MemoryTier.WORKING:
                try:
                    created = datetime.fromisoformat(memory.created_at)
                    age_hours = (now - created).total_seconds() / 3600
                    if age_hours > WORKING_TTL_HOURS:
                        # Expired working memory
                        if memory.importance >= 6:
                            self._promote(memory, MemoryTier.SHORT_TERM)
                            stats["promoted"] += 1
                        else:
                            to_archive.append(mem_id)
                            stats["working_expired"] += 1
                        continue
                except (ValueError, TypeError):
                    pass

            # Short-term memory TTL check
            if memory.tier == MemoryTier.SHORT_TERM:
                try:
                    created = datetime.fromisoformat(memory.created_at)
                    age_hours = (now - created).total_seconds() / 3600
                    if age_hours > SHORT_TERM_TTL_DAYS * 24:
                        # Expired short-term memory
                        if memory.importance >= 8 or memory.accessed_count >= 5:
                            self._promote(memory, MemoryTier.LONG_TERM)
                            stats["promoted"] += 1
                        else:
                            to_archive.append(mem_id)
                        continue
                except (ValueError, TypeError):
                    pass

            # Strength-based promotion/demotion
            if memory.strength >= 0.8:
                # Strong memory — promote if not already long-term
                if memory.tier == MemoryTier.WORKING:
                    self._promote(memory, MemoryTier.SHORT_TERM)
                    stats["promoted"] += 1
                elif memory.tier == MemoryTier.SHORT_TERM:
                    if memory.importance >= 8 or memory.accessed_count >= 5:
                        self._promote(memory, MemoryTier.LONG_TERM)
                        stats["promoted"] += 1
            elif memory.strength < ARCHIVE_THRESHOLD:
                # Weak memory — demote or archive
                if memory.tier == MemoryTier.LONG_TERM:
                    if memory.confidence < DELETE_THRESHOLD and memory.accessed_count == 0:
                        to_delete.append(mem_id)
                    else:
                        to_archive.append(mem_id)
                elif memory.tier == MemoryTier.SHORT_TERM:
                    self._demote(memory, MemoryTier.WORKING)
                    stats["demoted"] += 1

        # Step 3: Execute deletions
        for mem_id in to_delete:
            memory = self.memories.pop(mem_id, None)
            if memory:
                self.store.delete(memory)
                stats["deleted"] += 1

        # Step 4: Execute archives (move to working, they'll expire naturally)
        for mem_id in to_archive:
            memory = self.memories.get(mem_id)
            if memory:
                if memory.tier != MemoryTier.WORKING:
                    self._demote(memory, MemoryTier.WORKING)
                    stats["demoted"] += 1
                else:
                    # Already in working, just let it expire
                    pass

        # Step 5: Save all modified memories
        for memory in self.memories.values():
            self.store.save(memory)

        logger.info(
            f"Consolidation: promoted={stats['promoted']}, "
            f"demoted={stats['demoted']}, archived={len(to_archive)}, "
            f"deleted={stats['deleted']}, working_expired={stats['working_expired']}"
        )

        return stats

    def _promote(self, memory: Memory, new_tier: MemoryTier) -> None:
        """Promote a memory to a higher tier."""
        old_tier = memory.tier
        self.store.move_tier(memory, new_tier)
        logger.debug(f"Promoted: {memory.id[:8]} {old_tier.value} → {new_tier.value}")

    def _demote(self, memory: Memory, new_tier: MemoryTier) -> None:
        """Demote a memory to a lower tier."""
        old_tier = memory.tier
        self.store.move_tier(memory, new_tier)
        logger.debug(f"Demoted: {memory.id[:8]} {old_tier.value} → {new_tier.value}")
