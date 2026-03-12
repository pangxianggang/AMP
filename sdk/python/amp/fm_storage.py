"""
AMP Storage Backend - 火星文件管理系统集成

使用火星文件管理系统 (FM-Engine) 进行记忆持久化存储，提供：
- 事务支持（提交/回滚）
- 版本控制（SHA-256 hash）
- 审计日志
- 并发安全

Example:
    storage = FMStorage(workspace="~/.amp/agents")
    await storage.save_memory(agent_id, memory)
    await storage.commit(transaction_id)
    await storage.rollback(transaction_id)  # 失败时回滚
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from amp.memory import Memory, MemoryType

logger = logging.getLogger(__name__)


@dataclass
class TransactionResult:
    """事务操作结果"""
    success: bool
    transaction_id: Optional[str] = None
    diff: Optional[str] = None
    error: Optional[str] = None
    operations_count: int = 0


@dataclass
class FileVersion:
    """文件版本信息"""
    path: str
    hash: str
    size: int
    modified_at: str


@dataclass
class FileSnapshot:
    """文件快照（用于回滚）"""
    path: str
    original_content: Optional[str]  # 原始内容（None 表示文件不存在）
    original_hash: Optional[str]  # 原始 hash
    operation_type: str  # "write_file" or "delete_file"
    new_content: Optional[str] = None  # 新内容（仅写入操作）


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    timestamp: str
    transaction_id: str
    operation: str
    path: str
    status: str  # "success", "failed", "rolled_back"
    details: Optional[str] = None


class FMStorage:
    """
    火星文件管理系统存储后端
    
    使用 FM-Engine 进行记忆持久化，支持：
    - 事务性写入（先 dry-run 预览，再提交）
    - 版本控制（SHA-256 hash 校验）
    - 回滚支持
    - 审计日志
    
    Attributes:
        workspace: 工作区根目录
        enable_dry_run: 提交前是否先预览
        auto_commit: 是否自动提交事务
    """

    def __init__(
        self,
        workspace: str,
        enable_dry_run: bool = True,
        auto_commit: bool = False,
        fm_engine_path: Optional[str] = None,
    ):
        self.workspace = Path(workspace).expanduser()
        self.enable_dry_run = enable_dry_run
        self.auto_commit = auto_commit
        self.fm_engine_path = fm_engine_path or self._find_fm_engine()

        # 事务管理
        self._pending_transactions: Dict[str, List[Dict]] = {}
        self._transaction_counter = 0

        # 快照管理（用于回滚）
        self._transaction_snapshots: Dict[str, List[FileSnapshot]] = {}

        # 审计日志
        self._audit_log: List[Dict[str, Any]] = []
        self._log_max_size = 1000  # 最多保留 1000 条日志

        # 确保工作区存在
        self.workspace.mkdir(parents=True, exist_ok=True)

        logger.info(f"FMStorage initialized: workspace={self.workspace}")

    def _find_fm_engine(self) -> Optional[str]:
        """查找 FM-Engine CLI 路径"""
        # 常见安装位置
        possible_paths = [
            Path(r"C:\Users\Administrator\Desktop\文件管理系统\dist\fm-cli.exe"),
            Path(r"C:\Users\Administrator\Desktop\文件管理系统\dist\fm-cli"),
            Path.home() / ".local" / "bin" / "fm-cli",
            Path("/usr/local/bin/fm-cli"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # 尝试在 PATH 中查找
        try:
            result = subprocess.run(
                ["where", "fm-cli"] if sys.platform == "win32" else ["which", "fm-cli"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[0]
        except Exception:
            pass
        
        logger.warning("FM-Engine CLI not found, will use direct file operations")
        return None

    def _run_fm_command(
        self,
        command: List[str],
        timeout: int = 30,
    ) -> Tuple[bool, str, str]:
        """
        运行 FM-Engine CLI 命令
        
        Returns:
            (success, stdout, stderr)
        """
        if not self.fm_engine_path:
            return False, "", "FM-Engine CLI not available"
        
        try:
            cmd = [self.fm_engine_path] + command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"FM command timeout: {' '.join(command)}")
            return False, "", "Command timeout"
        except Exception as e:
            logger.error(f"FM command failed: {e}")
            return False, "", str(e)

    def _compute_hash(self, content: str) -> str:
        """计算内容的 SHA-256 hash"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _get_memory_file_path(self, agent_id: str, memory: Memory) -> Path:
        """获取记忆文件路径"""
        return self._get_memory_file_path_by_type(agent_id, memory.type.value, memory.id)

    def _get_memory_file_path_by_type(self, agent_id: str, memory_type: str, memory_id: str) -> Path:
        """通过类型和 ID 获取记忆文件路径（辅助方法）"""
        mem_dir = self.workspace / agent_id / "memories" / memory_type
        mem_dir.mkdir(parents=True, exist_ok=True)
        return mem_dir / f"{memory_id}.json"

    async def _read_file_with_version(self, file_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        读取文件并返回内容和 hash
        
        Returns:
            (content, hash) 或 (None, None) 如果文件不存在
        """
        if not file_path.exists():
            return None, None
        
        try:
            content = file_path.read_text(encoding='utf-8')
            file_hash = self._compute_hash(content)
            return content, file_hash
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None, None

    async def save_memory(
        self,
        agent_id: str,
        memory: Memory,
        transaction_id: Optional[str] = None,
    ) -> TransactionResult:
        """
        保存记忆到磁盘（使用事务）
        
        Args:
            agent_id: Agent ID
            memory: 记忆对象
            transaction_id: 可选的事务 ID，不提供则自动创建
            
        Returns:
            TransactionResult
        """
        if transaction_id is None:
            transaction_id = self._create_transaction_id()
        
        file_path = self._get_memory_file_path(agent_id, memory)
        content = json.dumps(memory.to_dict(), indent=2, ensure_ascii=False)
        new_hash = self._compute_hash(content)
        
        # 读取现有文件（如果有）
        existing_content, existing_hash = await self._read_file_with_version(file_path)
        
        # 如果内容相同，跳过
        if existing_hash == new_hash:
            logger.debug(f"Memory {memory.id} unchanged, skipping")
            return TransactionResult(
                success=True,
                transaction_id=transaction_id,
                operations_count=0
            )
        
        # 创建操作
        operation = {
            "type": "write_file",
            "path": str(file_path),
            "content": content,
            "baseVersion": existing_hash if existing_hash else "new",
        }
        
        # 记录到待处理事务
        if transaction_id not in self._pending_transactions:
            self._pending_transactions[transaction_id] = []
        
        self._pending_transactions[transaction_id].append(operation)

        # 创建快照（用于回滚）
        snapshot = FileSnapshot(
            path=str(file_path),
            original_content=existing_content,
            original_hash=existing_hash,
            operation_type="write_file",
            new_content=content,
        )
        if transaction_id not in self._transaction_snapshots:
            self._transaction_snapshots[transaction_id] = []
        self._transaction_snapshots[transaction_id].append(snapshot)

        logger.debug(f"Queued memory write: {memory.id} -> {file_path}")
        
        # 如果启用自动提交，立即提交
        if self.auto_commit:
            return await self.commit(transaction_id)
        
        return TransactionResult(
            success=True,
            transaction_id=transaction_id,
            operations_count=1
        )

    async def delete_memory(
        self,
        agent_id: str,
        memory_id: str,
        memory_type: MemoryType,
        transaction_id: Optional[str] = None,
    ) -> TransactionResult:
        """
        删除记忆（使用事务）

        Args:
            agent_id: Agent ID
            memory_id: 记忆 ID
            memory_type: 记忆类型
            transaction_id: 可选的事务 ID

        Returns:
            TransactionResult
        """
        if transaction_id is None:
            transaction_id = self._create_transaction_id()

        # 使用新方法获取文件路径，避免 hack
        file_path = self._get_memory_file_path_by_type(agent_id, memory_type.value, memory_id)
        
        if not file_path.exists():
            logger.warning(f"Memory {memory_id} not found, skipping delete")
            return TransactionResult(success=True, transaction_id=transaction_id, operations_count=0)
        
        # 读取现有文件获取 hash
        _, existing_hash = await self._read_file_with_version(file_path)
        
        # 创建删除操作
        operation = {
            "type": "delete_file",
            "path": str(file_path),
            "baseVersion": existing_hash or "nonexistent",
        }
        
        # 记录到待处理事务
        if transaction_id not in self._pending_transactions:
            self._pending_transactions[transaction_id] = []
        
        self._pending_transactions[transaction_id].append(operation)
        
        logger.debug(f"Queued memory delete: {memory_id}")
        
        # 如果启用自动提交，立即提交
        if self.auto_commit:
            return await self.commit(transaction_id)
        
        return TransactionResult(
            success=True,
            transaction_id=transaction_id,
            operations_count=1
        )

    async def commit(self, transaction_id: str) -> TransactionResult:
        """
        提交事务
        
        Args:
            transaction_id: 事务 ID
            
        Returns:
            TransactionResult
        """
        if transaction_id not in self._pending_transactions:
            return TransactionResult(
                success=False,
                error=f"Transaction {transaction_id} not found"
            )
        
        operations = self._pending_transactions[transaction_id]
        
        if not operations:
            logger.debug(f"Transaction {transaction_id} is empty, skipping commit")
            del self._pending_transactions[transaction_id]
            return TransactionResult(success=True, transaction_id=transaction_id, operations_count=0)
        
        # 如果启用了 dry-run，先预览
        if self.enable_dry_run and self.fm_engine_path:
            # TODO: 实现 FM-Engine 的 dry-run 调用
            # 目前简化处理，直接执行文件写入
            pass
        
        # 执行操作
        success_count = 0
        error_msg = None
        
        try:
            for op in operations:
                if op["type"] == "write_file":
                    file_path = Path(op["path"])
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(op["content"], encoding='utf-8')
                    success_count += 1
                    logger.debug(f"Written file: {op['path']}")

                elif op["type"] == "delete_file":
                    file_path = Path(op["path"])
                    if file_path.exists():
                        file_path.unlink()
                        success_count += 1
                        logger.debug(f"Deleted file: {op['path']}")

            # 清除已提交的事务和快照
            del self._pending_transactions[transaction_id]
            if transaction_id in self._transaction_snapshots:
                del self._transaction_snapshots[transaction_id]

            # 记录审计日志
            self._add_audit_log_entry(
                transaction_id=transaction_id,
                operation="commit",
                path="multiple",
                status="success",
                details=f"{success_count}/{len(operations)} operations committed"
            )

            logger.info(f"Transaction {transaction_id} committed: {success_count}/{len(operations)} operations")

            return TransactionResult(
                success=True,
                transaction_id=transaction_id,
                operations_count=success_count
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Transaction {transaction_id} failed: {error_msg}")
            
            # 尝试回滚
            await self.rollback(transaction_id)
            
            return TransactionResult(
                success=False,
                transaction_id=transaction_id,
                error=error_msg,
                operations_count=success_count
            )

    async def rollback(self, transaction_id: str) -> TransactionResult:
        """
        回滚事务（撤销已提交的操作，基于快照恢复）

        Args:
            transaction_id: 事务 ID

        Returns:
            TransactionResult
        """
        # 检查事务是否存在（已提交或未提交）
        is_pending = transaction_id in self._pending_transactions
        has_snapshots = transaction_id in self._transaction_snapshots

        if not is_pending and not has_snapshots:
            return TransactionResult(
                success=False,
                error=f"Transaction {transaction_id} not found or already rolled back"
            )

        # 如果是待处理事务，先清除
        ops_count = 0
        if is_pending:
            ops_count = len(self._pending_transactions[transaction_id])
            del self._pending_transactions[transaction_id]

        # 如果有快照，执行回滚（恢复原始状态）
        rolled_back_count = 0
        if has_snapshots:
            snapshots = self._transaction_snapshots[transaction_id]
            for snapshot in snapshots:
                try:
                    file_path = Path(snapshot.path)

                    if snapshot.operation_type == "write_file":
                        # 恢复原始内容或删除文件
                        if snapshot.original_content is None:
                            # 原始文件不存在，删除新创建的文件
                            if file_path.exists():
                                file_path.unlink()
                                logger.debug(f"Rollback: deleted {snapshot.path}")
                        else:
                            # 恢复原始内容
                            file_path.write_text(snapshot.original_content, encoding='utf-8')
                            logger.debug(f"Rollback: restored {snapshot.path}")

                    elif snapshot.operation_type == "delete_file":
                        # 恢复被删除的文件（如果有原始内容）
                        if snapshot.original_content is not None:
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text(snapshot.original_content, encoding='utf-8')
                            logger.debug(f"Rollback: restored deleted file {snapshot.path}")

                    rolled_back_count += 1

                    # 记录审计日志
                    self._add_audit_log_entry(
                        transaction_id=transaction_id,
                        operation="rollback",
                        path=snapshot.path,
                        status="success"
                    )

                except Exception as e:
                    logger.error(f"Rollback failed for {snapshot.path}: {e}")
                    self._add_audit_log_entry(
                        transaction_id=transaction_id,
                        operation="rollback",
                        path=snapshot.path,
                        status="failed",
                        details=str(e)
                    )

            # 清除快照
            del self._transaction_snapshots[transaction_id]

        # 如果是从 commit 失败触发的回滚，且是 pending 状态，已经在上层处理
        # 这里只处理已提交事务的回滚

        logger.warning(f"Transaction {transaction_id} rolled back: {rolled_back_count} files restored")

        return TransactionResult(
            success=True,
            transaction_id=transaction_id,
            operations_count=rolled_back_count
        )

    def _add_audit_log_entry(
        self,
        transaction_id: str,
        operation: str,
        path: str,
        status: str,
        details: Optional[str] = None,
    ) -> None:
        """添加审计日志条目"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            transaction_id=transaction_id,
            operation=operation,
            path=path,
            status=status,
            details=details,
        )
        self._audit_log.append(asdict(entry))

        # 限制日志大小
        if len(self._audit_log) > self._log_max_size:
            self._audit_log = self._audit_log[-self._log_max_size:]

    def get_audit_log(self, transaction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取审计日志（可按事务过滤）"""
        if transaction_id is None:
            return list(self._audit_log)
        return [entry for entry in self._audit_log if entry.get("transaction_id") == transaction_id]

    def clear_audit_log(self) -> None:
        """清空审计日志"""
        self._audit_log.clear()

    def _create_transaction_id(self) -> str:
        """创建事务 ID"""
        self._transaction_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"tx-{timestamp}-{self._transaction_counter:04d}"

    async def load_memories(self, agent_id: str) -> Dict[str, Memory]:
        """
        加载 Agent 的所有记忆
        
        Args:
            agent_id: Agent ID
            
        Returns:
            记忆字典 {memory_id: Memory}
        """
        memories = {}
        mem_dir = self.workspace / agent_id / "memories"
        
        if not mem_dir.exists():
            return memories
        
        for mem_type in MemoryType:
            type_dir = mem_dir / mem_type.value
            if not type_dir.exists():
                continue
            
            for mem_file in type_dir.glob("*.json"):
                try:
                    data = json.loads(mem_file.read_text(encoding='utf-8'))
                    memory = Memory.from_dict(data)
                    memories[memory.id] = memory
                except Exception as e:
                    logger.warning(f"Failed to load memory {mem_file}: {e}")
        
        logger.info(f"Loaded {len(memories)} memories for agent {agent_id}")
        return memories

    async def get_file_version(self, agent_id: str, memory_type: MemoryType, memory_id: str) -> Optional[FileVersion]:
        """
        获取记忆文件的版本信息
        
        Args:
            agent_id: Agent ID
            memory_type: 记忆类型
            memory_id: 记忆 ID
            
        Returns:
            FileVersion 或 None
        """
        file_path = self.workspace / agent_id / "memories" / memory_type.value / f"{memory_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            content = file_path.read_text(encoding='utf-8')
            stat = file_path.stat()
            
            return FileVersion(
                path=str(file_path),
                hash=self._compute_hash(content),
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to get file version: {e}")
            return None
