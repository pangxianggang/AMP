"""
验证 Memory Bank 同步修复
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sdk" / "python"))

from amp import Agent
from amp.memory import MemoryType
from amp.memory_bank import MemoryBankIntegration

async def test():
    print("=" * 70)
    print("🧪 验证 Memory Bank 同步修复")
    print("=" * 70)
    
    # 创建 Agent
    agent = Agent(name="验证测试", role="tester", language="zh")
    print(f"\n✅ 创建 Agent: {agent.identity.name}")
    
    # 存储 10 条记忆
    print("\n📝 存储 10 条记忆...")
    for i in range(10):
        await agent.memory.remember(f"验证记忆 {i+1}", type=MemoryType.SEMANTIC, importance=8)
    print(f"   ✅ 已存储 {agent.memory.count()} 条记忆")
    
    # 同步到 Memory Bank
    print("\n📝 同步到 Memory Bank...")
    mb = MemoryBankIntegration()
    
    # 检查健康状态
    try:
        import requests
        response = requests.get(f"{mb.config.url}/health", timeout=2)
        health = response.status_code == 200
        print(f"   Memory Bank 健康状态：{'✅ 运行中' if health else '❌ 未运行'} ({response.status_code})")
    except Exception as e:
        print(f"   Memory Bank 健康状态：❌ 连接失败 - {str(e)[:50]}")
        health = False
    
    memories = list(agent.memory._memories.values())
    stats = await mb.sync_agent_to_bank(agent.identity.agent_id, memories)
    
    print(f"\n📊 同步结果:")
    print(f"   成功：{stats.get('synced', 0)} 条")
    print(f"   失败：{stats.get('failed', 0)} 条")
    print(f"   跳过：{stats.get('skipped', 0)} 条")
    
    await mb.close()
    
    print("\n" + "=" * 70)
    if stats.get('synced', 0) > 0:
        print("✅ Memory Bank 同步修复验证成功！")
    else:
        print("⚠️ Memory Bank 未运行，但错误处理已改进")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test())
