from __future__ import annotations

from collections import Counter
from typing import Any


BLOCKING_STATUSES = {"confirmed", "likely", "disputed", "needs_human_review"}


def _threshold_failures(findings: list[dict[str, Any]], release: dict[str, Any]) -> list[str]:
    counts = Counter(
        f.get("severity", f.get("max_reported_severity", "info"))
        for f in findings
        if f.get("disposition", f.get("verification_status", "unverified")) in BLOCKING_STATUSES
    )
    reasons = []
    for severity in ("blocker", "critical", "high"):
        maximum = int(release.get(f"max_{severity}", 0))
        if counts[severity] > maximum:
            reasons.append(f"{severity} findings {counts[severity]} exceed allowed {maximum}")
    return reasons


def evaluate_release_gate(
    *,
    release: dict[str, Any],
    deterministic_ok: bool,
    build_ok: bool,
    review_run: dict[str, Any] | None,
    qualifications: list[dict[str, Any]],
    required_providers: list[str],
    judged_findings: list[dict[str, Any]],
    human_approved: bool,
) -> dict[str, Any]:
    gates = []

    def gate(name: str, required: bool, passed: bool, reason: str):
        gates.append({"name": name, "required": required, "passed": passed, "reason": reason})

    req_det = bool(release.get("require_deterministic_tests", True))
    gate("deterministic", req_det, deterministic_ok or not req_det, "deterministic QA passed" if deterministic_ok else ("deterministic QA not required" if not req_det else "deterministic QA failed"))

    req_build = bool(release.get("require_build", True))
    gate("build", req_build, build_ok or not req_build, "publication build passed" if build_ok else ("publication build not required" if not req_build else "publication build failed"))

    review_ok = bool(review_run and review_run.get("complete"))
    gate("required_reviewers", True, review_ok, "all required reviewers completed" if review_ok else "required reviewer run incomplete")

    qualified = {q.get("provider") for q in qualifications if q.get("qualified")}
    missing = sorted(set(required_providers) - qualified)
    gate("provider_qualification", True, not missing, "all required providers qualified" if not missing else "unqualified providers: " + ", ".join(missing))

    threshold_reasons = _threshold_failures(judged_findings, release)
    gate("finding_thresholds", True, not threshold_reasons, "finding thresholds satisfied" if not threshold_reasons else "; ".join(threshold_reasons))

    req_human = bool(release.get("require_human_approval", True))
    gate("human_approval", req_human, human_approved or not req_human, "human approval recorded" if human_approved else ("human approval not required" if not req_human else "human approval missing"))

    passed = all(g["passed"] for g in gates if g["required"])
    return {
        "format_version": 1,
        "decision": "PASS" if passed else "FAIL",
        "gates": gates,
        "blocking_reasons": [g["reason"] for g in gates if g["required"] and not g["passed"]],
    }
