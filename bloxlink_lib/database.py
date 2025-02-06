from __future__ import annotations

import asyncio
from os.path import exists

from motor.motor_asyncio import AsyncIOMotorClient
from .config import CONFIG

mongo: AsyncIOMotorClient = None


def connect_database():
    global mongo  # pylint: disable=global-statement

    mongo_options: dict[str, str | int] = {}

    if CONFIG.MONGO_CA_FILE:
        ca_file = exists("cert.crt")

        if not ca_file:
            with open("src/cert.crt", "w", encoding="utf-8") as f:
                f.write(CONFIG.MONGO_CA_FILE)

        mongo_options["tlsCAFile"] = "src/cert.crt"

    if CONFIG.MONGO_URL:
        mongo_options["host"] = CONFIG.MONGO_URL
    else:
        mongo_options["host"] = CONFIG.MONGO_HOST
        mongo_options["port"] = int(CONFIG.MONGO_PORT)
        mongo_options["username"] = CONFIG.MONGO_USER
        mongo_options["password"] = CONFIG.MONGO_PASSWORD

    mongo = AsyncIOMotorClient(**mongo_options)
    mongo.get_io_loop = asyncio.get_running_loop


connect_database()
