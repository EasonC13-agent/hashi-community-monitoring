#!/usr/bin/env python3
"""Probe every endpoint in a Hashi on-chain committee roster."""
import concurrent.futures
import hashlib
import ipaddress
import json
import os
import socket
import ssl
import subprocess
import threading
import time

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROSTER = Path(os.getenv("ROSTER_FILE", "/data/committee.json"))
PORT = int(os.getenv("PORT", "19101"))
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "60"))
TIMEOUT = float(os.getenv("PROBE_TIMEOUT_SECONDS", "5"))
WORKERS = int(os.getenv("PROBE_WORKERS", "24"))
SERVICE_INFO_REFRESH_SECONDS = int(os.getenv("SERVICE_INFO_REFRESH_SECONDS", "300"))
NETWORK = os.getenv("NETWORK", "testnet")
_lock = threading.Lock()
_metrics = ""
_service_cache_lock = threading.Lock()
_service_cache = {}


def esc(value):
    return str(value or "").replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def labels(member):
    endpoint = member.get("endpoint") or ""
    host = urlparse(endpoint).hostname or ""
    values = {
        "network": NETWORK,
        "validator": member.get("validator", ""),
        "operator": member.get("operator", ""),
        "endpoint": endpoint,
        "host": host,
    }
    return ",".join(f'{k}="{esc(v)}"' for k, v in values.items())


def _probe_once(member):
    started = time.monotonic()
    endpoint = member.get("endpoint")
    result = {"dns": 0, "safe": 0, "tcp": 0, "tls": 0, "h2": 0, "duration": 0.0, "fingerprint": "", "target_ip": "", "service_info": 0, "server": "", "reported_epoch": 0, "checkpoint": 0}
    if not endpoint:
        result["duration"] = time.monotonic() - started
        return member, result
    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        result["duration"] = time.monotonic() - started
        return member, result
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        result["dns"] = 1 if addresses else 0
        public = [item for item in addresses if ipaddress.ip_address(item[4][0]).is_global]
        if not public:
            result["duration"] = time.monotonic() - started
            return member, result
        result["safe"] = 1
        family, socktype, proto, _, sockaddr = public[0]
        result["target_ip"] = sockaddr[0]
        raw = socket.socket(family, socktype, proto)
        raw.settimeout(TIMEOUT)
        raw.connect(sockaddr)
        result["tcp"] = 1
        if parsed.scheme == "https":
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.set_alpn_protocols(["h2"])
            with context.wrap_socket(raw, server_hostname=host) as tls:
                result["tls"] = 1
                result["h2"] = 1 if tls.selected_alpn_protocol() == "h2" else 0
                der = tls.getpeercert(binary_form=True)
                if der:
                    result["fingerprint"] = hashlib.sha256(der).hexdigest()
        else:
            raw.close()
    except Exception:
        pass
    result["duration"] = time.monotonic() - started
    return member, result


def probe(member):
    first_member, first = _probe_once(member)
    if first["h2"] or not first["safe"]:
        chosen_member, chosen = first_member, first
    else:
        time.sleep(0.25)
        second_member, second = _probe_once(member)
        first_score = (first["h2"], first["tls"], first["tcp"], first["dns"])
        second_score = (second["h2"], second["tls"], second["tcp"], second["dns"])
        chosen_member, chosen = (second_member, second) if second_score > first_score else (first_member, first)
        chosen["duration"] = first["duration"] + second["duration"] + 0.25
    if chosen["h2"]:
        query_service_info(chosen_member, chosen)
    return chosen_member, chosen


def query_service_info(member, result):
    cache_key = member["endpoint"]
    with _service_cache_lock:
        cached = _service_cache.get(cache_key)
    if cached and time.time() - cached[0] < SERVICE_INFO_REFRESH_SECONDS:
        result.update(cached[1])
        return
    parsed = urlparse(member["endpoint"])
    host = parsed.hostname
    port = parsed.port or 443
    ip = result["target_ip"]
    target = f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"
    command = [
        "/usr/local/bin/grpcurl", "-insecure", "-max-time", str(max(1, int(TIMEOUT))),
        "-authority", host, "-import-path", "/app", "-proto", "service_info.proto", "-d", "{}",
        target, "sui.hashi.v1alpha.BridgeService/GetServiceInfo",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT + 2)
        if completed.returncode != 0:
            return
        payload = json.loads(completed.stdout or "{}")
        result["service_info"] = 1
        result["server"] = payload.get("server", "")
        result["reported_epoch"] = int(payload.get("epoch", 0))
        result["checkpoint"] = int(payload.get("checkpointHeight", 0))
        cached_result = {key: result[key] for key in ("service_info", "server", "reported_epoch", "checkpoint")}
        with _service_cache_lock:
            _service_cache[cache_key] = (time.time(), cached_result)
    except Exception:
        return


def load_roster():
    payload = json.loads(ROSTER.read_text())
    if isinstance(payload, list):
        return {"updated_at": int(ROSTER.stat().st_mtime), "members": payload}
    return payload


def render():
    try:
        roster = load_roster()
        members = roster.get("members", [])
        updated_at = int(roster.get("updated_at", ROSTER.stat().st_mtime))
    except Exception as error:
        print(f"roster load failed: {error}", flush=True)
        return "# HELP hashi_network_roster_load_success Whether committee roster loaded.\n# TYPE hashi_network_roster_load_success gauge\nhashi_network_roster_load_success 0\n"
    epoch = max((int(x.get("epoch", 0)) for x in members), default=0)
    lines = [
        "# HELP hashi_network_roster_load_success Whether committee roster loaded.", "# TYPE hashi_network_roster_load_success gauge", "hashi_network_roster_load_success 1",
        "# HELP hashi_network_committee_epoch Current discovered Hashi committee epoch.", "# TYPE hashi_network_committee_epoch gauge", f'hashi_network_committee_epoch{{network="{esc(NETWORK)}"}} {epoch}',
        "# HELP hashi_network_committee_members Number of discovered current committee members.", "# TYPE hashi_network_committee_members gauge", f'hashi_network_committee_members{{network="{esc(NETWORK)}"}} {len(members)}',
        "# HELP hashi_network_roster_age_seconds Age of the last successful on-chain discovery.", "# TYPE hashi_network_roster_age_seconds gauge", f'hashi_network_roster_age_seconds{{network="{esc(NETWORK)}"}} {max(0, int(time.time())-updated_at)}',
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(probe, members))
    for member, result in results:
        lab = labels(member)
        lines.extend([
            f'hashi_network_member_info{{{lab}}} 1',
            f'hashi_network_endpoint_dns_ok{{{lab}}} {result["dns"]}',
            f'hashi_network_endpoint_target_safe{{{lab}}} {result["safe"]}',
            f'hashi_network_endpoint_tcp_up{{{lab}}} {result["tcp"]}',
            f'hashi_network_endpoint_tls_up{{{lab}}} {result["tls"]}',
            f'hashi_network_endpoint_http2_ready{{{lab}}} {result["h2"]}',
            f'hashi_network_endpoint_probe_duration_seconds{{{lab}}} {result["duration"]:.6f}',
            f'hashi_network_endpoint_service_info_success{{{lab}}} {result["service_info"]}',
            f'hashi_network_endpoint_version_reporting{{{lab}}} {1 if result["server"] else 0}',
            f'hashi_network_endpoint_reported_epoch{{{lab}}} {result["reported_epoch"]}',
            f'hashi_network_endpoint_reported_checkpoint{{{lab}}} {result["checkpoint"]}',
        ])
        if result["server"]:
            lines.append(f'hashi_network_endpoint_version_info{{{lab},server="{esc(result["server"])}"}} 1')
        if result["fingerprint"]:
            lines.append(f'hashi_network_endpoint_cert_info{{{lab},sha256="{result["fingerprint"]}"}} 1')
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
        if self.path == "/-/healthy":
            body = b"ok\n"
        elif self.path == "/metrics":
            with _lock:
                body = _metrics.encode()
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, format, *args): return


if __name__ == "__main__":
    _metrics = render()
    threading.Thread(target=updater, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
