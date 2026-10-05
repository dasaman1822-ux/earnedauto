# Validation Report

This bundle was validated in an isolated reconstruction of the current EarnedAutonomy architecture based on the project source available in the conversation.

## Verified

- pytest: 5 passed
- benchmark seed 42 executed twice
- complete structured JSON outputs were byte-identical
- threshold sweep executed for valid AUTO/PROPOSE threshold pairs
- seed 43 benchmark executed
- seed 43 threshold sweep executed
- Week 5 automation-vs-unsafe chart generated

## Important boundary

The user's live Windows repository at `C:\Users\KIIT0001\earnedauto` was not directly mounted or connected to this session. Therefore this bundle is **validated code and generated results from an isolated reconstruction**, not a claim that the live repository was modified, committed, or pushed.

Before treating the project as complete, the bundle must be applied to the actual repository and the same commands rerun there.

## Seed 42 benchmark

Always ask:
- automation rate: 0.000
- automatic resolution rate: 0.000
- mean time to recovery: 291.685 s
- human interruptions: 1000
- unsafe automatic executions: 0

Always act:
- automation rate: 1.000
- automatic resolution rate: 0.528
- mean time to recovery: 171.685 s
- human interruptions: 472
- unsafe automatic executions: 472

EarnedAutonomy:
- automation rate: 0.002
- automatic resolution rate: 0.000
- mean time to recovery: 443.905 s
- human interruptions: 1000
- unsafe automatic executions: 2

Unsafe automatic execution rate for EarnedAutonomy at the default threshold was 1.000 in seed 42 because both autonomous executions were unsafe. This is an important negative result and is not hidden.

## Seed 43 benchmark

EarnedAutonomy:
- automation rate: 0.011
- automatic resolution rate: 0.011
- mean time to recovery: 442.320 s
- human interruptions: 989
- unsafe automatic executions: 0

The qualitative conclusion remains: EarnedAutonomy is far less autonomous than always-act but produces dramatically fewer unsafe automatic executions.

## Week 5

At seed 42 and PROPOSE_THRESHOLD=0.35:
- AUTO 0.50: automation 3.7%, unsafe executions 9
- AUTO 0.55: automation 2.5%, unsafe executions 7
- AUTO 0.60: automation 1.1%, unsafe executions 4
- AUTO 0.65: automation 0.2%, unsafe executions 2
- AUTO >= 0.70: no autonomous executions in this run

This is a real trade-off in the simulator: permissive AUTO thresholds increase automation but also increase unsafe autonomous actions.

## Scientific limitation

The current BGL dataset informs incident-type frequency, not remediation ground truth. The benchmark therefore uses an explicit deterministic incident-to-action simulation mapping and fixed action outcome probabilities. The results demonstrate behavior of the implemented simulated gate; they do not establish production remediation effectiveness.
