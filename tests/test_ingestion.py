from pathlib import Path

from support_agent.ingestion import clean_text, load_product_docs


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  hello\n\n world\t ") == "hello world"


def test_load_product_docs(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "sample.md").write_text("# Sample\n\nBody text", encoding="utf-8")

    docs = load_product_docs(docs_dir)

    assert len(docs) == 1
    assert docs[0].doc_id == "sample"
    assert docs[0].title == "Sample"
