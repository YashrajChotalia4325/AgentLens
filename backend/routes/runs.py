from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from agent.versions import VERSIONS
from database.db import get_session
from database.models import Run
from services.run_service import run_and_save

router = APIRouter(prefix="/api")


def run_summary(run):
    return {
        "id": run.id,
        "experiment_id": run.experiment_id,
        "test_case_id": run.test_case_id,
        "agent_name": run.agent_name,
        "agent_version": run.agent_version,
        "model": run.model,
        "input": run.input,
        "status": run.status,
        "started_at": run.started_at,
        "latency_ms": run.latency_ms,
        "total_tokens": run.input_tokens + run.output_tokens,
        "cost_usd": run.cost_usd,
        "step_count": len(run.steps),
        "evaluations": {e.evaluator: {"score": e.score, "passed": e.passed} for e in run.evaluations},
    }


def run_detail(run):
    return {
        **run_summary(run),
        "output": run.output,
        "error_message": run.error_message,
        "ended_at": run.ended_at,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "steps": [
            {
                "step_index": s.step_index,
                "step_type": s.step_type,
                "name": s.name,
                "input": s.input,
                "output": s.output,
                "started_at": s.started_at,
                "latency_ms": s.latency_ms,
                "input_tokens": s.input_tokens,
                "output_tokens": s.output_tokens,
                "cost_usd": s.cost_usd,
                "error": s.error,
            }
            for s in run.steps
        ],
        "evaluation_details": [
            {"evaluator": e.evaluator, "score": e.score, "passed": e.passed, "details": e.details}
            for e in run.evaluations
        ],
    }


@router.get("/versions")
def list_versions():
    return [{"version": name, "model": config["model"]} for name, config in VERSIONS.items()]


@router.get("/runs")
def list_runs(limit: int = 50, experiment_id: int | None = None, session=Depends(get_session)):
    query = (
        select(Run)
        .options(selectinload(Run.steps), selectinload(Run.evaluations))
        .order_by(Run.id.desc())
        .limit(limit)
    )
    if experiment_id is not None:
        query = query.where(Run.experiment_id == experiment_id)
    return [run_summary(run) for run in session.scalars(query)]


@router.get("/runs/{run_id}")
def get_run(run_id: int, session=Depends(get_session)):
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_detail(run)


class NewRunRequest(BaseModel):
    # A cap on question length: a support question never needs more, and it stops
    # someone pasting a whole book into the public demo to burn tokens.
    input: str = Field(max_length=500)
    version: str = "v1"
    use_judge: bool = True


# A plain `def` (not `async def`): FastAPI runs it in a worker thread, so the
# slow, blocking LLM calls don't freeze the rest of the server.
@router.post("/runs")
def create_run(request: NewRunRequest, session=Depends(get_session)):
    if request.version not in VERSIONS:
        raise HTTPException(status_code=400, detail=f"Unknown version '{request.version}'")
    if not request.input.strip():
        raise HTTPException(status_code=400, detail="Input is empty")

    run_id, _ = run_and_save(request.input, request.version, use_judge=request.use_judge)
    return run_detail(session.get(Run, run_id))
