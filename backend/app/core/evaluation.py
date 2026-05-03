import pandas as pd


def compute_metrics(history: list[dict]):
    df = pd.DataFrame(history)
    metrics = []

    for strategy, group in df.groupby("strategy_name"):
        cumulative_revenue = group["revenue"].sum()
        average_revenue = group["revenue"].mean()
        average_demand = group["demand"].mean()
        price_volatility = group["price"].std() if len(group) > 1 else 0.0
        final_price = group["price"].iloc[-1]

        metrics.extend([
            {
                "strategy_name": strategy,
                "metric_name": "cumulative_revenue",
                "metric_value": float(cumulative_revenue),
            },
            {
                "strategy_name": strategy,
                "metric_name": "average_revenue",
                "metric_value": float(average_revenue),
            },
            {
                "strategy_name": strategy,
                "metric_name": "average_demand",
                "metric_value": float(average_demand),
            },
            {
                "strategy_name": strategy,
                "metric_name": "price_volatility",
                "metric_value": float(price_volatility),
            },
            {
                "strategy_name": strategy,
                "metric_name": "final_price",
                "metric_value": float(final_price),
            },
        ])

    return metrics


def choose_best_strategy(metrics: list[dict]):
    revenue_rows = [
        row for row in metrics
        if row["metric_name"] == "cumulative_revenue"
    ]

    if not revenue_rows:
        return None

    best = max(revenue_rows, key=lambda x: x["metric_value"])
    return best["strategy_name"]