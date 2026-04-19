from agents.qualification_agent import QualificationAgent


def test_rejects_nonprofit_only() -> None:
    agent = QualificationAgent()
    rows = [
        {
            "title": "Example",
            "eligibility_text": "This is nonprofit only.",
            "description": "",
            "program_type": "grant",
            "location_focus": "Sacramento",
            "requires_human_review": False,
        }
    ]
    result = agent.qualify(rows)
    assert result == []
