from typing import Any

from src.calls import BitcoinRPCClient, BitcoinRPCError
from src.metrics import (
    BITCOIN_NETWORK_HASH_RATE_HASHES_PER_SECOND,
    BITCOIN_NODE_BANNED_PEERS,
    BITCOIN_NODE_BLOCK_HEIGHT,
    BITCOIN_NODE_CHAIN_DIFFICULTY,
    BITCOIN_NODE_CHAIN_SIZE_BYTES,
    BITCOIN_NODE_CHAIN_TIPS,
    BITCOIN_NODE_CHAIN_TRANSACTIONS,
    BITCOIN_NODE_ESTIMATED_FEE_BTC_PER_KVB,
    BITCOIN_NODE_HEADER_HEIGHT,
    BITCOIN_NODE_INITIAL_BLOCK_DOWNLOAD,
    BITCOIN_NODE_LATEST_BLOCK_FEES_BTC,
    BITCOIN_NODE_LATEST_BLOCK_INPUTS,
    BITCOIN_NODE_LATEST_BLOCK_OUTPUT_VALUE_BTC,
    BITCOIN_NODE_LATEST_BLOCK_OUTPUTS,
    BITCOIN_NODE_LATEST_BLOCK_SIZE_BYTES,
    BITCOIN_NODE_PRUNED,
    BITCOIN_NODE_PRUNE_HEIGHT,
    BITCOIN_NODE_LATEST_BLOCK_TRANSACTIONS,
    BITCOIN_NODE_LATEST_BLOCK_TIMESTAMP_SECONDS,
    BITCOIN_NODE_LATEST_BLOCK_WEIGHT,
    BITCOIN_NODE_LOCKED_MEMORY_FREE_BYTES,
    BITCOIN_NODE_LOCKED_MEMORY_FREE_CHUNKS,
    BITCOIN_NODE_LOCKED_MEMORY_LOCKED_BYTES,
    BITCOIN_NODE_LOCKED_MEMORY_TOTAL_BYTES,
    BITCOIN_NODE_LOCKED_MEMORY_USED_BYTES,
    BITCOIN_NODE_LOCKED_MEMORY_USED_CHUNKS,
    BITCOIN_NODE_MEMPOOL_LIMIT_BYTES,
    BITCOIN_NODE_MEMPOOL_MEMORY_BYTES,
    BITCOIN_NODE_MEMPOOL_MIN_FEE_BTC_PER_KVB,
    BITCOIN_NODE_MEMPOOL_SIZE_BYTES,
    BITCOIN_NODE_MEMPOOL_TRANSACTIONS,
    BITCOIN_NODE_MEMPOOL_UNBROADCAST_TRANSACTIONS,
    BITCOIN_NODE_NETWORK_RECEIVED_BYTES_TOTAL,
    BITCOIN_NODE_NETWORK_SENT_BYTES_TOTAL,
    BITCOIN_NODE_PEERS_INBOUND,
    BITCOIN_NODE_PEERS_OUTBOUND,
    BITCOIN_NODE_PEERS_TOTAL,
    BITCOIN_NODE_PROTOCOL_VERSION,
    BITCOIN_NODE_RPC_ACTIVE_CALLS,
    BITCOIN_NODE_SYNC_PROGRESS_RATIO,
    BITCOIN_NODE_UPTIME_SECONDS,
    BITCOIN_NODE_ACTIVE_WARNINGS,
    BITCOIN_NODE_INFO,
    EXPORTER_ERRORS,
    BITCOIN_NODE_FEATURE_ENABLED,
    BITCOIN_NODE_INDEX_HEIGHT,
    BITCOIN_NODE_INDEX_SYNCED,
)

from src.helpers import format_bitcoin_version
from utils.logger import logger

SATOSHIS_PER_BTC = 100_000_000

HASH_RATE_WINDOWS = {
    "12_blocks": 12,
    "120_blocks": 120,
    "2016_blocks": 2016,
}

FEE_ESTIMATION_TARGETS = (
    2,
    6,
    12,
)

TOTAL_COLLECTOR_GROUPS = 14

def count_exception(name: str, error: Exception) -> None:
    exception_type = f"{type(error).__module__}.{type(error).__name__}"
    EXPORTER_ERRORS.labels(
        collector=name,
        type=exception_type,
    ).inc()

def run_collector(
    name: str,
    collector,
    *args,
) -> tuple[bool, Any]:
    try:
        result = collector(*args)
        return True, result

    except BitcoinRPCError as error:
        count_exception(name, error)
        logger.error(f"Failed to collect {name} metrics: {error}")

    except KeyError as error:
        count_exception(name, error)
        logger.error(f"Missing field in {name} RPC response: {error}")

    except (TypeError, ValueError) as error:
        count_exception(name, error)
        logger.error(f"Invalid value in {name} RPC response: {error}")

    except Exception as error:
        count_exception(name, error)
        logger.exception(f"Unexpected error while collecting {name} metrics")

    return False, None

def collect_blockchain_metrics(
    rpc: BitcoinRPCClient,
) -> dict[str, Any]:
    info = rpc.call("getblockchaininfo")
    logger.debug(f"getblockchaininfo response: {info}")

    BITCOIN_NODE_BLOCK_HEIGHT.set(info["blocks"])
    BITCOIN_NODE_HEADER_HEIGHT.set(info["headers"])
    BITCOIN_NODE_SYNC_PROGRESS_RATIO.set(info["verificationprogress"])
    BITCOIN_NODE_INITIAL_BLOCK_DOWNLOAD.set(int(info["initialblockdownload"]))
    BITCOIN_NODE_CHAIN_DIFFICULTY.set(info["difficulty"])
    BITCOIN_NODE_CHAIN_SIZE_BYTES.set(info["size_on_disk"])

    is_pruned = bool(info.get("pruned", False))

    BITCOIN_NODE_PRUNED.set(int(is_pruned))
    BITCOIN_NODE_PRUNE_HEIGHT.set(info.get("pruneheight", 0) if is_pruned else 0)

    return info


def collect_network_metrics(
    rpc: BitcoinRPCClient,
) -> dict[str, Any]:
    info = rpc.call("getnetworkinfo")
    logger.debug(f"getnetworkinfo response: {info}")

    BITCOIN_NODE_PROTOCOL_VERSION.set(info["protocolversion"])
    BITCOIN_NODE_PEERS_TOTAL.set(info["connections"])
    BITCOIN_NODE_PEERS_INBOUND.set(info["connections_in"])
    BITCOIN_NODE_PEERS_OUTBOUND.set(info["connections_out"])
    BITCOIN_NODE_ACTIVE_WARNINGS.set(len(info.get("warnings", [])))

    local_services = info.get("localservicesnames", [])

    BITCOIN_NODE_FEATURE_ENABLED.labels(feature="peerblockfilters",).set(int("COMPACT_FILTERS" in local_services))

    return info


def collect_mempool_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    info = rpc.call("getmempoolinfo")
    logger.debug(f"getmempoolinfo response: {info}")

    BITCOIN_NODE_MEMPOOL_TRANSACTIONS.set(info["size"])
    BITCOIN_NODE_MEMPOOL_SIZE_BYTES.set(info["bytes"])
    BITCOIN_NODE_MEMPOOL_MEMORY_BYTES.set(info["usage"])
    BITCOIN_NODE_MEMPOOL_LIMIT_BYTES.set(info["maxmempool"])
    BITCOIN_NODE_MEMPOOL_MIN_FEE_BTC_PER_KVB.set(info["mempoolminfee"])
    BITCOIN_NODE_MEMPOOL_UNBROADCAST_TRANSACTIONS.set(info.get("unbroadcastcount", 0))


def collect_uptime_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    info = rpc.call("uptime")
    logger.debug(f"uptime response: {info}")

    BITCOIN_NODE_UPTIME_SECONDS.set(info)


def collect_chain_transaction_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    info = rpc.call("getchaintxstats")
    logger.debug(f"getchaintxstats response: {info}")

    BITCOIN_NODE_CHAIN_TRANSACTIONS.set(info["txcount"])


def collect_network_traffic_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    info = rpc.call("getnettotals")
    logger.debug(f"getnettotals response: {info}")

    BITCOIN_NODE_NETWORK_RECEIVED_BYTES_TOTAL.set(info["totalbytesrecv"])
    BITCOIN_NODE_NETWORK_SENT_BYTES_TOTAL.set(info["totalbytessent"])


def collect_rpc_server_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    info = rpc.call("getrpcinfo")
    logger.debug(f"getrpcinfo response: {info}")

    BITCOIN_NODE_RPC_ACTIVE_CALLS.set(len(info["active_commands"]))


def collect_chain_tip_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    tips = rpc.call("getchaintips")
    logger.debug(f"getchaintips response: {tips}")

    BITCOIN_NODE_CHAIN_TIPS.set(len(tips))


def collect_banned_peer_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    banned_peers = rpc.call("listbanned")
    logger.debug(f"listbanned response: {banned_peers}")

    BITCOIN_NODE_BANNED_PEERS.set(len(banned_peers))


def collect_latest_block_metrics(
    rpc: BitcoinRPCClient,
    block_height: int,
) -> None:
    stats = rpc.call(
        "getblockstats",
        block_height,
        [
            "time",
            "total_size",
            "total_weight",
            "txs",
            "ins",
            "outs",
            "total_out",
            "totalfee",
        ],
    )
    logger.debug(f"getblockstats response: {stats}")

    BITCOIN_NODE_LATEST_BLOCK_TIMESTAMP_SECONDS.set(stats["time"])
    BITCOIN_NODE_LATEST_BLOCK_SIZE_BYTES.set(stats["total_size"])
    BITCOIN_NODE_LATEST_BLOCK_WEIGHT.set(stats["total_weight"])
    BITCOIN_NODE_LATEST_BLOCK_TRANSACTIONS.set(stats["txs"])
    BITCOIN_NODE_LATEST_BLOCK_INPUTS.set(stats["ins"])
    BITCOIN_NODE_LATEST_BLOCK_OUTPUTS.set(stats["outs"])
    BITCOIN_NODE_LATEST_BLOCK_OUTPUT_VALUE_BTC.set(stats["total_out"] / SATOSHIS_PER_BTC)
    BITCOIN_NODE_LATEST_BLOCK_FEES_BTC.set(stats["totalfee"] / SATOSHIS_PER_BTC)


def collect_hash_rate_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    for window, block_count in HASH_RATE_WINDOWS.items():
        hash_rate = rpc.call(
            "getnetworkhashps",
            block_count,
        )
        logger.debug(f"getnetworkhashps[{block_count} | {window}] response: {hash_rate}")

        BITCOIN_NETWORK_HASH_RATE_HASHES_PER_SECOND.labels(window=window,).set(hash_rate)


def collect_fee_estimation_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    for target in FEE_ESTIMATION_TARGETS:
        estimate = rpc.call(
            "estimatesmartfee",
            target,
        )
        logger.debug(f"estimatesmartfee response: {estimate}")

        fee_rate = estimate.get("feerate")

        if fee_rate is None:
            logger.debug(f"No fee estimate available for {target} blocks: {estimate.get('errors', 'unknown reason')}")
            continue

        BITCOIN_NODE_ESTIMATED_FEE_BTC_PER_KVB.labels(target_blocks=str(target),).set(fee_rate)


def collect_memory_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    info = rpc.call(
        "getmemoryinfo",
        "stats",
    )
    logger.debug(f"getmemoryinfo response: {info}")

    locked = info["locked"]

    BITCOIN_NODE_LOCKED_MEMORY_USED_BYTES.set(locked["used"])
    BITCOIN_NODE_LOCKED_MEMORY_FREE_BYTES.set(locked["free"])
    BITCOIN_NODE_LOCKED_MEMORY_TOTAL_BYTES.set(locked["total"])
    BITCOIN_NODE_LOCKED_MEMORY_LOCKED_BYTES.set(locked["locked"])
    BITCOIN_NODE_LOCKED_MEMORY_USED_CHUNKS.set(locked["chunks_used"])
    BITCOIN_NODE_LOCKED_MEMORY_FREE_CHUNKS.set(locked["chunks_free"])

def collect_index_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    indexes = rpc.call("getindexinfo")

    logger.debug(f"getindexinfo response: {indexes}")

    BITCOIN_NODE_INDEX_SYNCED.clear()
    BITCOIN_NODE_INDEX_HEIGHT.clear()

    txindex_enabled = "txindex" in indexes
    blockfilterindex_enabled = "basic block filter index" in indexes

    BITCOIN_NODE_FEATURE_ENABLED.labels(feature="txindex").set(int(txindex_enabled))
    BITCOIN_NODE_FEATURE_ENABLED.labels(feature="blockfilterindex").set(int(blockfilterindex_enabled))

    BITCOIN_NODE_INDEX_SYNCED.labels(index="txindex").set(0)
    BITCOIN_NODE_INDEX_HEIGHT.labels(index="txindex").set(0)
    BITCOIN_NODE_INDEX_SYNCED.labels(index="blockfilterindex").set(0)
    BITCOIN_NODE_INDEX_HEIGHT.labels(index="blockfilterindex").set(0)

    for index_name, index_info in indexes.items():
        index_label = (
            "blockfilterindex"
            if index_name == "basic block filter index"
            else index_name
        )

        BITCOIN_NODE_INDEX_SYNCED.labels(index=index_label).set(int(index_info["synced"]))
        BITCOIN_NODE_INDEX_HEIGHT.labels(index=index_label).set(index_info["best_block_height"])

def collect_metrics(
    rpc: BitcoinRPCClient,
) -> None:
    successful_calls = 0

    success, blockchain_info = run_collector(
        "blockchain",
        collect_blockchain_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, network_info = run_collector(
        "network",
        collect_network_metrics,
        rpc,
    )
    successful_calls += int(success)

    if blockchain_info and network_info:
        version = format_bitcoin_version(
            network_info["subversion"]
        )

        BITCOIN_NODE_INFO.clear()
        BITCOIN_NODE_INFO.labels(chain=blockchain_info["chain"],version=version,).set(1)

    success, _ = run_collector(
        "mempool",
        collect_mempool_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "uptime",
        collect_uptime_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "chain transactions",
        collect_chain_transaction_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "network traffic",
        collect_network_traffic_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "RPC server",
        collect_rpc_server_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "chain tips",
        collect_chain_tip_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "banned peers",
        collect_banned_peer_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "indexes",
        collect_index_metrics,
        rpc,
    )
    successful_calls += int(success)

    if blockchain_info:
        success, _ = run_collector(
            "latest block",
            collect_latest_block_metrics,
            rpc,
            blockchain_info["blocks"],
        )
        successful_calls += int(success)

    success, _ = run_collector(
        "network hash rate",
        collect_hash_rate_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "fee estimation",
        collect_fee_estimation_metrics,
        rpc,
    )
    successful_calls += int(success)

    success, _ = run_collector(
        "locked memory",
        collect_memory_metrics,
        rpc,
    )
    successful_calls += int(success)

    logger.info(f"Bitcoin metric collection completed. Successful groups: {successful_calls}/{TOTAL_COLLECTOR_GROUPS}")