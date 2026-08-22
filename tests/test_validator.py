from opsguardian.lineage import trace_downstream
from opsguardian.tools import dependency_lookup, sandbox_validate
from opsguardian.validator import validate_repair_candidates, verify_deployed_transform


def test_lineage_trace_is_real_graph_walk():
    assets = trace_downstream("crm.customer_export")
    assert assets == [
        "stg_customer_normalized",
        "fct_orders_customer_join",
        "customer_ltv_features",
        "executive_customer_dashboard",
    ]


def test_dependency_tool_reports_count():
    result = dependency_lookup("crm.customer_export")
    assert result["count"] == 4
    assert result["downstream_assets"][-1] == "executive_customer_dashboard"


def test_sandbox_rejects_lossy_integer_cast_and_accepts_string_normalization():
    bad, good = validate_repair_candidates(
        {
            "operation": "normalize_to_string",
            "summary": "Normalize customer IDs to strings",
            "patch": "CAST(customer_id AS STRING) AS customer_id",
        }
    )
    assert bad.status == "rejected"
    assert bad.error is not None
    assert good.status == "passed"
    assert good.checks_passed == 17
    assert good.checks_total == 17


def test_tool_sandbox_uses_same_validator():
    result = sandbox_validate("normalize_to_string")
    assert result["status"] == "passed"
    assert result["checks_passed"] == 17


def test_post_deploy_verification_executes_transform_again():
    verification = verify_deployed_transform("fix-2")
    assert verification["pipeline_run"] == "success"
    assert verification["checks"]["sandbox_checks"] == "17/17"
    assert verification["checks"]["alphanumeric_id"] == "pass"
    assert verification["rollback_required"] is False


def test_non_allowlisted_agent_operation_is_rejected():
    results = validate_repair_candidates(
        {"operation": "execute_arbitrary_sql", "summary": "unsafe", "patch": "DROP TABLE customers"}
    )
    assert results[1].status == "rejected"
    assert "not allowlisted" in (results[1].error or "")


def test_explicit_empty_dataset_is_not_silently_replaced_with_demo_rows():
    from opsguardian.validator import evaluate_candidate, normalize_to_string

    result = evaluate_candidate(
        "empty",
        "empty input",
        "noop",
        normalize_to_string,
        rows=[],
    )
    assert result.transformed_rows == []
    assert result.status == "rejected"
