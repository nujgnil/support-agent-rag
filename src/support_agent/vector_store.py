from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import faiss
import numpy as np

from support_agent.ingestion import Document


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray:
        ...


def normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1e-12)


class FaissVectorStore:
    def __init__(self, index: faiss.Index, documents: list[Document]) -> None:
        self.index = index
        self.documents = documents

    @classmethod
    def build(cls, documents: list[Document], embedder: Embedder) -> "FaissVectorStore":
        if not documents:
            raise ValueError("Cannot build a vector store without documents.")

        vectors = normalize(embedder.embed([doc.text for doc in documents]))
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index=index, documents=documents)

    @classmethod
    def load(cls, directory: Path) -> "FaissVectorStore":
        index_path = directory / "index.faiss"
        metadata_path = directory / "documents.json"
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(
                f"Missing FAISS index files in {directory}. Run scripts/build_index.py."
            )

        index = faiss.read_index(str(index_path))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        documents = [Document(**item) for item in metadata]
        return cls(index=index, documents=documents)

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "index.faiss"))
        payload = [doc.__dict__ for doc in self.documents]
        (directory / "documents.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def search(self, query: str, embedder: Embedder, k: int = 3) -> list[tuple[Document, float]]:
        query_vector = normalize(embedder.embed([query]))
        scores, indices = self.index.search(query_vector, k)
        results: list[tuple[Document, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0:
                continue
            results.append((self.documents[int(idx)], float(score)))
        return results
