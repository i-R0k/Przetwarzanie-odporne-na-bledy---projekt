import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
API_PATH = ROOT / "VetClinic" / "API"

# Ensure local API package is importable before any globally installed one
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))
