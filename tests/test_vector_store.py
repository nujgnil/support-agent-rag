from support_agent.embeddings import HashingEmbedder
from support_agent.ingestion import Document
from support_agent.vector_store import FaissVectorStore


def test_vector_store_search_returns_relevant_doc() -> None:
    docs = [
        Document("billing", "Billing", "invoice plan billing charge", "billing.md"),
        Document("sso", "SSO", "saml identity provider metadata", "sso.md"),
    ]
    embedder = HashingEmbedder()
    store = FaissVectorStore.build(docs, embedder)

    results = store.search("invoice charge mismatch", embedder, k=1)

    assert results[0][0].doc_id == "billing"
