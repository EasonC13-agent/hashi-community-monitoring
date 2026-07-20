#!/usr/bin/env python3
"""Expose Sui Address Balance as Prometheus metrics using the public Sui GraphQL API."""
import json
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GRAPHQL_URL = os.getenv("SUI_GRAPHQL_URL", "https://graphql.testnet.sui.io/graphql")
PORT = int(os.getenv("PORT", "19100"))
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "60"))
NODES = json.loads(os.environ["NODES_JSON"])

_lock = threading.Lock()
_metrics = ""


def esc(value):
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def query_balance(address):
    query = "query($a:SuiAddress!){address(address:$a){balance(coinType:\"0x2::sui::SUI\"){coinBalance addressBalance totalBalance}}}"
    body = json.dumps({"query": query, "variables": {"a": address}}).encode()
    request = urllib.request.Request(GRAPHQL_URL, data=body, headers={"Content-Type": "application/json", "User-Agent": "hashi-community-monitoring/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result["data"]["address"]["balance"]


def render():
    lines = [
        "# HELP hashi_operator_sui_balance_mist Operator total SUI balance in MIST.",
        "# TYPE hashi_operator_sui_balance_mist gauge",
        "# HELP hashi_operator_sui_address_balance_mist Operator SUI Address Balance in MIST.",
        "# TYPE hashi_operator_sui_address_balance_mist gauge",
        "# HELP hashi_operator_sui_coin_balance_mist Operator owned coin-object balance in MIST.",
        "# TYPE hashi_operator_sui_coin_balance_mist gauge",
        "# HELP hashi_operator_sui_balance_scrape_success Whether the latest Sui GraphQL balance query succeeded.",
        "# TYPE hashi_operator_sui_balance_scrape_success gauge",
    ]
    for node in NODES:
        labels = ",".join(f'{key}="{esc(node.get(key, ""))}"' for key in ("network", "operator", "node", "validator", "address"))
        try:
            balance = query_balance(node["address"])
            lines.extend([
                f'hashi_operator_sui_balance_mist{{{labels}}} {int(balance["totalBalance"])}',
                f'hashi_operator_sui_address_balance_mist{{{labels}}} {int(balance["addressBalance"])}',
                f'hashi_operator_sui_coin_balance_mist{{{labels}}} {int(balance["coinBalance"])}',
                f'hashi_operator_sui_balance_scrape_success{{{labels}}} 1',
            ])
        except Exception as error:
            lines.append(f'hashi_operator_sui_balance_scrape_success{{{labels}}} 0')
            print(f"balance query failed for {node.get('node')}: {error}", flush=True)
    return "\n".join(lines) + "\n"


def updater():
    global _metrics
    while True:
        rendered = render()
        with _lock:
            _metrics = rendered
        time.sleep(REFRESH_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/metrics", "/-/healthy"):
            self.send_error(404)
            return
        if self.path == "/-/healthy":
            body = b"ok\n"
        else:
            with _lock:
                body = _metrics.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    _metrics = render()
    threading.Thread(target=updater, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
