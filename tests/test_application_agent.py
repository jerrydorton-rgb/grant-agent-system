from pathlib import Path

from agents.application_agent import ApplicationAgent


def test_application_agent_revises_until_internal_acceptance(tmp_path: Path) -> None:
    agent = ApplicationAgent(output_dir=tmp_path)
    rows = [
        {
            "source_name": "Example Grant",
            "source_url": "https://example.org/grant",
            "title": "Example Small Business Grant",
            "program_type": "grant",
            "eligibility_text": "Small business applicants are eligible.",
            "amount_text": "$10,000",
            "deadline_text": "June 30, 2026",
            "description": "A grant for small business innovation, measurable outcomes, and local impact.",
            "location_focus": "Sacramento",
            "requires_human_review": False,
            "fit_tags": ["small business", "innovation"],
            "qualification_status": "qualified",
            "score": 70,
        }
    ]

    queue = agent.generate(rows)

    assert queue[0]["acceptance_status"] == "accepted_internal_review"
    assert queue[0]["application_score"] >= agent.acceptance_threshold
    assert Path(queue[0]["draft_file"]).exists()


def test_revise_from_feedback_creates_revised_file(tmp_path: Path) -> None:
    draft = tmp_path / "draft.md"
    draft.write_text("# Example Grant\n\nBudget is vague. Outcomes are vague.", encoding="utf-8")

    agent = ApplicationAgent(output_dir=tmp_path)
    revised = agent.revise_from_feedback(draft, "Budget is unclear and outcomes need stronger metrics.")

    assert revised.exists()
    content = revised.read_text(encoding="utf-8")
    assert "External feedback received" in content
    assert "Budget justification" in content
