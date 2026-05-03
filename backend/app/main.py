from fastapi import FastAPI
from .database import Base, engine
from .models import Experiment, Result, Metric
from .api.experiments import router as experiments_router

app = FastAPI(title="Russian Marketplace Adaptive Pricing Platform")

Base.metadata.create_all(bind=engine)

app.include_router(experiments_router)