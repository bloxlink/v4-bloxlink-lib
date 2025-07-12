import logging

from .models.base import *
from .models import *
from .models.schemas.guilds import *  # pylint: disable=no-name-in-module
from .models.schemas.users import *  # pylint: disable=no-name-in-module
from .models.roblox import *
from .models.roblox.binds import *
from .models.binds import *
from .models.v3_binds import *
from .exceptions import *
from .utils import *
from .fetch import *
from .config import *
from .module import *
from .database.mongodb import fetch_item, update_item
from .database.redis import redis
from .metrics import start_metrics_server

logging.basicConfig(level=CONFIG.LOG_LEVEL)

init_sentry()
start_metrics_server()
