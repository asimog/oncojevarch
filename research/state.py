from __future__ import annotations

from dataclasses import replace

from research.models import Investigation


def revise_investigation(
    investigation: Investigation,
    *,
    evidence_ids: tuple[str, ...] = (),
    next_action: str | None = None,
    unresolved_uncertainty: tuple[str, ...] | None = None,
) -> Investigation:
    """Append newly admitted evidence and update the investigation's next action.

    Revisions are monotonic: existing evidence ids are preserved and duplicates are not repeated.
    Nothing in a revision rewrites previously recorded evidence.
    """

    evidence = investigation.evidence_ids + tuple(
        evidence_id for evidence_id in evidence_ids if evidence_id not in investigation.evidence_ids
    )
    return replace(
        investigation,
        evidence_ids=evidence,
        next_action=next_action if next_action is not None else investigation.next_action,
        unresolved_uncertainty=(
            unresolved_uncertainty
            if unresolved_uncertainty is not None
            else investigation.unresolved_uncertainty
        ),
    )
