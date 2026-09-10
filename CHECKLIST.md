# Mission 2.5: Noise Storm — Progress Tracker

**Rank**: Lieutenant
**Arc**: Incident Response — Act 1 of 2 (Act 2 is [Mission 2.6: Counterattack](https://github.com/starfall-defence-corps/mission-2-6-counterattack))

Check each item off as you complete it. Run `make test` after each phase — it
re-scores all five. If a phase is blocked, see `docs/HINTS.md`. For a clean scored
run from the top, `make reset` first.

---

## Phase 0: Weather Report

- [ ] `make doctor` — machine is mission-ready
- [ ] `make setup` — fleet is online **and under attack**
- [ ] Confirmed the storm is landing (a fresh `make test` fails Phase 1 — that's expected)

---

## Phase 1: Key-Only Auth

- [ ] Filled in `roles/hardening` — `PasswordAuthentication no`, key auth kept on
- [ ] sshd reloads on change (handler), applied fleet-wide via `ansible-playbook site.yml`
- [ ] ARIA: the storm can no longer get a password prompt on any node

---

## Phase 2: Rate-Limit & Ban

- [ ] Filled in `roles/defense` — fail2ban sshd jail, tuned to trip fast, ban long
- [ ] Service enabled + started fleet-wide
- [ ] ARIA: the storm's SSH probes stop landing on every node (may take ~1-2 min to trip)

---

## Phase 3: See the Storm

- [ ] `collect-triage.yml` gathers auth-log evidence and renders `reports/noise-report.md`
- [ ] The report names the storm's **current source IP** (gathered live, not hand-typed)
- [ ] Filled in `roles/observability` — rsyslog forwards to the SOC collector (sdc-app) fleet-wide
- [ ] ARIA: report present + names the live IOC; forwarding configured everywhere

---

## Phase 4: Block the IOC

- [ ] Wrote `block-ioc.yml` — **parameterised** on `ioc_ip`, drops all traffic from that IP, fleet-wide
- [ ] ARIA runs your playbook against the live source and the storm goes dark on port 80 everywhere

---

## Phase 5: Hold the Line

- [ ] The attacker rotated address — your **parameterised** block sealed the new IOC too
- [ ] (If you hardcoded the old IP: regenerate your triage report, find the new address, parameterise)
- [ ] ARIA: fleet stays dark after the rotation

---

## Verification

- [ ] `make test` — all five phases pass, storm defeated
- [ ] `make submit` — work submitted for ARIA review

**Next stop**: [Mission 2.6 — Counterattack](https://github.com/starfall-defence-corps/mission-2-6-counterattack)
