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
    logging.debug("Checking Sentry rate limits...")
    dsn = sentry_sdk.Hub.current.client.dsn

    # Extract the URL from the DSN
    url = dsn.get_endpoint()

    logging.debug("Got endpoints")

    try:
        # Construct the headers (mimicking what the SDK does)
        headers = {"X-Sentry-Auth": dsn.get_auth_header()}

        logging.debug("Sending request")

        # Make a test request to Sentry (e.g., HEAD request to avoid sending data)
        response = requests.head(url, headers=headers)

        # Access the rate limit headers
        limit = response.headers.get("X-Sentry-Rate-Limit-Limit")
        remaining = response.headers.get("X-Sentry-Rate-Limit-Remaining")
        reset = response.headers.get("X-Sentry-Rate-Limit-Reset")

        logging.debug("Limits: %s, %s, %s", limit, remaining, reset)

        if limit:
            logging.info(f"Rate Limit: {limit}")
            logging.info(f"Remaining: {remaining}")
            logging.info(f"Reset: {reset}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking rate limits: {e}")

    return event  # Return the event to be sent by the SDK


def init_sentry():
    """Initialize Sentry."""

    if CONFIG.SENTRY_DSN:
        logging.debug(CONFIG.SENTRY_DSN)
        sentry_sdk.init(
            dsn=CONFIG.SENTRY_DSN,
            integrations=[AioHttpIntegration()],
            before_send=sentry_before_send,
            environment=get_environment().name.lower(),
            enable_tracing=True,
            debug=True,
            attach_stacktrace=True,
        )

        try:
            1 / 0  # Force an exception
        except Exception as e:
            sentry_sdk.capture_exception(e)

        logging.debug("Test event sent.")


def NO_OP(*args, **kwargs):
    """No operation function."""
    pass
