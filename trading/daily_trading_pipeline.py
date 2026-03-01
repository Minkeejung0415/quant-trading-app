"""Autonomous daily pipeline for KR market prediction and execution."""

from __future__ import annotations

import os
import pickle
import subprocess
from datetime import datetime

import pandas as pd
import qlib
import yfinance as yf
from loguru import logger
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

from trading.broker_ibkr import IbkrBroker, IbkrConfig
from trading.monitoring import write_daily_report
from trading.risk_manager import RiskConfig, RiskManager

CONFIG = {
    "topk": 30,
    "max_position_pct": 0.05,
    "capital_krw": 100_000_000,
    "min_volume": 100_000,
    "model_path": "models/lgbm_kr_alpha158.pkl",
    "raw_dir": "data/raw_csv",
    "qlib_dir": "data/qlib_kr_data",
    "log_dir": "logs",
    "broker": "ibkr",
    "paper": True,
}


def rebuild_qlib_bin() -> None:
    cmd = [
        "python",
        "-m",
        "qlib.run",
        "dump_bin",
        "--csv_path",
        CONFIG["raw_dir"],
        "--qlib_dir",
        CONFIG["qlib_dir"],
        "--include_fields",
        "open,close,high,low,volume,factor",
        "--date_field_name",
        "date",
        "--file_suffix",
        ".csv",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def load_predictions() -> pd.DataFrame:
    qlib.init(provider_uri=CONFIG["qlib_dir"], region="cn")
    with open(CONFIG["model_path"], "rb") as f:
        model = pickle.load(f)

    handler = Alpha158(
        instruments="kospi",
        start_time="2023-01-01",
        end_time=datetime.now().strftime("%Y-%m-%d"),
        infer_processors=[
            {"class": "RobustZScoreNorm", "kwargs": {"fields_group": "feature", "clip_outlier": True}},
            {"class": "Fillna", "kwargs": {"fields_group": "feature"}},
        ],
        label=[["Ref($close, -1) / $close - 1"]],
    )
    dataset = DatasetH(handler=handler, segments={"test": ["2023-01-01", "2030-12-31"]})
    pred = model.predict(dataset)
    latest = pred.index.get_level_values(0).max()
    return pred.loc[latest].sort_values("score", ascending=False)


def get_vol_proxy() -> float:
    vix = yf.download("^VIX", period="5d", progress=False)
    return float(vix["Close"].iloc[-1])


def filter_liquidity(pred: pd.DataFrame) -> pd.DataFrame:
    if "volume" not in pred.columns:
        return pred
    return pred[pred["volume"] >= CONFIG["min_volume"]]


def to_target_shares(pred: pd.DataFrame, exposure: float) -> dict[str, int]:
    top = pred.head(CONFIG["topk"])
    capital = CONFIG["capital_krw"] * exposure
    per_position = min(capital / CONFIG["topk"], CONFIG["capital_krw"] * CONFIG["max_position_pct"])
    return {ticker: max(1, int(per_position / 50000)) for ticker in top.index}


def run_daily_pipeline() -> None:
    os.makedirs(CONFIG["log_dir"], exist_ok=True)
    logger.add(os.path.join(CONFIG["log_dir"], "trading_{time}.log"), rotation="1 day", retention="90 days")

    rebuild_qlib_bin()
    predictions = load_predictions()
    predictions = filter_liquidity(predictions)

    rm = RiskManager(RiskConfig(max_position_pct=CONFIG["max_position_pct"]))
    vix_proxy = get_vol_proxy()
    exposure = rm.volatility_exposure_multiplier(vix_proxy)
    target = to_target_shares(predictions, exposure)

    broker = IbkrBroker(IbkrConfig(port=7497 if CONFIG["paper"] else 7496))
    broker.connect()
    try:
        current = broker.get_positions()
        broker.execute_delta_orders(target, current)
    finally:
        broker.disconnect()

    report_lines = [
        f"date={datetime.now().date()}",
        f"prediction_count={len(predictions)}",
        f"target_count={len(target)}",
        f"vix_proxy={vix_proxy:.2f}",
        f"exposure_multiplier={exposure:.2f}",
    ]
    write_daily_report(os.path.join(CONFIG["log_dir"], f"daily_report_{datetime.now().date()}.txt"), report_lines)


if __name__ == "__main__":
    run_daily_pipeline()
