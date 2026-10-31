"""Association estimates and a separate, date-held-out prediction exercise."""
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

TARGETS = ["listing_return_pct", "parkinson_daily"]


def estimate(panel):
    scores = [c for c in ["finbert_score", "lm_score"] if c in panel]
    records, correlations, diagnostics, skipped = [], [], [], []
    for score in scores:
        for target in TARGETS:
            cols = [target, score, "issue_price", "article_count", "listing_date"]
            d = panel[cols + ["symbol"]].dropna().copy()
            if len(d) < 12 or d[score].nunique() < 2 or d[target].nunique() < 2:
                skipped.append({"score": score, "target": target, "reason": "insufficient observations or variation", "n": len(d)})
                continue
            pr, pp = pearsonr(d[score], d[target])
            sr, sp = spearmanr(d[score], d[target])
            correlations.append(dict(score=score, target=target, n=len(d), pearson_r=pr, pearson_p=pp, spearman_r=sr, spearman_p=sp))
            for specification in ["simple", "controlled"]:
                x = pd.DataFrame({score: d[score]}, index=d.index)
                if specification == "controlled":
                    x["log_issue_price"] = np.log(d.issue_price)
                    x["log_articles"] = np.log1p(d.article_count)
                    years = pd.get_dummies(pd.to_datetime(d.listing_date).dt.year, prefix="year", drop_first=True, dtype=float)
                    x = pd.concat([x, years], axis=1)
                    x["within_year_trend"] = pd.to_datetime(d.listing_date).dt.dayofyear / 365.25
                x = sm.add_constant(x, has_constant="add").astype(float)
                if len(d) <= x.shape[1] + 3 or np.linalg.matrix_rank(x) < x.shape[1]:
                    skipped.append({"score": score, "target": target, "specification": specification, "reason": "rank deficient or too few residual degrees of freedom"})
                    continue
                ordinary = sm.OLS(d[target], x).fit()
                influence = ordinary.get_influence()
                if influence.hat_matrix_diag.max() >= 1-1e-10:
                    skipped.append({"score": score, "target": target, "specification": specification, "reason": "unit leverage prevents HC3 inference"})
                    continue
                fit = ordinary.get_robustcov_results(cov_type="HC3", use_t=True)
                conf = fit.conf_int()
                for i, variable in enumerate(x.columns):
                    records.append(dict(score=score, target=target, specification=specification, term=variable,
                                        coef=fit.params[i], se_hc3=fit.bse[i], p=fit.pvalues[i],
                                        ci_low=conf[i, 0], ci_high=conf[i, 1], n=len(d), r2=fit.rsquared,
                                        adjusted_r2=fit.rsquared_adj))
                for j, (_, row) in enumerate(d.iterrows()):
                    diagnostics.append(dict(score=score, target=target, specification=specification, symbol=row.symbol,
                                            residual=ordinary.resid.iloc[j], leverage=influence.hat_matrix_diag[j], cooks_distance=influence.cooks_distance[0][j]))
    coefficients = pd.DataFrame(records)
    if not coefficients.empty:
        primary = coefficients.term.eq(coefficients.score) & coefficients.specification.eq("controlled")
        coefficients["primary_p_holm"] = np.nan
        finite = primary & np.isfinite(coefficients.p)
        if finite.any():
            coefficients.loc[finite, "primary_p_holm"] = multipletests(coefficients.loc[finite, "p"], method="holm")[1]
    return coefficients, pd.DataFrame(correlations), pd.DataFrame(diagnostics), skipped


def holdout(panel, score, target, fraction=0.75, cutoff_date=None):
    """Hold out whole listing dates. Future years never enter training dummies.

    Compare intercept-only historical mean, controls, and controls plus sentiment.
    No tuning on the holdout; all three use identical train/test observations.
    """
    d = panel.dropna(subset=[score, target, "issue_price", "article_count", "listing_date"]).sort_values("listing_date").copy()
    dates = sorted(d.listing_date.unique())
    if len(dates) < 8:
        return {"score": score, "target": target, "status": "too_few_unique_dates"}, pd.DataFrame()
    cutoff = pd.Timestamp(cutoff_date) if cutoff_date else dates[max(1, min(len(dates)-1, int(len(dates)*fraction)))]
    train, test = d[d.listing_date < cutoff], d[d.listing_date >= cutoff]
    if len(train) < 12 or len(test) < 3:
        return {"score": score, "target": target, "status": "too_few_rows"}, pd.DataFrame()
    def design(frame, sentiment):
        x = pd.DataFrame({"const": 1.0, "log_issue_price": np.log(frame.issue_price), "log_articles": np.log1p(frame.article_count)}, index=frame.index)
        if sentiment:
            x[score] = frame[score]
        return x
    predictions = test[["symbol", "listing_date", target]].copy()
    predictions["historical_mean"] = train[target].mean()
    metrics = {"score": score, "target": target, "status": "ok", "cutoff": str(cutoff), "n_train": len(train), "n_test": len(test),
               "split_rule": "predeclared_calendar_cutoff" if cutoff_date else "latest_quarter_of_unique_listing_dates"}
    for name, sentiment in [("controls", False), ("controls_sentiment", True)]:
        x = design(train, sentiment)
        if np.linalg.matrix_rank(x) < x.shape[1]:
            return {**metrics, "status": "rank_deficient_training_design"}, pd.DataFrame()
        fit = sm.OLS(train[target], x).fit()
        predictions[name] = fit.predict(design(test, sentiment))
    for name in ["historical_mean", "controls", "controls_sentiment"]:
        error = predictions[name] - test[target]
        metrics[name + "_mae"] = float(error.abs().mean())
        metrics[name + "_rmse"] = float(np.sqrt(np.mean(error**2)))
    return metrics, predictions
