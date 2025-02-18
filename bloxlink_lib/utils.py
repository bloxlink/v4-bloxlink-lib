from typing import Callable, Iterable, Awaitable, Type
import logging
import asyncio
import enum
from os import getenv
import requests
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from .models.base import BaseModel
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


def sentry_before_send(event, hint):
    # Get the DSN
    dsn = sentry_sdk.Hub.current.client.dsn

    # Extract the URL from the DSN
    url = dsn.get_endpoint()

    try:
        # Construct the headers (mimicking what the SDK does)
        headers = {"X-Sentry-Auth": dsn.get_auth_header()}

        # Make a test request to Sentry (e.g., HEAD request to avoid sending data)
        response = requests.head(url, headers=headers)

        # Access the rate limit headers
        limit = response.headers.get("X-Sentry-Rate-Limit-Limit")
        remaining = response.headers.get("X-Sentry-Rate-Limit-Remaining")
        reset = response.headers.get("X-Sentry-Rate-Limit-Reset")

        if limit:
            print(f"Rate Limit: {limit}")
            print(f"Remaining: {remaining}")
            print(f"Reset: {reset}")
            # Do something with this information (e.g., log it)

    except requests.exceptions.RequestException as e:
        print(f"Error checking rate limits: {e}")

    return event  # Return the event to be sent by the SDK


def init_sentry():
    """Initialize Sentry."""

    if CONFIG.SENTRY_DSN:
        print(CONFIG.SENTRY_DSN)
        # sentry_sdk.init(
        #     environment=get_environment().name.lower(),
        #     dsn=CONFIG.SENTRY_DSN,
        #     integrations=[AioHttpIntegration()],
        #     enable_tracing=True,
        #     debug=True,
        #     attach_stacktrace=True,
        # )

        sentry_sdk.init(
            CONFIG.SENTRY_DSN,
            before_send=sentry_before_send,
        )  # Replace with your actual DSN

        try:
            1 / 0  # Force an exception
        except Exception as e:
            sentry_sdk.capture_exception(e)

        print("Test event sent (hopefully).")


def NO_OP(*args, **kwargs):
    """No operation function."""
    pass
