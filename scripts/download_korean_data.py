"""Download Korean stock OHLCV data with pykrx and save per-ticker CSV files."""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime

import pandas as pd
from loguru import logger
from pykrx import stock

KOREAN_TO_ENGLISH = {
    "시가": "Open",
    "고가": "High",
    "저가": "Low",
    "종가": "Close",
    "거래량": "Volume",
    "거래대금": "TradingValue",
    "등락률": "ChangeRate",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="20150101")
    parser.add_argument("--end-date", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--markets", nargs="+", default=["KOSPI", "KOSDAQ"])
    parser.add_argument("--output-dir", default="data/raw_csv")
    parser.add_argument("--sleep", type=float, default=1.2)
    return parser.parse_args()


def download_ticker(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    adjusted = stock.get_market_ohlcv(start_date, end_date, ticker, adjusted=True)
    raw = stock.get_market_ohlcv(start_date, end_date, ticker, adjusted=False)
    if adjusted.empty:
        return pd.DataFrame()

    adjusted = adjusted.rename(columns=KOREAN_TO_ENGLISH)
    raw = raw.rename(columns={k: f"{v}_raw" for k, v in KOREAN_TO_ENGLISH.items()})
    merged = adjusted.join(raw[["Close_raw"]], how="left")
    merged["factor"] = merged["Close"] / merged["Close_raw"].replace(0, pd.NA)
    merged["factor"] = merged["factor"].fillna(1.0)

    qlib_df = merged[["Open", "High", "Low", "Close", "Volume", "factor"]].copy()
    qlib_df.columns = ["open", "high", "low", "close", "volume", "factor"]
    qlib_df.index.name = "date"
    return qlib_df


def main() -> None:
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    for market in args.markets:
        tickers = stock.get_market_ticker_list(market=market)
        logger.info("Found {} tickers in {}", len(tickers), market)
        for idx, ticker in enumerate(tickers, start=1):
            name = stock.get_market_ticker_name(ticker)
            try:
                df = download_ticker(ticker, args.start_date, args.end_date)
                if df.empty:
                    logger.warning("No data for {} ({})", ticker, name)
                    continue
                out = os.path.join(args.output_dir, f"{ticker}.csv")
                df.to_csv(out)
                if idx % 50 == 0:
                    logger.info("[{}] {}/{} downloaded", market, idx, len(tickers))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Download failed for {} ({}): {}", ticker, name, exc)
                time.sleep(args.sleep * 2)
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
