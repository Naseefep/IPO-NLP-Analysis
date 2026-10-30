"""Exploratory robustness checks using frozen article scores, without rescoring.

Run after the primary pipeline: python scripts/sensitivity.py
No holdout outcomes are used to choose these specifications.
"""
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from iposent.sentiment import aggregate
from iposent.analysis import estimate


if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    out=root/"results"
    articles=pd.read_csv(out/"article_scores.csv")
    base=pd.read_csv(out/"price_audit.csv")
    base["listing_date"]=pd.to_datetime(base.listing_date)
    published=pd.to_datetime(articles.published_local,utc=True).dt.tz_convert("Asia/Kolkata")
    cutoff=pd.to_datetime(articles.listing_date).dt.tz_localize("Asia/Kolkata")
    sets={"14_calendar_days":articles[published>=cutoff-pd.Timedelta(days=14)],
          "exclude_gmp":articles[~articles.text.str.contains(r"\bgmp\b|grey.market|gray.market",case=False,regex=True,na=False)]}
    tables=[]
    for name, subset in sets.items():
        panel=base.merge(aggregate(subset),on="symbol",how="left",validate="one_to_one")
        panel.article_count=panel.article_count.fillna(0)
        c,_,_,skipped=estimate(panel)
        if not c.empty:
            c=c[c.term.eq(c.score)&c.specification.eq("controlled")].copy()
            c["sensitivity"]=name
            tables.append(c)
    if tables:
        pd.concat(tables,ignore_index=True).to_csv(out/"sensitivity.csv",index=False)
