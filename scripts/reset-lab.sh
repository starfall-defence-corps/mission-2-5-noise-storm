#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$ROOT_DIR/.docker"

echo ""
echo "=============================================="
echo "  STARFALL DEFENCE CORPS ACADEMY"
echo "  Resetting Fleet + Range (re-arming the storm)..."
echo "=============================================="
echo ""

echo "  Destroying existing fleet + range..."
docker compose -f "$DOCKER_DIR/docker-compose.yml" down -v 2>&1 | while read -r line; do
    echo "    $line"
done

# Clear the range's published signal + rotation latch so the next run starts
# from a fresh, un-rotated storm.
rm -f "$ROOT_DIR/.lab/noise/status.json" "$ROOT_DIR/.lab/noise/rotated" 2>/dev/null || true

echo ""
echo "  Rebuilding fleet + range..."
# Reuse setup script for the rebuild
bash "$SCRIPT_DIR/setup-lab.sh"
