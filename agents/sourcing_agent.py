from __future__ import annotations

from dataclasses import asdict
from typing import Any

from utils.models import Opportunity, SourceDefinition
from utils.sources import SOURCE_REGISTRY
from utils.web_fetch import fetch_source


class SourcingAgent:
    def __init__(self) -> None:
        self.sources: list[SourceDefinition] = SOURCE_REGISTRY

    def collect(self) -> list[dict[str, Any]]:
        opportunities: list[dict[str, Any]] = []
        for source in self.sources:
            try:
                records = fetch_source(source)
                for record in records:
                    if isinstance(record, Opportunity):
                        opportunities.append(asdict(record))
                    else:
                        opportunities.append(record)
            except Exception as exc:  # pragma: no cover
                opportunities.append(
                    {
                        "source_name": source.name,
                        "source_url": source.url,
                        "title": f"Fetch error for {source.name}",
                        "program_type": "error",
                        "eligibility_text": "",
                        "amount_text": "",
                        "deadline_text": "",
                        "description": str(exc),
                        "location_focus": source.location_focus,
                        "requires_human_review": True,
                        "fit_tags": ["error"],
                    }
                )
        return opportunities
