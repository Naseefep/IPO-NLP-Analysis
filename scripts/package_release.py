"""Build a small source/data/report ZIP with an explicit allowlist."""
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
out=ROOT.parent/"ipo-sentiment-research.zip"
folders=["src","tests","scripts","docs","notebooks","reports","results",".github","data/research","data/templates","data/demo"]
files=["README.md","LICENSE","THIRD_PARTY_NOTICES.md","pyproject.toml","requirements-lock.txt",".gitignore",".gitattributes","data/lexicons/README.md","data/raw/.gitkeep"]
paths=[ROOT/name for name in files]
for folder in folders:
    paths.extend(p for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc")
with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(set(paths)):
        z.write(path,Path(ROOT.name)/path.relative_to(ROOT))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert all(not any(part in name.split('/') for part in [".venv",".cache","original"]) for name in names)
    assert ROOT.name+"/reports/report.pdf" in names
    assert ROOT.name+"/notebooks/ipo_sentiment.ipynb" in names
sha=hashlib.sha256(out.read_bytes()).hexdigest()
out.with_suffix(".zip.sha256").write_text(sha+"  "+out.name+"\n",encoding="utf8")
print(out,len(names),"files",out.stat().st_size,"bytes")
print("SHA256",sha)
