from __future__ import annotations

from utils.models import SourceDefinition


SOURCE_REGISTRY = [
    SourceDefinition(
        name="Grants.gov",
        url="https://www.grants.gov/",
        program_type="grant",
        location_focus="National",
        parser="generic",
        requires_human_review=True,
        tags=["federal", "small business", "grant"],
    ),
    SourceDefinition(
        name="CalOSBA Funding Opportunities",
        url="https://calosba.ca.gov/for-small-businesses-and-non-profits/funding-opportunities-for-small-businesses-and-nonprofits/",
        program_type="grant",
        location_focus="California",
        parser="generic",
        requires_human_review=False,
        tags=["california", "small business", "grant"],
    ),
    SourceDefinition(
        name="City of Sacramento Innovation Grants",
        url="https://www.cityofsacramento.gov/city-manager/oied/business/innovation-and-entrepreneurship/innovation-grants.html",
        program_type="grant",
        location_focus="Sacramento",
        parser="generic",
        requires_human_review=False,
        tags=["sacramento", "innovation", "grant"],
    ),
    SourceDefinition(
        name="City of Sacramento Grant Opportunity List",
        url="https://grants.cityofsacramento.gov/grants/s/grant-opportunity/Grant_Opportunity__c/00B1U00000EP9oOUAT",
        program_type="grant",
        location_focus="Sacramento",
        parser="generic",
        requires_human_review=False,
        tags=["sacramento", "microgrant", "grant"],
    ),
    SourceDefinition(
        name="SMUD Business Rebates",
        url="https://www.smud.org/Business-Solutions-and-Rebates/Business-Rebates",
        program_type="incentive",
        location_focus="Sacramento",
        parser="generic",
        requires_human_review=True,
        tags=["sacramento", "energy", "rebate"],
    ),
    SourceDefinition(
        name="SMUD SEED Small Business Incentive Program",
        url="https://www.smud.org/Corporate/Do-Business-with-SMUD/Small-Business-Incentive-Program",
        program_type="assistance",
        location_focus="Sacramento",
        parser="generic",
        requires_human_review=True,
        tags=["sacramento", "vendor", "small business"],
    ),
]
