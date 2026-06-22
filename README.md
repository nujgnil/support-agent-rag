# Customer Support Agent with FAISS, Streamlit, OpenAI Optional, and AzureML

End-to-end customer support agent pipeline for real support-style complaint data.

The project can run in two modes:

- **Free offline mode**: no OpenAI API key required, no paid API calls.
- **OpenAI mode**: uses OpenAI embeddings and a chat model for higher-quality RAG responses.

By default, the project uses **free offline mode**.

## What This Project Does

- Loads real public complaint records from the CFPB Consumer Complaint Database sample.
- Converts complaint records into a support-ticket format.
- Loads financial-support knowledge-base documents.
- Builds a FAISS vector index for document retrieval.
- Runs a support agent that performs:
  - sentiment detection
  - complaint category classification
  - relevant policy/document retrieval
  - suggested customer support response generation
- Provides a Streamlit UI for local testing.
- Includes AzureML managed online endpoint files for deployment.

## Architecture

```text
Real CFPB complaint data
        |
        v
support_tickets.csv
        |
        v
financial support knowledge docs
        |
        v
FAISS vector index
        |
        v
Support Agent
  - retrieve relevant docs
  - classify category
  - detect sentiment
  - generate response
        |
        +--> Streamlit local app
        +--> AzureML managed endpoint
```

## Project Layout

```text
.
+-- app.py                         # Streamlit dashboard
+-- azureml/                       # AzureML deployment files
|   +-- deployment.yml
|   +-- endpoint.yml
|   +-- environment.yml
|   +-- sample_request.json
|   +-- score.py
+-- data/
|   +-- cfpb_sample_1000.csv        # Raw public CFPB sample data
|   +-- support_tickets.csv         # Converted real support-style tickets
|   +-- product_docs/               # Financial-support knowledge base
+-- docs/
|   +-- data_sources.md             # Dataset source and mapping notes
+-- scripts/
|   +-- build_index.py              # Builds FAISS index
|   +-- fetch_cfpb_complaints.py    # Fetches/converts CFPB complaint data
+-- src/support_agent/
|   +-- agent.py                    # OpenAI-based support agent
|   +-- offline_agent.py            # Free offline support agent
|   +-- embeddings.py
|   +-- ingestion.py
|   +-- vector_store.py
|   +-- config.py
+-- tests/
+-- .env.example
+-- requirements.txt
```

## Cost Summary

### Free

These parts can run without paying:

- Local Python code
- Streamlit app
- FAISS vector search
- Real CFPB complaint CSV
- Offline hashing embeddings
- Rule-based sentiment/category/response generation

### Paid / Optional

These parts may cost money:

- OpenAI API calls, only if `USE_OPENAI=true`
- AzureML managed online endpoint compute, if deployed to Azure

For lowest cost, run locally in offline mode and do not deploy AzureML until the demo works.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Default `.env`:

```text
USE_OPENAI=false
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
FAISS_INDEX_DIR=artifacts/faiss_index
PRODUCT_DOCS_DIR=data/product_docs
SUPPORT_TICKETS_PATH=data/support_tickets.csv
```

With `USE_OPENAI=false`, you do **not** need an OpenAI API key.

## Data

The app reads this converted ticket file:

```text
data/support_tickets.csv
```

This file is created from real public CFPB complaint records. The raw sample file is:

```text
data/cfpb_sample_1000.csv
```

Dataset notes are documented in:

```text
docs/data_sources.md
```

## Rebuild the Real Ticket CSV

If `data/support_tickets.csv` already exists, you can skip this section.

If direct Python download works:

```powershell
python scripts/fetch_cfpb_complaints.py --limit 500
```

If Python download is blocked, download the public CSV first:

```powershell
Invoke-WebRequest `
  -Uri "https://huggingface.co/datasets/claritystorm/cfpb-consumer-complaints/resolve/main/sample_1000.csv" `
  -OutFile "data/cfpb_sample_1000.csv"
```

Then convert it:

```powershell
python scripts/fetch_cfpb_complaints.py `
  --input-csv data/cfpb_sample_1000.csv `
  --limit 500
```

The public sample contains fewer records with usable narrative text than the raw row count. In the current project, it produces 271 real complaint tickets.

## Build the Knowledge Index

Build the FAISS index:

```powershell
python scripts/build_index.py
```

With `USE_OPENAI=false`, this uses local hashing embeddings and costs nothing.

It creates:

```text
artifacts/faiss_index/index.faiss
artifacts/faiss_index/documents.json
```

The index is built from:

```text
data/product_docs/
```

## Run Locally

Start the Streamlit app:

```powershell
streamlit run app.py
```

Or, if using the virtual environment executable directly:

```powershell
.venv\Scripts\streamlit.exe run app.py
```

Open:

```text
http://localhost:8501
```

In the UI:

1. Select a real CFPB complaint ticket from the dropdown.
2. Review or edit the ticket text.
3. Click **Analyze ticket**.
4. The app returns sentiment, category, suggested response, and retrieved sources.

## Optional: Run with OpenAI

Only use this if you are willing to pay for API usage.

Edit `.env`:

```text
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Rebuild the FAISS index using OpenAI embeddings:

```powershell
python scripts/build_index.py
```

Run the app:

```powershell
streamlit run app.py
```

In OpenAI mode:

- `scripts/build_index.py` calls the OpenAI embeddings API.
- Each ticket analysis calls OpenAI for query embedding and response generation.

## Run Tests

```powershell
pytest
```

The tests validate local data loading and FAISS retrieval helpers.

## AzureML Deployment

AzureML deployment is optional and can cost money because managed online endpoints run on Azure compute.

Deploy only after the local Streamlit app works.

### Prerequisites

- Azure subscription
- Azure CLI
- Azure ML CLI extension
- AzureML workspace
- Built FAISS index in `artifacts/faiss_index`

Install AzureML CLI extension:

```powershell
az extension add -n ml
```

Sign in:

```powershell
az login
```

Select subscription and workspace defaults:

```powershell
az account set --subscription "<subscription-id>"
az configure --defaults group="<resource-group>" workspace="<workspace-name>"
```

### 1. Build the FAISS Index

For free offline deployment:

```powershell
$env:USE_OPENAI="false"
python scripts/build_index.py
```

Confirm these files exist:

```text
artifacts/faiss_index/index.faiss
artifacts/faiss_index/documents.json
```

### 2. Create the AzureML Endpoint

```powershell
az ml online-endpoint create -f azureml/endpoint.yml
```

This creates the public managed endpoint name:

```text
support-agent-endpoint
```

### 3. Create the Deployment

For free offline mode:

```powershell
az ml online-deployment create -f azureml/deployment.yml --all-traffic `
  --set environment_variables.USE_OPENAI=false
```

The deployment uses:

```yaml
instance_type: Standard_DS3_v2
instance_count: 1
```

This compute can incur Azure charges while running.

### 4. Optional AzureML Deployment with OpenAI

Only use this if you want the paid OpenAI version.

```powershell
$env:OPENAI_API_KEY="<your-openai-api-key>"

az ml online-deployment create -f azureml/deployment.yml --all-traffic `
  --set environment_variables.USE_OPENAI=true `
  --set environment_variables.OPENAI_API_KEY=$env:OPENAI_API_KEY
```

### 5. Test the Endpoint

Invoke the deployed endpoint:

```powershell
az ml online-endpoint invoke `
  --name support-agent-endpoint `
  --request-file azureml/sample_request.json
```

Request format:

```json
{
  "ticket_text": "My credit report shows a late payment that does not belong to me."
}
```

Response format:

```json
{
  "sentiment": "negative",
  "category": "credit_reporting",
  "response": "Suggested support response...",
  "sources": ["Credit Reporting Complaints", "Complaint Response Policy"]
}
```

### 6. Get Endpoint Credentials

```powershell
az ml online-endpoint get-credentials --name support-agent-endpoint
```

Use these credentials only if another app needs to call the AzureML endpoint directly.

### 7. Delete the Endpoint to Stop Charges

When finished:

```powershell
az ml online-endpoint delete --name support-agent-endpoint --yes
```

This is important because AzureML online endpoints can keep charging while active.

## How the System Works

### Offline Mode

1. `data/support_tickets.csv` provides real complaint text.
2. `data/product_docs/` provides financial-support knowledge documents.
3. `scripts/build_index.py` uses `HashingEmbedder` to create local vectors.
4. FAISS stores the local document index.
5. `OfflineSupportAgent` retrieves relevant docs.
6. The agent classifies category and sentiment using deterministic rules.
7. The agent generates a templated support response.

This path is free and does not call OpenAI.

### OpenAI Mode

1. `scripts/build_index.py` embeds product docs using OpenAI embeddings.
2. FAISS stores the OpenAI vectors.
3. At query time, the ticket text is embedded with OpenAI.
4. FAISS retrieves relevant product docs.
5. The OpenAI model generates sentiment, category, and response.

This path uses paid OpenAI API calls.

### AzureML Mode

1. AzureML packages `artifacts/faiss_index` as a model asset.
2. `azureml/score.py` loads the FAISS index when the endpoint starts.
3. A request sends `ticket_text`.
4. The scoring script runs either:
   - `OfflineSupportAgent` when `USE_OPENAI=false`
   - `SupportAgent` when `USE_OPENAI=true`
5. The endpoint returns sentiment, category, response, and retrieved sources.

## Production Notes

- Replace `data/product_docs/` with real company help-center articles, support policies, SOPs, or internal macros for production use.
- Do not commit real customer private data.
- Do not commit API keys.
- Use Azure Key Vault or AzureML-managed secrets for production credentials.
- Monitor AzureML endpoint costs and delete unused endpoints.
- Offline mode is good for portfolio/demo use, but OpenAI mode produces higher-quality natural language responses.
