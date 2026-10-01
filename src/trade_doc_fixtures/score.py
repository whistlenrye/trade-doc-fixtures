"""Score an extraction against a gold ExtractionResult.

Only fields present on the gold document are checked. Extra keys on the
actual document are ignored, so a richer model is not punished. Numbers match
within 0.02 absolute or 0.1% relative. Text is compared after lower-casing
and collapsing punctuation.
"""

from __future__ import annotations

import re
from typing import Any

_SCALAR_PATHS = (
    "doc_type",
    "invoice_number",
    "invoice_date",
    "incoterms",
    "currency",
    "subtotal",
    "freight",
    "insurance",
    "total",
    "shipper.name",
    "shipper.address",
    "shipper.country",
    "shipper.tax_id",
    "consignee.name",
    "consignee.address",
    "consignee.country",
    "transport.mode",
    "transport.ocean_bill",
    "transport.house_bill",
    "transport.vessel",
    "transport.voyage",
    "transport.port_of_loading",
    "transport.port_of_discharge",
    "transport.packages",
    "transport.gross_weight_kg",
    "transport.net_weight_kg",
)

_LINE_FIELDS = (
    "description",
    "quantity",
    "unit",
    "unit_price",
    "amount",
    "hs_code",
    "country_of_origin",
)


def _dig(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _norm(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _numbers_close(left: float, right: float) -> bool:
    scale = max(abs(left), abs(right), 1.0)
    return abs(left - right) <= max(0.02, 0.001 * scale)


def _equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return _numbers_close(float(expected), float(actual))
    if isinstance(expected, (int, float)) and isinstance(actual, str):
        try:
            return _numbers_close(float(expected), float(actual.replace(",", "")))
        except ValueError:
            return False
    return _norm(expected) == _norm(actual)


def _check(checks: list[dict[str, Any]], path: str, expected: Any, actual: Any) -> None:
    if expected is None or expected == "" or expected == []:
        return
    ok = actual is not None and _equal(expected, actual)
    checks.append({
        "path": path,
        "ok": ok,
        "expected": expected,
        "actual": actual,
    })


def _match_lines(expected: list[dict[str, Any]], actual: list[dict[str, Any]]) -> dict[int, int]:
    used: set[int] = set()
    matches: dict[int, int] = {}
    for index, line in enumerate(expected):
        target = _norm(line.get("description") or "")
        best: tuple[float, int] | None = None
        for actual_index, candidate in enumerate(actual):
            if actual_index in used:
                continue
            if target and target == _norm(candidate.get("description") or ""):
                best = (1.0, actual_index)
                break
        if best is None and index < len(actual) and index not in used:
            best = (0.0, index)
        if best is not None:
            used.add(best[1])
            matches[index] = best[1]
    return matches


def score_extraction(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """Gold-field recall for one document. 1.0 means every gold field matched."""
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        raise TypeError("actual and expected must both be objects.")
    checks: list[dict[str, Any]] = []
    for path in _SCALAR_PATHS:
        _check(checks, path, _dig(expected, path), _dig(actual, path))

    expected_boxes = (expected.get("transport") or {}).get("containers") if isinstance(expected.get("transport"), dict) else None
    if expected_boxes:
        actual_boxes = (actual.get("transport") or {}).get("containers") if isinstance(actual.get("transport"), dict) else None
        expected_set = {str(item).strip().upper() for item in expected_boxes}
        actual_set = {str(item).strip().upper() for item in (actual_boxes or [])}
        checks.append({
            "path": "transport.containers",
            "ok": expected_set == actual_set,
            "expected": sorted(expected_set),
            "actual": sorted(actual_set),
        })

    expected_lines = [line for line in expected.get("line_items") or [] if isinstance(line, dict)]
    actual_lines = [line for line in actual.get("line_items") or [] if isinstance(line, dict)]
    matches = _match_lines(expected_lines, actual_lines)
    for index, line in enumerate(expected_lines):
        actual_line = actual_lines[matches[index]] if index in matches else {}
        for field in _LINE_FIELDS:
            _check(checks, f"line_items[{index}].{field}", line.get(field), actual_line.get(field))

    hits = sum(1 for item in checks if item["ok"])
    total = len(checks)
    misses = [item for item in checks if not item["ok"]]
    return {
        "gold_fields": total,
        "hits": hits,
        "recall": 1.0 if total == 0 else round(hits / total, 4),
        "misses": misses,
    }
