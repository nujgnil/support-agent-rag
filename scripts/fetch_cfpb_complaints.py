from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import requests


API_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
HF_ROWS_URL = "https://datasets-server.huggingface.co/rows"
HF_DATASET = "claritystorm/cfpb-consumer-complaints"
HF_SAMPLE_CSV_URL = (
    "https://huggingface.co/datasets/claritystorm/cfpb-consumer-complaints/"
    "resolve/main/sample_1000.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch real public CFPB consumer complaint narratives."
    )
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--output", type=Path, default=Path("data/support_tickets.csv"))
    parser.add_argument("--product", default=None, help="Optional CFPB product filter.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=None,
        help="Optional local CFPB CSV file to convert instead of downloading.",
    )
    return parser.parse_args()


def fetch_page(size: int, offset: int, product: str | None) -> dict[str, Any]:
    params: dict[str, str | int] = {
        "field": "all",
        "format": "json",
        "no_aggs": "true",
        "size": size,
        "from": offset,
        "sort": "created_date_desc",
    }
    if product:
        params["product"] = product

    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "support-agent-demo/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_hf_page(size: int, offset: int) -> dict[str, Any]:
    params = {
        "dataset": HF_DATASET,
        "config": "default",
        "split": "train",
        "offset": offset,
        "length": size,
    }
    url = f"{HF_ROWS_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "support-agent-demo/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_hf_sample_csv() -> list[dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 support-agent-demo/1.0"
        ),
        "Accept": "text/csv,*/*",
    }
    response = requests.get(HF_SAMPLE_CSV_URL, headers=headers, timeout=60)
    response.raise_for_status()
    return list(csv.DictReader(response.text.splitlines()))


def fetch_hf_sample_csv_with_urllib() -> list[dict[str, Any]]:
    request = urllib.request.Request(
        HF_SAMPLE_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0 support-agent-demo/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8")
    return list(csv.DictReader(text.splitlines()))


def iter_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "rows" in payload:
        return [
            item["row"]
            for item in payload.get("rows", [])
            if isinstance(item, dict) and isinstance(item.get("row"), dict)
        ]

    hits = payload.get("hits", {}).get("hits", [])
    sources: list[dict[str, Any]] = []
    for hit in hits:
        source = hit.get("_source", hit)
        if isinstance(source, dict):
            sources.append(source)
    return sources


def derive_priority(source: dict[str, Any]) -> str:
    tags = " ".join(source.get("tags") or [])
    response = str(source.get("company_response") or "").lower()
    if "servicemember" in tags.lower() or "older american" in tags.lower():
        return "high"
    if "closed with monetary relief" in response:
        return "high"
    if "closed with explanation" in response:
        return "medium"
    return "low"


def to_ticket(source: dict[str, Any]) -> dict[str, str] | None:
    narrative = str(
        source.get("complaint_what_happened")
        or source.get("consumer_narrative")
        or ""
    ).strip()
    if not narrative:
        return None

    product = str(source.get("product") or "Unknown product").strip()
    issue = str(source.get("issue") or "Customer complaint").strip()
    sub_issue = str(source.get("sub_issue") or "").strip()
    subject = f"{product} - {issue}"
    if sub_issue:
        subject = f"{subject}: {sub_issue}"

    ticket_id = str(source.get("complaint_id") or source.get("id") or "").strip()
    if not ticket_id:
        return None

    return {
        "ticket_id": f"CFPB-{ticket_id}",
        "customer_name": "CFPB Consumer",
        "subject": subject,
        "description": narrative,
        "priority": derive_priority(source),
        "created_at": str(source.get("date_received") or source.get("created_date") or ""),
    }


def main() -> None:
    args = parse_args()
    rows: list[dict[str, str]] = []
    offset = 0
    page_size = min(100, max(args.limit, 1))

    source_name = "CFPB API"
    while len(rows) < args.limit:
        if args.input_csv:
            source_name = str(args.input_csv)
            with args.input_csv.open("r", encoding="utf-8", newline="") as file:
                sources = list(csv.DictReader(file))
            payload = {"rows": [{"row": source} for source in sources]}
        else:
            try:
                payload = fetch_page(size=page_size, offset=offset, product=args.product)
            except Exception as exc:
                if offset != 0:
                    raise
                print(f"CFPB API fetch failed ({exc}); falling back to public CSV sample.")
                source_name = f"Hugging Face dataset mirror: {HF_DATASET}"
                sources = fetch_hf_sample_csv()
                payload = {"rows": [{"row": source} for source in sources]}

        sources = iter_sources(payload)
        if not sources:
            break

        for source in sources:
            if args.product and args.product.lower() not in str(
                source.get("product", "")
            ).lower():
                continue
            ticket = to_ticket(source)
            if ticket:
                rows.append(ticket)
                if len(rows) >= args.limit:
                    break

        if args.input_csv:
            break
        offset += page_size

    if not rows:
        raise SystemExit("No complaint narratives were returned by the CFPB API.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "ticket_id",
                "customer_name",
                "subject",
                "description",
                "priority",
                "created_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real complaint records to {args.output}")
    print(f"Source: {source_name}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        print(f"Failed to fetch CFPB data: {exc}", file=sys.stderr)
        raise SystemExit(1)
