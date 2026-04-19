from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class QualificationAgent:
    REJECT_TERMS = [
        "nonprofit only",
        "501(c)(3) only",
        "individuals only",
        "students only",
        "homeowner only",
    ]

    LOW_CONFIDENCE_TERMS = [
        "technical assistance",
        "rebate",
        "incentive",
        "supplier",
        "vendor",
        "procurement",
    ]

    POSITIVE_TERMS = [
        "small business",
        "for-profit",
        "business",
        "entrepreneur",
        "innovation",
        "economic development",
        "workforce",
        "training",
    ]

    def qualify(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        qualified: list[dict[str, Any]] = []
        for opp in opportunities:
            eligibility = (opp.get("eligibility_text") or "").lower()
            description = (opp.get("description") or "").lower()
            full_text = f"{eligibility} {description}"

            if any(term in full_text for term in self.REJECT_TERMS):
                opp["qualification_status"] = "rejected"
                opp["qualification_reason"] = "Negative eligibility signal."
                continue

            score = 0
            score += sum(10 for term in self.POSITIVE_TERMS if term in full_text)
            score += 15 if opp.get("location_focus") == "Sacramento" else 0
            score += 10 if opp.get("location_focus") == "California" else 0
            score += 10 if opp.get("program_type") == "grant" else 0
            score += 5 if opp.get("amount_text") else 0
            score += 5 if opp.get("deadline_text") else 0
            score -= 20 if any(term in full_text for term in self.LOW_CONFIDENCE_TERMS) else 0
            score -= 20 if opp.get("requires_human_review") else 0

            opp["score"] = max(score, 0)
            opp["qualification_status"] = "qualified" if opp["score"] >= 25 else "review"
            opp["qualification_reason"] = self._reason(opp)
            opp["next_action"] = self._next_action(opp)
            opp["target_submission_date"] = (datetime.utcnow() + timedelta(days=3)).date().isoformat()
            qualified.append(opp)

        qualified.sort(key=lambda x: (x.get("qualification_status") != "qualified", -x.get("score", 0)))
        return qualified

    @staticmethod
    def _reason(opp: dict[str, Any]) -> str:
        if opp.get("program_type") != "grant":
            return "Opportunity may support cash flow or project economics, but source should be reviewed before treating it as a direct grant."
        if opp.get("requires_human_review"):
            return "Potential fit detected, but source language is ambiguous or incomplete."
        return "Opportunity has business-relevant signals and no hard exclusion terms were found."

    @staticmethod
    def _next_action(opp: dict[str, Any]) -> str:
        if opp.get("qualification_status") == "qualified":
            return "Generate draft narrative and prepare submission checklist."
        return "Human review required before drafting or submission."
