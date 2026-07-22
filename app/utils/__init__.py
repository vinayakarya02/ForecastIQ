"""ForecastIQ Streamlit app utilities.

Importing this package wires the project's ``src`` directory onto sys.path so the
app can ``import forecastiq`` regardless of the working directory.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"  # app/utils/ -> project root -> src
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
