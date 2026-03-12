"""
AMP 集成示例 - 展示所有新功能

功能演示:
1. 火星文件管理系统集成 (事务支持/版本控制)
2. Memory Bank 双向同步
3. OpenClaw 深度集成 (技能调用/子代理)
4. 心跳检查机制
"""

import asyncio
import sys
from pathlib import Path

# 添加 SDK 到路径
sdk_path = Path(__file__).parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

import amp
from amp.memory import MemoryType


async def demo_basic_agent():
    """示例 1: 基础 Agent 创建和使用"""
    print("=" * 70)
    print("📖 示例 1: 基础 Agent 创建和使用")
    print("=" * 70)
    
    # 创建 Agent（基础模式）
    agent = amp.Agent(
        name="测试助手",
        role="assistant",
        language="zh"
    )
    
    print(f"✅ Agent 已创建: {agent.identity.name}")
    print(f"   ID: {agent.identity.agent_id}")
    print(f"   等级: {agent.identity.level}")
    print(f"   XP: {agent.identity.experience_points}")
    
    # 存储记忆
    await agent.memory.remember(
        "用户喜欢中文回复",
        type=MemoryType.SEMANTIC,
        importance=8,
        tags=["用户", "偏好"]
    )
    
    await agent.memory.remember(
        "项目使用 MIT 许可证",
        type=MemoryType.SEMANTIC,
        importance=6,
        tags=["项目", "配置"]
    )
    
    print(f"   记忆数量：{agent.memory.count()}")
    
    # 回忆
    memories = await agent.memory.recall("用户偏好")
    print(f"   回忆结果:")
    for mem in memories:
        print(f"     - [{mem.type.value}] {mem.content}")
    
    print()


async def demo_fm_storage():
    """示例 2: 火星文件管理系统集成"""
    print("=" * 70)
    print("🔧 示例 2: 火星文件管理系统集成 (事务支持)")
    print("=" * 70)
    
    try:
        # 创建启用 FM 存储的 Agent
        agent = amp.Agent(
            name="FM 测试员",
            role="tester",
            language="zh",
            enable_fm=True,  # 启用火星文件管理
        )
        
        print("✅ Agent 已创建 (启用 FM 存储)")
        
        # 开始事务
        tx_id = agent.memory.begin_transaction()
        print(f"📝 开始事务：{tx_id}")
        
        # 批量写入记忆
        await agent.memory.remember(
            "第一次使用事务写入记忆",
            type=MemoryType.EPISODIC,
            importance=7,
            tags=["事务", "测试"]
        )
        
        await agent.memory.remember(
            "事务支持回滚操作",
            type=MemoryType.SEMANTIC,
            importance=8,
            tags=["事务", "功能"]
        )
        
        await agent.memory.remember(
            "火星文件管理系统提供版本控制",
            type=MemoryType.SEMANTIC,
            importance=9,
            tags=["火星", "版本控制"]
        )
        
        # 提交事务
        success = await agent.memory.commit_transaction()
        if success:
            print(f"✅ 事务提交成功")
        else:
            print(f"❌ 事务提交失败")
        
        print(f"   记忆数量：{agent.memory.count()}")
        
    except Exception as e:
        print(f"⚠️ FM 存储示例需要火星文件管理系统: {e}")
    
    print()


async def demo_memory_bank_sync():
    """示例 3: Memory Bank 双向同步"""
    print("=" * 70)
    print("🔄 示例 3: Memory Bank 双向同步")
    print("=" * 70)
    
    try:
        # 创建启用 Memory Bank 的 Agent
        agent = amp.Agent(
            name="同步测试员",
            role="sync_tester",
            language="zh",
            enable_memory_bank=True,  # 启用 Memory Bank 同步
            memory_bank_url="http://localhost:8100"
        )
        
        print("✅ Agent 已创建 (启用 Memory Bank 同步)")
        
        # 使用 Memory Bank 集成
        mb = amp.MemoryBankIntegration()
        
        # 保存对话
        messages = [
            {"role": "user", "content": "你好，我想了解 AMP 项目"},
            {"role": "assistant", "content": "AMP 是一个 AI 记忆协议项目..."},
        ]
        
        saved = await mb.save_conversation(
            agent_id=agent.identity.agent_id,
            messages=messages,
            summary="讨论 AMP 项目介绍",
            tags=["对话", "AMP"]
        )
        
        if saved:
            print("✅ 对话已保存到 Memory Bank")
        
        # 同步记忆
        memories = list(agent.memory._memories.values())
        stats = await mb.sync_agent_to_bank(agent.identity.agent_id, memories)
        print(f"📊 同步统计：{stats}")
        
        # 加载用户偏好
        preferences = await mb.load_user_preferences(agent.identity.agent_id)
        print(f"📥 加载用户偏好：{len(preferences)} 条")
        
        await mb.close()
        
    except Exception as e:
        print(f"⚠️ Memory Bank 示例需要服务运行：{e}")
    
    print()


async def demo_openclaw_integration():
    """示例 4: OpenClaw 深度集成"""
    print("=" * 70)
    print("🔗 示例 4: OpenClaw 深度集成 (技能调用)")
    print("=" * 70)
    
    try:
        # 创建启用 OpenClaw 的 Agent
        agent = amp.Agent(
            name="OpenClaw 助手",
            role="openclaw_assistant",
            language="zh",
            enable_openclaw=True,  # 启用 OpenClaw 集成
        )
        
        print("✅ Agent 已创建 (启用 OpenClaw 集成)")
        
        # 使用 serper 技能进行联网搜索
        print("\n🔍 使用 serper 技能搜索...")
        search_result = await agent.use_skill(
            "serper",
            query="Python 异步编程 最佳实践"
        )
        
        if search_result.get("status") == "success":
            print("✅ 搜索成功")
            # 记录搜索结果到记忆
            await agent.memory.remember(
                f"搜索结果：{str(search_result.get('result', ''))[:200]}",
                type=MemoryType.SEMANTIC,
                importance=6,
                tags=["搜索", "serper", "Python"]
            )
        else:
            print(f"⚠️ 搜索失败：{search_result.get('message', 'unknown')}")
        
        # 查看记忆（技能使用会被记录）
        skill_memories = await agent.memory.recall("skill", limit=3)
        print(f"\n📝 技能使用记忆：{len(skill_memories)} 条")
        for mem in skill_memories:
            print(f"   - [{mem.emotion}] {mem.content[:50]}...")
        
    except Exception as e:
        print(f"⚠️ OpenClaw 示例需要服务运行：{e}")
    
    print()


async def demo_heartbeat():
    """示例 5: 心跳检查机制"""
    print("=" * 70)
    print("💓 示例 5: 心跳检查机制")
    print("=" * 70)
    
    try:
        # 创建心跳管理器
        heartbeat = amp.HeartbeatManager(
            workspace=str(Path.home() / ".openclaw" / "workspace")
        )
        
        print("✅ 心跳管理器已创建")
        print(f"   HEARTBEAT 文件：{heartbeat.heartbeat_path}")
        
        # 添加任务
        heartbeat.add_task(
            "memory_consolidation",
            "0 3 * * *",
            description="每天凌晨 3 点进行记忆巩固"
        )
        
        heartbeat.add_task(
            "sync_with_memory_bank",
            "0 * * * *",
            description="每小时与 Memory Bank 同步"
        )
        
        heartbeat.add_task(
            "agent_health_check",
            "*/30 * * * *",
            description="每 30 分钟检查 Agent 健康状态"
        )
        
        print(f"📅 已添加 {len(heartbeat.tasks)} 个心跳任务")
        
        # 获取状态
        status = heartbeat.get_status()
        print(f"\n📊 心跳状态:")
        print(f"   运行中：{status['running']}")
        for name, task_status in status['tasks'].items():
            print(f"   - {name}: {task_status['last_status']} (错误：{task_status['error_count']})")
        
        # 手动运行一次
        print("\n🔔 手动运行任务...")
        success = await heartbeat.run_task_now("memory_consolidation")
        print(f"   结果：{'✅ 成功' if success else '❌ 失败'}")
        
    except Exception as e:
        print(f"⚠️ 心跳示例：{e}")
    
    print()


async def demo_full_integration():
    """示例 6: 完整集成演示"""
    print("=" * 70)
    print("🎯 示例 6: 完整集成演示 (所有功能)")
    print("=" * 70)
    
    try:
        # 创建启用所有功能的 Agent
        agent = amp.Agent(
            name="全功能助手",
            role="full_stack_assistant",
            language="zh",
            enable_fm=True,              # 火星文件管理
            enable_memory_bank=True,     # Memory Bank 同步
            enable_openclaw=True,        # OpenClaw 集成
        )
        
        print("✅ 全功能 Agent 已创建")
        print(f"   特性：FM=True, MemoryBank=True, OpenClaw=True")
        
        # 1. 使用技能获取信息
        print("\n🔧 步骤 1: 使用技能...")
        skill_result = await agent.use_skill("serper", query="AMP 项目")
        
        # 2. 存储到记忆（自动同步到 Memory Bank）
        print("\n📝 步骤 2: 存储记忆...")
        await agent.memory.remember(
            "使用 serper 搜索到 AMP 项目信息",
            type=MemoryType.EPISODIC,
            importance=7,
            tags=["技能", "搜索", "AMP"]
        )
        
        # 3. 执行任务
        print("\n⚡ 步骤 3: 执行任务...")
        result = await agent.act({
            "description": "整理 AMP 项目信息",
            "importance": 8,
            "tags": ["整理", "项目"]
        })
        print(f"   任务状态：{result.get('status')}")
        
        # 4. 查看记忆统计
        print("\n📊 步骤 4: 记忆统计...")
        stats = agent.memory.stats()
        print(f"   总记忆数：{stats['total']}")
        print(f"   按类型：{stats['by_type']}")
        print(f"   按情感：{stats['by_emotion']}")
        
        # 5. 睡眠（记忆巩固）
        print("\n💤 步骤 5: 睡眠（记忆巩固）...")
        sleep_stats = await agent.sleep()
        print(f"   巩固结果：{sleep_stats}")
        
        # 6. 查看最终状态
        print("\n📈 步骤 6: 最终状态...")
        status = agent.status()
        print(f"   Agent: {status['identity']['name']}")
        print(f"   等级：{status['identity']['level']}")
        print(f"   XP: {status['identity']['experience_points']}")
        print(f"   成功率：{status['identity']['success_rate']:.1%}")
        
    except Exception as e:
        print(f"⚠️ 完整集成示例：{e}")
    
    print()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("🚀 AMP 集成示例 - 新功能演示")
    print("=" * 70)
    print()
    
    # 运行所有示例
    await demo_basic_agent()
    await demo_fm_storage()
    await demo_memory_bank_sync()
    await demo_openclaw_integration()
    await demo_heartbeat()
    await demo_full_integration()
    
    print("=" * 70)
    print("✅ 所有示例运行完成!")
    print("=" * 70)
    print()
    print("📝 总结:")
    print("   1. ✅ 基础 Agent 创建和使用")
    print("   2. ✅ 火星文件管理系统集成 (事务支持)")
    print("   3. ✅ Memory Bank 双向同步")
    print("   4. ✅ OpenClaw 深度集成 (技能调用)")
    print("   5. ✅ 心跳检查机制")
    print("   6. ✅ 完整集成演示")
    print()


if __name__ == "__main__":
    asyncio.run(main())
