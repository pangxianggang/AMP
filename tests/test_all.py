"""
AMP v2.0 — Comprehensive test suite.
Tests core memory, agent, mesh, export, and quality features.
"""

import sys
import os
import asyncio
import shutil

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amp import Agent, MemoryType, MemoryTier
from amp.memory.types import Memory, CANDIDATE_CONFIDENCE, VERIFIED_THRESHOLD
from amp.memory.forgetting import compute_strength, ForgettingConfig
from amp.memory.quality import QualityManager
from amp.memory.recall import tokenize
from amp.mesh import AgentMesh
from amp.export.json_export import export_memories, import_memories, PROTOCOL_VERSION


TEST_DIR = os.path.join(os.path.dirname(__file__), "_test_data")


def cleanup():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} {detail}")


# ============================================================
async def test_all():
    global passed, failed
    cleanup()

    print("=== 1. Memory Types & Data Model ===")

    m = Memory(
        id="test001", type=MemoryType.SEMANTIC, content="test content",
        created_at="2026-03-18T12:00:00", importance=8
    )
    test("Memory creation", m.content == "test content")
    test("Default confidence", m.confidence == CANDIDATE_CONFIDENCE)
    test("Is candidate", m.is_candidate())
    test("Not verified", not m.is_verified())
    test("Tier default", m.tier == MemoryTier.LONG_TERM)

    # Confirm progression
    m.confirm(True)  # 0.64
    test("1st confirm", m.confidence == 0.64, f"got {m.confidence}")
    m.confirm(True)  # 0.80
    test("2nd confirm", m.confidence == 0.80, f"got {m.confidence}")
    m.confirm(True)  # 0.92
    test("3rd confirm → verified", m.confidence == 0.92, f"got {m.confidence}")
    test("Now verified", m.is_verified())

    # Reject
    m.confirm(False)
    test("Reject decreases confidence", m.confidence < 0.92, f"got {m.confidence}")

    # Serialization
    d = m.to_dict()
    m2 = Memory.from_dict(d)
    test("Round-trip serialize", m2.id == m.id and m2.content == m.content)

    print("\n=== 2. Tokenizer (Chinese + English) ===")

    tokens_cn = tokenize("用户喜欢用Python写代码")
    test("Chinese tokens", len(tokens_cn) > 0, f"got {tokens_cn}")
    test("Contains python", "python" in tokens_cn, f"got {tokens_cn}")

    tokens_en = tokenize("user prefers python programming")
    test("English tokens", "python" in tokens_en, f"got {tokens_en}")

    tokens_mixed = tokenize("Python FastAPI 开发部署")
    test("Mixed tokens", len(tokens_mixed) > 0, f"got {tokens_mixed}")

    print("\n=== 3. Forgetting Curve ===")

    # High importance, recently accessed = high strength
    m_strong = Memory(
        id="strong", type=MemoryType.SEMANTIC, content="important info",
        created_at="2026-03-18T12:00:00", importance=10, accessed_count=10
    )
    s = compute_strength(m_strong)
    test("Strong memory strength", s > 0.5, f"got {s:.3f}")

    # Low importance, old, never accessed = low strength
    m_weak = Memory(
        id="weak", type=MemoryType.EPISODIC, content="trivial old thing",
        created_at="2025-01-01T00:00:00", importance=1, accessed_count=0
    )
    w = compute_strength(m_weak)
    test("Weak memory strength", w < 0.3, f"got {w:.3f}")

    print("\n=== 4. Quality Manager ===")

    memories = {}
    qm = QualityManager(memories)

    # Add a semantic memory
    m1 = Memory(
        id="m1", type=MemoryType.SEMANTIC, content="User prefers Python 3.12",
        created_at="2026-03-18T12:00:00", importance=8
    )
    memories["m1"] = m1

    # Check conflict with similar content
    conflicts = qm.check_conflicts("User prefers Python 3.12", MemoryType.SEMANTIC)
    test("Exact duplicate detected", len(conflicts) > 0, f"got {len(conflicts)}")
    if conflicts:
        test("Conflict type is duplicate", conflicts[0].conflict_type == "duplicate")

    # No conflict with different content
    no_conflicts = qm.check_conflicts("User prefers Java", MemoryType.SEMANTIC)
    test("No conflict for different content", len(no_conflicts) == 0, f"got {len(no_conflicts)}")

    print("\n=== 5. Agent Core ===")

    agent = Agent(name="test_v2", role="tester", storage_dir=TEST_DIR)
    test("Agent created", agent.identity.name == "test_v2")
    test("Agent ID present", len(agent.identity.agent_id) == 16)
    test("Initial level", agent.identity.level == 1)
    test("Initial XP", agent.identity.experience_points == 0)

    # Remember
    mem1 = await agent.remember("user likes chinese", type=MemoryType.SEMANTIC, importance=8)
    test("Remember returns Memory", mem1.id is not None)
    test("Memory is candidate", mem1.is_candidate())
    test("Tier assigned", mem1.tier == MemoryTier.LONG_TERM, f"got {mem1.tier}")

    # Working memory for low importance
    mem2 = await agent.remember("quick note", type=MemoryType.EPISODIC, importance=2)
    test("Low importance → Working tier", mem2.tier == MemoryTier.WORKING, f"got {mem2.tier}")

    # Recall
    results = await agent.recall("chinese")
    test("Recall finds match", len(results) > 0)
    if results:
        test("Recall content", "chinese" in results[0].content.lower())

    no_results = await agent.recall("quantum physics xyz")
    test("No recall for non-existent", len(no_results) == 0)

    # Count
    test("Memory count", agent.memory.count() >= 2)

    # Stats
    stats = agent.memory.stats()
    test("Stats total", stats["total"] >= 2)
    test("Stats candidates", stats["candidates"] >= 2)

    # Confirm memory
    conf = await agent.confirm_memory(mem1.id, correct=True)
    test("Confirm increases confidence", conf > CANDIDATE_CONFIDENCE, f"got {conf}")

    # Forget
    forgot = await agent.forget(mem2.id)
    test("Forget returns True", forgot is True)
    test("Count decreased", agent.memory.count() == 1)

    # Persistence
    agent2 = Agent(name="test_v2", role="tester", storage_dir=TEST_DIR)
    test("Persistence: agent2 has memories", agent2.memory.count() == 1)

    print("\n=== 6. Task Execution & XP ===")

    await agent.act({"description": "test task"})
    test("After 1 task: XP=10", agent.identity.experience_points == 10)
    test("After 1 task: completed=1", agent.identity.tasks_completed == 1)
    test("After 1 task: level=1", agent.identity.level == 1)

    for i in range(9):
        await agent.act({"description": f"task {i}"})
    test("After 10 tasks: level=2", agent.identity.level == 2, f"got {agent.identity.level}")
    test("After 10 tasks: XP=100", agent.identity.experience_points == 100)

    print("\n=== 7. Memory Tiers ===")

    agent3 = Agent(name="tier_test", role="test", storage_dir=TEST_DIR)
    await agent3.remember("working note", importance=2)     # Working
    await agent3.remember("short term info", importance=5)   # Short-term
    await agent3.remember("important fact", importance=9)    # Long-term

    stats3 = agent3.memory.stats()
    test("Working tier count", stats3["by_tier"]["working"] == 1, f"got {stats3['by_tier']}")
    test("Short-term count", stats3["by_tier"]["short_term"] == 1, f"got {stats3['by_tier']}")
    test("Long-term count", stats3["by_tier"]["long_term"] == 1, f"got {stats3['by_tier']}")

    # Manual promote
    agent3.memory.promote(next(m.id for m in agent3.memory._memories.values() if m.tier == MemoryTier.WORKING))
    stats3b = agent3.memory.stats()
    test("Promote works", stats3b["by_tier"]["short_term"] == 2, f"got {stats3b['by_tier']}")

    print("\n=== 8. Export / Import ===")

    amp_data = agent3.memory.export(include_candidates=True)
    test("Export returns string", isinstance(amp_data, str))
    test("Export has protocol", "amp/2.0" in amp_data)

    # Import
    imported = import_memories(amp_data, mode="candidate")
    test("Import returns memories", len(imported) > 0)
    test("Imported as candidates", all(m.confidence == 0.50 for m in imported))

    imported_merge = import_memories(amp_data, mode="merge")
    test("Merge keeps confidence", all(m.confidence >= 0.50 for m in imported_merge))

    # File export
    amp_file = os.path.join(TEST_DIR, "export_test.amp")
    agent3.memory.export(filepath=amp_file)
    test("File export exists", os.path.exists(amp_file))

    # File import
    agent_import = Agent(name="import_target", role="test", storage_dir=TEST_DIR)
    await agent_import.remember("some memory", importance=7)
    amp_file2 = os.path.join(TEST_DIR, "export2.amp")
    agent_import.memory.export(filepath=amp_file2, include_candidates=True)
    # Modify: load and count
    from amp.export.json_export import load_amp_file
    loaded_memories = load_amp_file(amp_file2, mode="candidate")
    test("File import works", len(loaded_memories) > 0, f"got {len(loaded_memories)}")

    print("\n=== 9. Agent Mesh ===")

    mesh = AgentMesh()
    researcher = Agent(name="mesh_researcher", role="researcher", storage_dir=TEST_DIR)
    writer = Agent(name="mesh_writer", role="writer", storage_dir=TEST_DIR)

    await mesh.register(researcher)
    await mesh.register(writer)
    test("Mesh has 2 agents", len(mesh) == 2)

    await researcher.remember("AI market growing 40% YoY", type=MemoryType.SEMANTIC, importance=8)
    await researcher.remember("Python is the top language", type=MemoryType.SEMANTIC, importance=7)

    # Share knowledge (candidate mode)
    results_map = await mesh.share_knowledge(researcher, [writer], topic="AI market", mode="candidate")
    test("Share knowledge returns results", "mesh_writer" in results_map)
    # Note: export_knowledge filters by min_confidence=0.8, candidate memories won't be exported
    # This is by design — only verified knowledge is shared
    # So we test with merge mode (which keeps original confidence)
    results_map2 = await mesh.share_knowledge(researcher, [writer], topic="Python", mode="merge")
    test("Writer learned something (merge)", results_map2["mesh_writer"] > 0, f"got {results_map2}")

    # Verify imported memories are candidates
    writer_candidates = writer.memory.get_candidates()
    has_ai_market = any("AI market" in m.content for m in writer_candidates)
    test("Imported memories are candidates", has_ai_market)

    # Learn directly
    count = await writer.learn_from(researcher, topic="Python")
    test("Direct learn_from works", count > 0)

    # Team task
    team_result = await mesh.team_task({"description": "research project", "importance": 5})
    test("Team task completed", team_result.get("status") in ("completed", "partial"))

    print("\n=== 10. Consolidation (Sleep) ===")

    agent4 = Agent(name="sleep_test", role="test", storage_dir=TEST_DIR)
    await agent4.remember("keep this", importance=9)
    await agent4.remember("temporary note", importance=1)
    stats_sleep = await agent4.sleep()
    test("Consolidation runs", "strengths_recomputed" in stats_sleep)

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if failed == 0:
        print("ALL TESTS PASSED!")
    else:
        print(f"WARNING: {failed} tests failed!")

    cleanup()
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_all())
    sys.exit(0 if success else 1)
