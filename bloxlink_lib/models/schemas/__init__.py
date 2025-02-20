from bloxlink_lib.database.redis import redis
from bloxlink_lib.models.base.serializable import GuildSerializable, MemberSerializable
from bloxlink_lib.models.schemas.guilds import *
from bloxlink_lib.models.schemas.users import *


async def fetch_item[T](domain: str, constructor: Type[T], item_id: str, *aspects) -> T:
    """
    Fetch an item from local cache, then redis, then database.
    Will populate caches for later access
    """
    # should check local cache but for now just fetch from redis

    if aspects:
        item = await redis.hmget(f"{domain}:{item_id}", *aspects)
        item = {x: y for x, y in zip(aspects, item) if y is not None}
    else:
        item = await redis.hgetall(f"{domain}:{item_id}")

    if not item:
        item = await mongo.bloxlink[domain].find_one(
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
                        await pipeline.hmset(f"{domain}:{item_id}", items)
                        await pipeline.expire(
                            f"{domain}:{item_id}",
                            int(datetime.timedelta(hours=1).total_seconds()),
                        )
                        await pipeline.execute()
            else:
                async with redis.pipeline() as pipeline:
                    await pipeline.hmset(f"{domain}:{item_id}", item)
                    await pipeline.expire(
                        f"{domain}:{item_id}",
                        int(datetime.timedelta(hours=1).total_seconds()),
                    )
                    await pipeline.execute()

    if item.get("_id"):
        item.pop("_id")

    item["id"] = item_id

    return constructor(**item)


async def update_item(domain: str, item_id: str, **aspects) -> None:
    """
    Update an item's aspects in local cache, redis, and database.
    """

    unset_aspects = {}
    set_aspects = {}

    for key, val in aspects.items():
        if val is None:
            unset_aspects[key] = ""
        else:
            set_aspects[key] = val

    # check if the model is valid
    if domain == "users":
        schemas.UserData(id=item_id, **set_aspects)
    elif domain == "guilds":
        schemas.GuildData(id=item_id, **set_aspects)

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
            await pipeline.hset(f"{domain}:{item_id}", mapping=redis_set_aspects)
            await pipeline.expire(
                f"{domain}:{item_id}", int(datetime.timedelta(hours=1).total_seconds())
            )
            await pipeline.execute()

    if redis_unset_aspects:
        await redis.hdel(f"{domain}:{item_id}", *redis_unset_aspects.keys())

    # update database
    await mongo.bloxlink[domain].update_one(
        {"_id": item_id}, {"$set": set_aspects, "$unset": unset_aspects}, upsert=True
    )


async def fetch_user_data(
    user: str | int | dict | MemberSerializable, *aspects
) -> schemas.UserData:
    """
    Fetch a full user from local cache, then redis, then database.
    Will populate caches for later access
    """

    if isinstance(user, dict):
        user_id = str(user["id"])
    elif isinstance(user, MemberSerializable):
        user_id = str(user.id)
    else:
        user_id = str(user)

    return await fetch_item("users", schemas.UserData, user_id, *aspects)


async def fetch_guild_data(
    guild: str | int | dict | GuildSerializable, *aspects
) -> GuildData:
    """
    Fetch a full guild from local cache, then redis, then database.
    Will populate caches for later access
    """

    if isinstance(guild, dict):
        guild_id = str(guild["id"])
    elif isinstance(guild, GuildSerializable):
        guild_id = str(guild.id)
    else:
        guild_id = str(guild)

    return await fetch_item("guilds", GuildData, guild_id, *aspects)


async def update_user_data(
    user: str | int | dict | MemberSerializable, **aspects
) -> None:
    """
    Update a user's aspects in local cache, redis, and database.
    """

    if isinstance(user, dict):
        user_id = str(user["id"])
    elif isinstance(user, MemberSerializable):
        user_id = str(user.id)
    else:
        user_id = str(user)

    return await update_item("users", user_id, **aspects)


async def update_guild_data(
    guild: str | int | dict | GuildSerializable, **aspects
) -> None:
    """
    Update a guild's aspects in local cache, redis, and database.
    """

    if isinstance(guild, dict):
        guild_id = str(guild["id"])
    elif isinstance(guild, GuildSerializable):
        guild_id = str(guild.id)
    else:
        guild_id = str(guild)

    return await update_item("guilds", guild_id, **aspects)
