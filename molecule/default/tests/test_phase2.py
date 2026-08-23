"""
Phase 2 — Rate-Limit & Ban
==========================
Key-only auth stops the storm getting in, but it keeps hammering. Stand up a
rate-limit / ban (fail2ban's sshd jail, tuned to trip fast and ban long) so the
attacker's repeated probes get dropped at the TCP level. The storm's `tcp_open`
signal must fall to False on every node — a strictly stronger outcome than
phase 1 (the connection no longer completes at all).
"""
from conftest import TARGETS


class TestPhase2RateLimit:

    def test_storm_ssh_probes_blocked(self, noise):
        ok = noise.await_condition(
            lambda s: all(
                s["targets"].get(t, {}).get("tcp_open") is False
                for t in TARGETS
            ),
            timeout=180,
        )
        assert ok, (
            "ARIA: The storm can still open SSH connections to the fleet. A ban "
            "(e.g. fail2ban's sshd jail, tuned with a low findtime/maxretry so it "
            "trips inside the window and a bantime long enough to hold) should be "
            "dropping the attacker. Enable and tune it fleet-wide, then re-test."
        )
