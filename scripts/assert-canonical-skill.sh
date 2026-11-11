#!/usr/bin/env bash
# Fail when the repo has more than one whats-going-on SKILL.md body, or when a
# host manifest would mount evals/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$ROOT/skills/whats-going-on/SKILL.md"

if [[ ! -f "$CANONICAL" ]]; then
  echo "missing canonical skill: $CANONICAL" >&2
  exit 1
fi

canon_real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$CANONICAL")"
canon_hash="$(shasum -a 256 "$CANONICAL" | awk '{print $1}')"

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  case "$f" in
    */whats-going-on/SKILL.md) ;;
    *) continue ;;
  esac
  real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$f")"
  h="$(shasum -a 256 "$real" | awk '{print $1}')"
  if [[ "$h" != "$canon_hash" ]]; then
    echo "drifted SKILL.md at $f (hash $h != canonical $canon_hash)" >&2
    exit 1
  fi
  if [[ "$real" != "$canon_real" ]] && [[ ! -L "$f" ]]; then
    echo "extra real SKILL.md (not a symlink to canonical): $f -> $real" >&2
    exit 1
  fi
done < <(
  find "$ROOT" \
    \( -path "$ROOT/.git" -o -path "$ROOT/.venv" -o -path "*/.venv" -o -path "*/__pycache__" \) -prune -o \
    -type f -name SKILL.md -print \
    | sort
)

while IFS= read -r -d '' manifest; do
  if grep -Eiq 'evals/' "$manifest"; then
    echo "host manifest must not reference evals/: $manifest" >&2
    exit 1
  fi
done < <(
  find "$ROOT" \
    \( -path "$ROOT/.git" -o -path "*/.venv" \) -prune -o \
    \( -name plugin.json -o -name marketplace.json \) -type f -print0 \
    2>/dev/null || true
)

echo "canonical skill ok"
exit 0
