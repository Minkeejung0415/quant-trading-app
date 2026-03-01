"""Risk controls for autonomous Korean equity trading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class RiskConfig:
    max_position_pct: float = 0.05
    max_daily_loss_pct: float = 0.03
    max_drawdown_pct: float = 0.15
    vol_exit_threshold: float = 30.0
    vol_reenter_threshold: float = 22.0
    stop_loss_pct: float = 0.07
    max_sector_exposure_pct: float = 0.25
    max_avg_correlation: float = 0.6


class RiskManager:
    def __init__(self, cfg: RiskConfig) -> None:
        self.cfg = cfg

    def volatility_exposure_multiplier(self, volatility_index_value: float) -> float:
        if volatility_index_value >= self.cfg.vol_exit_threshold:
            return 0.3
        if volatility_index_value >= 25:
            return 0.6
        if volatility_index_value <= self.cfg.vol_reenter_threshold:
            return 1.0
        return 0.8

    def should_halt(self, daily_pnl_pct: float, drawdown_pct: float) -> bool:
        return daily_pnl_pct <= -self.cfg.max_daily_loss_pct or drawdown_pct <= -self.cfg.max_drawdown_pct

    def enforce_position_limit(self, target_weights: dict[str, float]) -> dict[str, float]:
        clipped = {k: min(v, self.cfg.max_position_pct) for k, v in target_weights.items()}
        total = sum(clipped.values())
        if total == 0:
            return clipped
        return {k: v / total for k, v in clipped.items()}

    def stop_loss_triggers(self, positions: Iterable[dict]) -> list[str]:
        trigger = []
        for pos in positions:
            if pos["entry_price"] <= 0:
                continue
            if (pos["last_price"] - pos["entry_price"]) / pos["entry_price"] <= -self.cfg.stop_loss_pct:
                trigger.append(pos["ticker"])
        return trigger

    def high_correlation(self, returns_df: pd.DataFrame) -> bool:
        if returns_df.empty or returns_df.shape[1] < 2:
            return False
        corr = returns_df.corr().to_numpy()
        upper = corr[np.triu_indices_from(corr, k=1)]
        upper = upper[~np.isnan(upper)]
        return bool(upper.size and upper.mean() > self.cfg.max_avg_correlation)
