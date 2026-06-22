from __future__ import annotations

from support_agent.agent import AgentResult
from support_agent.embeddings import HashingEmbedder
from support_agent.vector_store import FaissVectorStore


class OfflineSupportAgent:
    """No-cost local agent for demos without OpenAI API calls."""

    def __init__(self, faiss_index_dir) -> None:
        self.embedder = HashingEmbedder()
        self.store = FaissVectorStore.load(faiss_index_dir)

    def analyze(self, ticket_text: str) -> AgentResult:
        contexts = self.store.search(ticket_text, self.embedder, k=3)
        category = classify_category(ticket_text)
        sentiment = classify_sentiment(ticket_text)
        sources = [doc.title for doc, _score in contexts]
        return AgentResult(
            sentiment=sentiment,
            category=category,
            response=build_response(category, sources),
            sources=sources,
        )


def classify_category(text: str) -> str:
    lowered = text.lower()
    rules = [
        ("credit_reporting", ["credit report", "credit bureau", "tradeline", "late payment", "fico"]),
        ("debt_collection", ["debt", "collector", "collection", "owe", "validation"]),
        ("credit_card_dispute", ["credit card", "card", "charge", "merchant", "transaction"]),
        ("bank_account", ["bank account", "checking", "deposit", "overdraft", "atm"]),
        ("money_transfer", ["transfer", "wire", "payment app", "wallet", "zelle"]),
        ("mortgage_servicing", ["mortgage", "escrow", "foreclosure", "loan modification"]),
    ]
    for category, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return category
    return "general_support"


def classify_sentiment(text: str) -> str:
    lowered = text.lower()
    urgent_terms = ["urgent", "foreclosure", "fraud", "identity theft", "stolen", "legal action"]
    negative_terms = ["wrong", "incorrect", "not fixed", "refused", "failed", "cannot", "harass"]
    if any(term in lowered for term in urgent_terms):
        return "urgent"
    if any(term in lowered for term in negative_terms):
        return "negative"
    return "neutral"


def build_response(category: str, sources: list[str]) -> str:
    source_text = ", ".join(sources) if sources else "the available support policy"
    next_steps = {
        "credit_reporting": "Please share the disputed account name, bureau, account number if available, and the exact correction you are requesting.",
        "debt_collection": "Please provide the collector name, account reference, contact dates, and any validation notice you received.",
        "credit_card_dispute": "Please provide the transaction date, merchant name, amount, dispute reason, and any supporting documents.",
        "bank_account": "Please share the account type, transaction dates, amounts, and any prior case or dispute number.",
        "money_transfer": "Please provide the transfer ID, date, amount, sender and recipient details, and whether fraud is suspected.",
        "mortgage_servicing": "Please share the loan number, payment dates, escrow details, and any foreclosure or loss-mitigation deadlines.",
        "general_support": "Please provide any account reference, dates, amounts, prior case numbers, and documents related to the issue.",
    }
    return (
        "Thank you for explaining the issue. I understand this is frustrating and will help route it for review. "
        f"Based on {source_text}, this appears to be a {category.replace('_', ' ')} case. "
        f"{next_steps.get(category, next_steps['general_support'])} "
        "Once those details are available, the support team can review the timeline, check prior investigations, and respond with the next action."
    )
