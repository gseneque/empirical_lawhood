# SPDX-License-Identifier: MPL-2.0
"""Additive CONF entry with a genuine development nomination producer.

Original E3 products retain issued/reveal custody. The opportunity nomination
has its actual authored development packet and ordinary receipt, separately.
"""

from dataclasses import dataclass
from typing import ClassVar


from .selected_development_product import MatrixSelectedDevelopmentProduct
from .selected_entry import MatrixSelectedEntryEvidence, _validate_selected_entry_scope, reference
from .selected_protected_programme import MatrixSelectedPublicProgramme


@dataclass(frozen=True, slots=True)
class MatrixSelectedEntryEvidenceV2(MatrixSelectedEntryEvidence):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-entry-evidence-v2"
    development_nomination: MatrixSelectedDevelopmentProduct

    def __post_init__(self):
        MatrixSelectedEntryEvidence.__post_init__(self)
        if len(self.upstream_products) != 4 or type(self.development_nomination) is not MatrixSelectedDevelopmentProduct:
            raise TypeError("selected v2 entry separates original four issued E3 products from actual development nomination")
        self.development_nomination.__post_init__()


def validate_selected_entry_evidence_v2(evidence, programme):
    from .selected_original_commitments import MatrixSelectedEntryEvidenceV3
    if type(evidence) not in (MatrixSelectedEntryEvidenceV2, MatrixSelectedEntryEvidenceV3):
        raise TypeError("selected v2 entry requires its exact development-nomination evidence")
    evidence.__post_init__()
    if programme.phase != "E5_CONFIRMATION" or programme.nomination is None or evidence.development_nomination is None:
        raise ValueError("selected v2 development nomination entry is only the actual paired confirmation phase")
    nomination = programme.nomination.original_nomination if type(programme) is MatrixSelectedPublicProgramme else programme.nomination.identity
    development = evidence.development_nomination
    if (development.record != nomination or development.publication != programme.nomination_publication
            or development.receipt != reference(programme.nomination_receipt, "receipt_id")
            or (development.run_id, development.task_id) != (programme.nomination_receipt.run_id, programme.nomination_receipt.task_id)):
        raise ValueError("selected v2 entry substitutes its original development nomination publication or receipt")
    _validate_selected_entry_scope(evidence, programme, development_nomination=development)
