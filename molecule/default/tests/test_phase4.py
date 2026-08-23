"""
Phase 4 — Block the IOC
=======================
A ban stops the SSH hammering, but the storm is still fuzzing your web service
(port 80) from the same address. Author a PARAMETERISED block-ioc.yml that
firewall-drops a given IOC IP's traffic to the whole host, fleet-wide. ARIA runs
your playbook against the live source IP and confirms the storm goes dark on
port 80 everywhere — the `web_open` signal must fall to False on every node.
"""
import os

import pytest

from conftest import TARGETS, run_ansible, _workspace_dir


def _block_playbook():
    return os.path.join(_workspace_dir(), "block-ioc.yml")


class TestPhase4BlockIOC:

    def test_block_playbook_present(self):
        p = _block_playbook()
        assert os.path.isfile(p) and os.path.getsize(p) > 0, (
            "ARIA: No block-ioc.yml in your workspace. Author a parameterised "
            "playbook that firewall-drops a given IOC IP fleet-wide, accepting the "
            "address via -e ioc_ip=<ip>."
        )

    def test_ioc_blocked_fleetwide(self, noise):
        if not os.path.isfile(_block_playbook()):
            pytest.skip("block-ioc.yml not present yet")

        ioc = noise.active_source_ip()
        if ioc is None:
            pytest.fail(
                "ARIA: The range is not reporting a source IP — INCONCLUSIVE. "
                "Run 'make reset', then 'make test' again."
            )

        r = run_ansible(
            ["ansible-playbook", "block-ioc.yml", "-e", f"ioc_ip={ioc}"]
        )
        assert r.returncode == 0, (
            "ARIA: Your block-ioc.yml failed to run cleanly.\n"
            f"{(r.stderr or r.stdout)[-500:]}"
        )

        ok = noise.await_condition(
            lambda s: all(
                s["targets"].get(t, {}).get("web_open") is False
                for t in TARGETS
            ),
            timeout=150,
        )
        assert ok, (
            "ARIA: The IOC is still reaching the fleet's web service after your block "
            "ran. A port-22 ban is not enough — drop the IOC's traffic to the whole "
            "host, on every node."
        )
