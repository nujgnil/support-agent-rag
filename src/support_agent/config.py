from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    use_openai: bool
    openai_api_key: str | None
    openai_model: str
    openai_embedding_model: str
    faiss_index_dir: Path
    product_docs_dir: Path
    support_tickets_path: Path


def load_settings() -> Settings:
    load_dotenv()
    use_openai = os.getenv("USE_OPENAI", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }
    return Settings(
        use_openai=use_openai,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openai_embedding_model=os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        faiss_index_dir=Path(os.getenv("FAISS_INDEX_DIR", "artifacts/faiss_index")),
        product_docs_dir=Path(os.getenv("PRODUCT_DOCS_DIR", "data/product_docs")),
        support_tickets_path=Path(
            os.getenv("SUPPORT_TICKETS_PATH", "data/support_tickets.csv")
        ),
    )
