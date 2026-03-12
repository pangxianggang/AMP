# AMP Protocol: Agent Identity Specification

**Version**: 1.0.0
**Status**: Stable

---

## Overview

Every AMP agent has a persistent identity that survives across sessions, platforms, and time. This specification defines the structure and behavior of agent identities.

## Identity Structure

### Required Fields

| Field | Type | Description |
|---|---|---|
| `agent_id` | string | Unique identifier (auto-generated) |
| `name` | string | Human-readable name |
| `role` | string | Agent's primary role |
| `version` | string | Agent version (semver) |
| `created_at` | datetime | Creation timestamp |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `personality` | object | Behavioral traits |
| `capabilities` | string[] | List of skills |
| `language` | string | Preferred language |
| `reporting_to` | string | Parent agent or human |

### Computed Fields

| Field | Type | Description |
|---|---|---|
| `tasks_completed` | integer | Successful task count |
| `tasks_failed` | integer | Failed task count |
| `success_rate` | float | Completion rate (0.0-1.0) |
| `experience_points` | integer | Accumulated XP |
| `level` | integer | Agent level (XP / 100 + 1) |

## Agent ID Generation

```
agent_id = SHA256(name + ":" + role + ":" + created_at)[:16]
```

The agent_id is deterministic and permanent. Once created, it never changes.

## Leveling System

Agents gain experience through completing tasks:

| Action | XP Gained |
|---|---|
| Task completed successfully | +10 |
| Task failed (lesson learned) | +3 |
| Learned from another agent | +5 per memory |
| Memory consolidation | +2 |
| Team task completed | +15 |

Level = (XP / 100) + 1

## Identity Persistence

Agent identities MUST be persisted to durable storage. When an agent is instantiated with the same name and role, it SHOULD recover its previous identity including all statistics and history.

## Example

```json
{
  "agent_id": "a1b2c3d4e5f67890",
  "name": "Ali",
  "role": "project_manager",
  "version": "1.0.0",
  "created_at": "2026-03-12T10:30:00Z",
  "personality": {
    "style": "thorough and methodical",
    "language": "zh"
  },
  "capabilities": ["research", "summarization", "analysis"],
  "tasks_completed": 47,
  "tasks_failed": 3,
  "success_rate": 0.94,
  "experience_points": 520,
  "level": 6
}
```
