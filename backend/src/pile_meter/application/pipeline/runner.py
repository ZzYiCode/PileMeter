from __future__ import annotations

import time
from typing import Protocol

from pile_meter.application.pipeline.context import PipelineContext


class PipelineStep(Protocol):
    name: str

    def run(self, context: PipelineContext) -> PipelineContext: ...


class PipelineRunner:
    """Run pipeline steps sequentially and record timing after each success."""

    def __init__(self, steps: list[PipelineStep]) -> None:
        names = [step.name for step in steps]
        if len(names) != len(set(names)):
            raise ValueError("Pipeline step names must be unique")
        self._steps = steps

    @property
    def step_names(self) -> list[str]:
        return [step.name for step in self._steps]

    def run(self, context: PipelineContext) -> PipelineContext:
        context.ensure_artifact_dir()
        for step in self._steps:
            started = time.perf_counter()
            context = step.run(context)
            elapsed_ms = (time.perf_counter() - started) * 1000
            context.step_durations_ms[step.name] = round(elapsed_ms, 3)
            context.completed_steps.append(step.name)
        return context
