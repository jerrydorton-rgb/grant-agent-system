from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.sourcing_agent import SourcingAgent
from agents.qualification_agent import QualificationAgent
from agents.application_agent import ApplicationAgent
from agents.followup_agent import FollowupAgent
from utils.io import write_csv, write_json
from utils.sample_data import SAMPLE_OPPORTUNITIES

app = FastAPI(title="Grant Agent")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
APP_DIR = OUTPUT_DIR / "generated_applications"


class ReviseRequest(BaseModel):
    draft_file: str
    feedback: str


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run_endpoint(sample: bool = False) -> dict[str, object]:
    return run(sample=sample)


@app.post("/revise")
def revise_endpoint(request: ReviseRequest) -> dict[str, str]:
    try:
        revised_path = revise_application(Path(request.draft_file), request.feedback)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"revised_file": str(revised_path)}


def run(sample: bool = False) -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    APP_DIR.mkdir(parents=True, exist_ok=True)

    if sample:
        raw = SAMPLE_OPPORTUNITIES
    else:
        raw = SourcingAgent().collect()

    qualified = QualificationAgent().qualify(raw)
    applications = ApplicationAgent(output_dir=APP_DIR).generate(qualified)
    followups = FollowupAgent().build(applications)

    write_json(OUTPUT_DIR / "raw_opportunities.json", raw)
    write_json(OUTPUT_DIR / "qualified_opportunities.json", qualified)
    write_csv(OUTPUT_DIR / "application_queue.csv", applications)
    write_csv(OUTPUT_DIR / "followup_queue.csv", followups)

    summary: dict[str, object] = {
        "raw_count": len(raw),
        "qualified_count": len(qualified),
        "application_count": len(applications),
        "followup_count": len(followups),
        "output_dir": str(OUTPUT_DIR),
    }
    print(json.dumps(summary, indent=2))
    return summary


def revise_application(draft_file: Path, feedback: str) -> Path:
    if not draft_file.is_absolute():
        draft_file = BASE_DIR / draft_file
    if not draft_file.exists():
        raise FileNotFoundError(f"Draft file not found: {draft_file}")
    return ApplicationAgent(output_dir=draft_file.parent).revise_from_feedback(draft_file, feedback)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grant sourcing and application automation.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the full sourcing-to-follow-up pipeline.")
    run_parser.add_argument("--sample", action="store_true", help="Run from bundled sample data.")

    revise_parser = subparsers.add_parser("revise", help="Revise an existing draft using funder/portal feedback.")
    revise_parser.add_argument("--draft", required=True, help="Path to the draft Markdown file.")
    revise_parser.add_argument("--feedback", required=True, help="Feedback or rejection reason to address.")

    parser.add_argument("--sample", action="store_true", help="Backward-compatible shortcut for `run --sample`.")
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()
    if args.command == "revise":
        revised = revise_application(Path(args.draft), args.feedback)
        print(json.dumps({"revised_file": str(revised)}, indent=2))
    else:
        run(sample=bool(getattr(args, "sample", False)))
