from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str


def clean_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text


def load_support_tickets(path: Path) -> pd.DataFrame:
    tickets = pd.read_csv(path)
    required = {"ticket_id", "subject", "description", "priority"}
    missing = required.difference(tickets.columns)
    if missing:
        raise ValueError(f"Missing required ticket columns: {sorted(missing)}")

    tickets = tickets.copy()
    tickets["subject"] = tickets["subject"].map(clean_text)
    tickets["description"] = tickets["description"].map(clean_text)
    tickets["combined_text"] = tickets["subject"] + ". " + tickets["description"]
    return tickets


def load_product_docs(directory: Path) -> list[Document]:
    if not directory.exists():
        raise FileNotFoundError(f"Product docs directory not found: {directory}")

    documents: list[Document] = []
    for path in sorted(directory.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        title = lines[0].lstrip("# ").strip() if lines else path.stem
        text = clean_text(raw)
        documents.append(
            Document(doc_id=path.stem, title=title, text=text, source=str(path))
        )
    return documents
