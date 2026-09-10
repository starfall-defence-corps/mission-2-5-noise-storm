# Mission 2.5: Noise Storm — Hints & Troubleshooting Guide

> 📚 Deeper reference: [FM-1 — Ansible Module Reference](https://github.com/starfall-defence-corps/sdc-academy/blob/main/field-manuals/FM-1-ansible-reference.md)

**Rank**: Lieutenant (Reduced Scaffolding)

This guide is your safety net. If something is not working, the answer is likely here. Read the relevant section carefully before asking for help.

---

## Phase 1 — Key-Only Auth Hints

**Inspecting sshd's current configuration.**
SSH into a node and check what sshd is actually running with:

```bash
make ssh-app
sudo sshd -T | grep -i passwordauth
sudo sshd -T | grep -i pubkeyauth
```

`sshd -T` prints the fully resolved, effective configuration — including everything pulled in from `/etc/ssh/sshd_config.d/`. This is more reliable than reading the raw config files, because it shows you what sshd actually believes, after all drop-ins are merged.

**"I changed the config but nothing happened."**
A config file on disk does nothing until sshd reloads it. If your task edited or templated a file but did not `notify` a handler (or the handler did not fire), sshd is still running on the old configuration. Check:

```bash
sudo systemctl status ssh
```

and look at recent reload/restart timestamps.

**Do NOT disable `PubkeyAuthentication`.**
The objective is to remove the *password* vector, not authentication entirely. If you set `PubkeyAuthentication no` by mistake, or omit it in a way that defaults to no, you will lock out every key-based login — including your own `cadet` key and, critically, Ansible's own connections on the next run.

**You cannot actually lock yourself out of the range.**
The `cadet` key used by `make ssh-*` and by Ansible's `ansible.cfg` is management infrastructure, separate from anything you are configuring in `sshd_config.d/`. As long as `PubkeyAuthentication yes` stays in effect, your key keeps working no matter what you do to password auth. If you ever see `Permission denied` fleet-wide after a Phase 1 change, the fix is almost always "re-check that `PubkeyAuthentication` is still `yes`" — not "the range is broken."

**Checking the storm's own signal.**
Phase 1 is graded on the Storm's telemetry (`password_auth_offered`), not just your config. If you have confirmed with `sshd -T` that password auth is off on all three nodes and `make test` is still failing Phase 1, give it a little time — the signal is sampled continuously and needs a moment to settle to `False` after your change lands.

---

## Phase 2 — fail2ban Hints

**Checking fail2ban's status directly on a node.**

```bash
make ssh-web
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

The second command shows the `sshd` jail specifically — currently banned IPs, total banned count, and whether the jail is even active. If `fail2ban-client status` shows no jails at all, your jail file is not being picked up (wrong directory, wrong extension, or the service was never restarted after you dropped it in).

**Jail files go under `jail.d/`, never `jail.conf`.**
`jail.conf` is the package default and gets overwritten on updates. Your jail belongs in `/etc/fail2ban/jail.d/*.local` (or `.conf` — fail2ban reads both from `jail.d/`), which fail2ban layers on top.

**"My jail file is there but nothing is banning."**
Two common causes:
- The service was never (re)started after the jail file was dropped — fail2ban does not hot-reload jail.d/ changes on its own; make sure your task enables **and** starts (or reloads) the service.
- `findtime` is set too generously relative to `maxretry`, so the Storm's probes never accumulate fast enough inside the window to trip the ban. The mission guidance (`maxretry = 3`, `findtime = 30`, `bantime = 600`) is deliberately aggressive because the Storm is continuous — a jail tuned for a normal production environment will likely be too lax here.

**This phase's `make test` is slow on purpose.**
ARIA needs to watch the ban actually trip against a live attack and then confirm it *holds*, not just that it fired once. Up to 2-3 minutes for Phase 2's `make test` is normal. If it is still failing well past that, re-check your jail is active with `fail2ban-client status sshd` before assuming your Ansible is wrong.

---

## Phase 3 — Triage & Log Forwarding Hints

**Reading `/var/log/auth.log` directly.**

```bash
make ssh-app
sudo grep "Invalid user" /var/log/auth.log | tail -20
```

Failed/invalid login attempts include the source IP at the end of the line, e.g. `Invalid user baduser from 172.30.0.20 port 41122`. Your `collect-triage.yml` needs to extract and tally that IP across all the lines it finds.

**Filtering out your own noise.**
Your management SSH connections (from `make ssh-*`, or Ansible itself) will sometimes show up in the log via the Docker host gateway address, `192.168.65.1`. You don't need a perfect filter — ARIA only checks that the real attacker's IP appears in your rendered report — but restricting your tally to the `172.30.0.0/24` range, or just reporting your top few offenders, avoids confusing yourself while you build the playbook.

**`delegate_to: localhost` + `run_once: true` — why both?**
Without `delegate_to: localhost`, a templating task would try to render the report *on each remote node* — wrong target, and you'd end up with (at best) three separate report files scattered across the fleet instead of one. Without `run_once: true`, the same templating task would still execute once per host in your play, overwriting the same local report file three times in a row (harmless here, but wasteful and a common source of confusion when debugging "why did my report only show the last host's data").

- `delegate_to: localhost` — run the *action* on the control node, not the target host.
- `run_once: true` — only execute the task once for the whole play, using the first host's context.
- `become: false` — you don't need (and don't have) root on your own control node.

**Accessing other hosts' facts from a `run_once` task.**
Since the template task runs once, delegated to localhost, you cannot rely on the per-host `hostvars` implicitly being "the current host." Use `hostvars['sdc-app']`, `hostvars['sdc-web']`, `hostvars['sdc-db']` (or loop `groups['fleet']`) explicitly inside the template or in vars you pass to it, so all three nodes' evidence ends up in the one rendered report.

**Log forwarding — how ARIA checks it.**
ARIA's check is a simple grep for an *uncommented* line containing `@` (forward syntax) somewhere in `/etc/rsyslog.conf` or `/etc/rsyslog.d/` on every node. A commented-out example line, or a rule that only exists on one node, will not satisfy it.

---

## Phase 4 — Firewall (iptables) Hints

**Idempotency with `ansible.builtin.iptables`.**
The `ansible.builtin.iptables` module is idempotent by default when you give it a specific, matching rule — it checks whether an equivalent rule already exists before adding another. The trap is usually the opposite: if your `source` or other match criteria differ slightly between runs (e.g. whitespace, or a different `chain`), Ansible will see it as a *new* rule and stack duplicates. Keep the module arguments (`chain: INPUT`, `source: "{{ ioc_ip }}"`, `jump: DROP`) exactly consistent between runs.

**A port-22 ban is not a host block.**
If you only ever changed something for Phase 2 (fail2ban), that rule is scoped to SSH connection attempts. Phase 4 explicitly requires a rule with *no port restriction* — it must drop the IOC's traffic to the host regardless of destination port, since the Storm is fuzzing port 80 with the SSH vector already closed.

**Testing your own playbook before ARIA does.**
Run `block-ioc.yml` against the IP from your own triage report before `make test` gets there. If it fails to apply cleanly (missing `-e ioc_ip=...`, a typo in the module args), you'll get a much clearer error message running it yourself than parsing it out of ARIA's output.

```bash
ansible-playbook block-ioc.yml -e ioc_ip=172.30.0.20
```

Then confirm the rule landed:

```bash
make ssh-app
sudo iptables -L INPUT -n | grep 172.30.0.20
```

---

## Phase 5 — The Hardcode Trap

**This phase does not ask you to write anything new — it re-runs Phase 4's playbook, unchanged, against a different address.**
If your `block-ioc.yml` only ever references `{{ ioc_ip }}` (never a literal address baked into a `source:` value, a `when:` condition, or a comment you copy-pasted into logic), it will seal the rotated address automatically. This is the entire point of the phase: automation that only works for one memorised indicator is not automation, it's a one-time patch.

**Common way this trap gets sprung.**
It's easy to test Phase 4 successfully with `-e ioc_ip=172.30.0.20`, see it pass, and then — while debugging something else — leave a stray `source: "172.30.0.20"` in the playbook alongside the templated `{{ ioc_ip }}` line, or add a second task "just for the known bad IP" as a belt-and-braces measure. Search your `block-ioc.yml` for any literal `172.30.0.2` before considering this phase done.

**If Phase 5 fails, don't guess the new address — go get it.**
Regenerate your triage report against the live (now-rotated) fleet:

```bash
ansible-playbook collect-triage.yml
cat reports/noise-report.md
```

This will show you the Storm's current source IP directly from fresh evidence, which is useful for sanity-checking your fix even though ARIA supplies the address itself when it re-runs your playbook.

---

## General Troubleshooting

**"ARIA says INCONCLUSIVE" or "the range appears offline."**
This is not a pass or a fail — it means the Storm's own container has stalled or lost signal, and ARIA cannot honestly grade you against it. The fix is always the same:

```bash
make reset
```

Wait for the fleet and range to come back up, then run `make test` again.

**"I want a clean, freshly-scored run from Phase 1."**
`make test` exercises all five phases every time it runs — including applying your own `block-ioc.yml` against the live fleet and, once you reach Phase 5, triggering the Storm's rotation. That means repeated `make test` runs accumulate firewall state and can leave the Storm mid-rotation. If your results look inconsistent between runs, or you just want to start scoring fresh:

```bash
make reset
```

This re-arms the Storm on its **primary** address (172.30.0.20) and clears prior firewall state, while preserving everything you've written in `workspace/`.

**"make: *** No targets specified" or "make: *** No rule to make target".**
You are in the wrong directory. `make` commands must be run from the **project root**, where the `Makefile` lives — not from `workspace/`. Run `cd ..` to go back.

**If `make test` fails:**
Read ARIA's error message carefully — it names the specific signal it expected (`password_auth_offered`, `tcp_open`, `web_open`) versus what it observed, and which phase that maps to. Fix that one thing, then run `make test` again rather than reworking everything at once.

**Never edit anything under `.docker/`.**
That directory is the range itself — the Storm's container, the target-node images, the compose file wiring it all together. You do not need to touch it, and doing so will not help; your entire mission is written in `workspace/`.

**Quick diagnostic sequence when something is not working:**
1. `docker ps` — are all three fleet containers (and the noise container) running?
2. `make ssh-app` / `make ssh-web` / `make ssh-db` — can you still reach each node with your key?
3. On the node, check the specific service for the phase you're on: `sshd -T`, `fail2ban-client status sshd`, `sudo iptables -L -n`, `systemctl status rsyslog`.
4. `cat reports/noise-report.md` — does it name a real, current IP?
5. If nothing above explains it, `make reset` and re-test from a known-clean state.
