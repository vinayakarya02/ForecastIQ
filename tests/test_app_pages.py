"""Smoke tests: every Streamlit page renders without raising.

Uses Streamlit's AppTest to execute each page against the real warehouse. Requires the
warehouse to exist (run the ETL first); skipped gracefully if it doesn't.
"""

from pathlib import Path

import pytest

from forecastiq.config import Config

_PAGES_DIR = Path(__file__).resolve().parents[1] / "app" / "pages"
_PAGES = sorted(_PAGES_DIR.glob("*.py"))
_DB = Path(Config.load().db_url.replace("sqlite:///", ""))

pytestmark = pytest.mark.skipif(
    not _DB.exists(), reason="warehouse not built (run pipelines/run_etl.py)"
)


@pytest.mark.parametrize("page", _PAGES, ids=lambda p: p.stem)
def test_page_renders_without_exception(page):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(page), default_timeout=90)
    at.run()
    assert not at.exception, f"{page.name} raised: {at.exception}"


def test_all_ten_pages_present():
    assert len(_PAGES) == 10
