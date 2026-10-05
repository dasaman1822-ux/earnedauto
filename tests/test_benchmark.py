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
        IncidentResult("1", "restart_service", "AUTO", "harmful", True, 320.0, True),
        IncidentResult("2", "restart_service", "AUTO", "resolved", False, 20.0, False),
    ]
    values = metrics(rows)
    assert values["automation_rate"] == 1.0
    assert values["unsafe_automatic_executions"] == 1
    assert values["unsafe_automatic_execution_rate"] == 0.5
