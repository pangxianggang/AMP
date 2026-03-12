"""
AMP Config 测试

运行方式:
    python -m pytest tests/test_config.py -v
"""

import json
import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp.config import (
    AMPConfig,
    StorageConfig,
    OpenClawConfig,
    MemoryBankConfig,
    HeartbeatConfig,
    HeartbeatTaskConfig,
    load_config,
    get_config,
)


class TestStorageConfig:
    """测试 StorageConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = StorageConfig()

        assert config.backend == "local"
        assert config.enable_dry_run is True
        assert config.auto_commit is False
        assert config.fm_engine_path is None


class TestOpenClawConfig:
    """测试 OpenClawConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = OpenClawConfig()

        assert config.enabled is True
        assert config.gateway_url == "http://localhost:18789"
        assert config.auto_spawn_subagents is True
        assert "serper" in config.use_skills


class TestMemoryBankConfig:
    """测试 MemoryBankConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = MemoryBankConfig()

        assert config.enabled is True
        assert config.url == "http://localhost:8100"
        assert config.auto_sync is True
        assert config.min_importance == 5


class TestHeartbeatTaskConfig:
    """测试 HeartbeatTaskConfig"""

    def test_create_task_config(self):
        """测试创建任务配置"""
        config = HeartbeatTaskConfig(
            name="test_task",
            schedule="0 3 * * *",
            description="Test task"
        )

        assert config.name == "test_task"
        assert config.schedule == "0 3 * * *"
        assert config.description == "Test task"


class TestHeartbeatConfig:
    """测试 HeartbeatConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = HeartbeatConfig()

        assert config.enabled is True
        assert config.check_interval_minutes == 30
        assert config.tasks == []

    def test_with_tasks(self):
        """测试带任务的配置"""
        config = HeartbeatConfig(
            tasks=[
                HeartbeatTaskConfig(name="task1", schedule="0 3 * * *"),
                HeartbeatTaskConfig(name="task2", schedule="0 * * * *"),
            ]
        )

        assert len(config.tasks) == 2
        assert config.tasks[0].name == "task1"


class TestAMPConfig:
    """测试 AMPConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = AMPConfig()

        assert config.enabled is True
        assert config.storage_dir == "~/.amp/agents"
        assert config.auto_consolidate is True
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.openclaw, OpenClawConfig)
        assert isinstance(config.memory_bank, MemoryBankConfig)
        assert isinstance(config.heartbeat, HeartbeatConfig)

    def test_from_dict_minimal(self):
        """测试从字典创建 - 最小配置"""
        data = {}
        config = AMPConfig.from_dict(data)

        assert config.enabled is True

    def test_from_dict_full(self):
        """测试从字典创建 - 完整配置"""
        data = {
            "amp": {
                "enabled": True,
                "storage_dir": "/custom/path",
                "auto_consolidate": False,
                "storage": {
                    "backend": "fm",
                    "enable_dry_run": True,
                },
                "openclaw": {
                    "enabled": True,
                    "gateway_url": "http://custom:18789",
                },
                "memory_bank": {
                    "enabled": True,
                    "url": "http://custom:8100",
                },
                "heartbeat": {
                    "enabled": True,
                    "tasks": [
                        {"name": "task1", "schedule": "0 3 * * *"},
                    ]
                },
            }
        }

        config = AMPConfig.from_dict(data)

        assert config.storage_dir == "/custom/path"
        assert config.auto_consolidate is False
        assert config.storage.backend == "fm"
        assert config.openclaw.gateway_url == "http://custom:18789"
        assert config.memory_bank.url == "http://custom:8100"
        assert len(config.heartbeat.tasks) == 1

    def test_to_dict(self):
        """测试转换为字典"""
        config = AMPConfig()
        data = config.to_dict()

        assert "amp" in data
        assert "storage" in data["amp"]
        assert "openclaw" in data["amp"]
        assert "memory_bank" in data["amp"]
        assert "heartbeat" in data["amp"]

    def test_save_and_load(self, tmp_path):
        """测试保存和加载配置"""
        config_path = tmp_path / "config.json"

        # 创建配置
        config = AMPConfig(
            storage_dir="/custom/path",
        )

        # 保存
        config.save(str(config_path))

        # 验证文件存在
        assert config_path.exists()

        # 加载
        loaded_config = AMPConfig.load(str(config_path))

        assert loaded_config.storage_dir == "/custom/path"

    def test_load_nonexistent_file(self, tmp_path):
        """测试加载不存在的配置文件"""
        config_path = tmp_path / "nonexistent.json"

        # 应该返回默认配置而不是抛出异常
        config = AMPConfig.load(str(config_path))

        assert isinstance(config, AMPConfig)
        assert config.enabled is True

    def test_load_invalid_json(self, tmp_path):
        """测试加载无效 JSON"""
        config_path = tmp_path / "invalid.json"
        config_path.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            AMPConfig.load(str(config_path))


class TestGlobalConfig:
    """测试全局配置函数"""

    def test_get_config_default(self):
        """测试获取默认配置"""
        config = get_config()

        assert isinstance(config, AMPConfig)
        assert config.enabled is True

    def test_load_config(self, tmp_path):
        """测试加载配置"""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"amp": {"storage_dir": "/loaded"}}')

        config = load_config(str(config_path))

        assert config.storage_dir == "/loaded"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
