import logging
import uvicorn
from bloxlink_lib.utils import create_task_log_exception
from .config import CONFIG
from fastapi import APIRouter, FastAPI
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

router = APIRouter(tags=["Metrics"])


@router.get("/")
async def metrics():
    """Endpoint to get the metrics for the service."""

    return PlainTextResponse(generate_latest())


async def main():
    """Starts the metrics server."""

    if not CONFIG.METRICS_ENABLED:
        logging.info(
            "Metrics are disabled. To enable metrics, set METRICS_ENABLED to True."
        )
        return

    logging.info(
        f"Starting metrics server on {CONFIG.METRICS_HOST}:{CONFIG.METRICS_PORT}"
    )

    app = FastAPI()
    app.include_router(router)

    config = uvicorn.Config(
        app,
        host=CONFIG.METRICS_HOST,
        port=int(CONFIG.METRICS_PORT),
        log_level=CONFIG.LOG_LEVEL.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


create_task_log_exception(main())
