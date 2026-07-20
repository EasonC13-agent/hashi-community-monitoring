#!/usr/bin/env python3
"""Build a provider-neutral Hashi community dashboard from Trusted Point's MIT dashboard."""
import json
import re
import sys
from pathlib import Path

SOURCE = Path(sys.argv[1])
DEST = Path(sys.argv[2])
d = json.loads(SOURCE.read_text())

HASHI_FILTER = 'job="hashi",network=~"$network",operator=~"$operator",node=~"$node"'
BITCOIN_FILTER = 'job="bitcoin",network=~"$network",operator=~"$operator",node=~"$node"'


def rewrite_expr(expr: str) -> str:
    expr = expr.replace('alias="$hashi_alias"', HASHI_FILTER)
    expr = expr.replace('alias="$bitcoin_alias"', BITCOIN_FILTER)
    return expr


def datasource_walk(obj):
    if isinstance(obj, dict):
        if "datasource" in obj and isinstance(obj["datasource"], dict) and obj["datasource"].get("type") == "prometheus":
            obj["datasource"] = {"type": "prometheus", "uid": "${datasource}"}
        for key, value in obj.items():
            if key == "expr" and isinstance(value, str):
                obj[key] = rewrite_expr(value)
            else:
                datasource_walk(value)
    elif isinstance(obj, list):
        for value in obj:
            datasource_walk(value)


def stat_panel(pid, title, expr, x, w=4, unit="short", description=""):
    return {
        "id": pid,
        "type": "stat",
        "title": title,
        "description": description,
        "gridPos": {"x": x, "y": 1, "w": w, "h": 4},
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "targets": [{"refId": "A", "expr": expr, "instant": True, "range": False}],
        "fieldConfig": {"defaults": {"unit": unit, "color": {"mode": "thresholds"}, "thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]}}, "overrides": []},
        "options": {"reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": ""}, "orientation": "auto", "textMode": "auto", "colorMode": "background", "graphMode": "none", "justifyMode": "auto"},
    }


def variable(name, label, query, multi=True, include_all=True):
    return {
        "name": name, "label": label, "type": "query", "hide": 0,
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "query": {"query": query, "refId": f"var-{name}"},
        "definition": query, "refresh": 1, "sort": 1,
        "multi": multi, "includeAll": include_all, "allValue": ".*" if include_all else None,
        "current": {"selected": include_all, "text": "All" if include_all else "", "value": "$__all" if include_all else ""},
        "options": [],
    }

for panel in d.get("panels", []):
    panel["gridPos"]["y"] = panel.get("gridPos", {}).get("y", 0) + 6
    panel["title"] = re.sub(r"❗\s*", "", panel.get("title", ""))
    if panel.get("id") == 86:
        panel["title"] = "Presignature Gauge (informational)"
        panel["description"] = "Hashi may leave this gauge at zero until a signing path updates it. Do not alert on this metric alone."
        panel["fieldConfig"]["defaults"]["thresholds"] = {"mode": "absolute", "steps": [{"color": "blue", "value": None}]}
    if panel.get("id") in (87, 158):
        panel["title"] = "MPC Signing Recovery Activity"
        panel["description"] = "Recovery activity is diagnostic. It is not an incident when threshold signing ultimately succeeds."
    if panel.get("id") == 72:
        panel["description"] = "Investigate trends; do not page unless signing remains failed or bridge progress stalls."

datasource_walk(d)

d["id"] = None
d["uid"] = "hashi-community"
d["title"] = "Hashi Community — Fleet & Node Detail"
d["description"] = "Provider-neutral multi-operator Hashi, Bitcoin Signet and operator gas dashboard. Derived from Trusted Point's MIT-licensed dashboard and inspired by Sui validator fleet dashboards."
d["tags"] = ["hashi", "community", "multi-operator", "bitcoin", "sui"]
d["editable"] = True
d.pop("__inputs", None)
d.pop("__requires", None)

datasource_var = {
    "name": "datasource", "label": "Prometheus", "type": "datasource", "query": "prometheus",
    "refresh": 1, "current": {}, "options": [], "multi": False, "includeAll": False,
}
d["templating"] = {"list": [
    datasource_var,
    variable("network", "Network", "label_values(hashi_epoch, network)"),
    variable("operator", "Operator", 'label_values(hashi_epoch{network=~"$network"}, operator)'),
    variable("node", "Node", 'label_values(hashi_epoch{network=~"$network",operator=~"$operator"}, node)', multi=False, include_all=False),
]}

fleet_filter = 'network=~"$network",operator=~"$operator"'
healthy = f'''sum((max by(node,operator)(up{{job="hashi",{fleet_filter}}}) == 1)
 and on(node,operator) (max by(node,operator)(hashi_kyoto_synced{{{fleet_filter}}}) == 1)
 and on(node,operator) (max by(node,operator)(hashi_kyoto_connected_peers{{{fleet_filter}}}) > 0))'''
new_panels = [
    {"id": 1000, "type": "row", "title": "Community Fleet Overview", "collapsed": False, "panels": [], "gridPos": {"x": 0, "y": 0, "w": 24, "h": 1}},
    stat_panel(1001, "Reporting Nodes", f'count(max by(node,operator)(up{{job="hashi",{fleet_filter}}}))', 0),
    stat_panel(1002, "Healthy Nodes", healthy, 4),
    stat_panel(1003, "Epoch-aligned Nodes", f'sum((max by(node,operator)(hashi_epoch{{{fleet_filter}}}) - on(node,operator) max by(node,operator)(hashi_sui_epoch{{{fleet_filter}}})) == bool 0)', 8),
    stat_panel(1004, "Operator SUI Reserve", f'sum(hashi_operator_sui_balance_mist{{{fleet_filter}}}) / 1e9', 12, unit="sui"),
    stat_panel(1005, "Bitcoin RPC Healthy", f'sum(max by(node,operator)(bitcoin_node_rpc_available{{{fleet_filter}}}) == 1)', 16),
    stat_panel(1006, "Kyoto Synced", f'sum(max by(node,operator)(hashi_kyoto_synced{{{fleet_filter}}}) == 1)', 20),
]
d["panels"] = new_panels + d.get("panels", [])
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(d, indent=2) + "\n")
print(f"wrote {DEST}: {len(d['panels'])} panels")
