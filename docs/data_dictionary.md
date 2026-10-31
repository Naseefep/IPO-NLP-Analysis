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

In the 2020-2026 collection, `relevance_method=declared_issuer_alias_and_ipo` distinguishes
rule-based relevance checks from human annotation. Timestamps without an offset
are interpreted in Asia/Kolkata; offset-aware timestamps are converted to IST.
Missing/unparseable timestamps are rejected. Listing-day midnight is excluded.

`prices.csv` also preserves ISIN and PREVCLOSE. Each row's source URL is the
official bhavcopy for that date. `ipos.csv` records issue open/close dates and the
NSE universe feed URL. `sources.json` traces every cached raw response by SHA-256.
`bhavcopy_symbol` preserves the historic exchange symbol where a rename applies.
Both legacy and UDiFF bhavcopy schemas are supported.

`sampling_frame.csv` contains every eligible candidate before annual sampling.
`selection_audit.csv` records primary date strata, reserve selections and price
failures. `issuer_aliases.csv` lists the declared relevance phrases, while
`query_log.csv` records dated queries and their retrieval results.
The annual target is 25 price-verified IPOs; all 12 available 2020 candidates are
retained. The 2026 period is year to date through 31 October 2026.

## Outputs

| Output | Purpose |
|---|---|
| manifest.json | Input/model versions, hashes, window, counts, status, skipped models |
| news_audit.csv | Every candidate, parsed time and first rejection reason |
| price_audit.csv | Every IPO, price eligibility and derived outcomes |
| article_scores.csv | Retained headline and each method's measurements |
| analysis_panel.csv | All IPOs, including missing-coverage rows |
| ipo_news_counts.csv | Company, symbol, listing date and retained headline count |
| yearly_coverage.csv | Verified IPOs, news-covered IPOs and headline counts by year |
| coefficients.csv | OLS coefficients, HC3 SE, 95% CI, raw p, Holm p for primary tests |
| correlations.csv | Pearson and Spearman associations, without adjusted p-values |
| diagnostics.csv | Residuals, leverage and Cook's distance per fitted model |
| holdout_metrics.json | Date split, training/test counts, MAE and RMSE by baseline |
| holdout_*.csv | Actual outcomes and identical-row baseline/sentiment predictions |

The Holm family comprises controlled FinBERT/LM sentiment coefficients for return
and Parkinson proxy. Simple regressions and correlations are exploratory.
Log transforms and date controls are specified in code; no holdout outcomes are
used to select hyperparameters. Missing coverage is reported, never filled as neutral.
The published multi-year prediction test is fixed at 1 January 2026: earlier
listings form training data and covered 2026 IPOs form the test data.
