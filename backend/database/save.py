from database.models import Evaluation, Run, Step


def save_trace(session, trace, experiment_id=None, test_case_id=None):
    """Turn an in-memory Trace into rows in `runs` and `steps`. Returns the Run."""
    run = Run(
        experiment_id=experiment_id,
        test_case_id=test_case_id,
        agent_name=trace.agent_name,
        agent_version=trace.agent_version,
        model=trace.model,
        input=trace.input,
        output=trace.output,
        status=trace.status,
        error_message=trace.error_message,
        started_at=trace.started_at,
        ended_at=trace.ended_at,
        latency_ms=trace.latency_ms,
        input_tokens=trace.input_tokens,
        output_tokens=trace.output_tokens,
        cost_usd=trace.cost_usd,
    )
    for step in trace.steps:
        run.steps.append(Step(
            step_index=step.step_index,
            step_type=step.step_type,
            name=step.name,
            input=step.input,
            output=step.output,
            started_at=step.started_at,
            latency_ms=step.latency_ms,
            input_tokens=step.input_tokens,
            output_tokens=step.output_tokens,
            cost_usd=step.cost_usd,
            error=step.error,
        ))

    session.add(run)
    session.commit()
    return run


def save_evaluations(session, run, results):
    for result in results:
        run.evaluations.append(Evaluation(**result))
    session.commit()
