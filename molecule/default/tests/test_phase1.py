"""
Phase 1 — Key-Only Auth
=======================
The storm probes each node's SSH and records whether the server still offers
password authentication. Harden the fleet to key-only auth and the storm's
`password_auth_offered` signal must fall to False on every node — sustained.
"""
from conftest import TARGETS


class TestPhase1KeyOnlyAuth:

    def test_password_auth_refused_fleetwide(self, noise):
        ok = noise.await_condition(
            lambda s: all(
                s["targets"].get(t, {}).get("password_auth_offered") is False
                for t in TARGETS
            )
        )
        assert ok, (
            "ARIA: The fleet's SSH is still offering password authentication to the "
            "storm. Harden every node to key-only auth (PasswordAuthentication no) "
            "and apply your role fleet-wide, then run 'make test' again."
        )
