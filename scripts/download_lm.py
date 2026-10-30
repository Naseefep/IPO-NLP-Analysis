"""Fetch the official academic LM CSV linked from Notre Dame SRAF.

Source page: https://sraf.nd.edu/loughranmcdonald-master-dictionary/
Source download ID verified on 29 October 2026. Distribution terms remain those
of the authors. This script does not grant rights or bundle their dictionary.
"""
from pathlib import Path
import requests


if __name__=="__main__":
    path=Path("data/lexicons/Loughran-McDonald_MasterDictionary_1993-2025.csv")
    path.parent.mkdir(parents=True,exist_ok=True)
    response=requests.get("https://drive.usercontent.google.com/download",params={"export":"download","id":"1iq2RUf8qGFEAk1g8wQntP3habOnR3fXF","confirm":"t"},timeout=90)
    response.raise_for_status()
    if b"word" not in response.content[:500].lower():
        # Official alternate XLSX link also exposes a complete CSV export.
        response=requests.get("https://docs.google.com/spreadsheets/d/1P3KtWuDyQT2Eu_VwTU3D2sEeQxR9dWCS/export?format=csv",timeout=90)
        response.raise_for_status()
    if b"word" not in response.content[:500].lower() or b"positive" not in response.content[:1000].lower():
        raise ValueError("The download is not the expected master dictionary CSV")
    path.write_bytes(response.content)
    print(path,len(response.content))
