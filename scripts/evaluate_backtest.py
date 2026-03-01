"""Evaluate core metrics and flag suspicious backtest outcomes."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass


@dataclass
class Thresholds:
    ic_min: float = 0.02
    ic_max: float = 0.08
    sharpe_warn: float = 2.0
    sharpe_red_flag: float = 3.0
    drawdown_warn: float = -0.25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-json", required=True, help="Path to JSON with keys: ic, sharpe, max_drawdown, turnover")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    thresholds = Thresholds()
    with open(args.metrics_json, encoding="utf-8") as f:
        m = json.load(f)

    ic, sharpe, mdd = m["ic"], m["sharpe"], m["max_drawdown"]
    print(f"IC={ic:.4f}, Sharpe={sharpe:.4f}, MaxDD={mdd:.2%}")

    if not (thresholds.ic_min <= ic <= thresholds.ic_max):
        print("WARNING: IC out of expected range (0.02-0.08).")
    if sharpe > thresholds.sharpe_warn:
        print("WARNING: Sharpe above 2.0, inspect for overfitting.")
    if sharpe > thresholds.sharpe_red_flag:
        print("RED FLAG: Sharpe above 3.0 is likely unrealistic.")
    if mdd > -0.05:
        print("WARNING: Drawdown too small; may miss stress periods.")
    if mdd < thresholds.drawdown_warn:
        print("WARNING: Drawdown deeper than -25%; risk may be unacceptable.")


if __name__ == "__main__":
    main()
