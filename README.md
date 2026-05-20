# Customer Support Agent with OpenAI and AzureML

End-to-end customer support agent pipeline:

- Ingest support tickets and product documentation.
- Clean ticket text with `pandas`.
- Build OpenAI embeddings and store them in a local FAISS index.
- Run a RAG support workflow for sentiment analysis, ticket categorization, and response generation.
- Serve the agent through Streamlit locally.
- Package the same agent for AzureML managed online endpoints.

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
├── app.py                         # Streamlit dashboard
├── azureml/                       # AzureML endpoint assets
├── data/
│   ├── product_docs/              # Knowledge base markdown files
│   └── support_tickets.csv        # Sample support tickets
├── scripts/
│   └── build_index.py             # Builds the FAISS knowledge index
├── src/support_agent/             # Agent package
├── tests/                         # Lightweight unit tests
├── .env.example                   # Required environment variables
└── requirements.txt
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
- `OPENAI_API_KEY` stored as an endpoint/deployment environment variable or AzureML secret

Install the AzureML CLI extension:

```powershell
az extension add -n ml
az login
az account set --subscription "<subscription-id>"
az configure --defaults group="<resource-group>" workspace="<workspace-name>"
```

Build the local FAISS index before packaging:

```powershell
python scripts/build_index.py
```

Create endpoint and deployment:

```powershell
az ml online-endpoint create -f azureml/endpoint.yml
az ml online-deployment create -f azureml/deployment.yml --all-traffic
```

Score a request:

```powershell
az ml online-endpoint invoke `
  --name support-agent-endpoint `
  --request-file azureml/sample_request.json
```

## Notes

- The AzureML scoring script expects the FAISS index under `artifacts/faiss_index`.
- Keep product documentation current; RAG quality depends on the knowledge base.
- For production, put secrets in Azure Key Vault or AzureML-managed environment variables, not source control.
