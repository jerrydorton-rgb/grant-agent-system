from __future__ import annotations

import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from utils.models import Opportunity, SourceDefinition

USER_AGENT = "Mozilla/5.0 (compatible; GrantAgent/1.0; +https://example.local)"


def fetch_source(source: SourceDefinition) -> list[Opportunity]:
    resp = requests.get(source.url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "lxml")
    title = _first_nonempty([
        soup.title.string if soup.title else "",
        _text_of_first(soup, ["h1", "h2"]),
        source.name,
    ])
    body_text = _clean_text(soup.get_text(" ", strip=True))
    description = body_text[:8000]
    eligibility_text = _extract_window(body_text, ["eligibility", "small business", "for-profit", "applicant", "must"], 1000)
    amount_text = _extract_money(body_text)
    deadline_text = _extract_deadline(body_text)

    return [
        Opportunity(
            source_name=source.name,
            source_url=source.url,
            title=title,
            program_type=source.program_type,
            eligibility_text=eligibility_text,
            amount_text=amount_text,
            deadline_text=deadline_text,
            description=description,
            location_focus=source.location_focus,
            requires_human_review=source.requires_human_review,
            fit_tags=source.tags,
        )
    ]


def _text_of_first(soup: BeautifulSoup, tags: list[str]) -> str:
    for tag in tags:
        node = soup.find(tag)
        if node and node.get_text(strip=True):
            return node.get_text(strip=True)
    return ""


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_window(text: str, keywords: list[str], window: int = 600) -> str:
    lower = text.lower()
    for keyword in keywords:
        idx = lower.find(keyword.lower())
        if idx != -1:
            return text[idx : idx + window]
    return text[:window]


def _extract_money(text: str) -> str:
    matches = re.findall(r"\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|k|m))?", text, flags=re.I)
    return "; ".join(matches[:10])


def _extract_deadline(text: str) -> str:
    patterns = [
        r"(?:deadline|due|applications due)[:\s]+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        r"(?:deadline|due|applications due)[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1)
    return ""


def _first_nonempty(values: list[str]) -> str:
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return "Untitled opportunity"
