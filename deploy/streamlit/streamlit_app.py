"""Entry point for the hosted dashboard on Streamlit Community Cloud.

Community Cloud runs one script from the repository. This runs the dashboard
that ships inside the installed quant-core package, fresh on every rerun, the
way `qc dashboard` does locally. The dashboard reads sample data from
`data/benchmark/` relative to the working directory, which Community Cloud sets
to the repository root.
"""

import runpy
from pathlib import Path

import quant_core.dashboard

APP = Path(quant_core.dashboard.__file__).parent / "app.py"
runpy.run_path(str(APP), run_name="__main__")
