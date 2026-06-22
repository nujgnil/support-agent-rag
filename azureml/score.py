from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from support_agent.agent import SupportAgent
from support_agent.config import Settings, load_settings
from support_agent.offline_agent import OfflineSupportAgent

agent: SupportAgent | OfflineSupportAgent | None = None


def init() -> None:
    global agent
    settings = load_settings()
    model_dir = os.getenv("AZUREML_MODEL_DIR")
    if model_dir:
        mounted_model = Path(model_dir)
        candidate = (
            mounted_model / "faiss_index"
            if (mounted_model / "faiss_index").exists()
            else mounted_model
        )
        if candidate.exists():
            settings = Settings(
                use_openai=settings.use_openai,
                openai_api_key=settings.openai_api_key,
                openai_model=settings.openai_model,
                openai_embedding_model=settings.openai_embedding_model,
                faiss_index_dir=candidate,
                product_docs_dir=settings.product_docs_dir,
                support_tickets_path=settings.support_tickets_path,
            )
    if settings.use_openai:
        agent = SupportAgent(settings)
    else:
        agent = OfflineSupportAgent(settings.faiss_index_dir)


def run(raw_data: str) -> str:
    if agent is None:
        raise RuntimeError("Agent has not been initialized.")

    payload = json.loads(raw_data)
    ticket_text = payload.get("ticket_text")
    if not ticket_text:
        return json.dumps({"error": "ticket_text is required"})

    result = agent.analyze(ticket_text)
    return json.dumps(
        {
            "sentiment": result.sentiment,
            "category": result.category,
            "response": result.response,
            "sources": result.sources,
        }
    )
