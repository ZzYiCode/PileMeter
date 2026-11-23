from pathlib import Path

from pile_meter.application.pipeline import PipelineContext, PipelineRunner


class RecordStep:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, context: PipelineContext) -> PipelineContext:
        context.metadata[self.name] = True
        return context


def test_runner_records_completed_steps(tmp_path: Path) -> None:
    context = PipelineContext(
        job_id="job-1",
        run_id="run-1",
        artifact_dir=tmp_path / "job-1" / "run-1",
    )

    result = PipelineRunner([RecordStep("validate"), RecordStep("reconstruct")]).run(context)

    assert result.completed_steps == ["validate", "reconstruct"]
    assert result.metadata == {"validate": True, "reconstruct": True}
    assert set(result.step_durations_ms) == {"validate", "reconstruct"}
    assert result.artifact_dir.is_dir()
