# Korean Autonomous Quant Trading System (Qlib + pykrx + IBKR/KIS)

This repository now contains an end-to-end scaffold for an autonomous Korean stock-market quant system:

- **Data pipeline**: `pykrx` OHLCV collection → per-ticker CSV → Qlib binary data.
- **Modeling**: Qlib + `Alpha158` + LightGBM workflow for Korean equities.
- **Backtesting evaluation**: threshold checks for IC, Sharpe, drawdown.
- **Live bridge**: broker adapters for IBKR and KIS.
- **Risk**: volatility-exposure control, daily loss / drawdown guard rails, position limits.
- **Automation**: scheduler loop for pre-open execution.

## Project Structure

```text
config/
  kr_lgbm_alpha158.yaml
  kr_double_ensemble.yaml
  broker_config.yaml.example
scripts/
  download_korean_data.py
  create_instruments.py
  update_data_daily.py
  train_and_backtest.py
  evaluate_backtest.py
trading/
  risk_manager.py
  broker_ibkr.py
  broker_kis.py
  portfolio_tracker.py
  daily_trading_pipeline.py
scheduler.py
requirements.txt
```

## Quickstart

1. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Download initial data:

```bash
python scripts/download_korean_data.py --start-date 20150101 --end-date 20260228
```

3. Build Qlib binaries:

```bash
python -m qlib.run dump_bin \
  --csv_path ./data/raw_csv \
  --qlib_dir ./data/qlib_kr_data \
  --include_fields open,close,high,low,volume,factor \
  --date_field_name date \
  --file_suffix .csv
```

4. Create instrument files:

```bash
python scripts/create_instruments.py
```

5. Train baseline model:

```bash
python scripts/train_and_backtest.py --config config/kr_lgbm_alpha158.yaml
```

6. Start scheduled automation:

```bash
python scheduler.py
```

## Important market-specific defaults

- Label formula: `Ref($close, -1) / $close - 1`.
- Daily price limit in backtest: `limit_threshold: 0.30`.
- Trade unit: `trade_unit: 1`.
- Annualization: `ann_scaler: 252`.
- Start with **paper trading only**.

## Notes

- `broker_config.yaml.example` is a template; place real credentials in a non-versioned local file.
- IBKR adapter is implemented and wired by default in the daily pipeline.
- KIS adapter is included as an alternative and may need small API signature adjustments depending on `python-kis` version.
