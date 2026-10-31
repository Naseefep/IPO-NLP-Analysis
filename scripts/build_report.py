"""Generate the project report from the frozen empirical results."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("build_project_report.py")),run_name="__main__")
