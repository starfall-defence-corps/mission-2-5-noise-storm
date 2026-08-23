---
CLASSIFICATION: ENSIGN EYES ONLY
MISSION: 2.5 — NOISE STORM
THEATRE: Starfall Defence Corps Academy
AUTHORITY: SDC Cyber Command, 2187
---

# OPERATION ORDER — MISSION 2.5: NOISE STORM

---

## 1. SITUATION

### 1a. Enemy Forces

An unidentified adversary has opened a sustained assault against fleet infrastructure. Origin: unknown. Designation: **THE STORM**. Modus operandi: relentless, automated probing of every node's SSH and web-facing ports from a fixed source address — a textbook indicator of compromise (IOC). The Storm does not need to be clever. It needs only to be patient, and it is hammering the fleet around the clock.

The Storm is opaque range infrastructure. You will never see its code, its container, or its operator. You cannot script against it, disable it, or negotiate with it. You can only observe what it does to your fleet and respond. Intelligence further indicates the adversary is capable of **rotating its source address** mid-engagement — do not assume the address you see today is the address you will see tomorrow.

### 1b. Friendly Forces

The **Starfall Defence Corps (SDC)** fleet — three nodes, hardened in prior engagements, now under sustained fire. `sdc-app`, `sdc-web`, and `sdc-db` are all being probed simultaneously. Prior mission doctrine (roles, variables, templates, firewall rules) holds, but none of it was built to weather a continuous storm. That gap is what this mission closes.

### 1c. Attachments / Support

**ARIA** (Automated Review & Intelligence Analyst) remains assigned. ARIA reads the Storm's own telemetry against your fleet and reports, phase by phase, whether the Storm is landing or being repelled.

### 1d. Operational Tool

All operations will be conducted using **ANSIBLE** — *Automated Network for Secure Infrastructure, Baseline Lockdown & Enforcement*. This is a defensive engagement. Every line of automation you write in this mission hardens, observes, or blocks. You will not write offensive code, and you will never interact with the Storm's infrastructure directly.

---

## 2. MISSION

Weather the noise storm. Harden the fleet's SSH exposure to key-only authentication. Stand up a rate-limit and ban against the relentless probing. Gain visibility over the attack — know the enemy's current address and centralise the fleet's logs. Firewall-block the Storm's traffic fleet-wide. Hold that block even after the Storm changes address.

**End state**: All three nodes key-only on SSH, banning repeat offenders, forwarding logs to the SOC collector, and firewalled against the Storm's traffic — including any address it rotates to after first contact.

---

## 3. EXECUTION

### 3a. Commander's Intent

A fleet that only reacts to today's attack will fall to tomorrow's. This mission is built in layers for that reason: authentication hardening, then rate-limiting, then observability, then a block — and finally, a test of whether that block was built to last or built to memorise one address. An operator who hardcodes the enemy's IP has not defended the fleet; they have defended against one bad afternoon. Build automation that holds the line against *any* indicator, not the one you happened to see first.

### 3b. Concept of Operations

Five sequential phases. Complete each phase before advancing. Full procedural detail is in **EXERCISES.md**.

| Phase | Task | Objective |
|-------|------|-----------|
| 1 | Key-Only Auth | Disable password authentication fleet-wide; stop the Storm's credential guessing |
| 2 | Rate-Limit & Ban | Stand up fail2ban against the SSH hammering; drop repeat offenders at the TCP level |
| 3 | See the Storm | Triage the attack into a report naming the live IOC; forward all fleet logs to the SOC |
| 4 | Block the IOC | Firewall-drop the Storm's traffic to the whole host, fleet-wide, on every port |
| 5 | Hold the Line | Withstand the Storm rotating to a new source address — capstone |

### 3c. Fleet Assets

All nodes are accessible via SSH. Credentials are uniform across the fleet. Every node also runs nginx on port 80 — the Storm probes both services.

| Designation | Role | IP Address | SSH Port |
|-------------|------|------------|----------|
| `sdc-app` | Fleet Application Node | 172.30.0.11 | 2221 |
| `sdc-web` | Fleet Web Server | 172.30.0.12 | 2222 |
| `sdc-db` | Fleet Database Server | 172.30.0.13 | 2223 |

**SSH User**: `cadet`
**Authentication**: SSH key located at `workspace/.ssh/cadet_key`

### 3d. Rules of Engagement

- This is a **defensive engagement only**. You will write and apply Ansible against your own fleet — never against the Storm's infrastructure. You do not have access to it, and you are not meant to.
- Do not modify anything under `.docker/` — that is range infrastructure, not fleet infrastructure. Your work lives entirely in `workspace/`.
- All defensive measures must be applied fleet-wide. A hardened `sdc-app` with an exposed `sdc-web` is not a hardened fleet.
- Your automation must generalise. Any indicator you block must be handled as a variable, not a literal — the Storm will test this directly.
- All findings are to be reproducible. If ARIA cannot verify your work, your work is not complete.

---

## 4. SUPPORT

| Resource | Function | Command |
|----------|----------|---------|
| **ARIA** | Verifies mission compliance; reports pass/fail per phase | `make test` |
| **HINTS.md** | Operational guidance if mission stalls | — |
| **Fleet Reset** | Rebuilds the fleet and re-arms the Storm on its primary address | `make reset` |

Run `make test` after each phase. Note that `make test` exercises **all five phases** every time — including running your own `block-ioc.yml` against the fleet and, in Phase 5, triggering the Storm's rotation. For a clean, freshly scored run, use `make reset` first.

If ARIA ever reports the range as offline or inconclusive, this is not a failed phase — the Storm's container has stalled. Run `make reset` and try again.

Consulting **HINTS.md** is authorised at Ensign rank. Using available intelligence is not weakness — it is doctrine.

---

## 5. COMMAND AND SIGNAL

**Reporting**: ARIA is your automated reporting chain. Her output is your after-action record.

**Commander's Final Order**: This mission does not end until the fleet is key-only on SSH, banning repeat offenders, observing and reporting the attack, and firewalled against the Storm's traffic — on its original address and any address it rotates to. No exceptions.

Proceed to **EXERCISES.md** for phase-by-phase operational instructions.

---

*SDC Cyber Command — 2187 — ENSIGN EYES ONLY*
