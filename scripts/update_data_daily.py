"""Incremental daily update for local per-ticker CSV files."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from loguru import logger
from pykrx import stock


KOR_COLS = ["Open", "High", "Low", "Close", "Volume", "TradingValue", "ChangeRate"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw_csv")
    parser.add_argument("--sleep", type=float, default=0.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    prev = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")

    for market in ["KOSPI", "KOSDAQ"]:
        for ticker in stock.get_market_ticker_list(market=market):
            try:
                df = stock.get_market_ohlcv(prev, today, ticker)
                if df.empty:
                    continue
                df.columns = KOR_COLS
                qlib_df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
                qlib_df.columns = ["open", "high", "low", "close", "volume"]
                qlib_df["factor"] = 1.0
                qlib_df.index.name = "date"

                path = raw_dir / f"{ticker}.csv"
                if path.exists():
                    existing = pd.read_csv(path, index_col=0, parse_dates=True)
                    merged = pd.concat([existing, qlib_df])
                    merged = merged[~merged.index.duplicated(keep="last")].sort_index()
                    merged.to_csv(path)
                else:
                    qlib_df.to_csv(path)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed {}: {}", ticker, exc)
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
