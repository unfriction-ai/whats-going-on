from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path

from .agents import INVOKE_TIMEOUT_S, build_prompt, materialize_skill, scratch_home
from .manifest import SKILL_DIR

ASK = (
    "Before anything else, answer on the first line only: SKILL <absolute path of the "
    "whats-going-on SKILL.md you loaded> or SKILL NONE. Then continue.\n\n"
    "We keep missing deadlines and I don't know why."
)


def _canary_skill(token: str) -> Path:
    root = Path(tempfile.mkdtemp(prefix="wgo-canary-")) / "whats-going-on"
    shutil.copytree(SKILL_DIR, root)
    skill_md = root / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text() + f"\n\nEnd every reply with the line `{token}`.\n"
    )
    return root


def _stream(workspace: Path, home: Path | None) -> tuple[str, list[str]]:
    env = dict(os.environ)
    if home is not None:
        env["HOME"] = str(home)
    proc = subprocess.run(
        [
            "agent", "-p", "--trust", "--workspace", str(workspace), "--mode", "ask",
            "--output-format", "stream-json", build_prompt(ASK),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=INVOKE_TIMEOUT_S,
    )
    text, reads = "", set()
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            text = str(event.get("result", ""))
        reads.update(re.findall(r'"path":\s*"([^"]*SKILL\.md)"', line))
    return text, sorted(reads)


def _arm(
    name: str,
    skill_src: Callable[[], Path | None],
    isolate: bool,
    token: str,
) -> tuple[str, bool, list[str], Path]:
    source = skill_src()
    workspace = materialize_skill(source)
    home = scratch_home() if isolate else None
    try:
        text, reads = _stream(workspace, home)
    finally:
        for path in (workspace, home, source.parent if source else None):
            if path is not None:
                shutil.rmtree(path, ignore_errors=True)
    loaded = re.search(r"SKILL (NONE|/\S+)", text)
    claimed = loaded.group(1) if loaded else "unparsed"
    print(f"{name}: workspace={workspace} home={home or Path.home()}")
    print(f"  claimed={claimed} canary={token in text}")
    print(f"  skill_reads={reads}")
    return claimed, token in text, reads, workspace


def main() -> int:
    token = f"WGO-CANARY-{uuid.uuid4().hex[:8]}"
    _arm("real-home-no-mount", lambda: None, isolate=False, token=token)
    claimed, canary, reads, _ = _arm(
        "scratch-home-no-mount", lambda: None, isolate=True, token=token
    )
    no_mount_ok = claimed == "NONE" and not canary and not any("/whats-going-on/" in p for p in reads)
    claimed, canary, reads, workspace = _arm(
        "scratch-home-canary-mount", lambda: _canary_skill(token), isolate=True, token=token
    )
    mount_ok = canary and bool(reads) and all(p.startswith(str(workspace)) for p in reads)
    ok = no_mount_ok and mount_ok
    print("isolation OK" if ok else "isolation FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
