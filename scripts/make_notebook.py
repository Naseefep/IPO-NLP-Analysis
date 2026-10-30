"""Build a clean, output-free notebook that runs the packaged project."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(text):
    cells.append(dict(cell_type="markdown",metadata={},source=text.splitlines(keepends=True)))
def code(text):
    cells.append(dict(cell_type="code",metadata={},execution_count=None,outputs=[],source=text.splitlines(keepends=True)))

md("""# Financial news sentiment and Indian IPO outcomes
Naseef E. P. | October 2026

Compare FinBERT and Loughran-McDonald sentiment on dated pre-listing headlines.
The frozen sample, audit trail and report are included in the project ZIP.
Read `README.md` and `reports/report.pdf` for the scope and actual findings.

**Local Jupyter:** open this notebook from the repository. **Colab:** upload the
project ZIP in the next cell. The first complete model run downloads weights;
CPU inference is supported. No API keys are required.
""")
code("""from pathlib import Path
import os, sys, zipfile
try:
    import google.colab
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

if IN_COLAB:
    from google.colab import files
    uploaded = files.upload()  # select ipo-sentiment-research.zip
    archive = next(Path(name) for name in uploaded if name.endswith('.zip'))
    destination = Path('/content/ipo-study').resolve()
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            resolved = (destination / member.filename).resolve()
            if destination != resolved and destination not in resolved.parents:
                raise ValueError('Unsafe archive member')
        z.extractall(destination)
    candidates = list(destination.rglob('pyproject.toml'))
    if len(candidates) != 1:
        raise ValueError('Expected one project in the archive')
    project = candidates[0].parent
else:
    project = Path.cwd()
    if not (project / 'pyproject.toml').exists():
        project = project.parent
    if not (project / 'pyproject.toml').exists():
        raise FileNotFoundError('Open the notebook from this project folder')
os.chdir(project)
print('Project:', project)
""")
md("## 1. Inspect the frozen study before downloading a model")
code("""import json
import pandas as pd
manifest = json.loads(Path('results/manifest.json').read_text())
print(manifest['counts'])
print('Model revision:', manifest.get('finbert_revision'))
panel = pd.read_csv('results/analysis_panel.csv')
display(panel[['symbol', 'listing_date', 'article_count', 'finbert_score', 'lm_score', 'listing_return_pct']])
coef = pd.read_csv('results/coefficients.csv')
display(coef[(coef.term == coef.score) & (coef.specification == 'controlled')])
""")
md("## 2. Install the project and download the official dictionary\nModel weights and dictionaries retain their original terms; see THIRD_PARTY_NOTICES.md.")
code("""import subprocess
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', '.[finbert]'])
subprocess.check_call([sys.executable, 'scripts/download_lm.py'])
""")
md("## 3. Reproduce the analysis\nUse a new output directory each time. The notebook does not overwrite the frozen results.")
code("""from datetime import datetime
run_folder = 'outputs/notebook-' + datetime.now().strftime('%Y%m%d-%H%M%S')
subprocess.check_call([
    sys.executable, '-m', 'iposent.cli',
    '--ipos', 'data/research/ipos.csv',
    '--prices', 'data/research/prices.csv',
    '--news', 'data/research/news.csv',
    '--model', 'both',
    '--lm-dictionary', 'data/lexicons/Loughran-McDonald_MasterDictionary_1993-2025.csv',
    '--output', run_folder,
])
""")
md("## 4. Read the audit and prediction results")
code("""run_path = Path(run_folder)
audit = pd.read_csv(run_path / 'news_audit.csv')
display(audit.rejection.fillna('retained').value_counts())
display(pd.DataFrame(json.loads((run_path / 'holdout_metrics.json').read_text())))
from IPython.display import Image, display
display(Image(filename=str(run_path / 'sentiment_outcomes.png')))
""")
md("## 5. Run the offline checks")
code("""subprocess.check_call([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
""")
md("""## Interpretation
Read coefficient confidence intervals and the chronological test errors together.
Neither correlation nor OLS establishes causation. A null result is not proof
of market efficiency. Search coverage and model/dictionary vintage limit claims
about historical forecasting. The report documents the retained sample and checks.
""")
out=ROOT/"notebooks/ipo_sentiment.ipynb"
out.parent.mkdir(exist_ok=True)
for i,cell in enumerate(cells):
    cell["id"]=f"cell-{i:03d}"
out.write_text(json.dumps(dict(cells=cells,metadata=dict(kernelspec=dict(display_name="Python 3",language="python",name="python3"),language_info=dict(name="python",version="3.12")),nbformat=4,nbformat_minor=5),indent=2),encoding="utf8")
print(out)
