from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


EvidenceType = Literal[
    "primary_source",
    "standard",
    "authoritative_manual",
    "executable_test",
    "compiler",
    "simulator",
    "emulator",
    "secondary_source",
    "human_review",
]


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    type: EvidenceType
    ref: str
    supports: Literal["confirm", "dispute", "context"]
    source_digest: str | None = None
    detail: str | None = None
    collected_at: str | None = None

    def record(self):
        data = asdict(self)
        if data["collected_at"] is None:
            data["collected_at"] = datetime.now(timezone.utc).isoformat()
        return data


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_strength(kind: str) -> int:
    return {
        "primary_source": 5,
        "standard": 5,
        "executable_test": 5,
        "compiler": 5,
        "simulator": 4,
        "emulator": 4,
        "authoritative_manual": 4,
        "human_review": 3,
        "secondary_source": 2,
    }.get(kind, 0)


def verification_from_evidence(evidence: list[dict], requires_verification: bool = True) -> str:
    if not evidence:
        return "needs_human_review" if requires_verification else "likely"

    confirms = [e for e in evidence if e.get("supports") == "confirm"]
    disputes = [e for e in evidence if e.get("supports") == "dispute"]

    if confirms and disputes:
        return "disputed"

    strongest_confirm = max((evidence_strength(e.get("type", "")) for e in confirms), default=0)
    strongest_dispute = max((evidence_strength(e.get("type", "")) for e in disputes), default=0)

    if strongest_dispute >= 4:
        return "false_positive"
    if strongest_confirm >= 4:
        return "confirmed"
    if strongest_confirm >= 2:
        return "likely"
    return "needs_human_review" if requires_verification else "likely"
