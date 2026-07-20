#!/usr/bin/env python3
"""Extract the machine-readable JSON array from Hashi CLI output atomically."""
import json
import os
import sys
import time
from pathlib import Path

out = Path(sys.argv[1])
lines = sys.stdin.read().splitlines()
arrays = []
for line in lines:
    line = line.strip()
    if line.startswith("[") and line.endswith("]"):
        try:
            value = json.loads(line)
            if isinstance(value, list): arrays.append(value)
        except json.JSONDecodeError:
            pass
if not arrays:
    raise SystemExit("no committee JSON array found in Hashi CLI output")
members = arrays[-1]
if len(members) < 1:
    raise SystemExit("refusing to replace roster with an empty committee")
payload = {"updated_at": int(time.time()), "members": members}
out.parent.mkdir(parents=True, exist_ok=True)
tmp = out.with_suffix(out.suffix + ".tmp")
tmp.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
os.chmod(tmp, 0o644)
os.replace(tmp, out)
print(f"updated committee roster: epoch={max(x.get('epoch',0) for x in members)} members={len(members)}")
