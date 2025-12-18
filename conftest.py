import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import sys
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parent / "VetClinic" / "GUI"
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

@pytest.fixture(scope="session", autouse=True)
def _qt_finalize(qapp):
    """
    Keep QApplication alive for the whole session and flush events on shutdown.
    """
    yield
    try:
        qapp.processEvents()
        qapp.quit()
        qapp.processEvents()
    except Exception:
        pass
