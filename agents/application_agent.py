from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Template

try:  # package layout
    from utils.io import slugify
except ModuleNotFoundError:  # flat upload layout
    from io import slugify  # type: ignore


APPLICATION_TEMPLATE = Template("""# {{ title }}

## Internal opportunity summary
- Source: {{ source_name }}
- URL: {{ source_url }}
- Program type: {{ program_type }}
- Amount text: {{ amount_text or 'Not captured' }}
- Deadline text: {{ deadline_text or 'Not captured' }}
- Qualification status: {{ qualification_status }}
- Score: {{ score }}
- Application quality score: {{ application_score }}
- Revision round: {{ revision_round }}
- Acceptance status: {{ acceptance_status }}

## Draft narrative
### Organization overview
{{ company_overview }}

### Need / opportunity
{{ need_statement }}

### Proposed use of funds
{{ use_of_funds }}

### Alignment with funder priorities
{{ funder_alignment }}

### Implementation plan
{{ implementation_plan }}

### Sacramento impact
{{ sacramento_impact }}

### Outcomes and measurement
{{ outcomes }}

### Budget justification
{{ budget_justification }}

### Risk and compliance note
{{ compliance_note }}

## Acceptance checklist
{% for item in acceptance_checklist -%}
- {{ item }}
{% endfor %}

## Revision history
{% for item in revision_history -%}
- Round {{ item.round }}: {{ item.summary }}
{% endfor %}

## Extracted source text
{{ extracted_text }}
""")


@dataclass(frozen=True)
class ReviewResult:
    score: int
    accepted: bool
    issues: list[str]
    recommendations: list[str]


class ApplicationAgent:
    """Generate and revise grant application drafts until they pass an internal acceptance gate.

    This does not guarantee the funder will award the grant. It means the draft has been
    adjusted until it satisfies this app's submission-readiness rubric or reaches max rounds.
    """

    DEFAULT_ACCEPTANCE_THRESHOLD = 85

    def __init__(
        self,
        output_dir: Path,
        acceptance_threshold: int = DEFAULT_ACCEPTANCE_THRESHOLD,
        max_revision_rounds: int = 5,
    ) -> None:
        self.output_dir = output_dir
        self.acceptance_threshold = acceptance_threshold
        self.max_revision_rounds = max_revision_rounds
        self.library = self._load_content_library()

    def generate(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        queue: list[dict[str, Any]] = []
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for opp in opportunities:
            record = self._build_initial_record(opp)
            record = self._revise_until_accepted(record)

            filename = f"{slugify(record['title'])}.md"
            out_path = self.output_dir / filename
            out_path.write_text(APPLICATION_TEMPLATE.render(**record), encoding="utf-8")

            queue.append(
                {
                    "title": record["title"],
                    "source_name": record["source_name"],
                    "source_url": record["source_url"],
                    "program_type": record["program_type"],
                    "qualification_status": record["qualification_status"],
                    "score": record["score"],
                    "application_score": record["application_score"],
                    "acceptance_status": record["acceptance_status"],
                    "revision_rounds": record["revision_round"],
                    "draft_file": str(out_path),
                    "next_action": self._next_action(record),
                }
            )
        return queue

    def revise_from_feedback(
        self,
        draft_file: Path,
        feedback: str,
        opportunity: dict[str, Any] | None = None,
    ) -> Path:
        """Revise a saved draft using actual funder/portal feedback.

        Use this after a rejected or returned application. The revised file is saved next to
        the original with a -revised suffix.
        """
        existing = draft_file.read_text(encoding="utf-8")
        opp = opportunity or {"title": self._extract_title(existing), "description": existing}
        record = self._build_initial_record(opp)
        record["revision_history"].append({"round": 0, "summary": f"External feedback received: {feedback}"})
        record["extracted_text"] = existing[:4000]
        record = self._apply_feedback(record, feedback)
        record = self._revise_until_accepted(record)

        revised_path = draft_file.with_name(f"{draft_file.stem}-revised.md")
        revised_path.write_text(APPLICATION_TEMPLATE.render(**record), encoding="utf-8")
        return revised_path

    def _load_content_library(self) -> dict[str, Any]:
        candidates = [
            Path(__file__).resolve().parent / "content_library.json",
            Path(__file__).resolve().parent / "data" / "content_library.json",
            Path(__file__).resolve().parents[1] / "data" / "content_library.json",
        ]
        for path in candidates:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        raise FileNotFoundError("Could not find content_library.json")

    def _build_initial_record(self, opp: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": opp.get("title", "Untitled opportunity"),
            "source_name": opp.get("source_name", "Unknown"),
            "source_url": opp.get("source_url", ""),
            "program_type": opp.get("program_type", "unknown"),
            "amount_text": opp.get("amount_text", ""),
            "deadline_text": opp.get("deadline_text", ""),
            "qualification_status": opp.get("qualification_status", "review"),
            "score": opp.get("score", 0),
            "company_overview": self.library["company_overview"],
            "need_statement": self.library["need_statement"],
            "use_of_funds": self._pick_use_of_funds(opp),
            "funder_alignment": self._build_funder_alignment(opp),
            "implementation_plan": self._build_implementation_plan(opp),
            "sacramento_impact": self.library["sacramento_impact"],
            "outcomes": self.library["outcomes"],
            "budget_justification": self._build_budget_justification(opp),
            "compliance_note": self.library["compliance_note"],
            "extracted_text": (opp.get("description") or "")[:4000],
            "acceptance_checklist": [],
            "revision_history": [],
            "revision_round": 0,
            "application_score": 0,
            "acceptance_status": "draft",
        }

    def _revise_until_accepted(self, record: dict[str, Any]) -> dict[str, Any]:
        for round_number in range(self.max_revision_rounds + 1):
            review = self._review(record)
            record["application_score"] = review.score
            record["acceptance_checklist"] = self._checklist(review)
            record["acceptance_status"] = "accepted_internal_review" if review.accepted else "needs_revision"
            record["revision_round"] = round_number
            if review.accepted:
                return record
            if round_number == self.max_revision_rounds:
                record["acceptance_status"] = "max_revisions_reached"
                return record
            record = self._revise(record, review, round_number + 1)
        return record

    def _review(self, record: dict[str, Any]) -> ReviewResult:
        issues: list[str] = []
        recommendations: list[str] = []
        score = 40

        required_fields = {
            "company_overview": "organization overview",
            "need_statement": "need statement",
            "use_of_funds": "use of funds",
            "funder_alignment": "funder alignment",
            "implementation_plan": "implementation plan",
            "outcomes": "outcomes",
            "budget_justification": "budget justification",
            "compliance_note": "compliance note",
        }
        for key, label in required_fields.items():
            value = str(record.get(key, "")).strip()
            if len(value) >= 120:
                score += 5
            else:
                issues.append(f"Expand {label}; current section is too thin.")
                recommendations.append(f"Add specific, funder-facing detail to the {label} section.")

        combined = " ".join(str(record.get(k, "")) for k in required_fields)
        lower = combined.lower()
        signal_terms = ["measurable", "eligible", "timeline", "budget", "outcomes", "impact", "capacity"]
        score += sum(2 for term in signal_terms if term in lower)

        if not record.get("amount_text"):
            issues.append("Funding amount was not captured from the source.")
            recommendations.append("Keep requested budget flexible and verify allowable amount before submission.")
        else:
            score += 4

        if record.get("qualification_status") != "qualified":
            issues.append("Opportunity is not fully qualified yet.")
            recommendations.append("Confirm eligibility before submission.")
        else:
            score += 6

        score = min(score, 100)
        return ReviewResult(
            score=score,
            accepted=score >= self.acceptance_threshold and not self._has_blocking_issue(issues),
            issues=issues,
            recommendations=recommendations,
        )

    def _has_blocking_issue(self, issues: list[str]) -> bool:
        blocking = ("Opportunity is not fully qualified yet",)
        return any(any(term in issue for term in blocking) for issue in issues)

    def _revise(self, record: dict[str, Any], review: ReviewResult, round_number: int) -> dict[str, Any]:
        record["revision_history"].append(
            {"round": round_number, "summary": "; ".join(review.recommendations) or "Strengthened draft."}
        )
        for issue in review.issues:
            if "organization overview" in issue:
                record["company_overview"] += " The applicant has the operational focus to convert small awards into practical execution, documented deliverables, and follow-through for entrepreneurs and small-business clients."
            elif "need statement" in issue:
                record["need_statement"] += " The requested support addresses an immediate capacity gap by funding tools, outreach, and implementation activities that the business could deploy within the award period."
            elif "use of funds" in issue:
                record["use_of_funds"] += " Funds will be limited to eligible, documented expenses that directly support the program purpose and can be tracked through invoices, receipts, and milestone reporting."
            elif "funder alignment" in issue:
                record["funder_alignment"] += " The proposal is aligned to the funder by connecting the requested investment to eligibility, local economic benefit, practical implementation, and measurable outputs."
            elif "implementation plan" in issue:
                record["implementation_plan"] += " Execution will follow a 30/60/90-day plan: finalize scope, purchase or deploy approved resources, launch outreach or delivery, then report measurable results."
            elif "outcomes" in issue:
                record["outcomes"] += " Progress will be measured through completed activities, businesses reached, resources deployed, follow-up engagement, and documented improvements in readiness or operating capacity."
            elif "budget justification" in issue:
                record["budget_justification"] += " Each budget item will be tied to an allowable cost category, a vendor quote or estimate where available, and a clear business purpose."
            elif "compliance note" in issue:
                record["compliance_note"] += " The applicant will retain documentation, avoid unsupported claims, and revise the scope immediately if any cost is deemed ineligible."
        return record

    def _apply_feedback(self, record: dict[str, Any], feedback: str) -> dict[str, Any]:
        feedback_lower = feedback.lower()
        if any(term in feedback_lower for term in ["budget", "cost", "expense", "allowable"]):
            record["budget_justification"] += " This revision adds a clearer cost rationale, separates essential expenses from optional expenses, and ties each requested dollar to an eligible activity."
        if any(term in feedback_lower for term in ["impact", "outcome", "metric", "measure"]):
            record["outcomes"] += " This revision adds measurable outputs, including number of businesses reached, delivery milestones, and documented improvements in readiness or operating capacity."
        if any(term in feedback_lower for term in ["eligible", "eligibility", "not eligible"]):
            record["compliance_note"] += " This revision flags eligibility as a required pre-submission verification item and removes unsupported eligibility assumptions."
        if any(term in feedback_lower for term in ["timeline", "schedule", "implementation"]):
            record["implementation_plan"] += " This revision clarifies timing with a phased implementation plan and milestone-based reporting."
        if any(term in feedback_lower for term in ["alignment", "priority", "mission"]):
            record["funder_alignment"] += " This revision directly connects the proposal to the funder's stated priorities and expected community or business impact."
        return record

    def _checklist(self, review: ReviewResult) -> list[str]:
        if review.accepted:
            return [
                "Internal readiness gate passed.",
                "Verify applicant eligibility against official program rules.",
                "Attach required documents before submission.",
                "Confirm budget and requested amount match allowable costs.",
            ]
        return [f"Needs revision: {issue}" for issue in review.issues]

    def _next_action(self, record: dict[str, Any]) -> str:
        if record["acceptance_status"] == "accepted_internal_review":
            return "Verify official eligibility, attach documents, and submit. If funder returns feedback, run revise_from_feedback()."
        return "Review unresolved issues manually before submission."

    def _build_funder_alignment(self, opp: dict[str, Any]) -> str:
        tags = ", ".join(opp.get("fit_tags", []) or []) or "small business growth"
        return (
            f"The proposal is positioned around the funder's apparent priorities: {tags}. "
            "The application connects the requested support to eligible business-building activity, practical delivery capacity, local economic participation, and measurable outcomes."
        )

    def _build_implementation_plan(self, opp: dict[str, Any]) -> str:
        deadline = opp.get("deadline_text") or "the award period"
        return (
            f"Implementation will begin immediately after approval and be managed against {deadline}. "
            "The applicant will confirm allowable costs, finalize vendors or delivery partners, deploy funds to approved activities, track receipts and milestones, and prepare a closeout summary."
        )

    def _build_budget_justification(self, opp: dict[str, Any]) -> str:
        amount = opp.get("amount_text") or "the maximum allowable award"
        return (
            f"The request will be sized to {amount} and limited to documented costs that advance the funded purpose. "
            "Budget categories may include outreach, technology, implementation support, contractor capacity, training delivery, or eligible operating improvements, depending on final program rules."
        )

    def _pick_use_of_funds(self, opp: dict[str, Any]) -> str:
        text = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
        if "energy" in text or "electric" in text or "hvac" in text:
            return self.library["use_of_funds"]["technology_and_facility"]
        if "workforce" in text or "training" in text or "education" in text:
            return self.library["use_of_funds"]["workforce_and_programs"]
        if "innovation" in text or "entrepreneur" in text:
            return self.library["use_of_funds"]["innovation_and_scale"]
        return self.library["use_of_funds"]["general_growth"]

    @staticmethod
    def _extract_title(markdown: str) -> str:
        match = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
        return match.group(1).strip() if match else "Revised grant application"
