"""
AMP Heartbeat - 心跳检查机制

集成 HEARTBEAT.md，实现定时任务调度和健康检查：
- 记忆巩固调度（每天凌晨 3 点）
- Memory Bank 同步（每小时）
- Agent 健康检查（每 30 分钟）

HEARTBEAT.md 格式:
```markdown
# HEARTBEAT.md

## Last Update: 2026-03-12T15:30:00

### memory_consolidation
- **Status**: ok
- **Timestamp**: 2026-03-12 03:00:00
- **Details**: Promoted=5, Decayed=12

### sync_with_memory_bank
- **Status**: ok
- **Timestamp**: 2026-03-12 15:00:00

### agent_health_check
- **Status**: ok
- **Timestamp**: 2026-03-12 15:30:00
```
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class HeartbeatTask:
    """心跳检查任务"""
    name: str
    schedule: str  # cron 表达式
    description: str
    enabled: bool = True
    last_run: Optional[str] = None
    last_status: str = "unknown"
    error_count: int = 0
    handler: Optional[Callable] = None  # 异步处理函数
    handler_args: Optional[Dict[str, Any]] = None  # handler 参数
    timeout: int = 300  # 任务超时时间（秒），默认 5 分钟


class HeartbeatManager:
    """
    心跳检查管理器
    
    管理定时任务调度，更新 HEARTBEAT.md
    
    Features:
    - cron 表达式调度
    - 任务状态追踪
    - 错误计数和告警
    - HEARTBEAT.md 持久化
    
    Example:
        heartbeat = HeartbeatManager(workspace="~/.openclaw/workspace")
        
        # 添加任务
        heartbeat.add_task("memory_consolidation", "0 3 * * *", consolidate_memories)
        
        # 启动调度器
        await heartbeat.start()
    """

    def __init__(
        self,
        workspace: str = "~/.openclaw/workspace",
        heartbeat_file: str = "HEARTBEAT.md",
    ):
        self.workspace = Path(workspace).expanduser()
        self.heartbeat_path = self.workspace / heartbeat_file
        self.tasks: Dict[str, HeartbeatTask] = {}
        self._running = False
        self._task_handles: Dict[str, asyncio.Task] = {}
        
        # 确保工作区存在
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # 加载现有任务
        self._load_heartbeat()
        
        logger.info(f"HeartbeatManager initialized: {self.heartbeat_path}")

    def _load_heartbeat(self) -> None:
        """加载 HEARTBEAT.md"""
        if not self.heartbeat_path.exists():
            logger.debug("HEARTBEAT.md not found, will create on first update")
            return
        
        try:
            content = self.heartbeat_path.read_text(encoding='utf-8')
            # 简单解析（v1.0）
            # v2.0 可以使用更完善的解析器
            lines = content.split('\n')
            
            current_task = None
            for line in lines:
                if line.startswith('### '):
                    task_name = line[4:].strip()
                    current_task = task_name
                elif current_task and '**Status**:' in line:
                    status = line.split(':')[1].strip()
                    if current_task in self.tasks:
                        self.tasks[current_task].last_status = status
                    else:
                        self.tasks[current_task] = HeartbeatTask(
                            name=current_task,
                            schedule="* * * * *",
                            description="",
                            last_status=status
                        )
            
            logger.debug(f"Loaded {len(self.tasks)} tasks from HEARTBEAT.md")
            
        except Exception as e:
            logger.warning(f"Failed to load HEARTBEAT.md: {e}")

    def _save_heartbeat(self) -> None:
        """保存 HEARTBEAT.md"""
        content = "# HEARTBEAT.md\n\n"
        content += f"## Last Update: {datetime.now().isoformat()}\n\n"
        
        for task in self.tasks.values():
            content += f"### {task.name}\n"
            content += f"- **Status**: {task.last_status}\n"
            if task.last_run:
                content += f"- **Timestamp**: {task.last_run}\n"
            if task.description:
                content += f"- **Description**: {task.description}\n"
            if task.error_count > 0:
                content += f"- **Errors**: {task.error_count}\n"
            content += "\n"
        
        self.heartbeat_path.write_text(content, encoding='utf-8')
        logger.debug(f"Updated HEARTBEAT.md")

    def add_task(
        self,
        name: str,
        schedule: str,
        handler: Optional[Callable] = None,
        description: str = "",
        handler_args: Optional[Dict[str, Any]] = None,
        timeout: int = 300,  # 任务超时时间（秒）
    ) -> None:
        """
        添加心跳检查任务

        Args:
            name: 任务名称
            schedule: cron 表达式
            handler: 异步处理函数（可选，可以后续添加）
            description: 任务描述
            handler_args: handler 函数的参数字典
            timeout: 任务超时时间（秒），默认 5 分钟

        Example:
            # 添加记忆巩固任务
            heartbeat.add_task(
                "memory_consolidation",
                "0 3 * * *",
                consolidate_memories,
                description="每天凌晨 3 点进行记忆巩固",
                handler_args={"agent": agent_instance},
                timeout=600  # 10 分钟超时
            )

            # 也可以先添加任务，后续再设置 handler
            heartbeat.add_task(
                "custom_task",
                "0 * * * *",
                description="自定义任务"
            )
        """
        self.tasks[name] = HeartbeatTask(
            name=name,
            schedule=schedule,
            description=description,
            enabled=True,
            handler=handler,
            handler_args=handler_args or {},
            timeout=timeout,
        )
        logger.info(f"Added heartbeat task: {name} ({schedule})")

    async def start(self) -> None:
        """启动心跳调度器"""
        self._running = True
        logger.info("Starting heartbeat scheduler...")
        
        for name, task in self.tasks.items():
            if task.enabled:
                handle = asyncio.create_task(self._run_task_loop(name, task))
                self._task_handles[name] = handle
        
        logger.info(f"Heartbeat scheduler started with {len(self.tasks)} tasks")

    async def stop(self) -> None:
        """停止心跳调度器"""
        self._running = False
        
        for name, handle in self._task_handles.items():
            handle.cancel()
            try:
                await handle
            except asyncio.CancelledError:
                pass
        
        self._task_handles.clear()
        logger.info("Heartbeat scheduler stopped")

    async def _run_task_loop(
        self,
        name: str,
        task: HeartbeatTask,
    ) -> None:
        """运行任务循环"""
        # 解析 cron 表达式（简化版）
        interval_seconds = self._cron_to_seconds(task.schedule)

        logger.info(f"Task '{name}' will run every {interval_seconds} seconds")

        while self._running:
            try:
                await asyncio.sleep(interval_seconds)

                if not task.enabled:
                    continue

                logger.debug(f"🔔 Running heartbeat task: {name}")

                # 更新状态
                task.last_status = "running"
                task.last_run = datetime.now().isoformat()
                self._save_heartbeat()

                # 执行实际的 handler，带超时控制
                if task.handler:
                    try:
                        # 支持异步和同步 handler
                        coro = task.handler(**task.handler_args) if task.handler_args else task.handler()
                        if asyncio.iscoroutine(coro):
                            # 使用 wait_for 添加超时控制
                            await asyncio.wait_for(coro, timeout=task.timeout)
                        else:
                            # 同步 handler，在线程池中运行以避免阻塞
                            await asyncio.get_event_loop().run_in_executor(None, task.handler)
                        logger.info(f"Heartbeat task '{name}' completed successfully")
                        task.last_status = "ok"
                    except asyncio.TimeoutError:
                        task.error_count += 1
                        task.last_status = f"error: timeout ({task.timeout}s)"
                        logger.error(f"Heartbeat task '{name}' timed out after {task.timeout}s")
                    except Exception as e:
                        task.error_count += 1
                        task.last_status = f"error: {e}"
                        logger.error(f"Heartbeat task '{name}' failed: {e}")

                self._save_heartbeat()

            except asyncio.CancelledError:
                break
            except Exception as e:
                task.error_count += 1
                task.last_status = f"error: {e}"
                logger.error(f"Heartbeat task '{name}' failed: {e}")
                self._save_heartbeat()

    def _cron_to_seconds(self, cron: str) -> int:
        """
        将 cron 表达式转换为秒数（简化版）
        
        支持的格式：
        - "0 3 * * *" -> 每天凌晨 3 点 -> 86400 秒
        - "0 * * * *" -> 每小时 -> 3600 秒
        - "*/30 * * * *" -> 每 30 分钟 -> 1800 秒
        - "* * * * *" -> 每分钟 -> 60 秒
        """
        parts = cron.split()
        if len(parts) != 5:
            logger.warning(f"Invalid cron expression: {cron}, using 3600s default")
            return 3600
        
        minute, hour, day, month, weekday = parts
        
        # 每分钟
        if minute == "*" and hour == "*":
            return 60
        
        # 每 N 分钟
        if minute.startswith("*/"):
            try:
                n = int(minute[2:])
                return n * 60
            except ValueError:
                pass
        
        # 每小时
        if minute == "0" and hour == "*":
            return 3600
        
        # 每天固定时间
        if minute != "*" and hour != "*" and day == "*":
            try:
                h = int(hour)
                m = int(minute)
                now = datetime.now()
                target = now.replace(hour=h, minute=m, second=0)
                if target < now:
                    target = target.replace(day=target.day + 1)
                return int((target - now).total_seconds())
            except ValueError:
                pass
        
        # 默认每小时
        return 3600

    async def run_task_now(self, name: str) -> bool:
        """
        立即运行指定任务

        Args:
            name: 任务名称

        Returns:
            是否成功
        """
        if name not in self.tasks:
            logger.error(f"Task '{name}' not found")
            return False

        task = self.tasks[name]
        task.last_status = "running"
        task.last_run = datetime.now().isoformat()
        self._save_heartbeat()

        try:
            # 执行实际的 handler，带超时控制
            if task.handler:
                try:
                    # 支持异步和同步 handler
                    result = task.handler(**task.handler_args) if task.handler_args else task.handler()
                    if asyncio.iscoroutine(result):
                        # 使用 wait_for 添加超时控制
                        await asyncio.wait_for(result, timeout=task.timeout)
                    else:
                        # 同步 handler，在线程池中运行
                        await asyncio.get_event_loop().run_in_executor(None, task.handler)
                    logger.info(f"Heartbeat task '{name}' completed successfully")
                    task.last_status = "ok"
                except asyncio.TimeoutError:
                    task.error_count += 1
                    task.last_status = f"error: timeout ({task.timeout}s)"
                    logger.error(f"Heartbeat task '{name}' timed out after {task.timeout}s")
                    raise
                except Exception as e:
                    task.error_count += 1
                    task.last_status = f"error: {e}"
                    logger.error(f"Heartbeat task '{name}' failed: {e}")
                    raise
            else:
                logger.warning(f"Task '{name}' has no handler configured")

            self._save_heartbeat()
            logger.info(f"Heartbeat task '{name}' completed")
            return True

        except Exception as e:
            task.last_status = f"error: {e}"
            task.error_count += 1
            self._save_heartbeat()
            logger.error(f"Heartbeat task '{name}' failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取心跳状态"""
        return {
            "running": self._running,
            "tasks": {
                name: {
                    "schedule": task.schedule,
                    "last_status": task.last_status,
                    "last_run": task.last_run,
                    "error_count": task.error_count,
                    "enabled": task.enabled,
                }
                for name, task in self.tasks.items()
            }
        }

    async def update_status(
        self,
        task_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        更新任务状态
        
        Args:
            task_name: 任务名称
            status: 状态 ("ok", "warning", "error")
            details: 详细信息
        """
        if task_name in self.tasks:
            task = self.tasks[task_name]
            task.last_status = status
            task.last_run = datetime.now().isoformat()
            
            if status == "error":
                task.error_count += 1
            
            self._save_heartbeat()
            logger.debug(f"Updated task '{task_name}' status: {status}")
