from __future__ import annotations

from .lineage import trace_downstream
from .validator import validate_repair_candidates


def inspect_incident(anomaly: dict) -> dict:
    """Return facts that are safe for the model to reason over."""
    return {
        "dataset": anomaly.get("dataset"),
        "field": anomaly.get("field"),
        "expected_type": anomaly.get("expected_type"),
        "observed_type": anomaly.get("observed_type"),
        "first_bad_version": anomaly.get("first_bad_version"),
        "sample_new_values": anomaly.get("sample_new_values", []),
    }


def dependency_lookup(dataset: str) -> dict:
    assets = trace_downstream(dataset)
    return {"dataset": dataset, "downstream_assets": assets, "count": len(assets)}


def sandbox_validate(operation: str) -> dict:
    proposal = {
        "operation": operation,
        "summary": f"Validate {operation}",
        "patch": operation,
    }
    candidates = validate_repair_candidates(proposal)
    selected = candidates[1]
    return selected.as_dict()
