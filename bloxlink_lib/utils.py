from typing import Callable, Coroutine, Iterable, Awaitable, Type
import logging
import asyncio
import enum
from os import getenv
import json
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


def get_node_id() -> int:
    """Gets the node ID from the hostname."""

    hostname = getenv("HOSTNAME", "bloxlink-0")

    try:
        node_id = int(hostname.split("-")[-1])
    except ValueError:
        node_id = 0

    return node_id


def get_node_count() -> int:
    """Gets the node count."""

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
            traces_sample_rate=(
                1.0 if environment in (Environment.LOCAL, Environment.STAGING) else 0.2
            ),
            attach_stacktrace=True,
        )


async def use_cached_request[T: BaseModel | dict, V](
    cache_type: enum.Enum,
    cache_id: str | int,
    model: Type[T] | Callable[[V], T],
    coroutine: Coroutine[any, any, V],
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

    cache_key = f"requests:{coroutine.__name__}:{cache_type.value}:{cache_id}"

    redis_cache = await redis.get(cache_key)

    if redis_cache:
        data = json.loads(redis_cache)

        if callable(model):
            return model(data)

        return model(**data)

    result: T = await coroutine

    parsed_model = parse_into(result, model) if not callable(model) else model(result)

    if isinstance(parsed_model, (BaseModel, dict)):
        serialized_data = json.dumps(dict(parsed_model))
    else:
        serialized_data = json.dumps(parsed_model)

    # TODO: create utility to map to Redis hashmap instead of JSON string
    await redis.set(
        name=cache_key,
        value=serialized_data,
        ex=ttl_seconds,
    )

    return result


def NO_OP(*args, **kwargs):
    """No operation function."""
    pass
