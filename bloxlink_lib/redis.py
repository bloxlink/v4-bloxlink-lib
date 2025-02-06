from __future__ import annotations

import asyncio
import datetime
import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from redis import ConnectionError as RedisConnectionError

from bloxlink_lib import BaseModel
from .config import CONFIG

redis: Redis = None


def connect_redis():
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

    # override redis with better set method
    redis._old_set = redis.set  # pylint: disable=protected-access
    redis.set = redis_set

    # loop.create_task(_heartbeat_loop()) # TODO: fix this


async def redis_set(key: str, value: BaseModel | Any, expire: datetime.timedelta | int = None, **kwargs):
    """Set a value in Redis. Accepts BaseModels and expirations as datetimes."""

    await redis._old_set(key,  # pylint: disable=protected-access
                         value.model_dump_json() if isinstance(value, BaseModel) else (
                             json.dumps(value) if isinstance(value, (list, dict)) else value),
                         ex=int(expire.total_seconds()) if expire and isinstance(
                             expire, datetime.timedelta) else expire,
                         **kwargs)


async def _heartbeat_loop():
    while True:
        try:
            await asyncio.wait_for(redis.ping(), timeout=10)
        except RedisConnectionError as e:
            raise SystemError("Failed to connect to Redis.") from e

        await asyncio.sleep(5)


async def wait_for_redis():
    while True:
        try:
            await asyncio.wait_for(redis.ping(), timeout=10)
        except RedisConnectionError:
            pass
        else:
            break

        await asyncio.sleep(1)


connect_redis()
