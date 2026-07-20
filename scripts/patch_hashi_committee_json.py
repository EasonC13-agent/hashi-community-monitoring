#!/usr/bin/env python3
"""Add read-only JSON committee output to a Hashi source checkout."""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
p = root / "crates/hashi/src/cli/commands/committee.rs"
s = p.read_text()
marker = "Machine-readable discovery output for community fleet monitoring."
if marker in s:
    print(f"already patched: {p}")
    raise SystemExit(0)
needle = '    println!("\\n👥 Committee Members (Epoch {}):\\n", current_epoch);\n'
insert = '''    // Machine-readable discovery output for community fleet monitoring.
    if std::env::var_os("HASHI_COMMITTEE_JSON").is_some() {
        let rows: Vec<_> = members
            .iter()
            .map(|m| {
                serde_json::json!({
                    "epoch": current_epoch,
                    "validator": display::format_address_full(&m.validator_address),
                    "operator": display::format_address_full(&m.operator_address),
                    "endpoint": m.endpoint_url.as_ref().map(ToString::to_string),
                })
            })
            .collect();
        println!("{}", serde_json::to_string(&rows)?);
        return Ok(());
    }

'''
if needle not in s:
    raise SystemExit(f"unsupported Hashi source layout: insertion point not found in {p}")
p.write_text(s.replace(needle, insert + needle, 1))
print(f"patched: {p}")
