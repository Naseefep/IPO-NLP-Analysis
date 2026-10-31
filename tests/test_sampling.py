import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from collect_multiyear import company_aliases,sampling_order


class SamplingTests(unittest.TestCase):
    def test_strata_span_the_year_before_reserves(self):
        rows=[dict(symbol=f"A{i}",_date=pd.Timestamp('2024-01-01')+pd.Timedelta(days=10*i)) for i in range(30)]
        order=sampling_order(rows,10)
        primary=[r for selected,r in order if selected]
        self.assertEqual(len(primary),10)
        self.assertEqual(primary[0]['symbol'],'A0')
        self.assertEqual(primary[-1]['symbol'],'A29')
        self.assertEqual(len({r['symbol'] for _,r in order}),30)

    def test_small_year_keeps_every_eligible_ipo(self):
        rows=[dict(symbol=f"B{i}",_date=pd.Timestamp('2020-01-01')+pd.Timedelta(days=i)) for i in range(12)]
        self.assertEqual(sum(flag for flag,_ in sampling_order(rows,25)),12)

    def test_aliases_are_explicit_and_distinctive(self):
        self.assertIn('SBI Card',company_aliases('SBI Cards and Payment Services Limited'))
        self.assertIn('Signature Global',company_aliases('Signatureglobal (India) Limited'))
        self.assertNotIn('India',company_aliases('Signatureglobal (India) Limited'))


if __name__=='__main__':
    unittest.main()
