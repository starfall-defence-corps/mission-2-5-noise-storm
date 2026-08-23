---
CLASSIFICATION: LIEUTENANT EYES ONLY
MISSION: 2.5 — NOISE STORM
DOCUMENT: EXERCISES — Phase-by-Phase Operational Instructions
---

# EXERCISES — MISSION 2.5: NOISE STORM

Complete each phase in sequence. Run `make test` after each phase. Do not advance until ARIA confirms compliance.

**Two directories, two purposes:**

- **Ansible commands** (`ansible`, `ansible-playbook`): Run from `workspace/` where `ansible.cfg` lives.
- **Make commands** (`make test`, `make reset`): Run from the **project root** (where the `Makefile` lives).

When a phase says "Run ARIA's Verification", return to the project root first:

```bash
cd ..        # from workspace/ back to project root
make test
cd workspace # return to workspace for the next phase
```

**A note on `make test`**: unlike a simple pass/fail check, `make test` exercises **all five phases every time** — including running your own `block-ioc.yml` against the fleet, and, once you reach it, triggering the Storm's address rotation for Phase 5. This means `make test` mutates the live lab. If you want a clean, freshly scored run from Phase 1 onward, run `make reset` first — it re-arms the Storm on its primary address and clears any firewall state from prior runs.

If ARIA ever reports the range as offline or **INCONCLUSIVE**, this is never counted as a pass or a fail — it means the Storm's container has stalled. Run `make reset` and try again.

---

## PHASE 0: Launch the Fleet, Observe the Storm

> Before any defence can begin, your fleet must be online — and so must the enemy. Launch the fleet, then confirm the Storm has already begun landing.

### Step 0.1 — Preflight Check

From the **project root directory**, confirm your machine is mission-ready:

```bash
make doctor
```

### Step 0.2 — Start the Fleet and the Range

From the **project root directory** (not `workspace/`), run:

```bash
make setup
```

This builds the Docker containers, generates SSH credentials, starts all three fleet nodes, and arms the noise storm against them. Wait for the output to confirm:

```
  Fleet Status: 3 nodes ONLINE — and under attack.
```

### Step 0.3 — Activate the Python Environment

`make setup` creates a Python virtual environment with Ansible and testing tools. **Activate it** before running any Ansible commands:

```bash
source venv/bin/activate
```

Your terminal prompt will show `(venv)` when active. You need to do this once per terminal session. If you open a new terminal, activate again.

### Step 0.4 — Orient Yourself

You are not attacking anything in this mission — you are defending. The Storm is opaque range infrastructure: you will never see its code or touch its container. Everything you write lives in `workspace/`, targets your own fleet, and is applied fleet-wide.

Take a look at what's already scaffolded for you:

```bash
cd workspace
cat site.yml
ls roles/
```

`site.yml` applies three roles — `hardening`, `defense`, and `observability` — to the whole fleet. Each role's `tasks/main.yml` is a TODO stub. You will fill them in as you work through the phases below.

### Step 0.5 — If Things Go Wrong

If containers are in a bad state, the range has stalled, or you need a clean start at any point during the mission:

```bash
make reset
```

This destroys all containers, rebuilds them, and re-arms the Storm on its primary address. Your work in `workspace/` (roles, playbooks, reports) is preserved — only the lab state is reset.

---

## PHASE 1: Key-Only Auth

> The Storm is guessing its way in — hammering SSH with password attempts. Take the password vector away entirely. If the fleet only accepts keys, guessing is worthless.

### What You Are Building

You will fill in `workspace/roles/hardening/tasks/main.yml` to disable password authentication on every node's SSH daemon, while keeping key-based authentication working — your `cadet` key must still get you in.

### Step 1.1 — Understand the Objective

- Set `PasswordAuthentication no` in the sshd configuration. Consider `KbdInteractiveAuthentication no` too, for the same reason.
- **Keep `PubkeyAuthentication yes`.** You are removing the password vector, not locking yourself out.
- The change must actually take effect — sshd needs to reload or restart after the config changes.

A drop-in file under `/etc/ssh/sshd_config.d/` is cleaner than editing the main config directly. A handler, notified only when the config changes, is the idiomatic way to reload sshd.

### Step 1.2 — Edit the Role

Open `workspace/roles/hardening/tasks/main.yml` and replace the TODO task. You will likely need:

- A task to template or copy a config drop-in (`ansible.builtin.template` or `ansible.builtin.copy`) into `/etc/ssh/sshd_config.d/`.
- A `notify` on that task pointing at a handler that reloads/restarts `ssh`/`sshd`.
- A handler in `roles/hardening/handlers/main.yml` (create this file if it does not exist) to perform the reload.

### Step 1.3 — Apply It

From `workspace/`:

```bash
ansible-playbook site.yml
```

This applies all three roles fleet-wide, including your Phase 1 work. It is safe to run repeatedly — Phases 2 and 3 will simply report "replace me" until you fill them in too.

### Step 1.4 — Run ARIA's Verification

```bash
make test
```

ARIA is watching the Storm's own telemetry: it checks that the Storm's `password_auth_offered` signal has fallen to `False` on all three nodes, and stays there. This can take a short while to register — give it a moment before assuming failure.

---

## PHASE 2: Rate-Limit & Ban

> Key-only auth stopped the Storm getting in — but it has not stopped knocking. Every failed attempt is still a connection. Stand up a ban so the Storm gets dropped before it can even try.

### What You Are Building

You will fill in `workspace/roles/defense/tasks/main.yml` to configure and enable **fail2ban** with an sshd jail tuned to trip fast and hold long.

### Step 2.1 — Understand the Objective

- fail2ban ships on the fleet nodes already, dormant. Ensure it is installed/present and enabled.
- Configure an sshd jail. Suggested tuning: `maxretry = 3`, `findtime = 30`, `bantime = 600` — trip fast, ban long.
- Drop your jail configuration as a file under `/etc/fail2ban/jail.d/` (a `.local` file) — do not edit `jail.conf` directly.
- Enable and start the `fail2ban` service. Reload it if configuration changes on a later run.

### Step 2.2 — Edit the Role

Open `workspace/roles/defense/tasks/main.yml` and replace the TODO task(s). You will likely need:

- A task to ensure the `fail2ban` package/service is present (`ansible.builtin.package` or `ansible.builtin.service`, depending on what the base image ships).
- A task to template/copy your jail config into `/etc/fail2ban/jail.d/`.
- A task (or `notify`-driven handler) to enable and start the service, and reload it on config change.

### Step 2.3 — Apply and Verify

```bash
ansible-playbook site.yml
```

```bash
cd ..
make test
cd workspace
```

**This phase's check can be slow.** ARIA is waiting for the ban to actually trip against a live, continuous attack, then confirming it holds. `make test` for Phase 2 can take up to 2-3 minutes — that is expected, not a failure.

ARIA checks the Storm's `tcp_open` signal falls to `False` on every node — a strictly stronger outcome than Phase 1, since the connection no longer completes at all (not even to be rejected on password).

---

## PHASE 3: See the Storm

> You cannot defend what you cannot see. Two things are needed: a clear picture of who is attacking you right now, and a way for the SOC to watch the fight from one place.

This phase has two deliverables.

### Deliverable A — Triage Report

### Step 3.1 — Understand the Objective

`workspace/collect-triage.yml` must:

1. Gather each node's SSH auth log. `/var/log/auth.log` contains lines like `Invalid user baduser from 172.30.0.20 port 41122 ...` — the source IP is the offender.
2. Tally the offending source IPs and identify the busiest one — that is your prime suspect, the live IOC.
3. Render `workspace/templates/noise-report.md.j2` into `workspace/reports/noise-report.md`, naming that IP.

**Tip:** Your own management SSH connection may also show up as noise in the logs (via the Docker host gateway, `192.168.65.1`). You do not need to filter this out perfectly — ARIA only requires that the real attacker's IP appears in your report — but filtering to the `172.30.0.0/24` range, or simply reporting the top few offenders, will make your report more useful to you.

### Step 3.2 — Gather and Tally

Fill in the first task in `collect-triage.yml`. You will likely need `ansible.builtin.shell` or `ansible.builtin.command` to read and grep/tally `/var/log/auth.log` on each node, registering the result.

### Step 3.3 — Render the Report

The report is rendered **once**, on the control node — not once per fleet node. Use:

```yaml
delegate_to: localhost
run_once: true
become: false
```

on your `ansible.builtin.template` task, targeting `templates/noise-report.md.j2` → `reports/noise-report.md`. To build a fleet-wide picture inside that single render, use `hostvars` and `groups['fleet']` in the template — see `workspace/templates/noise-report.md.j2` for the TODO markers showing where the prime suspect and per-node breakdown belong.

### Step 3.4 — Run It

From `workspace/`:

```bash
ansible-playbook collect-triage.yml
```

Check the result:

```bash
cat reports/noise-report.md
```

Confirm it actually names an IP address in the `172.30.0.0/24` range — that is your evidence for Phase 4.

### Deliverable B — Log Forwarding

### Step 3.5 — Understand the Objective

Fill in `workspace/roles/observability/tasks/main.yml` to configure rsyslog on every node to forward its logs to the SOC collector — `sdc-app` at `172.30.0.11`, port `514`. For example, a rule of:

```
*.* @@172.30.0.11:514
```

(`@@` is TCP, `@` is UDP — either is accepted.) Drop this as a file under `/etc/rsyslog.d/`, then restart/reload `rsyslog` so it takes effect.

### Step 3.6 — Apply and Verify

```bash
ansible-playbook site.yml
```

```bash
cd ..
make test
cd workspace
```

ARIA checks that your triage report exists and names the Storm's *current* live IOC, and that an uncommented rsyslog forward rule is present on every node.

---

## PHASE 4: Block the IOC

> Key-only auth and the ban have shut down the SSH vector — but the Storm is still fuzzing your web service on port 80, from the same address. A port-22 ban does not touch this. You need a wider block.

### What You Are Building

You will write `workspace/block-ioc.yml` — a standalone, **parameterised** playbook that firewall-drops a given IOC's traffic to the *whole host*, on *every port*, fleet-wide. It accepts the address to block as an extra variable, not a hardcoded value.

### Step 4.1 — Understand the Objective

- Accept the indicator via `-e ioc_ip=<ip>`. The scaffold already has an `ansible.builtin.assert` guarding that `ioc_ip` is defined — leave that in place.
- Drop **all** traffic from `ioc_ip`, not just port 22. Use `ansible.builtin.iptables`: `chain: INPUT`, `source: "{{ ioc_ip }}"`, `jump: DROP`.
- Make it idempotent — running it twice against the same IP should not duplicate rules or fail.
- This must run fleet-wide, on all three nodes.

### Step 4.2 — Write the Playbook

Replace the TODO task in `workspace/block-ioc.yml`.

### Step 4.3 — Test It Yourself

You know the live IOC from your Phase 3 triage report. Run your playbook against it manually before ARIA does:

```bash
ansible-playbook block-ioc.yml -e ioc_ip=<the-ip-from-your-report>
```

### Step 4.4 — Run ARIA's Verification

```bash
cd ..
make test
cd workspace
```

For this phase, **ARIA runs your own `block-ioc.yml`** against the Storm's live source IP, then checks that the Storm's `web_open` signal falls to `False` on all three nodes. If you only banned port 22 in Phase 2, this phase will show you why that was not enough.

---

## PHASE 5: Hold the Line (Capstone)

> The attacker rotates to a new source address. Everything you built so far gets tested against an indicator you have not seen yet.

### What Happens

ARIA moves the Storm onto its **secondary** source address, then re-runs your own `block-ioc.yml` — the exact same file, unmodified — against the new indicator. If `block-ioc.yml` is properly parameterised on `ioc_ip`, it seals the new address automatically and the fleet stays dark. If you hardcoded the original address anywhere in the playbook, the Storm gets straight back in and this phase fails.

### Step 5.1 — Nothing New to Write (If You Parameterised Correctly)

There is no new deliverable for this phase if Phase 4 was built the way the brief asked — your `block-ioc.yml` should already generalise to any `ioc_ip`. This phase exists to prove it.

### Step 5.2 — If You Hardcoded the Original IP

Go back to `workspace/block-ioc.yml` and remove the hardcoded address — it must come only from `{{ ioc_ip }}`. If you need to discover the Storm's new address to sanity-check your fix yourself, regenerate your triage report:

```bash
ansible-playbook collect-triage.yml
cat reports/noise-report.md
```

### Step 5.3 — Run ARIA's Final Verification

```bash
cd ..
make test
cd workspace
```

ARIA checks that, with the Storm now on its rotated address, `web_open` is `False` on all three nodes.

---

## MISSION COMPLETE — DEBRIEF CHECKLIST

Before closing this mission, confirm the following:

- [ ] `roles/hardening` disables password SSH auth fleet-wide, keeps key auth working
- [ ] `roles/defense` installs, configures, and enables a tuned fail2ban sshd jail fleet-wide
- [ ] `collect-triage.yml` gathers auth-log evidence and renders `reports/noise-report.md`, naming the live IOC
- [ ] `roles/observability` forwards every node's logs to the SOC collector at `172.30.0.11:514`
- [ ] `block-ioc.yml` firewall-drops a given `ioc_ip`'s traffic to the whole host, fleet-wide, and is idempotent
- [ ] `block-ioc.yml` is parameterised — no hardcoded IOC address anywhere in the file
- [ ] `make test` reports all phases passing, including Phase 5 after the Storm's rotation

If any item is incomplete, return to the corresponding phase and complete it before closing the mission record.

---

*SDC Cyber Command — 2187 — LIEUTENANT EYES ONLY*
