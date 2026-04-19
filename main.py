from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.sourcing_agent import SourcingAgent
from agents.qualification_agent import QualificationAgent
from agents.application_agent import ApplicationAgent
from agents.followup_agent import FollowupAgent
from utils.io import write_json, write_csv
from utils.sample_data import SAMPLE_OPPORTUNITIES

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}
    
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
APP_DIR = OUTPUT_DIR / "generated_applications"


def run(sample: bool = False) -> None:
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

    summary = {
        "raw_count": len(raw),
        "qualified_count": len(qualified),
        "application_count": len(applications),
        "followup_count": len(followups),
        "output_dir": str(OUTPUT_DIR),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Run from bundled sample data.")
    args = parser.parse_args()
    run(sample=args.sample)
