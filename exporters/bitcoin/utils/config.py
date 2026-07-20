import argparse
import os
from dataclasses import dataclass

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Built-in defaults
# ---------------------------------------------------------------------------

DEFAULT_BITCOIN_RPC_IP = "127.0.0.1"
DEFAULT_BITCOIN_RPC_PORT = 38332
DEFAULT_BITCOIN_RPC_TIMEOUT = 10.0

DEFAULT_PROMETHEUS_HOST = "127.0.0.1"
DEFAULT_PROMETHEUS_PORT = 9097
DEFAULT_PROMETHEUS_COLLECT_INTERVAL = 15.0

DEFAULT_APP_LOG_LEVEL = "INFO"


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {name} must be an integer, got: {value!r}"
        ) from error


def get_env_float(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {name} must be a number, got: {value!r}"
        ) from error


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bitcoin Fullnode Prometheus Exporter",
        epilog="Config priority: CLI flags --> .env --> built-in defaults\n\n"
    )

    parser.add_argument(
        "--bitcoin-rpc-ip",
        default=None,
        help=(
            f"Bitcoin RPC host "
            f"(default: {DEFAULT_BITCOIN_RPC_IP})"
        ),
    )

    parser.add_argument(
        "--bitcoin-rpc-port",
        type=int,
        default=None,
        help=(
            f"Bitcoin RPC port "
            f"(default: {DEFAULT_BITCOIN_RPC_PORT})"
        ),
    )

    parser.add_argument(
        "--bitcoin-rpc-timeout",
        type=float,
        default=None,
        help=(
            f"Bitcoin RPC response timeout in seconds "
            f"(default: {DEFAULT_BITCOIN_RPC_TIMEOUT})"
        ),
    )

    parser.add_argument(
        "--prometheus-host",
        default=None,
        help=(
            f"Prometheus metrics bind host "
            f"(default: {DEFAULT_PROMETHEUS_HOST})"
        ),
    )

    parser.add_argument(
        "--prometheus-port",
        type=int,
        default=None,
        help=(
            f"Prometheus metrics server port "
            f"(default: {DEFAULT_PROMETHEUS_PORT})"
        ),
    )

    parser.add_argument(
        "--collect-interval",
        type=float,
        default=None,
        help=(
            f"Metrics collection interval in seconds "
            f"(default: {DEFAULT_PROMETHEUS_COLLECT_INTERVAL})"
        ),
    )

    parser.add_argument(
        "--app-log-level",
        default=None,
        help=(
            f"Application log level "
            f"(default: {DEFAULT_APP_LOG_LEVEL})"
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Config:
    bitcoin_rpc_username: str
    bitcoin_rpc_password: str
    bitcoin_rpc_ip: str
    bitcoin_rpc_port: int
    bitcoin_rpc_timeout: float

    prometheus_host: str
    prometheus_port: int
    prometheus_collect_interval: float

    app_log_level: str

    @property
    def bitcoin_rpc_url(self) -> str:
        return (
            f"http://{self.bitcoin_rpc_ip}:"
            f"{self.bitcoin_rpc_port}"
        )


def load_config() -> Config:
    args = parse_args()

    bitcoin_rpc_username = os.getenv(
        "BITCOIN_RPC_USERNAME",
        "",
    )

    bitcoin_rpc_password = os.getenv(
        "BITCOIN_RPC_PASSWORD",
        "",
    )

    bitcoin_rpc_ip = (
        args.bitcoin_rpc_ip
        if args.bitcoin_rpc_ip is not None
        else os.getenv(
            "BITCOIN_RPC_IP",
            DEFAULT_BITCOIN_RPC_IP,
        )
    )

    bitcoin_rpc_port = (
        args.bitcoin_rpc_port
        if args.bitcoin_rpc_port is not None
        else get_env_int(
            "BITCOIN_RPC_PORT",
            DEFAULT_BITCOIN_RPC_PORT,
        )
    )

    bitcoin_rpc_timeout = (
        args.bitcoin_rpc_timeout
        if args.bitcoin_rpc_timeout is not None
        else get_env_float(
            "BITCOIN_RPC_TIMEOUT",
            DEFAULT_BITCOIN_RPC_TIMEOUT,
        )
    )

    prometheus_host = (
        args.prometheus_host
        if args.prometheus_host is not None
        else os.getenv(
            "PROMETHEUS_HOST",
            DEFAULT_PROMETHEUS_HOST,
        )
    )

    prometheus_port = (
        args.prometheus_port
        if args.prometheus_port is not None
        else get_env_int(
            "PROMETHEUS_PORT",
            DEFAULT_PROMETHEUS_PORT,
        )
    )

    prometheus_collect_interval = (
        args.collect_interval
        if args.collect_interval is not None
        else get_env_float(
            "PROMETHEUS_COLLECT_INTERVAL",
            DEFAULT_PROMETHEUS_COLLECT_INTERVAL,
        )
    )

    app_log_level = (
        args.app_log_level
        if args.app_log_level is not None
        else os.getenv(
            "APP_LOG_LEVEL",
            DEFAULT_APP_LOG_LEVEL,
        )
    ).upper()

    return Config(
        bitcoin_rpc_username=bitcoin_rpc_username,
        bitcoin_rpc_password=bitcoin_rpc_password,
        bitcoin_rpc_ip=bitcoin_rpc_ip,
        bitcoin_rpc_port=bitcoin_rpc_port,
        bitcoin_rpc_timeout=bitcoin_rpc_timeout,
        prometheus_host=prometheus_host,
        prometheus_port=prometheus_port,
        prometheus_collect_interval=prometheus_collect_interval,
        app_log_level=app_log_level,
    )


config = load_config()