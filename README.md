# AMP v2.0 — Agent Memory Protocol

> 零依赖的 AI Agent 记忆协议，让 AI 拥有像人一样的记忆系统。

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)

## 为什么需要 AMP？

当前 AI Agent 面临一个根本问题：**没有真正的记忆**。每次对话结束，一切都忘记了。

ChatGPT 有 Memory 功能，但它锁在 OpenAI 的生态里。LangChain 有 Memory 模块，但它需要向量数据库、Embedding 模型等一堆依赖。

**AMP 的做法不同：**

- **零外部依赖** — 纯 Python 标准库，复制就能用
- **认知科学基础** — 工作记忆 / 短期记忆 / 长期记忆三层架构
- **质量保证** — 新记忆默认不可信，通过验证才能晋升
- **标准化格式** — `.amp` 文件让记忆可以在不同 Agent 之间迁移

## 快速开始

```python
import asyncio
from amp import Agent, MemoryType

async def main():
    # 创建 Agent（自动持久化到 ~/.amp/）
    agent = Agent(name="Ali", role="project_manager")

    # 记住信息
    await agent.remember(
        "用户偏好中文沟通",
        type=MemoryType.SEMANTIC,
        importance=8
    )

    # 回忆
    memories = await agent.recall("用户偏好")
    for m in memories:
        print(f"[{m.tier.value}] {m.content}")

    # 导出记忆（可迁移到其他 Agent）
    agent.memory.export("ali_knowledge.amp")

    # Agent 会自动成长
    await agent.act({"description": "完成任务"})
    print(f"Level: {agent.identity.level}, XP: {agent.identity.experience_points}")

asyncio.run(main())
```

## 核心特性

### 1. 记忆分层

模仿人类认知系统：

| 层级 | 容量 | TTL | 晋升条件 |
|------|------|-----|----------|
| 工作记忆 (Working) | 10 条 | 1 小时 | importance ≥ 6 |
| 短期记忆 (Short-term) | 100 条 | 7 天 | importance ≥ 8 或访问 ≥ 5 次 |
| 长期记忆 (Long-term) | 无限 | 永久 | — |

### 2. 记忆质量保证

新记忆不是直接可信的。它们以「候选」状态进入系统 (confidence=0.50)，必须通过使用验证：

```
0.50 (候选) → 0.64 → 0.80 (已验证) → 0.92 (高可信) → 0.96 → 0.98
```

这防止了 AI 幻觉产生的假信息被当作事实。

**冲突检测**自动识别：
- 重复记忆（完全相同的内容）
- 替代记忆（新版本覆盖旧版本）
- 矛盾记忆（互相冲突的信息）

### 3. 认知遗忘

基于艾宾浩斯遗忘曲线，但做了改进：

```
strength = 重要性(0.4) + 访问频率(0.25) + 新近度(0.25) + 信心(0.1)
```

- 默认半衰期：14 天
- 重要且常访问的记忆保持高强度
- 不重要的记忆自然衰减、归档、删除
- 类似人类「睡眠巩固」的 `sleep()` 方法

### 4. 记忆可移植性

`.amp` 文件是标准化的记忆交换格式：

```python
# 导出
agent.memory.export("knowledge.amp", include_candidates=False)

# 导入（三种模式）
agent.memory.import_from("knowledge.amp", mode="candidate")  # 作为候选
agent.memory.import_from("knowledge.amp", mode="merge")      # 合并
agent.memory.import_from("knowledge.amp", mode="replace")    # 替换
```

### 5. 中英文搜索

无需 NLP 库，内置分词器：
- 中文：字符 bigram/trigram
- 英文：单词切分 + 停用词过滤
- 混合文本自动处理

### 6. Agent Mesh（多智能体协作）

```python
mesh = AgentMesh()
await mesh.register(researcher)
await mesh.register(writer)

# 知识共享（带质量保证）
await mesh.share_knowledge(researcher, [writer], topic="AI")

# 团队任务
await mesh.team_task({"description": "写研究报告"})
```

### 7. 四种记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| Episodic (情景) | 具体事件和经历 | "上次会议讨论了预算问题" |
| Semantic (语义) | 知识和事实 | "Python 3.12 新增了 type参数语法" |
| Procedural (程序) | 操作方法和技能 | "部署流程: build → test → deploy" |
| Emotional (情感) | 情感和偏好 | "用户对延迟交付感到不满" |

## 项目结构

```
amp/
├── __init__.py              # 版本 2.0.0，导出核心类
├── agent.py                 # Agent + AgentMemory
├── memory/
│   ├── types.py             # Memory/MemoryType/MemoryTier
│   ├── store.py             # JSON 文件存储
│   ├── recall.py            # 中英文搜索
│   ├── forgetting.py        # 艾宾浩斯遗忘曲线 v2
│   └── quality.py           # 质量保证 + 冲突检测
├── mesh/
│   └── __init__.py          # Agent Mesh 多智能体协作
└── export/
    ├── __init__.py
    └── json_export.py       # .amp 标准格式
tests/
└── test_all.py              # 61 项测试
```

## 与其他方案的对比

| 特性 | AMP | ChatGPT Memory | LangChain Memory | Mem0 | MemGPT |
|------|-----|----------------|------------------|------|--------|
| 零依赖 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 记忆分层 | ✅ | ❌ | 部分 | ❌ | ✅ |
| 质量保证 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 标准化导出 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 认知遗忘 | ✅ | ❌ | ❌ | ❌ | ✅ |
| 开源 | ✅ | ❌ | ✅ | ✅ | ✅ |
| 需要 GPU | ❌ | 云端 | 可选 | 可选 | 可选 |

## 本地测试

```bash
# 零安装，直接运行
python tests/test_all.py
```

测试覆盖：
- 数据模型与序列化
- 中英文分词器
- 艾宾浩斯遗忘曲线
- 质量检测与冲突识别
- Agent 创建与持久化
- 任务执行与 XP 升级
- 记忆分层与晋升
- 导出/导入 (.amp 格式)
- Agent Mesh 知识共享
- 记忆巩固（睡眠）

## 设计文档

- [协议规范](VISION.md)
- [快速入门](QUICKSTART.md)
- [贡献指南](CONTRIBUTING.md)

## 诚实声明

- ⭐ 0 stars — 这是一个真实的新项目
- 📦 尚未发布到 PyPI — 不能 `pip install`，需要手动复制
- 🔍 搜索是关键词匹配，不是向量搜索（可选扩展）
- 🧪 61 项测试全部通过，但还需要更多边界测试

## License

MIT License — 自由使用、修改和分发。
