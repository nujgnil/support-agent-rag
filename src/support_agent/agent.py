from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from support_agent.config import Settings, load_settings
from support_agent.embeddings import OpenAIEmbedder
from support_agent.vector_store import FaissVectorStore


@dataclass(frozen=True)
class AgentResult:
    sentiment: str
    category: str
    response: str
    sources: list[str]


class SupportAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required.")

        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.embedder = OpenAIEmbedder(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_embedding_model,
        )
        self.store = FaissVectorStore.load(self.settings.faiss_index_dir)

    def analyze(self, ticket_text: str) -> AgentResult:
        contexts = self.store.search(ticket_text, self.embedder, k=3)
        context_text = "\n\n".join(
            f"Source: {doc.title}\n{doc.text}" for doc, _score in contexts
        )
        prompt = self._build_prompt(ticket_text=ticket_text, context_text=context_text)
        output = self._call_model(prompt)
        sections = self._parse_sections(output)
        return AgentResult(
            sentiment=sections.get("sentiment", "unknown"),
            category=sections.get("category", "general_support"),
            response=sections.get("response", output.strip()),
            sources=[doc.title for doc, _score in contexts],
        )

    def _call_model(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=prompt,
            temperature=0.2,
        )
        return response.output_text

    @staticmethod
    def _build_prompt(ticket_text: str, context_text: str) -> str:
        return f"""You are a customer support agent.

Use the product documentation context to answer the ticket. If context is missing, say what information support should verify. Be concise, empathetic, and operationally specific.

Return exactly these fields:
Sentiment: <positive|neutral|negative|urgent>
Category: <credit_reporting|debt_collection|credit_card_dispute|bank_account|money_transfer|mortgage_servicing|general_support>
Response: <customer-facing response>

Product documentation:
{context_text}

Customer ticket:
{ticket_text}
"""

    @staticmethod
    def _parse_sections(text: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        current_key: str | None = None
        chunks: list[str] = []

        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                normalized = key.strip().lower()
                if normalized in {"sentiment", "category", "response"}:
                    if current_key:
                        sections[current_key] = "\n".join(chunks).strip()
                    current_key = normalized
                    chunks = [value.strip()]
                    continue
            if current_key:
                chunks.append(line)

        if current_key:
            sections[current_key] = "\n".join(chunks).strip()
        return sections
