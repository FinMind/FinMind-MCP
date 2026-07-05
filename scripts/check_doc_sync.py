#!/usr/bin/env python3
"""CI gate: keep the MCP dataset catalog in sync with FinMind-Doc.

The MCP knowledge pack (`knowledge/datasets.md`) is the single source of truth
for "what datasets exist", shared by the `list_datasets` tool and the Custom GPT
knowledge bundle. FinMind ships new datasets by documenting them in FinMind-Doc,
and historically the MCP catalog silently drifted behind (datasets added to the
docs months earlier were missing here). Unit tests can't catch that — it is a
content gap, not a code bug.

This script fails CI when a dataset is documented in FinMind-Doc (i.e. appears in
an example `dataset="..."` call under docs/tutor/) but is absent from the MCP
catalog and not in the explicit EXCLUDE allowlist below. When it fails, the fix
is one of:
  * add the dataset to knowledge/datasets.md (it belongs in the catalog), or
  * add it to EXCLUDE with a reason (documented in FinMind-Doc but intentionally
    outside the MCP generic-endpoint catalog, or a known doc typo).

Usage:
    python scripts/check_doc_sync.py --doc ./FinMind-Doc
    FINMIND_DOC_DIR=./FinMind-Doc python scripts/check_doc_sync.py
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Datasets that appear in FinMind-Doc example code but are intentionally NOT in
# the MCP generic-endpoint catalog. Every entry needs a reason so this list
# stays auditable rather than becoming a dumping ground that hides real drift.
EXCLUDE: dict[str, str] = {
    # Doc example typo: the documented dataset section is `TaiwanStockDividend`
    # (股利政策表, already in the catalog); a couple of example snippets in
    # Fundamental.md write `dataset="TaiwanStockStockDividend"` with a stray
    # extra "Stock". The API enum has no such dataset.
    "TaiwanStockStockDividend": "Doc example typo for TaiwanStockDividend",
}

# Matches `dataset="Name"`, `dataset='Name'`, and `"dataset": "Name"`.
_DATASET_RE = re.compile(
    r"""(?:"dataset"\s*:\s*|dataset\s*=\s*)["']([A-Za-z][A-Za-z0-9]+)["']"""
)


def documented_datasets(doc_dir: Path) -> set[str]:
    """Dataset ids that appear in example calls under docs/tutor/."""
    tutor = doc_dir / "docs" / "tutor"
    if not tutor.is_dir():
        sys.exit(
            f"error: {tutor} not found — is --doc pointing at a FinMind-Doc "
            f"checkout? (got {doc_dir})"
        )
    found: set[str] = set()
    for md in tutor.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        found.update(_DATASET_RE.findall(text))
    return found


def catalog_datasets(catalog_md: Path) -> set[str]:
    """Dataset names from the `### Name` headers in knowledge/datasets.md."""
    names: set[str] = set()
    for line in catalog_md.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            names.add(line[4:].strip())
    return names


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--doc",
        default=os.environ.get("FINMIND_DOC_DIR", "./FinMind-Doc"),
        help="Path to a FinMind-Doc checkout (default: ./FinMind-Doc or "
        "$FINMIND_DOC_DIR)",
    )
    parser.add_argument(
        "--catalog",
        default=str(repo_root / "knowledge" / "datasets.md"),
        help="Path to knowledge/datasets.md",
    )
    args = parser.parse_args()

    doc = documented_datasets(Path(args.doc))
    catalog = catalog_datasets(Path(args.catalog))

    missing = sorted(doc - catalog - set(EXCLUDE))
    # Excludes that no longer appear in the docs — clean them up so the list
    # keeps reflecting reality (warning only, does not fail the build).
    stale_excludes = sorted(set(EXCLUDE) - doc)

    print(f"FinMind-Doc documented datasets : {len(doc)}")
    print(f"MCP catalog datasets            : {len(catalog)}")
    print(f"EXCLUDE allowlist               : {len(EXCLUDE)}")

    if stale_excludes:
        print()
        print("warning: EXCLUDE entries no longer found in FinMind-Doc "
              "(consider removing):")
        for name in stale_excludes:
            print(f"  - {name}")

    if missing:
        print()
        print("FAIL: datasets documented in FinMind-Doc but missing from "
              "knowledge/datasets.md:")
        for name in missing:
            print(f"  - {name}")
        print()
        print("Fix: add each to knowledge/datasets.md (with Endpoint/Tier/"
              "Required/Optional/Key columns/描述), or add it to EXCLUDE in "
              "scripts/check_doc_sync.py with a reason.")
        return 1

    print()
    print("OK: MCP catalog is in sync with FinMind-Doc.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
