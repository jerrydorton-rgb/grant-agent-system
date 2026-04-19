from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Template

from utils.io import slugify


APPLICATION_TEMPLATE = Template(
    """# {{ title }}\n\n"
    "## Internal opportunity summary\n"
    "- Source: {{ source_name }}\n"
    "- URL: {{ source_url }}\n"
    "- Program type: {{ program_type }}\n"
    "- Amount text: {{ amount_text or 'Not captured' }}\n"
    "- Deadline text: {{ deadline_text or 'Not captured' }}\n"
    "- Qualification status: {{ qualification_status }}\n"
    "- Score: {{ score }}\n\n"
    "## Draft narrative\n"
    "### Organization overview\n{{ company_overview }}\n\n"
    "### Need / opportunity\n{{ need_statement }}\n\n"
    "### Proposed use of funds\n{{ use_of_funds }}\n\n"
    "### Sacramento impact\n{{ sacramento_impact }}\n\n"
    "### Outcomes\n{{ outcomes }}\n\n"
    "### Compliance note\n{{ compliance_note }}\n\n"
    "## Extracted source text\n"
    "{{ extracted_text }}\n"
    """
)


class ApplicationAgent:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        library_path = Path(__file__).resolve().parents[1] / "data" / "content_library.json"
        self.library = json.loads(library_path.read_text())

    def generate(self, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        queue: list[dict[str, Any]] = []
        for opp in opportunities:
            record = {
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
                "sacramento_impact": self.library["sacramento_impact"],
                "outcomes": self.library["outcomes"],
                "compliance_note": self.library["compliance_note"],
                "extracted_text": (opp.get("description") or "")[:4000],
            }
            filename = f"{slugify(record['title'])}.md"
            out_path = self.output_dir / filename
            out_path.write_text(APPLICATION_TEMPLATE.render(**record))
            queue.append(
                {
                    "title": record["title"],
                    "source_name": record["source_name"],
                    "source_url": record["source_url"],
                    "program_type": record["program_type"],
                    "qualification_status": record["qualification_status"],
                    "score": record["score"],
                    "draft_file": str(out_path),
                    "next_action": "Review, attach supporting documents, and submit if eligible.",
                }
            )
        return queue

    def _pick_use_of_funds(self, opp: dict[str, Any]) -> str:
        text = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
        if "energy" in text or "electric" in text or "hvac" in text:
            return self.library["use_of_funds"]["technology_and_facility"]
        if "workforce" in text or "training" in text or "education" in text:
            return self.library["use_of_funds"]["workforce_and_programs"]
        if "innovation" in text or "entrepreneur" in text:
            return self.library["use_of_funds"]["innovation_and_scale"]
        return self.library["use_of_funds"]["general_growth"]
