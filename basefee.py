"""EIP-1559 base-fee dynamics simulator.

Models how Ethereum's base fee adapts block-by-block to demand, using the
exact update rule from EIP-1559:

    base_fee(n+1) = base_fee(n) * (1 + 1/8 * (gas_used - gas_target) / gas_target)

Full blocks push the fee up (max +12.5%/block), empty blocks pull it down.
The base fee is burned; only the priority fee (tip) goes to the validator.

Pure Python, no dependencies. All values are in wei unless stated otherwise.
"""

import math
import random

GAS_LIMIT = 30_000_000
GAS_TARGET = GAS_LIMIT // 2          # 15M gas target (EIP-1559)
MIN_BASE_FEE = 1                     # base fee never drops below 1 wei
TX_GAS = 21_000                      # every synthetic tx is a simple transfer
MIN_PRIORITY_FEE = 1_000_000_000     # assumed 1 gwei tip for inclusion

GWEI = 1_000_000_000
MAX_TXS_PER_BLOCK = GAS_LIMIT // TX_GAS


def next_base_fee(base_fee: int, gas_used: int,
                 gas_target: int = GAS_TARGET) -> int:
    """EIP-1559 base-fee update rule. Returns the next block's base fee (wei)."""
    # Canonical integer math: delta rounds toward zero on tiny blocks.
    delta = (base_fee * (gas_used - gas_target)) // (gas_target * 8)
    new_fee = base_fee + delta
    return max(new_fee, MIN_BASE_FEE)


def block_demand(rng: random.Random, n_txs: int, median_fee_gwei: float,
                 spread: float = 0.8) -> list:
    """Generate max-fee-per-gas offers (wei) for one block's mempool.

    Willingness to pay follows a lognormal distribution: most users cluster
    near the median, a few will pay a lot more.
    """
    mu = math.log(median_fee_gwei * GWEI)
    return [int(rng.lognormvariate(mu, spread)) for _ in range(n_txs)]


def simulate(base_fee_gwei: float, blocks: int, demand_fn, seed: int = 42):
    """Run the fee market for ``blocks`` blocks.

    demand_fn(block_index) -> (n_txs, median_fee_gwei): how many potential
    transactions show up and what the typical user is willing to pay.

    Returns a list of per-block dicts: block, base_fee_gwei, gas_used,
    fullness, txs (included), burned_eth.
    """
    rng = random.Random(seed)
    base_fee = int(base_fee_gwei * GWEI)
    history = []
    for b in range(blocks):
        n_txs, median = demand_fn(b)
        offers = block_demand(rng, n_txs, median)
        # Only txs covering base fee + tip get in; block space goes to the
        # highest bidders first, capped by the gas limit.
        eligible = sorted(
            (o for o in offers if o >= base_fee + MIN_PRIORITY_FEE),
            reverse=True,
        )
        included = eligible[:MAX_TXS_PER_BLOCK]
        gas_used = len(included) * TX_GAS
        burned = gas_used * base_fee  # the base fee is burned, in wei
        history.append({
            "block": b,
            "base_fee_gwei": base_fee / GWEI,
            "gas_used": gas_used,
            "fullness": gas_used / GAS_LIMIT,
            "txs": len(included),
            "burned_eth": burned / 1e18,
        })
        base_fee = next_base_fee(base_fee, gas_used)
    return history


def summarize(history: list) -> dict:
    """Compact summary stats for a finished ``simulate()`` run.

    Returns min/max/avg base fee (gwei), avg block fullness, total burned
    (ETH) and total included transactions — handy for comparing scenarios.
    """
    fees = [h["base_fee_gwei"] for h in history]
    return {
        "blocks": len(history),
        "min_base_fee_gwei": min(fees),
        "max_base_fee_gwei": max(fees),
        "avg_base_fee_gwei": sum(fees) / len(fees),
        "avg_fullness": sum(h["fullness"] for h in history) / len(history),
        "total_burned_eth": sum(h["burned_eth"] for h in history),
        "total_txs": sum(h["txs"] for h in history),
    }
