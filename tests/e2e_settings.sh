#!/usr/bin/env bash
# E2E smoke test for settings API
# Requires: backend running on localhost:8000
set -euo pipefail

BASE="http://localhost:8000"
PASS=0
FAIL=0

check() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == *"$expected"* ]]; then
    echo "  PASS: $desc"
    ((PASS++))
  else
    echo "  FAIL: $desc (expected '$expected', got '$actual')"
    ((FAIL++))
  fi
}

echo "=== Settings API E2E ==="

# 1. Status endpoint
echo ""
echo "--- GET /settings/status ---"
STATUS=$(curl -s "$BASE/settings/status")
check "status returns JSON" "configured" "$STATUS"

# 2. GET settings when not configured
echo ""
echo "--- GET /settings (no config) ---"
GET_RESP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/settings")
# May be 200 or 404 depending on whether config exists
echo "  INFO: GET /settings returned HTTP $GET_RESP"

# 3. POST settings with bad key (should fail validation)
echo ""
echo "--- POST /settings (bad key, expect 400) ---"
BAD_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/settings" \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","model":"gpt-4o","api_key":"sk-bad-key"}')
BAD_CODE=$(echo "$BAD_RESP" | tail -1)
check "bad key returns 400" "400" "$BAD_CODE"

# 4. POST settings with missing azure fields
echo ""
echo "--- POST /settings (azure missing fields, expect 422) ---"
AZ_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/settings" \
  -H "Content-Type: application/json" \
  -d '{"provider":"azure_openai","model":"gpt-4o","api_key":"abc"}')
check "azure missing fields returns 422" "422" "$AZ_RESP"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
