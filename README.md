# Hashi Community Monitoring

Provider-neutral Grafana and Prometheus monitoring for a fleet of [MystenLabs/Hashi](https://github.com/MystenLabs/Hashi) operators, including optional Bitcoin Core detail and Sui operator Address Balance.

## What is different from a single-operator dashboard?

Every series carries the same labels:

- `network`: `testnet` or `mainnet`
- `operator`: human-readable operator name
- `node`: stable unique node ID
- `validator`: Sui validator address
- `endpoint`: public Hashi endpoint where applicable

Grafana variables use these labels, so one dashboard works for one node, many nodes, or a community-wide collector. The first row is a fleet overview inspired by the Sui validator dashboards; the remaining rows provide selected-node detail.

## Included

- Full Hashi metrics dashboard derived from Trusted Point's Apache-2.0 dashboard
- Fleet-wide reporting, sync, epoch, Bitcoin RPC and SUI reserve panels
- Optional Trusted Point Bitcoin Core exporter pinned to commit `751cd40`
- Sui GraphQL exporter for coin balance + Address Balance
- Prometheus retention of 30 days / 20 GB
- Actionable-only sample alert rules with 10–30 minute persistence
- Local scrape and central Prometheus remote-write receiver support

## Quick start

1. Copy `.env.example` to `.env`, set a long Grafana password and the path to Bitcoin Core's RPC cookie.
2. Add Hashi targets to `prometheus/targets/hashi.yml` and Bitcoin exporters to `prometheus/targets/bitcoin.yml`.
3. Build the dashboard and validate configuration:

```bash
python3 scripts/build_dashboard.py \
  reference/Hashi-Node-Bitcoin-Core-Fullnode.json \
  grafana/dashboards/hashi-community.json

docker compose config
docker compose up -d --build
```

Local endpoints bind only to loopback:

- Grafana: `127.0.0.1:33000`
- Prometheus: `127.0.0.1:19090`
- Bitcoin exporter: `127.0.0.1:19097`
- SUI balance exporter: `127.0.0.1:19100`

Use a TLS reverse proxy for Grafana. Do not expose Bitcoin RPC or raw node metrics directly.

## Adding an operator locally

Add a target with standard labels:

```yaml
- targets: ["127.0.0.1:9180"]
  labels:
    network: testnet
    operator: ExampleOperator
    node: example-testnet-1
    validator: "0x..."
    endpoint: "https://hashi.example.org/"
```

Add the same node identity and operator address to `NODES_JSON` for SUI balance.

## Central/community mode

Hashi's native `metrics_push` uses Mysten's `sui-proxy /publish/metrics` mTLS protocol. It is **not** Prometheus remote-write and cannot be sent directly to Prometheus.

For opt-in community aggregation, run Prometheus Agent or vmagent beside each operator and remote-write to the collector's protected `/api/v1/write` endpoint. Apply the four standard labels before sending. Protect the receiver with per-operator authentication or mTLS; never make an unauthenticated receiver public.

Native Hashi metrics-push can be integrated later by deploying Mysten's compatible `sui-proxy` ingestion path and validating operators against on-chain TLS keys.

## Alert philosophy

The sample rules alert only on sustained, actionable faults:

- Hashi metrics absent for 10 minutes
- Kyoto unsynced/no peer for 30 minutes
- Bitcoin RPC unavailable for 15 minutes
- operator SUI below 15 SUI for 30 minutes

MPC recovery activity, temporary peer loss, successful rollback and recovery messages are dashboard diagnostics, not pages.

## Attribution

The detailed dashboard is derived from [trusted-point/Hashi-Bitcoin-Monitoring](https://github.com/trusted-point/Hashi-Bitcoin-Monitoring), licensed under Apache-2.0. The fleet layout is inspired by the public Sui Testnet Validators dashboard. Modifications include provider-neutral labels, fleet panels, safer semantic descriptions, SUI Address Balance metrics and actionable-only alert rules.
