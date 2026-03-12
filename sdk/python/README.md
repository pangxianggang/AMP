# AMP — Agent Memory Protocol

**The open protocol for AI agents that remember, learn, and collaborate.**

---

> *"An AI without memory is a calculator. An AI with memory is a colleague."*

---

## 🚀 快速开始

### 安装

```bash
cd "C:\Users\Administrator\Desktop\AMP 成品\sdk\python"
pip install -e .
```

### 创建你的第一个 Agent

```python
import amp
import asyncio

async def main():
    # 创建 Agent
    agent = amp.Agent(
        name="Ali",
        role="project_manager",
        language="zh"
    )

    # Agent 会记住
    await agent.memory.remember(
        "用户喜欢中文回复",
        type=amp.MemoryType.SEMANTIC,
        importance=8
    )

    # 下次会话仍然记得
    memories = await agent.memory.recall("用户偏好")
    print(memories)

    # 执行任务
    result = await agent.act({
        "description": "规划项目结构"
    })
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧠 记忆系统

AMP 的记忆系统受人类认知科学启发，设计了四种记忆类型：

| 记忆类型 | 说明 | 用途 | 示例 |
|---------|------|------|------|
| **情景记忆** (Episodic) | 发生了什么 | 记录事件和经历 | "2026-03-12 修复了连接问题" |
| **语义记忆** (Semantic) | 知道什么 | 存储事实和概念 | "用户喜欢中文回复" |
| **程序记忆** (Procedural) | 如何做 | 技能和操作方法 | "如何部署 FastAPI 应用" |
| **情感记忆** (Emotional) | 什么有效/无效 | 带价值的经验 | "这个方案用户很满意 (+)" |

---

## 🔗 与 OpenClaw 集成

```python
from amp.integrations.openclaw import OpenClawAMPBridge

async def openclaw_integration():
    bridge = OpenClawAMPBridge()
    agent = await bridge.create_agent("Ali", "project_manager")
    result = await bridge.spawn_subagent(
        name="助手",
        role="assistant",
        task={"description": "研究 Python 异步编程"}
    )
    return result
```

---

## 🔗 与 Memory Bank 集成

```python
from amp.integrations.memory_bank import MemoryBankIntegration

async def memory_bank_integration():
    mb = MemoryBankIntegration()
    await mb.save_conversation(
        agent=agent,
        messages=[...],
        summary="讨论了项目架构"
    )
    await mb.sync_agent_to_bank(agent)
```

---

## 📊 CLI 使用

```bash
# 初始化
amp init

# 创建 Agent
amp agent create Ali project_manager --lang zh

# 列出所有 Agent
amp agent list

# 搜索记忆
amp memory search "部署步骤"

# 记忆统计
amp memory stats

# 记忆巩固
amp memory consolidate

# 查看状态
amp status
```

---

## 📁 项目结构

```
AMP 成品/
├── protocol/              # 协议规范
│   ├── spec/             # 规范文档
│   └── schemas/          # JSON Schema
├── sdk/python/amp/       # Python SDK
│   ├── __init__.py
│   ├── agent.py          # Agent 核心
│   ├── memory.py         # 记忆系统
│   ├── mesh.py           # Agent Mesh
│   └── cli.py            # 命令行工具
├── integrations/
│   ├── openclaw/         # OpenClaw 集成
│   └── memory_bank/      # Memory Bank 集成
├── config/               # 配置文件
├── docs/                 # 文档
├── examples/             # 示例代码
└── tests/                # 测试
```

---

## 🛣️ 路线图

- [x] 协议规范
- [x] Agent 核心类
- [x] Memory 核心类
- [x] Mesh 网络
- [x] CLI 工具
- [x] OpenClaw 集成
- [x] Memory Bank 集成
- [ ] 向量搜索（语义相似度）
- [ ] LLM 集成（think 方法）
- [ ] PyPI 发布
- [ ] TypeScript SDK

---

**Every AI deserves to remember.**

*Agent Memory Protocol — Amplifying Intelligence Through Memory*
