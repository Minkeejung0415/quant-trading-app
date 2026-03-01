"""Train a Qlib model and run records from YAML configuration."""

from __future__ import annotations

import argparse
import os
import pickle

import qlib
import yaml
from qlib.model.trainer import task_train


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/kr_lgbm_alpha158.yaml")
    parser.add_argument("--model-output", default="models/lgbm_kr_alpha158.pkl")
    parser.add_argument("--experiment-name", default="kr_lgbm_alpha158")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    qlib.init(**config["qlib_init"])
    recorder, model = task_train(config["task"], experiment_name=args.experiment_name)

    os.makedirs(os.path.dirname(args.model_output), exist_ok=True)
    with open(args.model_output, "wb") as f:
        pickle.dump(model, f)

    print(f"Saved model to {args.model_output}")
    print(f"Recorder ID: {recorder.id}")


if __name__ == "__main__":
    main()
