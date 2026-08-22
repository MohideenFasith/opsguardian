from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROWS_PATH = ROOT / "sample_data" / "customer_rows.json"


@dataclass
class CandidateResult:
    id: str
    summary: str
    patch: str
    status: str
    checks_passed: int
    checks_total: int
    failed_checks: list[str]
    transformed_rows: list[dict]
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "summary": self.summary,
            "patch": self.patch,
            "status": self.status,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "failed_checks": self.failed_checks,
            "error": self.error,
        }


def load_rows(path: Path = DEFAULT_ROWS_PATH) -> list[dict]:
    return json.loads(path.read_text())


def coerce_to_integer(rows: list[dict]) -> list[dict]:
    output = copy.deepcopy(rows)
    for row in output:
        # This intentionally demonstrates the tempting but unsafe repair.
        row["customer_id"] = str(int(str(row["customer_id"]).strip()))
    return output


def normalize_to_string(rows: list[dict]) -> list[dict]:
    output = copy.deepcopy(rows)
    for row in output:
        value = row.get("customer_id")
        row["customer_id"] = "" if value is None else str(value).strip()
    return output


def _validation_checks(source: list[dict], transformed: list[dict]) -> list[tuple[str, bool]]:
    source_ids = [str(r.get("customer_id", "")).strip() for r in source]
    out_ids = [r.get("customer_id") for r in transformed]
    src_orders = [r["order_id"] for r in source]
    out_orders = [r["order_id"] for r in transformed]
    src_amounts = [r["amount"] for r in source]
    out_amounts = [r["amount"] for r in transformed]
    src_emails = [r["email"] for r in source]
    out_emails = [r["email"] for r in transformed]

    # These checks are intentionally explicit and auditable rather than a single opaque score.
    return [
        ("row_count_preserved", len(transformed) == len(source)),
        ("customer_id_non_null", all(v is not None for v in out_ids)),
        ("customer_id_is_string", all(isinstance(v, str) for v in out_ids)),
        ("customer_id_non_empty", all(bool(v) for v in out_ids)),
        ("customer_id_trimmed", all(v == v.strip() for v in out_ids if isinstance(v, str))),
        ("legacy_numeric_id_100480_preserved", "100480" in out_ids),
        ("legacy_numeric_id_100481_preserved", "100481" in out_ids),
        ("numeric_string_id_100482_preserved", "100482" in out_ids),
        ("alphanumeric_id_preserved", "C-100483" in out_ids),
        ("all_source_ids_preserved", sorted(out_ids) == sorted(source_ids)),
        ("customer_ids_unique", len(out_ids) == len(set(out_ids))),
        ("order_ids_preserved", out_orders == src_orders),
        ("order_ids_unique", len(out_orders) == len(set(out_orders))),
        ("amounts_preserved", out_amounts == src_amounts),
        ("emails_preserved", out_emails == src_emails),
        ("join_cardinality_preserved", len(set(zip(out_ids, out_orders))) == len(source)),
        ("bounded_identifier_length", all(len(v) <= 64 for v in out_ids)),
    ]


def evaluate_candidate(
    candidate_id: str,
    summary: str,
    patch: str,
    transform: Callable[[list[dict]], list[dict]],
    rows: list[dict] | None = None,
) -> CandidateResult:
    source = load_rows() if rows is None else rows
    try:
        transformed = transform(source)
        checks = _validation_checks(source, transformed)
        failed = [name for name, ok in checks if not ok]
        passed = sum(1 for _, ok in checks if ok)
        return CandidateResult(
            id=candidate_id,
            summary=summary,
            patch=patch,
            status="passed" if not failed else "rejected",
            checks_passed=passed,
            checks_total=len(checks),
            failed_checks=failed,
            transformed_rows=transformed,
        )
    except Exception as exc:
        # A transform that cannot process a valid new ID is itself a failed sandbox candidate.
        checks_total = len(_validation_checks(source, normalize_to_string(source)))
        return CandidateResult(
            id=candidate_id,
            summary=summary,
            patch=patch,
            status="rejected",
            checks_passed=0,
            checks_total=checks_total,
            failed_checks=["transform_execution"],
            transformed_rows=[],
            error=f"{type(exc).__name__}: {exc}",
        )


def validate_repair_candidates(proposed: dict) -> list[CandidateResult]:
    candidate_1 = evaluate_candidate(
        "fix-1",
        "Coerce new STRING IDs back to INTEGER",
        "CAST(customer_id AS INT64)",
        coerce_to_integer,
    )

    allowed_transforms = {
        "normalize_to_string": normalize_to_string,
        "coerce_to_integer": coerce_to_integer,
    }
    operation = proposed.get("operation", "")
    transform = allowed_transforms.get(operation)
    if transform is None:
        def unsupported(_: list[dict]) -> list[dict]:
            raise ValueError(f"Repair operation is not allowlisted: {operation!r}")
        transform = unsupported

    candidate_2 = evaluate_candidate(
        "fix-2",
        proposed.get("summary", "Agent-proposed repair"),
        proposed.get("patch", operation or "unknown operation"),
        transform,
    )
    # Keep the selected tool operation visible in the audit details.
    candidate_2.patch = proposed.get("patch", operation or "unknown operation")
    return [candidate_1, candidate_2]


def verify_deployed_transform(candidate_id: str) -> dict:
    rows = load_rows()
    transform = normalize_to_string if candidate_id == "fix-2" else coerce_to_integer
    result = evaluate_candidate(candidate_id, "deployed", "", transform, rows)
    null_count = sum(1 for row in result.transformed_rows if not row.get("customer_id"))
    row_delta_pct = ((len(result.transformed_rows) - len(rows)) / len(rows) * 100) if rows else 0.0
    return {
        "pipeline_run": "success" if result.status == "passed" else "failed",
        "checks": {
            "sandbox_checks": f"{result.checks_passed}/{result.checks_total}",
            "row_count_delta": f"{row_delta_pct:+.2f}%",
            "null_rate_customer_id": f"{(null_count / len(rows) * 100 if rows else 0):.2f}%",
            "join_cardinality": "pass" if "join_cardinality_preserved" not in result.failed_checks else "fail",
            "alphanumeric_id": "pass" if "alphanumeric_id_preserved" not in result.failed_checks else "fail",
        },
        "rollback_required": result.status != "passed",
        "failed_checks": result.failed_checks,
    }
