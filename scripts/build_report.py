"""Generate the report from frozen results. No invented or hardcoded estimates.

Uses reportlab; run from the project root after results and sensitivity exist.
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/"results"
OUT=ROOT/"reports"
OUT.mkdir(exist_ok=True)
panel=pd.read_csv(RESULTS/"analysis_panel.csv")
sample=panel[panel.article_count.gt(0)]
articles=pd.read_csv(RESULTS/"article_scores.csv")
coeff=pd.read_csv(RESULTS/"coefficients.csv")
primary=coeff[coeff.term.eq(coeff.score)&coeff.specification.eq("controlled")]
correlations=pd.read_csv(RESULTS/"correlations.csv")
sensitivity=pd.read_csv(RESULTS/"sensitivity.csv")
manifest=json.loads((RESULTS/"manifest.json").read_text(encoding="utf8"))
metrics=json.loads((RESULTS/"holdout_metrics.json").read_text(encoding="utf8"))
finreturn=primary[primary.score.eq("finbert_score")&primary.target.eq("listing_return_pct")].iloc[0]
lmzero=int(articles.lm_coverage.eq(0).sum())
missing=", ".join(panel.loc[panel.article_count.eq(0),"symbol"])

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle",fontName="Helvetica-Bold",fontSize=28,leading=33,textColor=colors.HexColor("#15364a"),spaceAfter=18))
styles.add(ParagraphStyle(name="Deck",fontName="Helvetica",fontSize=13,leading=19,textColor=colors.HexColor("#386074"),spaceAfter=17))
styles.add(ParagraphStyle(name="BodyReport",fontName="Helvetica",fontSize=10.5,leading=15.5,spaceAfter=10))
styles.add(ParagraphStyle(name="SmallReport",fontName="Helvetica",fontSize=8.5,leading=12,spaceAfter=8))
styles.add(ParagraphStyle(name="TableReport",fontName="Helvetica",fontSize=8.5,leading=11))
styles["Heading1"].fontSize=19
styles["Heading1"].leading=24
styles["Heading1"].textColor=colors.HexColor("#15364a")
styles["Heading1"].spaceAfter=16
styles["Heading2"].fontSize=12
styles["Heading2"].spaceBefore=10
styles["Heading2"].spaceAfter=8

story=[]
markdown=[]
def para(text,style="BodyReport"):
    story.append(Paragraph(text,styles[style]))
    markdown.append(text.replace("<b>","**").replace("</b>","**"))
def heading(text):
    story.append(Paragraph(text,styles["Heading1"]))
    markdown.append("\n## "+text)
def sub(text):
    story.append(Paragraph(text,styles["Heading2"]))
    markdown.append("\n### "+text)
def table(headers,rows,widths):
    data=[[Paragraph(escape(str(v)),styles["TableReport"]) for v in headers]]
    data += [[Paragraph(escape(str(v)),styles["TableReport"]) for v in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e4eff3")),("VALIGN",(0,0),(-1,-1),"TOP"),
                           ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
                           ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
                           ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f8fa")])]))
    story.append(t)
    story.append(Spacer(1,12))
    markdown.append("| "+" | ".join(map(str,headers))+" |\n|"+"---|"*len(headers))
    markdown.extend("| "+" | ".join(map(str,row))+" |" for row in rows)
def page():
    story.append(PageBreak())
def metric(score,target):
    return next(m for m in metrics if m["score"]==score and m["target"]==target)
def fmt(x, digits=3):
    return f"{x:.{digits}f}"

para("Financial news sentiment<br/>and Indian IPO outcomes","ReportTitle")
para("FinBERT and Loughran-McDonald evidence from a 2023 NSE sample","Deck")
para("Naseef E. P. | Research report | 29 October 2026","SmallReport")
sub("Abstract")
para(f"This study examines whether the tone of news before an IPO is associated with its listing-day return and daily high-low volatility. The dataset contains {len(panel)} NSE mainboard IPOs selected from the exchange's past-issues feed, with nominal prices checked against listing-date bhavcopies. A strict 30-calendar-day window retains {len(articles)} headlines covering {len(sample)} IPOs. Each headline is measured using FinBERT and the Loughran-McDonald dictionary, and the resulting scores are averaged within each company. Controlled regressions use HC3 standard errors and Holm adjustment across four primary sentiment tests. FinBERT has a positive return coefficient with an unadjusted p-value of {finreturn.p:.3f}, but the adjusted p-value is {finreturn.primary_p_holm:.3f}. None of the four primary tests passes the five per cent adjusted threshold. The chronological holdout also does not show improved RMSE over the historical-mean baseline. The findings therefore support a cautious conclusion: contextual sentiment captures some in-sample variation, but this sample does not establish reliable forecasting value.")
table(["Price-verified IPOs","IPOs with news","Retained headlines"],[[len(panel),len(sample),len(articles)]],[156,156,156])
sub("Research question")
para("Do finance-specific sentiment measures of pre-listing headlines help explain or predict listing-day outcomes after simple observable controls are considered? Returns and the daily range proxy are treated as separate outcomes. The analysis distinguishes an association in the full sample from predictive performance on later IPOs.")
para("Keywords: Indian IPOs; financial sentiment; FinBERT; Loughran-McDonald; listing return; reproducible research.","SmallReport")

page()
heading("1. Sample and source verification")
para("An IPO's listing-day return compares the first closing price with the issue price paid by an allotted investor. News may help explain this difference because it communicates information about valuation, subscription demand and the company's business. But the dates matter: an article describing the listing result cannot be used as a pre-listing predictor.")
para("The sample is defined before sentiment estimation. The current NSE past-issues response is filtered to EQ issues with both an issue-opening date and a listing date in 2023. This gives a bounded mainboard sample. It is not a certified census of every IPO in that year, and it excludes the SME category. Both the feed and the raw exchange responses are recorded by source URL and SHA-256 hash.")
table(["Step","Rule / result"],[
    ["Universe",f"{len(panel)} eligible feed-defined EQ issues opened and listed in 2023"],
    ["Prices",f"{len(panel)} exact symbol/EQ/date matches in official NSE bhavcopies"],
    ["Issue-price check","Feed issue price equals listing-day PREVCLOSE, within INR 0.005"],
    ["News discovery",f"{manifest['counts']['news_input']} historical Google News RSS candidates"],
    ["Date screening",f"{manifest['news_rejections'].get('at_or_after_cutoff',0)} excluded at or after listing-day midnight IST"],
    ["Relevance screening",f"{manifest['news_rejections'].get('relevance_not_verified',0)} excluded by the declared company-phrase + IPO rule"],
    ["Final corpus",f"{len(articles)} eligible headlines; {len(sample)} IPOs with at least one headline"],
    ["Missing coverage",missing+"; retained in the price panel, excluded from sentiment models"]
],[106,362])
para("NSE bhavcopies give prices as recorded for that trading date. This avoids mixing an original issue price with a subsequently split-adjusted historical close. No nearby-day price is substituted when an exact listing-day record is absent. OHLC values must also be positive and internally consistent.")
para("Google News is a discovery source, while the publishers identified in RSS are the content sources. These historical searches are made in October 2026. Their results can omit old stories or expose later revisions, so the corpus should be understood as a reproducible retrieval snapshot rather than a complete contemporary news archive.")

page()
heading("2. Measurement and estimation")
sub("Pre-listing information")
para("The primary window starts 30 calendar days before listing and ends immediately before midnight on the listing date in Asia/Kolkata. Offset-aware timestamps are converted to local time. Naive dates are interpreted locally; invalid timestamps are rejected. All listing-day articles are excluded, including date-only records. A shorter 14-day window is an exploratory sensitivity check.")
para("Relevance requires the normalised company phrase and the word IPO in the title. This is a declared rule, not human-labelled relevance. Exact URL or normalised-title duplicates are removed within an IPO. The headline is scored without stemming or stopword removal, so contextual words and negation remain available to FinBERT. A publisher suffix is removed only when it exactly matches the RSS source.")
table(["Measure","Definition"],[
    ["FinBERT headline score","P(positive) - P(negative), preserving all three class probabilities"],
    ["LM headline score","(positive token count - negative token count) / all alphabetic tokens"],
    ["IPO sentiment","Equal-weighted mean of retained headline scores within the IPO"],
    ["Listing return (%)","100 x (listing-day close / issue price - 1)"],
    ["Parkinson daily proxy","ln(high / low) / sqrt(4 x ln(2)); daily units, without annualisation"]
],[132,336])
para("FinBERT is a finance-domain BERT classifier described by Araci (2019). Its output measures textual tone; it is not a calibrated probability that the share price will rise. The Loughran-McDonald dictionary was developed for financial disclosures (Loughran and McDonald, 2011), so its transfer to short Indian IPO headlines is examined through observed word coverage. Removed dictionary categories are excluded and uncertainty is recorded separately.")
sub("Statistical design")
para("For each outcome and sentiment method, simple OLS is followed by a controlled model with log issue price, log(1 + headline count) and a within-year listing-date trend. The package supports year indicators for multi-year extensions; no year effect can be estimated within this single-year sample. HC3 standard errors and t-based 95% confidence intervals are reported. Holm adjustment covers the four controlled sentiment coefficients. Correlations, simple regressions and sensitivity checks remain exploratory.")
para("The Parkinson measure is a daily high-low range proxy. It relies on assumptions about the price process and may be affected by opening price discovery, drift and market frictions. It is not tick-based realised volatility, and the classical efficiency comparison with close-to-close estimators should not be taken as a guarantee for IPO listing sessions.","SmallReport")

page()
heading("3. Main empirical results")
desc=sample[["listing_return_pct","parkinson_daily","finbert_score","lm_score"]]
names={"listing_return_pct":"Listing return (%)","parkinson_daily":"Daily Parkinson proxy","finbert_score":"FinBERT IPO score","lm_score":"LM IPO score"}
table(["Variable (N = 44)","Mean","Median","Std. dev."],[[names[c],fmt(desc[c].mean(),4),fmt(desc[c].median(),4),fmt(desc[c].std(),4)] for c in desc],[180,96,96,96])
para("The return distribution is wide, and sentiment also varies across IPOs. The Pearson association between FinBERT and return is positive, but association alone does not show whether the text adds useful predictive information. The controlled coefficients below use the same 44 IPOs for both methods.")
rows=[]
for r in primary.itertuples():
    rows.append(["FinBERT" if r.score.startswith("finbert") else "LM", "Return (%)" if r.target=="listing_return_pct" else "Daily proxy",fmt(r.coef,3),f"[{r.ci_low:.3f}, {r.ci_high:.3f}]",fmt(r.p,3),fmt(r.primary_p_holm,3)])
table(["Method","Outcome","Coefficient","95% HC3 CI","Raw p","Holm p"],rows,[58,76,74,150,54,56])
para("Coefficients are per one unit of the original sentiment score. The confidence intervals are pointwise intervals; they are not adjusted for the four-test family. A 0.1 increase in FinBERT score corresponds to an estimated "+f"{finreturn.coef*.1:.2f}"+" percentage-point increase in return, holding the specified controls fixed. Its pointwise interval just excludes zero, but the Holm-adjusted test does not pass the five per cent threshold.")
para("The return model's total R-squared is "+f"{finreturn.r2:.3f}"+" and adjusted R-squared is "+f"{finreturn.adjusted_r2:.3f}"+". These values describe the full specification, not the contribution of sentiment alone. LM estimates are imprecise and daily-proxy estimates provide little evidence of a stable relationship. This is not evidence that sentiment has exactly zero effect; it shows that this sample does not estimate those relationships precisely.")
if (RESULTS/"sentiment_outcomes.png").exists():
    page()
    heading("3. Main results: visual inspection")
    para("Each point below represents an IPO with eligible news and a verified listing-day price. Both panels use the same IPO-level FinBERT score. The scatter makes the dispersion visible; it does not adjust for company or date controls. The uncertainty around the controlled coefficients is reported on the preceding page.")
    story.append(Image(str(RESULTS/"sentiment_outcomes.png"),width=468,height=187.2))
    markdown.append("\n![Sentiment and outcomes](../results/sentiment_outcomes.png)")
    sub("Five highest listing returns in the analysed sample")
    top=sample.sort_values("listing_return_pct",ascending=False).head(5)
    table(["Symbol","Return (%)","FinBERT","LM"],[[r.symbol,fmt(r.listing_return_pct,2),fmt(r.finbert_score,3),fmt(r.lm_score,3)] for r in top.itertuples()],[180,96,96,96])
    para("These observations illustrate why the headline score should be interpreted alongside its coverage and the underlying news. A large listing return does not require an extreme sentiment score. The table is a descriptive view of the retained sample and is not used to select observations for the regression or to tune the prediction model.")

page()
heading("4. Chronological prediction check")
m=metric("finbert_score","listing_return_pct")
para(f"Prediction is evaluated separately from the full-sample regressions. The latest quarter of unique listing dates is held out, with same-date IPOs kept together. The split begins on 7 November 2023 and gives {m['n_train']} training IPOs and {m['n_test']} test IPOs. This is not a random split, and all three predictors are compared on identical test rows.")
para("The historical-mean predictor uses the training outcome mean. The controls-only predictor uses log issue price and log headline count. The third predictor adds one sentiment score. No future-year dummy or outcome-based feature selection is used. Because the test set is small, the errors are descriptive estimates rather than a precise ranking of forecasting methods.")
sub("Listing return: errors in percentage points")
f=metric("finbert_score","listing_return_pct")
l=metric("lm_score","listing_return_pct")
table(["Predictor","MAE","RMSE"],[
    ["Historical mean",fmt(f['historical_mean_mae'],2),fmt(f['historical_mean_rmse'],2)],
    ["Controls only",fmt(f['controls_mae'],2),fmt(f['controls_rmse'],2)],
    ["Controls + FinBERT",fmt(f['controls_sentiment_mae'],2),fmt(f['controls_sentiment_rmse'],2)],
    ["Controls + LM",fmt(l['controls_sentiment_mae'],2),fmt(l['controls_sentiment_rmse'],2)]
],[280,94,94])
sub("Daily Parkinson proxy: errors in daily units")
f=metric("finbert_score","parkinson_daily")
l=metric("lm_score","parkinson_daily")
table(["Predictor","MAE","RMSE"],[
    ["Historical mean",fmt(f['historical_mean_mae'],4),fmt(f['historical_mean_rmse'],4)],
    ["Controls only",fmt(f['controls_mae'],4),fmt(f['controls_rmse'],4)],
    ["Controls + FinBERT",fmt(f['controls_sentiment_mae'],4),fmt(f['controls_sentiment_rmse'],4)],
    ["Controls + LM",fmt(l['controls_sentiment_mae'],4),fmt(l['controls_sentiment_rmse'],4)]
],[280,94,94])
para("Neither sentiment method improves RMSE over the historical-mean baseline for either target. FinBERT slightly reduces return MAE relative to controls alone, but its return RMSE increases. LM gives especially unstable return predictions, which is consistent with its very sparse polarity coverage. The small holdout does not establish which approach would work best in a larger population.")

page()
heading("5. Measurement checks and sensitivity")
para(f"The LM dictionary contains no positive or negative match in {lmzero} of {len(articles)} retained headlines ({100*lmzero/len(articles):.1f}%). A zero polarity score therefore often reflects no matched polarity word. It should not automatically be interpreted as evidence that a headline is substantively neutral. The uncertainty category is stored separately and does not enter the primary polarity score.")
para("FinBERT produces more varied scores, including for headlines about subscriptions and anchor investment. However, this project does not have a manually labelled Indian IPO benchmark. More variation does not establish greater sentiment accuracy. A useful extension is independent annotation of a stratified sample, followed by macro-F1, agreement and error analysis before changing the measurement specification.")
sub("Exploratory return-coefficient checks")
s=sensitivity[sensitivity.score.eq("finbert_score")&sensitivity.target.eq("listing_return_pct")]
table(["Specification","N","FinBERT coef.","Raw p","Holm p"],[["14-day window" if r.sensitivity=="14_calendar_days" else "Exclude GMP / grey-market titles",r.n,fmt(r.coef,2),fmt(r.p,3),fmt(r.primary_p_holm,3)] for r in s.itertuples()],[220,38,90,60,60])
para("The shorter window weakens the return association. Removing headlines that explicitly mention GMP or grey-market prices leaves a positive coefficient, but it still does not pass the within-specification Holm adjustment. These are sensitivity checks, not additional primary discoveries. Their p-values are not adjusted across every exploratory choice in the project.")
sub("Influential observations and sparse text")
diag=pd.read_csv(RESULTS/"diagnostics.csv")
subdiag=diag[diag.score.eq("finbert_score")&diag.target.eq("listing_return_pct")&diag.specification.eq("controlled")].sort_values("cooks_distance",ascending=False).head(3)
table(["Largest Cook's distances: return model","Cook's D","Leverage"],[[r.symbol,fmt(r.cooks_distance,3),fmt(r.leverage,3)] for r in subdiag.itertuples()],[280,94,94])
para("These diagnostics identify rows that deserve source and model review. They do not justify removing IPOs solely because their outcomes are inconvenient. The full sample remains the primary specification. Ordinary HC3 inference does not account for all possible dependence between IPOs listed in the same market environment; a larger multi-year sample would support stronger time-block inference.")

page()
heading("6. Interpretation and limitations")
para("The clearest result is the difference between an in-sample relationship and forecasting value. FinBERT tone is positively associated with listing returns, but the adjusted test and holdout errors do not support a strong predictive claim. The LM comparison also shows why a finance-specific dictionary is not automatically informative for every financial text format: short IPO headlines can contain very few polarity words.")
para("The results do not identify a causal effect of journalism. Subscription demand, company quality, valuation, industry and grey-market expectations may influence both reporting and prices. Log issue price is an observable price-level control, not a complete measure of company size or valuation. News count may also be related to investor attention and should not be treated as an exogenous variable.")
table(["Limitation","Consequence"],[
    ["Feed-defined single-year sample","Results describe the included IPOs; omitted EQ issues and other years may behave differently."],
    ["Retrospective RSS retrieval","Search ranking, missing stories and updated content can affect the measured information set."],
    ["Strict company phrase","Reduces ambiguous matches but misses aliases and two IPOs entirely."],
    ["Headline-only text","Preserves a consistent unit, but omits detail and can misread context or irony."],
    ["No local sentiment gold labels","FinBERT classification accuracy on Indian IPO news is not established."],
    ["Sparse LM polarity matches","Estimates can be unstable and zero scores require careful interpretation."],
    ["Contemporary measurement tools","Current model and dictionary vintages prevent claims of a historically certified trading strategy."],
    ["Small holdout and shared market shocks","Test errors and conventional regression uncertainty do not establish general market performance."]
],[148,320])
para("A non-significant sentiment coefficient is not proof of semi-strong market efficiency. Market efficiency concerns risk-adjusted opportunities and the information set available to investors. An allotted investor's issue-to-close return is also different from a strategy available to someone buying after the listing opens. These questions require a broader design, allocation assumptions and trading-cost treatment.")
para("The next research extension should expand the independently verified IPO universe, add pre-listing company and market controls, validate sentiment labels and preserve a genuinely untouched later-year evaluation set. It should retain the same auditable date rules and document any change before comparing outcomes.")

page()
heading("7. Reproduction and validation")
para("The repository separates source inputs, article measurement, IPO-level analysis, prediction checks and reporting. Frozen input tables make the reported estimates reproducible without relying on a new historical search. Source collection scripts are also provided, although future downloads can legitimately change the retrieval snapshot.")
table(["Research component","Implementation and checks"],[
    ["Pre-listing information window","Local timestamp screening before any sentiment aggregation"],
    ["Listing-day identification","Exact date, symbol and EQ-series checks in official bhavcopies"],
    ["Price verification","Nominal exchange OHLC with source URL, ISIN and issue-price cross-check"],
    ["Sentiment measurement","Contextual FinBERT and official LM comparison on identical headlines"],
    ["Statistical inference","HC3 intervals and a declared four-test Holm family"],
    ["Prediction evaluation","Chronological held-out predictions against simple baselines"],
    ["Interpretation","Separate conclusions about association, prediction and market efficiency"],
    ["Reproducibility","Reusable package, notebook, tests, CI and report generated from results"]
],[224,244])
sub("Run the study")
para("Install the package with its FinBERT extra, download the authors' official dictionary, then run the command in README.md with the bundled data/research inputs and a new output directory. The notebook provides the same steps for local Jupyter and Colab. The source ZIP includes the code, input tables, frozen results and report; model weights are downloaded separately.")
para("The run manifest records input SHA-256 hashes, package versions, the dictionary hash and the immutable model revision. Nine offline tests check date and timezone boundaries, price matching, duplicate handling, missing news coverage, dictionary-category removal and whole-date holdout splitting. A synthetic demonstration tests the software without supplying research evidence.")
sub("Measurement provenance")
para("FinBERT revision: "+manifest['finbert_revision'],"SmallReport")
para("LM dictionary SHA-256: "+manifest['lm_dictionary_sha256'],"SmallReport")
para("The model and dictionary are third-party research resources. Their terms are listed in THIRD_PARTY_NOTICES.md. The project code is licensed separately.","SmallReport")

page()
heading("References and source access")
refs=[
    ("Araci, D. (2019). FinBERT: Financial Sentiment Analysis with Pre-trained Language Models. arXiv:1908.10063.","https://arxiv.org/abs/1908.10063"),
    ("Loughran, T., and McDonald, B. (2011). When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks. Journal of Finance, 66(1), 35-65.","https://sraf.nd.edu/loughranmcdonald-master-dictionary/"),
    ("Parkinson, M. (1980). The Extreme Value Method for Estimating the Variance of the Rate of Return. Journal of Business, 53(1), 61-65.","https://doi.org/10.1086/296071"),
    ("ProsusAI. FinBERT model card, architecture, label mapping and usage terms. Accessed 29 October 2026.","https://huggingface.co/ProsusAI/finbert"),
    ("University of Notre Dame SRAF. Loughran-McDonald Master Dictionary, 1993-2025 edition. Accessed 29 October 2026; official spreadsheet CSV export used when the direct CSV link reached its quota.","https://sraf.nd.edu/loughranmcdonald-master-dictionary/"),
    ("National Stock Exchange of India. Past public issues feed and dated equity bhavcopies. Retrieved 29 October 2026; exact URLs and hashes in data/research/sources.json.","https://www.nseindia.com/all-reports"),
    ("Google News RSS and named publishers. Historical headline metadata retrieved 29 October 2026. Individual publisher names, publication timestamps and article links are retained in the corpus.","https://news.google.com/"),
    ("statsmodels. Robust covariance results documentation: HC3 and t-based inference. Accessed 29 October 2026.","https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html")
]
for text,url in refs:
    para(escape(text),"BodyReport")
    para(f'<link href="{escape(url)}" color="#157a86">Source link</link>',"SmallReport")
    markdown.append(url)
sub("Data and code accompanying this report")
para("The project release contains the reusable Python package, notebook, frozen input metadata, complete exclusion audits, regression and holdout tables, sensitivity outputs and this report. Every empirical number in the report is read from the saved result tables. Synthetic fixtures are stored separately and do not contribute to the reported estimates.")

def footer(canvas,doc):
    canvas.saveState()
    canvas.setFont("Helvetica",8)
    canvas.setFillColor(colors.HexColor("#60737c"))
    canvas.drawString(63,34,"IPO sentiment | 2023 NSE study")
    canvas.drawRightString(532,34,str(doc.page))
    canvas.restoreState()

pdf=OUT/"report.pdf"
doc=SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=63,rightMargin=64.28,topMargin=54,bottomMargin=54,
                      title="Financial news sentiment and Indian IPO outcomes",author="Naseef E. P.")
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/"report.md").write_text("\n\n".join(markdown),encoding="utf8")
print(pdf)
