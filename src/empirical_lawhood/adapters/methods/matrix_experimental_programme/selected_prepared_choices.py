# SPDX-License-Identifier: MPL-2.0
"""Immutable selected preparation mathematics, without source or phase bindings."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .preparation_records import MatrixCouplingRecipe, MatrixOriginalScheduleRecipe, coupling_recipe_types, is_baseline_recipe, validate_matched_preparation_menu
from .records import MatrixFunctionalCriterion

PHASES = ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER")


def pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


@dataclass(frozen=True, slots=True)
class SelectedPreparedSpecification(CanonicalRecord):
    """Scientific settings, with no generated programme, graph or task IDs."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-specification"
    VERSION: ClassVar[str] = "2.0.0"
    specification_id: str
    account: str
    phase: str
    expected_groups: int
    arms: tuple[tuple[str, MatrixCouplingRecipe | MatrixOriginalScheduleRecipe], ...]
    criterion: MatrixFunctionalCriterion
    minimum_recoverable_groups: int | None
    tie_policy: str | None
    transfer_domain_claims: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (self.account not in ("ORIGINAL_E3", "REVISION") or self.phase not in PHASES
                or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.criterion) is not MatrixFunctionalCriterion
                or type(self.arms) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.arms)
                or tuple(arm for arm, _ in self.arms) != tuple(sorted({arm for arm, _ in self.arms}))
                or len(self.arms) != {"E5_OPPORTUNITY": 3, "E5_CONFIRMATION": 2, "E6_TRANSFER": 1}[self.phase]
                or any(type(recipe) not in coupling_recipe_types() for _, recipe in self.arms)
                or sum(is_baseline_recipe(recipe) for _, recipe in self.arms) != 1):
            raise ValueError("selected declarative science requires explicit complete phase, arms, counts and decision choices")
        if self.phase == "E5_OPPORTUNITY" or self.account == "REVISION":
            if (type(self.minimum_recoverable_groups) is not int or not 1 <= self.minimum_recoverable_groups <= self.expected_groups
                    or self.tie_policy not in ("LEXICAL_ARM_ID", "MINIMUM_TOTAL_EFFORT_THEN_LEXICAL")):
                raise ValueError("select explicit recoverability and tie operands for the actual programme")
        elif self.minimum_recoverable_groups is not None or self.tie_policy is not None:
            raise ValueError("original E3 protected phases do not select a new DEV nomination rule")
        self.criterion.__post_init__()
        if self.criterion.is_matched and (self.account != 'REVISION'
                or self.expected_groups != {'E5_OPPORTUNITY': 16, 'E5_CONFIRMATION': 80, 'E6_TRANSFER': 64}[self.phase]
                or self.minimum_recoverable_groups != 2 or self.tie_policy != 'MINIMUM_TOTAL_EFFORT_THEN_LEXICAL'):
            raise ValueError('matched prepared choices retain the fixed SR/BR account and complete amended phase counts/rule')
        if self.criterion.is_matched:
            validate_matched_preparation_menu(self.arms)
        if max(self.criterion.minimum_usable_groups, self.criterion.minimum_admitted_groups) > self.expected_groups:
            raise ValueError("selected functional thresholds exceed the declared complete independent groups")
        for arm, recipe in self.arms:
            validate_stable_id(arm); recipe.__post_init__()
            if recipe.effort_unit != self.criterion.effort_unit:
                raise ValueError("selected recipe and functional effort conventions differ")
        if type(self.transfer_domain_claims) is not tuple or (
                self.phase == "E6_TRANSFER" and (len(self.transfer_domain_claims) != 2 or any(value not in
                    ("INTERPOLATION_WITHIN_ASSESSED_DOMAIN", "EXTRAPOLATION_WITHIN_ASSESSED_DOMAIN")
                    for value in self.transfer_domain_claims))
                or self.phase != "E6_TRANSFER" and self.transfer_domain_claims):
            raise ValueError("select separate transfer interpretations only for the two retained transfer regimes")

    @property
    def identity(self):
        return pin(self, "specification_id")

    @property
    def expected_sources(self):
        return self.expected_groups * {"E5_OPPORTUNITY": 3, "E5_CONFIRMATION": 2, "E6_TRANSFER": 2}[self.phase]


@dataclass(frozen=True, slots=True)
class SelectedPreparedProtectedSpecification(SelectedPreparedSpecification):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-protected-specification"

    def __post_init__(self):
        SelectedPreparedSpecification.__post_init__(self)
        if self.phase == "E5_OPPORTUNITY":
            raise ValueError("protected declaration cannot select development work")


@dataclass(frozen=True, slots=True)
class SelectedPreparedDevelopmentSpecification(SelectedPreparedSpecification):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-development-specification"

    def __post_init__(self):
        SelectedPreparedSpecification.__post_init__(self)
        if self.phase != "E5_OPPORTUNITY":
            raise ValueError("development declaration cannot select protected work")


@dataclass(frozen=True, slots=True)
class SelectedPreparedRecipeFamily(CanonicalRecord):
    """An arm choice; generated recipe fingerprints remain code-owned."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-recipe-family"
    arm_id: str
    family_id: str
    scientific_premise: ObjectIdentity

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import STRATA
        validate_stable_id(self.arm_id)
        if self.family_id not in STRATA or type(self.scientific_premise) is not ObjectIdentity:
            raise ValueError("select an actual supported recipe family and explicit scientific premise")
        self.scientific_premise.__post_init__()
