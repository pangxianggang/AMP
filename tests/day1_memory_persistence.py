"""
AMP 7 天价值测试 - Day 1: 记忆持久化测试

测试问题：AI 能否像人一样记住用户？
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import time

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp import Agent
from amp.memory import MemoryType

print("=" * 70)
print("🧪 AMP 7 天价值测试 - Day 1")
print("📝 记忆持久化测试")
print("=" * 70)
print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

async def test_memory_persistence():
    results = {
        "memories_stored": 0,
        "memories_recalled": 0,
        "recall_rate": 0.0,
        "accuracy": 0.0,
        "response_time_ms": 0,
        "total_score": 0.0,
    }
    
    # 用户信息（模拟庞先生的偏好）
    user_profile = {
        "language": "中文",
        "wake_time": "7 点起床",
        "allergy": "芒果过敏",
        "preference": "喜欢直接高效的沟通",
        "project": "使用 FastAPI 框架",
    }
    
    # ========== 第 1 次见面 ==========
    print("=" * 70)
    print("📖 场景：第 1 次见面 - 存储用户信息")
    print("=" * 70)
    
    ali_1 = Agent(name="阿里", role="assistant", language="zh")
    print(f"\n✅ 创建 Agent: {ali_1.identity.name}")
    
    print("\n📝 存储用户信息...")
    await ali_1.memory.remember(
        f"用户喜欢{user_profile['language']}",
        type=MemoryType.SEMANTIC,
        importance=10,
        tags=["用户", "偏好", "语言"]
    )
    print(f"   ✓ 用户语言：{user_profile['language']}")
    
    await ali_1.memory.remember(
        f"用户{user_profile['wake_time']}",
        type=MemoryType.SEMANTIC,
        importance=8,
        tags=["用户", "习惯", "作息"]
    )
    print(f"   ✓ 作息时间：{user_profile['wake_time']}")
    
    await ali_1.memory.remember(
        f"用户{user_profile['allergy']}",
        type=MemoryType.SEMANTIC,
        importance=10,
        tags=["用户", "健康", "过敏"]
    )
    print(f"   ✓ 过敏信息：{user_profile['allergy']}")
    
    await ali_1.memory.remember(
        f"用户{user_profile['preference']}",
        type=MemoryType.SEMANTIC,
        importance=9,
        tags=["用户", "偏好", "沟通"]
    )
    print(f"   ✓ 沟通偏好：{user_profile['preference']}")
    
    await ali_1.memory.remember(
        f"用户{user_profile['project']}",
        type=MemoryType.SEMANTIC,
        importance=8,
        tags=["用户", "项目", "技术"]
    )
    print(f"   ✓ 项目技术：{user_profile['project']}")
    
    results["memories_stored"] = ali_1.memory.count()
    print(f"\n📊 共存储 {results['memories_stored']} 条记忆")
    
    # ========== 第 2 次见面（模拟重启） ==========
    print("\n" + "=" * 70)
    print("📖 场景：第 2 次见面 - 测试记忆召回")
    print("=" * 70)
    
    print("\n🔄 模拟 Agent 重启...")
    ali_2 = Agent(name="阿里", role="assistant", language="zh")
    await ali_2.initialize()  # 加载之前的记忆
    print(f"✅ 新 Agent 创建完成")
    print(f"   自动加载记忆数：{ali_2.memory.count()}")
    
    # ========== 测试记忆召回 ==========
    print("\n" + "=" * 70)
    print("📝 测试：记忆召回和回答准确性")
    print("=" * 70)
    
    test_questions = [
        ("用户喜欢什么语言？", "中文", ["语言", "中文"]),
        ("用户几点起床？", "7 点", ["作息", "起床", "7 点"]),
        ("用户对什么过敏？", "芒果", ["过敏", "芒果"]),
        ("用户喜欢什么样的沟通？", "直接", ["沟通", "直接", "高效"]),
        ("用户使用什么框架？", "FastAPI", ["框架", "FastAPI"]),
    ]
    
    correct_count = 0
    total_response_time = 0
    
    for i, (question, expected_keyword, search_terms) in enumerate(test_questions, 1):
        print(f"\n{i}. 问题：{question}")
        
        # 计时
        start_time = time.time()
        
        # 搜索记忆
        memories = await ali_2.memory.recall(search_terms[0], limit=3)
        
        # 计算响应时间
        response_time = (time.time() - start_time) * 1000
        total_response_time += response_time
        
        # 检查是否找到相关记忆
        found = False
        answer = "未找到相关信息"
        
        for mem in memories:
            if expected_keyword in mem.content:
                found = True
                answer = mem.content
                correct_count += 1
                break
        
        status = "✅" if found else "❌"
        print(f"   {status} 回答：{answer}")
        print(f"   ⏱️  响应时间：{response_time:.2f}ms")
    
    # 计算结果
    results["memories_recalled"] = correct_count
    results["recall_rate"] = (correct_count / len(test_questions)) * 100
    results["accuracy"] = results["recall_rate"]
    results["response_time_ms"] = total_response_time / len(test_questions)
    
    # ========== 计算得分 ==========
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    
    # 评分标准
    recall_score = min(results["recall_rate"], 100) * 0.4  # 40% 权重
    accuracy_score = min(results["accuracy"], 100) * 0.4   # 40% 权重
    speed_score = max(0, (100 - results["response_time_ms"])) * 0.2  # 20% 权重，100ms 内满分
    
    results["total_score"] = recall_score + accuracy_score + speed_score
    
    print(f"\n记忆召回率：{results['recall_rate']:.1f}% ({correct_count}/{len(test_questions)}) - {'✅' if results['recall_rate'] >= 100 else '⚠️'}")
    print(f"回答准确率：{results['accuracy']:.1f}% - {'✅' if results['accuracy'] >= 100 else '⚠️'}")
    print(f"平均响应时间：{results['response_time_ms']:.2f}ms - {'✅' if results['response_time_ms'] < 100 else '⚠️'}")
    print(f"\n{'='*70}")
    print(f"总得分：{results['total_score']:.1f}/10")
    print(f"{'='*70}")
    
    # ========== 评价 ==========
    print("\n📝 评价:")
    if results["total_score"] >= 9:
        print("   ⭐⭐⭐⭐⭐ 优秀！AMP 记忆持久化完美工作")
    elif results["total_score"] >= 7:
        print("   ⭐⭐⭐⭐ 良好！记忆持久化基本可靠")
    elif results["total_score"] >= 5:
        print("   ⭐⭐⭐ 一般！需要改进")
    else:
        print("   ⭐⭐ 需改进！记忆持久化有问题")
    
    # ========== 关键发现 ==========
    print("\n💡 关键发现:")
    if results["recall_rate"] == 100:
        print("   ✓ 记忆持久化完美 - 新 Agent 能访问所有之前的记忆")
    if results["response_time_ms"] < 50:
        print(f"   ✓ 响应速度极快 - 平均{results['response_time_ms']:.2f}ms")
    if results["memories_stored"] == ali_2.memory.count():
        print("   ✓ 记忆完整无丢失")
    
    return results

# 执行测试
if __name__ == "__main__":
    results = asyncio.run(test_memory_persistence())
    
    # 输出 JSON 结果（用于生成报告）
    print("\n" + "=" * 70)
    print("📄 测试结果摘要")
    print("=" * 70)
    print(f"存储记忆数：{results['memories_stored']}")
    print(f"召回记忆数：{results['memories_recalled']}")
    print(f"召回率：{results['recall_rate']:.1f}%")
    print(f"准确率：{results['accuracy']:.1f}%")
    print(f"响应时间：{results['response_time_ms']:.2f}ms")
    print(f"得分：{results['total_score']:.1f}/10")
    print("=" * 70)
