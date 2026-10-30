Financial news sentiment<br/>and Indian IPO outcomes

FinBERT and Loughran-McDonald evidence from a 2023 NSE sample

Naseef E. P. | Research report | 29 October 2026


### Abstract

This study examines whether the tone of news before an IPO is associated with its listing-day return and daily high-low volatility. The dataset contains 46 NSE mainboard IPOs selected from the exchange's past-issues feed, with nominal prices checked against listing-date bhavcopies. A strict 30-calendar-day window retains 406 headlines covering 44 IPOs. Each headline is measured using FinBERT and the Loughran-McDonald dictionary, and the resulting scores are averaged within each company. Controlled regressions use HC3 standard errors and Holm adjustment across four primary sentiment tests. FinBERT has a positive return coefficient with an unadjusted p-value of 0.047, but the adjusted p-value is 0.189. None of the four primary tests passes the five per cent adjusted threshold. The chronological holdout also does not show improved RMSE over the historical-mean baseline. The findings therefore support a cautious conclusion: contextual sentiment captures some in-sample variation, but this sample does not establish reliable forecasting value.

| Price-verified IPOs | IPOs with news | Retained headlines |
|---|---|---|

| 46 | 44 | 406 |


### Research question

Do finance-specific sentiment measures of pre-listing headlines help explain or predict listing-day outcomes after simple observable controls are considered? Returns and the daily range proxy are treated as separate outcomes. The analysis distinguishes an association in the full sample from predictive performance on later IPOs.

Keywords: Indian IPOs; financial sentiment; FinBERT; Loughran-McDonald; listing return; reproducible research.


## 1. Sample and source verification

An IPO's listing-day return compares the first closing price with the issue price paid by an allotted investor. News may help explain this difference because it communicates information about valuation, subscription demand and the company's business. But the dates matter: an article describing the listing result cannot be used as a pre-listing predictor.

The sample is defined before sentiment estimation. The current NSE past-issues response is filtered to EQ issues with both an issue-opening date and a listing date in 2023. This gives a bounded mainboard sample. It is not a certified census of every IPO in that year, and it excludes the SME category. Both the feed and the raw exchange responses are recorded by source URL and SHA-256 hash.

| Step | Rule / result |
|---|---|

| Universe | 46 eligible feed-defined EQ issues opened and listed in 2023 |

| Prices | 46 exact symbol/EQ/date matches in official NSE bhavcopies |

| Issue-price check | Feed issue price equals listing-day PREVCLOSE, within INR 0.005 |

| News discovery | 828 historical Google News RSS candidates |

| Date screening | 192 excluded at or after listing-day midnight IST |

| Relevance screening | 230 excluded by the declared company-phrase + IPO rule |

| Final corpus | 406 eligible headlines; 44 IPOs with at least one headline |

| Missing coverage | YATHARTH, SIGNATURE; retained in the price panel, excluded from sentiment models |

NSE bhavcopies give prices as recorded for that trading date. This avoids mixing an original issue price with a subsequently split-adjusted historical close. No nearby-day price is substituted when an exact listing-day record is absent. OHLC values must also be positive and internally consistent.

Google News is a discovery source, while the publishers identified in RSS are the content sources. These historical searches are made in October 2026. Their results can omit old stories or expose later revisions, so the corpus should be understood as a reproducible retrieval snapshot rather than a complete contemporary news archive.


## 2. Measurement and estimation


### Pre-listing information

The primary window starts 30 calendar days before listing and ends immediately before midnight on the listing date in Asia/Kolkata. Offset-aware timestamps are converted to local time. Naive dates are interpreted locally; invalid timestamps are rejected. All listing-day articles are excluded, including date-only records. A shorter 14-day window is an exploratory sensitivity check.

Relevance requires the normalised company phrase and the word IPO in the title. This is a declared rule, not human-labelled relevance. Exact URL or normalised-title duplicates are removed within an IPO. The headline is scored without stemming or stopword removal, so contextual words and negation remain available to FinBERT. A publisher suffix is removed only when it exactly matches the RSS source.

| Measure | Definition |
|---|---|

| FinBERT headline score | P(positive) - P(negative), preserving all three class probabilities |

| LM headline score | (positive token count - negative token count) / all alphabetic tokens |

| IPO sentiment | Equal-weighted mean of retained headline scores within the IPO |

| Listing return (%) | 100 x (listing-day close / issue price - 1) |

| Parkinson daily proxy | ln(high / low) / sqrt(4 x ln(2)); daily units, without annualisation |

FinBERT is a finance-domain BERT classifier described by Araci (2019). Its output measures textual tone; it is not a calibrated probability that the share price will rise. The Loughran-McDonald dictionary was developed for financial disclosures (Loughran and McDonald, 2011), so its transfer to short Indian IPO headlines is examined through observed word coverage. Removed dictionary categories are excluded and uncertainty is recorded separately.


### Statistical design

For each outcome and sentiment method, simple OLS is followed by a controlled model with log issue price, log(1 + headline count) and a within-year listing-date trend. The package supports year indicators for multi-year extensions; no year effect can be estimated within this single-year sample. HC3 standard errors and t-based 95% confidence intervals are reported. Holm adjustment covers the four controlled sentiment coefficients. Correlations, simple regressions and sensitivity checks remain exploratory.

The Parkinson measure is a daily high-low range proxy. It relies on assumptions about the price process and may be affected by opening price discovery, drift and market frictions. It is not tick-based realised volatility, and the classical efficiency comparison with close-to-close estimators should not be taken as a guarantee for IPO listing sessions.


## 3. Main empirical results

| Variable (N = 44) | Mean | Median | Std. dev. |
|---|---|---|---|

| Listing return (%) | 28.9911 | 21.0594 | 34.9661 |

| Daily Parkinson proxy | 0.0654 | 0.0592 | 0.0285 |

| FinBERT IPO score | 0.0949 | 0.1000 | 0.1037 |

| LM IPO score | 0.0035 | 0.0000 | 0.0156 |

The return distribution is wide, and sentiment also varies across IPOs. The Pearson association between FinBERT and return is positive, but association alone does not show whether the text adds useful predictive information. The controlled coefficients below use the same 44 IPOs for both methods.

| Method | Outcome | Coefficient | 95% HC3 CI | Raw p | Holm p |
|---|---|---|---|---|---|

| FinBERT | Return (%) | 102.489 | [1.349, 203.629] | 0.047 | 0.189 |

| FinBERT | Daily proxy | -0.015 | [-0.073, 0.044] | 0.619 | 1.000 |

| LM | Return (%) | 307.275 | [-6025.527, 6640.078] | 0.922 | 1.000 |

| LM | Daily proxy | 0.197 | [-1.427, 1.821] | 0.807 | 1.000 |

Coefficients are per one unit of the original sentiment score. The confidence intervals are pointwise intervals; they are not adjusted for the four-test family. A 0.1 increase in FinBERT score corresponds to an estimated 10.25 percentage-point increase in return, holding the specified controls fixed. Its pointwise interval just excludes zero, but the Holm-adjusted test does not pass the five per cent threshold.

The return model's total R-squared is 0.119 and adjusted R-squared is 0.029. These values describe the full specification, not the contribution of sentiment alone. LM estimates are imprecise and daily-proxy estimates provide little evidence of a stable relationship. This is not evidence that sentiment has exactly zero effect; it shows that this sample does not estimate those relationships precisely.


## 3. Main results: visual inspection

Each point below represents an IPO with eligible news and a verified listing-day price. Both panels use the same IPO-level FinBERT score. The scatter makes the dispersion visible; it does not adjust for company or date controls. The uncertainty around the controlled coefficients is reported on the preceding page.


![Sentiment and outcomes](../results/sentiment_outcomes.png)


### Five highest listing returns in the analysed sample

| Symbol | Return (%) | FinBERT | LM |
|---|---|---|---|

| TATATECH | 162.60 | 0.124 | 0.003 |

| IDEAFORGE | 92.70 | 0.337 | 0.024 |

| UTKARSHBNK | 92.00 | 0.133 | 0.000 |

| NETWEB | 82.08 | 0.018 | 0.000 |

| GANDHAR | 78.34 | 0.022 | 0.000 |

These observations illustrate why the headline score should be interpreted alongside its coverage and the underlying news. A large listing return does not require an extreme sentiment score. The table is a descriptive view of the retained sample and is not used to select observations for the regression or to tune the prediction model.


## 4. Chronological prediction check

Prediction is evaluated separately from the full-sample regressions. The latest quarter of unique listing dates is held out, with same-date IPOs kept together. The split begins on 7 November 2023 and gives 29 training IPOs and 15 test IPOs. This is not a random split, and all three predictors are compared on identical test rows.

The historical-mean predictor uses the training outcome mean. The controls-only predictor uses log issue price and log headline count. The third predictor adds one sentiment score. No future-year dummy or outcome-based feature selection is used. Because the test set is small, the errors are descriptive estimates rather than a precise ranking of forecasting methods.


### Listing return: errors in percentage points

| Predictor | MAE | RMSE |
|---|---|---|

| Historical mean | 29.82 | 43.15 |

| Controls only | 31.04 | 43.79 |

| Controls + FinBERT | 30.60 | 45.11 |

| Controls + LM | 50.47 | 92.06 |


### Daily Parkinson proxy: errors in daily units

| Predictor | MAE | RMSE |
|---|---|---|

| Historical mean | 0.0261 | 0.0312 |

| Controls only | 0.0314 | 0.0369 |

| Controls + FinBERT | 0.0313 | 0.0370 |

| Controls + LM | 0.0359 | 0.0455 |

Neither sentiment method improves RMSE over the historical-mean baseline for either target. FinBERT slightly reduces return MAE relative to controls alone, but its return RMSE increases. LM gives especially unstable return predictions, which is consistent with its very sparse polarity coverage. The small holdout does not establish which approach would work best in a larger population.


## 5. Measurement checks and sensitivity

The LM dictionary contains no positive or negative match in 393 of 406 retained headlines (96.8%). A zero polarity score therefore often reflects no matched polarity word. It should not automatically be interpreted as evidence that a headline is substantively neutral. The uncertainty category is stored separately and does not enter the primary polarity score.

FinBERT produces more varied scores, including for headlines about subscriptions and anchor investment. However, this project does not have a manually labelled Indian IPO benchmark. More variation does not establish greater sentiment accuracy. A useful extension is independent annotation of a stratified sample, followed by macro-F1, agreement and error analysis before changing the measurement specification.


### Exploratory return-coefficient checks

| Specification | N | FinBERT coef. | Raw p | Holm p |
|---|---|---|---|---|

| 14-day window | 44 | 76.95 | 0.090 | 0.358 |

| Exclude GMP / grey-market titles | 44 | 90.01 | 0.030 | 0.120 |

The shorter window weakens the return association. Removing headlines that explicitly mention GMP or grey-market prices leaves a positive coefficient, but it still does not pass the within-specification Holm adjustment. These are sensitivity checks, not additional primary discoveries. Their p-values are not adjusted across every exploratory choice in the project.


### Influential observations and sparse text

| Largest Cook's distances: return model | Cook's D | Leverage |
|---|---|---|

| TATATECH | 0.454 | 0.125 |

| UTKARSHBNK | 0.234 | 0.304 |

| NETWEB | 0.197 | 0.173 |

These diagnostics identify rows that deserve source and model review. They do not justify removing IPOs solely because their outcomes are inconvenient. The full sample remains the primary specification. Ordinary HC3 inference does not account for all possible dependence between IPOs listed in the same market environment; a larger multi-year sample would support stronger time-block inference.


## 6. Interpretation and limitations

The clearest result is the difference between an in-sample relationship and forecasting value. FinBERT tone is positively associated with listing returns, but the adjusted test and holdout errors do not support a strong predictive claim. The LM comparison also shows why a finance-specific dictionary is not automatically informative for every financial text format: short IPO headlines can contain very few polarity words.

The results do not identify a causal effect of journalism. Subscription demand, company quality, valuation, industry and grey-market expectations may influence both reporting and prices. Log issue price is an observable price-level control, not a complete measure of company size or valuation. News count may also be related to investor attention and should not be treated as an exogenous variable.

| Limitation | Consequence |
|---|---|

| Feed-defined single-year sample | Results describe the included IPOs; omitted EQ issues and other years may behave differently. |

| Retrospective RSS retrieval | Search ranking, missing stories and updated content can affect the measured information set. |

| Strict company phrase | Reduces ambiguous matches but misses aliases and two IPOs entirely. |

| Headline-only text | Preserves a consistent unit, but omits detail and can misread context or irony. |

| No local sentiment gold labels | FinBERT classification accuracy on Indian IPO news is not established. |

| Sparse LM polarity matches | Estimates can be unstable and zero scores require careful interpretation. |

| Contemporary measurement tools | Current model and dictionary vintages prevent claims of a historically certified trading strategy. |

| Small holdout and shared market shocks | Test errors and conventional regression uncertainty do not establish general market performance. |

A non-significant sentiment coefficient is not proof of semi-strong market efficiency. Market efficiency concerns risk-adjusted opportunities and the information set available to investors. An allotted investor's issue-to-close return is also different from a strategy available to someone buying after the listing opens. These questions require a broader design, allocation assumptions and trading-cost treatment.

The next research extension should expand the independently verified IPO universe, add pre-listing company and market controls, validate sentiment labels and preserve a genuinely untouched later-year evaluation set. It should retain the same auditable date rules and document any change before comparing outcomes.


## 7. Reproduction and validation

The repository separates source inputs, article measurement, IPO-level analysis, prediction checks and reporting. Frozen input tables make the reported estimates reproducible without relying on a new historical search. Source collection scripts are also provided, although future downloads can legitimately change the retrieval snapshot.

| Research component | Implementation and checks |
|---|---|

| Pre-listing information window | Local timestamp screening before any sentiment aggregation |

| Listing-day identification | Exact date, symbol and EQ-series checks in official bhavcopies |

| Price verification | Nominal exchange OHLC with source URL, ISIN and issue-price cross-check |

| Sentiment measurement | Contextual FinBERT and official LM comparison on identical headlines |

| Statistical inference | HC3 intervals and a declared four-test Holm family |

| Prediction evaluation | Chronological held-out predictions against simple baselines |

| Interpretation | Separate conclusions about association, prediction and market efficiency |

| Reproducibility | Reusable package, notebook, tests, CI and report generated from results |


### Run the study

Install the package with its FinBERT extra, download the authors' official dictionary, then run the command in README.md with the bundled data/research inputs and a new output directory. The notebook provides the same steps for local Jupyter and Colab. The source ZIP includes the code, input tables, frozen results and report; model weights are downloaded separately.

The run manifest records input SHA-256 hashes, package versions, the dictionary hash and the immutable model revision. Nine offline tests check date and timezone boundaries, price matching, duplicate handling, missing news coverage, dictionary-category removal and whole-date holdout splitting. A synthetic demonstration tests the software without supplying research evidence.


### Measurement provenance

FinBERT revision: 0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031

LM dictionary SHA-256: 147cb24a1687ccde60363a0fa29c62be4097debcc698c01a83e51bb8a176dbb3

The model and dictionary are third-party research resources. Their terms are listed in THIRD_PARTY_NOTICES.md. The project code is licensed separately.


## References and source access

Araci, D. (2019). FinBERT: Financial Sentiment Analysis with Pre-trained Language Models. arXiv:1908.10063.

<link href="https://arxiv.org/abs/1908.10063" color="#157a86">Source link</link>

https://arxiv.org/abs/1908.10063

Loughran, T., and McDonald, B. (2011). When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks. Journal of Finance, 66(1), 35-65.

<link href="https://sraf.nd.edu/loughranmcdonald-master-dictionary/" color="#157a86">Source link</link>

https://sraf.nd.edu/loughranmcdonald-master-dictionary/

Parkinson, M. (1980). The Extreme Value Method for Estimating the Variance of the Rate of Return. Journal of Business, 53(1), 61-65.

<link href="https://doi.org/10.1086/296071" color="#157a86">Source link</link>

https://doi.org/10.1086/296071

ProsusAI. FinBERT model card, architecture, label mapping and usage terms. Accessed 29 October 2026.

<link href="https://huggingface.co/ProsusAI/finbert" color="#157a86">Source link</link>

https://huggingface.co/ProsusAI/finbert

University of Notre Dame SRAF. Loughran-McDonald Master Dictionary, 1993-2025 edition. Accessed 29 October 2026; official spreadsheet CSV export used when the direct CSV link reached its quota.

<link href="https://sraf.nd.edu/loughranmcdonald-master-dictionary/" color="#157a86">Source link</link>

https://sraf.nd.edu/loughranmcdonald-master-dictionary/

National Stock Exchange of India. Past public issues feed and dated equity bhavcopies. Retrieved 29 October 2026; exact URLs and hashes in data/research/sources.json.

<link href="https://www.nseindia.com/all-reports" color="#157a86">Source link</link>

https://www.nseindia.com/all-reports

Google News RSS and named publishers. Historical headline metadata retrieved 29 October 2026. Individual publisher names, publication timestamps and article links are retained in the corpus.

<link href="https://news.google.com/" color="#157a86">Source link</link>

https://news.google.com/

statsmodels. Robust covariance results documentation: HC3 and t-based inference. Accessed 29 October 2026.

<link href="https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html" color="#157a86">Source link</link>

https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html


### Data and code accompanying this report

The project release contains the reusable Python package, notebook, frozen input metadata, complete exclusion audits, regression and holdout tables, sensitivity outputs and this report. Every empirical number in the report is read from the saved result tables. Synthetic fixtures are stored separately and do not contribute to the reported estimates.