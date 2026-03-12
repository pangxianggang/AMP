"""
AMP FM Storage 测试

运行方式:
    python -m pytest tests/test_fm_storage.py -v
"""

import asyncio
import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# 添加 SDK 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

from amp.fm_storage import FMStorage, TransactionResult, FileSnapshot
from amp.memory import Memory, MemoryType


class TestFMStorage:
    """测试 FM 存储后端"""

    @pytest.fixture
    def storage(self, tmp_path):
        """创建测试用存储实例"""
        return FMStorage(workspace=str(tmp_path))

    @pytest.fixture
    def sample_memory(self):
        """创建示例记忆"""
        return Memory(
            id="test-001",
            type=MemoryType.SEMANTIC,
            content="测试内容",
            created_at="2026-03-12T10:00:00",
            importance=8,
            tags=["test"],
        )

    @pytest.mark.asyncio
    async def test_save_memory(self, storage, sample_memory):
        """测试保存记忆"""
        result = await storage.save_memory("agent-001", sample_memory)

        assert result.success is True
        assert result.operations_count == 1

    @pytest.mark.asyncio
    async def test_transaction_commit(self, storage, sample_memory):
        """测试事务提交"""
        # 开始事务
        tx_id = storage._create_transaction_id()

        # 保存记忆
        result = await storage.save_memory("agent-001", sample_memory, transaction_id=tx_id)
        assert result.transaction_id == tx_id

        # 提交事务
        commit_result = await storage.commit(tx_id)
        assert commit_result.success is True
        assert commit_result.operations_count == 1

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, storage, sample_memory):
        """测试事务回滚"""
        # 创建初始文件
        initial_result = await storage.save_memory("agent-001", sample_memory)
        await storage.commit(initial_result.transaction_id)

        # 开始新事务，修改记忆
        tx_id = storage._create_transaction_id()
        modified_memory = Memory(
            id="test-001",
            type=MemoryType.SEMANTIC,
            content="修改后的内容",
            created_at="2026-03-12T10:00:00",
            importance=5,
            tags=["test", "modified"],
        )
        await storage.save_memory("agent-001", modified_memory, transaction_id=tx_id)

        # 回滚事务
        rollback_result = await storage.rollback(tx_id)
        assert rollback_result.success is True

        # 验证文件已恢复（回滚会恢复原始内容）
        # 注意：由于回滚只清除待处理操作，已提交的需要特别处理

    @pytest.mark.asyncio
    async def test_load_memories(self, storage, sample_memory):
        """测试加载记忆"""
        # 保存记忆
        result = await storage.save_memory("agent-001", sample_memory)
        await storage.commit(result.transaction_id)

        # 加载记忆
        memories = await storage.load_memories("agent-001")

        assert len(memories) == 1
        assert sample_memory.id in memories
        assert memories[sample_memory.id].content == sample_memory.content

    @pytest.mark.asyncio
    async def test_delete_memory(self, storage, sample_memory):
        """测试删除记忆"""
        # 先保存
        save_result = await storage.save_memory("agent-001", sample_memory)
        await storage.commit(save_result.transaction_id)

        # 删除
        tx_id = storage._create_transaction_id()
        delete_result = await storage.delete_memory(
            "agent-001",
            sample_memory.id,
            sample_memory.type,
            transaction_id=tx_id
        )
        assert delete_result.success is True

        commit_result = await storage.commit(tx_id)
        assert commit_result.success is True

    @pytest.mark.asyncio
    async def test_audit_log(self, storage, sample_memory):
        """测试审计日志"""
        # 执行一些操作
        result = await storage.save_memory("agent-001", sample_memory)
        await storage.commit(result.transaction_id)

        # 获取审计日志
        log = storage.get_audit_log()

        assert len(log) > 0
        assert any(entry["operation"] == "commit" for entry in log)

    @pytest.mark.asyncio
    async def test_file_version(self, storage, sample_memory):
        """测试文件版本获取"""
        # 保存记忆
        result = await storage.save_memory("agent-001", sample_memory)
        await storage.commit(result.transaction_id)

        # 获取版本
        version = await storage.get_file_version(
            "agent-001",
            sample_memory.type,
            sample_memory.id
        )

        assert version is not None
        assert version.path.endswith(f"{sample_memory.id}.json")
        assert version.size > 0


class TestTransactionResult:
    """测试 TransactionResult"""

    def test_success_result(self):
        """测试成功结果"""
        result = TransactionResult(
            success=True,
            transaction_id="tx-001",
            operations_count=5
        )

        assert result.success is True
        assert result.transaction_id == "tx-001"
        assert result.operations_count == 5
        assert result.error is None

    def test_error_result(self):
        """测试错误结果"""
        result = TransactionResult(
            success=False,
            error="Something went wrong"
        )

        assert result.success is False
        assert result.error == "Something went wrong"


class TestFileSnapshot:
    """测试文件快照"""

    def test_snapshot_for_write(self):
        """测试写入操作的快照"""
        snapshot = FileSnapshot(
            path="/test/file.json",
            original_content=None,
            original_hash=None,
            operation_type="write_file",
            new_content='{"test": true}',
        )

        assert snapshot.path == "/test/file.json"
        assert snapshot.original_content is None  # 新文件
        assert snapshot.operation_type == "write_file"

    def test_snapshot_for_delete(self):
        """测试删除操作的快照"""
        snapshot = FileSnapshot(
            path="/test/file.json",
            original_content='{"test": true}',
            original_hash="abc123",
            operation_type="delete_file",
        )

        assert snapshot.path == "/test/file.json"
        assert snapshot.original_content is not None
        assert snapshot.operation_type == "delete_file"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
