# Grant Agent

Automates a grant pipeline:

1. Source opportunities
2. Qualify and score opportunities
3. Generate application drafts
4. Revise drafts until they pass an internal submission-readiness gate
5. Build follow-up queues

> Internal acceptance means the draft passed this tool's readiness rubric. It does not guarantee a funder will approve or award the grant.

## Run with sample data

```bash
python main.py --sample
```

Outputs are written to:

```text
outputs/
├── raw_opportunities.json
├── qualified_opportunities.json
├── application_queue.csv
├── followup_queue.csv
└── generated_applications/
```

## Revise a rejected or returned application

When a funder or portal gives feedback, run:

```bash
python main.py revise --draft outputs/generated_applications/example.md --feedback "Budget is unclear and outcomes need stronger metrics."
```

The agent creates a revised Markdown file beside the original draft.

## API

Start the API:

```bash
uvicorn main:app --reload
```

Health check:

```text
GET /
```

Generate applications:

```text
POST /run?sample=true
```

Revise from feedback:

```text
POST /revise
```

JSON body:

```json
{
  "draft_file": "outputs/generated_applications/example.md",
  "feedback": "Budget is unclear and outcomes need stronger metrics."
}
```
