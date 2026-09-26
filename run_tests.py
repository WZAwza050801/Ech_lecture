"""Run the test suite without pytest: python run_tests.py

pytest users can still run `pip install pytest && pytest tests/` (tests/conftest.py
applies the same module aliases).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tests"))
import conftest  # noqa: F401  (registers work.* module aliases for this clone layout)

import unittest

if __name__ == "__main__":
    suite = unittest.TestLoader().discover(str(Path(__file__).resolve().parent / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
