# SPDX-License-Identifier: MPL-2.0
"""Exact original source closure and separately derived protected preparations.

One actual reservation/allocation/specification is retained. Bounded references
resolve through one operation-local index; recipes create distinct prepared
sources sharing the actual original starts. These records grant no freshness,
numerical qualification, issue or outcome-access authority.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from bisect import bisect_left
from dataclasses import dataclass
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, ScheduledSpecification, _publication
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

from .preparation_records import MatrixCouplingRecipe, MatrixPreparationInitialState, MatrixPreparationInitialStateV2, MatrixPreparationSource, initial_state_types, MatrixOriginalScheduleRecipe, coupling_recipe_types, is_baseline_recipe


@dataclass(frozen=True, slots=True)
class MatrixProtectedSourceClosure(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/protected-source-closure"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    reservation: ScheduledReservation
    specification: ScheduledSpecification
    provenances: tuple[NumericalProducingProvenance, ...]
    descriptors: tuple[ScheduledSource, ...]
    audit: ScheduledExposureAudit
    audit_publication: ArtifactWriteResult
    initial_states: tuple[tuple[str, MatrixPreparationInitialState | MatrixPreparationInitialStateV2], ...]
    numerical_scope: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.reservation, ScheduledReservation), (self.specification, ScheduledSpecification),
                (self.audit, ScheduledExposureAudit), (self.audit_publication, ArtifactWriteResult), (self.numerical_scope, ObjectIdentity)):
            if type(value) is not kind:
                raise TypeError("protected source closure requires its exact original scientific/custody owners")
            value.__post_init__()
        if (type(self.descriptors) is not tuple or not self.descriptors
                or any(type(row) is not ScheduledSource for row in self.descriptors)
                or tuple(row.root_id for row in self.descriptors) != tuple(sorted({row.root_id for row in self.descriptors}))
                or type(self.provenances) is not tuple or not self.provenances
                or any(type(row) is not NumericalProducingProvenance for row in self.provenances)
                or tuple(row.fingerprint() for row in self.provenances) != tuple(sorted({row.fingerprint() for row in self.provenances}))
                or type(self.initial_states) is not tuple
                or tuple(key for key, _ in self.initial_states) != tuple(row.root_id for row in self.descriptors)
                or any(type(row) not in initial_state_types() for _, row in self.initial_states)):
            raise ValueError("protected source closure omits its complete unique selected roots/provenance/shared-start census")
        if {row.provenance for row in self.descriptors} != {row.identity for row in self.provenances}:
            raise ValueError("protected source closure adds or omits actual producing provenance")
        _publication(self.audit_publication, self.audit)
        index = self.source_index()
        index.require_roster(self.descriptors, expected_root_ids=tuple(value.root_id for value in self.descriptors))
        self.audit.validate_source(index.resolve(self.descriptors[0]))
        for _, initial in self.initial_states:
            initial.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def source_index(self):
        return ScheduledSourceIndex.from_shared(reservation=self.reservation, specification=self.specification,
            provenances=self.provenances)

    def original(self, descriptor, *, index):
        if type(descriptor) is not ScheduledSource:
            raise TypeError("protected source closure requires the current bounded source")
        position = bisect_left(self.descriptors, descriptor.root_id, key=lambda value: value.root_id)
        if position == len(self.descriptors) or self.descriptors[position] != descriptor:
            raise ValueError("protected source closure substitutes an unselected original subject")
        if (index.reservation_identity, index.specification_identity) != (
                descriptor.reservation, descriptor.specification):
            raise ValueError("protected closure resolution substitutes its shared source parents")
        return index.resolve(descriptor)

    def prepare_source(self, descriptor, recipe, *, index):
        """Derive a new preparation identity; do not rename its original subject."""
        original = self.original(descriptor, index=index)
        if type(recipe) not in coupling_recipe_types():
            raise TypeError("protected preparation requires its exact unchanged fixed recipe")
        position = bisect_left(self.initial_states, descriptor.root_id, key=lambda value: value[0])
        initial = self.initial_states[position][1]
        digest = sha256(canonical_json_bytes((descriptor.identity, initial.identity, recipe.identity))).hexdigest()
        return MatrixPreparationSource("prepared-source." + digest, ScheduledPublicSource.from_source(original),
            original.root, initial, recipe, original.provenance, original.numerical_design)


@dataclass(frozen=True, slots=True)
class MatrixConfirmationSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/confirmation-sources"
    record_id: str
    closure: MatrixProtectedSourceClosure
    recipes: tuple[tuple[str, MatrixCouplingRecipe | MatrixOriginalScheduleRecipe], ...]
    hold_arm_id: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.hold_arm_id)
        if type(self.closure) is not MatrixProtectedSourceClosure:
            raise TypeError("confirmation requires its exact original protected source closure")
        self.closure.__post_init__()
        if (type(self.recipes) is not tuple or len(self.recipes) != 2
                or tuple(arm for arm, _ in self.recipes) != tuple(sorted({arm for arm, _ in self.recipes}))
                or self.hold_arm_id not in dict(self.recipes)
                or any(type(recipe) not in coupling_recipe_types() for _, recipe in self.recipes)
                or not is_baseline_recipe(dict(self.recipes)[self.hold_arm_id])
                or sum(is_baseline_recipe(recipe) for _, recipe in self.recipes) != 1
                or len({recipe.identity for _, recipe in self.recipes}) != 2
                or any(row.root.root.role is not MatrixProgrammeRole.CONFIRMATION for row in self.closure.descriptors)):
            raise ValueError("confirmation requires actual fresh CONF roots and exactly the selected recipe versus HOLD")
        for arm, recipe in self.recipes:
            validate_stable_id(arm)
            recipe.__post_init__()
        sources = self.source_arms()
        if len({row.root.root.independent_group_id for _, row in sources}) * 2 != len(sources):
            raise ValueError("confirmation counts repeated coordinates or nested recipes as independent groups")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def source_arms(self):
        index = self.closure.source_index()
        return tuple(sorted(((arm, self.closure.prepare_source(descriptor, recipe, index=index))
            for descriptor in self.closure.descriptors for arm, recipe in self.recipes), key=lambda row: row[1].source_id))


@dataclass(frozen=True, slots=True)
class MatrixReservedTransferSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/reserved-transfer-sources"
    record_id: str
    closure: MatrixProtectedSourceClosure
    recipes: tuple[tuple[ObjectIdentity, MatrixCouplingRecipe | MatrixOriginalScheduleRecipe], ...]
    hold_arm_id: str

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.hold_arm_id)
        if type(self.closure) is not MatrixProtectedSourceClosure:
            raise TypeError("transfer requires its exact original protected source closure")
        self.closure.__post_init__()
        coordinates = {row.coordinate for row in self.closure.descriptors}
        if (type(self.recipes) is not tuple or not self.recipes
                or tuple(key.object_id for key, _ in self.recipes) != tuple(sorted({key.object_id for key, _ in self.recipes}))
                or {key for key, _ in self.recipes} != coordinates
                or any(type(key) is not ObjectIdentity or type(recipe) not in coupling_recipe_types() or not is_baseline_recipe(recipe) for key, recipe in self.recipes)
                or any(row.root.root.role is not MatrixProgrammeRole.WITHHELD_TRANSFER for row in self.closure.descriptors)):
            raise ValueError("transfer requires every actual reserved root and nominal HOLD per original coordinate")
        actual = {row.root.root_id for row in self.closure.reservation.allocation.roots if row.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
        if actual != {row.root_id for row in self.closure.descriptors}:
            raise ValueError("transfer drops or substitutes a member of its complete original pre-fit reserve")
        if len({row.root.root.independent_group_id for row in self.closure.descriptors}) != len(self.closure.descriptors):
            raise ValueError("transfer reuses a whole independent group across nested coordinates or regimes")
        self.source_arms()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    def source_arms(self):
        recipes = dict(self.recipes)
        index = self.closure.source_index()
        return tuple(sorted(((self.hold_arm_id, self.closure.prepare_source(row, recipes[row.coordinate], index=index))
            for row in self.closure.descriptors), key=lambda row: row[1].source_id))
