from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path("..") / "data"


def find_dataset_file() -> Path:
    candidates = list(DATA_DIR.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(
            "CSV dataset not found. Put your Kaggle CSV file inside the data/ folder."
        )
    return candidates[0]


def load_marketplace_dataset(max_rows: int = 300_000) -> pd.DataFrame:
    path = find_dataset_file()

    df = pd.read_csv(path, nrows=max_rows)

    required = {"event_type", "price"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df = df[["event_type", "price"]].copy()
    df = df.dropna()
    df = df[df["price"] > 0]

    return df


def calibrate_from_dataset(max_rows: int = 300_000) -> dict:
    df = load_marketplace_dataset(max_rows=max_rows)

    purchases = df[df["event_type"] == "purchase"].copy()

    if purchases.empty:
        raise ValueError("No purchase events found in dataset.")

    prices = purchases["price"].astype(float)

    price_min = float(np.percentile(prices, 5))
    price_max = float(np.percentile(prices, 95))
    v_mean = float(np.percentile(prices, 70))

    # Approximation: higher spread means weaker price sensitivity
    spread = max(price_max - price_min, 1.0)
    beta = float(min(max(5.0 / spread, 0.005), 0.2))

    market_size = int(min(max(len(purchases) / 100, 500), 5000))

    return {
        "price_min": round(price_min, 2),
        "price_max": round(price_max, 2),
        "v_mean": round(v_mean, 2),
        "beta": round(beta, 4),
        "market_size": market_size,
        "purchase_count": int(len(purchases)),
    }