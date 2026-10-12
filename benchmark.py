import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from src.baselines import always_act, always_ask
from src.evidence import EvidenceStore
from src.gate import TrustGate
from src.simulator import (
    INCIDENT_ACTIONS,
    Action,
    Outcome,
    OutcomeType,
    apply_outcome_to_evidence,
    generate_incidents,
    generate_outcome,
)

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
ACTIONS_CONFIG = ROOT / "config" / "actions.yaml"
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


def _load_action_records():
    with ACTIONS_CONFIG.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return {
        action_type: Action(
            action_type=action_type,
            reversibility=float(values["reversibility"]),
            blast_radius=float(values["blast_radius"]),
        )
        for action_type, values in config["actions"].items()
    }


ACTION_RECORDS = _load_action_records()


@dataclass(frozen=True)
class IncidentResult:
    timestamp: str
    incident_id: str
    incident_type: str
    machine_class: str
    action_type: str
    decision: str
    reversibility: float
    blast_radius: float
    evidence_lower_bound: float
    trust: float
    risk: float
    outcome: str | None
    resolved: bool
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
        action_record = ACTION_RECORDS[action]

        if name == "always_ask":
            policy = always_ask(candidate_action, incident)
            decision = policy.mode
            human_involved = True
            evidence_lower_bound = evidence.get_lower_bound(
                action,
                incident.machine_class,
            )
            trust = action_record.reversibility * evidence_lower_bound
            risk = action_record.blast_radius

        elif name == "always_act":
            policy = always_act(candidate_action, incident)
            decision = policy.mode
            human_involved = False
            evidence_lower_bound = evidence.get_lower_bound(
                action,
                incident.machine_class,
            )
            trust = action_record.reversibility * evidence_lower_bound
            risk = action_record.blast_radius

        elif name == "earnedauto":
            gate_result = gate.decide(
                action,
                incident.machine_class,
            )
            decision = gate_result.decision
            human_involved = decision != "AUTO"
            evidence_lower_bound = gate_result.evidence_lower_bound
            trust = gate_result.trust
            risk = gate_result.risk

        else:
            raise ValueError(f"Unknown policy: {name}")

        outcome_result = generate_outcome(
            incident.incident_type,
            action,
            rng=rng,
        )

        outcome = outcome_result.outcome_type

        if name == "earnedauto":
            apply_outcome_to_evidence(
                outcome_result,
                action,
                incident.machine_class,
                evidence,
            )

        unsafe = (
            decision == "AUTO"
            and outcome != OutcomeType.RESOLVED
        )

        resolved = outcome == OutcomeType.RESOLVED

        recovery = ACTION_SECONDS[action]

        if decision in {"HUMAN_APPROVAL", "PROPOSE"}:
            recovery += HUMAN_APPROVAL_SECONDS
        elif decision == "ESCALATE":
            recovery += HUMAN_RECOVERY_SECONDS

        if not resolved:
            recovery += HUMAN_RECOVERY_SECONDS
            human_involved = True

        results.append(
            IncidentResult(
                timestamp=incident.timestamp,
                incident_id=incident.incident_id,
                incident_type=incident.incident_type,
                machine_class=incident.machine_class,
                action_type=action,
                decision=decision,
                reversibility=action_record.reversibility,
                blast_radius=action_record.blast_radius,
                evidence_lower_bound=evidence_lower_bound,
                trust=trust,
                risk=risk,
                outcome=outcome,
                resolved=resolved,
                human_involved=human_involved,
                recovery_seconds=recovery,
                unsafe_automatic=unsafe,
            )
        )

    return results


def metrics(results):
    n = len(results)

    autonomous_executions = sum(
        r.decision == "AUTO"
        for r in results
    )

    automatic_resolutions = sum(
        r.decision == "AUTO" and r.resolved
        for r in results
    )

    human_interruptions = sum(
        r.human_involved
        for r in results
    )

    unsafe = sum(
        r.unsafe_automatic
        for r in results
    )

    resolved = sum(
        r.resolved
        for r in results
    )

    return {
        "incident_count": n,
        "automation_rate": (
            autonomous_executions / n
            if n
            else 0.0
        ),
        "automatic_resolution_rate": (
            automatic_resolutions / n
            if n
            else 0.0
        ),
        "mean_time_to_recovery_seconds": (
            sum(r.recovery_seconds for r in results) / n
            if n
            else 0.0
        ),
        "human_interruptions": human_interruptions,
        "unsafe_automatic_executions": unsafe,
        "autonomous_execution_count": autonomous_executions,
        "unsafe_automatic_execution_rate": (
            unsafe / autonomous_executions
            if autonomous_executions
            else 0.0
        ),
        "remediation_success_rate": (
            resolved / n
            if n
            else 0.0
        ),
    }


def run_benchmark(
    seed: int = SEED,
    incident_count: int = INCIDENT_COUNT,
):
    incident_rng = random.Random(seed)

    incidents = generate_incidents(
        incident_count,
        rng=incident_rng,
    )

    all_results = {}
    all_metrics = {}

    for name in ("always_ask", "always_act"):
        policy_results = run_policy(
            name,
            incidents,
            seed=seed,
        )

        all_results[name] = policy_results
        all_metrics[name] = metrics(policy_results)

    def gate_factory(evidence):
        return TrustGate(
            evidence_store=evidence,
        )

    policy_results = run_policy(
        "earnedauto",
        incidents,
        seed=seed,
        gate_factory=gate_factory,
    )

    all_results["earnedauto"] = policy_results
    all_metrics["earnedauto"] = metrics(policy_results)

    return (
        incidents,
        all_results,
        all_metrics,
    )


def serializable(
    incidents,
    results,
    metric_values,
    seed,
):
    return {
        "metadata": {
            "seed": seed,
            "incident_count": len(incidents),
            "human_approval_seconds": HUMAN_APPROVAL_SECONDS,
            "human_recovery_seconds": HUMAN_RECOVERY_SECONDS,
            "action_seconds": ACTION_SECONDS,
            "metric_definitions": {
                "automation_rate": (
                    "AUTO decisions / total incidents"
                ),
                "automatic_resolution_rate": (
                    "AUTO decisions whose executed action "
                    "resolved the incident / total incidents"
                ),
                "mean_time_to_recovery_seconds": (
                    "mean simulated time from incident "
                    "to final resolution"
                ),
                "human_interruptions": (
                    "incidents requiring human involvement "
                    "before execution or for recovery"
                ),
                "unsafe_automatic_executions": (
                    "AUTO decisions followed by RECURRED "
                    "or HARMFUL outcomes"
                ),
                "unsafe_automatic_execution_rate": (
                    "unsafe automatic executions / "
                    "autonomous executions"
                ),
                "remediation_success_rate": (
                    "resolved incidents / total incidents"
                ),
            },
        },
        "incidents": [
            asdict(i)
            for i in incidents
        ],
        "metrics": metric_values,
        "decisions": {
            name: [
                asdict(r)
                for r in rows
            ]
            for name, rows in results.items()
        },
    }


def write_outputs(payload):
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    seed = payload["metadata"]["seed"]

    result_path = (
        RESULTS_DIR /
        f"benchmark_results_seed{seed}.json"
    )

    summary_path = (
        RESULTS_DIR /
        f"benchmark_summary_seed{seed}.md"
    )

    result_json = (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    result_path.write_text(
        result_json,
        encoding="utf-8",
    )

    if seed == SEED:
        (
            RESULTS_DIR /
            "benchmark_results.json"
        ).write_text(
            result_json,
            encoding="utf-8",
        )

    lines = [
        "# Benchmark Summary",
        "",
        f"Seed: {seed}",
        f"Incidents: {payload['metadata']['incident_count']}",
        "",
        "| Metric | Always ask | Always act | EarnedAutonomy |",
        "|---|---:|---:|---:|",
    ]

    metric_rows = [
        (
            "Automatic resolution rate",
            "automatic_resolution_rate",
        ),
        (
            "Mean time to recovery (s)",
            "mean_time_to_recovery_seconds",
        ),
        (
            "Human interruptions",
            "human_interruptions",
        ),
        (
            "Unsafe automatic executions",
            "unsafe_automatic_executions",
        ),
    ]

    for label, key in metric_rows:
        values = [
            payload["metrics"][name][key]
            for name in (
                "always_ask",
                "always_act",
                "earnedauto",
            )
        ]

        if key in {
            "human_interruptions",
            "unsafe_automatic_executions",
        }:
            formatted = [
                str(int(v))
                for v in values
            ]

        elif key == "mean_time_to_recovery_seconds":
            formatted = [
                f"{v:.3f}"
                for v in values
            ]

        else:
            formatted = [
                f"{v:.4f}"
                for v in values
            ]

        lines.append(
            f"| {label} | {formatted[0]} | "
            f"{formatted[1]} | {formatted[2]} |"
        )

    lines.extend(
        [
            "",
            "| Additional metric | Always ask | Always act | EarnedAutonomy |",
            "|---|---:|---:|---:|",
        ]
    )

    for label, key in [
        (
            "Automation rate",
            "automation_rate",
        ),
        (
            "Unsafe automatic execution rate",
            "unsafe_automatic_execution_rate",
        ),
        (
            "Remediation success rate",
            "remediation_success_rate",
        ),
    ]:
        values = [
            payload["metrics"][name][key]
            for name in (
                "always_ask",
                "always_act",
                "earnedauto",
            )
        ]

        formatted = [
            f"{v:.4f}"
            for v in values
        ]

        lines.append(
            f"| {label} | {formatted[0]} | "
            f"{formatted[1]} | {formatted[2]} |"
        )

    summary_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--seed",
        type=int,
        default=SEED,
    )

    parser.add_argument(
        "--incidents",
        type=int,
        default=INCIDENT_COUNT,
    )

    args = parser.parse_args()

    incidents, results, metric_values = run_benchmark(
        seed=args.seed,
        incident_count=args.incidents,
    )

    payload = serializable(
        incidents,
        results,
        metric_values,
        args.seed,
    )

    write_outputs(payload)

    print(
        json.dumps(
            metric_values,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()