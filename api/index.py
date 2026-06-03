from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
API_APP_PATH = ROOT / "apps" / "api"

if str(API_APP_PATH) not in sys.path:
    sys.path.insert(0, str(API_APP_PATH))

from app.main import app  # noqa: E402
