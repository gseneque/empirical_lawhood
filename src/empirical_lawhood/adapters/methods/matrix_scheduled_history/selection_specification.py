# SPDX-License-Identifier: MPL-2.0
"""Editable E4 selections; immutable method identities are derived on lowering."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.experimental_selection import DeclaredCandidate, DeclaredSelectionDesign, WholeUnitFold
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .programme_records import ScheduledProgramme
from .programme_selection import (
    ScheduledRevisionSpecification, ScheduledRevisionTarget, ScheduledRevisionTrigger,
    ScheduledRevisionTuning, feature_definition, programme_selection_allocation,
)


@dataclass(frozen=True, slots=True)
class RevisionCandidateSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-candidate-selection"
    candidate_id: str
    tuning: ScheduledRevisionTuning

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        if type(self.tuning) is not ScheduledRevisionTuning:
            raise TypeError("editable revision candidates require their actual scientific tuning")
        self.tuning.__post_init__()


@dataclass(frozen=True, slots=True)
class ScheduledRevisionExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-experiment-specification"
    specification_id: str
    programme: ObjectIdentity
    target: ScheduledRevisionTarget
    trigger: ScheduledRevisionTrigger
    folds: tuple[WholeUnitFold, ...]
    fold_count: int
    maximum_fit_calls: int
    revision_candidates: tuple[RevisionCandidateSelection, ...]
    baseline_candidates: tuple[RevisionCandidateSelection, ...]
    revision_tie_order: tuple[str, ...]
    baseline_tie_order: tuple[str, ...]

    def __post_init__(self):
        self._validate_operands(programme_schema=ScheduledProgramme.SCHEMA)

    def _validate_operands(self, *, programme_schema):
        validate_stable_id(self.specification_id)
        if (type(self.programme) is not ObjectIdentity or self.programme.object_schema != programme_schema
                or type(self.target) is not ScheduledRevisionTarget or type(self.trigger) is not ScheduledRevisionTrigger
                or type(self.folds) is not tuple or not self.folds
                or any(type(row) is not WholeUnitFold for row in self.folds)
                or tuple(row.unit_id for row in self.folds) != tuple(sorted({row.unit_id for row in self.folds}))
                or type(self.fold_count) is not int or self.fold_count < 2
                or type(self.maximum_fit_calls) is not int or self.maximum_fit_calls < 1):
            raise ValueError("E4 authoring requires explicit original sources, whole-unit folds and a finite fit budget")
        self.target.__post_init__(); self.trigger.__post_init__()
        for row in self.folds:
            row.__post_init__()
        all_ids, tunings = set(), {}
        for candidates, ties in ((self.revision_candidates, self.revision_tie_order),
                                  (self.baseline_candidates, self.baseline_tie_order)):
            if (type(candidates) is not tuple or not candidates
                    or any(type(row) is not RevisionCandidateSelection for row in candidates)
                    or tuple(row.candidate_id for row in candidates) != tuple(sorted({row.candidate_id for row in candidates}))
                    or type(ties) is not tuple or len(ties) != len(candidates)
                    or set(ties) != {row.candidate_id for row in candidates}):
                raise ValueError("E4 authoring requires complete named candidate lists and explicit tie order")
            for row in candidates:
                row.__post_init__()
                if row.candidate_id in all_ids:
                    raise ValueError("revision and baseline candidate identities must be distinct")
                all_ids.add(row.candidate_id)
                if tunings.setdefault(row.tuning.tuning_id, row.tuning) != row.tuning:
                    raise ValueError("one declared tuning ID aliases different scientific settings")
        if len(self.revision_candidates) != len(self.baseline_candidates):
            raise ValueError("revision and baseline must retain comparable candidate and fitting budgets")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def derive_revision_specification(specification, programme):
    """Derive hashes, allocation references and method IDs from editable science."""
    if type(specification) is not ScheduledRevisionExperimentSpecification:
        raise TypeError("E4 authoring requires its editable experiment specification")
    specification.__post_init__()
    allocation = programme_selection_allocation(programme)
    if specification.programme != programme.identity or specification.target.criterion != programme.criterion:
        raise ValueError("E4 experiment selection changes its actual original programme or criterion")
    designs, tunings = [], {}
    for suffix, candidates, ties in (("revision", specification.revision_candidates, specification.revision_tie_order),
                                    ("baseline", specification.baseline_candidates, specification.baseline_tie_order)):
        for row in candidates:
            tunings[row.tuning.tuning_id] = row.tuning
        designs.append(DeclaredSelectionDesign("design." + specification.fingerprint() + "." + suffix,
            allocation.identity, "development",
            tuple(DeclaredCandidate(row.candidate_id, row.tuning.family_id, row.tuning.identity) for row in candidates),
            specification.folds, specification.fold_count, specification.maximum_fit_calls, ties,
            "MINIMIZE", "REQUIRE_COMPLETE", specification.target.identity, specification.target.criterion,
            feature_definition(programme).identity))
    result = ScheduledRevisionSpecification("selection." + specification.fingerprint(), programme.identity,
        specification.target, specification.trigger, *designs,
        tuple(tunings[key] for key in sorted(tunings)))
    result.validate_programme(programme)
    return result
