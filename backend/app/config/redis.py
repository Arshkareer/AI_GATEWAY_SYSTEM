import redis.asyncio as aioredis
from typing import Optional
import json

from .settings import settings


class RedisClient:
    """Redis connection manager."""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        
    async def connect(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self.redis:
            return None
        return await self.redis.get(key)
        
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        """Set value in Redis."""
        if not self.redis:
            return
        await self.redis.set(key, value, ex=expire)
        
    async def delete(self, key: str):
        """Delete key from Redis."""
        if not self.redis:
            return
        await self.redis.delete(key)
        
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from Redis."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
        
    async def set_json(self, key: str, value: dict, expire: Optional[int] = None):
        """Set JSON value in Redis."""
        await self.set(key, json.dumps(value), expire)
        
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.redis:
            return False
        return await self.redis.exists(key)
        
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment value in Redis."""
        if not self.redis:
            return 0
        return await self.redis.incr(key, amount)
        
    async def expire(self, key: str, seconds: int):
        """Set expiration for key."""
        if not self.redis:
            return
        await self.redis.expire(key, seconds)


# Global Redis client
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client."""
    return redis_client