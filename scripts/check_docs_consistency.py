"""Backward-compatible entry point for docs consistency check."""

from __future__ import annotations

import sys

from scripts.verify.check_docs_consistency import main

if __name__ == "__main__":
    sys.exit(main())
