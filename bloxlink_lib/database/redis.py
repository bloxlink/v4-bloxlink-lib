from __future__ import annotations

import asyncio
import datetime
import json
from typing import Any

from redis.asyncio import Redis
from redis import ConnectionError as RedisConnectionError

from bloxlink_lib import BaseModel
from bloxlink_lib.config import CONFIG

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

    # loop.create_task(_heartbeat_loop()) # TODO: fix this


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
