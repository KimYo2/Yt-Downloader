"""Add project root to sys.path so app.* imports resolve correctly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
