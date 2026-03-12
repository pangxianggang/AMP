"""
AMP 7 天价值测试 - Day 3: 多 Agent 协作测试

测试问题：团队是否比个人更强？
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent
from amp.mesh import AgentMesh
from amp.memory import MemoryType

print("=" * 70)
print("🧪 AMP 7 天价值测试 - Day 3")
print("🤝 多 Agent 协作测试")
print("=" * 70)
print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

async def test_collaboration():
    results = {
        "solo_time": 0,
        "team_time": 0,
        "solo_quality": 0,
        "team_quality": 0,
        "knowledge_shared": False,
        "total_score": 0.0,
    }
    
    # ========== 个人模式 ==========
    print("=" * 70)
    print("📖 场景：个人模式 - 独狼完成完整项目")
    print("=" * 70)
    
    solo = Agent(name="独狼", role="fullstack", language="zh")
    print(f"\n✅ 创建个人 Agent: {solo.identity.name}")
    
    print("\n📝 执行完整项目（10 个任务）...")
    start = time.time()
    solo_success = 0
    for i in range(10):
        result = await solo.act({"description": f"完整项目 - 任务 {i+1}", "importance": 8})
        if result.get("status") == "completed":
            solo_success += 1
    results["solo_time"] = time.time() - start
    results["solo_quality"] = solo_success / 10 * 100
    
    print(f"   完成时间：{results['solo_time']:.2f}s")
    print(f"   任务质量：{results['solo_quality']:.1f}% ({solo_success}/10)")
    
    # ========== 团队模式 ==========
    print("\n" + "=" * 70)
    print("📖 场景：团队模式 - PM+Dev+Tester 协作")
    print("=" * 70)
    
    pm = Agent(name="PM", role="pm", language="zh")
    dev = Agent(name="Dev", role="developer", language="zh")
    tester = Agent(name="Tester", role="tester", language="zh")
    print(f"\n✅ 创建 3 个 Agent: PM, Dev, Tester")
    
    # PM 记住需求
    print("\n📝 PM 记录需求...")
    for i in range(5):
        await pm.memory.remember(f"需求 {i+1}", type=MemoryType.SEMANTIC, importance=8)
    
    # 团队注册
    print("\n📝 团队注册到 Mesh...")
    mesh = AgentMesh()
    await mesh.register(pm)
    await mesh.register(dev)
    await mesh.register(tester)
    print(f"   ✅ Mesh 注册成功，团队规模：{len(mesh)}")
    
    # 团队任务
    print("\n📝 执行团队任务...")
    start = time.time()
    result = await mesh.team_task(
        task={"description": "完整项目", "importance": 8},
        agents=[pm, dev, tester]
    )
    results["team_time"] = time.time() - start
    
    if result.get("status") == "completed":
        results["team_quality"] = 100
        print(f"   ✅ 团队任务完成")
    else:
        results["team_quality"] = 0
        print(f"   ❌ 团队任务失败")
    
    print(f"   完成时间：{results['team_time']:.2f}s")
    print(f"   任务质量：{results['team_quality']:.1f}%")
    
    # ========== 知识共享测试 ==========
    print("\n" + "=" * 70)
    print("📝 测试：知识共享")
    print("=" * 70)
    
    # Dev 向 PM 学习
    learned_dev = await dev.learn_from(pm, topic="需求")
    print(f"\n   Dev 向 PM 学习：{learned_dev} 条")
    
    # Tester 向 Dev 学习
    learned_tester = await tester.learn_from(dev, topic="实现")
    print(f"   Tester 向 Dev 学习：{learned_tester} 条")
    
    # 验证知识共享
    if learned_dev > 0 or learned_tester > 0:
        results["knowledge_shared"] = True
        print(f"   ✅ 知识共享成功")
    else:
        print(f"   ⚠️ 知识共享未成功")
    
    # ========== 对比结果 ==========
    print("\n" + "=" * 70)
    print("📊 个人 vs 团队对比")
    print("=" * 70)
    
    print(f"\n完成时间:")
    print(f"   个人：{results['solo_time']:.2f}s")
    print(f"   团队：{results['team_time']:.2f}s")
    time_better = "团队" if results["team_time"] < results["solo_time"] else "个人"
    print(f"   ✅ {time_better}更快")
    
    print(f"\n任务质量:")
    print(f"   个人：{results['solo_quality']:.1f}%")
    print(f"   团队：{results['team_quality']:.1f}%")
    quality_better = "团队" if results["team_quality"] > results["solo_quality"] else "个人"
    print(f"   ✅ {quality_better}更好")
    
    print(f"\n知识共享:")
    print(f"   Dev 学到：{learned_dev} 条")
    print(f"   Tester 学到：{learned_tester} 条")
    
    # ========== 计算得分 ==========
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    
    time_score = max(0, (1 - (results["team_time"] / max(results["solo_time"], 0.01))) * 100 + 50) * 0.3
    quality_score = max(0, (results["team_quality"] - results["solo_quality"] + 50)) * 0.4
    knowledge_score = 100 if results["knowledge_shared"] else 0
    knowledge_score *= 0.3
    
    results["total_score"] = min(time_score + quality_score + knowledge_score, 100)
    
    print(f"\n完成时间：团队 {results['team_time']:.2f}s vs 个人 {results['solo_time']:.2f}s - {'✅' if results['team_time'] < results['solo_time'] else '⚠️'}")
    print(f"任务质量：团队 {results['team_quality']:.1f}% vs 个人 {results['solo_quality']:.1f}% - {'✅' if results['team_quality'] >= results['solo_quality'] else '⚠️'}")
    print(f"知识共享：{'✅' if results['knowledge_shared'] else '❌'}")
    print(f"\n{'='*70}")
    print(f"总得分：{results['total_score']:.1f}/10")
    print(f"{'='*70}")
    
    # ========== 评价 ==========
    print("\n📝 评价:")
    if results["total_score"] >= 9:
        print("   ⭐⭐⭐⭐⭐ 优秀！团队协作明显优于个人")
    elif results["total_score"] >= 7:
        print("   ⭐⭐⭐⭐ 良好！团队协作有效")
    elif results["total_score"] >= 5:
        print("   ⭐⭐⭐ 一般！团队协作基本可用")
    else:
        print("   ⭐⭐ 需改进！团队协作有问题")
    
    # ========== 关键发现 ==========
    print("\n💡 关键发现:")
    if results["team_time"] < results["solo_time"]:
        print(f"   ✓ 团队更快 - 节省{((results['solo_time']-results['team_time'])/results['solo_time']*100):.1f}%时间")
    if results["team_quality"] > results["solo_quality"]:
        print(f"   ✓ 团队质量更高 - 提升{results['team_quality']-results['solo_quality']:.1f}%")
    if results["knowledge_shared"]:
        print(f"   ✓ 知识共享成功 - Dev 学到{learned_dev}条，Tester 学到{learned_tester}条")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_collaboration())
    
    print("\n" + "=" * 70)
    print("📄 测试结果摘要")
    print("=" * 70)
    print(f"个人完成时间：{results['solo_time']:.2f}s")
    print(f"团队完成时间：{results['team_time']:.2f}s")
    print(f"个人质量：{results['solo_quality']:.1f}%")
    print(f"团队质量：{results['team_quality']:.1f}%")
    print(f"知识共享：{'是' if results['knowledge_shared'] else '否'}")
    print(f"得分：{results['total_score']:.1f}/10")
    print("=" * 70)
