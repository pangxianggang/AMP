"""
AMP OpenClaw Integration - 深度集成 OpenClaw 系统

实现 AMP 与 OpenClaw 的深度集成：
- 使用 OpenClaw sessions_spawn 创建子代理
- 使用 cron 系统进行记忆巩固调度
- 使用 message 系统进行通知
- 使用 serper/github 等技能
- 集成 HEARTBEAT.md 心跳检查

OpenClaw API:
- POST /sessions/spawn - 创建子代理
- POST /cron/add - 添加定时任务
- POST /message/send - 发送消息
- GET /memory/search - 搜索记忆
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import json

from amp.memory import Memory, MemoryType

logger = logging.getLogger(__name__)


@dataclass
class OpenClawConfig:
    """OpenClaw 配置"""
    gateway_url: str = "http://localhost:18789"
    workspace_dir: str = "~/.openclaw/workspace"
    skills_dir: str = "~/.openclaw/workspace/skills"
    timeout: int = 60


class OpenClawIntegration:
    """
    OpenClaw 深度集成

    提供 AMP 与 OpenClaw 系统的双向集成能力。

    Features:
    - 创建 AMP Agent 作为 OpenClaw 子代理
    - 派生子代理执行任务
    - 使用 OpenClaw 技能系统
    - 集成 cron 定时任务
    - 消息路由和通知
    - HEARTBEAT.md 心跳检查

    Example:
        oc = OpenClawIntegration()

        # 创建 Agent
        agent = await oc.create_agent("Ali", "project_manager")

        # 派生子代理执行任务
        result = await oc.spawn_subagent(
            name="研究员",
            role="researcher",
            task={"description": "研究 AI 框架"}
        )

        # 使用技能
        search_result = await oc.use_skill("serper", query="Python 异步编程")
    """

    # 技能脚本路径映射表
    SKILL_SCRIPTS = {
        "serper": "scripts/search.py",
        "github": "scripts/run.py",
        "weather": "scripts/run.py",
        "coding-agent": "scripts/run.py",
    }

    def __init__(self, config: Optional[OpenClawConfig] = None):
        self.config = config or OpenClawConfig()
        self._session = None
        logger.info(f"OpenClawIntegration initialized: {self.config.gateway_url}")

    async def _get_session(self):
        """获取 aiohttp session"""
        if self._session is None:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession()
            except ImportError:
                logger.warning("aiohttp not installed, OpenClaw integration disabled")
                return None
        return self._session

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None

    async def create_agent(
        self,
        name: str,
        role: str,
        language: str = "zh",
        capabilities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        在 OpenClaw 中创建 AMP Agent
        
        Args:
            name: Agent 名称
            role: Agent 角色
            language: 语言
            capabilities: 能力列表
            
        Returns:
            Agent 信息
        """
        try:
            session = await self._get_session()
            if not session:
                return {"status": "error", "message": "aiohttp not available"}
            
            # 使用 OpenClaw 的 sessions_spawn API
            payload = {
                "name": name,
                "role": role,
                "config": {
                    "language": language,
                    "capabilities": capabilities or [],
                    "amp_enabled": True,
                }
            }
            
            async with session.post(
                f"{self.config.gateway_url}/sessions/spawn",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"Created OpenClaw agent: {name} ({role})")
                    return {
                        "status": "success",
                        "agent_id": data.get("session_id", ""),
                        "name": name,
                        "role": role,
                    }
                else:
                    error_text = await resp.text()
                    logger.warning(f"Failed to create agent: {resp.status} - {error_text}")
                    return {"status": "error", "code": resp.status, "message": error_text}
                    
        except Exception as e:
            logger.error(f"OpenClaw create agent failed: {e}")
            return {"status": "error", "message": str(e)}

    async def spawn_subagent(
        self,
        name: str,
        role: str,
        task: Dict[str, Any],
        parent_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        派生子代理执行任务
        
        Args:
            name: 子代理名称
            role: 子代理角色
            task: 任务描述
            parent_agent_id: 父 Agent ID
            
        Returns:
            执行结果
        """
        try:
            session = await self._get_session()
            if not session:
                return {"status": "error", "message": "aiohttp not available"}
            
            payload = {
                "name": name,
                "role": role,
                "task": task,
                "parent_id": parent_agent_id,
                "config": {
                    "amp_enabled": True,
                    "auto_sync_memory": True,
                }
            }
            
            async with session.post(
                f"{self.config.gateway_url}/sessions/spawn",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"Spawned subagent {name} for task: {task.get('description', '')[:50]}...")
                    
                    # 等待任务完成（轮询）
                    session_id = data.get("session_id")
                    if session_id:
                        return await self._wait_for_task_completion(session_id)
                    
                    return data
                else:
                    error_text = await resp.text()
                    logger.warning(f"Failed to spawn subagent: {resp.status}")
                    return {"status": "error", "code": resp.status, "message": error_text}
                    
        except Exception as e:
            logger.error(f"OpenClaw spawn subagent failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _wait_for_task_completion(
        self,
        session_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """等待任务完成"""
        import asyncio
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                session = await self._get_session()
                if not session:
                    break
                
                async with session.get(
                    f"{self.config.gateway_url}/sessions/{session_id}/status",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get("status")
                        
                        if status == "completed":
                            return {
                                "status": "completed",
                                "session_id": session_id,
                                "result": data.get("result"),
                            }
                        elif status == "failed":
                            return {
                                "status": "failed",
                                "session_id": session_id,
                                "error": data.get("error"),
                            }
            except Exception as e:
                logger.debug(f"Polling status failed: {e}")
            
            await asyncio.sleep(poll_interval)
        
        return {
            "status": "timeout",
            "session_id": session_id,
            "message": f"Task did not complete within {timeout}s",
        }

    async def use_skill(
        self,
        skill_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        使用 OpenClaw 技能

        Args:
            skill_name: 技能名称 (如 "serper", "github", "weather")
            **kwargs: 技能参数

        Returns:
            技能执行结果

        Raises:
            SkillNotFoundError: 技能脚本不存在
            SkillTimeoutError: 技能执行超时
            SkillExecutionError: 技能执行失败
        """
        try:
            # 技能通过执行脚本调用
            import subprocess

            # 使用技能脚本映射表获取正确的路径
            script_name = self.SKILL_SCRIPTS.get(skill_name, "scripts/run.py")
            skill_script = f"{self.config.skills_dir}/{skill_name}/{script_name}"
            skill_path = Path(skill_script).expanduser()

            # 检查技能脚本是否存在
            if not skill_path.exists():
                logger.error(f"Skill script not found: {skill_script}")
                return {
                    "status": "error",
                    "error_type": "SkillNotFoundError",
                    "skill": skill_name,
                    "message": f"Skill '{skill_name}' not found. Script path: {skill_script}",
                    "hint": f"Please install the skill or check the skills directory: {self.config.skills_dir}"
                }

            cmd = ["python", str(skill_path)]
            for key, value in kwargs.items():
                cmd.extend([f"--{key}", str(value)])

            logger.info(f"Executing skill: {skill_name}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 秒超时
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                logger.info(f"Skill {skill_name} executed successfully")
                return {
                    "status": "success",
                    "skill": skill_name,
                    "result": result.stdout,
                }
            else:
                logger.warning(f"Skill {skill_name} failed: {result.stderr}")
                return {
                    "status": "error",
                    "error_type": "SkillExecutionError",
                    "skill": skill_name,
                    "error": result.stderr,
                    "stdout": result.stdout,
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Skill {skill_name} timed out")
            return {
                "status": "error",
                "error_type": "SkillTimeoutError",
                "skill": skill_name,
                "message": "Skill execution timed out after 60 seconds",
            }
        except FileNotFoundError:
            logger.error(f"Python interpreter not found or skill script not executable")
            return {
                "status": "error",
                "error_type": "SkillExecutionError",
                "skill": skill_name,
                "message": "Failed to execute skill script. Please check Python installation.",
            }
        except PermissionError as e:
            logger.error(f"Permission denied for skill {skill_name}: {e}")
            return {
                "status": "error",
                "error_type": "SkillPermissionError",
                "skill": skill_name,
                "message": f"Permission denied: {e}",
            }
        except Exception as e:
            logger.error(f"OpenClaw use skill failed: {e}")
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "skill": skill_name,
                "message": str(e),
            }

    async def add_cron_task(
        self,
        name: str,
        schedule: str,  # cron 表达式
        handler: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        添加定时任务（用于记忆巩固等）
        
        Args:
            name: 任务名称
            schedule: cron 表达式 (如 "0 3 * * *" 每天凌晨 3 点)
            handler: 处理函数名称
            params: 任务参数
            
        Returns:
            是否成功
        """
        try:
            session = await self._get_session()
            if not session:
                return False
            
            payload = {
                "name": name,
                "schedule": schedule,
                "handler": handler,
                "params": params or {},
                "enabled": True,
            }
            
            async with session.post(
                f"{self.config.gateway_url}/cron/add",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Added cron task: {name} ({schedule})")
                    return True
                else:
                    logger.warning(f"Failed to add cron task: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.debug(f"OpenClaw add cron task failed: {e}")
            return False

    async def send_message(
        self,
        to: str,
        content: str,
        message_type: str = "notification",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        发送消息（用于 Agent 间通知）
        
        Args:
            to: 接收者
            content: 消息内容
            message_type: 消息类型
            metadata: 元数据
            
        Returns:
            是否成功
        """
        try:
            session = await self._get_session()
            if not session:
                return False
            
            payload = {
                "to": to,
                "content": content,
                "type": message_type,
                "metadata": metadata or {},
            }
            
            async with session.post(
                f"{self.config.gateway_url}/message/send",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.debug(f"Sent message to {to}")
                    return True
                else:
                    logger.warning(f"Failed to send message: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.debug(f"OpenClaw send message failed: {e}")
            return False

    async def update_heartbeat(
        self,
        task_name: str,
        status: str = "ok",
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新 HEARTBEAT.md
        
        Args:
            task_name: 任务名称
            status: 状态 ("ok", "warning", "error")
            details: 详细信息
            
        Returns:
            是否成功
        """
        try:
            heartbeat_path = Path(self.config.workspace_dir).expanduser() / "HEARTBEAT.md"
            
            content = f"""# HEARTBEAT.md

## Last Update: {datetime.now().isoformat()}

### {task_name}
- **Status**: {status}
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            if details:
                content += "\n### Details\n"
                for key, value in details.items():
                    content += f"- **{key}**: {value}\n"
            
            heartbeat_path.write_text(content, encoding='utf-8')
            logger.debug(f"Updated HEARTBEAT.md: {task_name} = {status}")
            return True
            
        except Exception as e:
            logger.debug(f"Update heartbeat failed: {e}")
            return False

    async def search_memory(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        搜索 OpenClaw MEMORY.md 中的记忆
        
        Args:
            query: 搜索查询
            agent_id: Agent ID 过滤
            limit: 结果数量
            
        Returns:
            记忆列表
        """
        try:
            # 读取 MEMORY.md 并搜索
            memory_path = Path(self.config.workspace_dir).expanduser() / "MEMORY.md"
            
            if not memory_path.exists():
                return []
            
            content = memory_path.read_text(encoding='utf-8')
            
            # 简单关键字搜索（v1.0）
            # v2.0 可以使用向量搜索
            results = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if query.lower() in line.lower():
                    # 获取上下文
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    results.append({
                        "content": line.strip(),
                        "context": context,
                        "line": i + 1,
                    })
                    
                    if len(results) >= limit:
                        break
            
            logger.info(f"Found {len(results)} memories for query: {query}")
            return results
            
        except Exception as e:
            logger.debug(f"OpenClaw search memory failed: {e}")
            return []

    async def sync_to_memory_bank(
        self,
        agent_id: str,
        memories: List[Memory],
    ) -> Dict[str, int]:
        """
        同步 AMP 记忆到 Memory Bank
        
        Args:
            agent_id: Agent ID
            memories: 记忆列表
            
        Returns:
            同步统计
        """
        # 复用 MemoryBankIntegration
        from amp.memory_bank import MemoryBankIntegration
        
        mb = MemoryBankIntegration()
        stats = await mb.sync_agent_to_bank(agent_id, memories)
        await mb.close()
        
        return stats

    async def load_from_memory_bank(
        self,
        agent_id: str,
        topic: Optional[str] = None,
    ) -> List[Memory]:
        """
        从 Memory Bank 加载记忆到 AMP

        Args:
            agent_id: Agent ID
            topic: 主题过滤

        Returns:
            记忆列表
        """
        from amp.memory_bank import MemoryBankIntegration
        from amp.memory import Memory, MemoryType

        mb = MemoryBankIntegration()

        # 使用 search_memories 方法替代 load_user_preferences
        search_query = topic or "用户偏好 配置 习惯"
        memories_data = await mb.search_memories(
            query=search_query,
            agent_id=agent_id,
            limit=20
        )

        # 将字典转换为 Memory 对象
        memories = []
        for item in memories_data:
            memory = Memory(
                id=item.get("id", ""),
                type=MemoryType(item.get("memory_type", "semantic")),
                content=item.get("content", ""),
                created_at=item.get("created_at", datetime.now().isoformat()),
                importance=item.get("importance", 5),
                tags=item.get("tags", []),
                emotion=item.get("emotion", "neutral"),
            )
            memories.append(memory)

        await mb.close()
        logger.info(f"📥 Loaded {len(memories)} memories from Memory Bank")
        return memories
