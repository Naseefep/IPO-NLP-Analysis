"""Download candidate OHLC; verify nominal prices independently before research.

Historical vendor OHLC can reflect splits even with auto_adjust=False. Never
automatically mark these rows verified. Use exchange records to verify each row.
"""
import argparse
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from iposent.data import validate_ipos


def main():
    import yfinance as yf
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ipos", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    out = Path(args.output)
    if out.exists():
        p.error("Output already exists")
    rows = []
    for row in validate_ipos(pd.read_csv(args.ipos)).itertuples():
        ticker = getattr(row, "yahoo_symbol", row.symbol + ".NS")
        item = dict(symbol=row.symbol, observed_date="", open=None, high=None, low=None, close=None,
                    quote_basis="vendor_unverified", verified=False, source_url=f"https://finance.yahoo.com/quote/{ticker}/history/", status="no_exact_date")
        try:
            data = yf.Ticker(ticker).history(start=row.listing_date.strftime("%Y-%m-%d"),
                   end=(row.listing_date+pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                   interval="1d", auto_adjust=False, back_adjust=False)
            exact = data[[t.date() == row.listing_date.date() for t in data.index]]
            if len(exact) == 1:
                item.update(observed_date=str(row.listing_date.date()), status="candidate_requires_verification",
                            **{c.lower(): float(exact.iloc[0][c]) for c in ["Open", "High", "Low", "Close"]})
        except Exception as exc:
            item["status"] = f"download_error: {exc}"
        rows.append(item)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print("Saved price candidates. Verify against dated exchange records before analysis.")


if __name__ == "__main__":
    main()
