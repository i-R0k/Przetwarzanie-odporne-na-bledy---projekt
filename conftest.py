import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
API_PATH = ROOT / "VetClinic" / "API"

if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))
