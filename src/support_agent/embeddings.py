from __future__ import annotations

import hashlib

import numpy as np
from openai import OpenAI


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed(self, texts: list[str]) -> np.ndarray:
        response = self.client.embeddings.create(model=self.model, input=texts)
        vectors = [item.embedding for item in response.data]
        return np.array(vectors, dtype="float32")


class HashingEmbedder:
    """Deterministic test embedder that avoids external API calls."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimensions), dtype="float32")
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % self.dimensions
                vectors[row, idx] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)
