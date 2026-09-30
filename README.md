# eip1559-basefee-sim

A tiny, dependency-free simulator of Ethereum's **EIP-1559 fee market**.
It shows how the protocol's *base fee* adapts block-by-block to demand —
rising when blocks are more than half full, falling when they're emptier —
without any central price setter.

## The rule

Every block updates the base fee with the exact EIP-1559 formula:

```
base_fee(n+1) = base_fee(n) × (1 + 1/8 × (gas_used − gas_target) / gas_target)
```

- Block gas limit: 30M, target: 15M (half-full blocks keep the fee flat)
- Max adjustment: ±12.5% per block
- The base fee is **burned**; validators only receive the priority fee (tip)

## Demand model

Each simulated block draws a mempool of potential transactions whose
willingness to pay follows a lognormal distribution. A transaction is
included only if it covers `base_fee + tip`, with block space going to the
highest bidders first (capped by the 30M gas limit, 21k gas per tx).

## Run it

```bash
python3 example.py
```

Three scenarios play out over 80 blocks, with an ASCII chart of the base fee:

1. **steady demand** — the market finds its equilibrium fee on its own
2. **demand spike (blocks 20–40)** — an NFT-mint style mania: fees climb fast,
   then decay back once the rush passes
3. **demand crash (block 30+)** — demand evaporates and the fee bleeds out

## Files

- `basefee.py` — `next_base_fee()`, the lognormal demand model, and `simulate()`
- `example.py` — the three scenarios above

## Try tweaking

- `demand_fn`: plug in your own demand curve (e.g. daily on-chain cycles)
- `spread`: a wider spread means fatter whale tails in the mempool
- `MIN_PRIORITY_FEE`: how the assumed tip changes inclusion during congestion
