from typing import Any
from pathlib import Path

import requests

from src.metrics import (
    BITCOIN_NODE_RPC_AVAILABLE,
    BITCOIN_RPC_REQUESTS_FAILED_TOTAL,
    BITCOIN_RPC_REQUESTS_SUCCESSFUL_TOTAL,
)
from utils.logger import logger


class BitcoinRPCError(Exception):
    pass


class BitcoinRPCClient:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        cookie_file: str = "",
        timeout: float = 10.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.cookie_file = cookie_file

        self.session = requests.Session()
        if cookie_file:
            self._refresh_cookie_auth()
        else:
            self.session.auth = (username, password)

    def _refresh_cookie_auth(self) -> None:
        """Reload Bitcoin Core's rotating RPC cookie before every request."""
        value = Path(self.cookie_file).read_text().strip()
        if ":" not in value:
            raise BitcoinRPCError("Bitcoin RPC cookie has invalid format")
        username, password = value.split(":", 1)
        self.session.auth = (username, password)

    def call(self, method: str, *params: Any) -> Any:
        if self.cookie_file:
            self._refresh_cookie_auth()
        payload = {
            "jsonrpc": "2.0",
            "id": "bitcoin-fn-exporter",
            "method": method,
            "params": list(params),
        }

        logger.debug(f"Calling Bitcoin RPC method: {method}")

        try:
            response = self.session.post(
                self.url,
                json=payload,
                timeout=self.timeout,
            )

        except requests.Timeout:
            BITCOIN_NODE_RPC_AVAILABLE.set(0)

            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="timeout",
            ).inc()

            raise BitcoinRPCError(
                f"Bitcoin RPC request timed out after "
                f"{self.timeout} seconds"
            )

        except requests.ConnectionError:
            BITCOIN_NODE_RPC_AVAILABLE.set(0)

            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="connection_error",
            ).inc()

            raise BitcoinRPCError(
                f"Could not connect to Bitcoin RPC at {self.url}"
            )

        except requests.RequestException as error:
            BITCOIN_NODE_RPC_AVAILABLE.set(0)

            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="request_error",
            ).inc()

            raise BitcoinRPCError(
                f"Bitcoin RPC request failed: {error}"
            )

        try:
            data = response.json()

        except ValueError:
            BITCOIN_NODE_RPC_AVAILABLE.set(0)

            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="invalid_json",
            ).inc()

            raise BitcoinRPCError(
                f"Bitcoin RPC returned invalid JSON "
                f"(HTTP {response.status_code})"
            )

        BITCOIN_NODE_RPC_AVAILABLE.set(1)

        if data.get("error"):
            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="rpc_error",
            ).inc()

            rpc_error = data["error"]

            if isinstance(rpc_error, dict):
                code = rpc_error.get("code", "unknown")
                message = rpc_error.get(
                    "message",
                    "Unknown RPC error",
                )

                raise BitcoinRPCError(
                    f"Bitcoin RPC error {code}: {message}"
                )

            raise BitcoinRPCError(
                f"Bitcoin RPC error: {rpc_error}"
            )

        if response.status_code != 200:
            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="http_error",
            ).inc()

            raise BitcoinRPCError(
                f"Bitcoin RPC returned HTTP "
                f"{response.status_code}"
            )

        if "result" not in data:
            BITCOIN_RPC_REQUESTS_FAILED_TOTAL.labels(
                method=method,
                reason="missing_result",
            ).inc()

            raise BitcoinRPCError(
                "Bitcoin RPC response does not contain a result"
            )

        BITCOIN_RPC_REQUESTS_SUCCESSFUL_TOTAL.labels(
            method=method,
        ).inc()

        return data["result"]

    def close(self) -> None:
        self.session.close()