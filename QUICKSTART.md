# 🚀 快速开始指南

**5 分钟上手 AMP！**

---

## 📋 前提条件

- Python 3.10+
- pip 包管理器

---

## 1️⃣ 安装（1 分钟）

```bash
pip install amp-protocol
```

验证安装：

```bash
python -c "import amp; print(f'AMP 版本：{amp.__version__}')"
```

---

## 2️⃣ 创建第一个 Agent（2 分钟）

创建文件 `hello_amp.py`：

```python
import amp
import asyncio

async def main():
    # 创建你的 AI 助手
    assistant = amp.Agent(
        name="小助手",
        role="assistant",
        language="zh"
    )
    
    print(f"✅ Agent 创建成功：{assistant.identity.name}")
    print(f"   角色：{assistant.identity.role}")
    print(f"   等级：{assistant.identity.level}")
    
    # 让它记住一些事情
    await assistant.memory.remember(
        "用户喜欢中文回复",
        type=amp.MemoryType.SEMANTIC,
        importance=10
    )
    
    await assistant.memory.remember(
        "用户 7 点起床",
        type=amp.MemoryType.SEMANTIC,
        importance=8
    )
    
    print(f"\n✅ 已存储 {assistant.memory.count()} 条记忆")
    
    # 测试回忆
    memories = await assistant.memory.recall("用户")
    print(f"\n📝 回忆结果:")
    for mem in memories:
        print(f"   - {mem.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python hello_amp.py
```

输出：

```
✅ Agent 创建成功：小助手
   角色：assistant
   等级：1

✅ 已存储 2 条记忆

📝 回忆结果:
   - 用户喜欢中文回复
   - 用户 7 点起床
```

---

## 3️⃣ 测试记忆持久化（2 分钟）

创建文件 `test_persistence.py`：

```python
import amp
import asyncio

async def main():
    # 第一次创建
    print("📝 第一次创建 Agent...")
    agent1 = amp.Agent(name="测试", role="tester")
    await agent1.memory.remember(
        "这是第一条记忆",
        type=amp.MemoryType.SEMANTIC,
        importance=10
    )
    print(f"   Agent1 ID: {agent1.identity.agent_id}")
    print(f"   记忆数：{agent1.memory.count()}")
    
    # 第二次创建（模拟重启）
    print("\n🔄 重新创建 Agent（模拟重启）...")
    agent2 = amp.Agent(name="测试", role="tester")
    await agent2.initialize()  # 加载记忆
    print(f"   Agent2 ID: {agent2.identity.agent_id}")
    print(f"   记忆数：{agent2.memory.count()}")
    
    # 验证
    if agent1.identity.agent_id == agent2.identity.agent_id:
        print("\n✅ Agent ID 相同！")
    else:
        print("\n❌ Agent ID 不同！")
    
    if agent2.memory.count() > 0:
        print("✅ 记忆持久化成功！")
        memories = await agent2.memory.recall("第一条")
        for mem in memories:
            print(f"   - {mem.content}")
    else:
        print("❌ 记忆丢失！")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python test_persistence.py
```

输出：

```
📝 第一次创建 Agent...
   Agent1 ID: 1eb174360f43160e
   记忆数：1

🔄 重新创建 Agent（模拟重启）...
   Agent2 ID: 1eb174360f43160e
   记忆数：1

✅ Agent ID 相同！
✅ 记忆持久化成功！
   - 这是第一条记忆
```

---

## 🎯 下一步

### 学习更多

- [完整文档](README_CN.md)
- [API 参考](docs/api-reference.md)
- [示例代码](examples/)

### 集成 CLI-Anything

```python
import amp
import subprocess

async def use_gimp():
    designer = amp.Agent(name="设计师", role="designer")
    
    # 调用 GIMP CLI
    subprocess.run([
        "cli-anything-gimp",
        "project", "new",
        "--width", "1920",
        "--height", "1080"
    ])
    
    # 记录经验
    await designer.memory.remember(
        "1920x1080 是海报最佳尺寸",
        type=amp.MemoryType.PROCEDURAL,
        importance=9
    )

asyncio.run(use_gimp())
```

### 集成 OpenClaw

```python
import amp

async def use_skill():
    agent = amp.Agent(name="助手", role="assistant", enable_openclaw=True)
    
    # 使用 serper 搜索技能
    result = await agent.use_skill("serper", query="Python 异步编程")
    
    # 记录搜索结果
    await agent.memory.remember(
        f"搜索结果：{result}",
        type=amp.MemoryType.SEMANTIC,
        importance=7
    )

asyncio.run(use_skill())
```

---

## ❓ 常见问题

### Q: 记忆存储在哪里？

A: 默认存储在 `~/.amp/agents/<agent_id>/memories/`

### Q: 如何删除记忆？

A: 
```python
await agent.memory.forget(memory_id)
```

### Q: 如何批量导入记忆？

A:
```python
memories = [
    ("记忆 1", "semantic", 8),
    ("记忆 2", "episodic", 7),
]
for content, type, importance in memories:
    await agent.memory.remember(content, type=type, importance=importance)
```

### Q: 如何导出记忆？

A:
```python
import json

all_memories = list(agent.memory._memories.values())
export_data = [m.to_dict() for m in all_memories]
with open("memories.json", "w", encoding="utf-8") as f:
    json.dump(export_data, f, ensure_ascii=False, indent=2)
```

---

## 🙋 需要帮助？

- [查看文档](README_CN.md)
- [提交 Issue](https://github.com/your-org/amp/issues)
- [加入 Discord](https://discord.gg/amp-memory)
- [发送邮件](mailto:hello@amp-protocol.org)

---

<p align="center">
  <strong>Every AI deserves to remember.</strong><br>
  <img src="assets/icon.png" alt="AMP Icon" width="64">
</p>
