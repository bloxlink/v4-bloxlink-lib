import logging
import time
import threading
import uvicorn
from fastapi import APIRouter, FastAPI
from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest
from .config import CONFIG

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def metrics():
    """Endpoint to get the metrics for the service"""

    return PlainTextResponse(generate_latest())


class MetricsServer:
    """A background metrics server that runs in a separate thread"""

    def __init__(self):
        self.server = None
        self.thread = None
        self.started = False

    def start(self):
        """Start the metrics server in a background thread"""

        if self.started:
            logging.warning("Metrics server is already running")
            return

        app = FastAPI()
        app.include_router(router)

        config = uvicorn.Config(
            app,
            host=CONFIG.METRICS_HOST,
            port=int(CONFIG._METRICS_PORT),
            log_level=CONFIG.LOG_LEVEL.lower(),
        )
        self.server = uvicorn.Server(config=config)

        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

        # Wait for server to start
        for _ in range(100):  # Wait up to 10 seconds
            if self.started:
                break

            time.sleep(0.1)

        if self.started:
            logging.info(
                f"Metrics server started on {CONFIG.METRICS_HOST}:{CONFIG._METRICS_PORT}"
            )
        else:
            logging.error("Failed to start metrics server")

    def _run_server(self):
        """Internal method to run the server"""

        try:
            self.started = True
            self.server.run()

        except Exception as e:
            logging.error(f"Error running metrics server: {e}")

        finally:
            self.started = False

    def stop(self):
        """Stop the metrics server"""

        if not self.started:
            return

        if self.server:
            self.server.should_exit = True

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        self.started = False

        logging.info("Metrics server stopped")

    def is_running(self):
        """Check if the metrics server is running"""

        return self.started and self.thread and self.thread.is_alive()


def start_metrics_server():
    """Start the metrics server in the background"""

    if not CONFIG.METRICS_ENABLED:
        logging.info(
            "Metrics are disabled. To enable metrics, set METRICS_ENABLED to True."
        )
        return

    server = MetricsServer()
    server.start()
