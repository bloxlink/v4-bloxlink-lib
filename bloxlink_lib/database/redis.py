from __future__ import annotations

import asyncio

from redis.asyncio import Redis
from redis import ConnectionError as RedisConnectionError


from bloxlink_lib.config import CONFIG

redis: Redis = None


def connect_redis():
    """Connect to Redis"""

    global redis  # pylint: disable=global-statement

    if CONFIG.REDIS_URL:
        redis = Redis.from_url(
            CONFIG.REDIS_URL,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    else:
        redis = Redis(
            host=CONFIG.REDIS_HOST,
            port=CONFIG.REDIS_PORT,
            password=CONFIG.REDIS_PASSWORD,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )


async def wait_for_redis():
    """Block until Redis connects"""

    while True:
        try:
            await asyncio.wait_for(redis.ping(), timeout=10)
        except RedisConnectionError:
            pass
        else:
            break

        await asyncio.sleep(1)


connect_redis()
