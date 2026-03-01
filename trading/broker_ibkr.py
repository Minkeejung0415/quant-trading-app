"""Interactive Brokers execution adapter."""

from __future__ import annotations

import time
from dataclasses import dataclass

from ib_insync import IB, MarketOrder, Stock
from loguru import logger


@dataclass
class IbkrConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    exchange: str = "KSE"
    currency: str = "KRW"


class IbkrBroker:
    def __init__(self, cfg: IbkrConfig) -> None:
        self.cfg = cfg
        self.ib = IB()

    def connect(self) -> None:
        self.ib.connect(self.cfg.host, self.cfg.port, clientId=self.cfg.client_id)

    def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()

    def get_positions(self) -> dict[str, int]:
        positions = {}
        for p in self.ib.positions():
            symbol = p.contract.symbol
            positions[symbol] = int(p.position)
        return positions

    def execute_delta_orders(self, target: dict[str, int], current: dict[str, int], max_retries: int = 3) -> None:
        tickers = sorted(set(target) | set(current))
        for ticker in tickers:
            delta = target.get(ticker, 0) - current.get(ticker, 0)
            if delta == 0:
                continue
            action = "BUY" if delta > 0 else "SELL"
            qty = abs(delta)

            contract = Stock(ticker, self.cfg.exchange, self.cfg.currency)
            self.ib.qualifyContracts(contract)

            for attempt in range(1, max_retries + 1):
                trade = self.ib.placeOrder(contract, MarketOrder(action, qty))
                self.ib.sleep(2)
                if trade.orderStatus.status in {"Submitted", "Filled", "PreSubmitted"}:
                    logger.info("{} {} {} attempt {}", action, qty, ticker, attempt)
                    break
                logger.warning("Order retry {} for {} {}", attempt, action, ticker)
                time.sleep(2**attempt)
