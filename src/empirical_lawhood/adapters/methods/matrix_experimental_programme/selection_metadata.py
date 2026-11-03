# SPDX-License-Identifier: MPL-2.0
"""Source and phase joins without replaying the scientific outcome worker."""

from .records import MatrixProgrammeEvidence
from .science import MatrixPreparationNomination, validate_sources


def validate_phase_metadata(specification, roster, package, allocation, nomination):
    """Freeze actual nomination/freshness; compute no case result or statistic."""
    if specification.phase == "E5_CONFIRMATION":
        if (type(nomination) is not MatrixPreparationNomination or nomination.identity != specification.nomination
                or nomination.package != package.identity or nomination.disposition != "NOMINATED"
                or nomination.selected_arm_id not in specification.arm_ids
                or nomination.selected_arm_id == specification.hold_arm_id
                or set(nomination.development_unit_ids) & set(allocation.unit_ids())):
            raise ValueError("E5 confirmation changes the frozen recipe/package or reuses development groups")
        if nomination.functional_criterion != specification.criterion or nomination.tie_policy != specification.tie_policy:
            raise ValueError("E5 confirmation changes its frozen functional criterion or recipe-selection rule")
        if any(case.recipe != nomination.selected_recipe for case in roster.cases if case.arm_id == nomination.selected_arm_id):
            raise ValueError("E5 confirmation replaces its development-selected unchanged fixed recipe")
        if any(case.recipe != nomination.hold_recipe for case in roster.cases if case.arm_id == specification.hold_arm_id):
            raise ValueError("E5 confirmation replaces its original HOLD recipe")
        return nomination.selected_arm_id
    if nomination is not None:
        raise ValueError("opportunity and E6 outcomes cannot import a later preparation nomination")
    return None


def validate_later_selection(specification, roster, package, evidence, nomination=None):
    """Authenticate immutable source/evidence identities and phase applicability.

    Outcome validity, complete response-cell arithmetic, functional headroom,
    nomination, case reduction and probability calculations remain in the one
    registered scientific worker. Missing outcome rows remain assigned units.
    """
    allocation, design = validate_sources(specification, roster, package)
    if (type(evidence) is not MatrixProgrammeEvidence or evidence.identity != specification.evidence
            or evidence.roster != roster.identity or evidence.package != package.identity):
        raise ValueError("later selection changes its exact original evidence bank")
    if {row.case_id for row in evidence.rows} - {case.case_id for case in roster.cases}:
        raise ValueError("later selection adds unassigned original source cases")
    validate_phase_metadata(specification, roster, package, allocation, nomination)
    return allocation, design
