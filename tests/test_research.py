import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from iposent.data import validate_ipos, price_features, filter_news
from iposent.sentiment import LoughranMcDonald, aggregate
from iposent.analysis import holdout


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.ipos = validate_ipos(pd.DataFrame([dict(symbol="ABC", company="ABC Ltd", listing_date="2024-02-01", issue_price=100)]))

    def news(self, times):
        return pd.DataFrame([dict(symbol="ABC", headline=f"News item {i}", published_at=t, source="Test", url=f"https://example.invalid/{i}", relevance_verified=True) for i,t in enumerate(times)])

    def test_timezone_cutoff(self):
        # 18:30 UTC is midnight in India. Date-only listing-day news is excluded.
        n = self.news(["2024-01-31T18:29:59Z", "2024-01-31T18:30:00Z", "2024-02-01", "bad", "2023-12-01"])
        keep, audit = filter_news(self.ipos, n, 30)
        self.assertEqual(len(keep), 1)
        self.assertEqual(audit.rejection.tolist(), ["", "at_or_after_cutoff", "at_or_after_cutoff", "invalid_timestamp", "before_window"])

    def test_missing_coverage_stays_missing(self):
        agg = aggregate(pd.DataFrame(columns=["symbol", "lm_score"]))
        panel = self.ipos.merge(agg, on="symbol", how="left")
        self.assertTrue(pd.isna(panel.lm_score.iloc[0]))

    def test_dedup_and_relevance(self):
        n = self.news(["2024-01-30"]*4)
        n.loc[1,"headline"] = "NEWS item 0!!!"
        n.loc[2,"url"] = n.loc[0,"url"]
        n.loc[3,"relevance_verified"] = False
        keep, audit = filter_news(self.ipos,n)
        self.assertEqual(len(keep),1)
        self.assertEqual((audit.rejection=="duplicate").sum(),2)

    def prices(self):
        return pd.DataFrame([dict(symbol="ABC", observed_date="2024-02-01", open=110, high=125, low=105, close=120, quote_basis="listing_day_nominal", verified=True, source_url="https://example.invalid/price")])

    def test_returns_and_daily_volatility(self):
        d = price_features(self.ipos,self.prices()).iloc[0]
        self.assertAlmostEqual(d.listing_return_pct,20)
        self.assertAlmostEqual(d.parkinson_daily,np.log(125/105)/np.sqrt(4*np.log(2)))

    def test_wrong_date_never_falls_back(self):
        p=self.prices()
        p.loc[0,"observed_date"]="2024-02-02"
        d=price_features(self.ipos,p).iloc[0]
        self.assertEqual(d.price_rejection,"wrong_or_missing_date")
        self.assertTrue(pd.isna(d.listing_return_pct))

    def test_unverified_prices_and_bad_ranges(self):
        p=self.prices()
        p.loc[0,"verified"]=False
        self.assertEqual(price_features(self.ipos,p).price_rejection.iloc[0],"unverified_price")
        p=self.prices()
        p.loc[0,"high"]=100
        self.assertEqual(price_features(self.ipos,p).price_rejection.iloc[0],"inconsistent_ohlc")

    def test_removed_lm_entries(self):
        tmp=Path(__file__).resolve().parents[1]/"tmp"
        tmp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp) as td:
            path=Path(td)/"toy.csv"
            pd.DataFrame([dict(Word="GAIN",Positive=2009,Negative=0),dict(Word="OLD",Positive=0,Negative=-2020),dict(Word="LOSS",Positive=0,Negative=2009)]).to_csv(path,index=False)
            result=LoughranMcDonald(path).score(["gain old loss gain"]).iloc[0]
            self.assertEqual(result.lm_positive,2)
            self.assertEqual(result.lm_negative,1)
            self.assertEqual(result.lm_score,.25)

    def test_duplicate_ipo_rejected(self):
        with self.assertRaises(ValueError):
            validate_ipos(pd.concat([self.ipos,self.ipos]))

    def test_holdout_keeps_whole_dates(self):
        rng=np.random.default_rng(4)
        dates=pd.date_range("2023-01-01",periods=20,freq="7D").repeat(2)
        d=pd.DataFrame(dict(symbol=[f"D{i}" for i in range(40)],listing_date=dates,issue_price=rng.uniform(10,500,40),article_count=rng.integers(1,10,40),lm_score=rng.normal(size=40),listing_return_pct=rng.normal(size=40)))
        metric,pred=holdout(d,"lm_score","listing_return_pct")
        self.assertEqual(metric["status"],"ok")
        cutoff=pd.Timestamp(metric["cutoff"])
        self.assertTrue((pred.listing_date>=cutoff).all())
        self.assertTrue((d[d.listing_date<cutoff].listing_date.max()<pred.listing_date.min()))
        self.assertAlmostEqual(pred.historical_mean.iloc[0],d[d.listing_date<cutoff].listing_return_pct.mean())


if __name__=="__main__":
    unittest.main()
