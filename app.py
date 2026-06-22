from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from support_agent.agent import SupportAgent
from support_agent.config import load_settings
from support_agent.ingestion import load_support_tickets
from support_agent.offline_agent import OfflineSupportAgent


st.set_page_config(page_title="Customer Support Agent", page_icon=":headphones:", layout="wide")

settings = load_settings()

st.title("Customer Support Agent")

with st.sidebar:
    st.header("Pipeline")
    if settings.use_openai:
        st.caption("OpenAI embeddings -> FAISS retrieval -> RAG response")
        st.text_input("Chat model", value=settings.openai_model, disabled=True)
        st.text_input("Embedding model", value=settings.openai_embedding_model, disabled=True)
    else:
        st.caption("Offline hashing embeddings -> FAISS retrieval -> rule-based response")
        st.text_input("Mode", value="Offline / no API cost", disabled=True)

try:
    tickets = load_support_tickets(settings.support_tickets_path)
except Exception as exc:
    st.error(f"Could not load tickets: {exc}")
    st.stop()

ticket_options = {
    f"{row.ticket_id} - {row.subject}": row.combined_text
    for row in tickets.itertuples(index=False)
}

left, right = st.columns([0.38, 0.62])

with left:
    selected = st.selectbox("Sample ticket", list(ticket_options))
    default_text = ticket_options[selected]
    ticket_text = st.text_area("Ticket text", value=default_text, height=220)
    run = st.button("Analyze ticket", type="primary", use_container_width=True)

with right:
    if run:
        try:
            with st.spinner("Retrieving docs and generating response..."):
                if settings.use_openai:
                    result = SupportAgent(settings).analyze(ticket_text)
                else:
                    result = OfflineSupportAgent(settings.faiss_index_dir).analyze(ticket_text)
        except Exception as exc:
            st.error(str(exc))
            st.info("Run `python scripts/build_index.py` first. Only set OPENAI_API_KEY if USE_OPENAI=true.")
            st.stop()

        metric_cols = st.columns(2)
        metric_cols[0].metric("Sentiment", result.sentiment)
        metric_cols[1].metric("Category", result.category)
        st.subheader("Suggested Response")
        st.write(result.response)
        st.subheader("Retrieved Sources")
        st.write(", ".join(result.sources))
    else:
        st.info("Select or edit a ticket, then run the agent.")
