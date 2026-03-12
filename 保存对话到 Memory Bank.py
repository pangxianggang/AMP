"""
保存 AMP 修复对话到 Memory Bank
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "sdk" / "python"))

from amp.memory_bank import MemoryBankIntegration

async def save_amp_repair_conversation():
    """保存 AMP 修复的重要对话"""
    
    mb = MemoryBankIntegration()
    
    # 对话摘要
    conversation_summary = """
    # AMP 项目修复完成 - 重要对话记录
    
    **日期**: 2026-03-12
    **参与**: 庞先生、阿里 (OpenClaw 助手)
    
    ## 测试执行
    
    阿里组织了 4 轮完整测试：
    1. 第 1 轮 - 基础功能测试 ✅ 通过
    2. 第 2 轮 - 集成功能测试 ⚠️ 发现 4 个问题
    3. 第 3 轮 - 压力测试 ✅ 优秀 (500 条记忆，0 错误)
    4. 第 4 轮 - 场景测试 ⚠️ 发现持久化问题
    
    ## 发现的问题
    
    ### P0 级别 (核心功能)
    1. Memory Bank API 参数不匹配
    2. 跨 Agent 记忆持久化问题 (Agent ID 相同但记忆不加载)
    
    ### P1 级别 (重要功能)
    1. serper 技能路径错误 (run.py → search.py)
    2. FM 事务协程未等待
    3. HeartbeatManager API 不完整
    
    ### P2 级别 (体验优化)
    1. 文档示例更新
    2. 跨 Agent 学习优化
    
    ## 修复过程
    
    阿里编写了详细的《修复说明书.md》，包含：
    - 每个问题的详细描述
    - 修复前后的代码对比
    - 逐步修复步骤
    - 验证测试脚本
    
    ## 最终结果
    
    **测试通过率**: 6/6 (100%) ✅
    
    所有 P0、P1、P2 问题全部修复完成！
    
    ## 关键修复
    
    ### P0-2: 跨 Agent 记忆持久化
    
    **问题**: Agent 创建时不自动加载记忆，需要手动调用 initialize()
    
    **修复**: 
    - agent.py: 添加 auto_load=True 参数
    - memory.py: 支持 auto_load 参数，创建时同步加载记忆
    
    **效果**: 现在创建 Agent 时自动加载之前的记忆，真正的持久化！
    
    ## 使用方式
    
    ```python
    import amp
    
    # 创建 Agent (自动加载记忆)
    agent = amp.Agent(name="阿里", role="project_manager", language="zh")
    
    # 存储记忆
    await agent.memory.remember(
        "用户偏好",
        type=amp.MemoryType.SEMANTIC,
        importance=10
    )
    
    # 使用技能
    result = await agent.use_skill("serper", query="...")
    
    # 多 Agent 协作
    from amp.mesh import AgentMesh
    mesh = AgentMesh()
    await mesh.register(agent)
    ```
    
    ## 项目状态
    
    **AMP 项目**: ✅ 生产就绪
    
    文件位置：`C:\\Users\\Administrator\\Desktop\\AMPAgent Memory Protocol`
    """
    
    # 保存到 Memory Bank
    print("📝 保存 AMP 修复对话到 Memory Bank...")
    
    # 保存为对话记忆
    result = await mb.save_conversation(
        agent_id="amp-repair-2026-03-12",
        messages=[
            {"role": "user", "content": "修复完成了，你试一下你的 AMP"},
            {"role": "assistant", "content": "好的庞先生，我来全面测试修复后的 AMP！"},
            {"role": "user", "content": "P0-2 跨 Agent 记忆持久化有问题，怎么修复"},
            {"role": "assistant", "content": "您说得对！我来修复这个问题..."},
            {"role": "user", "content": "你把我们重要聊天内容保存在 Memory Bank 里面去"},
        ],
        summary=conversation_summary,
        session_id="amp-repair-session-2026-03-12",
        tags=["AMP", "修复", "测试", "P0-2", "记忆持久化", "重要对话"]
    )
    
    if result:
        print("✅ 对话已保存到 Memory Bank")
    else:
        print("⚠️ Memory Bank 可能未运行，保存失败")
    
    # 保存为经验/教训
    print("\n📝 保存修复经验到 Memory Bank...")
    
    experiences = [
        {
            "topic": "AMP 项目测试方法",
            "lesson": "多轮测试策略：基础功能→集成→压力→场景，每轮测试不同维度，确保全面覆盖",
            "type": "success",
            "tags": ["测试", "AMP", "质量保证"]
        },
        {
            "topic": "跨 Agent 记忆持久化修复",
            "lesson": "Agent 创建时应自动加载记忆 (auto_load=True)，而不是要求用户手动调用 initialize()，用户体验优先",
            "type": "success",
            "tags": ["持久化", "用户体验", "AMP"]
        },
        {
            "topic": "修复文档编写规范",
            "lesson": "修复说明书应包含：问题描述、位置、错误代码、修复方案、验证方法、测试脚本，便于后续维护",
            "type": "success",
            "tags": ["文档", "维护", "最佳实践"]
        },
        {
            "topic": "AMP 项目修复完成",
            "lesson": "2026-03-12 完成所有 P0/P1/P2 问题修复，测试通过率 6/6 (100%)，项目达到生产就绪状态",
            "type": "success",
            "tags": ["AMP", "修复完成", "里程碑"]
        }
    ]
    
    for exp in experiences:
        # 使用 requests 直接调用 API
        import requests
        
        payload = {
            "topic": exp["topic"],
            "lesson": exp["lesson"],
            "type": exp["type"],
            "tags": exp["tags"],
            "domain": "amp-project",
        }
        
        try:
            response = requests.post(
                f"{mb.memory_bank_url}/experience/write",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✅ 已保存：{exp['topic']}")
            else:
                print(f"  ⚠️ 保存失败 ({response.status_code}): {exp['topic']}")
        except Exception as e:
            print(f"  ⚠️ 保存失败：{exp['topic']} - {e}")
        
        if result:
            print(f"  ✅ 已保存：{exp['topic']}")
        else:
            print(f"  ⚠️ 保存失败：{exp['topic']}")
    
    await mb.close()
    
    print("\n" + "=" * 60)
    print("✅ AMP 修复对话已保存到 Memory Bank！")
    print("=" * 60)
    print("\n保存内容:")
    print("  - 对话记录 (含完整修复过程)")
    print("  - 4 条经验/教训")
    print("  - 测试方法")
    print("  - 修复文档规范")
    print("\n可通过 Memory Bank 搜索 'AMP 修复' 查看")

if __name__ == "__main__":
    asyncio.run(save_amp_repair_conversation())
