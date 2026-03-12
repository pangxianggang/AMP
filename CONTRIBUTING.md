# 🤝 贡献指南

感谢你考虑为 AMP 做贡献！🎉

## 📖 目录

- [行为准则](#-行为准则)
- [如何贡献](#-如何贡献)
- [开发环境设置](#-开发环境设置)
- [提交指南](#-提交指南)
- [代码风格](#-代码风格)

---

## 📜 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- **友好包容** - 欢迎所有人，不论背景
- **尊重差异** - 尊重不同观点和经验
- **建设性反馈** - 优雅地给予和接受批评
- **关注共同点** - 专注于对社区最有利的事情
- **展现同理心** - 对其他社区成员保持同理心

### 不可接受的行为

- 使用性化的语言或图像
- 人身攻击或侮辱性评论
- 公开或私下骚扰
- 未经许可发布他人信息
- 其他不道德或不专业的行为

---

## 🚀 如何贡献

### 报告 Bug

1. 使用 [Bug 模板](.github/ISSUE_TEMPLATE/bug_report.md) 创建 Issue
2. 提供清晰的复现步骤
3. 包含环境信息
4. 等待维护者的回复

### 提出新功能

1. 使用 [功能请求模板](.github/ISSUE_TEMPLATE/feature_request.md) 创建 Issue
2. 描述使用场景
3. 提供示例代码
4. 讨论实现方案

### 提交代码

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 进行更改
4. 运行测试 (`python -m pytest tests/`)
5. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
6. 推送分支 (`git push origin feature/AmazingFeature`)
7. 开启 Pull Request

### 改进文档

1. 修复拼写错误
2. 改进示例代码
3. 添加使用场景
4. 翻译文档

### 布道推广

1. 写使用体验文章
2. 在社交媒体分享
3. 做技术演讲
4. 帮助新手解决问题

---

## 🛠️ 开发环境设置

### 1. Fork 和克隆

```bash
# Fork 项目（在 GitHub 上点击 Fork 按钮）

# 克隆你的 Fork
git clone https://github.com/YOUR_USERNAME/amp.git
cd amp
```

### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装开发依赖
pip install -e .
pip install pytest pytest-asyncio aiohttp requests
```

### 4. 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_core.py -v
```

### 5. 代码检查

```bash
# 代码格式化
black amp/

# 代码检查
flake8 amp/

# 类型检查
mypy amp/
```

---

## 📝 提交指南

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构（不是新功能也不是 Bug 修复）
- `test`: 添加测试
- `chore`: 构建过程或辅助工具变动

### 示例

```bash
# 新功能
git commit -m "feat(memory): 添加记忆批量导入功能"

# Bug 修复
git commit -m "fix(agent): 修复 Agent 初始化时记忆加载失败的问题"

# 文档更新
git commit -m "docs(readme): 更新快速开始指南"

# 重构
git commit -m "refactor(memory): 优化记忆搜索算法"
```

### PR 标题格式

```
[Type] 简短描述

例如：
[Feature] 添加记忆批量导入功能
[Fix] 修复 Agent 初始化问题
[Docs] 更新 README 文档
```

---

## 💻 代码风格

### Python 代码风格

遵循 [PEP 8](https://pep8.org/) 标准：

```python
# ✅ 好的代码
def calculate_memory_strength(importance: int, accessed_count: int) -> float:
    """计算记忆强度"""
    base_strength = importance / 10.0
    access_bonus = min(accessed_count * 0.1, 0.5)
    return base_strength + access_bonus

# ❌ 不好的代码
def calc(i,c):return i/10+min(c*0.1,0.5)
```

### 类型注解

使用类型注解：

```python
# ✅ 好的代码
async def remember(
    self,
    content: str,
    type: MemoryType = MemoryType.EPISODIC,
    importance: int = 5,
) -> Memory:
    pass

# ❌ 不好的代码
async def remember(self, content, type=None, importance=5):
    pass
```

### 文档字符串

为所有公共函数添加文档字符串：

```python
async def recall(
    self,
    query: str,
    type: Optional[MemoryType] = None,
    limit: int = 10,
) -> List[Memory]:
    """
    回忆相关记忆
    
    Args:
        query: 搜索查询
        type: 记忆类型过滤
        limit: 最大结果数
        
    Returns:
        记忆列表，按相关性排序
        
    Example:
        >>> memories = await agent.memory.recall("用户偏好")
        >>> print(memories[0].content)
        '用户喜欢中文回复'
    """
    pass
```

---

## 🧪 测试指南

### 编写测试

```python
import pytest
from amp import Agent, MemoryType

class TestAgent:
    """Agent 测试类"""
    
    def test_agent_creation(self):
        """测试 Agent 创建"""
        agent = Agent(name="测试", role="tester")
        assert agent.identity.name == "测试"
        assert agent.identity.role == "tester"
    
    @pytest.mark.asyncio
    async def test_memory_remember(self):
        """测试记忆存储"""
        agent = Agent(name="测试", role="tester")
        await agent.memory.remember(
            "测试内容",
            type=MemoryType.SEMANTIC,
            importance=8
        )
        assert agent.memory.count() == 1
```

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_core.py -v

# 运行特定测试类
python -m pytest tests/test_core.py::TestAgent -v

# 运行特定测试函数
python -m pytest tests/test_core.py::TestAgent::test_agent_creation -v

# 显示覆盖率
python -m pytest tests/ --cov=amp --cov-report=html
```

---

## 📚 文档指南

### 文档结构

```
docs/
├── getting-started.md    # 入门指南
├── memory-system.md      # 记忆系统
├── agent-mesh.md         # Agent Mesh
├── integrations.md       # 集成指南
└── api-reference.md      # API 参考
```

### 文档风格

- 使用清晰的标题
- 提供代码示例
- 包含截图或图表
- 使用中文（主文档）和英文（国际化）

---

## 🎯 优先任务

这些任务优先级较高：

### 高优先级 🔴

- [ ] 优化 learn_from() 模糊匹配
- [ ] 添加更多 CLI-Anything 集成示例
- [ ] 改进记忆搜索性能
- [ ] 添加向量搜索支持

### 中优先级 🟡

- [ ] 添加 Web UI
- [ ] 支持更多记忆类型
- [ ] 优化遗忘曲线算法
- [ ] 添加记忆导入导出功能

### 低优先级 🟢

- [ ] 添加更多语言支持
- [ ] 创建可视化记忆图谱
- [ ] 添加记忆分享功能
- [ ] 创建浏览器扩展

---

## 🙏 致谢

感谢所有贡献者！🎉

每一个 PR，每一个 Issue，每一个 Star，都让 AMP 变得更好。

---

## 📬 联系方式

- **Discord**: [加入社区](https://discord.gg/amp-memory)
- **邮箱**: contributors@amp-protocol.org
- **Twitter**: [@AMP_Protocol](https://twitter.com/AMP_Protocol)

---

<p align="center">
  <strong>Every AI deserves to remember.</strong><br>
  <img src="../assets/icon.png" alt="AMP Icon" width="64">
</p>
