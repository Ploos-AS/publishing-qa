from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_command_evidence(
    *,
    evidence_id: str,
    kind: str,
    command: str,
    cwd: Path,
    supports_on_success: str = "confirm",
    supports_on_failure: str = "dispute",
    supports_on_timeout: str = "context",
    timeout: int = 300,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        proc = None
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

    if timed_out:
        exit_code = None
        supports = supports_on_timeout
    else:
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
        supports = supports_on_success if exit_code == 0 else supports_on_failure

    transcript = json.dumps({
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
    }, sort_keys=True).encode("utf-8")

    return {
        "evidence_id": evidence_id,
        "type": kind,
        "ref": command,
        "supports": supports,
        "source_digest": sha256_bytes(transcript),
        "detail": f"exit_code={exit_code}; timed_out={str(timed_out).lower()}",
        "collected_at": started,
        "provenance": {
            "command": command,
            "cwd": str(cwd),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        },
    }


def collect_artifact_evidence(*, evidence_id: str, kind: str, path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "evidence_id": evidence_id,
        "type": kind,
        "ref": str(path.relative_to(root)),
        "supports": "context",
        "source_digest": sha256_bytes(data),
        "detail": f"artifact_size={len(data)}",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {"size": len(data)},
    }
