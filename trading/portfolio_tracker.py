"""Portfolio bookkeeping and daily reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class DailySnapshot:
    day: date
    equity: float
    daily_pnl: float
    drawdown_pct: float
    fills: int
    failed_orders: int


@dataclass
class PortfolioTracker:
    peak_equity: float
    history: list[DailySnapshot] = field(default_factory=list)

    def record_day(self, snapshot: DailySnapshot) -> None:
        self.peak_equity = max(self.peak_equity, snapshot.equity)
        self.history.append(snapshot)

    def current_drawdown_pct(self, equity: float) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return (equity - self.peak_equity) / self.peak_equity

    def latest(self) -> DailySnapshot | None:
        return self.history[-1] if self.history else None
