#!/usr/bin/env bash
set -Eeuo pipefail
BASE=${BASE:-/mnt/PCIE5_4T_SSD/hashi-testnet}
MONITOR_ROOT=${MONITOR_ROOT:-$BASE/monitoring/community}
IMAGE=${DISCOVERY_IMAGE:-hashi-fleet-discovery:b8fce9de}
RAW=$(mktemp)
trap 'rm -f "$RAW"' EXIT

docker run --rm \
  -e HASHI_COMMITTEE_JSON=1 \
  -v "$BASE/hashi/config:/config:ro" \
  -v "$BASE/hashi/keys:/keys:ro" \
  --entrypoint /opt/hashi/bin/hashi \
  "$IMAGE" committee --config /config/hashi-cli.toml list >"$RAW"

python3 "$MONITOR_ROOT/scripts/extract_committee_json.py" \
  "$MONITOR_ROOT/data/committee.json" <"$RAW"
