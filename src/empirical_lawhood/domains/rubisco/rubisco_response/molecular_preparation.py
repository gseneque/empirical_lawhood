# SPDX-License-Identifier: MPL-2.0
"""Complete matched preparation census, with no native entry or admission.

The selection expands every case, chemical alternative and parameter model into
both endpoints. Processing views live in the actual complete sequence cases.
Original custody is referenced, never manufactured by this pure reducer.
"""

from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import ChemicalProtocol, validate_paired_chemical_selection
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_assessment import MolecularPreparationAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import AtomicTransformation, validate_atomic_transformation


@dataclass(frozen=True, slots=True)
class MolecularPreparationSlot(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-preparation-slot"
    case: ObjectIdentity
    material: ObjectIdentity
    arm: str
    processing_view: str
    chemistry: ObjectIdentity
    parameter_model: ObjectIdentity
    preparation_protocol: ObjectIdentity
    temperature_k: Decimal

    def __post_init__(self):
        for row in (self.case, self.material, self.chemistry, self.parameter_model, self.preparation_protocol):
            exact(row, ObjectIdentity)
        if self.arm not in {"mutant", "wild_type"}:
            raise ValueError("molecular slot changes its paired endpoint meaning")
        validate_stable_id(self.processing_view)
        validate_decimal(self.temperature_k, field_name="temperature_k", minimum=Decimal(0))
        if self.temperature_k == 0:
            raise ValueError("molecular preparation needs a positive selected temperature")

    @property
    def identity(self):
        return ObjectIdentity.from_record("molecular.slot." + self.fingerprint(), self)

    @property
    def pair_key(self):
        return self.case.object_id, self.chemistry.object_id, self.parameter_model.object_id


@dataclass(frozen=True, slots=True)
class MolecularPreparationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-preparation-selection"
    selection_id: str
    cases: RubiscoCaseSet
    chemistries: tuple[ChemicalProtocol, ...]
    parameter_models: tuple[ObjectIdentity, ...]
    preparation_protocol: ObjectIdentity
    temperature_k: Decimal
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.cases, RubiscoCaseSet)
        if type(self.chemistries) is not tuple or not self.chemistries:
            raise ValueError("preparation needs its complete selected chemical alternatives")
        require_sorted_unique_ids(self.chemistries, attribute="protocol_id", field_name="chemistries")
        for row in self.chemistries:
            exact(row, ChemicalProtocol)
            for case in self.cases.cases:
                validate_paired_chemical_selection(case, row)
        identities(self.parameter_models)
        exact(self.preparation_protocol, ObjectIdentity)
        validate_decimal(self.temperature_k, field_name="temperature_k", minimum=Decimal(0))
        if self.temperature_k == 0:
            raise ValueError("preparation temperature cannot be zero")
        identities(self.sources)
        required = {self.cases.identity, self.preparation_protocol, *self.parameter_models,
                    *self.cases.sources, *(row.identity for row in self.chemistries),
                    *(source for row in self.chemistries for source in row.sources)}
        if not required.issubset(self.sources):
            raise ValueError("preparation selection loses original case/chemical/parameter sources")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    @property
    def slots(self):
        """Code-owned full Cartesian census; no caller-authored task identities."""
        return tuple(MolecularPreparationSlot(case.identity, material.identity, arm,
            material.processing_view, chemistry.identity, parameter, self.preparation_protocol, self.temperature_k)
            for case, chemistry, parameter in product(self.cases.cases, self.chemistries, self.parameter_models)
            for arm, material in (("mutant", case.mutant), ("wild_type", case.parent)))


@dataclass(frozen=True, slots=True)
class RetainedPreparationMember:
    """Reducer operands. Actual payloads stay with their selected source owner."""
    slot: MolecularPreparationSlot
    original_state: str
    representation: MolecularRepresentation | None
    assessment: MolecularPreparationAssessment | None
    original_evidence: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        exact(self.slot, MolecularPreparationSlot)
        _member_operands(self.slot, self.original_state,
            None if self.representation is None else self.representation.identity,
            self.assessment, self.original_evidence)
        if self.representation is not None:
            model = self.representation
            exact(model, MolecularRepresentation)
            if (model.material.identity, model.material.processing_view, model.chemistry.identity,
                    model.parameter_model, model.preparation_protocol, model.temperature_k) != (
                    self.slot.material, self.slot.processing_view, self.slot.chemistry,
                    self.slot.parameter_model, self.slot.preparation_protocol, self.slot.temperature_k):
                raise ValueError("preparation member changes its selected full endpoint/chemistry/parameter/temperature")
            if not {model.raw_topology, model.raw_coordinates}.issubset(self.original_evidence):
                raise ValueError("preparation member drops its original topology or coordinate evidence")


def _member_operands(slot, state, model, assessment, evidence):
    identities(evidence, allow_empty=True)
    if state not in {"AVAILABLE", "FAILED", "UNKNOWN", "NOT_ENTERED"}:
        raise ValueError("preparation census loses its original outcome state")
    if (state == "AVAILABLE" and model is None
            or state == "NOT_ENTERED" and (model is not None or assessment is not None or evidence)):
        raise ValueError("preparation availability disagrees with its retained operands")
    if state in {"FAILED", "UNKNOWN"} and not evidence:
        raise ValueError("failed/unknown preparation needs its original attempt evidence")
    if model is not None:
        exact(model, ObjectIdentity)
        if model.object_schema != MolecularRepresentation.SCHEMA or model.object_version != MolecularRepresentation.VERSION:
            raise ValueError("preparation member changes the molecular record revision")
    if assessment is not None:
        exact(assessment, MolecularPreparationAssessment)
        if model is None or assessment.representation != model:
            raise ValueError("preparation member substitutes another endpoint's assessment")


def _member_requirements(slot, state, model, assessment):
    prefix = "requirement." + slot.identity.object_id
    required = {prefix + ".original-preparation-custody", prefix + ".physical-chemical-admission"}
    if state != "AVAILABLE":
        required.add(prefix + ".available-preparation")
    if model is None:
        required.add(prefix + ".complete-molecular-representation")
    if assessment is None:
        required.add(prefix + ".independent-preparation-assessment")
    else:
        required.update(assessment.unresolved_requirement_ids)
    return tuple(sorted(required))


@dataclass(frozen=True, slots=True)
class MolecularPreparationMemberFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-preparation-member-finding"
    slot: MolecularPreparationSlot
    original_state: str
    representation: ObjectIdentity | None
    assessment: MolecularPreparationAssessment | None
    original_evidence: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        exact(self.slot, MolecularPreparationSlot)
        _member_operands(self.slot, self.original_state, self.representation, self.assessment, self.original_evidence)
        if self.unresolved_requirement_ids != _member_requirements(
                self.slot, self.original_state, self.representation, self.assessment):
            raise ValueError("preparation finding changes actual remaining endpoint requirements")

    @property
    def geometry_gate(self):
        return A.UNEVALUABLE if self.assessment is None else self.assessment.geometry_gate

    @property
    def force_gate(self):
        return A.UNEVALUABLE if self.assessment is None else self.assessment.force_gate


def _pairs(members):
    return tuple((members[i], members[i + 1]) for i in range(0, len(members), 2))


def _census_requirements(selection, members):
    required = {*selection.unresolved_requirement_ids,
                *(name for row in selection.chemistries for name in row.unresolved_requirement_ids),
                *(name for row in members for name in row.unresolved_requirement_ids)}
    for mutant, wild_type in _pairs(members):
        if mutant.representation is None or wild_type.representation is None:
            required.add("requirement." + mutant.slot.identity.object_id + ".matched-finite-transformation")
    return tuple(sorted(required))


@dataclass(frozen=True, slots=True)
class MolecularPreparationCensus(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-preparation-census"
    census_id: str
    selection: MolecularPreparationSelection
    members: tuple[MolecularPreparationMemberFinding, ...]
    transformations: tuple[AtomicTransformation, ...]
    unresolved_requirement_ids: tuple[str, ...]
    physical_and_chemical_admission: A = A.UNEVALUABLE
    new_native_calls: int = 0
    independent_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.census_id)
        exact(self.selection, MolecularPreparationSelection)
        if type(self.members) is not tuple or tuple(row.slot for row in self.members) != self.selection.slots:
            raise ValueError("preparation census drops/reorders a selected case, view, chemistry, parameter or endpoint")
        for row in self.members:
            exact(row, MolecularPreparationMemberFinding)
        if type(self.transformations) is not tuple:
            raise ValueError("preparation census requires its complete finite transformation tuple")
        expected = tuple((wild_type.representation, mutant.representation, mutant.slot.case)
            for mutant, wild_type in _pairs(self.members)
            if mutant.representation is not None and wild_type.representation is not None)
        for row in self.transformations:
            exact(row, AtomicTransformation)
            if row.kind != "FINITE_SEQUENCE_SUBSTITUTION":
                raise ValueError("matched endpoints need their finite sequence transformation")
        if tuple((row.before, row.after, row.case) for row in self.transformations) != expected:
            raise ValueError("preparation census drops or substitutes a matched finite transformation")
        if self.unresolved_requirement_ids != _census_requirements(self.selection, self.members):
            raise ValueError("preparation census prunes remaining scientific requirements")
        if (self.physical_and_chemical_admission is not A.UNEVALUABLE
                or type(self.new_native_calls) is not int or self.new_native_calls != 0
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("complete preparation census cannot create scientific admission or biological units")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.census_id, self)

    @property
    def state_counts(self):
        return tuple((state, sum(row.original_state == state for row in self.members))
            for state in ("AVAILABLE", "FAILED", "UNKNOWN", "NOT_ENTERED"))


def assess_preparation_census(selection, members, transformations, *, census_id):
    """Join every original endpoint and independently check each full atom map.

    Retained readers supply actual source/custody operands. This reducer opens
    no files, invokes no backend and does not convert references into authority.
    """
    exact(selection, MolecularPreparationSelection)
    if type(members) is not tuple or tuple(row.slot for row in members) != selection.slots:
        raise ValueError("preparation reducer requires its complete derived slot census")
    for member in members:
        exact(member, RetainedPreparationMember)
    if type(transformations) is not tuple:
        raise ValueError("preparation reducer requires all actual paired transformations")
    pairs = tuple((mutant, wild_type) for mutant, wild_type in _pairs(members)
                  if mutant.representation is not None and wild_type.representation is not None)
    if len(pairs) != len(transformations):
        raise ValueError("preparation reducer omits a finite endpoint transformation")
    cases = {row.identity: row for row in selection.cases.cases}
    for (mutant, wild_type), transformation in zip(pairs, transformations, strict=True):
        validate_atomic_transformation(transformation, wild_type.representation, mutant.representation,
            case=cases[mutant.slot.case])
    findings = tuple(MolecularPreparationMemberFinding(row.slot, row.original_state,
        None if row.representation is None else row.representation.identity, row.assessment, row.original_evidence,
        _member_requirements(row.slot, row.original_state, row.representation, row.assessment)) for row in members)
    return MolecularPreparationCensus(census_id, selection, findings, transformations,
        _census_requirements(selection, findings))
