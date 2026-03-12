# 🚀 AMP 快速开始指南

## 1. 安装依赖

```powershell
# 进入项目目录
cd "C:\Users\Administrator\Desktop\AMP 成品\sdk\python"

# 安装依赖
pip install -e .
```

## 2. 验证安装

```powershell
# 查看版本
amp version

# 查看状态
amp status
```

## 3. 创建你的第一个 Agent

```powershell
# 创建 Agent
amp agent create Ali project_manager --lang zh

# 查看 Agent
amp agent list

# 查看 Agent 详情
amp agent info Ali
```

## 4. 运行示例代码

```powershell
# 运行完整示例
cd "C:\Users\Administrator\Desktop\AMP 成品"
python examples/basic_usage.py
```

## 5. Python 代码使用

创建 `test_agent.py`:

```python
import asyncio
from amp import Agent, MemoryType

async def main():
    # 创建 Agent
    agent = Agent(
        name="Ali",
        role="project_manager",
        language="zh"
    )

    # 存储记忆
    await agent.memory.remember(
        "用户喜欢中文回复",
        type=MemoryType.SEMANTIC,
        importance=8
    )

    # 回忆
    memories = await agent.memory.recall("用户偏好")
    print(f"回忆：{memories[0].content}")

    # 执行任务
    result = await agent.act({
        "description": "规划项目"
    })
    print(f"任务：{result}")

if __name__ == "__main__":
    asyncio.run(main())
```

运行:
```powershell
python test_agent.py
```

## 6. 与 OpenClaw 集成

```python
import asyncio
from amp.integrations.openclaw import OpenClawAMPBridge

async def openclaw_demo():
    bridge = OpenClawAMPBridge()

    # 创建 Agent
    agent = await bridge.create_agent("助手", "assistant")

    # 派生子代理
    result = await bridge.spawn_subagent(
        name="研究员",
        role="researcher",
        task={"description": "研究 Python 异步编程"}
    )

    # 同步到 Memory Bank
    await bridge.sync_to_memory_bank(agent)

if __name__ == "__main__":
    asyncio.run(openclaw_demo())
```

## 7. 与 Memory Bank 集成

```python
import asyncio
from amp.integrations.memory_bank import MemoryBankIntegration

async def memory_bank_demo():
    mb = MemoryBankIntegration()

    # 创建 Agent
    from amp import Agent
    agent = Agent(name="记忆助手", role="assistant")

    # 保存对话
    await mb.save_conversation(
        agent=agent,
        messages=[
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "有什么可以帮助你的？"}
        ],
        summary="初次对话",
        session_id="session-001"
    )

    # 同步记忆
    await mb.sync_agent_to_bank(agent, min_importance=5)

if __name__ == "__main__":
    asyncio.run(memory_bank_demo())
```

## 8. CLI 命令参考

```powershell
# Agent 管理
amp agent create <name> <role> [--lang zh] [--skills skill1,skill2]
amp agent list
amp agent info <name>
amp agent forget <name>

# 记忆管理
amp memory search <query> [--agent <name>] [--limit 10]
amp memory stats
amp memory consolidate

# 系统
amp init
amp status
amp version
```

## 9. 常见问题

### Q: Memory Bank 连接失败？
A: 确保 Memory Bank 服务正在运行：
```powershell
cd "C:\Users\Administrator\Desktop\AgentMemoryBank"
python main.py
```

### Q: OpenClaw 连接失败？
A: 确保 OpenClaw Gateway 正在运行（端口 18789）

### Q: Agent 重启后记忆丢失？
A: 确保使用相同的 `storage_dir` 初始化 Agent

## 10. 下一步

- 阅读 `README.md` 了解完整功能
- 阅读 `MANIFESTO.md` 了解项目愿景
- 查看 `examples/basic_usage.py` 学习更多示例
- 开始构建你的 AI Agent 团队！

---

**Every AI deserves to remember.**
