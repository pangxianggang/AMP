"""
AMP Memory Bank Integration - 双向记忆同步

实现 AMP 与 Memory Bank 系统的双向同步：
- AMP → Memory Bank: 保存新记忆和经验
- Memory Bank → AMP: 加载用户偏好和已验证经验

Memory Bank API:
- POST /memory/write - 保存记忆
- POST /memory/search - 搜索记忆
- POST /experience/write - 保存经验
- POST /experience/search - 搜索经验
- POST /experience/{id}/feedback - 提交反馈
- POST /experience/{id}/promote - 手动转正
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import aiohttp

from amp.memory import Memory, MemoryType

logger = logging.getLogger(__name__)


class MemoryBankError(Exception):
    """Memory Bank 操作异常基类"""
    pass


class MemoryBankConnectionError(MemoryBankError):
    """连接错误"""
    pass


class MemoryBankAuthError(MemoryBankError):
    """认证错误"""
    pass


class MemoryBankDataError(MemoryBankError):
    """数据错误（写入/读取失败）"""
    pass


@dataclass
class MemoryBankConfig:
    """Memory Bank 配置"""
    url: str = "http://localhost:8100"
    timeout: int = 30
    auto_sync: bool = True
    min_importance: int = 5  # 只同步重要性 >= 此值的记忆


class MemoryBankIntegration:
    """
    Memory Bank 集成
    
    提供 AMP 与 Memory Bank 之间的双向同步能力。
    
    Features:
    - 保存对话历史
    - 同步记忆到 Memory Bank
    - 从 Memory Bank 加载用户偏好
    - 同步经验/教训
    - 支持候选经验转正机制
    
    Example:
        mb = MemoryBankIntegration()
        
        # 保存对话
        await mb.save_conversation(agent, messages, summary)
        
        # 同步记忆
        await mb.sync_agent_to_bank(agent)
        
        # 加载用户偏好
        await mb.load_user_preferences(agent)
    """

    def __init__(self, config: Optional[MemoryBankConfig] = None):
        self.config = config or MemoryBankConfig()
        self._session = None
        self._health_cache = False
        logger.info(f"MemoryBankIntegration initialized: {self.config.url}")
    
    def check_health(self) -> bool:
        """检查 Memory Bank 服务是否可用"""
        import requests
        try:
            response = requests.get(f"{self.config.url}/health", timeout=2)
            self._health_cache = response.status_code == 200
        except Exception:
            self._health_cache = False
        return self._health_cache

    async def _get_session(self):
        """获取 aiohttp session"""
        if self._session is None:
            try:
                import aiohttp
                self._session = aiohttp.ClientSession()
            except ImportError:
                logger.warning("aiohttp not installed, Memory Bank integration disabled")
                return None
        return self._session

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None

    async def save_conversation(
        self,
        agent_id: str,
        messages: List[Dict[str, str]],
        summary: str,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        保存对话历史到 Memory Bank
        
        Args:
            agent_id: Agent ID
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            summary: 对话摘要
            session_id: 会话 ID
            tags: 标签
            
        Returns:
            是否成功
        """
        try:
            session = await self._get_session()
            if not session:
                return False
            
            payload = {
                "agent_id": agent_id,
                "scope": "session",
                "session_id": session_id or datetime.now().strftime("%Y%m%d%H%M%S"),
                "summary": summary,
                "messages": messages,
                "metadata": {
                    "source": "amp-conversation",
                    "timestamp": datetime.now().isoformat(),
                },
                "tags": tags or ["conversation", "amp"],
            }

            async with session.post(
                f"{self.config.url}/memory-bank/chat-history",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Saved conversation to Memory Bank: {summary[:50]}...")
                    return True
                elif resp.status == 401:
                    logger.error(f"Memory Bank authentication failed: {resp.status}")
                    raise MemoryBankAuthError(f"Authentication failed: {resp.status}")
                elif resp.status >= 500:
                    logger.error(f"Memory Bank server error: {resp.status}")
                    raise MemoryBankDataError(f"Server error: {resp.status}")
                else:
                    error_text = await resp.text()
                    logger.warning(f"Failed to save conversation: {resp.status} - {error_text}")
                    raise MemoryBankDataError(f"Write failed: {resp.status} - {error_text}")

        except aiohttp.ClientError as e:
            logger.error(f"Memory Bank connection error: {e}")
            raise MemoryBankConnectionError(f"Connection failed: {e}")
        except MemoryBankError:
            raise
        except Exception as e:
            logger.error(f"Memory Bank save conversation failed: {e}")
            raise MemoryBankDataError(f"Unexpected error: {e}")

    async def sync_agent_to_bank(
        self,
        agent_id: str,
        memories: List[Memory],
        min_importance: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        同步 Agent 记忆到 Memory Bank (改进错误处理)

        Args:
            agent_id: Agent ID
            memories: 记忆列表
            min_importance: 最小重要性阈值

        Returns:
            同步统计 {synced: 成功数，failed: 失败数，skipped: 跳过数}
        """
        # ✅ 先检查 Memory Bank 是否可用
        if not self.check_health():
            logger.warning(f"⚠️ Memory Bank 不可用 ({self.config.url})，跳过同步")
            logger.info(f"💡 提示：请启动 Memory Bank 服务 - cd AgentMemoryBank && python main.py")
            return {"synced": 0, "failed": 0, "skipped": len(memories)}
        
        threshold = min_importance or self.config.min_importance
        stats = {"synced": 0, "failed": 0, "skipped": 0}
        errors: Dict[str, int] = {"connection": 0, "auth": 0, "server": 0, "other": 0}

        for memory in memories:
            if memory.importance < threshold:
                continue

            try:
                session = await self._get_session()
                if not session:
                    stats["failed"] += 1
                    errors["connection"] += 1
                    continue

                payload = {
                    "content": memory.content,
                    "memory_type": memory.type.value,
                    "agent_id": agent_id,
                    "scope": "agent",
                    "importance": memory.importance,
                    "tags": memory.tags,
                    "metadata": {
                        "emotion": memory.emotion,
                        "context": memory.context,
                        "source_agent": memory.source_agent,
                        "created_at": memory.created_at,
                    }
                }

                async with session.post(
                    f"{self.config.url}/memory/write",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        stats["synced"] += 1
                    elif resp.status == 401:
                        errors["auth"] += 1
                        logger.error(f"Auth failed for memory {memory.id}: {resp.status}")
                        stats["failed"] += 1
                    elif resp.status >= 500:
                        errors["server"] += 1
                        logger.error(f"Server error for memory {memory.id}: {resp.status}")
                        stats["failed"] += 1
                    else:
                        errors["other"] += 1
                        logger.warning(f"Failed to sync memory {memory.id}: {resp.status}")
                        stats["failed"] += 1

            except aiohttp.ClientError as e:
                errors["connection"] += 1
                logger.error(f"Connection error for memory {memory.id}: {e}")
                stats["failed"] += 1
            except Exception as e:
                errors["other"] += 1
                logger.error(f"Unexpected error for memory {memory.id}: {e}")
                stats["failed"] += 1

        # ✅ 提供清晰的同步报告
        if stats["synced"] > 0:
            logger.info(f"✅ 成功同步 {stats['synced']} 条记忆到 Memory Bank")
        if stats["failed"] > 0:
            logger.warning(f"⚠️ {stats['failed']} 条记忆同步失败")
            logger.debug(f"错误分类：{errors}")
        if stats["skipped"] > 0:
            logger.debug(f"ℹ️ 跳过 {stats['skipped']} 条记忆（服务不可用）")

        return stats

    async def load_user_preferences(self, agent_id: str) -> List[Memory]:
        """
        从 Memory Bank 加载用户偏好到 Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            加载的记忆列表
        """
        try:
            session = await self._get_session()
            if not session:
                return []
            
            # 搜索用户偏好相关的记忆
            payload = {
                "query": "用户偏好 喜欢 习惯 配置",
                "agent_id": agent_id,
                "memory_type": "semantic",
                "limit": 20,
            }
            
            async with session.post(
                f"{self.config.url}/memory/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    memories = []
                    
                    for item in data.get("memories", []):
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
                    
                    logger.info(f"Loaded {len(memories)} user preferences from Memory Bank")
                    return memories
                else:
                    logger.warning(f"Failed to load user preferences: {resp.status}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Memory Bank load preferences failed: {e}")
            return []

    async def save_experience(
        self,
        agent_id: str,
        topic: str,
        lesson: str,
        experience_type: str = "lesson",  # "lesson" or "success"
        tags: Optional[List[str]] = None,
        domain: str = "general",
    ) -> bool:
        """
        保存经验/教训到 Memory Bank
        
        Args:
            agent_id: Agent ID
            topic: 经验主题
            lesson: 经验/教训内容
            experience_type: 类型 ("lesson" 或 "success")
            tags: 标签
            domain: 领域
            
        Returns:
            是否成功
        """
        try:
            session = await self._get_session()
            if not session:
                return False
            
            payload = {
                "topic": topic,
                "lesson": lesson,
                "type": experience_type,
                "agent_id": agent_id,
                "tags": tags or [],
                "domain": domain,
                "metadata": {
                    "source": "amp",
                    "timestamp": datetime.now().isoformat(),
                }
            }
            
            async with session.post(
                f"{self.config.url}/experience/write",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Saved experience to Memory Bank: {topic}")
                    return True
                else:
                    logger.warning(f"Failed to save experience: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.debug(f"Memory Bank save experience failed: {e}")
            return False

    async def load_experiences(
        self,
        agent_id: str,
        topic: Optional[str] = None,
        domain: Optional[str] = None,
        include_candidates: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        从 Memory Bank 加载经验
        
        Args:
            agent_id: Agent ID
            topic: 主题过滤
            domain: 领域过滤
            include_candidates: 是否包含候选经验（未转正）
            
        Returns:
            经验列表
        """
        try:
            session = await self._get_session()
            if not session:
                return []
            
            params = {
                "agent_id": agent_id,
                "include_candidates": str(include_candidates).lower(),
            }
            
            if topic:
                params["topic"] = topic
            if domain:
                params["domain"] = domain
            
            async with session.get(
                f"{self.config.url}/experience/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    experiences = data.get("experiences", [])
                    logger.info(f"Loaded {len(experiences)} experiences from Memory Bank")
                    return experiences
                else:
                    logger.warning(f"Failed to load experiences: {resp.status}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Memory Bank load experiences failed: {e}")
            return []

    async def submit_feedback(
        self,
        experience_id: str,
        success: bool,
        agent_id: Optional[str] = None,
    ) -> bool:
        """
        提交经验反馈（用于置信度更新）
        
        Args:
            experience_id: 经验 ID
            success: 是否成功采纳
            agent_id: Agent ID
            
        Returns:
            是否成功
        """
        try:
            session = await self._get_session()
            if not session:
                return False
            
            payload = {
                "success": success,
                "agent_id": agent_id or "unknown",
                "timestamp": datetime.now().isoformat(),
            }
            
            async with session.post(
                f"{self.config.url}/experience/{experience_id}/feedback",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Submitted feedback for experience {experience_id}")
                    return True
                else:
                    logger.warning(f"Failed to submit feedback: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.debug(f"Memory Bank submit feedback failed: {e}")
            return False

    async def promote_experience(self, experience_id: str) -> bool:
        """
        手动转正候选经验
        
        Args:
            experience_id: 经验 ID
            
        Returns:
            是否成功
        """
        try:
            session = await self._get_session()
            if not session:
                return False
            
            async with session.post(
                f"{self.config.url}/experience/{experience_id}/promote",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Promoted experience {experience_id} to verified")
                    return True
                else:
                    logger.warning(f"Failed to promote experience: {resp.status}")
                    return False
                    
        except Exception as e:
            logger.debug(f"Memory Bank promote experience failed: {e}")
            return False

    async def search_memories(
        self,
        query: str,
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        搜索 Memory Bank 中的记忆
        
        Args:
            query: 搜索查询
            agent_id: Agent ID 过滤
            memory_type: 记忆类型过滤
            limit: 结果数量限制
            
        Returns:
            记忆列表
        """
        try:
            session = await self._get_session()
            if not session:
                return []
            
            payload = {
                "query": query,
                "limit": limit,
            }
            
            if agent_id:
                payload["agent_id"] = agent_id
            if memory_type:
                payload["memory_type"] = memory_type
            
            async with session.post(
                f"{self.config.url}/memory/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("memories", [])
                else:
                    logger.warning(f"Failed to search memories: {resp.status}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Memory Bank search failed: {e}")
            return []
