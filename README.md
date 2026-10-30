# Financial news sentiment and Indian IPO outcomes

A reproducible study of pre-listing headline sentiment, listing-day returns and
daily high-low volatility for an explicitly bounded sample of 2023 NSE mainboard
IPOs. It compares **FinBERT** with the **Loughran-McDonald financial dictionary**.

The Python package provides input validation, strict news cutoffs, verified
exchange prices, audit files, robust inference, chronological prediction checks
and a report generated from results.

## Start here

- [Research report (PDF)](reports/report.pdf) and [editable text](reports/report.md).
- [Jupyter / Colab notebook](notebooks/ipo_sentiment.ipynb).
- `results/`: frozen empirical output tables, audits, chart and run manifest.
- `data/research/`: study input tables and source provenance.
- `src/iposent/`: reusable analysis code.

## Verified study snapshot

The study sample has **46 exchange-verified IPOs** and **406 eligible headlines
covering 44 IPOs**. FinBERT's controlled return coefficient has raw p = 0.047 and
Holm-adjusted p = 0.189. None of the four primary sentiment tests passes the
adjusted 5% threshold. For held-out listing returns, RMSE is 43.15 percentage
points for the historical-mean baseline and 45.11 for controls plus FinBERT.
The report explains why these results do not establish reliable forecasting value.

## Install

Python 3.10+ is required; Python 3.12 is recommended. From this folder:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[finbert]"
```

The base install is lightweight and supports dictionary analysis. FinBERT also
downloads approximately 440 MB of model weights on first use; a GPU is optional.
`requirements-lock.txt` records the verified environment. For a CPU-only torch
wheel, install torch from the official PyTorch CPU index before the editable install.

## Reproduce the empirical study

```bash
python scripts/download_lm.py
ipo-sentiment --ipos data/research/ipos.csv --prices data/research/prices.csv --news data/research/news.csv --model both --lm-dictionary data/lexicons/Loughran-McDonald_MasterDictionary_1993-2025.csv --output outputs/my-reproduction
```

Choose a new output folder for every run. The command never mixes new files with
old outputs. The manifest records input and dictionary hashes, package versions,
the immutable FinBERT revision, exclusions and model status. Compare the new
tables with `results/`; small floating-point differences can occur across runtimes.

The local model cache and original dictionary are excluded from Git and the ZIP.
The dictionary downloader validates the response and tries the authors' official
spreadsheet export if their CSV download is unavailable.

After the main run, `python scripts/sensitivity.py` reproduces the exploratory
checks from `results/article_scores.csv`. `python scripts/build_report.py`
regenerates the PDF and editable report from the frozen `results/` folder
(install the `report` extra first). `python scripts/verify_results.py` checks
the frozen output's input hashes, probability scores and date boundaries.

## Collect the source dataset

```bash
python scripts/collect_2023.py
```

This downloads the current NSE past-issues feed, selects EQ issues both opened
and listed in 2023, and matches the exact listing date and symbol/series in the
official NSE bhavcopy. The issue price must equal the first-day PREVCLOSE field.
It caches raw public responses locally and records hashes and source URLs.
It then retrieves historical RSS candidates using a dated company query.
Live sources can change, so use the bundled input tables for the frozen study.

This is a **feed-defined sample**, not a claim to cover every Indian IPO in 2023.
SME issues, REITs and InvITs are outside the selected EQ sample. Never add an IPO
solely because its first-day price resembles an issue price.

## Research choices

1. Retain news in `[listing midnight IST - 30 calendar days, listing midnight IST)`.
   Listing-day articles are excluded even when they have only a calendar date.
   The search query is only discovery; local timestamp filtering is authoritative.
2. Require the normalised company phrase and the word IPO in a headline. This
   deterministic relevance rule is recorded, not presented as human annotation.
   Company aliases can improve coverage but must be declared before estimation.
3. Deduplicate within each IPO by normalised headline or identical URL. Store
   every rejected candidate with a reason. Near-duplicate syndicated stories can remain.
4. Score headlines without removing negation or stopwords. Remove the publisher
   suffix when it exactly matches the RSS source. Do not add snippets that repeat
   a headline or contain search-page boilerplate.
5. FinBERT score is `P(positive) - P(negative)`. Preserve all three probabilities.
   Overlength text is chunked without silent truncation and chunk probabilities
   are averaged. The short-headline study does not need long-document chunking.
6. LM score is `(positive tokens - negative tokens) / all alphabetic tokens`.
   Removed category flags are excluded. Retain coverage and uncertainty measures.
   No lexicon matches means zero polarity; no eligible news means missing sentiment.
7. Average each method's article scores equally within an IPO. No price outcomes
   enter scoring or headline selection. Compare methods on the same retained corpus.
8. Return is `100 * (listing close / issue price - 1)`, in percentage points.
   Parkinson daily range proxy is `ln(high/low)/sqrt(4*ln(2))`, in daily units.
   It is not an annualised measure or observed intraday realised volatility.
9. Fit simple and controlled OLS separately for each sentiment method and target.
   Controls: log issue price, log(1 + headline count), within-year listing-date trend
   and year indicators if multiple years exist. Use HC3 standard errors and t-based
   confidence intervals. Reject singular designs and unit-leverage inference.
   Apply Holm adjustment to the four controlled sentiment tests.
10. Separately hold out the latest 25% of unique listing dates, keeping same-date
    IPOs together. Compare historical-mean, controls-only and controls-plus-sentiment
    predictions on identical rows. Forecasting controls are log issue price and
    log headline count; no future-year dummy is estimated. Report MAE and RMSE.

## Offline software demonstration

```bash
python scripts/create_demo.py
ipo-sentiment --ipos data/demo/ipos.csv --prices data/demo/prices.csv --news data/demo/news.csv --model lm --lm-dictionary data/demo/toy_dictionary.csv --demo --output outputs/demo
python -m unittest discover -s tests -v
```

The fictional companies, prices, headlines and toy word list test the software.
They are clearly marked synthetic and are never used in the research report.
GitHub Actions runs these tests without downloading FinBERT or a dictionary.

## Use your own data

See `data/templates/` and the column specification in `docs/data_dictionary.md`.
`scripts/collect_prices.py` and `scripts/collect_news.py` create candidates for
other years; independent price and relevance verification is required. They do
not automatically certify a complete historical corpus.

## Limits and interpretation

Retrospective RSS retrieval, incomplete coverage, headline-only text, a small
single-year sample and unmeasured IPO characteristics limit inference. The
current dictionary/model vintage makes this a retrospective measurement study,
not a certified historically deployable trading strategy. A non-significant
coefficient does not establish market efficiency. An association does not identify
a causal effect. See the report for actual estimates and prediction errors.

## Publish on GitHub

The release ZIP contains the source, input metadata, frozen results and report.
Extract it, open a terminal in the project folder and run:

```bash
git init
git add .
git commit -m "Add reproducible IPO sentiment study"
git branch -M main
```

Create an empty repository in your GitHub account, then use its actual URL:

```bash
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Review the source terms in `THIRD_PARTY_NOTICES.md` before distributing third-party
materials. The project's MIT license applies to original code. No model weights,
private documents, credentials or local environments belong in the repository.

## References

- Araci (2019), [FinBERT](https://arxiv.org/abs/1908.10063).
- Loughran & McDonald (2011), *When Is a Liability Not a Liability? Textual Analysis,
  Dictionaries, and 10-Ks*, Journal of Finance 66(1), 35-65;
  [authors' dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/).
- Parkinson (1980), *The Extreme Value Method for Estimating the Variance of the
  Rate of Return*, Journal of Business 53(1), 61-65.
- [NSE reports](https://www.nseindia.com/all-reports) and the source URLs recorded
  for each observation.
