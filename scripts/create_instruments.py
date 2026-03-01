"""Create Qlib instrument text files from downloaded raw CSVs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from pykrx import stock


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw_csv")
    parser.add_argument("--qlib-dir", default="data/qlib_kr_data")
    parser.add_argument("--markets", nargs="+", default=["KOSPI", "KOSDAQ"])
    return parser.parse_args()


def build_lines(raw_dir: Path, tickers: list[str]) -> list[str]:
    lines: list[str] = []
    for ticker in tickers:
        csv_path = raw_dir / f"{ticker}.csv"
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        if df.empty:
            continue
        start, end = df.index.min().strftime("%Y-%m-%d"), df.index.max().strftime("%Y-%m-%d")
        lines.append(f"{ticker}\t{start}\t{end}")
    return lines


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    inst_dir = Path(args.qlib_dir) / "instruments"
    os.makedirs(inst_dir, exist_ok=True)

    combined: list[str] = []
    for market in args.markets:
        tickers = stock.get_market_ticker_list(market=market)
        lines = build_lines(raw_dir, tickers)
        (inst_dir / f"{market.lower()}.txt").write_text("\n".join(lines), encoding="utf-8")
        combined.extend(lines)
        print(f"{market}: {len(lines)} instruments")

    (inst_dir / "all.txt").write_text("\n".join(combined), encoding="utf-8")


if __name__ == "__main__":
    main()
