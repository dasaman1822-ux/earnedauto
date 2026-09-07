# Earned Autonomy: A Reversibility and Evidence Gate for Automated Infrastructure Remediation

## 1. Introduction

Modern infrastructure systems can detect failures and perform automated remediation actions. Automation can reduce recovery time and the amount of work required from human operators. However, automatically performing an incorrect remediation can make an incident worse.

This project explores a trust gate for automated infrastructure remediation. The gate will decide whether a remediation action should be **AUTO**, **PROPOSE**, or **ESCALATE**.

The decision will consider three main factors: the **reversibility** of the action, its **blast radius**, and accumulated **evidence** about whether the action is successful in a particular context.

The central idea is **earned autonomy**. An action should gain permission to operate automatically as evidence of successful behavior accumulates. If the action fails, its level of autonomy should be reduced.

---

## 2. Problem Statement

A self-healing infrastructure system needs to balance automation and safety. A highly automated system can reduce recovery time, but automatically executing an incorrect action can cause additional damage.

The project therefore asks:

> How can a remediation system decide when it has enough evidence and sufficiently low risk to perform an action automatically?

The proposed trust gate will provide three possible decisions:

- **AUTO** — execute the action automatically.
- **PROPOSE** — recommend the action but require human approval.
- **ESCALATE** — require human intervention.

---

## 3. Project Scope

The project focuses on the decision-making layer between fault detection and remediation execution.

The project does not build a monitoring system, dashboard, or machine-learning failure detector. Instead, a simulator is used to generate infrastructure incidents and provide a controlled environment for evaluating the trust gate.

The project considers six remediation actions:

1. Restart a stateless service
2. Requeue a failed job
3. Reset a device driver
4. Drain a node and migrate work
5. Reclaim disk space by deleting temporary files
6. Escalate to a human

The simulator will later be used to evaluate whether the trust gate can increase automation while limiting unsafe automatic actions.

---

## 4. Dataset and Incident Analysis

The Blue Gene/L (BGL) public log dataset was selected to understand real infrastructure incident patterns.

The analysis identified:

- **4,747,963** total log records
- **4,399,503** normal records
- **348,460** alert records
- **7.34%** alert records
- **42** distinct alert labels

The most frequent alert labels included `KERNDTLB`, `KERNSTOR`, `APPSEV`, `KERNMNTF`, and `KERNTERM`.

A Python script, `src/analyze_bgl.py`, was created to read the BGL log and count the labels.

The BGL dataset is used only to understand the distribution of infrastructure alerts and to inform the simulator. The simulator does not attempt to reproduce all 42 BGL labels directly.

---

## 5. Incident and Action Data Structures

Two simple data classes were created for the simulator.

### Incident

Each incident contains:

- Incident ID
- Incident type
- Machine class
- Timestamp

Example:

```text
INC-000001
storage_error
storage_node
2026-09-07 22:30:00