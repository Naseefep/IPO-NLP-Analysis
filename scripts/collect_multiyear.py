"""Collect a date-stratified NSE EQ IPO sample, 2020-2026 (2026 year to date).

Sampling uses listing dates only, before news scoring or return calculation.
Nominal OHLC must match official bhavcopy identity/date and the issue price.
All candidate news is audited later; search date clauses are not trusted alone.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from iposent.data import clean_text, normalise_headline


def company_aliases(company):
    """Deterministic full/short name variants, preserving distinctive phrases."""
    name=re.sub(r"\s+(limited|ltd\.?)$","",company,flags=re.I).strip()
    aliases=[name]
    for pattern in [r"\s+technologies$",r"\s+technology$",r"\s+industries$",r"\s+international$",
                    r"\s+corporation$",r"\s+finance corporation$",r"\s+and payment services$",
                    r"\s+food specialities$",r"\s+hospital\s*(?:and trauma care services)?$"]:
        short=re.sub(pattern,"",name,flags=re.I).strip()
        if len(short)>=6 and short!=name:
            aliases.append(short)
    # Named brands already present in the official issuer name, not fuzzy matches.
    if name.lower().startswith("sbi cards"):
        aliases.extend(["SBI Cards","SBI Card"])
    if name.lower().startswith("mrs. bectors"):
        aliases.extend(["Mrs Bectors","Mrs. Bectors","Bectors Food"])
    if name.lower().startswith("yatharth hospital"):
        aliases.append("Yatharth Hospital")
    if name.lower().startswith("signatureglobal"):
        aliases.extend(["Signature Global","Signatureglobal"])
    if name.lower().startswith("rr kabel"):
        aliases.append("RR Kabel")
    return list(dict.fromkeys(aliases))


def sampling_order(rows,target):
    """Evenly spaced dates first, followed by deterministic gap-filling reserves."""
    rows=sorted(rows,key=lambda r:(r["_date"],r["symbol"]))
    chosen=list(dict.fromkeys(np.linspace(0,len(rows)-1,min(target,len(rows))).round().astype(int)))
    remaining=[i for i in range(len(rows)) if i not in chosen]
    return [(i in chosen, rows[i]) for i in chosen+remaining]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-per-year",type=int,default=25)
    parser.add_argument("--as-of",default="2026-10-31")
    parser.add_argument("--output",default="data/multiyear")
    args=parser.parse_args()
    if args.target_per_year<10:
        parser.error("Use at least 10 as the annual target")
    raw=ROOT/"data/raw/collection2020_2026"
    out=ROOT/args.output
    raw.mkdir(parents=True,exist_ok=True)
    out.mkdir(parents=True,exist_ok=True)
    session=requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0","Accept-Language":"en-IN,en;q=0.9"})
    session.mount("https://",HTTPAdapter(max_retries=Retry(total=2,backoff_factor=.7,status_forcelist=[429,500,502,503,504])))
    provenance={}
    def get(url,key,params=None):
        file=raw/key
        if file.exists():
            content=file.read_bytes()
        else:
            response=session.get(url,params=params,timeout=30)
            response.raise_for_status()
            content=response.content
            file.write_bytes(content)
            time.sleep(.35)
        provenance[key]=dict(file=file.relative_to(ROOT).as_posix(),url=url,params=params,
                             sha256=hashlib.sha256(content).hexdigest())
        return content
    universe_url="https://www.nseindia.com/api/public-past-issues?category=equities&type=all"
    universe=json.loads(get(universe_url,"nse_past_issues.json"))
    change_url="https://nsearchives.nseindia.com/content/equities/symbolchange.csv"
    changes=None
    try:
        changes=pd.read_csv(io.BytesIO(get(change_url,"symbolchange.csv")))
        changes.columns=changes.columns.str.strip()
        print("Symbol-change columns",changes.columns.tolist(),flush=True)
    except Exception as exc:
        print("Symbol-change feed unavailable:",str(exc)[:120],flush=True)
    eligible=[]
    asof=pd.Timestamp(args.as_of)
    universe_audit=[]
    for row in universe:
        if row.get("securityType")!="EQ":
            continue
        try:
            day=pd.to_datetime(row.get("listingDate"),format="%d-%b-%Y")
            opening=pd.to_datetime(row.get("ipoStartDate"),format="%d-%b-%Y")
            if pd.isna(day) or pd.isna(opening) or not 2020<=day.year<=2026 or day>asof:
                continue
            if not 0<=(day-opening).days<=90:
                universe_audit.append(dict(symbol=row['symbol'],listing_date=str(day.date()),reason="offer_to_listing_gap_over_90_days_or_negative"))
                continue
            issue=float(str(row["issuePrice"]).replace(",","").strip())
            if not np.isfinite(issue) or issue<=0:
                raise ValueError("invalid issue price")
            eligible.append({**row,"_date":day,"_open":opening,"_issue":issue})
        except (TypeError,ValueError):
            continue
    # Preserve the full eligible sampling frame, including unselected rows.
    frame=pd.DataFrame([dict(symbol=r['symbol'],company=r.get('company',r.get('companyName')),
                              listing_date=str(r['_date'].date()),year=r['_date'].year,issue_price=r['_issue']) for r in eligible])
    frame=frame.drop_duplicates(["symbol","listing_date"]).sort_values(["year","listing_date","symbol"])
    frame.to_csv(out/"sampling_frame.csv",index=False)
    unique={}
    for r in eligible:
        unique.setdefault((r['symbol'],r['_date']),r)
    eligible=list(unique.values())
    ipos,prices,news,exclusions,queries,selection=[],[],[],[],[],[]
    def listing_symbols(symbol):
        aliases={symbol}
        if changes is not None:
            previous=next((c for c in changes if 'old' in c.lower() and 'symbol' in c.lower()),None)
            current=next((c for c in changes if 'new' in c.lower() and 'symbol' in c.lower()),None)
            if previous and current:
                for _ in range(5):
                    for _,change in changes.iterrows():
                        old,new=str(change[previous]).strip(),str(change[current]).strip()
                        if old in aliases or new in aliases:
                            aliases.update([old,new])
        return aliases
    def checkpoint():
        pd.DataFrame(ipos).to_csv(out/"ipos.csv",index=False)
        pd.DataFrame(prices).to_csv(out/"prices.csv",index=False)
        pd.DataFrame(news,columns=["symbol","headline","published_at","source","url","relevance_verified","relevance_method","matched_alias","retrieval_source","query_id"]).to_csv(out/"news.csv",index=False)
        pd.DataFrame(exclusions,columns=["symbol","year","stage","reason"]).to_csv(out/"collection_exclusions.csv",index=False)
        pd.DataFrame(queries).to_csv(out/"query_log.csv",index=False)
        pd.DataFrame(selection).to_csv(out/"selection_audit.csv",index=False)
        pd.DataFrame(universe_audit,columns=["symbol","listing_date","reason"]).to_csv(out/"universe_exclusions.csv",index=False)
        (out/"sources.json").write_text(json.dumps(list(provenance.values()),indent=2),encoding="utf8")
        (out/"collection_config.json").write_text(json.dumps(dict(start_year=2020,end_year=2026,as_of=args.as_of,target_per_year=args.target_per_year,
            sampling="evenly spaced listing-date ranks, with next chronological candidates as price-verification reserves",
            news_window_calendar_days=30,query_strategy="full issuer name, distinctive aliases, plus two half-window searches",
            minimum_news_requirement="none at sampling; missing coverage retained in IPO panel",retrieved_utc=datetime.now(timezone.utc).isoformat()),indent=2),encoding="utf8")
    for year in range(2020,2027):
        rows=[r for r in eligible if r['_date'].year==year]
        print("YEAR",year,"eligible",len(rows),"target",min(args.target_per_year,len(rows)),flush=True)
        obtained=0
        for primary,row in sampling_order(rows,args.target_per_year):
            if obtained>=args.target_per_year:
                break
            symbol=row['symbol']
            day=row['_date']
            company=row.get('company',row.get('companyName'))
            issue=row['_issue']
            try:
                modern=day>=pd.Timestamp("2024-07-08")
                if modern:
                    url=f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{day.strftime('%Y%m%d')}_F_0000.csv.zip"
                else:
                    url=f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{year}/{day.strftime('%b').upper()}/cm{day.strftime('%d%b%Y').upper()}bhav.csv.zip"
                content=get(url,day.strftime('%Y%m%d')+".zip")
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    table=pd.read_csv(z.open(next(n for n in z.namelist() if n.lower().endswith('.csv'))),low_memory=False)
                table.columns=table.columns.str.strip()
                aliases=listing_symbols(symbol)
                if modern:
                    match=table[table.TckrSymb.astype(str).str.strip().isin(aliases)&table.SctySrs.astype(str).str.strip().eq("EQ")]
                    mapping=dict(date="TradDt",open="OpnPric",high="HghPric",low="LwPric",close="ClsPric",prev="PrvsClsgPric",isin="ISIN",symbol="TckrSymb")
                else:
                    match=table[table.SYMBOL.astype(str).str.strip().isin(aliases)&table.SERIES.astype(str).str.strip().eq("EQ")]
                    mapping=dict(date="TIMESTAMP",open="OPEN",high="HIGH",low="LOW",close="CLOSE",prev="PREVCLOSE",isin="ISIN",symbol="SYMBOL")
                if len(match)!=1:
                    raise ValueError("not exactly one official symbol/rename and EQ-series match")
                q=match.iloc[0]
                observed=pd.to_datetime(q[mapping['date']])
                if observed.date()!=day.date():
                    raise ValueError("bhavcopy date mismatch")
                if abs(float(q[mapping['prev']])-issue)>.005:
                    raise ValueError(f"issue price {issue} differs from first-day reference {q[mapping['prev']]}")
                o,h,l,c=[float(q[mapping[k]]) for k in ['open','high','low','close']]
                if not all(np.isfinite(v) and v>0 for v in [o,h,l,c]) or not l<=min(o,c)<=max(o,c)<=h:
                    raise ValueError("invalid or inconsistent OHLC")
                ipos.append(dict(symbol=symbol,company=company,listing_date=str(day.date()),issue_price=issue,year=year,
                                  issue_open_date=str(row['_open'].date()),issue_close_date=str(pd.to_datetime(row['ipoEndDate'],format='%d-%b-%Y').date()),
                                  universe_source=universe_url,sampling_rank="primary_date_stratum" if primary else "reserve_after_price_exclusion"))
                prices.append(dict(symbol=symbol,observed_date=str(day.date()),open=o,high=h,low=l,close=c,quote_basis="listing_day_nominal",verified=True,
                                    source_url=url,isin=q[mapping['isin']],previous_close=q[mapping['prev']],bhavcopy_symbol=q[mapping['symbol']]))
                obtained+=1
                selection.append(dict(symbol=symbol,year=year,listing_date=str(day.date()),primary_stratum=primary,status="price_verified"))
            except Exception as exc:
                exclusions.append(dict(symbol=symbol,year=year,stage="price",reason=str(exc)))
                selection.append(dict(symbol=symbol,year=year,listing_date=str(day.date()),primary_stratum=primary,status="price_excluded"))
                print(year,symbol,"PRICE EXCLUDED",str(exc)[:140],flush=True)
                checkpoint()
                continue
            aliases=company_aliases(company)
            begin=pd.Timestamp(day.to_pydatetime()-timedelta(days=30))
            middle=pd.Timestamp(day.to_pydatetime()-timedelta(days=15))
            searches=[(aliases[0],begin,day,"full")]
            if len(aliases)>1:
                searches.append((aliases[-1],begin,day,"alias"))
            searches.extend([(aliases[-1],begin,middle,"first_half"),(aliases[-1],middle,day,"second_half")])
            count=0
            for phrase,start,end,label in searches:
                query=f'"{phrase}" IPO after:{start.date()} before:{end.date()}'
                params=dict(q=query,hl="en-IN",gl="IN",ceid="IN:en")
                query_id=hashlib.sha256(query.encode()).hexdigest()[:16]
                try:
                    xml=get("https://news.google.com/rss/search",query_id+".xml",params)
                    items=ET.fromstring(xml).findall('.//item')
                    for item in items:
                        title=clean_text(item.findtext('title',''))
                        normalized=normalise_headline(title)
                        alias=next((a for a in aliases if re.search(r'\b'+re.escape(normalise_headline(a))+r'\b',normalized)),"")
                        relevant=bool(alias and re.search(r'\bipo\b',normalized))
                        news.append(dict(symbol=symbol,headline=title,published_at=item.findtext('pubDate',''),source=item.findtext('source','Google News RSS'),
                                         url=item.findtext('link',''),relevance_verified=relevant,relevance_method="declared_issuer_alias_and_ipo",
                                         matched_alias=alias,retrieval_source="Google News RSS",query_id=query_id))
                    queries.append(dict(symbol=symbol,year=year,query_id=query_id,label=label,query=query,count=len(items),status="ok"))
                    count+=len(items)
                except Exception as exc:
                    exclusions.append(dict(symbol=symbol,year=year,stage="news_query",reason=str(exc)))
                    queries.append(dict(symbol=symbol,year=year,query_id=query_id,label=label,query=query,count=0,status=str(exc)))
            print(year,f"{obtained:02d}",symbol,"verified;",count,"news candidates",flush=True)
            checkpoint()
        print("YEAR COMPLETE",year,"verified",obtained,flush=True)
    checkpoint()
    print("COLLECTION COMPLETE",len(ipos),"IPOs",len(news),"news candidates before filtering/deduplication",flush=True)


if __name__=="__main__":
    main()
