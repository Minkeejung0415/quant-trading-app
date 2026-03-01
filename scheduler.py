"""Run the daily pipeline at Korean pre-open equivalent in local timezone."""

from __future__ import annotations

import time

import schedule

from trading.daily_trading_pipeline import run_daily_pipeline


# 15:30 PST ~= 08:30 KST next day. Adjust manually for PDT if needed.
schedule.every().monday.at("15:30").do(run_daily_pipeline)
schedule.every().tuesday.at("15:30").do(run_daily_pipeline)
schedule.every().wednesday.at("15:30").do(run_daily_pipeline)
schedule.every().thursday.at("15:30").do(run_daily_pipeline)
schedule.every().friday.at("15:30").do(run_daily_pipeline)


if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
