"""Korea Investment & Securities execution adapter (python-kis)."""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

try:
    from pykis import PyKis
except Exception:  # noqa: BLE001
    PyKis = None


@dataclass
class KisConfig:
    app_key: str
    app_secret: str
    account_no: str
    product_code: str = "01"
    paper: bool = True


class KisBroker:
    def __init__(self, cfg: KisConfig) -> None:
        if PyKis is None:
            raise RuntimeError("python-kis is not installed")
        self.cfg = cfg
        self.kis = PyKis(cfg.app_key, cfg.app_secret, virtual=cfg.paper)

    def get_positions(self) -> dict[str, int]:
        # Wrapper signatures can vary by python-kis version; keep minimal safe fallback.
        positions = {}
        for p in self.kis.account(self.cfg.account_no).balance().stocks:
            positions[p.symbol] = int(p.quantity)
        return positions

    def execute_delta_orders(self, target: dict[str, int], current: dict[str, int]) -> None:
        all_tickers = sorted(set(target) | set(current))
        account = self.kis.account(self.cfg.account_no)
        for ticker in all_tickers:
            delta = target.get(ticker, 0) - current.get(ticker, 0)
            if delta == 0:
                continue
            if delta > 0:
                account.buy(ticker, delta, order="market")
                logger.info("BUY {} {}", ticker, delta)
            else:
                account.sell(ticker, abs(delta), order="market")
                logger.info("SELL {} {}", ticker, abs(delta))
