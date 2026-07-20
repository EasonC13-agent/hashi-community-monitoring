from prometheus_client import (
    Counter,
    Gauge,
    REGISTRY,
    disable_created_metrics,
)
from prometheus_client.gc_collector import GC_COLLECTOR
from prometheus_client.platform_collector import PLATFORM_COLLECTOR
from prometheus_client.process_collector import PROCESS_COLLECTOR

disable_created_metrics()

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)

# Exporter RPC metrics

BITCOIN_RPC_REQUESTS_SUCCESSFUL_TOTAL = Counter(
    "bitcoin_node_rpc_requests_successful_total",
    "Total number of successful Bitcoin Core RPC requests made by the exporter",
    ["method"],
)

BITCOIN_RPC_REQUESTS_FAILED_TOTAL = Counter(
    "bitcoin_node_rpc_requests_failed_total",
    "Total number of failed Bitcoin Core RPC requests made by the exporter",
    ["method", "reason"],
)

BITCOIN_RPC_REQUEST_DURATION_SECONDS = Gauge(
    "bitcoin_node_rpc_request_duration_seconds",
    "Duration of the latest Bitcoin Core RPC request made by the exporter",
    ["method"],
)

BITCOIN_NODE_RPC_AVAILABLE = Gauge(
    "bitcoin_node_rpc_available",
    "Whether the Bitcoin Core RPC endpoint is reachable",
)

# Blockchain metrics

BITCOIN_NODE_INFO = Gauge(
    "bitcoin_node_info",
    "Static information about the connected Bitcoin Core node",
    ["chain", "version"],
)

BITCOIN_NODE_BLOCK_HEIGHT = Gauge(
    "bitcoin_node_block_height",
    "Current validated Bitcoin block height",
)

BITCOIN_NODE_HEADER_HEIGHT = Gauge(
    "bitcoin_node_header_height",
    "Current known Bitcoin block header height",
)

BITCOIN_NODE_SYNC_PROGRESS_RATIO = Gauge(
    "bitcoin_node_sync_progress_ratio",
    "Bitcoin blockchain verification progress as a ratio from 0 to 1",
)

BITCOIN_NODE_INITIAL_BLOCK_DOWNLOAD = Gauge(
    "bitcoin_node_initial_block_download",
    "Whether the Bitcoin node is performing initial block download",
)

BITCOIN_NODE_CHAIN_DIFFICULTY = Gauge(
    "bitcoin_node_chain_difficulty",
    "Current Bitcoin blockchain difficulty",
)

BITCOIN_NODE_CHAIN_SIZE_BYTES = Gauge(
    "bitcoin_node_chain_size_bytes",
    "Bitcoin blockchain data size stored on disk in bytes",
)

BITCOIN_NODE_PRUNED = Gauge(
    "bitcoin_node_pruned",
    "Whether Bitcoin Core is running in pruned mode",
)

BITCOIN_NODE_PRUNE_HEIGHT = Gauge(
    "bitcoin_node_prune_height",
    "Lowest block height retained by a pruned Bitcoin Core node",
)

BITCOIN_NODE_CHAIN_TRANSACTIONS = Gauge(
    "bitcoin_node_chain_transactions",
    "Estimated total number of transactions in the active Bitcoin blockchain",
)

BITCOIN_NODE_CHAIN_TIPS = Gauge(
    "bitcoin_node_chain_tips",
    "Number of known Bitcoin blockchain tips",
)

# Node information metrics

BITCOIN_NODE_UPTIME_SECONDS = Gauge(
    "bitcoin_node_uptime_seconds",
    "Number of seconds the Bitcoin Core node has been running",
)

BITCOIN_NODE_PROTOCOL_VERSION = Gauge(
    "bitcoin_node_protocol_version",
    "Bitcoin Core peer protocol version",
)

BITCOIN_NODE_ACTIVE_WARNINGS = Gauge(
    "bitcoin_node_warnings",
    "Number of active Bitcoin Core warnings",
)

# Peer metrics

BITCOIN_NODE_PEERS_TOTAL = Gauge(
    "bitcoin_node_peers_total",
    "Total number of connected Bitcoin peers",
)

BITCOIN_NODE_PEERS_INBOUND = Gauge(
    "bitcoin_node_peers_inbound",
    "Number of inbound Bitcoin peer connections",
)

BITCOIN_NODE_PEERS_OUTBOUND = Gauge(
    "bitcoin_node_peers_outbound",
    "Number of outbound Bitcoin peer connections",
)

BITCOIN_NODE_BANNED_PEERS = Gauge(
    "bitcoin_node_banned_peers",
    "Number of peers currently banned by the Bitcoin Core node",
)

# Network traffic metrics

BITCOIN_NODE_NETWORK_RECEIVED_BYTES_TOTAL = Gauge(
    "bitcoin_node_network_received_bytes_total",
    "Total number of network bytes received by the Bitcoin Core node",
)

BITCOIN_NODE_NETWORK_SENT_BYTES_TOTAL = Gauge(
    "bitcoin_node_network_sent_bytes_total",
    "Total number of network bytes sent by the Bitcoin Core node",
)

# Mempool metrics

BITCOIN_NODE_MEMPOOL_TRANSACTIONS = Gauge(
    "bitcoin_node_mempool_transactions",
    "Number of transactions currently in the Bitcoin mempool",
)

BITCOIN_NODE_MEMPOOL_SIZE_BYTES = Gauge(
    "bitcoin_node_mempool_size_bytes",
    "Serialized Bitcoin mempool size in bytes",
)

BITCOIN_NODE_MEMPOOL_MEMORY_BYTES = Gauge(
    "bitcoin_node_mempool_memory_bytes",
    "Memory used by the Bitcoin mempool in bytes",
)

BITCOIN_NODE_MEMPOOL_LIMIT_BYTES = Gauge(
    "bitcoin_node_mempool_limit_bytes",
    "Maximum configured Bitcoin mempool size in bytes",
)

BITCOIN_NODE_MEMPOOL_MIN_FEE_BTC_PER_KVB = Gauge(
    "bitcoin_node_mempool_min_fee_btc_per_kvb",
    "Minimum Bitcoin mempool fee rate in BTC per kvB",
)

BITCOIN_NODE_MEMPOOL_UNBROADCAST_TRANSACTIONS = Gauge(
    "bitcoin_node_mempool_unbroadcast_transactions",
    "Number of mempool transactions not yet acknowledged by a peer",
)

# Bitcoin Core RPC server metrics

BITCOIN_NODE_RPC_ACTIVE_CALLS = Gauge(
    "bitcoin_node_rpc_active_calls",
    "Number of Bitcoin Core RPC calls currently being processed",
)

# Latest block metrics

BITCOIN_NODE_LATEST_BLOCK_SIZE_BYTES = Gauge(
    "bitcoin_node_latest_block_size_bytes",
    "Serialized size of the latest Bitcoin block in bytes",
)

BITCOIN_NODE_LATEST_BLOCK_WEIGHT = Gauge(
    "bitcoin_node_latest_block_weight",
    "Weight of the latest Bitcoin block",
)

BITCOIN_NODE_LATEST_BLOCK_TRANSACTIONS = Gauge(
    "bitcoin_node_latest_block_transactions",
    "Number of transactions in the latest Bitcoin block",
)

BITCOIN_NODE_LATEST_BLOCK_TIMESTAMP_SECONDS = Gauge(
    "bitcoin_node_latest_block_timestamp_seconds",
    "Unix timestamp of the latest validated Bitcoin block",
)

BITCOIN_NODE_LATEST_BLOCK_INPUTS = Gauge(
    "bitcoin_node_latest_block_inputs",
    "Number of transaction inputs in the latest Bitcoin block",
)

BITCOIN_NODE_LATEST_BLOCK_OUTPUTS = Gauge(
    "bitcoin_node_latest_block_outputs",
    "Number of transaction outputs in the latest Bitcoin block",
)

BITCOIN_NODE_LATEST_BLOCK_OUTPUT_VALUE_BTC = Gauge(
    "bitcoin_node_latest_block_output_value_btc",
    "Total output value of the latest Bitcoin block in BTC",
)

BITCOIN_NODE_LATEST_BLOCK_FEES_BTC = Gauge(
    "bitcoin_node_latest_block_fees_btc",
    "Total transaction fees in the latest Bitcoin block in BTC",
)


# Network hash rate metrics

BITCOIN_NETWORK_HASH_RATE_HASHES_PER_SECOND = Gauge(
    "bitcoin_network_hash_rate_hashes_per_second",
    "Estimated Bitcoin network hash rate in hashes per second",
    ["window"],
)

# Fee estimation metrics

BITCOIN_NODE_ESTIMATED_FEE_BTC_PER_KVB = Gauge(
    "bitcoin_node_estimated_fee_btc_per_kvb",
    "Estimated fee rate in BTC per kvB for the requested confirmation target",
    ["target_blocks"],
)

# Locked-memory allocator metrics

BITCOIN_NODE_LOCKED_MEMORY_USED_BYTES = Gauge(
    "bitcoin_node_locked_memory_used_bytes",
    "Bytes used by the Bitcoin Core locked-memory allocator",
)

BITCOIN_NODE_LOCKED_MEMORY_FREE_BYTES = Gauge(
    "bitcoin_node_locked_memory_free_bytes",
    "Bytes available in the Bitcoin Core locked-memory allocator",
)

BITCOIN_NODE_LOCKED_MEMORY_TOTAL_BYTES = Gauge(
    "bitcoin_node_locked_memory_total_bytes",
    "Total bytes managed by the Bitcoin Core locked-memory allocator",
)

BITCOIN_NODE_LOCKED_MEMORY_LOCKED_BYTES = Gauge(
    "bitcoin_node_locked_memory_locked_bytes",
    "Bytes successfully locked in memory by Bitcoin Core",
)

BITCOIN_NODE_LOCKED_MEMORY_USED_CHUNKS = Gauge(
    "bitcoin_node_locked_memory_used_chunks",
    "Number of allocated chunks in the Bitcoin Core locked-memory allocator",
)

BITCOIN_NODE_LOCKED_MEMORY_FREE_CHUNKS = Gauge(
    "bitcoin_node_locked_memory_free_chunks",
    "Number of available chunks in the Bitcoin Core locked-memory allocator",
)

EXPORTER_ERRORS = Counter(
    "bitcoin_exporter_errors_total",
    "Total exporter errors by collector and exception type",
    ["collector", "type"],
)

BITCOIN_NODE_INDEX_SYNCED = Gauge(
    "bitcoin_node_index_synced",
    "Whether the Bitcoin Core index is fully synced",
    ["index"],
)

BITCOIN_NODE_INDEX_HEIGHT = Gauge(
    "bitcoin_node_index_height",
    "Best block height processed by the Bitcoin Core index",
    ["index"],
)

BITCOIN_NODE_FEATURE_ENABLED = Gauge(
    "bitcoin_node_feature_enabled",
    "Whether a Bitcoin Core node feature is enabled",
    ["feature"],
)