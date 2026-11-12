#!/usr/bin/env bash
# Omit -e so a failing gate does not skip the rest.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
failed=()
ran=0

gate() {
  local name="$1"
  shift
  echo "== ${name} ($*) =="
  (
    cd "$ROOT" && "$@"
  )
  local rc=$?
  echo "exit ${rc}"
  ran=$((ran + 1))
  if [[ "$rc" -ne 0 ]]; then
    failed+=("${name} (exit ${rc})")
  fi
}

gate eval-check bash -c 'cd evals/whats-going-on && python -m whats_going_on_eval check'
gate canonical-skill bash scripts/assert-canonical-skill.sh

if [[ ${#failed[@]} -eq 0 ]]; then
  summary="PR gates: all ${ran} passed"
else
  summary="PR gates: ${#failed[@]} of ${ran} failed: ${failed[*]}"
fi

echo "$summary"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  printf '%s\n' "$summary" >> "$GITHUB_STEP_SUMMARY"
fi

if [[ ${#failed[@]} -eq 0 ]]; then
  exit 0
fi
exit 1
