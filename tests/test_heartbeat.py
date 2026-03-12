"""
AMP Heartbeat 测试

运行方式:
    python -m pytest tests/test_heartbeat.py -v
"""

import asyncio
import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp.heartbeat import HeartbeatManager, HeartbeatTask


class TestHeartbeatTask:
    """测试 HeartbeatTask 数据类"""

    def test_create_task(self):
        """测试创建任务"""
        task = HeartbeatTask(
            name="test_task",
            schedule="0 * * * *",
            description="Test task"
        )

        assert task.name == "test_task"
        assert task.schedule == "0 * * * *"
        assert task.description == "Test task"
        assert task.enabled is True
        assert task.last_status == "unknown"
        assert task.error_count == 0
        assert task.timeout == 300  # 默认超时 5 分钟

    def test_task_with_timeout(self):
        """测试带超时的任务"""
        task = HeartbeatTask(
            name="long_task",
            schedule="0 3 * * *",
            description="Long running task",
            timeout=600  # 10 分钟超时
        )

        assert task.timeout == 600


class TestHeartbeatManager:
    """测试 HeartbeatManager"""

    @pytest.fixture
    def manager(self, tmp_path):
        """创建心跳管理器"""
        return HeartbeatManager(workspace=str(tmp_path))

    def test_create_manager(self, manager):
        """测试创建管理器"""
        assert manager.tasks == {}
        assert manager._running is False

    def test_add_task(self, manager):
        """测试添加任务"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="*/5 * * * *",
            handler=dummy_handler,
            description="Test task"
        )

        assert "test_task" in manager.tasks
        assert manager.tasks["test_task"].name == "test_task"
        assert manager.tasks["test_task"].schedule == "*/5 * * * *"

    def test_add_task_with_timeout(self, manager):
        """测试添加带超时的任务"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="long_task",
            schedule="0 3 * * *",
            handler=dummy_handler,
            timeout=600
        )

        assert manager.tasks["long_task"].timeout == 600

    def test_cron_to_seconds_every_minute(self, manager):
        """测试 cron 解析 - 每分钟"""
        seconds = manager._cron_to_seconds("* * * * *")
        assert seconds == 60

    def test_cron_to_seconds_every_hour(self, manager):
        """测试 cron 解析 - 每小时"""
        seconds = manager._cron_to_seconds("0 * * * *")
        assert seconds == 3600

    def test_cron_to_seconds_every_30_minutes(self, manager):
        """测试 cron 解析 - 每 30 分钟"""
        seconds = manager._cron_to_seconds("*/30 * * * *")
        assert seconds == 1800

    def test_cron_to_seconds_daily(self, manager):
        """测试 cron 解析 - 每天"""
        seconds = manager._cron_to_seconds("0 3 * * *")
        # 每天固定时间，返回到下一个执行点的秒数
        assert seconds > 0

    def test_cron_to_seconds_invalid(self, manager):
        """测试 cron 解析 - 无效表达式"""
        seconds = manager._cron_to_seconds("invalid")
        assert seconds == 3600  # 默认值

    def test_get_status(self, manager):
        """测试获取状态"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="* * * * *",
            handler=dummy_handler
        )

        status = manager.get_status()

        assert status["running"] is False
        assert "test_task" in status["tasks"]

    @pytest.mark.asyncio
    async def test_run_task_now(self, manager):
        """测试立即运行任务"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="* * * * *",
            handler=dummy_handler
        )

        result = await manager.run_task_now("test_task")
        assert result is True

    @pytest.mark.asyncio
    async def test_run_task_not_found(self, manager):
        """测试运行不存在的任务"""
        result = await manager.run_task_now("nonexistent_task")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_status(self, manager):
        """测试更新状态"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="* * * * *",
            handler=dummy_handler
        )

        await manager.update_status("test_task", "ok")
        assert manager.tasks["test_task"].last_status == "ok"

    @pytest.mark.asyncio
    async def test_update_status_error(self, manager):
        """测试更新错误状态"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="* * * * *",
            handler=dummy_handler
        )

        await manager.update_status("test_task", "error")
        assert manager.tasks["test_task"].last_status == "error"
        assert manager.tasks["test_task"].error_count >= 1

    @pytest.mark.asyncio
    async def test_start_stop(self, manager):
        """测试启动和停止"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="* * * * *",
            handler=dummy_handler
        )

        # 启动（不等待，因为会进入无限循环）
        await manager.start()
        assert manager._running is True

        # 立即停止
        await manager.stop()
        assert manager._running is False

    def test_heartbeat_file_creation(self, manager):
        """测试 HEARTBEAT.md 文件创建"""
        async def dummy_handler():
            pass

        manager.add_task(
            name="test_task",
            schedule="* * * * *",
            handler=dummy_handler
        )

        manager._save_heartbeat()

        assert manager.heartbeat_path.exists()


class TestHeartbeatIntegration:
    """测试 Heartbeat 集成场景"""

    @pytest.mark.asyncio
    async def test_task_timeout_handling(self, tmp_path):
        """测试任务超时处理"""
        manager = HeartbeatManager(workspace=str(tmp_path))

        # 创建一个会超时的异步 handler
        async def slow_handler():
            await asyncio.sleep(10)  # 10 秒

        manager.add_task(
            name="slow_task",
            schedule="* * * * *",
            handler=slow_handler,
            timeout=1  # 1 秒超时
        )

        # 使用 run_task_now 立即运行任务以测试超时
        result = await manager.run_task_now("slow_task")

        # 验证超时处理
        assert result is False
        assert manager.tasks["slow_task"].error_count >= 1
        # 验证任务状态为错误（可能是 timeout 或一般 error）
        assert manager.tasks["slow_task"].last_status.startswith("error")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
