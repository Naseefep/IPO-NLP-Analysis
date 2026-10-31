"""Generate a multi-year project report from frozen empirical outputs."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
OUT=ROOT/'reports'
OUT.mkdir(exist_ok=True)
panel=pd.read_csv(R/'analysis_panel.csv')
panel['listing_date']=pd.to_datetime(panel.listing_date)
panel['year']=panel.listing_date.dt.year
sample=panel[panel.article_count.gt(0)]
articles=pd.read_csv(R/'article_scores.csv')
coeff=pd.read_csv(R/'coefficients.csv')
primary=coeff[coeff.term.eq(coeff.score)&coeff.specification.eq('controlled')]
correlations=pd.read_csv(R/'correlations.csv')
sensitivity=pd.read_csv(R/'sensitivity.csv')
diagnostics=pd.read_csv(R/'diagnostics.csv')
manifest=json.loads((R/'manifest.json').read_text(encoding='utf8'))
metrics=json.loads((R/'holdout_metrics.json').read_text(encoding='utf8'))
config=json.loads((ROOT/'data/research/collection_config.json').read_text(encoding='utf8'))
frame=pd.read_csv(ROOT/'data/research/sampling_frame.csv')
coverage=pd.read_csv(R/'yearly_coverage.csv').set_index('listing_year')
queries=pd.read_csv(ROOT/'data/research/query_log.csv')
zero=int(articles.lm_coverage.eq(0).sum())
significant=primary[primary.primary_p_holm.lt(.05)]

def row(score,target):
    return primary[primary.score.eq(score)&primary.target.eq(target)].iloc[0]
def metric(score,target):
    return next(m for m in metrics if m['score']==score and m['target']==target)
fret=row('finbert_score','listing_return_pct')
fm=metric('finbert_score','listing_return_pct')
lm=metric('lm_score','listing_return_pct')
fvol=metric('finbert_score','parkinson_daily')
lvol=metric('lm_score','parkinson_daily')
test_improves=fm['controls_sentiment_rmse']<fm['historical_mean_rmse']
verdict=(f"{len(significant)} of the four controlled sentiment tests {'passes' if len(significant)==1 else 'pass'} the Holm-adjusted five per cent threshold."
         if len(significant) else 'None of the four controlled sentiment tests passes the Holm-adjusted five per cent threshold.')
forecast=("FinBERT's return model has lower 2026 test RMSE than the historical-mean baseline in this sample."
          if test_improves else "FinBERT's return model does not improve 2026 test RMSE over the historical-mean baseline in this sample.")

styles=getSampleStyleSheet()
for name,size,leading,color in [('TitleProject',28,34,'#15364a'),('SubtitleProject',14,20,'#386074'),('BodyProject',10.3,15,'#172b36'),('SmallProject',8.2,11.5,'#334e5c'),('CellProject',8.1,10.7,'#172b36'),('AppendixCell',7.5,9.3,'#172b36')]:
    styles.add(ParagraphStyle(name=name,fontName='Helvetica-Bold' if name=='TitleProject' else 'Helvetica',fontSize=size,leading=leading,textColor=colors.HexColor(color),spaceAfter=10 if 'Cell' not in name else 0))
styles['Heading1'].fontSize=18
styles['Heading1'].leading=23
styles['Heading1'].spaceAfter=15
styles['Heading1'].textColor=colors.HexColor('#15364a')
styles['Heading2'].fontSize=12
styles['Heading2'].spaceBefore=9
styles['Heading2'].spaceAfter=8
story=[]
md=[]
def para(text,style='BodyProject'):
    story.append(Paragraph(text,styles[style]))
    md.append(text.replace('<b>','**').replace('</b>','**').replace('<br/>','\n'))
def heading(text):
    story.append(Paragraph(text,styles['Heading1']))
    md.append('\n## '+text)
def sub(text):
    story.append(Paragraph(text,styles['Heading2']))
    md.append('\n### '+text)
def page():
    story.append(PageBreak())
def table(headers,rows,widths,compact=False):
    style=styles['AppendixCell' if compact else 'CellProject']
    data=[[Paragraph(escape(str(x)),style) for x in headers]]+[[Paragraph(escape(str(x)),style) for x in values] for values in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3eef3')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),4 if compact else 7),('BOTTOMPADDING',(0,0),(-1,-1),4 if compact else 7),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f8fa')])]))
    story.extend([t,Spacer(1,11)])
    md.append('| '+' | '.join(map(str,headers))+' |\n|'+'---|'*len(headers))
    md.extend('| '+' | '.join(map(str,values))+' |' for values in rows)
def fig(name,height=175):
    story.append(Image(str(R/name),width=468,height=height))
    story.append(Spacer(1,9))
    md.append(f'![Research figure](../results/{name})')
def num(value,digits=3):
    return f'{value:.{digits}f}'

para('Financial News Sentiment<br/>and IPO Listing-Day<br/>Performance','TitleProject')
para('Evidence from NSE mainboard IPOs, 2020-2026','SubtitleProject')
story.append(Spacer(1,20))
para('PROJECT REPORT','SubtitleProject')
para('Naseef E. P.<br/>31 October 2026')
story.append(Spacer(1,27))
table(['Period','Verified IPOs','IPOs analysed','Eligible headlines'],[[f"2020-2026 YTD",len(panel),len(sample),len(articles)]],[118,116,116,118])
para('A comparative study of contextual FinBERT sentiment and the Loughran-McDonald financial dictionary, using dated pre-listing news headlines and official exchange prices.')
para('2026 coverage is year to date, with a collection cutoff of 31 October 2026. The sample is defined from the available NSE past-issues feed and should not be read as a census of every Indian IPO.','SmallProject')
story.append(Spacer(1,20))
sub('Report structure')
para('Abstract; introduction and objectives; literature review; sample design; data collection and verification; measurement and empirical strategy; descriptive results; regression results; 2026 prediction test; sensitivity and diagnostics; discussion and conclusion; reproduction guide; references; annual IPO and news-count appendices.','SmallProject')

page()
heading('Abstract')
para(f"This project examines whether financial news sentiment before an IPO is associated with its listing-day performance on the National Stock Exchange of India. The dataset covers {len(panel)} price-verified mainboard IPOs listed between 2020 and 2026, with 2026 observed only up to the collection cutoff. Date-stratified selection targets up to 25 verified IPOs per year, while retaining all eligible candidates in smaller years. Historical news is retrieved through multiple issuer-name and date-window searches. After local timestamp, relevance and duplicate checks, {len(articles):,} distinct headline observations remain for {len(sample)} IPOs. Headlines are scored separately with ProsusAI FinBERT and the official Loughran-McDonald dictionary. Company sentiment is the equal-weighted mean of the eligible headline scores.")
para('The two outcomes are the listing-day closing return relative to the issue price and the daily Parkinson high-low proxy. Controlled OLS includes log issue price, log headline count, listing-year indicators and a within-year date trend. HC3 standard errors and a four-test Holm correction are used for the primary sentiment coefficients. A separate calendar holdout fits prediction models on pre-2026 IPOs and tests them on the available 2026 IPOs.')
para(f"The controlled FinBERT return coefficient is {fret.coef:.3f}, with an unadjusted p-value of {fret.p:.4f} and a Holm-adjusted p-value of {fret.primary_p_holm:.4f}. {verdict} {forecast} LM matches no positive or negative word in {zero:,} of {len(articles):,} retained headlines, which limits the resolution of its polarity measure.")
para('The results distinguish text measurement, in-sample association and out-of-sample prediction. They do not identify a causal effect of media coverage and do not, by themselves, establish market efficiency or a profitable trading strategy. The main contribution is a reproducible multi-year comparison with explicit price verification, news-date screening and year-wise coverage reporting.')
para('Keywords: initial public offerings; NSE; financial news; FinBERT; Loughran-McDonald; listing return; sentiment analysis; reproducibility.','SmallProject')

page()
heading('1. Introduction and research objectives')
para('An initial public offering allows a company to offer its shares to public investors before exchange trading begins. The difference between the issue price and the first closing price can be substantial. Financial reporting before listing discusses the business, valuation, subscription demand, risks and expected market reception. This creates a measurable question: does the tone of that reporting help explain the first trading day?')
para('The question requires care because favourable news may reflect information that investors already know. News may also be written in response to subscription demand or grey-market expectations. A positive relationship between news tone and a listing gain would therefore be an association, rather than evidence that the reporting caused the gain.')
sub('Problem statement')
para('A general sentiment dictionary may miss finance-specific meaning, while a contextual model may interpret a headline more flexibly. At the same time, a sophisticated model cannot repair a news corpus containing articles published after the outcome. This project studies both the measurement choice and the information window, across different listing years.')
table(['Objective','How it is addressed'],[
    ['Cover different market periods','Select IPOs from each year from 2020 through 2026 YTD, using listing dates before outcomes are analysed.'],
    ['Build an auditable information set','Match official listing-day prices and retain only relevant, distinct pre-listing headlines.'],
    ['Compare sentiment measures','Score the same headlines with FinBERT and LM, retaining probabilities and dictionary coverage.'],
    ['Test association and prediction','Estimate controlled regressions and evaluate a separate 2026 chronological test set.'],
    ['Make the study reproducible','Publish source code, input metadata, exclusion records, tables, figures and the report.']
],[140,328])
sub('Research hypotheses')
para('H1: pre-listing headline sentiment is associated with the issue-to-close listing return. H2: pre-listing sentiment is associated with the daily high-low volatility proxy. Both are tested against zero-coefficient null hypotheses using two-sided tests. Four controlled sentiment tests arise because each hypothesis is evaluated with two sentiment methods.')

page()
heading('2. Review of relevant literature')
para('Textual analysis in finance connects language with information, expectations and market activity. The literature also shows that the appropriate method depends on the document type and the research objective. A model that classifies textual tone accurately does not necessarily forecast returns accurately.')
table(['Study','Contribution and relevance'],[
    ['Loughran and McDonald (2011)','Using US 10-K filings, the authors show that a general dictionary misclassifies common financial language. Their financial word lists provide an interpretable domain-specific benchmark.'],
    ['Araci (2019)','FinBERT adapts BERT to financial language and reports strong performance on financial sentiment benchmarks. This work is associated with the ProsusAI checkpoint used here.'],
    ['Huang, Wang and Yang (2023)','Their FinBERT implementation outperforms LM and several alternatives on labelled analyst-report sentences, supporting contextual financial text modelling. It is a different implementation from the Prosus model.'],
    ['Parkinson (1980)','The high-low price range provides a variance estimator under a particular price-process model. Here it supplies a daily range-based proxy when tick data are unavailable.']
],[150,318])
para('For short headlines, context can change the interpretation of individual words. A statement that losses have narrowed contains a negative word but may describe improvement. FinBERT can use the surrounding wording, while LM records matches to a fixed vocabulary. This gives a reason to use contextual sentiment as the primary measurement approach and retain LM as a transparent comparison.')
para('However, the cited benchmark results do not validate either method on Indian IPO headlines. This project has no independent local gold-standard sentiment labels. The comparison therefore reports coverage, score behaviour and economic associations without claiming a measured classification-accuracy advantage in this corpus.')
para('The multi-year design addresses variation across listing periods. It also separates the explanatory regressions from the later-year prediction test. Neither design establishes a causal response to media tone, since company characteristics and investor demand may affect reporting and prices together.')

page()
heading('3. Research design and annual sample')
para('The unit of economic analysis is one IPO. Headlines are measured individually and then aggregated within the IPO. The sampling frame consists of EQ issues from the NSE past-issues response with listing dates from 2020 to the 2026 cutoff. Offer opening must precede listing by no more than 90 days; this helps reject later exchange migrations or inconsistent date records.')
para('Within each year, the collector targets up to 25 IPOs at evenly spaced ranks in the chronological listing-date order. If a selected record fails price verification, the remaining chronological candidates serve as reserves. No return, sentiment score, p-value or observed headline count is used to choose the original date strata. Missing news does not cause an IPO to be silently replaced.')
year_rows=[]
for year in range(2020,2027):
    c=coverage.loc[year]
    year_rows.append([str(year)+(' YTD' if year==2026 else ''),int(frame.year.eq(year).sum()),int(c.verified_ipos),int(c.ipos_with_news),int(c.eligible_headlines),num(c.median_headlines,1)])
table(['Year','Eligible frame','Verified IPOs','With news','Headlines','Median / IPO'],year_rows,[60,80,82,76,82,88])
para(f"The resulting panel has {len(panel)} verified IPOs and {len(sample)} IPOs with eligible headlines. Price-only observations remain visible in the panel and appendices but are excluded from sentiment regressions. The sample is larger than a fixed ten-per-year design while preserving representation from each available year.")
para('The annual counts are not population weights. Because the target is similar across years, a year with many IPOs contributes a smaller sampled fraction than a quieter year. The pooled estimates describe this sampled panel, not an average over every Indian IPO issued during the period.','SmallProject')

page()
heading('4. Data collection and quality controls')
sub('Official financial data')
para('Listing-day prices are read from dated NSE bhavcopies. The collector supports both the legacy format and the UDiFF format used for later dates. It requires an exact trading-date match and one EQ-series identity match. Official symbol-change records allow documented ticker renames to be followed; the historic bhavcopy symbol and ISIN are retained.')
para('The final issue price in the NSE issue feed must agree with the first-day reference-price field to within INR 0.005. Open, high, low and close must be finite, positive and internally consistent. These checks protect the return calculation from using a modern split-adjusted quote against the original issue price. A neighbouring trading date is never substituted.')
sub('Historical news discovery')
para(f"The collection uses {queries.query_id.nunique():,} distinct dated queries, including full issuer names, declared distinctive aliases and split-window searches. Additional short-name queries use prefixes unique within the eligible issuer frame, plus documented abbreviations. Publisher names, original RSS URLs, query identifiers, retrieval records and source-response hashes are retained. The analysis uses headlines, not full article bodies.")
rejections=manifest['news_rejections']
rows=[['Raw candidate rows',manifest['counts']['news_input']],['Eligible distinct headlines',len(articles)]]
rows += [[reason.replace('_',' ').capitalize(),count] for reason,count in rejections.items() if reason]
table(['Screening stage / first rejection reason','Number of rows'],rows,[340,128])
para('A headline must fall in the local pre-listing window, match a declared issuer name or alias, contain IPO, and have a source and URL. Identical URLs or normalised headline text are deduplicated within each IPO. Publisher suffixes are removed before title comparison. The audit gives each excluded row its first rejection reason, so counts should not be read as overlapping categories.')
para('Retrospective RSS searches can miss older articles, repeat syndicated reporting or expose updated metadata. Extra queries improve retrieval coverage, but do not turn the corpus into a complete archive or guarantee independent observations.','SmallProject')

page()
heading('5. Sentiment and outcome measurement')
para('The primary information window is the 30 calendar days immediately before listing-day midnight in Asia/Kolkata. Dates with timezone offsets are converted to local time. Naive dates are interpreted locally, and all listing-day items are excluded, including those recorded only by calendar date.')
table(['Variable','Definition and interpretation'],[
    ['FinBERT headline score','P(positive) minus P(negative). All three label probabilities are saved; the score is textual tone, not a probability of a future price gain.'],
    ['LM headline score','Positive-token count minus negative-token count, divided by all alphabetic tokens. Only active positive/negative category flags are used.'],
    ['LM coverage and uncertainty','Polarity-word matches divided by tokens; uncertainty matches are recorded separately. No polarity match is not proof of substantive neutrality.'],
    ['IPO-level sentiment','Equal-weighted mean of the eligible article scores within each IPO. No eligible headlines gives missing sentiment.'],
    ['Listing return (%)','100 x (listing-day close / issue price - 1). This is the allottee issue-to-close return, expressed in percentage points.'],
    ['Parkinson daily proxy','ln(high / low) / sqrt(4 x ln(2)), without annualisation. It measures the day\'s price range under the estimator\'s assumptions.']
],[142,326])
para('Headline wording is retained for contextual inference: there is no stopword removal or stemming before FinBERT. If text exceeds the model capacity, it is divided into token chunks and class probabilities are averaged. IPO aggregation gives each headline equal weight, rather than allowing a single long text to dominate the company score.')
para('The dictionary is the official 1993-2025 master edition downloaded from the authors. FinBERT uses an immutable model revision. Both vintages are recorded in the run manifest. Applying contemporary measurement tools to older news makes this a retrospective text-measurement study; it is not a certified simulation of the exact model and data available to traders in 2020.')

page()
heading('6. Empirical strategy')
sub('Association models')
para('For each outcome and sentiment method, the project estimates a simple OLS regression and a controlled regression. The controlled specification is:')
para('Outcome = intercept + sentiment + log(issue price) + log(1 + headline count) + listing-year indicators + within-year listing-date trend.','SmallProject')
para('Year indicators allow the average outcome to differ across listing periods. The within-year trend is day of year divided by 365.25. Log issue price controls for an observable price level, not firm size or valuation in a complete economic sense. Headline count accounts partly for variation in measured attention, although it may itself be endogenous.')
para('Standard errors use HC3 and t-based pointwise 95% confidence intervals. Singular designs, inadequate residual degrees of freedom and unit-leverage cases are rejected rather than reported as valid inference. The four controlled sentiment coefficients form the primary Holm-adjustment family: two methods multiplied by two outcomes. Correlations and simple regressions are exploratory.')
sub('Predeclared 2026 prediction test')
para(f"The prediction split is 1 January 2026. Models are fitted using only earlier IPOs and evaluated on the {fm['n_test']} covered IPOs listed in 2026; {fm['n_train']} covered IPOs form the training sample. This keeps whole listing dates together. No 2026 outcome is used to estimate the prediction coefficients.")
para('Three predictions are compared on identical test rows: the historical training mean, a controls-only OLS model, and the same controls plus one sentiment score. Forecasting controls are log issue price and log headline count. Future-year dummy coefficients are not estimated. Mean absolute error and root mean squared error are reported for both outcomes.')
sub('Sensitivity and dependence')
para('Exploratory checks use a 14-day window, exclude explicitly named GMP or grey-market headlines, require at least five eligible headlines per IPO, and exclude 2026 from association estimation. HC3 handles heteroskedasticity, but does not remove omitted variables or all possible dependence among IPOs exposed to common market shocks.')

page()
heading('7. Descriptive findings')
labels={'listing_return_pct':'Listing return (%)','parkinson_daily':'Daily Parkinson proxy','finbert_score':'FinBERT IPO sentiment','lm_score':'LM IPO sentiment','article_count':'Headlines per IPO'}
table(['Variable: covered IPOs','N','Mean','Median','Std. dev.'],[[label,len(sample),num(sample[key].mean(),4),num(sample[key].median(),4),num(sample[key].std(),4)] for key,label in labels.items()],[184,40,82,82,80])
fig('yearly_coverage.png',168.5)
para('The coverage chart separates the verified financial panel from the subset with eligible news. News counts are the distinct headline observations after filtering, rather than the raw number of search results. A missing-news IPO is not assigned a neutral score. This distinction matters when comparing quieter and more heavily reported listing years.')
para('The range of issue-to-close returns and the distribution of company sentiment should be considered before reading a single coefficient. Descriptive annual differences can reflect the selected sample, issuer mix, market conditions and retrieval coverage. They are not a census-based comparison of annual IPO market performance.')

page()
heading('8. Distributions and visual relationships')
fig('descriptive_distributions.png',168.5)
para('The return boxplots show dispersion within the sampled listing years. FinBERT company scores are the mean of pre-listing headlines. These figures describe the data and do not control for differences in issue price, headline count or listing year.')
fig('sentiment_outcomes.png',168.5)
para('Each scatter point represents one covered IPO; colours identify listing years. The two panels use the same sentiment score with different outcomes. A visible relationship in a pooled scatter can partly reflect between-year composition. The controlled regressions and the separate prediction test provide the more specific comparisons below.')
para('There is no rule that adding headlines must strengthen a relationship or make a p-value smaller. Extra observations are useful when they improve measurement and coverage; repeated or irrelevant observations can instead obscure the information of interest.','SmallProject')

page()
heading('9. Primary regression results')
rows=[]
for r in primary.itertuples():
    rows.append(['FinBERT' if r.score=='finbert_score' else 'LM','Return (%)' if r.target=='listing_return_pct' else 'Daily proxy',num(r.coef),f'[{r.ci_low:.3f}, {r.ci_high:.3f}]',num(r.p,4),num(r.primary_p_holm,4)])
table(['Method','Outcome','Coefficient','95% HC3 CI','Raw p','Holm p'],rows,[57,74,76,145,58,58])
para(f"{verdict} The controlled FinBERT return estimate is {fret.coef:.3f}. A 0.1-unit increase in its score corresponds to an estimated {fret.coef*.1:.2f} percentage-point difference in return, holding the stated controls fixed. The coefficient's pointwise interval is [{fret.ci_low:.3f}, {fret.ci_high:.3f}] per one score unit. These intervals are not simultaneous multiplicity-adjusted intervals.")
para(f"For the controlled FinBERT return model, total R-squared is {fret.r2:.3f} and adjusted R-squared is {fret.adjusted_r2:.3f}. This describes the complete specification; it is not the fraction explained by sentiment alone. The larger set of year controls also consumes degrees of freedom, so adjusted fit and uncertainty matter alongside raw fit.")
sub('Exploratory correlations')
table(['Method','Outcome','Pearson r','Pearson p','Spearman r'],[['FinBERT' if r.score=='finbert_score' else 'LM','Return (%)' if r.target=='listing_return_pct' else 'Daily proxy',num(r.pearson_r),num(r.pearson_p,4),num(r.spearman_r)] for r in correlations.itertuples()],[76,104,96,96,96])
para('The correlation table does not control for year or other variables and its p-values are not part of the primary Holm family. Comparing a correlation with a controlled coefficient can reveal how sensitive the pooled relationship is to observable differences, but does not establish why the relationship changes.')

page()
heading('10. Prediction on 2026 IPOs')
para(f"The pre-2026 training group contains {fm['n_train']} IPOs and the 2026 test group contains {fm['n_test']}. All predictors for a given outcome are evaluated on the same companies. 2026 is a partial year, and this held-out period should not be treated as a complete future market cycle.")
sub('Issue-to-close return: errors in percentage points')
table(['Predictor','MAE','RMSE'],[
    ['Historical training mean',num(fm['historical_mean_mae'],2),num(fm['historical_mean_rmse'],2)],
    ['Controls only',num(fm['controls_mae'],2),num(fm['controls_rmse'],2)],
    ['Controls + FinBERT',num(fm['controls_sentiment_mae'],2),num(fm['controls_sentiment_rmse'],2)],
    ['Controls + LM',num(lm['controls_sentiment_mae'],2),num(lm['controls_sentiment_rmse'],2)]
],[280,94,94])
sub('Daily Parkinson proxy: errors in daily units')
table(['Predictor','MAE','RMSE'],[
    ['Historical training mean',num(fvol['historical_mean_mae'],4),num(fvol['historical_mean_rmse'],4)],
    ['Controls only',num(fvol['controls_mae'],4),num(fvol['controls_rmse'],4)],
    ['Controls + FinBERT',num(fvol['controls_sentiment_mae'],4),num(fvol['controls_sentiment_rmse'],4)],
    ['Controls + LM',num(lvol['controls_sentiment_mae'],4),num(lvol['controls_sentiment_rmse'],4)]
],[280,94,94])
para(forecast+' MAE and RMSE may rank predictors differently because RMSE places greater weight on large errors. The tables give error magnitudes, rather than a test of profitable trading after allocation constraints, risk adjustment and transaction costs.')
para('The test design improves separation between fitting and evaluation, but historical search retrieval and contemporary text-model vintages still prevent a claim that these are fully point-in-time investable forecasts. A further later-year test would be needed after the measurement and specification are fixed.')

page()
heading('11. Sensitivity and diagnostic checks')
sub('Controlled return coefficients: exploratory specifications')
names={'14_calendar_days':'14-day window','exclude_gmp':'Exclude GMP titles','minimum_5_headlines':'At least 5 headlines','exclude_2026':'2020-2025 only'}
selected=sensitivity[sensitivity.target.eq('listing_return_pct')]
table(['Specification','Method','N','Coefficient','Holm p'],[[names.get(r.sensitivity,r.sensitivity),'FinBERT' if r.score=='finbert_score' else 'LM',r.n,num(r.coef,2),num(r.primary_p_holm,4)] for r in selected.itertuples()],[172,70,40,100,86])
para('The complete sensitivity table also includes the daily range outcome. Holm adjustment is applied within each specification, not across every exploratory analysis. These checks should be read as evidence about stability; the project does not select the most favourable specification as its final result.')
sub('Influential observations: primary FinBERT return model')
diag=diagnostics[diagnostics.score.eq('finbert_score')&diagnostics.target.eq('listing_return_pct')&diagnostics.specification.eq('controlled')].sort_values('cooks_distance',ascending=False).head(4)
table(['Symbol','Cook\'s distance','Leverage'],[[r.symbol,num(r.cooks_distance,3),num(r.leverage,3)] for r in diag.itertuples()],[240,114,114])
para('Cook\'s distance and leverage identify observations that warrant review of the source and specification. They are not grounds to remove a large or inconvenient return after observing it. The untrimmed sample remains the primary analysis.')

page()
heading('12. News coverage and measurement limits')
para(f"LM has no active positive or negative token match in {zero:,} of {len(articles):,} headlines ({100*zero/len(articles):.1f}%). This is a coverage finding, not a measured error rate. Zero-match headlines may convey information about subscriptions, anchors or valuations without using the dictionary's polarity vocabulary.")
publishers=articles.source.value_counts().head(8)
table(['Largest publisher labels in the retained RSS corpus','Headlines'],[[name,count] for name,count in publishers.items()],[350,118])
para('The RSS publisher label is retained as received. Some labels can refer to brands or sections rather than a harmonised publisher identity. The project therefore does not present these counts as a comprehensive measure of media-market concentration. Syndicated stories with materially different titles can remain after exact deduplication.')
para(f"Across covered IPOs, the median headline count is {sample.article_count.median():.1f}, with a range from {int(sample.article_count.min())} to {int(sample.article_count.max())}. Company sentiment based on one or two headlines is less well measured than sentiment based on a richer corpus. The minimum-five-headline sensitivity addresses part of this problem, although it may favour larger or more prominent offerings.")
para('The broader collection adds observations across years, but differences in retrieval success are not random. Older reporting may be less discoverable, and the exact-alias rule can miss brand-only headlines. These limitations are made visible through per-IPO counts, query logs and missing-coverage records rather than hidden by assigning neutral values.')

page()
heading('13. Discussion, conclusion and further work')
para(f"The project brings together a multi-year financial panel and a dated headline corpus to compare contextual and dictionary sentiment. {verdict} {forecast} These are the conclusions for the specified sample and models; they should not be generalised to every IPO or every form of financial text.")
para('The contextual and dictionary approaches measure different aspects of language. FinBERT uses the surrounding wording, while LM makes its word-level mechanism easy to inspect. Dictionary sparsity can weaken its resolution on short headlines. But the project cannot declare a local accuracy winner without independent human labels for this corpus.')
para('The economic relationship remains observational. Subscription demand, issue characteristics, sector exposure and market conditions can influence both reporting and the listing outcome. Issue price and headline count are limited controls. Pre-listing market returns, issue size, valuation, sector indicators and subscription data would improve the design if collected with equivalent timing checks.')
para('A null coefficient is not proof of semi-strong market efficiency. Conversely, an adjusted significant coefficient would not by itself establish an exploitable trading strategy. Issue-to-close gains depend on receiving an IPO allocation, and the model does not account for allocation probabilities, financing constraints, risk-adjusted benchmarks or trading costs.')
sub('Priorities for further research')
para('First, obtain a timestamped archive or licensed news source to assess retrieval completeness. Second, independently label a sample of headlines and evaluate agreement, macro-F1 and domain-specific mistakes. Third, collect stronger pre-listing controls and use larger later-year tests. Fourth, examine time-block dependence and robustness with more complete annual samples. These extensions should be specified before comparing results.')
para('The reproducible contribution is practical: every included IPO has a documentary price source; every candidate headline has a timestamp and an inclusion decision; both sentiment methods use the same retained corpus; and the report is generated from the saved results.')

page()
heading('14. Reproduction and project organisation')
table(['Location','Purpose'],[
    ['data/research/','Frozen IPO, price and news inputs; complete sampling frame, declared aliases, query logs and source hashes.'],
    ['src/iposent/','Validation, headline measurement, IPO aggregation, association models and chronological predictions.'],
    ['scripts/','Source collection, alias enrichment, sensitivity checks, figures, report generation and release packaging.'],
    ['results/','Article scores, price/news audits, per-IPO counts, yearly coverage, coefficients, diagnostics and test predictions.'],
    ['notebooks/ipo_sentiment.ipynb','A local Jupyter and Colab walkthrough that loads the public repository automatically.'],
    ['tests/ and .github/workflows/','Offline regression checks and continuous integration without model downloads.']
],[176,292])
para('Open the notebook through the repository\'s Open in Colab link and save a copy to Drive. Run the setup cell, inspect the frozen results, install the package and dictionary, then run the analysis. The notebook uses a fresh output directory, so it does not mix new outputs with the published snapshot.')
para('For a command-line reproduction, install the FinBERT extra, obtain the official dictionary, and run the command in README.md using the three data/research input CSVs, --model both and --holdout-from 2026-01-01. Live source collection is optional; published inputs provide the frozen study and may differ from future search results.')
para('The offline tests cover date/timezone boundaries, exact price dates, OHLC validation, duplicates including publisher suffixes, missing news, removed dictionary flags, date-stratified sampling, declared aliases and chronological holdouts. The verification script checks input hashes, class probabilities, per-year coverage and train/test dates.')
para('FinBERT revision: '+manifest['finbert_revision'],'SmallProject')
para('LM CSV SHA-256: '+manifest['lm_dictionary_sha256'],'SmallProject')
para('Model weights and the dictionary are not redistributed in the source ZIP. Their original terms remain applicable; see THIRD_PARTY_NOTICES.md. Original project code has its own MIT license.','SmallProject')

page()
heading('References and source access')
refs=[
 ('Araci, D. (2019). FinBERT: Financial Sentiment Analysis with Pre-trained Language Models. arXiv:1908.10063.','https://arxiv.org/abs/1908.10063'),
 ('Huang, A. H., Wang, H., and Yang, Y. (2023). FinBERT: A Large Language Model for Extracting Information from Financial Text. Contemporary Accounting Research, 40(2), 806-841.','https://doi.org/10.1111/1911-3846.12832'),
 ('Loughran, T., and McDonald, B. (2011). When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks. Journal of Finance, 66(1), 35-65.','https://doi.org/10.1111/j.1540-6261.2010.01625.x'),
 ('Parkinson, M. (1980). The Extreme Value Method for Estimating the Variance of the Rate of Return. Journal of Business, 53(1), 61-65.','https://doi.org/10.1086/296071'),
 ('ProsusAI. FinBERT model card, label mapping and usage terms. Immutable revision recorded in the manifest.','https://huggingface.co/ProsusAI/finbert'),
 ('Notre Dame SRAF. Loughran-McDonald Master Dictionary, 1993-2025 edition. Official source and academic-use information.','https://sraf.nd.edu/loughranmcdonald-master-dictionary/'),
 ('National Stock Exchange of India. Public past-issues feed, symbol-change records and dated equity bhavcopies. Exact URLs, query parameters and source hashes accompany the dataset.','https://www.nseindia.com/all-reports'),
 ('Google News RSS and named publishers. Historical headline metadata. Article timestamps, publisher labels and URLs are retained in the input and audit files.','https://news.google.com/'),
 ('statsmodels. OLS robust covariance documentation, including HC3 and t-based inference.','https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html')
]
for text,url in refs:
    para(escape(text),'SmallProject')
    para(f'<link href="{escape(url)}" color="#157a86">Source link</link>','SmallProject')
    md.append(url)

for year in range(2020,2027):
    page()
    heading(f'Appendix: {year} IPOs and news coverage'+(' (YTD)' if year==2026 else ''))
    annual=panel[panel.year.eq(year)].sort_values('listing_date')
    para(f"{len(annual)} verified IPOs; {int(annual.article_count.gt(0).sum())} with eligible news; {int(annual.article_count.sum()):,} distinct headline observations. A zero count means the IPO is retained in the price panel but excluded from sentiment regressions.",'SmallProject')
    rows=[]
    for r in annual.itertuples():
        company=r.company if len(r.company)<=45 else r.company[:42]+'...'
        rows.append([company,r.symbol,str(r.listing_date.date()),int(r.article_count),num(r.listing_return_pct,2)])
    table(['Company (shortened where needed)','Symbol','Listing date','Headlines','Return (%)'],rows,[180,80,78,60,70],compact=True)
    para('Full company names, source URLs, original headline metadata and both sentiment scores are available in the accompanying CSVs. Returns are in percentage points and are not annualised.','SmallProject')

def footer(canvas,doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#60737c'))
    canvas.setFont('Helvetica',8)
    canvas.drawString(63,33,'IPO sentiment | NSE mainboard | 2020-2026 YTD')
    canvas.drawRightString(532,33,str(doc.page))
    canvas.restoreState()

doc=SimpleDocTemplate(str(OUT/'report.pdf'),pagesize=(595.28,841.89),leftMargin=63,rightMargin=64.28,topMargin=52,bottomMargin=53,
                      title='Financial News Sentiment and IPO Listing-Day Performance: 2020-2026',author='Naseef E. P.')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'report.md').write_text('\n\n'.join(md),encoding='utf8')
print(OUT/'report.pdf')
