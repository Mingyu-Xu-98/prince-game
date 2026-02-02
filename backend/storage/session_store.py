"""
会话存储
管理游戏会话状态
"""
from abc import ABC, abstractmethod
from typing import Optional
from models.game_state import GameState


class SessionStore(ABC):
    """会话存储抽象基类"""

    @abstractmethod
    async def get(self, session_id: str) -> Optional[GameState]:
        """获取会话"""
        pass

    @abstractmethod
    async def set(self, session_id: str, state: GameState) -> None:
        """保存会话"""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """删除会话"""
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        pass


class InMemorySessionStore(SessionStore):
    """内存会话存储（开发用）"""

    def __init__(self):
        self._sessions: dict[str, GameState] = {}

    async def get(self, session_id: str) -> Optional[GameState]:
        return self._sessions.get(session_id)

    async def set(self, session_id: str, state: GameState) -> None:
        self._sessions[session_id] = state

    async def delete(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    async def list_sessions(self) -> list[str]:
        """列出所有会话ID"""
        return list(self._sessions.keys())

    async def clear_all(self) -> None:
        """清除所有会话"""
        self._sessions.clear()


# 尝试导入 Redis 存储
try:
    import redis.asyncio as redis
    import json

    class RedisSessionStore(SessionStore):
        """Redis 会话存储（生产用）"""

        def __init__(self, redis_url: str):
            self.redis = redis.from_url(redis_url)
            self.prefix = "prince_game:"
            self.ttl = 3600 * 24  # 24小时过期

        async def get(self, session_id: str) -> Optional[GameState]:
            data = await self.redis.get(f"{self.prefix}{session_id}")
            if data:
                return GameState.model_validate_json(data)
            return None

        async def set(self, session_id: str, state: GameState) -> None:
            await self.redis.setex(
                f"{self.prefix}{session_id}",
                self.ttl,
                state.model_dump_json(),
            )

        async def delete(self, session_id: str) -> None:
            await self.redis.delete(f"{self.prefix}{session_id}")

        async def exists(self, session_id: str) -> bool:
            return await self.redis.exists(f"{self.prefix}{session_id}") > 0

except ImportError:
    RedisSessionStore = None
