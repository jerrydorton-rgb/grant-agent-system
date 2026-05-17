from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceDefinition:
    name: str
    url: str
    program_type: str
    location_focus: str
    parser: str = "generic"
    requires_human_review: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class Opportunity:
    source_name: str
    source_url: str
    title: str
    program_type: str
    eligibility_text: str
    amount_text: str
    deadline_text: str
    description: str
    location_focus: str
    requires_human_review: bool = False
    fit_tags: list[str] = field(default_factory=list)
