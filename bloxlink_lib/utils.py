from typing import Callable, Coroutine, Iterable, Awaitable, Type, TypeVar
import logging
import asyncio
from inspect import isfunction
import enum
import json
from aiohttp import ClientConnectorError
import hikari
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from .models.base import BaseModel
from .database.redis import redis
from .config import CONFIG


class Environment(enum.Enum):
    """Environment types."""

    LOCAL = 1
    STAGING = 2
    PRODUCTION = 3


T = TypeVar("T")
V = TypeVar("V")

CachableCallable = Type[T] | Callable[[V], T]


def find[T](predicate: Callable[[T], bool], iterable: Iterable[T]) -> T | None:
    """Finds the first element in an iterable that matches the predicate."""

    for element in iterable:
        try:
            if predicate(element):
                return element

        except TypeError:
            if predicate(*element):
                return element

    return None


def create_task_log_exception(awaitable: Awaitable) -> asyncio.Task:
    """Creates a task that logs exceptions."""
    # https://stackoverflow.com/questions/30361824/asynchronous-exception-handling-in-python

    async def _log_exception(awaitable):
        try:
            return await awaitable

        except Exception as e:  # pylint: disable=broad-except
            logging.exception(e)

    return asyncio.create_task(_log_exception(awaitable))


async def _set_shard_config():
    """Sets the shard config in Redis."""

    existing_shard_count = await redis.get(f"bloxlink:{CONFIG.BOT_RELEASE}:shard_count")
    existing_shards_per_node = await redis.get(
        f"bloxlink:{CONFIG.BOT_RELEASE}:shards_per_node"
    )

    if not existing_shard_count or existing_shard_count != CONFIG.SHARD_COUNT:
        await redis.set(
            f"bloxlink:{CONFIG.BOT_RELEASE}:shard_count", CONFIG.SHARD_COUNT
        )

    if (
        not existing_shards_per_node
        or existing_shards_per_node != CONFIG.SHARDS_PER_NODE
    ):
        await redis.set(
            f"bloxlink:{CONFIG.BOT_RELEASE}:shards_per_node",
            CONFIG.SHARDS_PER_NODE,
        )


async def get_node_id() -> int:
    """Gets a unique node ID by atomically incrementing a Redis counter.

    This function uses a Redis lock to ensure only one process increments the counter at a time.
    When the counter reaches the node count, it wraps around to 0.

    Returns:
        int: The node ID for this process
    """

    if not (CONFIG.SHARD_COUNT and CONFIG.SHARDS_PER_NODE):
        raise RuntimeError("Shard count and shards per node must be set")

    lock = redis.lock(
        f"bloxlink:{CONFIG.BOT_RELEASE}:node_id",
        blocking=True,
        timeout=CONFIG.NODE_LOCK_TTL,
    )

    try:
        if await lock.acquire():
            logging.debug("Acquired lock for node ID allocation")

            counter_key = f"bloxlink:{CONFIG.BOT_RELEASE}:node_id_counter"
            node_id = await redis.incr(counter_key)
            node_id -= 1

            node_count = get_node_count()
            logging.debug(f"Allocated Node ID: {node_id}, Max Node Count: {node_count}")

            if node_id >= node_count - 1:
                logging.debug(
                    f"Resetting node ID counter (reached max of {node_count})"
                )
                await redis.set(counter_key, "0")

            await _set_shard_config()

            return int(node_id % node_count)

    finally:
        if lock and await lock.locked():
            await lock.release()
            logging.debug("Released node ID allocation lock")


def get_node_count() -> int:
    """Gets the node count."""

    if not (CONFIG.SHARD_COUNT and CONFIG.SHARDS_PER_NODE):
        raise RuntimeError("Shard count and shards per node must be set")

    shards_per_node = CONFIG.SHARDS_PER_NODE
    shard_count = CONFIG.SHARD_COUNT

    return shard_count // shards_per_node


def parse_into[T: BaseModel | dict](data: dict, model: Type[T]) -> T:
    """Parse a dictionary into a dataclass.

    Args:
        data (dict): The dictionary to parse.
        model (Type[T]): The dataclass to parse the dictionary into.

    Returns:
        T: The dataclass instance of the response.
    """

    if issubclass(model, BaseModel):
        # Filter only relevant fields before constructing the pydantic instance
        relevant_fields = {
            field_name: data.get(field_name, data.get(field.alias))
            for field_name, field in model.model_fields.items()
            if field_name in data or field.alias in data
        }

        return model(**relevant_fields)

    return model(**data)


def get_environment() -> Environment:
    """Get whether this is local, staging or production."""

    bot_release = CONFIG.BOT_RELEASE

    if bot_release == "LOCAL":
        return Environment.LOCAL
    if bot_release == "CANARY":
        return Environment.STAGING

    return Environment.PRODUCTION


def init_sentry():
    """Initialize Sentry."""

    environment = get_environment()

    if CONFIG.SENTRY_DSN:
        sentry_sdk.init(
            environment=environment.name.lower(),
            dsn=CONFIG.SENTRY_DSN,
            integrations=[AioHttpIntegration()],
            enable_tracing=True,
            debug=environment in (Environment.LOCAL, Environment.STAGING),
            traces_sample_rate=0.01,
            sample_rate=0.01,
            ignore_errors=[
                StopAsyncIteration,
                ClientConnectorError,
                "ForbiddenError",
                "NotFoundError",
                "HTTPError",
                "BadSignatureError",
                "RobloxDown",
            ],
        )


class JSONSerializer(json.JSONEncoder):
    """JSON serializer that serializes BaseModel instances to dictionaries."""

    def default(self, o):
        """Serialize the object to JSON."""

        match o:
            case BaseModel():
                return dict(o)
            case _:
                try:
                    iter(o)
                except TypeError:
                    pass
                else:
                    if all(issubclass(item, BaseModel) for item in o):
                        return [dict(item) for item in o]

                    return list(o)

                return super().default(o)


class JSONDecoder(json.JSONDecoder):
    """JSON decoder that deserializes dictionaries to BaseModel instances."""

    def __init__(self, model: CachableCallable, *args, **kwargs):
        self.model = model

        super().__init__(object_hook=self.custom_object_hook, *args, **kwargs)

    def custom_object_hook(self, obj):
        """Deserialize the object from JSON."""

        try:
            iter(obj)
        except TypeError:
            pass
        else:
            if all(issubclass(item, BaseModel) for item in obj):
                return [self.model(item) for item in obj]

            return list(obj)

        return self.model(**obj)


async def use_cached_request(
    cache_type: enum.Enum,
    cache_id: str | int,
    model: CachableCallable[T, V],
    request_coroutine: Coroutine[any, any, V],
    *,
    cache_encoder: Callable[[T, V], V] | None = None,
    cache_decoder: Callable[[dict | str], T] | None = None,
    ttl_seconds: int = 10,
) -> T:
    """
    Return the cached response if it exists, otherwise run the coroutine and cache the response.
    The cached item is stored in Redis as JSON.

    If model is callable, the function is executed and then stored in Redis as a string.
    """

    if ttl_seconds is None:
        raise ValueError("ttl_seconds must be set")

    if ttl_seconds < 1:
        raise ValueError("ttl_seconds must be greater than 0")

    cache_key = f"requests:{request_coroutine.__name__}:{cache_type.value}:{cache_id}"
    redis_cache = await redis.get(cache_key)

    if redis_cache:
        data = json.loads(redis_cache)

        if cache_decoder:
            return cache_decoder(data)

        if isfunction(model):
            return model(data)

        return model(**data)

    result = await request_coroutine

    if cache_encoder:
        parsed_model = cache_encoder(model, result)
    else:
        parsed_model = model(result) if isfunction(model) else parse_into(result, model)

    serialized_data = json.dumps(parsed_model, cls=JSONSerializer)

    # TODO: create utility to map to Redis hashmap instead of JSON string
    await redis.set(
        name=cache_key,
        value=serialized_data,
        ex=ttl_seconds,
    )

    return parsed_model


def NO_OP(*args, **kwargs):
    """No operation function."""
    pass
