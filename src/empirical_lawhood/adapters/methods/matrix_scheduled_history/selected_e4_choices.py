# SPDX-License-Identifier: MPL-2.0
"""Pure selected E4 factorial choices; programme binding stays a later operation."""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from . import programme_factorial as factorial, selected_e4_methods as science
from . import selected_e4_programme as p, selected_e4_native_records as native
from .programme_selection import ScheduledRevisionTarget
from .e4_structural_prediction import E4MatchedRelationTarget


@dataclass(frozen=True, slots=True)
class SelectedE4FactorialChoices(CanonicalRecord):
    """Explicit complete family without a caller-computed programme hash."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/factorial-choices"
    VERSION: ClassVar[str] = "3.0.0"
    record_id: str
    target: ScheduledRevisionTarget | E4MatchedRelationTarget
    endpoint: str
    pair_scale: factorial.PairInteractionScale
    comparisons: tuple[factorial.ScheduledFactorialComparison, ...]
    alpha: Decimal | None
    procedure: str
    sampling_requirement: factorial.ScientificRequirementSpec | None
    assumption_references: tuple[ObjectIdentity, ...]
    missing_policy: str
    family_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        # The existing exact scientific validator owns all supported arithmetic.
        placeholder = ObjectIdentity("programme.configuration-validator", p.SelectedE4PhaseProgramme.SCHEMA,
            p.SelectedE4PhaseProgramme.VERSION, "0" * 64)
        self.bind(placeholder).__post_init__()

    def bind(self, programme):
        return science.SelectedE4FactorialSpecification("factorial." + self.record_id, programme, self.target,
            self.endpoint, self.pair_scale, self.comparisons, self.alpha, self.procedure,
            self.sampling_requirement, self.assumption_references, self.missing_policy, self.family_ids)

    @property
    def identity(self):
        return native.pin(self)
