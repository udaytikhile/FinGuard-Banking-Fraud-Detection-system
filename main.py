"""
FinGuard Root CLI Launcher
Delegates execution to FinGuard/main.py.
"""

import sys
from pathlib import Path

FINGUARD_DIR = Path(__file__).resolve().parent / "FinGuard"
sys.path.insert(0, str(FINGUARD_DIR))

if __name__ == "__main__":
    from main import main
    main()

