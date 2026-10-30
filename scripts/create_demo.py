"""Generate fictional fixtures to test software. No empirical research data."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd


def create(output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    ipos, prices, news = [], [], []
    positive = ["growth", "profit", "strong", "gain", "improved"]
    negative = ["loss", "weak", "decline", "risk", "uncertain"]
    for i in range(48):
        symbol = f"DEMO{i:03d}"
        day = pd.Timestamp("2020-02-10") + pd.Timedelta(days=35*i)
        issue = float(rng.uniform(80, 1200))
        op = issue * rng.uniform(.8, 1.8)
        close = op * rng.uniform(.88, 1.12)
        ipos.append(dict(symbol=symbol, company=f"Fictional Company {i}", listing_date=str(day.date()), issue_price=issue))
        prices.append(dict(symbol=symbol, observed_date=str(day.date()), open=op, high=max(op,close)*rng.uniform(1.01,1.1),
                           low=min(op,close)*rng.uniform(.9,.99), close=close, quote_basis="listing_day_nominal", verified=True,
                           source_url=f"https://example.invalid/synthetic/{symbol}"))
        for j in range(int(rng.integers(2,7))):
            words = rng.choice(positive+negative, size=3, replace=True)
            news.append(dict(symbol=symbol, headline=f"{symbol} IPO {j}: {' '.join(words)} outlook", published_at=str((day-pd.Timedelta(days=j+1)).date()),
                             source="Fictional news", url=f"https://example.invalid/{symbol}/{j}", relevance_verified=True))
        # Deliberate future leakage and exact duplicate exercise filtering.
        news.append({**news[-1], "published_at": str((day+pd.Timedelta(days=1)).date()), "url": f"https://example.invalid/future/{symbol}"})
        news.append(news[-2].copy())
    pd.DataFrame(ipos).to_csv(out/"ipos.csv", index=False)
    pd.DataFrame(prices).to_csv(out/"prices.csv", index=False)
    pd.DataFrame(news).to_csv(out/"news.csv", index=False)
    # This is a toy fixture, explicitly not the Loughran-McDonald dictionary.
    pd.DataFrame([dict(Word=w.upper(), Positive=int(w in positive), Negative=int(w in negative), Uncertainty=int(w=="uncertain")) for w in positive+negative]).to_csv(out/"toy_dictionary.csv", index=False)
    print(f"SYNTHETIC fixtures written to {out}")


if __name__ == "__main__":
    create(sys.argv[1] if len(sys.argv)>1 else "data/demo")
