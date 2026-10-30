# Data dictionary

All CSVs are UTF-8. Dates are ISO `YYYY-MM-DD`. Price units are INR per share.
Symbols are historic listing-date identifiers, not assumed current tickers.

| File | Required fields | Meaning |
|---|---|---|
| IPOs | symbol, company, listing_date, issue_price | One IPO per unique symbol; price positive |
| Prices | symbol, observed_date, open, high, low, close | Exact listing day; positive internally consistent OHLC |
| Prices | verified, quote_basis, source_url | true, listing_day_nominal, and documentary source URL |
| News | symbol, headline, published_at, source, url | Article-level headline and original metadata |
| News | relevance_verified | true only after a declared rule or human review establishes relevance |

In the 2023 collection, `relevance_method=exact_company_phrase_and_ipo` distinguishes
rule-based relevance checks from human annotation. Timestamps without an offset
are interpreted in Asia/Kolkata; offset-aware timestamps are converted to IST.
Missing/unparseable timestamps are rejected. Listing-day midnight is excluded.

`prices.csv` also preserves ISIN and PREVCLOSE. Each row's source URL is the
official bhavcopy for that date. `ipos.csv` records issue open/close dates and the
NSE universe feed URL. `sources.json` traces every cached raw response by SHA-256.

## Outputs

| Output | Purpose |
|---|---|
| manifest.json | Input/model versions, hashes, window, counts, status, skipped models |
| news_audit.csv | Every candidate, parsed time and first rejection reason |
| price_audit.csv | Every IPO, price eligibility and derived outcomes |
| article_scores.csv | Retained headline and each method's measurements |
| analysis_panel.csv | All IPOs, including missing-coverage rows |
| coefficients.csv | OLS coefficients, HC3 SE, 95% CI, raw p, Holm p for primary tests |
| correlations.csv | Pearson and Spearman associations, without adjusted p-values |
| diagnostics.csv | Residuals, leverage and Cook's distance per fitted model |
| holdout_metrics.json | Date split, training/test counts, MAE and RMSE by baseline |
| holdout_*.csv | Actual outcomes and identical-row baseline/sentiment predictions |

The Holm family comprises controlled FinBERT/LM sentiment coefficients for return
and Parkinson proxy. Simple regressions and correlations are exploratory.
Log transforms and date controls are specified in code; no holdout outcomes are
used to select hyperparameters. Missing coverage is reported, never filled as neutral.
