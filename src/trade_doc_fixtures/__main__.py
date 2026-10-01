"""CLI: trade-doc-score actual.json fixtures/packing_list/expected.json"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trade_doc_fixtures.score import score_extraction


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score an extraction JSON file against a gold fixture.")
    parser.add_argument("actual")
    parser.add_argument("expected")
    parser.add_argument("--threshold", type=float, default=1.0, help="Minimum recall that still exits 0.")
    args = parser.parse_args(argv)
    try:
        actual = json.loads(Path(args.actual).read_text(encoding="utf-8"))
        expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
        report = score_extraction(actual, expected)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["recall"] + 1e-9 >= args.threshold else 1


if __name__ == "__main__":
    raise SystemExit(main())
