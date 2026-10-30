"""Validate the frozen empirical snapshot without a network request or model."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    root=Path(__file__).resolve().parents[1]
    results=root/"results"
    manifest=json.loads((results/"manifest.json").read_text(encoding="utf8"))
    checks={}
    checks["completed_research_run"]=manifest["status"]=="complete" and manifest["mode"]=="research"
    checks["input_hashes_match"]=all(hashlib.sha256((root/path).read_bytes()).hexdigest()==sha for path,sha in manifest["inputs"].items())
    a=pd.read_csv(results/"article_scores.csv")
    pub=pd.to_datetime(a.published_local,utc=True).dt.tz_convert("Asia/Kolkata")
    cutoff=pd.to_datetime(a.listing_date).dt.tz_localize("Asia/Kolkata")
    checks["all_news_strictly_prelisting"]=bool((pub<cutoff).all())
    lower=cutoff.map(lambda t:t-pd.Timedelta(days=manifest["lookback_calendar_days"]))
    checks["all_news_within_window"]=bool((pub>=lower).all())
    probability=a[["finbert_p_positive","finbert_p_negative","finbert_p_neutral"]]
    checks["finite_valid_probabilities"]=bool(np.isfinite(probability).all().all() and probability.ge(0).all().all() and probability.le(1).all().all() and np.allclose(probability.sum(axis=1),1,atol=1e-6))
    checks["sentiment_score_matches_probabilities"]=bool(np.allclose(a.finbert_score,a.finbert_p_positive-a.finbert_p_negative))
    p=pd.read_csv(results/"analysis_panel.csv")
    checks["no_missing_price_in_frozen_cohort"]=bool(p.price_rejection.isna().all())
    checks["exact_listing_dates"]=bool(p.observed_date.eq(p.listing_date).all())
    checks["nominal_prices_verified"]=bool(p.verified.all() and p.quote_basis.eq("listing_day_nominal").all())
    checks["missing_news_remains_missing"]=bool(p.loc[p.article_count.eq(0),["finbert_score","lm_score"]].isna().all().all())
    metrics=json.loads((results/"holdout_metrics.json").read_text(encoding="utf8"))
    for m in metrics:
        pred=pd.read_csv(results/f"holdout_{m['score']}_{m['target']}.csv")
        checks[f"test_dates_{m['score']}_{m['target']}"]=bool((pd.to_datetime(pred.listing_date)>=pd.Timestamp(m['cutoff'])).all() and len(pred)==m['n_test'])
    report={"status":"passed" if all(checks.values()) else "failed","checks":checks,
            "counts":{"ipos":len(p),"ipos_with_news":int(p.article_count.gt(0).sum()),"headlines":len(a)}}
    (results/"verification.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print(json.dumps(report,indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__=="__main__":
    main()
