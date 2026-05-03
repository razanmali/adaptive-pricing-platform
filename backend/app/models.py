from sqlalchemy import Column, Integer, Float, String, ForeignKey
from .database import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    market_size = Column(Integer, nullable=False)
    time_horizon = Column(Integer, nullable=False)

    price_min = Column(Float, nullable=False)
    price_max = Column(Float, nullable=False)
    price_step = Column(Float, nullable=False)

    beta = Column(Float, nullable=False)
    v_mean = Column(Float, nullable=False)

    strategies = Column(String, nullable=False)
    status = Column(String, default="created")


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))

    strategy_name = Column(String, nullable=False)
    round = Column(Integer, nullable=False)

    price = Column(Float, nullable=False)
    demand = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))

    strategy_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)