from __future__ import annotations

from typing import Any

from .consensus import group_findings, summarize_groups
from .judge import judge_record
from .release_gate import evaluate_release_gate


def run_pipeline(
    *,
    project: str,
    config: dict[str, Any],
    deterministic_report: dict[str, Any],
    review_run: dict[str, Any],
    qualifications: list[dict[str, Any]],
    human_approved: bool,
) -> dict[str, Any]:
    findings = list(review_run.get("findings", []))
    groups = summarize_groups(group_findings(findings))
    by_id = {f["finding_id"]: f for f in findings}
    judged = [judge_record(group, by_id) for group in groups]

    release = config.get("release", {})
    required = [
        spec["id"] if isinstance(spec, dict) else spec
        for spec in config.get("ai", {}).get("reviewers", {}).get("required", [])
    ]

    deterministic_ok = bool(deterministic_report.get("passed", False))
    build_ok = bool(deterministic_report.get("build_passed", False))

    gate = evaluate_release_gate(
        release=release,
        deterministic_ok=deterministic_ok,
        build_ok=build_ok,
        review_run=review_run,
        qualifications=qualifications,
        required_providers=required,
        judged_findings=judged,
        human_approved=human_approved,
    )

    return {
        "format_version": 1,
        "project": project,
        "decision": gate["decision"],
        "deterministic": deterministic_report,
        "review_run": review_run,
        "consensus": groups,
        "judged_findings": judged,
        "qualifications": qualifications,
        "release_gate": gate,
    }
