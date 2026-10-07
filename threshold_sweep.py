import argparse
import json
import random
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import yaml

from benchmark import (
    INCIDENT_COUNT,
    candidate_action,
    metrics,
    run_policy,
)
from src.evidence import EvidenceStore
from src.gate import TrustGate
from src.simulator import Outcome, OutcomeType, apply_outcome_to_evidence, generate_incidents, generate_outcome

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
AUTO_THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
PROPOSE_THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]


def run_one(auto_threshold, propose_threshold, incidents, seed):
    if propose_threshold >= auto_threshold:
        return None

    with tempfile.TemporaryDirectory() as tmp:
        threshold_path = Path(tmp) / "thresholds.yaml"
        threshold_path.write_text(
            yaml.safe_dump(
                {
                    "AUTO_THRESHOLD": auto_threshold,
                    "PROPOSE_THRESHOLD": propose_threshold,
                    "RISK_CEILING": 0.60,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        rng = random.Random(seed)
        evidence = EvidenceStore()
        gate = TrustGate(
            thresholds_config=threshold_path,
            evidence_store=evidence,
        )
        results = []
        for incident in incidents:
            action = candidate_action(incident)
            gate_result = gate.decide(action, incident.machine_class)
            decision = gate_result.decision

            # Reuse the benchmark execution model with the custom thresholds.
            outcome = generate_outcome(action, rng=rng).outcome_type
            apply_outcome_to_evidence(
                Outcome(outcome),
                action,
                incident.machine_class,
                evidence,
            )
            human = decision != "AUTO"

            from benchmark import ACTION_SECONDS, HUMAN_APPROVAL_SECONDS, HUMAN_RECOVERY_SECONDS
            recovery = ACTION_SECONDS[action]
            if decision == "PROPOSE":
                recovery += HUMAN_APPROVAL_SECONDS
            elif decision == "ESCALATE":
                recovery += HUMAN_RECOVERY_SECONDS
            if outcome != OutcomeType.RESOLVED:
                recovery += HUMAN_RECOVERY_SECONDS
                human = True

            from benchmark import IncidentResult
            results.append(
                IncidentResult(
                    timestamp=incident.timestamp,
                    incident_id=incident.incident_id,
                    incident_type=incident.incident_type,
                    machine_class=incident.machine_class,
                    action_type=action,
                    decision=decision,
                    reversibility=gate_result.reversibility,
                    blast_radius=gate_result.blast_radius,
                    evidence_lower_bound=gate_result.evidence_lower_bound,
                    trust=gate_result.trust,
                    risk=gate_result.risk,
                    outcome=outcome,
                    resolved=outcome == OutcomeType.RESOLVED,
                    human_involved=human,
                    recovery_seconds=recovery,
                    unsafe_automatic=(
                        decision == "AUTO" and outcome != OutcomeType.RESOLVED
                    ),
                )
            )

        m = metrics(results)
        m.update({
            "AUTO_THRESHOLD": auto_threshold,
            "PROPOSE_THRESHOLD": propose_threshold,
            "seed": seed,
        })
        return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--incidents", type=int, default=INCIDENT_COUNT)
    args = parser.parse_args()

    incident_rng = random.Random(args.seed)
    incidents = generate_incidents(args.incidents, rng=incident_rng)

    rows = []
    for auto_threshold in AUTO_THRESHOLDS:
        for propose_threshold in PROPOSE_THRESHOLDS:
            row = run_one(auto_threshold, propose_threshold, incidents, args.seed)
            if row is not None:
                rows.append(row)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"threshold_sweep_seed{args.seed}.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    plt.figure(figsize=(8, 5))
    for propose in sorted({r["PROPOSE_THRESHOLD"] for r in rows}):
        subset = [r for r in rows if r["PROPOSE_THRESHOLD"] == propose]
        subset.sort(key=lambda r: r["AUTO_THRESHOLD"])
        plt.plot(
            [r["automation_rate"] * 100 for r in subset],
            [r["unsafe_automatic_execution_rate"] * 100 for r in subset],
            marker="o",
            label=f"PROPOSE={propose:.2f}",
        )
    plt.xlabel("Automation rate (%)")
    plt.ylabel("Unsafe automatic execution rate (%)")
    plt.title("Automation–Safety Trade-off Across Thresholds")
    plt.grid(axis="both", alpha=0.3)
    plt.legend(title="Proposal threshold")
    plt.tight_layout()
    plt.savefig(
    RESULTS_DIR / f"automation_vs_unsafe_execution_seed{args.seed}.png",
    dpi=300,
)
    plt.close()

    summary = [
        "# Threshold Sweep",
        "",
        f"Seed: {args.seed}",
        f"Incidents: {args.incidents}",
        f"AUTO thresholds: {AUTO_THRESHOLDS}",
        f"PROPOSE thresholds: {PROPOSE_THRESHOLDS}",
        "",
        "The sweep excludes configurations where PROPOSE_THRESHOLD >= AUTO_THRESHOLD.",
        "",
        "## Observations",
        "",
        f"- See `threshold_sweep_seed{args.seed}.json` for the complete machine-readable experiment output.",
        "- The chart plots automation rate against unsafe automatic execution rate.",
        "- No threshold configuration is selected as 'best' without considering the safety objective.",
    ]
    (RESULTS_DIR / f"threshold_sweep_summary_seed{args.seed}.md").write_text(
        "\n".join(summary) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
