"""Add declared, unique issuer-name prefixes to historical headline discovery.

This uses only issuer names and dates, never outcomes or model scores. Original
candidate rows are preserved. The analysis applies time/relevance/dedup rules.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ET
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from iposent.data import clean_text,normalise_headline
from collect_multiyear import company_aliases


def unique_aliases(ipos):
    names={r.symbol:normalise_headline(r.company) for r in ipos.itertuples()}
    result={}
    for r in ipos.itertuples():
        aliases=company_aliases(r.company)
        words=re.findall(r"[A-Za-z0-9]+",re.sub(r"\s+(limited|ltd\.?)$","",r.company,flags=re.I))
        for length in [3,2]:
            phrase=' '.join(words[:length])
            if len(words)>length and len(phrase)>=8:
                normalized=normalise_headline(phrase)
                matches=[symbol for symbol,name in names.items() if re.search(r'\b'+re.escape(normalized)+r'\b',name)]
                if matches==[r.symbol]:
                    aliases.append(phrase)
        if r.company.lower().startswith('uti asset management'):
            aliases.append('UTI AMC')
        if r.company.lower().startswith('life insurance corporation'):
            aliases.append('LIC')
        result[r.symbol]=list(dict.fromkeys(aliases))
    return result


def main():
    out=ROOT/'data/multiyear'
    raw=ROOT/'data/raw/collection2020_2026'
    ipos=pd.read_csv(out/'ipos.csv')
    frame=pd.read_csv(out/'sampling_frame.csv')
    # Uniqueness is checked against the full eligible frame, not just sampled IPOs.
    alias_map=unique_aliases(frame.drop_duplicates('symbol'))
    news=pd.read_csv(out/'news.csv').to_dict('records')
    sources=json.loads((out/'sources.json').read_text(encoding='utf8'))
    source_keys={row['file']:row for row in sources}
    queries=pd.read_csv(out/'query_log.csv').to_dict('records')
    declared=[]
    session=requests.Session()
    session.headers['User-Agent']='Mozilla/5.0'
    session.mount('https://',HTTPAdapter(max_retries=Retry(total=2,backoff_factor=.7,status_forcelist=[429,500,502,503,504])))
    def checkpoint():
        pd.DataFrame(news).to_csv(out/'news.csv',index=False)
        pd.DataFrame(queries).drop_duplicates(['symbol','query_id'],keep='last').to_csv(out/'query_log.csv',index=False)
        pd.DataFrame(declared).to_csv(out/'issuer_aliases.csv',index=False)
        (out/'sources.json').write_text(json.dumps(list(source_keys.values()),indent=2),encoding='utf8')
    for r in ipos.itertuples():
        aliases=alias_map[r.symbol]
        for phrase in aliases:
            declared.append(dict(symbol=r.symbol,company=r.company,alias=phrase,method='official_issuer_name_or_unique_prefix_or_declared_abbreviation'))
        additional=[a for a in aliases if a not in company_aliases(r.company)]
        day=pd.Timestamp(r.listing_date)
        start=day-pd.Timedelta(days=30)
        # At most two distinct additional aliases; no article-count-driven selection.
        for phrase in additional[-2:]:
            query=f'"{phrase}" IPO after:{start.date()} before:{day.date()}'
            key=hashlib.sha256(query.encode()).hexdigest()[:16]
            path=raw/(key+'.xml')
            params=dict(q=query,hl='en-IN',gl='IN',ceid='IN:en')
            try:
                if not path.exists():
                    response=session.get('https://news.google.com/rss/search',params=params,timeout=30)
                    response.raise_for_status()
                    path.write_bytes(response.content)
                    time.sleep(.4)
                content=path.read_bytes()
                items=ET.fromstring(content).findall('.//item')
                source_keys[path.relative_to(ROOT).as_posix()]=dict(file=path.relative_to(ROOT).as_posix(),url='https://news.google.com/rss/search',params=params,sha256=hashlib.sha256(content).hexdigest())
                for item in items:
                    news.append(dict(symbol=r.symbol,headline=clean_text(item.findtext('title','')),published_at=item.findtext('pubDate',''),source=item.findtext('source','Google News RSS'),url=item.findtext('link',''),
                                     relevance_verified=False,relevance_method='declared_issuer_alias_and_ipo',matched_alias='',retrieval_source='Google News RSS',query_id=key))
                queries.append(dict(symbol=r.symbol,year=r.year,query_id=key,label='unique_issuer_alias',query=query,count=len(items),status='ok'))
            except Exception as exc:
                queries.append(dict(symbol=r.symbol,year=r.year,query_id=key,label='unique_issuer_alias',query=query,count=0,status=str(exc)))
        print(r.year,r.symbol,'declared aliases',len(aliases),'additional searches',len(additional[-2:]),flush=True)
        checkpoint()
    for row in news:
        normalized=normalise_headline(row['headline'])
        alias=next((a for a in alias_map[row['symbol']] if re.search(r'\b'+re.escape(normalise_headline(a))+r'\b',normalized)),'')
        row['matched_alias']=alias
        row['relevance_verified']=bool(alias and re.search(r'\bipo\b',normalized))
        row['relevance_method']='declared_issuer_alias_and_ipo'
    config=json.loads((out/'collection_config.json').read_text())
    config.update(supplementary_alias_protocol='up to two extra unique issuer-prefix/declared-abbreviation queries, selected before scoring',
                  supplementary_retrieved_utc=datetime.now(timezone.utc).isoformat())
    (out/'collection_config.json').write_text(json.dumps(config,indent=2),encoding='utf8')
    checkpoint()
    print('ENRICHMENT COMPLETE',len(news),'candidate rows including duplicates',flush=True)


if __name__=='__main__':
    main()
