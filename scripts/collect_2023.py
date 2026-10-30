"""Collect an explicitly bounded 2023 NSE mainboard sample from public sources.

Universe is the current NSE past-issues feed, NOT a certified full 2023 census.
Only EQ issues opened and listed in 2023 are eligible. Prices must match the
official listing-date bhavcopy, including issue-price == PREVCLOSE.
RSS headlines are retained by a documented exact company-phrase + IPO rule.
No full article text is copied. Search results remain retrospective, incomplete.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from iposent.data import clean_text, normalise_headline

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/"data/raw/collection2023"
OUT = ROOT/"data/research"


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    s=requests.Session()
    s.headers["User-Agent"]="Mozilla/5.0"
    provenance=[]
    def get(url, key, params=None):
        path=RAW/key
        if path.exists():
            content=path.read_bytes()
        else:
            r=s.get(url,params=params,timeout=40)
            r.raise_for_status()
            content=r.content
            path.write_bytes(content)
            time.sleep(.5)
        provenance.append(dict(file=str(path.relative_to(ROOT)),url=url,params=params,sha256=hashlib.sha256(content).hexdigest()))
        return content
    universe_url="https://www.nseindia.com/api/public-past-issues?category=equities&type=all"
    universe=json.loads(get(universe_url,"nse_past_issues.json"))
    eligible=[r for r in universe if r.get("securityType")=="EQ" and str(r.get("listingDate","")).endswith("2023") and str(r.get("ipoStartDate","")).endswith("2023")]
    ipos, prices, news, exclusions=[],[],[],[]
    for row in sorted(eligible,key=lambda r:pd.to_datetime(r["listingDate"],format="%d-%b-%Y")):
        symbol=row["symbol"]
        date=pd.to_datetime(row["listingDate"],format="%d-%b-%Y")
        issue=float(row["issuePrice"])
        company=row.get("company",row.get("companyName"))
        url=f"https://nsearchives.nseindia.com/content/historical/EQUITIES/2023/{date.strftime('%b').upper()}/cm{date.strftime('%d%b%Y').upper()}bhav.csv.zip"
        try:
            content=get(url,date.strftime("%Y%m%d")+".zip")
            z=zipfile.ZipFile(io.BytesIO(content))
            table=pd.read_csv(z.open(next(n for n in z.namelist() if n.endswith('.csv'))))
            match=table[table.SYMBOL.eq(symbol)&table.SERIES.eq("EQ")]
            if len(match)!=1:
                raise ValueError("not exactly one symbol/EQ match")
            quote=match.iloc[0]
            if pd.to_datetime(quote.TIMESTAMP).date()!=date.date():
                raise ValueError("bhavcopy date mismatch")
            if abs(float(quote.PREVCLOSE)-issue)>.005:
                raise ValueError("issue price differs from listing-day PREVCLOSE")
            ipos.append(dict(symbol=symbol,company=company,listing_date=str(date.date()),issue_price=issue,
                              issue_open_date=str(pd.to_datetime(row['ipoStartDate'],format='%d-%b-%Y').date()),
                              issue_close_date=str(pd.to_datetime(row['ipoEndDate'],format='%d-%b-%Y').date()),universe_source=universe_url))
            prices.append(dict(symbol=symbol,observed_date=str(date.date()),open=quote.OPEN,high=quote.HIGH,low=quote.LOW,close=quote.CLOSE,
                               quote_basis="listing_day_nominal",verified=True,source_url=url,isin=quote.ISIN,previous_close=quote.PREVCLOSE))
        except Exception as exc:
            exclusions.append(dict(symbol=symbol,stage="price",reason=str(exc)))
            print(symbol,"PRICE EXCLUDED",str(exc),flush=True)
            continue
        phrase=re.sub(r"\s+(limited|ltd\.?)$","",company,flags=re.I).strip()
        start=date-pd.Timedelta(days=30)
        params={"q":f'"{phrase}" IPO after:{start.date()} before:{date.date()}',"hl":"en-IN","gl":"IN","ceid":"IN:en"}
        try:
            xml=get("https://news.google.com/rss/search",symbol+".xml",params)
            items=ET.fromstring(xml).findall(".//item")
            accepted=0
            for item in items:
                title=clean_text(item.findtext("title", ""))
                normal=normalise_headline(title)
                relevant=(normalise_headline(phrase) in normal) and bool(re.search(r"\bipo\b",normal))
                news.append(dict(symbol=symbol,headline=title,published_at=item.findtext("pubDate", ""),source=item.findtext("source", "Google News RSS"),url=item.findtext("link", ""),
                                 relevance_verified=relevant,relevance_method="exact_company_phrase_and_ipo",retrieval_source="Google News RSS"))
                accepted+=int(relevant)
            print(symbol,"prices verified",len(items),"RSS candidates",accepted,"phrase matches",flush=True)
        except Exception as exc:
            exclusions.append(dict(symbol=symbol,stage="news",reason=str(exc)))
            print(symbol,"NEWS ERROR",str(exc),flush=True)
    pd.DataFrame(ipos).to_csv(OUT/"ipos.csv",index=False)
    pd.DataFrame(prices).to_csv(OUT/"prices.csv",index=False)
    pd.DataFrame(news).to_csv(OUT/"news.csv",index=False)
    pd.DataFrame(exclusions,columns=["symbol","stage","reason"]).to_csv(OUT/"collection_exclusions.csv",index=False)
    (OUT/"sources.json").write_text(json.dumps(provenance,indent=2),encoding="utf8")
    print("Collected",len(ipos),"price-verified IPOs and",len(news),"news candidates",flush=True)


if __name__=="__main__":
    main()
