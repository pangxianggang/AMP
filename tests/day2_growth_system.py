"""
AMP 7 天价值测试 - Day 2: 成长系统测试

测试问题：AI 能否从错误中学习并改进？
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent
from amp.memory import MemoryType

print("=" * 70)
print("🧪 AMP 7 天价值测试 - Day 2")
print("📈 成长系统测试")
print("=" * 70)
print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

async def test_growth_system():
    results = {
        "initial_xp": 0,
        "final_xp": 0,
        "xp_gained": 0,
        "initial_level": 1,
        "final_level": 1,
        "level_up": False,
        "initial_success_rate": 0.0,
        "final_success_rate": 0.0,
        "success_rate_improvement": 0.0,
        "emotional_memories": 0,
        "total_score": 0.0,
    }
    
    # ========== 创建学习者 Agent ==========
    print("=" * 70)
    print("📖 场景：创建一个学习者 Agent")
    print("=" * 70)
    
    learner = Agent(name="学习者", role="learner", language="zh")
    print(f"\n✅ 创建 Agent: {learner.identity.name}")
    print(f"   初始等级：{learner.identity.level}")
    print(f"   初始 XP: {learner.identity.experience_points}")
    print(f"   初始成功率：{learner.identity.success_rate:.1%}")
    
    results["initial_xp"] = learner.identity.experience_points
    results["initial_level"] = learner.identity.level
    results["initial_success_rate"] = learner.identity.success_rate
    
    # ========== 第 1 次：犯错 ==========
    print("\n" + "=" * 70)
    print("📖 场景：第 1 次尝试 - 犯错并学习")
    print("=" * 70)
    
    print("\n📝 任务 1: 完成一个困难任务...")
    # 模拟失败任务
    result1 = await learner.act({"description": "困难任务 - 第 1 次尝试", "importance": 8})
    
    # 记录失败教训
    await learner.memory.remember(
        "困难任务需要更多准备，第 1 次失败了",
        type=MemoryType.EMOTIONAL,
        emotion="negative",
        importance=9,
        tags=["教训", "困难任务"]
    )
    print(f"   ❌ 任务失败，记录情感记忆")
    results["emotional_memories"] += 1
    
    # ========== 第 2-3 次：改进 ==========
    print("\n" + "=" * 70)
    print("📖 场景：第 2-3 次尝试 - 从错误中改进")
    print("=" * 70)
    
    for i in range(2, 4):
        print(f"\n📝 任务 {i}: 改进后再次尝试...")
        result = await learner.act({"description": f"困难任务 - 第{i}次尝试", "importance": 8})
        
        if result.get("status") == "completed":
            print(f"   ✅ 任务成功！")
            # 记录成功经验
            await learner.memory.remember(
                f"第{i}次尝试成功了，改进方法有效",
                type=MemoryType.EMOTIONAL,
                emotion="positive",
                importance=8,
                tags=["经验", "成功"]
            )
            results["emotional_memories"] += 1
        else:
            print(f"   ❌ 任务失败")
    
    # ========== 第 4-10 次：重复练习 ==========
    print("\n" + "=" * 70)
    print("📖 场景：第 4-10 次尝试 - 重复练习巩固技能")
    print("=" * 70)
    
    success_count = 0
    for i in range(4, 11):
        result = await learner.act({"description": f"练习任务 {i-3}", "importance": 6})
        if result.get("status") == "completed":
            success_count += 1
    
    print(f"\n📊 练习结果：{success_count}/7 成功")
    
    # ========== 查看成长 ==========
    print("\n" + "=" * 70)
    print("📊 成长报告")
    print("=" * 70)
    
    print(f"\n初始状态:")
    print(f"   等级：{results['initial_level']}")
    print(f"   XP: {results['initial_xp']}")
    print(f"   成功率：{results['initial_success_rate']:.1%}")
    
    print(f"\n最终状态:")
    print(f"   等级：{learner.identity.level}")
    print(f"   XP: {learner.identity.experience_points}")
    print(f"   成功率：{learner.identity.success_rate:.1%}")
    
    results["final_xp"] = learner.identity.experience_points
    results["final_level"] = learner.identity.level
    results["final_success_rate"] = learner.identity.success_rate
    
    # 计算成长
    results["xp_gained"] = results["final_xp"] - results["initial_xp"]
    results["level_up"] = results["final_level"] > results["initial_level"]
    results["success_rate_improvement"] = results["final_success_rate"] - results["initial_success_rate"]
    
    print(f"\n📈 成长数据:")
    print(f"   XP 增长：+{results['xp_gained']}")
    print(f"   等级提升：{'✅ 是' if results['level_up'] else '❌ 否'}")
    print(f"   成功率提升：{results['success_rate_improvement']:.1%}")
    print(f"   情感记忆数：{results['emotional_memories']} 条")
    
    # ========== 测试记忆召回 ==========
    print("\n" + "=" * 70)
    print("📝 测试：能否回忆起失败教训？")
    print("=" * 70)
    
    memories = await learner.memory.recall("失败", limit=3)
    print(f"\n找到 {len(memories)} 条关于'失败'的记忆:")
    for mem in memories:
        print(f"   - [{mem.type.value}] {mem.content[:50]}...")
        if mem.emotion == "negative":
            print(f"     情感：❌ 负面（教训）")
        elif mem.emotion == "positive":
            print(f"     情感：✅ 正面（经验）")
    
    # ========== 计算得分 ==========
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    
    # 评分标准
    xp_score = min(results["xp_gained"] / 80 * 100, 100) * 0.3  # 30% 权重，目标 80 XP
    level_score = 100 if results["level_up"] else 0
    level_score *= 0.3  # 30% 权重
    success_score = min(results["final_success_rate"] / 0.8 * 100, 100) * 0.4  # 40% 权重，目标 80%
    
    results["total_score"] = xp_score + level_score + success_score
    
    print(f"\nXP 增长：{results['xp_gained']} (目标：>80) - {'✅' if results['xp_gained'] > 80 else '⚠️'}")
    print(f"等级提升：{'✅ 是' if results['level_up'] else '❌ 否'} (目标：≥Level 2)")
    print(f"成功率：{results['final_success_rate']:.1%} (目标：>80%) - {'✅' if results['final_success_rate'] > 0.8 else '⚠️'}")
    print(f"\n{'='*70}")
    print(f"总得分：{results['total_score']:.1f}/10")
    print(f"{'='*70}")
    
    # ========== 评价 ==========
    print("\n📝 评价:")
    if results["total_score"] >= 9:
        print("   ⭐⭐⭐⭐⭐ 优秀！AI 成长系统完美工作")
    elif results["total_score"] >= 7:
        print("   ⭐⭐⭐⭐ 良好！AI 能从经验中成长")
    elif results["total_score"] >= 5:
        print("   ⭐⭐⭐ 一般！成长系统基本可用")
    else:
        print("   ⭐⭐ 需改进！成长系统有问题")
    
    # ========== 关键发现 ==========
    print("\n💡 关键发现:")
    if results["xp_gained"] > 0:
        print(f"   ✓ XP 系统正常 - 获得 {results['xp_gained']} XP")
    if results["emotional_memories"] > 0:
        print(f"   ✓ 情感记忆记录 - {results['emotional_memories']} 条教训/经验")
    if results["final_success_rate"] > results["initial_success_rate"]:
        print(f"   ✓ 成功率提升 - 从{results['initial_success_rate']:.1%} → {results['final_success_rate']:.1%}")
    if results["level_up"]:
        print(f"   ✓ 等级提升 - Level {results['initial_level']} → {results['final_level']}")
    
    return results

# 执行测试
if __name__ == "__main__":
    results = asyncio.run(test_growth_system())
    
    # 输出 JSON 结果（用于生成报告）
    print("\n" + "=" * 70)
    print("📄 测试结果摘要")
    print("=" * 70)
    print(f"初始 XP: {results['initial_xp']}")
    print(f"最终 XP: {results['final_xp']}")
    print(f"XP 增长：+{results['xp_gained']}")
    print(f"初始等级：{results['initial_level']}")
    print(f"最终等级：{results['final_level']}")
    print(f"等级提升：{'是' if results['level_up'] else '否'}")
    print(f"初始成功率：{results['initial_success_rate']:.1%}")
    print(f"最终成功率：{results['final_success_rate']:.1%}")
    print(f"成功率提升：{results['success_rate_improvement']:.1%}")
    print(f"情感记忆：{results['emotional_memories']} 条")
    print(f"得分：{results['total_score']:.1f}/10")
    print("=" * 70)
