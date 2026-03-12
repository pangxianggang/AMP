"""
AMP Configuration - 配置加载和管理

提供 AMP 配置文件的加载、验证和访问功能。

Example:
    config = AMPConfig.load("~/.amp/config.json")
    print(config.amp.storage.backend)
    print(config.openclaw.gateway_url)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """存储配置"""
    backend: str = "local"  # "local", "fm", "memory_bank"
    enable_dry_run: bool = True
    auto_commit: bool = False
    fm_engine_path: Optional[str] = None


@dataclass
class OpenClawConfig:
    """OpenClaw 集成配置"""
    enabled: bool = True
    gateway_url: str = "http://localhost:18789"
    workspace_dir: str = "~/.openclaw/workspace"
    auto_spawn_subagents: bool = True
    use_skills: List[str] = field(default_factory=lambda: ["serper", "github"])


@dataclass
class MemoryBankConfig:
    """Memory Bank 集成配置"""
    enabled: bool = True
    url: str = "http://localhost:8100"
    auto_sync: bool = True
    min_importance: int = 5
    sync_conversations: bool = True


@dataclass
class HeartbeatTaskConfig:
    """心跳任务配置"""
    name: str
    schedule: str
    description: str = ""


@dataclass
class HeartbeatConfig:
    """心跳检查配置"""
    enabled: bool = True
    check_interval_minutes: int = 30
    tasks: List[HeartbeatTaskConfig] = field(default_factory=list)


@dataclass
class AMPConfig:
    """AMP 主配置类"""

    enabled: bool = True
    storage_dir: str = "~/.amp/agents"
    auto_consolidate: bool = True
    consolidate_interval_hours: int = 24
    sync_with_memory_bank: bool = True
    memory_bank_url: str = "http://localhost:8100"

    storage: StorageConfig = field(default_factory=StorageConfig)
    openclaw: OpenClawConfig = field(default_factory=OpenClawConfig)
    memory_bank: MemoryBankConfig = field(default_factory=MemoryBankConfig)
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)

    agents: List[Dict[str, Any]] = field(default_factory=list)
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "level": "INFO",
        "file": "~/.amp/amp.log",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    })

    @classmethod
    def load(cls, path: str = "~/.amp/config.json") -> "AMPConfig":
        """
        从文件加载配置

        Args:
            path: 配置文件路径

        Returns:
            AMPConfig 实例

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON 格式错误
            ValidationError: 配置验证失败
        """
        config_path = Path(path).expanduser()

        if not config_path.exists():
            logger.info(f"Config file not found: {config_path}, using defaults")
            return cls()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read config file: {e}")
            raise

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AMPConfig":
        """
        从字典创建配置

        Args:
            data: 配置字典

        Returns:
            AMPConfig 实例
        """
        config = cls()

        # 解析 AMP 配置
        if "amp" in data:
            amp_data = data["amp"]
            config.enabled = amp_data.get("enabled", True)
            config.storage_dir = amp_data.get("storage_dir", "~/.amp/agents")
            config.auto_consolidate = amp_data.get("auto_consolidate", True)
            config.consolidate_interval_hours = amp_data.get("consolidate_interval_hours", 24)
            config.sync_with_memory_bank = amp_data.get("sync_with_memory_bank", True)
            config.memory_bank_url = amp_data.get("memory_bank_url", "http://localhost:8100")

            # 解析子配置
            if "storage" in amp_data:
                config.storage = StorageConfig(**amp_data["storage"])
            if "openclaw" in amp_data:
                config.openclaw = OpenClawConfig(**amp_data["openclaw"])
            if "memory_bank" in amp_data:
                config.memory_bank = MemoryBankConfig(**amp_data["memory_bank"])
            if "heartbeat" in amp_data:
                heartbeat_data = amp_data["heartbeat"]
                config.heartbeat = HeartbeatConfig(
                    enabled=heartbeat_data.get("enabled", True),
                    check_interval_minutes=heartbeat_data.get("check_interval_minutes", 30),
                    tasks=[HeartbeatTaskConfig(**t) for t in heartbeat_data.get("tasks", [])],
                )

            # 解析 Agent 预配置
            config.agents = amp_data.get("agents", [])

        # 解析日志配置
        if "logging" in data:
            config.logging = data["logging"]

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict

        return {
            "amp": {
                "enabled": self.enabled,
                "storage_dir": self.storage_dir,
                "auto_consolidate": self.auto_consolidate,
                "consolidate_interval_hours": self.consolidate_interval_hours,
                "sync_with_memory_bank": self.sync_with_memory_bank,
                "memory_bank_url": self.memory_bank_url,
                "storage": asdict(self.storage),
                "openclaw": asdict(self.openclaw),
                "memory_bank": asdict(self.memory_bank),
                "heartbeat": {
                    "enabled": self.heartbeat.enabled,
                    "check_interval_minutes": self.heartbeat.check_interval_minutes,
                    "tasks": [asdict(t) for t in self.heartbeat.tasks],
                },
                "agents": self.agents,
            },
            "logging": self.logging,
        }

    def save(self, path: str = "~/.amp/config.json") -> None:
        """
        保存配置到文件

        Args:
            path: 配置文件路径
        """
        config_path = Path(path).expanduser()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Config saved to {config_path}")

    def setup_logging(self) -> None:
        """应用日志配置"""
        level = getattr(logging, self.logging.get("level", "INFO").upper(), logging.INFO)
        log_file = self.logging.get("file", "~/.amp/amp.log")
        log_format = self.logging.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # 配置根日志记录器
        logging.basicConfig(
            level=level,
            format=log_format,
        )

        # 文件处理器
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))

        logging.getLogger().addHandler(file_handler)

        logger.info("Logging configured")


# 全局配置实例（懒加载）
_config: Optional[AMPConfig] = None


def get_config() -> AMPConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AMPConfig()
    return _config


def load_config(path: str = "~/.amp/config.json") -> AMPConfig:
    """加载并设置全局配置"""
    global _config
    _config = AMPConfig.load(path)
    return _config
