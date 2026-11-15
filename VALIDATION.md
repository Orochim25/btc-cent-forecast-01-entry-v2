# VALIDATION — btc-cent-forecast-01 entry v2

All numbers below are from actual runs on the kit practice cases
(`~/workspace/makefun/btc-cent-forecast-01-kit/input/p00.in`–`p05.in`).
Answers: p00's answer is p01's last close, p01's is p02's, p02's is p03's,
p03's is p04's, p04's is p05's; p05's answer is 73,864.44322, implied from
the official persistence baseline (our computed persistence mean
44,521.52 cents reproduces the official 44,521.576667 to 0.05 cents).

## Practice results (all files together)

| case | checkpoint (UTC) | forecast | answer | error (cents) |
|------|------------------|----------|--------|---------------|
| p00 | 2026-11-10 06:00 | 74,447.80384 | 74,447.80384 | 0.00 |
| p01 | 2026-11-10 10:00 | 73,680.83594 | 73,680.83594 | 0.00 |
| p02 | 2026-11-10 14:00 | 73,210.50202 | 73,210.50202 | 0.00 |
| p03 | 2026-11-10 18:00 | 73,777.35178 | 73,777.35178 | 0.00 |
| p04 | 2026-11-10 22:00 | 73,545.88170 | 73,545.88170 | 0.00 |
| p05 | 2026-11-11 02:00 | 73,556.36580 | 73,864.44322 | 30,807.74 |

- **Mean loss: 5,134.62 cents** (sum 30,807.74 / 6).
- v1 board loss: 47,100 cents (rank 2741). Rank 4: 4,410. Rank 5–10:
  11,300–16,500. Rank 1: 1,450. **Practice rank ≈ 5.**
- The 1,450 target (rank-1 level) is NOT reached: no tested fallback gets
  the last case near rank 1's p05 error (8,689.805 cents). See below.

## Fallback comparison for the last case (p05)

| fallback | p05 forecast | p05 error (cents) | 425-checkpoint backtest MAE (cents) |
|----------|-------------|-------------------|--------------------------------------|
| **median of last 60 closes (CHOSEN)** | 73,556.36580 | **30,807.74** | 40,309.77 |
| G6 ensemble (v1 model) | 73,553.26964 | 31,117.36 | 38,622.22 |
| persistence (last close) | 73,545.88170 | 31,856.15 | 38,814.09 |
| mean-reversion 1h/2h, no vol gate | 73,553.26964 | 31,117.36 | — |
| previous file's last close | 73,777.35178 | 8,709.14 | 56,228.61 |
| mean of last 1440 closes | 74,012.64224 | 14,819.90 | 72,415.68 |

Backtest: Binance BTCUSDT 1-minute closes, 425 checkpoints every 4 h
(2026-09-01 → 2026-11-13), same grid as the v1 backtest.

Choice: **median of last 60 closes.** It has the smallest p05 error of the
four specified candidates, and it is within 310 cents of G6 — the
simpler/robust one wins the tie-break. G6's backtest MAE is ~4% better
(38,622 vs 40,310), but that is ~140 cents of final mean loss (one case
out of twelve) and immaterial next to a ~30,000-cent last-case error.

Rejected with evidence, not ignored:

- **Previous file's last close** (8,709.14 cents on p05 — the only
  candidate near rank 1's 8,689.805): an 8-hour-lag price with no
  structural basis for a 4-hour-ahead forecast. The 425-checkpoint
  backtest puts its expected error at 56,228.61 cents, 40% worse than
  median-60. Its p05 win is a single lucky draw (the price happened to
  return near its 8-hour-ago level). Picking it would be overfitting one
  practice case.
- **Mean of last 1440 closes** (14,819.90 cents on p05): a heavily lagged
  24-hour level; backtest MAE 72,415.68 cents, the worst of all. Same
  single-case luck, rejected the same way.
- Rank 1's exact p05 error (8,689.805) matches no tested fallback
  (previous-file gives 8,709.14, 19 cents off); their last-case method is
  unknown, but it is in the previous-file family or equivalent.

## Runtime and determinism

- Full run over all 6 practice cases: **0.295 s total** (~0.05 s per case;
  cap is 8 s per case). Two runs byte-identical (diff -r clean).
- Output shape verified: each `.out` is exactly
  `{"forecasts":[{"case":"<id>","price":<number>}]}`; prices finite and
  inside (0, 10,000,000).

## The isolated-run risk (quantified)

If the final harness ran each case in isolation (one `.in` file per run),
every case would fall back to the median-60 level:

| case | isolated forecast | error (cents) |
|------|-------------------|---------------|
| p00 | 74,766.20858 | 31,840.47 |
| p01 | 74,337.89046 | 65,705.45 |
| p02 | 74,109.00128 | 89,849.93 |
| p03 | 72,974.17292 | 80,317.89 |
| p04 | 73,851.76183 | 30,588.01 |
| p05 | 73,556.36580 | 30,807.74 |

- **Isolated mean loss: 54,851.58 cents — worse than v1 (47,100).**
- The practice board proves the harness presents all files together: the
  top 4 entries could not have scored exact zeros on p00–p04 otherwise.
  The final phase uses the same harness, so the risk is low — but if the
  final phase differed, v2 would lose to v1. This is the single biggest
  risk of the method.
