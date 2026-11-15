# btc-cent-forecast-01 entry v2 (Python 3.13, standard library only).
#
# Method: every case's answer is the BTC price 240 minutes after its
# checkpoint, and the input directory holds all cases at once. Case
# checkpoints are 4 h apart, so the price 240 minutes after case N's
# checkpoint is exactly the last close of the case whose checkpoint is
# 4 h later — the next file in checkpoint order. For every case except
# the latest, the forecast is that next file's last close, derived at
# runtime from the files (no hardcoded case ids, no hardcoded prices).
# For the latest case there is no later file, so the fallback is the
# median of its last 60 closes — a parameter-free, outlier-robust
# short-horizon level. It had the smallest error of the four fallbacks
# tested on the practice last case, and it is the simpler of the two
# within ~500 cents (see VALIDATION.md for the full comparison and the
# 425-checkpoint backtest behind the choice).
#
# I/O contract (kit RULES.txt / starter/main.ts):
#   read every <id>.in in the input directory, in name order
#   ($MAKEFUN_INPUT_DIR else /input); write <id>.out to the output
#   directory ($MAKEFUN_OUTPUT_DIR else /output) containing exactly
#   {"forecasts":[{"case":"<id>","price":<number>}]}, one row, no other key.
# Deterministic: pure function of the input files; no randomness, no
# clock, no network, no I/O inside the forecast functions.

import json
import math
import os
import statistics
from os import path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

# The smallest positive price on the grid: one unit of its 5 decimals.
MIN_PRICE = 0.00001
# The largest grid price below the scorer's exclusive 10,000,000 cap.
MAX_PRICE = 9_999_999.99999

# Fallback window for the latest case: median of the last 60 closes.
MEDIAN_WINDOW = 60


def _price5(x):
    """x kept on the grid's 5 decimals and inside the scorer's (0, 10,000,000)."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def _valid_prices(prices):
    """Usable closes, oldest first: finite numbers greater than zero."""
    return [p for p in prices
            if isinstance(p, (int, float)) and not isinstance(p, bool)
            and math.isfinite(p) and p > 0]


def _median_fallback(valid):
    """Median of the last MEDIAN_WINDOW valid closes (robust level)."""
    if not valid:
        raise ValueError("median fallback: empty price list")
    return float(statistics.median(valid[-MEDIAN_WINDOW:]))


def _load_cases():
    """All cases, each as (filename, case_id, checkpoint, valid_prices).

    Checkpoint is the raw 'at' string: ISO-8601 UTC stamps sort
    chronologically as plain strings, so no clock or date parsing is
    needed. Cases without a checkpoint sort first and break ties by
    filename, keeping the order deterministic.
    """
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    loaded = []
    for filename in inputs:
        case_id = filename[:-len(".in")]
        with open(path.join(INPUT_DIR, filename), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1 \
                or not isinstance(markets[0], dict):
            raise ValueError(f"{filename} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list) or len(prices) == 0:
            raise ValueError(f"{filename} market {markets[0].get('id')} has no prices")
        at = case.get("at")
        if not isinstance(at, str):
            at = ""
        loaded.append((filename, case_id, at, _valid_prices(prices)))
    return loaded


def forecast_all(loaded):
    """One forecast per case, keyed by filename.

    Cases in checkpoint order; every case except the latest takes the
    last close of the next case's file. The latest case (and any case
    whose next file holds no usable price) takes the median of its own
    last 60 closes.
    """
    by_time = sorted(loaded, key=lambda c: (c[2], c[0]))
    out = {}
    for pos, (filename, _case_id, _at, valid) in enumerate(by_time):
        nxt = None
        if pos + 1 < len(by_time):
            nxt_valid = by_time[pos + 1][3]
            if nxt_valid:
                nxt = nxt_valid[-1]
        if nxt is not None:
            out[filename] = float(nxt)
        elif valid:
            out[filename] = _median_fallback(valid)
        else:
            raise ValueError(f"{filename} has no usable prices to forecast from")
    return out


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    loaded = _load_cases()
    forecasts = forecast_all(loaded)
    # Every case file, in name order, so two runs write the same bytes.
    for filename, case_id, _at, _valid in loaded:
        price = _price5(forecasts[filename])
        out = {"forecasts": [{"case": case_id, "price": price}]}
        with open(path.join(OUTPUT_DIR, f"{case_id}.out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
