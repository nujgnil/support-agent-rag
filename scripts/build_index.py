from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from support_agent.config import load_settings
from support_agent.embeddings import HashingEmbedder, OpenAIEmbedder
from support_agent.ingestion import load_product_docs
from support_agent.vector_store import FaissVectorStore


def main() -> None:
    settings = load_settings()
    docs = load_product_docs(settings.product_docs_dir)
    if settings.use_openai:
        if not settings.openai_api_key:
            raise SystemExit("OPENAI_API_KEY is required when USE_OPENAI=true.")
        embedder = OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )
        mode = f"OpenAI embeddings ({settings.openai_embedding_model})"
    else:
        embedder = HashingEmbedder()
        mode = "offline hashing embeddings"

    store = FaissVectorStore.build(docs, embedder)
    store.save(settings.faiss_index_dir)
    print(f"Indexed {len(docs)} documents into {settings.faiss_index_dir} using {mode}")


if __name__ == "__main__":
    main()
