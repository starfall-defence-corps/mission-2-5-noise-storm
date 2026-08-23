#!/usr/bin/env bash
# ============================================================================
# sdc-noise — supervisor loop for the "noise storm".
#
# Every cycle it probes each fleet node and atomically publishes what it saw
# to /run/noise/status.json (bind-mounted to the host at .lab/noise/). The
# ARIA test harness reads that file directly and asserts on it.
#
# Signals published per target:
#   tcp_open              — TCP/22 reachable from the active source
#   password_auth_offered — sshd advertised the 'password' method (key-only
#                           hardening removes it)
#   web_open              — TCP/80 reachable (only a blanket IOC firewall drop
#                           closes this; a port-22 ban does not)
#
# cycle_seq increments every sweep and is the LIVENESS proof: a crashed storm
# can never advance it, so the harness reads a dead range as inconclusive,
# never as a pass. Safety envelope: short timeouts, a single small status file
# overwritten in place, and a 5s sleep between sweeps -> near-idle.
# ============================================================================
set -u

SRC_A="172.30.0.20"          # primary source IP (IOC_A)
SRC_B="172.30.0.21"          # secondary source IP (IOC_B, phase-5 rotation)
TARGETS=("172.30.0.11" "172.30.0.12" "172.30.0.13")

STATUS_DIR="/run/noise"
STATUS="$STATUS_DIR/status.json"
ROTATE_FLAG="$STATUS_DIR/rotated"
WORDLIST="/opt/noise/wordlist.txt"

mkdir -p "$STATUS_DIR"

# Attach the secondary source IP so rotation can bind to it later.
ip addr add "${SRC_B}/24" dev eth0 2>/dev/null || true

# Startup grace: wait until the fleet is up so the pre-defence baseline reads
# "attack landing" (guarantees a zero-work run fails phase 1). Probe port 80
# (nginx) for readiness, NOT 22 — if the storm ever restarts against an already
# hardened/banned fleet, SSH may be firewalled off and we must still start.
# Capped so a probe that never answers can never wedge the loop.
for _ in $(seq 1 45); do
    nc -z -w2 "${TARGETS[0]}" 80 2>/dev/null && break
    sleep 2
done

# Probe one target from a given source IP. Emits a JSON object.
probe_target() {
    local src="$1" tgt="$2"
    local tcp_open=false pw_offered=false web_open=false

    if nc -z -w2 -s "$src" "$tgt" 22 2>/dev/null; then
        tcp_open=true
        # Safe auth-method enumeration — never submits a password.
        # `timeout` bounds the WHOLE ssh: ConnectTimeout only covers the TCP
        # connect, so a mid-handshake packet drop (e.g. a fresh firewall/ban)
        # would otherwise hang the probe — and the loop — indefinitely.
        local out
        out="$(timeout 6 ssh -b "$src" \
                -o PreferredAuthentications=none -o BatchMode=yes \
                -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
                -o ConnectTimeout=3 \
                baduser@"$tgt" true 2>&1 || true)"
        printf '%s' "$out" | grep -q 'password' && pw_offered=true
    fi

    if nc -z -w2 -s "$src" "$tgt" 80 2>/dev/null; then
        web_open=true
        # Light web fuzz — generates access noise; result is not graded.
        local path
        path="$(shuf -n1 "$WORDLIST" 2>/dev/null || echo /)"
        curl -s -m 3 --interface "$src" "http://${tgt}${path}" -o /dev/null 2>/dev/null || true
    fi

    printf '{"tcp_open":%s,"password_auth_offered":%s,"web_open":%s}' \
        "$tcp_open" "$pw_offered" "$web_open"
}

CYCLE=0
while true; do
    CYCLE=$((CYCLE + 1))

    if [ -f "$ROTATE_FLAG" ]; then SRC="$SRC_B"; else SRC="$SRC_A"; fi
    TS="$(date +%s)"

    tj=""
    for t in "${TARGETS[@]}"; do
        r="$(probe_target "$SRC" "$t")"
        [ -n "$tj" ] && tj="${tj},"
        tj="${tj}\"${t}\":${r}"
    done

    tmp="$(mktemp "${STATUS_DIR}/.status.XXXXXX")"
    printf '{"cycle_seq":%d,"updated_ts":%d,"active_source_ip":"%s","targets":{%s}}\n' \
        "$CYCLE" "$TS" "$SRC" "$tj" > "$tmp"
    mv -f "$tmp" "$STATUS"      # atomic publish

    sleep 5
done
