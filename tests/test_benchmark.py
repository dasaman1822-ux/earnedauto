import json
from pathlib import Path

from benchmark import metrics, run_benchmark
from src.baselines import always_act, always_ask
from src.simulator import Incident


def test_always_ask_requires_human():
    incident = Incident("INC-1", "kernel_error", "compute_node", "t")
    result = always_ask(lambda _: "reset_driver", incident)
    assert result.mode == "HUMAN_APPROVAL"
    assert result.human_involved is True


def test_always_act_has_no_pre_action_human():
    incident = Incident("INC-1", "kernel_error", "compute_node", "t")
    result = always_act(lambda _: "reset_driver", incident)
    assert result.mode == "AUTO"
    assert result.human_involved is False


def test_metric_zero_denominators_are_safe():
    values = metrics([])
    assert values["automatic_resolution_rate"] == 0.0
    assert values["unsafe_automatic_execution_rate"] == 0.0


def test_benchmark_is_deterministic():
    _, _, first = run_benchmark(seed=42, incident_count=100)
    _, _, second = run_benchmark(seed=42, incident_count=100)
    assert first == second


def test_unsafe_automatic_execution_metric():
    from benchmark import IncidentResult

    rows = [
        IncidentResult("t", "1", "kernel_error", "compute_node", "restart_service", "AUTO", 0.9, 0.1, 0.05, 0.04, 0.1, "harmful", False, True, 320.0, True),
        IncidentResult("t", "2", "kernel_error", "compute_node", "restart_service", "AUTO", 0.9, 0.1, 0.05, 0.04, 0.1, "resolved", True, False, 20.0, False),
    ]
    values = metrics(rows)
    assert values["automation_rate"] == 1.0
    assert values["unsafe_automatic_executions"] == 1
    assert values["unsafe_automatic_execution_rate"] == 0.5


def test_decision_records_contain_required_audit_fields():
    _, results, _ = run_benchmark(seed=42, incident_count=1)
    record = results["earnedauto"][0]

    assert record.timestamp
    assert record.incident_id
    assert record.incident_type
    assert record.machine_class
    assert record.action_type
    assert 0.0 <= record.reversibility <= 1.0
    assert 0.0 <= record.blast_radius <= 1.0
    assert 0.0 <= record.evidence_lower_bound <= 1.0
    assert record.decision in {"AUTO", "PROPOSE", "ESCALATE"}
    assert record.outcome in {"resolved", "recurred", "harmful"}
    assert isinstance(record.resolved, bool)
    assert record.recovery_seconds >= 0.0
