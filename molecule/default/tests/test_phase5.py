"""
Phase 5 — Hold the Line
=======================
The attacker rotates to a new source IP. ARIA moves the storm onto its secondary
address, then re-runs YOUR block-ioc.yml against the rotated IOC. If your block
is parameterised on ioc_ip it seals the new address and the fleet stays dark; if
you hardcoded the old IP, the storm gets straight back in. This is the capstone:
your automation must work for ANY indicator, not one you memorised.
"""
import os

import pytest

from conftest import TARGETS, IOC_B, run_ansible, _workspace_dir


def _block_playbook():
    return os.path.join(_workspace_dir(), "block-ioc.yml")


class TestPhase5HoldTheLine:

    def test_rotated_ioc_blocked(self, noise):
        if not os.path.isfile(_block_playbook()):
            pytest.skip("block-ioc.yml not present yet")

        # Move the storm onto its secondary source IP (idempotent latch).
        noise.trigger_rotation()
        if not noise.await_source(IOC_B, timeout=90):
            pytest.fail(
                "ARIA: The storm did not rotate to its secondary source — "
                "INCONCLUSIVE. Run 'make reset', then 'make test' again."
            )

        # Re-run the cadet's OWN playbook against the new indicator.
        r = run_ansible(
            ["ansible-playbook", "block-ioc.yml", "-e", f"ioc_ip={IOC_B}"]
        )
        assert r.returncode == 0, (
            "ARIA: Your block-ioc.yml failed to run against the rotated IOC.\n"
            f"{(r.stderr or r.stdout)[-500:]}"
        )

        ok = noise.await_condition(
            lambda s: s.get("active_source_ip") == IOC_B and all(
                s["targets"].get(t, {}).get("web_open") is False
                for t in TARGETS
            ),
            timeout=150,
        )
        assert ok, (
            "ARIA: The attacker changed address and is hitting the fleet again. Your "
            "block must work for ANY IOC — parameterise it on ioc_ip so re-running it "
            "against the new source seals the fleet. (Tip: regenerate your triage "
            "report to discover the storm's new address.)"
        )
