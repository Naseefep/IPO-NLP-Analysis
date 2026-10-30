"""Best-effort historical Google News RSS candidates, NEVER a complete archive.

python scripts/collect_news.py --ipos data/ipo_master.csv --output data/raw/news_candidates.csv
Review candidates and set relevance_verified=true only after checking the linked
article and publication time. The research pipeline enforces the window again.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as ET
import pandas as pd
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iposent.data import validate_ipos


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ipos", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--lookback-days", type=int, default=30)
    args = p.parse_args()
    if args.lookback_days < 1:
        p.error("lookback-days must be positive")
    out = Path(args.output)
    if out.exists():
        p.error("Output exists; choose a new filename to preserve the previous collection")
    rows, log = [], []
    ipos = validate_ipos(pd.read_csv(args.ipos))
    session = requests.Session()
    session.headers["User-Agent"] = "IPO-Sentiment-Research/1.0 (academic research)"
    raw_dir = out.parent / (out.stem + "_rss")
    raw_dir.mkdir(parents=True, exist_ok=True)
    for row in ipos.itertuples():
        start = (row.listing_date - pd.Timedelta(days=args.lookback_days)).date()
        end = row.listing_date.date()
        query = f'"{row.company}" IPO after:{start} before:{end}'
        try:
            response = session.get("https://news.google.com/rss/search", params={"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}, timeout=30)
            response.raise_for_status()
            # Never use an input symbol directly as a filename.
            import hashlib
            key = hashlib.sha256(row.symbol.encode()).hexdigest()[:16]
            (raw_dir / f"{key}.xml").write_bytes(response.content)
            items = ET.fromstring(response.content).findall(".//item")
            for item in items:
                rows.append(dict(symbol=row.symbol, headline=item.findtext("title", ""), published_at=item.findtext("pubDate", ""),
                                 source=item.findtext("source", "Google News RSS"), url=item.findtext("link", ""),
                                 relevance_verified=False, retrieved_utc=datetime.now(timezone.utc).isoformat()))
            log.append(dict(symbol=row.symbol, count=len(items), status="ok", query=query))
        except (requests.RequestException, ET.ParseError) as exc:
            log.append(dict(symbol=row.symbol, count=0, status=str(exc), query=query))
        time.sleep(1)
    pd.DataFrame(rows, columns=["symbol", "headline", "published_at", "source", "url", "relevance_verified", "retrieved_utc"]).to_csv(out, index=False)
    pd.DataFrame(log).to_csv(out.with_suffix(".collection_log.csv"), index=False)
    print(f"Saved {len(rows)} candidates. Human review is required before analysis.")


if __name__ == "__main__":
    main()
