#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DIR="$ROOT_DIR/molecule/default/tests"

# -- Colors ----------------------------------------------------------------
GREEN='\033[32m'
RED='\033[31m'
CYAN='\033[36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

echo ""
echo -e "  ${CYAN}${BOLD}=============================================="
echo -e "  ARIA — Automated Review & Intelligence Analyst"
echo -e "  Mission 2.5: Noise Storm"
echo -e "  ==============================================${RESET}"

cd "$ROOT_DIR"

# Activate project venv if it exists
if [ -f "$ROOT_DIR/venv/bin/activate" ]; then
    source "$ROOT_DIR/venv/bin/activate"
fi

# Run the phased verification. test_phase1..5.py sort in order; conftest.py
# renders the ARIA report. ARIA_COLOR=1 forces color through the grep filter.
# conftest writes to stderr; discard pytest's stdout and its stderr noise,
# keeping only our indented ARIA lines.
ARIA_COLOR=1 python3 -m pytest "$TEST_DIR" -p no:cacheprovider --tb=no --no-header -q 2>&1 1>/dev/null \
    | grep -vE '^(assert |FAILED| *\+  where|  *\+  |[0-9]+ (passed|failed))' || true
EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}=============================================="
    echo -e "  ARIA: All objectives verified."
    echo -e "  Mission 2.5 status: COMPLETE"
    echo -e ""
    echo -e "  Cadet, you held the line through the storm."
    echo -e "  The fleet is hardened, watched, and the intruder"
    echo -e "  is locked out — even after they changed address."
    echo -e "  The Starfall Defence Corps salutes you."
    echo -e "  ==============================================${RESET}"
else
    echo -e "  ${RED}${BOLD}=============================================="
    echo -e "  ARIA: Deficiencies detected."
    echo -e "  The storm is still landing. Review the findings"
    echo -e "  above, reinforce your defences, and run"
    echo -e "  'make test' again when ready."
    echo -e "  ==============================================${RESET}"
fi

echo ""
exit $EXIT_CODE
