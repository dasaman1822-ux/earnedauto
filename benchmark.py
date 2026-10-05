import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from src.baselines import always_act, always_ask
from src.evidence import EvidenceStore
from src.gate import TrustGate
from src.simulator import INCIDENT_ACTIONS, OutcomeType, generate_incidents, generate_outcome, apply_outcome_to_evidence

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
SEED = 42
INCIDENT_COUNT = 1000
HUMAN_APPROVAL_SECONDS = 120.0
HUMAN_RECOVERY_SECONDS = 300.0
ACTION_SECONDS = {
    "restart_service": 20.0,
    "requeue_job": 15.0,
    "reset_driver": 30.0,
    "drain_node": 60.0,
    "reclaim_disk": 45.0,
}
POLICY_NAMES = ("always_ask", "always_act", "earnedauto")


@dataclass(frozen=True)
class IncidentResult:
    incident_id: str
    action_type: str
    decision: str
    outcome: str | None
    human_involved: bool
    recovery_seconds: float
    unsafe_automatic: bool


def candidate_action(incident):
    return INCIDENT_ACTIONS[incident.incident_type]


def run_policy(name: str, incidents, seed: int, gate_factory=None):
    rng = random.Random(seed)
    evidence = EvidenceStore()
    gate = gate_factory(evidence) if gate_factory else None
    results = []

    for incident in incidents:
        action = candidate_action(incident)

        if name == "always_ask":
            policy = always_ask(candidate_action, incident)
            decision = policy.mode
            human_involved = True
        elif name == "always_act":
            policy = always_act(candidate_action, incident)
            decision = policy.mode
            human_involved = False
        elif name == "earnedauto":
            gate_result = gate.decide(action, incident.machine_class)
            decision = gate_result.decision
            human_involved = decision != "AUTO"
        else:
            raise ValueError(f"Unknown policy: {name}")

        executed = decision in {"AUTO", "HUMAN_APPROVAL", "PROPOSE", "ESCALATE"}
        outcome = None
        unsafe = False

        if executed:
            outcome = generate_outcome(action, rng=rng).outcome_type
            if name == "earnedauto":
                apply_outcome_to_evidence(
                    type("Outcome", (), {"outcome_type": outcome})(),
                    action,
                    incident.machine_class,
                    evidence,
                )
            unsafe = decision == "AUTO" and outcome != OutcomeType.RESOLVED
        else:
            raise AssertionError("Unexpected non-executing decision")

        recovery = ACTION_SECONDS[action]
        if decision == "HUMAN_APPROVAL":
            recovery += HUMAN_APPROVAL_SECONDS
        elif decision == "PROPOSE":
            recovery += HUMAN_APPROVAL_SECONDS
        elif decision == "ESCALATE":
            recovery += HUMAN_RECOVERY_SECONDS
        if outcome != OutcomeType.RESOLVED and executed:
            recovery += HUMAN_RECOVERY_SECONDS
            human_involved = True

        results.append(
            IncidentResult(
                incident_id=incident.incident_id,
                action_type=action,
                decision=decision,
                outcome=outcome,
                human_involved=human_involved,
                recovery_seconds=recovery,
                unsafe_automatic=unsafe,
            )
        )
    return results


def metrics(results):
    n = len(results)
    autonomous_executions = sum(r.decision == "AUTO" for r in results)
    automatic_resolutions = sum(
        r.decision == "AUTO" and r.outcome == OutcomeType.RESOLVED
        for r in results
    )
    human_interruptions = sum(r.human_involved for r in results)
    unsafe = sum(r.unsafe_automatic for r in results)
    resolved = sum(r.outcome == OutcomeType.RESOLVED for r in results)

    return {
        "incident_count": n,
        "automation_rate": autonomous_executions / n if n else 0.0,
        "automatic_resolution_rate": automatic_resolutions / n if n else 0.0,
        "mean_time_to_recovery_seconds": (
            sum(r.recovery_seconds for r in results) / n if n else 0.0
        ),
        "human_interruptions": human_interruptions,
        "unsafe_automatic_executions": unsafe,
        "autonomous_execution_count": autonomous_executions,
        "unsafe_automatic_execution_rate": (
            unsafe / autonomous_executions if autonomous_executions else 0.0
        ),
        "remediation_success_rate": resolved / n if n else 0.0,
    }


def run_benchmark(seed: int = SEED, incident_count: int = INCIDENT_COUNT):
    incident_rng = random.Random(seed)
    incidents = generate_incidents(incident_count, rng=incident_rng)

    all_results = {}
    all_metrics = {}

    for name in ("always_ask", "always_act"):
        policy_results = run_policy(name, incidents, seed=seed)
        all_results[name] = policy_results
        all_metrics[name] = metrics(policy_results)

    def gate_factory(evidence):
        return TrustGate(evidence_store=evidence)

    policy_results = run_policy(
        "earnedauto",
        incidents,
        seed=seed,
        gate_factory=gate_factory,
    )
    all_results["earnedauto"] = policy_results
    all_metrics["earnedauto"] = metrics(policy_results)

    return incidents, all_results, all_metrics


def serializable(incidents, results, metric_values, seed):
    return {
        "metadata": {
            "seed": seed,
            "incident_count": len(incidents),
            "human_approval_seconds": HUMAN_APPROVAL_SECONDS,
            "human_recovery_seconds": HUMAN_RECOVERY_SECONDS,
            "action_seconds": ACTION_SECONDS,
            "metric_definitions": {
                "automation_rate": "AUTO decisions / total incidents",
                "automatic_resolution_rate": "AUTO decisions whose executed action resolved the incident / total incidents",
                "mean_time_to_recovery_seconds": "mean simulated time from incident to final resolution",
                "human_interruptions": "incidents requiring human involvement before execution or for recovery",
                "unsafe_automatic_executions": "AUTO decisions followed by RECURRED or HARMFUL outcomes",
                "unsafe_automatic_execution_rate": "unsafe automatic executions / autonomous executions",
                "remediation_success_rate": "resolved incidents / total incidents",
            },
        },
        "incidents": [asdict(i) for i in incidents],
        "metrics": metric_values,
        "decisions": {
            name: [asdict(r) for r in rows]
            for name, rows in results.items()
        },
    }


def write_outputs(payload):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "benchmark_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Week 4 Benchmark Summary",
        "",
        f"Seed: {payload['metadata']['seed']}",
        f"Incidents: {payload['metadata']['incident_count']}",
        "",
        "| Metric | Always ask | Always act | EarnedAutonomy |",
        "|---|---:|---:|---:|",
    ]
    metric_rows = [
        ("Automatic resolution rate", "automatic_resolution_rate"),
        ("Mean time to recovery (s)", "mean_time_to_recovery_seconds"),
        ("Human interruptions", "human_interruptions"),
        ("Unsafe automatic executions", "unsafe_automatic_executions"),
    ]
    for label, key in metric_rows:
        values = [payload["metrics"][name][key] for name in ("always_ask", "always_act", "earnedauto")]
        if key in {"human_interruptions", "unsafe_automatic_executions"}:
            formatted = [str(int(v)) for v in values]
        elif key == "mean_time_to_recovery_seconds":
            formatted = [f"{v:.2f}" for v in values]
        else:
            formatted = [f"{v:.4f}" for v in values]
        lines.append(f"| {label} | {formatted[0]} | {formatted[1]} | {formatted[2]} |")
    lines.extend([
        "",
        "| Additional metric | Always ask | Always act | EarnedAutonomy |",
        "|---|---:|---:|---:|",
    ])
    for label, key in [
        ("Automation rate", "automation_rate"),
        ("Unsafe automatic execution rate", "unsafe_automatic_execution_rate"),
        ("Remediation success rate", "remediation_success_rate"),
    ]:
        values = [payload["metrics"][name][key] for name in ("always_ask", "always_act", "earnedauto")]
        lines.append(f"| {label} | {values[0]:.4f} | {values[1]:.4f} | {values[2]:.4f} |")
    (RESULTS_DIR / "benchmark_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--incidents", type=int, default=INCIDENT_COUNT)
    args = parser.parse_args()

    incidents, results, metric_values = run_benchmark(args.seed, args.incidents)
    payload = serializable(incidents, results, metric_values, args.seed)
    write_outputs(payload)

    print(f"Seed: {args.seed}")
    print(f"Incidents: {args.incidents}")
    for name in ("always_ask", "always_act", "earnedauto"):
        print(name, metric_values[name])


if __name__ == "__main__":
    main()
