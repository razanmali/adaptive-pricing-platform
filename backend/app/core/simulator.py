import numpy as np
from .demand import LogitDemandModel
from .strategies import (
    StaticPricing,
    EpsilonGreedyPricing,
    UCBPricing,
    StackelbergBestResponse,
)


def create_price_set(price_min, price_max, price_step):
    return [
        round(float(p), 2)
        for p in np.arange(price_min, price_max + price_step, price_step)
    ]


def build_strategy(name, price_set, demand_model):
    if name == "static":
        return StaticPricing(price_set)

    if name == "epsilon_greedy":
        return EpsilonGreedyPricing(price_set)

    if name == "ucb":
        return UCBPricing(price_set)

    if name == "stackelberg":
        return StackelbergBestResponse(price_set, demand_model)

    raise ValueError(f"Unknown strategy: {name}")


def run_market_simulation(config: dict):
    price_set = create_price_set(
        config["price_min"],
        config["price_max"],
        config["price_step"],
    )

    demand_model = LogitDemandModel(
        market_size=config["market_size"],
        beta=config["beta"],
        v_mean=config["v_mean"],
        seed=config.get("seed", 42),
    )

    strategies = {
        name: build_strategy(name, price_set, demand_model)
        for name in config["strategies"]
    }

    history = []

    for t in range(config["time_horizon"]):
        for strategy_name, strategy in strategies.items():
            price = strategy.select_price()
            demand = demand_model.sample_demand(price)
            revenue = price * demand
            strategy.update(price, demand, revenue)

            history.append({
                "strategy_name": strategy_name,
                "round": t,
                "price": float(price),
                "demand": float(demand),
                "revenue": float(revenue),
            })

    return history