from __future__ import annotations

import asyncio
import datetime
import logging
import os
from typing import Type, TYPE_CHECKING

from motor.motor_asyncio import AsyncIOMotorClient
from bloxlink_lib.config import CONFIG
from bloxlink_lib.database.redis import redis  # pylint: disable=no-name-in-module

mongo: AsyncIOMotorClient = None

if TYPE_CHECKING:  # pragma: no cover
    from bloxlink_lib.models.schemas import BaseSchema


def connect_database():
    """Connect to MongoDB"""

    global mongo  # pylint: disable=global-statement

    if CONFIG.SKIP_MONGO_LOAD and CONFIG.TEST_MODE:
        logging.info("Skipping MongoDB initialization in test mode")
        return

    mongo_options: dict[str, str | int] = {}

    if CONFIG.MONGO_CA_FILE:
        ca_file_path = os.path.join(os.getcwd(), "cert.crt")
        ca_file = os.path.exists(ca_file_path)

        if not ca_file:
            with open(ca_file_path, "w", encoding="utf-8") as f:
                f.write(CONFIG.MONGO_CA_FILE)

        mongo_options["tlsCAFile"] = ca_file_path

    if CONFIG.MONGO_URL:
        mongo_options["host"] = CONFIG.MONGO_URL
    else:
        mongo_options["host"] = CONFIG.MONGO_HOST
        mongo_options["port"] = int(CONFIG.MONGO_PORT)
        mongo_options["username"] = CONFIG.MONGO_USER
        mongo_options["password"] = CONFIG.MONGO_PASSWORD

    mongo = AsyncIOMotorClient(**mongo_options)
    mongo.get_io_loop = asyncio.get_running_loop


async def fetch_item[T: "BaseSchema"](
    constructor: Type[T], item_id: str, *aspects
) -> T:
    """
    Fetch an item from local cache, then redis, then database.
    Will populate caches for later access
    """

    # should check local cache but for now just fetch from redis

    database_domain = constructor.database_domain().value

    if aspects:
        item = await redis.hmget(f"{database_domain}:{item_id}", *aspects)
        item = {x: y for x, y in zip(aspects, item) if y is not None}
    else:
        item = await redis.hgetall(f"{database_domain}:{item_id}")

    if not item:
        item = await mongo.bloxlink[database_domain].find_one(
            {"_id": item_id}, {x: True for x in aspects}
        ) or {"_id": item_id}

        if item and not isinstance(item, (list, dict)):
            if aspects:
                items = {
                    x: item[x]
                    for x in aspects
                    if item.get(x) and not isinstance(item[x], dict)
                }

                if items:
                    async with redis.pipeline() as pipeline:
                        await pipeline.hmset(f"{database_domain}:{item_id}", items)
                        await pipeline.expire(
                            f"{database_domain}:{item_id}",
                            int(datetime.timedelta(hours=1).total_seconds()),
                        )
                        await pipeline.execute()
            else:
                async with redis.pipeline() as pipeline:
                    await pipeline.hmset(f"{database_domain}:{item_id}", item)
                    await pipeline.expire(
                        f"{database_domain}:{item_id}",
                        int(datetime.timedelta(hours=1).total_seconds()),
                    )
                    await pipeline.execute()

    if item.get("_id"):
        item.pop("_id")

    item["id"] = item_id

    return constructor(**item)


async def update_item[T: "BaseSchema"](
    constructor: Type[T], item_id: str, **aspects
) -> None:
    """
    Update an item's aspects in local cache, redis, and database.
    """

    database_domain = constructor.database_domain().value

    unset_aspects = {}
    set_aspects = {}

    # arrange items into set and unset (delete)
    for key, val in aspects.items():
        if val is None:
            unset_aspects[key] = ""
        else:
            set_aspects[key] = val

    # validate the model to ensure no invalid fields are being set
    constructor.model_validate({"id": item_id, **aspects})

    # Update redis cache
    redis_set_aspects = {}
    redis_unset_aspects = {}

    for aspect_name, aspect_value in dict(aspects).items():
        if aspect_value is None:
            redis_unset_aspects[aspect_name] = aspect_value
        elif isinstance(aspect_value, (dict, list, bool)):  # TODO
            pass
        else:
            redis_set_aspects[aspect_name] = aspect_value

    if redis_set_aspects:
        async with redis.pipeline() as pipeline:
            await pipeline.hset(
                f"{database_domain}:{item_id}", mapping=redis_set_aspects
            )
            await pipeline.expire(
                f"{database_domain}:{item_id}",
                int(datetime.timedelta(hours=1).total_seconds()),
            )
            await pipeline.execute()

    if redis_unset_aspects:
        await redis.hdel(f"{database_domain}:{item_id}", *redis_unset_aspects.keys())

    # update database
    await mongo.bloxlink[database_domain].update_one(
        {"_id": item_id},
        {
            "$set": set_aspects,
            "$unset": unset_aspects,
            "$currentDate": {"updatedAt": True},
        },
        upsert=True,
    )


connect_database()
