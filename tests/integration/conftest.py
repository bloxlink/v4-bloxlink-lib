import asyncio
from typing import Final

import pytest_asyncio
from bloxlink_lib.database.redis import (  # pylint: disable=no-name-in-module
    wait_for_redis as wait_for_redis_,
)
from bloxlink_lib.database.mongodb import mongo

TEST_GUILD_ID: Final[int] = 123


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop

    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
def start_docker_services(docker_services):  # pylint: disable=unused-argument
    """Start the Docker services."""


@pytest_asyncio.fixture(scope="function", autouse=True)
async def wait_for_redis():
    """Wait for Redis to be ready."""

    await wait_for_redis_()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_clean_guild_data(
    docker_services, wait_for_redis
):  # pylint: disable=unused-argument
    """Starts the database fresh for each test."""

    # Setup (nothing to do)
    yield

    # Teardown (runs after each test)
    await mongo.bloxlink.guilds.delete_one({"_id": TEST_GUILD_ID})


@pytest_asyncio.fixture(scope="session")
async def test_guild_id():
    """Returns the test guild ID."""

    return TEST_GUILD_ID
