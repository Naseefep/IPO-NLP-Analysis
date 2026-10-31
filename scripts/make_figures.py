"""Research figures from the saved multi-year analysis panel."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results'
panel=pd.read_csv(out/'analysis_panel.csv')
panel['year']=pd.to_datetime(panel.listing_date).dt.year
articles=pd.read_csv(out/'article_scores.csv')
covered=panel[panel.article_count.gt(0)]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})

coverage=panel.groupby('year').agg(prices=('symbol','size'),news=('article_count',lambda x:x.gt(0).sum()),headlines=('article_count','sum'))
fig,axes=plt.subplots(1,2,figsize=(10,3.6))
coverage[['prices','news']].rename(columns={'prices':'Verified IPOs','news':'IPOs with eligible news'}).plot.bar(ax=axes[0],color=['#15364a','#22a2a8'],rot=0)
axes[0].set(xlabel='Listing year',ylabel='Number of IPOs',title='Coverage by year')
axes[0].legend(fontsize=8)
axes[1].bar(coverage.index.astype(str),coverage.headlines,color='#157a86')
axes[1].set(xlabel='Listing year',ylabel='Eligible distinct headlines',title='News retained after screening')
fig.tight_layout()
fig.savefig(out/'yearly_coverage.png',dpi=180)
plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(10,3.6))
years=sorted(covered.year.unique())
axes[0].boxplot([covered.loc[covered.year.eq(y),'listing_return_pct'] for y in years],patch_artist=True,
               boxprops={'facecolor':'#c9e4e8'},medianprops={'color':'#15364a'},flierprops={'markersize':3})
axes[0].set_xticks(range(1,len(years)+1),[str(y) for y in years])
axes[0].axhline(0,color='#9ba9b0',lw=1)
axes[0].set(xlabel='Listing year',ylabel='Issue-to-close return (%)',title='Return dispersion in the sampled IPOs')
axes[1].hist(covered.finbert_score,bins=18,color='#157a86',alpha=.9)
axes[1].set(xlabel='IPO-level FinBERT score',ylabel='Number of IPOs',title='Pre-listing contextual sentiment')
fig.tight_layout()
fig.savefig(out/'descriptive_distributions.png',dpi=180)
plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(10,3.6))
for ax,target,label in zip(axes,['listing_return_pct','parkinson_daily'],['Listing return (%)','Daily Parkinson proxy']):
    scatter=ax.scatter(covered.finbert_score,covered[target],c=covered.year,cmap='viridis',alpha=.75,s=24)
    ax.set(xlabel='IPO-level FinBERT score',ylabel=label)
fig.colorbar(scatter,ax=axes.ravel().tolist(),label='Listing year',fraction=.025,pad=.025)
fig.subplots_adjust(left=.08,right=.89,bottom=.18,wspace=.35,top=.94)
fig.savefig(out/'sentiment_outcomes.png',dpi=180)
plt.close(fig)

articles.source.value_counts().head(8).rename_axis('publisher').reset_index(name='headlines').to_csv(out/'publisher_coverage.csv',index=False)
print('Saved multi-year research figures')
