from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Experiment, Result, Metric
from ..core.simulator import run_market_simulation
from ..core.evaluation import compute_metrics, choose_best_strategy
from ..core.data_loader import calibrate_from_dataset

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.get("/calibrate")
def calibrate_dataset():
    return calibrate_from_dataset()


@router.post("")
def create_experiment(payload: dict, db: Session = Depends(get_db)):
    strategies = payload.get("strategies", ["static", "epsilon_greedy", "ucb", "stackelberg"])

    experiment = Experiment(
        name=payload.get("name", "Эксперимент ценообразования"),
        market_size=int(payload["market_size"]),
        time_horizon=int(payload["time_horizon"]),
        beta=float(payload["beta"]),
        v_mean=float(payload["v_mean"]),
        price_min=float(payload["price_min"]),
        price_max=float(payload["price_max"]),
        price_step=float(payload["price_step"]),
        strategies=",".join(strategies),
        status="created",
    )

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return {"experiment_id": experiment.id, "status": experiment.status}


@router.get("")
def list_experiments(db: Session = Depends(get_db)):
    return db.query(Experiment).order_by(Experiment.id.desc()).all()


@router.post("/{experiment_id}/run")
def run_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    config = {
        "market_size": experiment.market_size,
        "time_horizon": experiment.time_horizon,
        "beta": experiment.beta,
        "v_mean": experiment.v_mean,
        "price_min": experiment.price_min,
        "price_max": experiment.price_max,
        "price_step": experiment.price_step,
        "strategies": experiment.strategies.split(","),
    }

    history = run_market_simulation(config)
    metrics = compute_metrics(history)
    best_strategy = choose_best_strategy(metrics)

    db.query(Result).filter(Result.experiment_id == experiment_id).delete()
    db.query(Metric).filter(Metric.experiment_id == experiment_id).delete()

    for row in history:
        db.add(Result(
            experiment_id=experiment_id,
            strategy_name=row["strategy_name"],
            round=row["round"],
            price=row["price"],
            demand=row["demand"],
            revenue=row["revenue"],
        ))

    for row in metrics:
        db.add(Metric(
            experiment_id=experiment_id,
            strategy_name=row["strategy_name"],
            metric_name=row["metric_name"],
            metric_value=row["metric_value"],
        ))

    experiment.status = "finished"
    db.commit()

    return {
        "experiment_id": experiment_id,
        "status": "finished",
        "best_strategy": best_strategy,
    }


@router.get("/{experiment_id}/results")
def get_results(experiment_id: int, db: Session = Depends(get_db)):
    rows = db.query(Result).filter(Result.experiment_id == experiment_id).all()
    return [
        {
            "strategy_name": r.strategy_name,
            "round": r.round,
            "price": r.price,
            "demand": r.demand,
            "revenue": r.revenue,
        }
        for r in rows
    ]


@router.get("/{experiment_id}/metrics")
def get_metrics(experiment_id: int, db: Session = Depends(get_db)):
    rows = db.query(Metric).filter(Metric.experiment_id == experiment_id).all()
    return [
        {
            "strategy_name": r.strategy_name,
            "metric_name": r.metric_name,
            "metric_value": r.metric_value,
        }
        for r in rows
    ]