import numpy as np

class LogitDemandModel:
    def __init__(self, market_size: int, beta: float, v_mean: float, seed: int = 42):
        self.market_size = market_size
        self.beta = beta
        self.v_mean = v_mean
        self.rng = np.random.default_rng(seed)

    def expected_demand(self, price: float) -> float:
        return self.market_size / (1.0 + np.exp(self.beta * (price - self.v_mean)))

    def sample_demand(self, price: float) -> int:
        expected = self.expected_demand(price)
        return int(self.rng.poisson(max(expected, 0.0)))