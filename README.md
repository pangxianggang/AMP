<div align="center">

# ⚡ AMP — Agent Memory Protocol

### 🧠 让 AI 拥有记忆，让 Agent 真正成长

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**English** · [简体中文](README_CN.md)

</div>

---

## 🔍 什么是 AMP?

AMP (Agent Memory Protocol) 是一个开放的记忆协议标准，为 AI Agent 提供**长期记忆**、**从错误学习**、**持续成长**的能力。

### 为什么需要 AMP?

| ❌ 当前 AI 的困境 | ✅ AMP 的解决方案 |
|------------------|------------------|
| 每次对话都是初次见面 | 🧠 持久化记忆，AI 记住每个用户 |
| 无法从错误中学习 | 📈 情感记忆记录成功/失败经验 |
| 经验无法积累和传承 | 🎮 XP/等级系统，AI 不断成长 |
| 多个 AI 之间信息孤岛 | 🕸️ Agent Mesh，知识共享传承 |

---

## ✨ 核心特性

- **🧠 四种记忆类型** — 情景、语义、程序、情感，模拟人类认知科学
- **📈 成长系统** — XP 经验值 + 等级晋升，越用越强
- **⏳ 遗忘曲线** — 基于艾宾浩斯遗忘曲线，自然管理记忆强度
- **🔗 多 Agent 协作** — Agent Mesh 网络，知识共享与传承
- **⚡ 高性能** — 本地存储，响应延迟 < 0.02ms
- **🔒 数据安全** — 隐私优先，数据不离开本地

---

## 🚀 快速开始

### 安装

```bash
# 从 PyPI 安装
pip install amp-protocol

# 或从源码安装
git clone https://github.com/pangxianggang/AMP.git
cd AMP/sdk/python
pip install -e .
```

### 创建你的第一个 Agent

```python
import asyncio
from amp import Agent, MemoryType

async def main():
    agent = Agent(name="Ali", role="project_manager", language="zh")

    # 存储记忆
    await agent.memory.remember(
        "用户喜欢中文回复",
        type=MemoryType.SEMANTIC,
        importance=8
    )

    # 回忆
    memories = await agent.memory.recall("用户偏好")
    print(f"记忆：{memories[0].content}")

    # 执行任务
    result = await agent.act({"description": "规划项目结构"})
    print(f"任务结果：{result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 运行测试

```bash
cd tests
python -m pytest
```

---

## 🧠 记忆系统

AMP 的记忆系统受人类认知科学启发，设计了四种记忆类型：

| 类型 | 名称 | 说明 | 示例 |
|------|------|------|------|
| 📖 | **情景记忆** (Episodic) | 记录事件和经历 | "与用户讨论了 AMP 架构设计" |
| 💡 | **语义记忆** (Semantic) | 存储事实和概念 | "用户偏好直接高效的沟通风格" |
| 🔧 | **程序记忆** (Procedural) | 技能和操作方法 | "部署流程：安装 → 配置 → 启动" |
| ❤️ | **情感记忆** (Emotional) | 带价值的经验 | "异步方案显著提升了性能 ✅" |

### 遗忘曲线

记忆强度遵循**艾宾浩斯遗忘曲线**，支持记忆巩固：

```python
# 记忆巩固（类似人类睡眠）
await agent.sleep()  # 整理记忆，强化重要的，淡化琐碎的
```

---

## 🤝 多 Agent 协作

```python
import asyncio
from amp import Agent, AgentMesh

async def team_work():
    researcher = Agent(name="Researcher", role="researcher")
    writer = Agent(name="Writer", role="writer")

    mesh = AgentMesh()
    await mesh.register(researcher)
    await mesh.register(writer)

    # 团队协作
    result = await mesh.team_task(
        task={"description": "Research AI frameworks", "importance": 8},
        agents=[researcher, writer]
    )

    # 知识传承
    await writer.learn_from(researcher, topic="AI frameworks")

asyncio.run(team_work())
```

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│                    用户层                             │
└─────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────┐
│           AMP (Agent Memory Protocol)                │
│  Agent Identity │ 4 Memory Types │ Agent Mesh │ Ebbinghaus │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │  Storage  │   │ Memory   │   │   CLI-    │         │
│  │ (JSON/DB) │   │ (Vector) │   │ Anything │         │
│  └──────────┘   └──────────┘   └──────────┘         │
└─────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
AMP/
├── protocol/              # 协议规范
│   ├── spec/              # 规范文档
│   └── schemas/           # JSON Schema
├── sdk/python/amp/        # Python SDK
│   ├── agent.py           # Agent 核心
│   ├── memory.py          # 记忆系统
│   ├── mesh.py            # Agent Mesh
│   └── ...
├── integrations/          # 集成模块
├── config/                # 配置文件
├── tests/                 # 测试套件
├── docs/                  # 文档 & 网站
├── examples/              # 示例代码
├── LICENSE                # MIT
└── README.md
```

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📄 License

[MIT](LICENSE) © 2026 pangxianggang

---

<div align="center">

**Every AI deserves to remember.**

</div>
