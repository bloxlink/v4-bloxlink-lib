import logging
import contextlib
import time
import threading
import uvicorn
from fastapi import APIRouter, FastAPI
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest
from .config import CONFIG

router = APIRouter(tags=["Metrics"])


@router.get("/")
async def metrics():
    """Endpoint to get the metrics for the service."""

    return PlainTextResponse(generate_latest())


class MetricsServer(uvicorn.Server):
    """
    A custom server that runs in a separate thread for metrics.
    """

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


if __name__ == "__main__":
    if not CONFIG.METRICS_ENABLED:
        logging.info(
            "Metrics are disabled. To enable metrics, set METRICS_ENABLED to True."
        )

    app = FastAPI()
    app.include_router(router)

    logging.info(
        f"Starting metrics server on {CONFIG.METRICS_HOST}:{CONFIG.METRICS_PORT}"
    )

    config = uvicorn.Config(
        app,
        host=CONFIG.METRICS_HOST,
        port=int(CONFIG.METRICS_PORT),
        log_level=CONFIG.LOG_LEVEL.lower(),
    )
    server = MetricsServer(config=config)

    with server.run_in_thread():
        logging.info("Metrics server started")
        while True:
            time.sleep(1)
