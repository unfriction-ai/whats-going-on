#!/usr/bin/env bash
# Materialize a local host install from the canonical skill. Never copies evals/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$ROOT/skills/whats-going-on"
HOME_DIR="${HOME:-}"

usage() {
  cat <<'EOF'
Usage: scripts/install-local.sh --host cursor|claude|codex|all

Installs from the canonical skills/whats-going-on/ tree into host-local paths
under $HOME. Never copies evals/.

  cursor  -> $HOME/.cursor/plugins/local/whats-going-on  (.cursor-plugin + skills)
  claude  -> $HOME/.claude/skills/whats-going-on
  codex   -> $HOME/.agents/skills/whats-going-on
  all     -> all three
EOF
}

install_cursor() {
  local dest="$HOME_DIR/.cursor/plugins/local/whats-going-on"
  mkdir -p "$dest"
  rsync -a --delete \
    --include='.cursor-plugin/***' \
    --include='skills/***' \
    --exclude='*' \
    "$ROOT/" "$dest/"
  test -f "$dest/skills/whats-going-on/SKILL.md"
  test ! -e "$dest/evals"
  echo "installed cursor -> $dest"
}

install_claude() {
  local dest="$HOME_DIR/.claude/skills/whats-going-on"
  mkdir -p "$(dirname "$dest")"
  rsync -a --delete "$CANONICAL/" "$dest/"
  test -f "$dest/SKILL.md"
  test ! -e "$dest/evals"
  echo "installed claude -> $dest"
}

install_codex() {
  local dest="$HOME_DIR/.agents/skills/whats-going-on"
  mkdir -p "$(dirname "$dest")"
  rsync -a --delete "$CANONICAL/" "$dest/"
  test -f "$dest/SKILL.md"
  test ! -e "$dest/evals"
  echo "installed codex -> $dest"
}

host=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      host="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$host" ]]; then
  usage >&2
  exit 1
fi

if [[ -z "$HOME_DIR" ]]; then
  echo "HOME is unset" >&2
  exit 1
fi

if [[ ! -d "$CANONICAL" ]]; then
  echo "missing canonical skill: $CANONICAL" >&2
  exit 1
fi

case "$host" in
  cursor) install_cursor ;;
  claude) install_claude ;;
  codex) install_codex ;;
  all)
    install_cursor
    install_claude
    install_codex
    ;;
  *)
    echo "unknown --host: $host" >&2
    usage >&2
    exit 1
    ;;
esac
