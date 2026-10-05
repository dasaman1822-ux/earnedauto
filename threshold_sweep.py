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
from src.simulator import generate_incidents

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

            # Reuse the benchmark's execution model through the same policy engine
            # shape, but with the custom gate.
            if decision == "AUTO":
                outcome = __import__("src.simulator", fromlist=["generate_outcome"]).generate_outcome(
                    action, rng=rng
                ).outcome_type
                from src.simulator import apply_outcome_to_evidence
                apply_outcome_to_evidence(
                    type("Outcome", (), {"outcome_type": outcome})(),
                    action,
                    incident.machine_class,
                    evidence,
                )
                human = False
            elif decision == "PROPOSE":
                outcome = __import__("src.simulator", fromlist=["generate_outcome"]).generate_outcome(
                    action, rng=rng
                ).outcome_type
                from src.simulator import apply_outcome_to_evidence
                apply_outcome_to_evidence(
                    type("Outcome", (), {"outcome_type": outcome})(),
                    action,
                    incident.machine_class,
                    evidence,
                )
                human = True
            else:
                outcome = __import__("src.simulator", fromlist=["generate_outcome"]).generate_outcome(
                    action, rng=rng
                ).outcome_type
                from src.simulator import apply_outcome_to_evidence
                apply_outcome_to_evidence(
                    type("Outcome", (), {"outcome_type": outcome})(),
                    action,
                    incident.machine_class,
                    evidence,
                )
                human = True

            from benchmark import ACTION_SECONDS, HUMAN_APPROVAL_SECONDS, HUMAN_RECOVERY_SECONDS
            from src.simulator import OutcomeType

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
                    incident.incident_id,
                    action,
                    decision,
                    outcome,
                    human,
                    recovery,
                    decision == "AUTO" and outcome != OutcomeType.RESOLVED,
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
        "# Week 5 Threshold Sweep",
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
        "- See `threshold_sweep.json` for the complete machine-readable experiment output.",
        "- The chart plots automatic resolution rate against unsafe automatic execution rate.",
        "- No threshold configuration is selected as 'best' without considering the safety objective.",
    ]
    (RESULTS_DIR / f"threshold_sweep_summary_seed{args.seed}.md").write_text(
        "\n".join(summary) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
