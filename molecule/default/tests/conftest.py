"""
ARIA Custom Test Reporter + Noise-Storm verification harness
============================================================
Mission 2.5: Noise Storm

The reporter provides color-coded, phase-grouped output (writes to stderr so
check-work.sh can discard pytest's default stdout).

The Noise helper reads the attacker-authored status file (published by the
sdc-noise range container to .lab/noise/status.json) and provides the single
convergence primitive the phase tests assert through: await_condition().

Design principle: never assert on instantaneous target-side state. Assert on a
monotonic, latching signal authored by the storm, sustained across k distinct
increasing cycle_seq values. A crashed storm can never advance cycle_seq, so a
dead range reads as INCONCLUSIVE, never as a pass.
"""
import json
import os
import subprocess
import time

import pytest

# -- Range constants ---------------------------------------------------------

IOC_A = "172.30.0.20"          # primary attacker source IP
IOC_B = "172.30.0.21"          # rotated attacker source IP (phase 5)
TARGETS = ["172.30.0.11", "172.30.0.12", "172.30.0.13"]  # app / web / db
NOISE_CONTAINER = "sdc-noise"


# -- Paths -------------------------------------------------------------------

def _root_dir():
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(tests_dir, "..", "..", ".."))


def _workspace_dir():
    return os.path.join(_root_dir(), "workspace")


def _status_path():
    return os.path.join(_root_dir(), ".lab", "noise", "status.json")


def _capped(timeout):
    """Optional ceiling on poll timeouts (seconds). Unset in normal use; the
    range-build harness sets ARIA_MAX_WAIT to iterate quickly."""
    override = os.environ.get("ARIA_MAX_WAIT")
    if override:
        try:
            return min(timeout, int(override))
        except ValueError:
            pass
    return timeout


# -- Noise-storm helper ------------------------------------------------------

class Noise:
    """Reads the storm's published status and waits for convergence."""

    def __init__(self):
        self.status_path = _status_path()

    def read(self):
        """Fresh read of the host-side status file. None if unreadable."""
        try:
            with open(self.status_path) as f:
                return json.load(f)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            return None

    def active_source_ip(self):
        s = self.read()
        return s.get("active_source_ip") if s else None

    def trigger_rotation(self):
        """Latch the storm onto its secondary source IP (idempotent).

        Written inside the container so it works regardless of bind-mount
        propagation direction; the latch persists until 'make reset'.
        """
        subprocess.run(
            ["docker", "exec", NOISE_CONTAINER, "touch", "/run/noise/rotated"],
            capture_output=True, timeout=15,
        )

    def await_condition(self, pred, k=3, timeout=120, interval=3):
        """Return True once `pred(status)` holds across k distinct increasing
        cycle_seq values. Returns False if the storm is alive but the condition
        never sustains (a genuine deficiency). Raises an INCONCLUSIVE failure if
        the storm never advances (dead range)."""
        timeout = _capped(timeout)
        seen = []
        last = None
        advanced = False
        deadline = time.time() + timeout
        while time.time() < deadline:
            s = self.read()
            if s is not None and "cycle_seq" in s:
                seq = s["cycle_seq"]
                if last is None or seq > last:
                    if last is not None:
                        advanced = True
                    last = seq
                    if pred(s):
                        seen.append(seq)
                        if len(seen) >= k:
                            return True
                    else:
                        seen.clear()
            time.sleep(interval)
        if not advanced:
            pytest.fail(
                "ARIA: The noise storm is not advancing — the range appears "
                "offline. This result is INCONCLUSIVE, not a pass or a fail. "
                "Run 'make reset' to re-arm the range, then 'make test' again."
            )
        return False

    def await_source(self, ip, timeout=90, interval=3):
        """Wait until the storm's active source IP becomes `ip`."""
        timeout = _capped(timeout)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.active_source_ip() == ip:
                return True
            time.sleep(interval)
        return False


@pytest.fixture(scope="session")
def noise():
    return Noise()


def run_ansible(args, timeout=120):
    """Run an ansible/ansible-playbook command in the student's workspace,
    using the workspace ansible.cfg + inventory + key (never the host's)."""
    env = dict(os.environ)
    env["ANSIBLE_CONFIG"] = os.path.join(_workspace_dir(), "ansible.cfg")
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout,
        cwd=_workspace_dir(), env=env,
    )


# ===========================================================================
# ARIA reporter (below) — presentation only.
# ===========================================================================

import sys  # noqa: E402

_COLOR = (
    os.environ.get("ARIA_COLOR") == "1"
    or (hasattr(sys.stderr, "isatty") and sys.stderr.isatty())
)


def _c(code):
    return code if _COLOR else ""


GREEN = _c("\033[32m")
RED = _c("\033[31m")
YELLOW = _c("\033[33m")
CYAN = _c("\033[36m")
DIM = _c("\033[2m")
BOLD = _c("\033[1m")
RESET = _c("\033[0m")

PHASES = {
    "TestPhase1KeyOnlyAuth":   ("1", "Key-Only Auth"),
    "TestPhase2RateLimit":     ("2", "Rate-Limit & Ban"),
    "TestPhase3Observability": ("3", "See the Storm"),
    "TestPhase4BlockIOC":      ("4", "Block the IOC"),
    "TestPhase5HoldTheLine":   ("5", "Hold the Line"),
}

FRIENDLY = {
    "test_password_auth_refused_fleetwide": "SSH password auth refused fleet-wide",
    "test_storm_ssh_probes_blocked":        "Storm's SSH probes are being blocked",
    "test_triage_report_exists":            "Triage report generated",
    "test_triage_report_names_current_ioc": "Report names the live attacker IP",
    "test_log_forwarding_configured":       "Fleet logs forwarded off-box",
    "test_block_playbook_present":          "Block-IOC playbook present",
    "test_ioc_blocked_fleetwide":           "IOC blocked across the whole fleet",
    "test_rotated_ioc_blocked":             "Rotated IOC blocked — parameterised hold",
}


class _ARIAReporter:
    def __init__(self):
        self._current_class = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self._phase_results = {}
        self._current_phase_passed = True

    @staticmethod
    def _out(text):
        sys.stderr.write(text)
        sys.stderr.flush()

    def record(self, nodeid, outcome, longrepr):
        parts = nodeid.split("::")
        cls = parts[1] if len(parts) > 1 else ""
        test = parts[-1]

        num, label = PHASES.get(cls, ("?", "Unknown"))
        name = FRIENDLY.get(test, test)

        if cls != self._current_class:
            if self._current_class is not None:
                self._phase_results[self._current_class] = self._current_phase_passed
            self._current_phase_passed = True
            self._current_class = cls
            self._out(f"\n  {CYAN}{BOLD}Phase {num}: {label}{RESET}\n")

        if outcome != "passed":
            self._current_phase_passed = False

        if outcome == "passed":
            self.passed += 1
            self._out(f"    {GREEN}✓{RESET} {name}\n")
        elif outcome == "skipped":
            self.skipped += 1
            self._out(f"    {YELLOW}○{RESET} {DIM}{name} — skipped{RESET}\n")
        else:
            self.failed += 1
            hint = _extract_hint(longrepr)
            if hint:
                self._out(f"    {YELLOW}✗{RESET} {name}\n")
                self._out(f"      {DIM}↳ {hint}{RESET}\n")
            else:
                self._out(f"    {RED}✗{RESET} {name}\n")

    def summary(self):
        if self._current_class is not None:
            self._phase_results[self._current_class] = self._current_phase_passed

        total = self.passed + self.failed + self.skipped
        self._out(f"\n  {'─' * 44}\n")

        phases_complete = sum(1 for v in self._phase_results.values() if v)
        total_phases = len(PHASES)
        self._out(f"  {BOLD}Progress:{RESET} {phases_complete} of {total_phases} phases complete\n")

        parts = []
        if self.passed:
            parts.append(f"{GREEN}{self.passed} verified{RESET}")
        if self.failed:
            parts.append(f"{RED}{self.failed} deficient{RESET}")
        if self.skipped:
            parts.append(f"{YELLOW}{self.skipped} skipped{RESET}")
        self._out(
            f"  {BOLD}Results:{RESET} {' · '.join(parts)}"
            f"  {DIM}({total} checks){RESET}\n"
        )


def _extract_hint(longrepr):
    if longrepr is None:
        return None
    crash = getattr(longrepr, "reprcrash", None)
    if crash:
        msg = getattr(crash, "message", "")
        if "ARIA:" in msg:
            return msg.split("ARIA:", 1)[-1].strip()
    text = str(longrepr)
    if "ARIA:" in text:
        raw = text.split("ARIA:")[-1].splitlines()[0].strip()
        return raw.rstrip("'\"")
    return None


_reporter = _ARIAReporter()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    if report.when == "call":
        _reporter.record(report.nodeid, report.outcome, report.longrepr)
        report.longrepr = None
    elif report.when == "setup" and report.skipped:
        _reporter.record(report.nodeid, "skipped", report.longrepr)
        report.longrepr = None


def pytest_report_teststatus(report, config):
    if report.when == "call":
        return report.outcome, "", ""
    if report.when == "setup" and report.skipped:
        return "skipped", "", ""


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    _reporter.summary()
    terminalreporter.stats.pop("failed", None)
    terminalreporter.stats.pop("error", None)
