# SPDX-License-Identifier: MPL-2.0
"""Prospective E1 allocation and criterion binding before the whole design D.

Input mathematics contains no placeholder allocation. The same constructor
supplies the later whole-programme compiler; neither route acquires evidence.
"""
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_records import (
    E1CompactCriterion, E1CompactCriterionChoices, E1FamilySize,
)
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import (
    E1FactorRule, E1HistoryAllocation, E1HistoryRoot,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import coordinate_identity, identity
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids, validate_sha256, validate_stable_id,
)
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)

PROTOCOL_ID = "matrix.programme.e1-allocation"


def ordinary_streams(material, group):
    validate_sha256(material)
    validate_stable_id(group)
    return tuple(MatrixHistorySeed(purpose, sha256(canonical_json_bytes((material, group, purpose))).hexdigest())
        for purpose in HISTORY_PURPOSES)


def e1_allocation(*, namespace, coordinates, family_requirements, census, root_material):
    """Construct actual membership once from the selected original operands."""
    validate_stable_id(namespace)
    validate_sha256(root_material)
    if (type(census) is not MatrixFactorExposureCensus or type(coordinates) is not tuple
            or any(type(coordinate) is not MatrixParameterCoordinate for coordinate in coordinates)
            or type(family_requirements) is not tuple
            or any(type(requirement) is not E1FamilySize for requirement in family_requirements)):
        raise TypeError("E1 allocation requires exact current coordinates, family choices and exposure census")
    census.__post_init__()
    require_sorted_unique_ids(coordinates, attribute="coordinate_id", field_name="coordinates")
    require_sorted_unique_ids(family_requirements, attribute="family_id", field_name="family_requirements")
    if (len(coordinates) != 4 or {coordinate.family_id for coordinate in coordinates} != set(FOUR_FAMILY_PREPARATION_IDS)
            or {requirement.family_id for requirement in family_requirements} != set(FOUR_FAMILY_PREPARATION_IDS)):
        raise ValueError("E1 allocation requires one actual coordinate and denominator for each of its four families")
    for value in (*coordinates, *family_requirements):
        value.__post_init__()
    counts = {requirement.family_id: requirement.requested_roots for requirement in family_requirements}
    roots = []
    for family_index, coordinate in enumerate(coordinates):
        for ordinal in range(counts[coordinate.family_id]):
            group = "group." + namespace + ".e1." + str(family_index) + "." + str(ordinal).zfill(3)
            root = MatrixProgrammeRoot("root." + group, group, "regime." + coordinate.coordinate_id,
                coordinate.coordinate_id, MatrixProgrammeRole.CONFIRMATION, coordinate.clock_id)
            roots.append(E1HistoryRoot(root, coordinate_identity(coordinate), ordinary_streams(root_material, group)))
    return E1HistoryAllocation("allocation." + namespace + ".e1", coordinates,
        tuple(sorted(roots, key=lambda row: row.root.root_id)), census)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE1AllocationRequest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/e1-allocation-request"
    record_id: str
    namespace: str
    exposure_census: ObjectIdentity
    root_seed_material_sha256: str
    coordinates: tuple[MatrixParameterCoordinate, ...]
    factor_rule: E1FactorRule
    criterion_choices: E1CompactCriterionChoices
    metadata_budget: ResourceBudget

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.namespace)
        validate_sha256(self.root_seed_material_sha256)
        if (type(self.exposure_census) is not ObjectIdentity
                or (self.exposure_census.object_schema, self.exposure_census.object_version)
                    != (MatrixFactorExposureCensus.SCHEMA, MatrixFactorExposureCensus.VERSION)):
            raise TypeError("prospective E1 allocation requires its exact selected exposure census")
        self.exposure_census.__post_init__()
        for value, kind in ((self.factor_rule, E1FactorRule), (self.criterion_choices, E1CompactCriterionChoices),
                (self.metadata_budget, ResourceBudget)):
            if type(value) is not kind:
                raise TypeError("prospective E1 allocation requires exact mathematics and finite metadata resources")
            value.__post_init__()
        if (type(self.coordinates) is not tuple or len(self.coordinates) != 4
                or any(type(value) is not MatrixParameterCoordinate for value in self.coordinates)):
            raise TypeError("prospective E1 allocation requires four exact current coordinates")
        require_sorted_unique_ids(self.coordinates, attribute="coordinate_id", field_name="coordinates")
        if {coordinate.family_id for coordinate in self.coordinates} != set(FOUR_FAMILY_PREPARATION_IDS):
            raise ValueError("prospective E1 allocation omits a selected family")
        for coordinate in self.coordinates:
            coordinate.__post_init__()
        if self.criterion_choices.factor_rule != identity(self.factor_rule):
            raise ValueError("prospective E1 criterion choices change the exact factor rule")
        if any(type(getattr(self.metadata_budget, name)) is not int or getattr(self.metadata_budget, name) < 1
                for name in ("memory_bytes", "source_scan_bytes", "output_bytes")):
            raise ValueError("prospective E1 allocation requires finite positive metadata byte and memory ceilings")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE1AllocationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/e1-allocation-specification"
    specification_id: str
    request: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (type(self.request) is not ObjectIdentity or (self.request.object_schema, self.request.object_version)
                != (MatrixProgrammeE1AllocationRequest.SCHEMA, MatrixProgrammeE1AllocationRequest.VERSION)):
            raise TypeError("prospective E1 allocation requires its actual current request")
        self.request.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE1AllocationInputs:
    request: MatrixProgrammeE1AllocationRequest | None
    census: MatrixFactorExposureCensus | None
    allocation: E1HistoryAllocation | None
    criterion: E1CompactCriterion | None
    record_paths: tuple


def bind_inputs(specification, records, *, record_paths=None, files=None):
    if type(specification) is not MatrixProgrammeE1AllocationSpecification:
        raise TypeError("prospective E1 allocation requires its exact current specification")
    specification.__post_init__()
    kinds = {"request": MatrixProgrammeE1AllocationRequest, "exposure-census": MatrixFactorExposureCensus,
        "allocation": E1HistoryAllocation, "criterion": E1CompactCriterion}
    if files or set(records) - set(kinds):
        raise ValueError("prospective E1 allocation accepts only its declared current record inputs")
    for key, record in records.items():
        if type(record) is not kinds[key]:
            raise TypeError("prospective E1 allocation changes its exact " + key)
        record.__post_init__()
    request, census, allocation, criterion = (records.get(key) for key in kinds)
    if request is not None and request.identity != specification.request:
        raise ValueError("prospective E1 allocation substitutes its selected request")
    if request is not None and census is not None and census.identity != request.exposure_census:
        raise ValueError("prospective E1 allocation substitutes its selected exposure census")
    if (allocation is None) != (criterion is None):
        raise ValueError("prospective E1 outputs require both the allocation and its actually bound criterion")
    if allocation is not None:
        if request is None or census is None or allocation.exposure != census or allocation.coordinates != request.coordinates:
            raise ValueError("prospective E1 outputs omit or change their original copied selections")
        if (allocation.allocation_id != "allocation." + request.namespace + ".e1"
                or criterion != request.criterion_choices.bind_allocation(allocation, request.factor_rule)):
            raise ValueError("prospective E1 outputs change the actual allocation or selected criterion")
        # Validate deterministic source identity without rebuilding a population.
        by_coordinate = {coordinate_identity(coordinate): ordinal for ordinal, coordinate in enumerate(request.coordinates)}
        counts = {requirement.family_id: requirement.requested_roots
            for requirement in request.criterion_choices.family_requirements}
        for row in allocation.roots:
            family = by_coordinate[row.coordinate]
            group = row.root.independent_group_id
            prefix = "group." + request.namespace + ".e1." + str(family) + "."
            suffix = group.removeprefix(prefix)
            if (not group.startswith(prefix) or not suffix.isdecimal()
                    or suffix != str(int(suffix)).zfill(3)
                    or int(suffix) >= counts[request.coordinates[family].family_id]
                    or row.root.root_id != "root." + group
                    or row.root.regime_id != "regime." + request.coordinates[family].coordinate_id
                    or row.streams != ordinary_streams(request.root_seed_material_sha256, group)):
                raise ValueError("prospective E1 outputs change their original assigned stream or root")
    return PreparedExperimentInputs({}, MatrixProgrammeE1AllocationInputs(request, census, allocation, criterion,
        tuple(sorted((record_paths or {}).items()))))


def prepare(specification, *, execution, method_inputs=None, **_kwargs):
    specification.__post_init__()
    dependencies = []
    if method_inputs is not None and type(method_inputs) is not MatrixProgrammeE1AllocationInputs:
        raise TypeError("prospective E1 preparation requires exact current bound inputs")
    for name, kind in (("workers", DependencyKind.ENVIRONMENT), ("environment_id", DependencyKind.ENVIRONMENT),
            ("source_snapshot", DependencyKind.ENVIRONMENT), ("output_root", DependencyKind.STORAGE)):
        if getattr(execution, name) is None:
            dependencies.append(ExperimentDependency("programme-e1-allocation.execution." + name.replace("_", "-"),
                kind, "Select explicit " + name + "."))
    if method_inputs is not None and method_inputs.allocation is not None:
        dependencies.append(ExperimentDependency("programme-e1-allocation.use-criterion", DependencyKind.EXTERNAL_INPUT,
            "Use this actual bound criterion and unchanged E1 mathematics in D, then compile all programme inputs."))
    else:
        for key, name in (("request", "request"), ("exposure-census", "census")):
            if method_inputs is None or getattr(method_inputs, name) is None:
                dependencies.append(ExperimentDependency("programme-e1-allocation." + key, DependencyKind.EXTERNAL_INPUT,
                    "Supply the exact prospective " + key + ".", key))
        dependencies.append(ExperimentDependency("programme-e1-allocation.derive", DependencyKind.EXTERNAL_INPUT,
            "Use experiment-derive-inputs to produce the actual allocation and bind the selected criterion before D."))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda value: value.code)), execution=execution, specification_record=specification)
