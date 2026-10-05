from dataclasses import dataclass
import random
from .evidence import EvidenceStore
@dataclass
class Incident:
    incident_id: str
    incident_type: str
    machine_class: str
    timestamp: str
class OutcomeType:
    RESOLVED="resolved"; RECURRED="recurred"; HARMFUL="harmful"
@dataclass
class Outcome:
    outcome_type: str
INCIDENT_TYPES=["kernel_error","storage_error","filesystem_failure","communication_failure","application_error"]
INCIDENT_WEIGHTS=[0.5235,0.1831,0.0930,0.0177,0.1827]
MACHINE_CLASSES=["compute_node","storage_node","scheduler"]
OUTCOME_PROBABILITIES={
 "restart_service":(0.80,0.15,0.05),
 "requeue_job":(0.45,0.35,0.20),
 "reset_driver":(0.60,0.25,0.15),
 "drain_node":(0.50,0.25,0.25),
 "reclaim_disk":(0.40,0.30,0.30),
}
INCIDENT_ACTIONS={
 "kernel_error":"reset_driver",
 "storage_error":"reclaim_disk",
 "filesystem_failure":"restart_service",
 "communication_failure":"drain_node",
 "application_error":"requeue_job",
}
def generate_incidents(count=1000, rng=None):
    rng=rng or random
    return [Incident(f"INC-{i+1:06d}", rng.choices(INCIDENT_TYPES,weights=INCIDENT_WEIGHTS,k=1)[0],
                     rng.choice(MACHINE_CLASSES),"2026-09-07 22:30:00") for i in range(count)]
def generate_outcome(action_type,rng=None):
    rng=rng or random
    probs=OUTCOME_PROBABILITIES[action_type]
    t=rng.choices([OutcomeType.RESOLVED,OutcomeType.RECURRED,OutcomeType.HARMFUL],weights=probs,k=1)[0]
    return Outcome(t)
def apply_outcome_to_evidence(outcome,action_type,machine_class,evidence_store):
    if outcome.outcome_type==OutcomeType.RESOLVED: evidence_store.record_success(action_type,machine_class)
    else: evidence_store.record_failure(action_type,machine_class)
