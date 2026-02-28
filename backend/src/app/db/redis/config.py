from redis.asyncio import Redis
from app.core.setting import settings

def create_redis():
    return Redis(
        host="redis",
        port=6379,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        max_connections=20,
    )

