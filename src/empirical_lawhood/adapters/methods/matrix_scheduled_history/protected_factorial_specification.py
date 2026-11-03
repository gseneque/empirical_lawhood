# SPDX-License-Identifier: MPL-2.0
"""Protected E4 selections reference the unchanged original scientific entry.

These metadata records grant neither fresh evidence nor outcome access. The
ordinary original criteria, receipt and complete acquisition roster remain
mandatory; the input-design seal does not replace that scientific chronology.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.experiment_entry import StudyDefinition

from .programme_factorial_confirmation import ScheduledFactorialAcquisitionLocator, ScheduledFactorialCriteriaBinding
from .programme_reduction import ScheduledProgrammeReduction
from .programme_selection import ScheduledRevisionDataBank


PROTOCOL_ID = "matrix.e4.protected-factorial-confirmation"


@dataclass(frozen=True, slots=True)
class ProtectedFactorialAcquisitionRoster(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/protected-factorial-acquisition-roster"
    roster_id: str
    acquisitions: tuple[ScheduledFactorialAcquisitionLocator, ...]

    def __post_init__(self):
        validate_stable_id(self.roster_id)
        if (type(self.acquisitions) is not tuple or len(self.acquisitions) != 16
                or any(type(row) is not ScheduledFactorialAcquisitionLocator for row in self.acquisitions)
                or tuple(row.wave_id for row in self.acquisitions) != tuple(sorted({row.wave_id for row in self.acquisitions}))
                or len({row.run_id for row in self.acquisitions}) != 16):
            raise ValueError("protected confirmation needs the complete sixteen original acquisition locators")
        for row in self.acquisitions:
            row.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.roster_id, self)


@dataclass(frozen=True, slots=True)
class ProtectedFactorialExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/protected-factorial-experiment-specification"
    specification_id: str
    original_study: ObjectIdentity
    criteria: ObjectIdentity
    acquisitions: ObjectIdentity
    question: str
    paired_inputs: tuple[ObjectIdentity, ...] = ()
    evidence_scope: str = "ORIGINAL_PROTECTED_E4_CONFIRMATION_NO_NEW_AUTHORITY"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for ref, kind in ((self.original_study, StudyDefinition), (self.criteria, ScheduledFactorialCriteriaBinding),
                (self.acquisitions, ProtectedFactorialAcquisitionRoster)):
            if (type(ref) is not ObjectIdentity
                    or (ref.object_schema, ref.object_version) != (kind.SCHEMA, kind.VERSION)):
                raise ValueError("protected experiment substitutes an original scientific source type or revision")
            ref.__post_init__()
        if (not isinstance(self.question, str) or not self.question.strip()
                or self.evidence_scope != "ORIGINAL_PROTECTED_E4_CONFIRMATION_NO_NEW_AUTHORITY"
                or len({self.specification_id, self.original_study.object_id, self.criteria.object_id,
                    self.acquisitions.object_id}) != 4):
            raise ValueError("protected experiment requires distinct exact original sources and its scientific question")
        if (type(self.paired_inputs) is not tuple
                or any(type(row) is not ObjectIdentity for row in self.paired_inputs)
                or tuple(row.object_id for row in self.paired_inputs) != tuple(sorted({row.object_id for row in self.paired_inputs}))
                or len(self.paired_inputs) not in (0, 2)
                or self.paired_inputs and {(row.object_schema, row.object_version) for row in self.paired_inputs} != {
                    (ScheduledProgrammeReduction.SCHEMA, ScheduledProgrammeReduction.VERSION),
                    (ScheduledRevisionDataBank.SCHEMA, ScheduledRevisionDataBank.VERSION)}):
            raise ValueError("protected experiment needs both exact original paired sources or neither")
        for row in self.paired_inputs:
            row.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)
