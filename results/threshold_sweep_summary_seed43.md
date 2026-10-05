# Week 5 Threshold Sweep

Seed: 43
Incidents: 1000
AUTO thresholds: [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
PROPOSE thresholds: [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]

The sweep excludes configurations where PROPOSE_THRESHOLD >= AUTO_THRESHOLD.

## Observations

- See `threshold_sweep.json` for the complete machine-readable experiment output.
- The chart plots automatic resolution rate against unsafe automatic execution rate.
- No threshold configuration is selected as 'best' without considering the safety objective.
