# Customer Support Agent with OpenAI and AzureML

End-to-end customer support agent pipeline:

- Ingest support tickets and product documentation.
- Clean ticket text with `pandas`.
- Build OpenAI embeddings and store them in a local FAISS index.
- Run a RAG support workflow for sentiment analysis, ticket categorization, and response generation.
- Serve the agent through Streamlit locally.
- Package the same agent for AzureML managed online endpoints.
- Optionally fetch real public complaint records from the CFPB Consumer Complaint Database.

## Architecture

```text
support tickets + product docs
        |
        v
data processing -> OpenAI embeddings -> FAISS vector store
        |
        v
RAG agent: sentiment -> category -> grounded response
        |
        +--> Streamlit UI
        +--> AzureML endpoint
```

## Project Layout

```text
.
+-- app.py                         # Streamlit dashboard
+-- azureml/                       # AzureML endpoint assets
+-- data/
|   +-- product_docs/              # Knowledge base markdown files
|   +-- support_tickets.csv        # Sample support tickets
+-- scripts/
|   +-- build_index.py             # Builds the FAISS knowledge index
|   +-- fetch_cfpb_complaints.py   # Fetches real public support-style tickets
+-- src/support_agent/             # Agent package
+-- tests/                         # Lightweight unit tests
+-- docs/data_sources.md           # Dataset notes and field mapping
+-- .env.example                   # Required environment variables
+-- requirements.txt
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set:

```text
OPENAI_API_KEY=your_key_here
```

Optional overrides:

```text
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Use Real Support-Style Ticket Data

The repository can use real public complaint records from the CFPB Consumer Complaint Database. These are consumer financial complaints that the CFPB sends to companies for response.

Fetch 500 public complaint narratives:

```powershell
python scripts/fetch_cfpb_complaints.py --limit 500
```

This replaces `data/support_tickets.csv` with real public records mapped into the app schema.

If direct Python download is blocked, download the public sample CSV first and convert it:

```powershell
Invoke-WebRequest `
  -Uri "https://huggingface.co/datasets/claritystorm/cfpb-consumer-complaints/resolve/main/sample_1000.csv" `
  -OutFile "data/cfpb_sample_1000.csv"

python scripts/fetch_cfpb_complaints.py `
  --input-csv data/cfpb_sample_1000.csv `
  --limit 500
```

Optional product-specific example:

```powershell
python scripts/fetch_cfpb_complaints.py --limit 500 --product "Credit reporting or other personal consumer reports"
```

Dataset notes are in `docs/data_sources.md`.

## Build the Knowledge Base

```powershell
python scripts/build_index.py
```

This creates `artifacts/faiss_index/`.

## Run Locally

```powershell
streamlit run app.py
```

Use one of the sample tickets or enter a new customer issue. The app retrieves relevant product documentation, classifies the issue, detects sentiment, and drafts a support response.

## Run Tests

```powershell
pytest
```

The tests do not call OpenAI; they validate local preprocessing and retrieval helpers.

## AzureML Deployment

Prerequisites:

- Azure CLI
- Azure ML CLI extension
- An AzureML workspace
- An OpenAI API key available in your local shell as `OPENAI_API_KEY`

### 1. Sign in and select the AzureML workspace

```powershell
az extension add -n ml
az login
az account set --subscription "<subscription-id>"
az configure --defaults group="<resource-group>" workspace="<workspace-name>"
```

### 2. Build the FAISS knowledge index

The endpoint needs the vector index files generated from the product documentation.

```powershell
python scripts/build_index.py
```

Confirm these files exist:

```text
artifacts/faiss_index/index.faiss
artifacts/faiss_index/documents.json
```

### 3. Create the managed online endpoint

```powershell
az ml online-endpoint create -f azureml/endpoint.yml
```

### 4. Deploy the scoring service

Set the OpenAI key in your current PowerShell session:

```powershell
$env:OPENAI_API_KEY="<your-openai-api-key>"
```

Create the deployment and pass the key as an AzureML deployment environment variable:

```powershell
az ml online-deployment create -f azureml/deployment.yml --all-traffic
az ml online-deployment update `
  --name blue `
  --endpoint-name support-agent-endpoint `
  --set environment_variables.OPENAI_API_KEY=$env:OPENAI_API_KEY
```

### 5. Test the deployed endpoint

Invoke the endpoint with the sample request:

```powershell
az ml online-endpoint invoke `
  --name support-agent-endpoint `
  --request-file azureml/sample_request.json
```

The response should contain:

```json
{
  "sentiment": "...",
  "category": "...",
  "response": "...",
  "sources": ["..."]
}
```

### 6. Get endpoint credentials

If another application needs to call the endpoint directly, retrieve the endpoint key:

```powershell
az ml online-endpoint get-credentials --name support-agent-endpoint
```

### 7. Clean up Azure resources

Delete the endpoint when you no longer need it to avoid compute charges:

```powershell
az ml online-endpoint delete --name support-agent-endpoint --yes
```

## How the Deployment Works

1. `scripts/build_index.py` embeds the product docs with OpenAI embeddings.
2. The embeddings and document metadata are saved in `artifacts/faiss_index`.
3. `azureml/deployment.yml` packages the FAISS index as an AzureML model asset.
4. `azureml/score.py` loads the model files when the deployment starts.
5. Each request sends `ticket_text` to the endpoint.
6. The scoring service retrieves relevant docs from FAISS, calls OpenAI, and returns sentiment, category, response, and sources.

Request shape:

```json
{
  "ticket_text": "Customer issue text goes here"
}
```

Response shape:

```json
{
  "sentiment": "negative",
  "category": "billing",
  "response": "Customer-facing response...",
  "sources": ["Billing and Plan Changes"]
}
```

## Notes

- The local app and AzureML endpoint both use the same agent code in `src/support_agent`.
- The AzureML deployment needs `OPENAI_API_KEY`; do not commit it to source control.
- Keep product documentation current; RAG quality depends on the knowledge base.
- For production, put secrets in Azure Key Vault or AzureML-managed environment variables, not source control.
