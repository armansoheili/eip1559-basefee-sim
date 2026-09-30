"""Runnable EIP-1559 scenarios: steady demand, a demand spike, a demand crash.

Usage:  python3 example.py
"""

from basefee import simulate


def ascii_chart(series, height=10):
    lo, hi = min(series), max(series)
    span = (hi - lo) or 1
    rows = []
    for r in range(height, 0, -1):
        thresh = lo + span * r / height
        rows.append("".join("#" if v >= thresh else " " for v in series))
    axis = f"gwei/block, {len(series)} blocks"
    return "\n".join(rows) + "\n" + axis, lo, hi


def show(title, history):
    fees = [h["base_fee_gwei"] for h in history]
    chart, lo, hi = ascii_chart(fees)
    avg_full = sum(h["fullness"] for h in history) / len(history)
    burned = sum(h["burned_eth"] for h in history)
    print(f"\n== {title} ==")
    print(f"base fee: {fees[0]:6.2f} -> {fees[-1]:6.2f} gwei "
          f"(min {lo:5.2f}, max {hi:6.2f}) | "
          f"avg fullness {avg_full:4.1%} | burned {burned:.4f} ETH")
    print(chart)


def steady(b):
    """Constant moderate demand — the fee market finds its equilibrium."""
    return 1200, 25.0


def spike(b):
    """NFT-mint style mania between blocks 20-40, then back to normal."""
    return (6000, 120.0) if 20 <= b < 40 else (1200, 25.0)


def crash(b):
    """Demand evaporates after block 30 — watch the fee bleed out."""
    return (200, 5.0) if b >= 30 else (1200, 25.0)


if __name__ == "__main__":
    N = 80
    show("steady demand", simulate(20.0, N, steady))
    show("demand spike (blocks 20-40)", simulate(20.0, N, spike))
    show("demand crash (block 30+)", simulate(20.0, N, crash))
