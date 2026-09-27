from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from database.db import get_session
from database.models import Experiment
from services.regression import compare_experiments, summarize_experiment

router = APIRouter(prefix="/api/experiments")


@router.get("")
def list_experiments(session=Depends(get_session)):
    ids = session.scalars(select(Experiment.id).order_by(Experiment.id.desc())).all()
    return [summarize_experiment(session, experiment_id) for experiment_id in ids]


@router.get("/compare")
def compare(a: int, b: int, session=Depends(get_session)):
    report = compare_experiments(session, a, b)
    if report is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return report


@router.get("/{experiment_id}")
def get_experiment(experiment_id: int, session=Depends(get_session)):
    summary = summarize_experiment(session, experiment_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return summary
