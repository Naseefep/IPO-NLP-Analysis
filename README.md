# Financial news sentiment and IPO listing-day performance, 2020-2026

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Naseefep/IPO-NLP-Analysis/blob/main/notebooks/ipo_sentiment.ipynb)

A reproducible comparison of **FinBERT** and the **Loughran-McDonald financial
dictionary**, using a date-stratified sample of NSE mainboard IPOs from every
year from 2020 through 2026. **2026 is year to date through 31 October.**

## Start here

- [Full project report (PDF)](reports/report.pdf) and [editable report](reports/report.md).
- [Open the notebook in Colab](https://colab.research.google.com/github/Naseefep/IPO-NLP-Analysis/blob/main/notebooks/ipo_sentiment.ipynb).
- [IPO-by-IPO news counts](results/ipo_news_counts.csv).
- [Year-wise coverage](results/yearly_coverage.csv).
- [Study input tables](data/research/) and [frozen results](results/).

## Study coverage

**162 exchange-verified IPOs** and **2,830 eligible distinct headlines**
covering **158 IPOs**. Headline observations are
retained only after local publication-date, issuer-relevance and duplicate checks.
These are headlines and metadata, not full article bodies.

| Listing year | Verified IPOs | IPOs with news | Eligible headlines |
|---|---:|---:|---:|
| 2020 | 12 | 12 | 95 |
| 2021 | 25 | 23 | 165 |
| 2022 | 25 | 23 | 260 |
| 2023 | 25 | 25 | 284 |
| 2024 | 25 | 25 | 315 |
| 2025 | 25 | 25 | 439 |
| 2026 YTD | 25 | 25 | 1272 |

Annual selection targets 25 IPOs at evenly spaced listing-date ranks. The smaller
2020 frame has 12 candidates, all retained. No sentiment score, return or p-value
is used to pick the date strata. Missing-news IPOs stay in the price panel but
are excluded from sentiment regressions. The sample is not a full IPO census.

## Main result

The controlled FinBERT return coefficient is 79.628, with raw p = 0.0018
and Holm-adjusted p = 0.0073. Across the four controlled sentiment
tests, 1 passes the adjusted 5% threshold.
Read the report for confidence intervals, 2026 prediction errors and limitations.
Textual sentiment accuracy, association and return prediction are separate claims.

## Run in Google Colab

1. Click **Open in Colab** above.
2. Click **Copy to Drive** to keep an editable copy.
3. Run the first code cell: it downloads the public repository automatically.
4. Run the saved-results cell to inspect the published study without a model download.
5. Run the installation cell, then the analysis and output cells in order.

Click the **play button on the left of a code cell** to run it. No ZIP upload,
Drive mount or API key is required. A full model run downloads FinBERT weights
and the authors' official dictionary. A GPU is optional; CPU execution is supported.

## Local installation and reproduction

Python 3.10+ is supported; Python 3.12 is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[finbert]"
python scripts/download_lm.py
ipo-sentiment --ipos data/research/ipos.csv --prices data/research/prices.csv --news data/research/news.csv --model both --holdout-from 2026-01-01 --lm-dictionary data/lexicons/Loughran-McDonald_MasterDictionary_1993-2025.csv --output outputs/my-reproduction
```

Choose a **new or empty output folder** for each run. The manifest records input
SHA-256 hashes, package versions, window, model revision and exclusion counts.
`requirements-lock.txt` records the verified dependency versions; the CPU torch
wheel uses the official PyTorch CPU index. Model weights and dictionary files are
downloaded separately, not bundled with the code.

## Collect the historical sources

```bash
python scripts/collect_multiyear.py --target-per-year 25 --as-of 2026-10-31
python scripts/enrich_news.py
```

These commands write a new source collection to `data/multiyear/` and cache raw
public responses under `data/raw/`. They do not overwrite the published research
inputs. Use the frozen `data/research/` inputs to reproduce the report, since
live search results and the NSE feed can change.

Financial verification uses official legacy and UDiFF NSE bhavcopies, matching
the exact date and EQ-series identity. Official symbol-change records support
documented ticker renames. Feed issue price must equal the first-day reference
price. Invalid OHLC and unmatched prices are excluded with reasons.

News searches use full issuer names, declared distinctive aliases, unique issuer
prefixes and split time windows. `sampling_frame.csv`, `selection_audit.csv`,
`issuer_aliases.csv`, `query_log.csv` and `sources.json` document the process.
The analysis independently reapplies all eligibility rules after retrieval.

## Research choices

1. News window: 30 calendar days before listing, ending immediately before
   listing-day midnight IST. Exclude all listing-day or later items and invalid dates.
2. Relevance: declared issuer-name/alias match plus IPO in the headline. This is
   a deterministic rule, not independent human annotation.
3. Deduplication: identical URLs or normalised headline text within the IPO,
   after removing an exact RSS publisher suffix. Near-duplicate syndication can remain.
4. FinBERT: `P(positive) - P(negative)`, preserving all three probabilities.
   Long text is token-chunked without silent truncation. No stemming or stopword removal.
5. LM: `(positive tokens - negative tokens) / all alphabetic tokens`, excluding
   removed category flags. Retain polarity coverage and uncertainty separately.
6. IPO sentiment: equal-weighted mean of eligible headline scores. No news is
   missing sentiment, not neutral sentiment.
7. Outcomes: issue-to-close listing return in percentage points, and the
   Parkinson daily high-low proxy, without annualisation.
8. Controlled OLS: sentiment, log issue price, log(1 + headline count), year
   indicators and within-year date trend; HC3 SE and pointwise 95% t intervals.
   Holm adjustment covers the four controlled sentiment tests.
9. Prediction: train on IPOs before 2026 and test on covered 2026 IPOs. Compare
   historical mean, controls-only and controls-plus-sentiment models on identical rows.
10. Sensitivity: 14-day window, exclude GMP titles, at least five headlines per
    IPO, and association models excluding 2026. These are exploratory checks.

## Diagnostics and report generation

```bash
python scripts/sensitivity.py
python scripts/make_figures.py
python scripts/verify_results.py
python -m pip install -e ".[report]"
python scripts/build_report.py
```

These supporting scripts use the frozen `results/` folder. The report contains
the introduction, literature, objectives, methods, yearly coverage, empirical
findings, prediction test, sensitivity checks, limitations, references and a
company-by-company appendix with headline counts for every year.

## Offline tests and fictional demonstration

```bash
python -m unittest discover -s tests -v
python scripts/create_demo.py
ipo-sentiment --ipos data/demo/ipos.csv --prices data/demo/prices.csv --news data/demo/news.csv --model lm --lm-dictionary data/demo/toy_dictionary.csv --demo --output outputs/demo
```

The demo companies, prices, headlines and tiny word list are fictional fixtures.
They test the software and never contribute to the research report. GitHub
Actions runs offline tests and the demo without downloading model weights.

## Interpretation and limits

Retrospective RSS discovery is incomplete and changes with time. Older stories,
brand-only titles and revised metadata can affect coverage. Exact deduplication
does not remove all dependence between articles. The study has no independent
Indian IPO sentiment gold labels and does not claim local classification accuracy.

The current model and dictionary vintages make this retrospective measurement,
not a certified historically deployable trading strategy. HC3 does not eliminate
omitted variables, endogeneity or common market shocks. Association is not
causation; a null result does not prove market efficiency. IPO allocation,
risk-adjusted benchmarks, financing and trading costs are outside the design.

## References and rights

- Araci (2019), [FinBERT](https://arxiv.org/abs/1908.10063).
- Huang, Wang and Yang (2023), [FinBERT and financial text](https://doi.org/10.1111/1911-3846.12832).
- Loughran and McDonald (2011), [financial dictionaries](https://doi.org/10.1111/j.1540-6261.2010.01625.x);
  [official dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/).
- Parkinson (1980), [daily high-low estimator](https://doi.org/10.1086/296071).
- [NSE source reports](https://www.nseindia.com/all-reports); exact source URLs and hashes accompany the data.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The MIT license covers
original project code; model weights, dictionary, exchange records and publisher
material retain their original terms.
