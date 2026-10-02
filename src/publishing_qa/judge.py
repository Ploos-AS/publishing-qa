from __future__ import annotations

from typing import Any


SEVERITY_ORDER = {"info":0,"low":1,"medium":2,"high":3,"critical":4,"blocker":5}


def judge_record(consensus: dict[str, Any], findings_by_id: dict[str, dict[str, Any]]):
    originals = [findings_by_id[x] for x in consensus["finding_ids"] if x in findings_by_id]
    max_severity = max((x["severity"] for x in originals), key=lambda s: SEVERITY_ORDER[s], default="info")
    statuses = {x.get("verification_status", "unverified") for x in originals}
    consensus_status = consensus.get("verification_status", "unverified")
    if consensus_status != "unverified":
        statuses = {consensus_status}

    if "confirmed" in statuses:
        disposition = "confirmed"
    elif "false_positive" in statuses and len(statuses) == 1:
        disposition = "false_positive"
    elif "disputed" in statuses:
        disposition = "disputed"
    else:
        disposition = "needs_human_review" if consensus["requires_verification"] else "likely"

    return {
        "consensus_id": consensus["consensus_id"],
        "disposition": disposition,
        "max_reported_severity": max_severity,
        "agreement_count": consensus["agreement_count"],
        "requires_verification": consensus["requires_verification"],
        "reason": "Disposition is derived from explicit verification states; reviewer agreement is informational only.",
    }
