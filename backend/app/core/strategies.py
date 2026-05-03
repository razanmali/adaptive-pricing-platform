import numpy as np


class StaticPricing:
    def __init__(self, price_set):
        self.price_set = list(price_set)
        self.fixed_price = self.price_set[len(self.price_set) // 2]

    def select_price(self):
        return float(self.fixed_price)

    def update(self, price, demand, revenue):
        pass


class EpsilonGreedyPricing:
    def __init__(self, price_set, epsilon=0.1, seed=42):
        self.price_set = list(price_set)
        self.epsilon = epsilon
        self.rng = np.random.default_rng(seed)
        self.counts = {p: 0 for p in self.price_set}
        self.revenues = {p: 0.0 for p in self.price_set}

    def select_price(self):
        if self.rng.random() < self.epsilon:
            return float(self.rng.choice(self.price_set))

        averages = {
            p: self.revenues[p] / self.counts[p] if self.counts[p] > 0 else 0.0
            for p in self.price_set
        }

        return float(max(averages, key=averages.get))

    def update(self, price, demand, revenue):
        self.counts[price] += 1
        self.revenues[price] += revenue


class UCBPricing:
    def __init__(self, price_set):
        self.price_set = list(price_set)
        self.counts = {p: 0 for p in self.price_set}
        self.revenues = {p: 0.0 for p in self.price_set}
        self.t = 0

    def select_price(self):
        self.t += 1

        for p in self.price_set:
            if self.counts[p] == 0:
                return float(p)

        scores = {}
        for p in self.price_set:
            mean = self.revenues[p] / self.counts[p]
            bonus = np.sqrt(2 * np.log(self.t) / self.counts[p])
            scores[p] = mean + bonus

        return float(max(scores, key=scores.get))

    def update(self, price, demand, revenue):
        self.counts[price] += 1
        self.revenues[price] += revenue


class StackelbergBestResponse:
    def __init__(self, price_set, demand_model):
        self.price_set = list(price_set)
        self.demand_model = demand_model

    def select_price(self):
        expected_revenues = {
            p: p * self.demand_model.expected_demand(p)
            for p in self.price_set
        }
        return float(max(expected_revenues, key=expected_revenues.get))

    def update(self, price, demand, revenue):
        pass