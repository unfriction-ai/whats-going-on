#!/usr/bin/env bash
# Fail when any whats-going-on skill copy drifts from the canonical tree, or when a
# host manifest would mount evals/. Identical-hash copies (Codex plugin tree) and
# symlinks to the canonical path are allowed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$ROOT/skills/whats-going-on/SKILL.md"

if [[ ! -f "$CANONICAL" ]]; then
  echo "missing canonical skill: $CANONICAL" >&2
  exit 1
fi

canon_hash="$(shasum -a 256 "$CANONICAL" | awk '{print $1}')"
canon_dir="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$(dirname "$CANONICAL")")"
found=0

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  case "$f" in
    */whats-going-on/SKILL.md) ;;
    *) continue ;;
  esac
  found=1
  real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$f")"
  h="$(shasum -a 256 "$real" | awk '{print $1}')"
  if [[ "$h" != "$canon_hash" ]]; then
    echo "drifted SKILL.md at $f (hash $h != canonical $canon_hash)" >&2
    exit 1
  fi
  copy_dir="$(dirname "$real")"
  if [[ "$copy_dir" != "$canon_dir" ]] && ! diff -rq -x '.*' "$canon_dir" "$copy_dir" >&2; then
    echo "drifted skill tree at $(dirname "$f")" >&2
    exit 1
  fi
done < <(
  find "$ROOT" \
    \( -path "$ROOT/.git" -o -path "$ROOT/.venv" -o -path "*/.venv" -o -path "*/__pycache__" \) -prune -o \
    -type f -name SKILL.md -print \
    | sort
)

if [[ "$found" -eq 0 ]]; then
  echo "no whats-going-on/SKILL.md found" >&2
  exit 1
fi

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
