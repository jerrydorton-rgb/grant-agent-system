# Grant Agent System

A structured grant production system designed to support a target of $50,000/month in grants without paid databases or subscriptions.

## What it does

- Pulls opportunities from free public sources
- Filters out clearly ineligible opportunities
- Scores opportunities for speed, fit, and expected yield
- Generates draft narratives from a modular content library
- Produces a review queue and application artifacts
- Tracks follow-up dates and pipeline status in CSV files

## Important constraints

This system is intentionally conservative:

- It does **not** claim the business is eligible when source language is unclear.
- It treats many public programs as **incentives or assistance opportunities**, not cash grants, unless the source explicitly says grant.
- It routes ambiguous or higher-risk opportunities to human review.
- It avoids paid data vendors and subscription databases.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py --sample
```

To run against live web pages, add your API key to `.env` and disable `--sample`.

## Environment variables

- `OPENAI_API_KEY` (optional, only for enhanced drafting)
- `MODEL_NAME` (optional, default `gpt-4.1-mini` in sample config)

## Outputs

Generated files are written to `outputs/`:

- `raw_opportunities.json`
- `qualified_opportunities.json`
- `application_queue.csv`
- `generated_applications/*.md`
- `followup_queue.csv`

## Sacramento profile

The default source registry includes:

- Grants.gov
- CalOSBA funding pages
- City of Sacramento grants portal
- City of Sacramento innovation grants
- City of Sacramento microgrant guidelines
- SMUD business rebates and energy incentives
- SMUD SEED small business incentive/vendor program

## Deployment notes

For unattended operation, schedule `python main.py` daily with cron, Task Scheduler, GitHub Actions, or a lightweight VM.

## Compliance notes

This is an application support and pipeline system. It is not legal advice, tax advice, or a guarantee of grant eligibility or award.
