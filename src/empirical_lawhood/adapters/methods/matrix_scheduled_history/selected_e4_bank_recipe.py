# SPDX-License-Identifier: MPL-2.0
"""Declared selected E4 bank recipes; no acquisition, qualification or authority.

The recipe creates new scientific source identities from explicit native inputs.
A seed derivation rule is a reproducible construction, never a sampling warrant.
Original E3 scientific products and their exposure remain unchanged.
"""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
    ConfiguredProtectedE3PreparationSelection, configured_preparation_types,
    validate_selection_science as validate_configured_selection_science,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import (
    ProtectedE3PreparationSelection, validate_selection_science,
)
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

from . import records as old
from . import selected_streams
from .source_index import ScheduledSourceIndex
from .selected_population import selected_e4_population_allocation, selected_e4_population_groups
from .forecast import ScheduledPublicSource
from .response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from .response_selection import ScheduledCalibrationCriterion, ScheduledResponseSelection
from .selected_e3_e4_records import (
    SelectedE3E4Design, SelectedE3E4DevelopmentBank, SelectedE3E4DevelopmentProgramme, SelectedE3E4ForecastDesign,
    require_e4_reserved_physical_exclusion,
)
from .selected_e4_programme import SelectedE4PhaseBank, SelectedE4PhaseProgramme

PHASES = ("CALIBRATION", "CONFIRMATION", "DEVELOPMENT")
CONSTRUCTION = "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"


def _pin(value, kind):
    kinds = kind if type(kind) is tuple else (kind,)
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) not in tuple((item.SCHEMA, item.VERSION) for item in kinds):
        raise TypeError("selected E4 recipe substitutes an exact versioned scientific operand")
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class SelectedE4BankRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/bank-recipe"
    record_id: str
    original_preparation: ObjectIdentity
    original_public_package: ObjectIdentity
    prototype: ObjectIdentity
    assay: ObjectIdentity
    prefix_policy: ObjectIdentity
    coordinates: tuple[MatrixParameterCoordinate, ...]
    population_designs: tuple[tuple[str, SelectedE3E4Design], ...]
    streams: selected_streams.SelectedE4StreamRecipe
    calibration_criterion: ScheduledCalibrationCriterion

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.original_preparation, (ProtectedE3PreparationSelection, *configured_preparation_types())),
                (self.original_public_package, (MatrixSelectedPublicPackage, ConfiguredMatrixSelectedPublicPackage)), (self.prototype, MatrixParameterCoordinate),
                (self.assay, ScheduledResponseProtocol), (self.prefix_policy, old.ScheduledPrefixPolicy)):
            _pin(value, kind)
        families = ((ProtectedE3PreparationSelection, MatrixSelectedPublicPackage),
            *((kind, ConfiguredMatrixSelectedPublicPackage) for kind in configured_preparation_types()))
        if not any((self.original_preparation.object_schema, self.original_preparation.object_version,
                self.original_public_package.object_schema, self.original_public_package.object_version) ==
                (preparation.SCHEMA, preparation.VERSION, public.SCHEMA, public.VERSION) for preparation, public in families):
            raise ValueError("selected E4 recipe mixes original preparation/predictor families")
        if (type(self.coordinates) is not tuple or any(type(value) is not MatrixParameterCoordinate for value in self.coordinates)
                or tuple(value.family_id for value in self.coordinates) != tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
                or len({value.coordinate_id for value in self.coordinates}) != len(self.coordinates)
                or type(self.population_designs) is not tuple
                or any(type(row) is not tuple or len(row) != 2 or type(row[1]) is not SelectedE3E4Design for row in self.population_designs)
                or tuple(phase for phase, _ in self.population_designs) != PHASES
                or type(self.streams) is not selected_streams.SelectedE4StreamRecipe
                or type(self.calibration_criterion) is not ScheduledCalibrationCriterion):
            raise TypeError("selected E4 recipe requires all four declared native families and all three complete explicit populations")
        for value in (*self.coordinates, *(design for _, design in self.population_designs),
                self.streams, self.calibration_criterion):
            value.__post_init__()
        designs = tuple(design for _, design in self.population_designs)
        if any(design.factors != designs[0].factors or design.confidence != designs[0].confidence for design in designs):
            raise ValueError("selected E4 phases substitute their common frozen factors or confidence")
        iid = dict(self.population_designs)['CALIBRATION'].family_sampling_rule == 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW'
        if (self.calibration_criterion.minimum_group_count > dict(self.population_designs)["CALIBRATION"].group_count
                or self.calibration_criterion.required_family_ids != (() if iid else tuple(sorted(FOUR_FAMILY_PREPARATION_IDS)))
                or iid and self.streams.family_seed_material_sha256 is None):
            raise ValueError("selected E4 calibration construction changes declared group/family denominator")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class SelectedE4BankRecipeSourceInputs(CanonicalRecord):
    """Retained original operands and actual publication locators, not custody."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/bank-recipe-source-inputs"
    record_id: str
    recipe: SelectedE4BankRecipe
    original_preparation: ProtectedE3PreparationSelection | ConfiguredProtectedE3PreparationSelection
    preparation_publication: ArtifactWriteResult
    original_public_package: MatrixSelectedPublicPackage | ConfiguredMatrixSelectedPublicPackage
    original_products: tuple[MatrixSelectedOriginalProduct, ...]
    assay: ScheduledResponseProtocol
    assay_publication: ArtifactWriteResult
    template_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.recipe, SelectedE4BankRecipe), (self.original_preparation, (ProtectedE3PreparationSelection, *configured_preparation_types())),
                (self.original_public_package, (MatrixSelectedPublicPackage, ConfiguredMatrixSelectedPublicPackage)), (self.assay, ScheduledResponseProtocol),
                (self.preparation_publication, ArtifactWriteResult), (self.assay_publication, ArtifactWriteResult),
                (self.template_publication, ArtifactWriteResult)):
            if type(value) not in (kind if type(kind) is tuple else (kind,)):
                raise TypeError("selected E4 bank recipe requires its exact original typed input/publication owners")
            value.__post_init__()
        preparation, public = self.original_preparation, self.original_public_package
        old._publication(self.preparation_publication, preparation)
        old._publication(self.assay_publication, self.assay)
        if (self.recipe.original_preparation != ObjectIdentity.from_record(preparation.selection_id, preparation)
                or self.recipe.original_public_package != public.identity or self.recipe.assay != ObjectIdentity.from_record(self.assay.protocol_id, self.assay)):
            raise ValueError("selected E4 recipe changes its original preparation/public predictor/assay")
        configured = type(preparation) in configured_preparation_types()
        if configured != (type(public) is ConfiguredMatrixSelectedPublicPackage):
            raise ValueError("selected E4 source operands mix original preparation/predictor families")
        validator = validate_configured_selection_science if configured else validate_selection_science
        validator(public.specification, public.allocation, preparation)
        roots = preparation.manifest.reservation.allocation
        rows = tuple(value for value in roots.coordinates if old.coordinate_identity(value) == self.recipe.prototype)
        if len(rows) != 1:
            raise ValueError("selected E4 recipe prototype is absent from original E3 native preparation")
        prototype, = rows
        policy = dict(preparation.manifest.native_specification.selection.coordinate_policies).get(self.recipe.prototype)
        if policy != self.recipe.prefix_policy:
            raise ValueError("selected E4 recipe changes its original frozen prefix policy")
        for coordinate in self.recipe.coordinates:
            if (coordinate.member, coordinate.primary_view, coordinate.fine_view, coordinate.clock_id, coordinate.q,
                    coordinate.initial_state_rule_id, coordinate.preparation_rule_id) != (
                    prototype.member, prototype.primary_view, prototype.fine_view, prototype.clock_id, prototype.q,
                    prototype.initial_state_rule_id, prototype.preparation_rule_id):
                raise ValueError("selected E4 recipe changes original paired numerical/member/initial conventions")
        if self.assay not in preparation.protocols:
            raise ValueError("selected E4 assay is not an actual original preparation protocol")
        selected = next((value for value in preparation.sources if value.root_id == self.assay.public_source.root.root_id), None)
        if selected is None:
            raise ValueError("selected E4 assay omits its exact original source")
        index=ScheduledSourceIndex.from_shared(reservation=preparation.manifest.reservation,
            specification=preparation.manifest.native_specification,provenances=preparation.manifest.provenances)
        self.assay.public_source.validate_source(index.resolve(selected))
        template, publication = self.assay.templates.array_artifact, self.template_publication
        if (template.artifact_id, template.payload_schema, template.sha256, template.media_type, template.size_bytes,
                self.assay.templates.outcome_access, self.assay.templates.visibility_ceiling) != (
                publication.logical.logical_artifact_id, publication.logical.payload_schema, publication.logical.content_sha256,
                publication.logical.media_type, publication.materialization.size_bytes,
                publication.logical.outcome_access, publication.logical.visibility_ceiling):
            raise ValueError("selected E4 recipe changes actual original complete template publication")
        expected = {old.identity(public.models), old.identity(public.model_freeze), public.calibration, old.identity(public.calibrated_freeze)}
        if (type(self.original_products) is not tuple or len(self.original_products) != 4
                or any(type(value) is not MatrixSelectedOriginalProduct for value in self.original_products)
                or tuple(value.record.object_id for value in self.original_products) != tuple(sorted({value.record.object_id for value in self.original_products}))
                or {value.record for value in self.original_products} != expected):
            raise ValueError("selected E4 recipe requires the exact four original issued scientific products")
        for value in self.original_products:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def recipe_allocation(inputs):
    """Derive the full three-phase matched census before any new publication."""
    if type(inputs) is not SelectedE4BankRecipeSourceInputs:
        raise TypeError("selected E4 allocation requires its exact typed recipe source bundle")
    inputs.__post_init__()
    recipe, original = inputs.recipe, inputs.original_preparation
    groups = selected_e4_population_groups(namespace=recipe.record_id, population_designs=recipe.population_designs,
        preparations=recipe.coordinates, streams=recipe.streams)
    streams = tuple((group, recipe.streams.streams(group, future=False))
        for group in sorted(group for _, _, assigned in groups for group in assigned))
    allocation = selected_e4_population_allocation(allocation_id="allocation." + recipe.record_id,
        namespace=recipe.record_id, preparations=recipe.coordinates, population_designs=recipe.population_designs,
        group_ids=groups, history_streams=streams, exposure=original.manifest.reservation.allocation.exposure)
    require_e4_reserved_physical_exclusion(allocation.coordinates, original.manifest.reservation)
    groups = allocation.independent_group_ids
    inputs.original_public_package.require_unused_groups(groups)
    reserves = {*inputs.original_public_package.allocation.unit_ids("transfer_nearby"),
        *inputs.original_public_package.allocation.unit_ids("transfer_shifted")}
    if reserves.intersection(groups):
        raise ValueError("selected E4 recipe consumes original E3 pre-fit transfer reserves")
    return allocation


def recipe_selection(inputs, reservation):
    policy = next(value for value in inputs.original_preparation.manifest.native_specification.selection.prefix_policies
        if old.identity(value) == inputs.recipe.prefix_policy)
    return old.ScheduledSelection("selection." + inputs.recipe.record_id, old.identity(reservation),
        inputs.original_preparation.manifest.native_specification.selection.numerical_design, (policy,),
        tuple((old.coordinate_identity(value), old.identity(policy)) for value in reservation.allocation.coordinates))


def recipe_responses(inputs, reservation, specification, provenance, phase):
    """Bind local references through one current shared scientific index."""
    if phase not in PHASES or type(provenance) is not NumericalProducingProvenance:
        raise TypeError("selected E4 bank requires an exact phase and producing provenance")
    provenance.__post_init__()
    descriptors, protocols = [], []
    index=ScheduledSourceIndex.from_shared(reservation=reservation,specification=specification,provenances=(provenance,))
    for root in reservation.allocation.roots:
        if root.root.role is not MatrixProgrammeRole(phase):
            continue
        reference=index.reference(source_id="source."+root.root.root_id,root_id=root.root.root_id,provenance=provenance.identity)
        source=index.resolve(reference)
        descriptors.append(reference)
        templates = replace(inputs.assay.templates, operand_id="templates." + source.root_id,
            source=old.identity(source), producers=(old.identity(source),))
        protocols.append(replace(inputs.assay, protocol_id="protocol." + source.root_id,
            public_source=ScheduledPublicSource.from_source(source), templates=templates))
    groups = tuple(sorted({descriptor.root.root.independent_group_id for descriptor in descriptors}))
    root_map = {root.root.independent_group_id: root for root in reservation.allocation.roots}
    panels = tuple((group, (
        ScheduledResponsePanel("panel." + group + ".0", group, "COMMON_NOISE_PANEL",
            "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", root_map[group].streams),
        ScheduledResponsePanel("panel." + group + ".1", group, "INDEPENDENT_FUTURE",
            "FRESH_DECLARED_FUTURE_START_AT_CUTOFF", inputs.recipe.streams.streams(group, future=True)),
    )) for group in groups)
    responses = ScheduledResponseSelection("responses." + inputs.recipe.record_id + "." + phase.lower(),
        ObjectIdentity.from_record(reservation.allocation.allocation_id, reservation.allocation), tuple(protocols), panels, (inputs.template_publication,),
        inputs.recipe.calibration_criterion if phase == "CALIBRATION" else None)
    responses.validate_allocation(reservation.allocation)
    return tuple(descriptors), responses


def recipe_bank(inputs, *, reservation, specification, provenance, criterion_publication, response_publication, phase):
    from .selected_e3_e4_records import selected_e3_fit_target
    descriptors, responses = recipe_responses(inputs, reservation, specification, provenance, phase)
    design = SelectedE3E4ForecastDesign("forecast-design." + inputs.recipe.record_id,
        inputs.original_public_package, old.identity(reservation.allocation), inputs.original_preparation.mathematical_protocol,
        criterion_publication, fit_target=selected_e3_fit_target(inputs.original_public_package))
    values = ("bank." + inputs.recipe.record_id + "." + phase.lower(), reservation, specification, (provenance,),
        descriptors, inputs.original_preparation.manifest.audit, inputs.original_preparation.manifest.audit_publication,
        design, responses, response_publication, dict(inputs.recipe.population_designs)[phase])
    return SelectedE3E4DevelopmentBank(*values) if phase == "DEVELOPMENT" else SelectedE4PhaseBank(*values, phase)


def recipe_programme(bank, phase):
    programme_id = "programme." + bank.bank_id.removeprefix("bank.")
    return (SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id=programme_id)
        if phase == "DEVELOPMENT" else SelectedE4PhaseProgramme.from_bank(bank, programme_id=programme_id))


def validate_selected_e4_recipe_bank(inputs, bank, phase):
    """Cold pure replay of the complete original recipe; publication custody is separate."""
    if type(inputs) is not SelectedE4BankRecipeSourceInputs or phase not in PHASES:
        raise TypeError("selected E4 recipe replay requires its exact source bundle and full phase")
    expected_type = SelectedE3E4DevelopmentBank if phase == "DEVELOPMENT" else SelectedE4PhaseBank
    if type(bank) is not expected_type or len(bank.provenances) != 1:
        raise TypeError("selected E4 recipe replay substitutes the exact phase bank/provenance")
    allocation = recipe_allocation(inputs)
    if bank.reservation.allocation != allocation:
        raise ValueError("selected E4 recipe replay changes its complete original allocation")
    expected_selection = recipe_selection(inputs, bank.reservation)
    if bank.specification.selection != expected_selection:
        raise ValueError("selected E4 recipe replay changes its original prefix/numerical selection")
    rebuilt = recipe_bank(inputs, reservation=bank.reservation, specification=bank.specification,
        provenance=bank.provenances[0], criterion_publication=bank.forecast_design.criterion_publication,
        response_publication=bank.response_selection_publication, phase=phase)
    if rebuilt.canonical_bytes() != bank.canonical_bytes():
        raise ValueError("selected E4 phase bank differs from complete retained recipe replay")
    return None


@dataclass(frozen=True, slots=True)
class SelectedE4BankRecipePublicationIndex(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-selected-e4/bank-recipe-publication-index"
    record_id: str
    recipe: ObjectIdentity
    source_inputs: ObjectIdentity
    provenance: ObjectIdentity
    banks: tuple[tuple[str, ObjectIdentity], ...]
    programmes: tuple[tuple[str, ObjectIdentity], ...]
    publications: tuple[tuple[str, ArtifactWriteResult], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.recipe, SelectedE4BankRecipe), (self.source_inputs, SelectedE4BankRecipeSourceInputs),
                (self.provenance, NumericalProducingProvenance)):
            _pin(value, kind)
        for rows in (self.banks, self.programmes, self.publications):
            if type(rows) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in rows):
                raise TypeError("selected E4 recipe publication index requires immutable exact rows")
            if tuple(key for key, _ in rows) != tuple(sorted({key for key, _ in rows})):
                raise ValueError("selected E4 recipe publication index aliases its retained census")
        if tuple(key for key, _ in self.banks) != PHASES or tuple(key for key, _ in self.programmes) != PHASES:
            raise ValueError("selected E4 recipe publication index omits a complete declared phase")
        for phase, pin in self.banks:
            _pin(pin, SelectedE3E4DevelopmentBank if phase == "DEVELOPMENT" else SelectedE4PhaseBank)
        for phase, pin in self.programmes:
            _pin(pin, SelectedE3E4DevelopmentProgramme if phase == "DEVELOPMENT" else SelectedE4PhaseProgramme)
        publications = dict(self.publications)
        required = {"allocation", "selection", "criterion", "recipe", "source-inputs", "provenance"}
        required.update(phase + "." + key for phase in PHASES for key in ("responses", "bank", "programme"))
        if set(publications) != required or any(type(value) is not ArtifactWriteResult for value in publications.values()):
            raise ValueError("selected E4 recipe publication index changes its complete metadata publication census")
        for key, value in self.publications:
            value.__post_init__()
        pinned = {"recipe": self.recipe, "source-inputs": self.source_inputs, "provenance": self.provenance}
        pinned.update((phase + ".bank", value) for phase, value in self.banks)
        pinned.update((phase + ".programme", value) for phase, value in self.programmes)
        for key, pin in pinned.items():
            publication = publications[key]
            if (publication.logical.payload_schema, publication.logical.content_sha256) != (
                    pin.object_schema, pin.object_fingerprint):
                raise ValueError("selected E4 recipe index substitutes its exact retained metadata bytes")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
