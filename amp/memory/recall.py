"""
AMP Memory Recall — Search, filter, and rank memories.

v1.0: Keyword-based search with Chinese/English support.
v2.0 plan: Optional vector-based semantic search.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from amp.memory.types import (
    Memory, MemoryType, MemoryTier,
    ARCHIVE_THRESHOLD, DELETE_THRESHOLD,
)

logger = logging.getLogger(__name__)

# Chinese stop words
CN_STOPWORDS = {
    '的', '了', '在', '是', '和', '与', '及', '等', '一个', '这个',
    '那个', '我', '你', '他', '她', '它', '我们', '你们', '他们',
    '也', '都', '就', '要', '会', '能', '可以', '还', '有', '没',
    '不', '很', '把', '被', '让', '给', '到', '从', '对', '为',
}

# English stop words
EN_STOPWORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'about', 'like',
    'through', 'after', 'over', 'between', 'out', 'against', 'during',
    'without', 'before', 'under', 'around', 'among', 'and', 'but', 'or',
    'not', 'no', 'so', 'if', 'than', 'too', 'very', 'just', 'that',
}


def tokenize(text: str) -> List[str]:
    """
    Simple tokenizer supporting Chinese and English.

    For Chinese: splits by common delimiters and punctuation.
    For English: splits by whitespace.
    Filters stop words.
    """
    # Normalize
    text = text.lower().strip()

    # Split by whitespace and punctuation
    # For Chinese, characters are kept as-is (no word boundary)
    tokens: List[str] = []

    # Find Chinese character sequences
    cn_pattern = re.compile(r'[\u4e00-\u9fff]+')
    en_pattern = re.compile(r'[a-z0-9]+')

    # Extract Chinese segments and English segments separately
    cn_matches = cn_pattern.findall(text)
    en_matches = en_pattern.findall(text)

    # Chinese: use bigrams for segments >= 2 chars
    for segment in cn_matches:
        if len(segment) >= 4:
            # Generate bigrams and trigrams
            for i in range(len(segment) - 1):
                tokens.append(segment[i:i+2])
            for i in range(len(segment) - 2):
                tokens.append(segment[i:i+3])
        elif len(segment) >= 2:
            tokens.append(segment)
        # Single Chinese characters are usually not meaningful enough

    # English: split by whitespace
    for word in en_matches:
        if word not in EN_STOPWORDS and len(word) > 1:
            tokens.append(word)

    return tokens


class RecallResult:
    """A single recall result with score breakdown."""

    def __init__(self, memory: Memory, score: float, match_type: str = "keyword"):
        self.memory = memory
        self.score = score
        self.match_type = match_type  # keyword / tag / context

    def __repr__(self):
        return f"RecallResult(score={self.score:.3f}, type={self.match_type}, content={self.memory.content[:30]!r})"


class MemoryRecaller:
    """
    Memory recall engine with scoring and ranking.

    Scoring formula:
        score = strength * relevance * recency_boost

    Where:
        - strength: computed memory strength (from forgetting.py)
        - relevance: keyword/content/tag match score (0.0-1.0)
        - recency_boost: slight boost for recently accessed memories
    """

    def __init__(self, memories: Dict[str, Memory]):
        self._memories = memories

    def search(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        tier: Optional[MemoryTier] = None,
        min_confidence: float = 0.0,
        min_strength: float = 0.0,
        tags: Optional[List[str]] = None,
        include_candidates: bool = True,
        limit: int = 10,
    ) -> List[RecallResult]:
        """
        Search memories by query.

        Args:
            query: Search query text
            type: Filter by memory type
            tier: Filter by memory tier
            min_confidence: Minimum confidence threshold
            min_strength: Minimum strength threshold
            tags: Filter by tags (any match)
            include_candidates: Include unverified memories
            limit: Maximum results

        Returns:
            List of RecallResult, sorted by score descending
        """
        query_tokens = set(tokenize(query))
        if not query_tokens:
            # Single word or no valid tokens — use original query
            query_tokens = {query.lower()}

        results: List[RecallResult] = []

        for mem_id, memory in self._memories.items():
            # Filter: tier
            if tier and memory.tier != tier:
                continue

            # Filter: type
            if type and memory.type != type:
                continue

            # Filter: confidence
            if not include_candidates and memory.is_candidate():
                continue
            if memory.confidence < min_confidence:
                continue

            # Filter: strength
            if memory.strength < min_strength:
                continue

            # Filter: tags
            if tags and not any(t.lower() in [mt.lower() for mt in memory.tags] for t in tags):
                continue

            # Compute relevance score
            relevance, match_type = self._compute_relevance(
                memory, query, query_tokens
            )

            if relevance <= 0:
                continue

            # Compute recency boost
            recency_boost = self._compute_recency_boost(memory)

            # Final score
            score = memory.strength * relevance * recency_boost

            # Touch memory (update access stats)
            memory.touch()

            results.append(RecallResult(memory, score, match_type))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def _compute_relevance(
        self,
        memory: Memory,
        query: str,
        query_tokens: Set[str],
    ) -> Tuple[float, str]:
        """
        Compute relevance of a memory to the query.

        Returns (relevance_score, match_type).
        """
        query_lower = query.lower()
        scores: List[Tuple[float, str]] = []

        # 1. Content match (weight: 1.0)
        content_lower = memory.content.lower()
        if query_lower in content_lower:
            # Exact substring match
            scores.append((1.0, "keyword"))

        # Token-based match
        content_tokens = set(tokenize(memory.content))
        if content_tokens & query_tokens:
            overlap = len(content_tokens & query_tokens)
            total = len(query_tokens)
            score = overlap / total if total > 0 else 0
            scores.append((score * 0.9, "keyword"))

        # 2. Tag match (weight: 0.8)
        for tag in memory.tags:
            tag_lower = tag.lower()
            if query_lower in tag_lower:
                scores.append((0.8, "tag"))
                break
            # Token match on tags
            tag_tokens = set(tokenize(tag))
            if tag_tokens & query_tokens:
                scores.append((0.7, "tag"))
                break

        # 3. Context match (weight: 0.6)
        if memory.context:
            context_lower = memory.context.lower()
            if query_lower in context_lower:
                scores.append((0.6, "context"))
            context_tokens = set(tokenize(memory.context))
            if context_tokens & query_tokens:
                overlap = len(context_tokens & query_tokens)
                total = len(query_tokens)
                score = overlap / total if total > 0 else 0
                scores.append((score * 0.5, "context"))

        # 4. Type name match (weight: 0.4)
        if query_lower in memory.type.value:
            scores.append((0.4, "keyword"))

        if not scores:
            return (0.0, "")

        # Return best match
        best = max(scores, key=lambda x: x[0])
        return best

    def _compute_recency_boost(self, memory: Memory) -> float:
        """
        Slight boost for recently accessed memories.

        Returns a multiplier between 1.0 and 1.2.
        """
        if not memory.last_accessed:
            return 1.0

        try:
            last = datetime.fromisoformat(memory.last_accessed)
            hours_since = (datetime.now() - last).total_seconds() / 3600

            if hours_since < 1:
                return 1.2  # Accessed within last hour
            elif hours_since < 6:
                return 1.1  # Accessed within last 6 hours
            elif hours_since < 24:
                return 1.05  # Accessed within last day
            elif hours_since < 168:  # 7 days
                return 1.02
            else:
                return 1.0
        except (ValueError, TypeError):
            return 1.0
