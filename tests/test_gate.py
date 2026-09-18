from src.evidence import EvidenceStore
from src.gate import TrustGate


def test_no_history_never_returns_auto():
    """
    An action with no previous outcomes must not be AUTO.
    """
    evidence = EvidenceStore()
    gate = TrustGate(evidence_store=evidence)

    result = gate.decide(
        action_type="restart_service",
        machine_class="compute_node",
    )

    assert result.has_history is False
    assert result.decision != "AUTO"


def test_high_blast_radius_never_returns_auto():
    """
    A high blast-radius action must not be AUTO,
    even when it has accumulated successful outcomes.
    """
    evidence = EvidenceStore()

    for _ in range(100):
        evidence.record_success(
            "drain_node",
            "compute_node",
        )

    gate = TrustGate(evidence_store=evidence)

    result = gate.decide(
        action_type="drain_node",
        machine_class="compute_node",
    )

    assert result.risk >= 0.60
    assert result.decision != "AUTO"


def test_gate_can_return_propose():
    """
    Moderate evidence should allow an action to be PROPOSED
    without allowing it to become AUTO.
    """
    evidence = EvidenceStore()

    for _ in range(5):
        evidence.record_success(
            "restart_service",
            "compute_node",
        )

    gate = TrustGate(evidence_store=evidence)

    result = gate.decide(
        action_type="restart_service",
        machine_class="compute_node",
    )

    assert result.has_history is True
    assert result.decision == "PROPOSE"


def test_gate_can_return_auto():
    """
    Strong accumulated evidence for a low-risk action
    should allow AUTO.
    """
    evidence = EvidenceStore()

    for _ in range(50):
        evidence.record_success(
            "restart_service",
            "compute_node",
        )

    gate = TrustGate(evidence_store=evidence)

    result = gate.decide(
        action_type="restart_service",
        machine_class="compute_node",
    )

    assert result.has_history is True
    assert result.trust > 0.65
    assert result.risk < 0.60
    assert result.decision == "AUTO"


def test_gate_can_return_escalate():
    """
    An action with no history should remain ESCALATE
    when there is insufficient trust.
    """
    evidence = EvidenceStore()
    gate = TrustGate(evidence_store=evidence)

    result = gate.decide(
        action_type="reclaim_disk",
        machine_class="storage_node",
    )

    assert result.has_history is False
    assert result.decision == "ESCALATE"