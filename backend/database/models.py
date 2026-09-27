from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


def _now():
    return datetime.now(timezone.utc)


class Experiment(Base):
    """One pass of a test dataset through one agent version."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    agent_version: Mapped[str] = mapped_column(String(50))
    dataset_name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    runs: Mapped[list["Run"]] = relationship(back_populates="experiment")


class Run(Base):
    """One execution of the agent: input in, answer out."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"), index=True)
    test_case_id: Mapped[str | None] = mapped_column(String(100))

    agent_name: Mapped[str] = mapped_column(String(100))
    agent_version: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    input: Mapped[str] = mapped_column(Text)
    output: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float)

    experiment: Mapped[Experiment | None] = relationship(back_populates="runs")
    steps: Mapped[list["Step"]] = relationship(
        back_populates="run", order_by="Step.step_index", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Step(Base):
    """One LLM call or tool call inside a run."""

    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    step_index: Mapped[int] = mapped_column(Integer)
    step_type: Mapped[str] = mapped_column(String(20))  # "llm" or "tool"
    name: Mapped[str] = mapped_column(String(100))
    # JSON because inputs/outputs have different shapes: chat messages for LLM
    # steps, tool arguments and results for tool steps. (JSONB would work too.)
    input: Mapped[dict] = mapped_column(JSON)
    output: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text)

    run: Mapped[Run] = relationship(back_populates="steps")


class Evaluation(Base):
    """One evaluator's verdict on one run."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    evaluator: Mapped[str] = mapped_column(String(50))
    score: Mapped[float] = mapped_column(Float)  # always 0.0 - 1.0
    passed: Mapped[bool]
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped[Run] = relationship(back_populates="evaluations")
