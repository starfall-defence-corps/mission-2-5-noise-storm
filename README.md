# Starfall Defence Corps Academy

> 🧭 [← 2.4 Defence in Depth](https://github.com/starfall-defence-corps/mission-2-4-defence-in-depth) · **You are here: 2.5 Noise Storm** · [2.6 Counterattack →](https://github.com/starfall-defence-corps/mission-2-6-counterattack) · [🏠 Academy Hub](https://github.com/starfall-defence-corps/sdc-academy) · [📚 Field Manuals](https://github.com/starfall-defence-corps/sdc-academy/tree/main/field-manuals)

> ☁️ **No Docker on your machine?** Create your own copy first (Use this template), then on **your** repo: **Code → Codespaces → Create codespace** — everything is preinstalled. First boot takes ~5 min (one-time); after that it starts fast.

## Mission 2.5: Noise Storm

> *"You can't stop the storm. You can decide what it reaches."*

An unknown adversary has opened up on the fleet. A relentless **noise storm** is hammering every node's SSH and web ports from a fixed address — probing for a way in, around the clock. This is your first live incident: you will weather it with Ansible. Harden the fleet to key-only auth, stand up a ban to drop the hammering, get eyes on the attack, and firewall the intruder off the fleet — then hold the line when it changes address.

You never touch the attacker. Everything you do is defensive automation, applied to **your** fleet.

## Prerequisites

- All of Module 1 (roles, variables, templates, firewalling) and Module 2 up to **2.4 Defence in Depth**.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose v2)
- [GNU Make](https://www.gnu.org/software/make/)
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/) (`ansible-core`)
- Python 3.10+ (for the test environment) — on Debian/Ubuntu: `sudo apt install python3-venv`
- Git

> **Windows users**: run everything inside [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install), with Docker Desktop on the WSL2 backend.

## Quick Start

```bash
# 1. Use this template on GitHub (green button, top right) to create YOUR OWN
#    copy. Set it Public, then clone it:
git clone https://github.com/YOUR-USERNAME/mission-2-5-noise-storm.git
cd mission-2-5-noise-storm

# 2. Check your machine is mission-ready
make doctor

# 3. Bring the fleet online — it comes up already under attack
make setup

# 4. Activate the Python environment
source venv/bin/activate
```

5. **Read your orders**: [Mission Briefing](docs/BRIEFING.md)
6. **Work the incident**: [Exercises](docs/EXERCISES.md)
7. **Stuck?** [Hints & Troubleshooting](docs/HINTS.md)
8. **Track progress**: [Checklist](CHECKLIST.md)

## Lab Architecture

```
 Your Machine
+---------------------------------------------------------------+
|  workspace/           (the only place you write Ansible)       |
|    ansible.cfg                                                 |
|    inventory/hosts.yml         (the fleet, pre-registered)     |
|    site.yml + roles/           (harden / defend / observe)     |
|    collect-triage.yml          (see the storm)                 |
|    block-ioc.yml               (block the intruder)            |
|    reports/noise-report.md     (you generate)                  |
|                                                               |
|  Docker Network: 172.30.0.0/24                                 |
|  +------------+  +------------+  +------------+   the fleet     |
|  | sdc-app    |  | sdc-web    |  | sdc-db     |   (you defend)  |
|  | .11  :2221 |  | .12  :2222 |  | .13  :2223 |                 |
|  +------------+  +------------+  +------------+                 |
|  all three nodes also serve HTTP on :80; sdc-web is primary web |
|                                                               |
|  +-------------------------------+   range infrastructure      |
|  | sdc-noise  .20 (rotates .21)  |   (opaque — never touch it) |
|  | the noise storm               |                             |
|  +-------------------------------+                             |
+---------------------------------------------------------------+
```

The three fleet nodes are yours to harden. `sdc-noise` is the storm — opaque range
infrastructure that probes the fleet and publishes what it can still reach. You
defend the fleet; ARIA reads the storm's own telemetry to score you.

## Available Commands

```
make help       Show available commands
make doctor     Check your machine is mission-ready
make setup      Start the fleet + range (comes up under attack)
make test       Ask ARIA to verify your work (runs all 5 phases)
make reset      Destroy, rebuild, and re-arm the storm (fresh scored run)
make destroy    Tear down everything (containers, keys, venv, range state)
make ssh-app    SSH into sdc-app  (172.30.0.11, also runs nginx :80)
make ssh-web    SSH into sdc-web  (172.30.0.12, primary web node, nginx :80)
make ssh-db     SSH into sdc-db   (172.30.0.13, also runs nginx :80)
make submit     Submit your work for ARIA review (branch, commit, push, PR)
```

## Mission Files

| File | Purpose |
|------|---------|
| [BRIEFING.md](docs/BRIEFING.md) | Mission briefing — **read this first** |
| [EXERCISES.md](docs/EXERCISES.md) | Phase-by-phase operational instructions (5 phases) |
| [HINTS.md](docs/HINTS.md) | Troubleshooting and hints |
| [CHECKLIST.md](CHECKLIST.md) | Progress tracker |

## How ARIA scores this mission

`make test` runs **all five phases** and reports which objectives the storm can
still defeat. Two things to know:

- **`make test` exercises the live lab.** It runs your `block-ioc.yml` and, in the
  final phase, moves the storm onto a new source address to see whether your block
  still holds. For a clean scored run from the top, run **`make reset`** first — it
  re-arms the storm on its primary address and clears firewall state.
- **"INCONCLUSIVE — the range appears offline"** means the storm container stalled,
  not that you failed. Run **`make reset`** and test again. ARIA never scores a dead
  range as a pass or a fail.

## ARIA Review (Pull Request Workflow)

**ARIA** (Automated Review & Intelligence Analyst) reviews your work two ways:

**Locally** — `make test` for instant pass/fail verification. No API key needed.

**On Pull Request** — push a branch, open a PR to `main`, and ARIA posts a
qualitative review as a PR comment. To enable it, add an `ANTHROPIC_API_KEY` repo
secret (**Settings → Secrets and variables → Actions**). Without a key, PR review is
skipped and `make test` still works locally.

## Troubleshooting

**Containers won't start**: Ensure Docker Desktop is running; check for port conflicts on 2221-2223. Only one SDC lab at a time is supported — run `make destroy` in any other mission first.

**`make test` says the range is offline / INCONCLUSIVE**: `make reset`.

**`make test` fails with "No module named pytest"**: run `make setup` first — it builds the Python environment.

**Need a clean slate**: `make reset` (re-arms the storm) or `make destroy` (full teardown).

**Docker network conflict** ("Pool overlaps..."): another Docker network is using 172.30.0.0/24 — stop it, or edit `.docker/docker-compose.yml`.
