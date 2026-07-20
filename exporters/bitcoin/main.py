import signal
import threading
import os

from socketserver import ThreadingMixIn
from typing import Callable

from prometheus_client import make_wsgi_app
from wsgiref.simple_server import (
    WSGIRequestHandler,
    WSGIServer,
    make_server,
)

from src.calls import BitcoinRPCClient
from src.collector import collect_metrics
from utils.config import config
from utils.logger import logger


shutdown_event = threading.Event()
metrics_server: WSGIServer | None = None


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    block_on_close = False
    allow_reuse_address = True
    request_queue_size = 32


class MetricsRequestHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args) -> None:
        logger.debug(f"Metrics HTTP: {format % args}")


def handle_shutdown_signal(signum, _frame) -> None:
    if shutdown_event.is_set():
        return

    signal_name = signal.Signals(signum).name
    logger.info(f"🛑 Received {signal_name}. Shutting down...")

    shutdown_event.set()

    if metrics_server is not None:
        threading.Thread(
            target=metrics_server.shutdown,
            name="prometheus-http-shutdown",
            daemon=True,
        ).start()


def print_app_config() -> None:
    logger.info("🏇 Starting the app...")
    logger.info("-------------------------------------------------")
    logger.info(f"|   App Log level:        {config.app_log_level}")
    logger.info(f"|   Prometheus host:      {config.prometheus_host}:{config.prometheus_port}")
    logger.info(f"|   Bitcoin RPC URL:      {config.bitcoin_rpc_url}")
    logger.info(f"|   Bitcoin RPC timeout:  {config.bitcoin_rpc_timeout} seconds")
    logger.info(f"|   Collection interval:  {config.prometheus_collect_interval} seconds")
    logger.info("-------------------------------------------------")


def create_metrics_app() -> Callable:
    metrics_app = make_wsgi_app()

    def app(environ, start_response):
        if environ.get("PATH_INFO") == "/metrics":
            return metrics_app(environ, start_response)

        start_response(
            "404 Not Found",
            [
                ("Content-Length", "0"),
            ],
        )

        return [b""]

    return app


def collector_loop(rpc: BitcoinRPCClient) -> None:
    while not shutdown_event.is_set():
        try:
            collect_metrics(rpc)
        except Exception:
            logger.exception("Unexpected error in metric collection loop")

        if shutdown_event.is_set():
            break

        shutdown_event.wait(
            config.prometheus_collect_interval
        )


def main() -> None:
    global metrics_server

    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    print_app_config()

    rpc = BitcoinRPCClient(
        url=config.bitcoin_rpc_url,
        username=config.bitcoin_rpc_username,
        password=config.bitcoin_rpc_password,
        cookie_file=os.getenv("BITCOIN_RPC_COOKIE_FILE", ""),
        timeout=config.bitcoin_rpc_timeout,
    )

    collector_thread = None

    try:
        metrics_server = make_server(
            config.prometheus_host,
            config.prometheus_port,
            create_metrics_app(),
            server_class=ThreadingWSGIServer,
            handler_class=MetricsRequestHandler,
        )

        collector_thread = threading.Thread(
            target=collector_loop,
            args=(rpc,),
            name="bitcoin-metrics-collector",
            daemon=True,
        )

        collector_thread.start()

        logger.info(
            f"📊 Metrics server started at "
            f"http://{config.prometheus_host}:"
            f"{config.prometheus_port}/metrics"
        )

        # HTTP server runs in the main thread.
        metrics_server.serve_forever()

    finally:
        shutdown_event.set()

        if metrics_server is not None:
            metrics_server.server_close()

        if collector_thread is not None:
            collector_thread.join(
                timeout=config.bitcoin_rpc_timeout + 5
            )

            if collector_thread.is_alive():
                logger.warning(
                    "⚠️ Collector thread did not stop within the timeout"
                )

        rpc.close()
        logger.info("🔌 Bitcoin RPC session closed")
        logger.info("📊 Metrics server stopped")


if __name__ == "__main__":
    main()