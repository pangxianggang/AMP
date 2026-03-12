# AMP Protocol: Memory Specification

**Version**: 1.0.0
**Status**: Stable

---

## Overview

AMP's memory system is modeled after human cognitive science. Agents maintain multiple types of memory with natural strengthening and decay mechanisms.

## Memory Types

### Episodic Memory
**What happened.**

Records of events, interactions, and experiences.

```json
{
  "type": "episodic",
  "content": "Helped user debug a Python async issue",
  "context": "User was confused about await syntax",
  "timestamp": "2026-03-12T14:30:00Z"
}
```

### Semantic Memory
**What I know.**

Facts, concepts, and general knowledge acquired through experience.

```json
{
  "type": "semantic",
  "content": "User prefers TypeScript over JavaScript",
  "source": "observed_pattern",
  "confidence": 0.9
}
```

### Procedural Memory
**How to do things.**

Skills, methods, and procedures learned through practice.

```json
{
  "type": "procedural",
  "content": "To deploy this project: 1) Run tests, 2) Build Docker image, 3) Push to registry, 4) Update k8s manifest",
  "success_count": 12,
  "last_used": "2026-03-14T09:00:00Z"
}
```

### Emotional Memory
**What worked and what didn't.**

Valenced experiences that guide future behavior.

```json
{
  "type": "emotional",
  "content": "Using recursive approach for tree traversal caused stack overflow on large inputs",
  "emotion": "negative",
  "lesson": "Use iterative approach with explicit stack for large trees",
  "importance": 9
}
```

## Memory Structure

### Required Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique memory ID |
| `type` | enum | episodic/semantic/procedural/emotional |
| `content` | string | Memory content |
| `created_at` | datetime | When the memory was formed |
| `importance` | integer | 1-10 scale |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `context` | string | Surrounding context |
| `tags` | string[] | Categorization tags |
| `emotion` | string | positive/negative/neutral |
| `source_agent` | string | If learned from another agent |
| `connections` | string[] | IDs of related memories |
| `accessed_count` | integer | How often recalled |
| `last_accessed` | datetime | Last recall time |

## Memory Strength

Memory strength follows the Ebbinghaus forgetting curve:

```
strength = (importance / 10) + min(accessed_count * 0.1, 0.5) × time_decay

where:
  time_decay = 1.0 / (1.0 + age_hours / 24.0)
```

Memories with strength below 0.1 are candidates for forgetting.

## Memory Operations

### Remember
Store a new memory. The system automatically:
1. Assesses importance
2. Classifies memory type
3. Builds connections to existing memories
4. Stores in appropriate tier (short-term vs long-term)

### Recall
Retrieve relevant memories. The system:
1. Searches by semantic similarity
2. Filters by type and recency
3. Ranks by composite score (relevance × strength × recency)
4. Updates access counts (strengthening recalled memories)

### Consolidate
Periodic memory maintenance (like human sleep):
1. Promote important short-term memories to long-term
2. Decay old, unaccessed memories
3. Merge similar memories
4. Discover patterns across memories

### Forget
Explicitly remove a memory. Used for:
- Removing outdated information
- Privacy compliance
- Correcting mistakes

## Storage Tiers

```
Working Memory (current task)
  ↓ (importance >= 4)
Short-Term Memory (current session)
  ↓ (importance >= 6, or consolidation)
Long-Term Memory (persistent storage)
```

## Implementation Notes

### v1.0 (Current)
- Keyword-based search
- Local file storage
- Basic forgetting curve

### v2.0 (Planned)
- Vector-based semantic search
- Optional cloud storage
- Advanced pattern discovery
