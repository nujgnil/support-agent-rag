# Data Sources

## Real Support-Style Ticket Data

The project uses the CFPB Consumer Complaint Database as a real public support-style dataset.

Source:

- https://www.consumerfinance.gov/data-research/consumer-complaints/
- https://cfpb.github.io/api/ccdb/

The dataset contains consumer complaints about financial products and services. Public complaint narratives are only published by the CFPB when consumers consent and after CFPB scrubbing processes.

Local ingestion script:

```powershell
python scripts/fetch_cfpb_complaints.py --limit 500
```

This writes:

```text
data/support_tickets.csv
```

The project maps CFPB fields into the app's support-ticket schema:

```text
ticket_id     <- CFPB complaint ID
subject       <- product + issue + sub-issue
description   <- public complaint narrative
priority      <- derived from tags/company response
created_at    <- date received
```

## Knowledge Base Data

The files in `data/product_docs/` are financial-support knowledge articles aligned with the CFPB complaint categories. They are not private company documents; they are project knowledge-base content created to make retrieval relevant for the real complaint data.

For a portfolio project, the CFPB complaints provide real customer issue text. For a production support agent, both ticket history and product documentation should come from the actual organization.
