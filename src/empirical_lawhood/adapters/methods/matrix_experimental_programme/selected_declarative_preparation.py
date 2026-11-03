# SPDX-License-Identifier: MPL-2.0
"""Explicit selected E5/E6 choices over existing source and lowering owners.

The request selects original scientific operands and real authority records.
Only this owner derives current programmes, roots, graphs and resource cells.
No qualification, receipt, source history or grant is copied to changed science.
"""
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.formal_analysis import FormalMethodCatalog, FormalGapSourceCapabilityInventory
from empirical_lawhood.planning.study_authoring import StudyDraft, DesignInputRecord, DesignInputRole
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency,
    ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent

from . import selected_prepared_choices as scientific_choices
from . import selected_opportunity_bindings as opportunity_owner
from . import selected_protected_bindings as protected_owner
from . import selected_revision_bindings as revision_owner
from .preparation_experiment import MatrixPreparationSourceBank
from .preparation_records import MatrixPreparationSource, is_baseline_recipe
from .protected_preparation_records import MatrixConfirmationSources, MatrixReservedTransferSources
from .prepared_assay_method import MatrixPreparedAssayMethod
from .prepared_point import MatrixPreparedPublicSource, MatrixPreparedRecipeInterpretation
from .prepared_response_science import MatrixPreparedResponsePanel
from .selected_public import MatrixSelectedPublicPackage, MatrixSelectedNominationSelection, package_identity, selected_public_package_types
from .configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from .selected_point import MatrixSelectedPointDesign
from .selected_opportunity import (
    MatrixSelectedOpportunityProgramme, MatrixSelectedOpportunityPublicProgramme,
    MatrixSelectedOpportunityEvidence, public_programme, validate_opportunity_evidence,
)
from .selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme
from .selected_entry import MatrixSelectedEntryEvidence, MatrixSelectedOriginalProduct, validate_selected_entry_evidence
from .selected_entry_v2 import MatrixSelectedEntryEvidenceV2, validate_selected_entry_evidence_v2
from .selected_revision_programme import MatrixRevisionSelectedPackage, MatrixRevisionPreparedProgramme
from .selected_revision_entry import MatrixRevisionEntryEvidence, validate_entry_evidence
from .selected_operational_resources import MatrixSelectedOperationalResources
from .source_selection_metadata import _source_allocation
from .e6_transport_records import MatrixE6EmpiricalTransportPolicy, MatrixE6FrozenCalibrationProjection
from .selected_original_commitments import (
    MatrixPreparedOriginalCommitments, MatrixSelectedOpportunityEvidenceV2, MatrixSelectedEntryEvidenceV3,
    MatrixRevisionEntryEvidenceV2, committed_entry_evidence, require_original_commitments,
)

DEVELOPMENT_PROTOCOL_ID = "matrix.selected-prepared.declarative-development"
PROTECTED_PROTOCOL_ID = "matrix.selected-prepared.declarative-protected"
RESOURCE_BINDING = "matrix.selected-declarative.resource-binding"
PHASES = ("E5_OPPORTUNITY", "E5_CONFIRMATION", "E6_TRANSFER")


def pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)



def recipe_interpretations(specification, request):
    if tuple(value.arm_id for value in request.interpretations) != tuple(arm for arm, _ in specification.arms):
        raise ValueError("select one explicit E3 feature family for every declared preparation arm")
    return tuple(sorted((MatrixPreparedRecipeInterpretation(recipe.identity, family.family_id, family.scientific_premise)
        for (_, recipe), family in zip(specification.arms, request.interpretations, strict=True)),
        key=lambda value: value.recipe.object_id))


@dataclass(frozen=True, slots=True)
class SelectedPreparedDerivationRequestV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-request-v2"
    VERSION: ClassVar[str] = '2.0.0'
    request_id: str
    development_sources: MatrixPreparationSourceBank | None
    protected_sources: MatrixConfirmationSources | MatrixReservedTransferSources | None
    reservation: ScheduledReservation
    original_e3: MatrixSelectedPublicPackage | ConfiguredMatrixSelectedPublicPackage | None
    original_e3_products: tuple[MatrixSelectedOriginalProduct, ...]
    interpretations: tuple[scientific_choices.SelectedPreparedRecipeFamily, ...]
    original_e3_source: MatrixSelectedEntryEvidence | MatrixSelectedEntryEvidenceV2 | MatrixSelectedEntryEvidenceV3 | None
    original_e3_nomination: MatrixSelectedNominationSelection | None
    revision: MatrixRevisionSelectedPackage | None
    revision_evidence: MatrixRevisionEntryEvidence | MatrixRevisionEntryEvidenceV2 | None
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    campaign: CampaignSpec
    root: StudyDraft | None
    cutoff: InformationCutoff
    operator_id: str
    entry: ExperimentEntryPackage | None
    formal_methods: FormalMethodCatalog | None
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    source_configs: tuple[SourceMaterializationConfig, ...]
    phase_resources: MatrixSelectedOperationalResources
    operational_resources: SelectedE4OperationalResources | None
    original_commitments: MatrixPreparedOriginalCommitments
    produced_input_parents: tuple[ArtifactLineageParent, ...]

    def __post_init__(self):
        _validate_derivation_request(self)

    @property
    def identity(self):
        return pin(self, "request_id")


@dataclass(frozen=True, slots=True)
class SelectedPreparedDerivationRequestV3(CanonicalRecord):
    """E6's actual preTRAIN assessment policy; no editable calibrated radius."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-request-v3"
    VERSION: ClassVar[str] = '2.0.0'
    request_id: str
    development_sources: MatrixPreparationSourceBank | None
    protected_sources: MatrixConfirmationSources | MatrixReservedTransferSources | None
    reservation: ScheduledReservation
    original_e3: MatrixSelectedPublicPackage | ConfiguredMatrixSelectedPublicPackage | None
    original_e3_products: tuple[MatrixSelectedOriginalProduct, ...]
    interpretations: tuple[scientific_choices.SelectedPreparedRecipeFamily, ...]
    original_e3_source: MatrixSelectedEntryEvidence | MatrixSelectedEntryEvidenceV2 | MatrixSelectedEntryEvidenceV3 | None
    original_e3_nomination: MatrixSelectedNominationSelection | None
    revision: MatrixRevisionSelectedPackage | None
    revision_evidence: MatrixRevisionEntryEvidence | MatrixRevisionEntryEvidenceV2 | None
    assay: MatrixPreparedAssayMethod
    panels: tuple[tuple[str, tuple[MatrixPreparedResponsePanel, ...]], ...]
    campaign: CampaignSpec
    root: StudyDraft | None
    cutoff: InformationCutoff
    operator_id: str
    entry: ExperimentEntryPackage | None
    formal_methods: FormalMethodCatalog | None
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    source_configs: tuple[SourceMaterializationConfig, ...]
    phase_resources: MatrixSelectedOperationalResources
    operational_resources: SelectedE4OperationalResources | None
    original_commitments: MatrixPreparedOriginalCommitments
    produced_input_parents: tuple[ArtifactLineageParent, ...]
    transport_policy: MatrixE6EmpiricalTransportPolicy

    def __post_init__(self):
        _validate_derivation_request(self)
        if type(self.transport_policy) is not MatrixE6EmpiricalTransportPolicy:
            raise TypeError("expanded E6 requires its actual preTRAIN transport policy")
        self.transport_policy.__post_init__()

    @property
    def identity(self):
        return pin(self, "request_id")


def _validate_derivation_request(request):
    require_original_commitments(request.original_commitments)
    from .selected_produced_inputs import validate_produced_input_parents
    validate_produced_input_parents(request.produced_input_parents)
    validate_stable_id(request.request_id); validate_stable_id(request.operator_id)
    required = ((request.reservation, ScheduledReservation), (request.assay, MatrixPreparedAssayMethod),
        (request.campaign, CampaignSpec), (request.cutoff, InformationCutoff),
        (request.phase_resources, MatrixSelectedOperationalResources))
    optional = ((request.development_sources, MatrixPreparationSourceBank),
        (request.original_e3, selected_public_package_types()),
        (request.original_e3_nomination, MatrixSelectedNominationSelection),
        (request.revision, MatrixRevisionSelectedPackage), (request.revision_evidence, (MatrixRevisionEntryEvidence, MatrixRevisionEntryEvidenceV2)),
        (request.root, StudyDraft), (request.entry, ExperimentEntryPackage), (request.formal_methods, FormalMethodCatalog),
        (request.operational_resources, SelectedE4OperationalResources))
    for value, kind in required:
        if type(value) is not kind: raise TypeError("selected request needs its exact scientific/operational input owners")
        value.__post_init__()
    for value, kind in optional:
        if value is not None:
            if type(value) not in (kind if type(kind) is tuple else (kind,)): raise TypeError("selected request substitutes an immutable original input")
            value.__post_init__()
    if request.protected_sources is not None:
        if type(request.protected_sources) not in (MatrixConfirmationSources, MatrixReservedTransferSources):
            raise TypeError("selected protected physical inputs require their exact original source owner")
        request.protected_sources.__post_init__()
    if request.original_e3_source is not None:
        if type(request.original_e3_source) not in (MatrixSelectedEntryEvidence, MatrixSelectedEntryEvidenceV2, MatrixSelectedEntryEvidenceV3):
            raise TypeError("selected original E3 source custody has an unsupported revision")
        request.original_e3_source.__post_init__()
    for rows, kind in ((request.original_e3_products, MatrixSelectedOriginalProduct),
            (request.interpretations, scientific_choices.SelectedPreparedRecipeFamily),
            (request.formal_source_inventories, FormalGapSourceCapabilityInventory),
            (request.qualifications, MaterializationQualificationReceipt), (request.source_configs, SourceMaterializationConfig)):
        if type(rows) is not tuple or any(type(row) is not kind for row in rows):
            raise TypeError("selected request requires its exact immutable input rosters")
        for row in rows: row.__post_init__()
        if len({row.fingerprint() for row in rows}) != len(rows):
            raise ValueError("selected request duplicates original immutable inputs")
    if (type(request.panels) is not tuple or any(type(row) is not tuple or len(row) != 2
            or type(row[1]) is not tuple or any(type(value) is not MatrixPreparedResponsePanel for value in row[1])
            for row in request.panels) or tuple(key for key, _ in request.panels) != tuple(sorted({key for key, _ in request.panels}))):
        raise TypeError("selected request requires complete declared original future panels")


def committed_request_types():
    return SelectedPreparedDerivationRequestV2, SelectedPreparedDerivationRequestV3


def derive_sources(specification, request):
    """Project recipes onto exact supplied physical starts; no native work."""
    expected_request = (SelectedPreparedDerivationRequestV3 if specification.account == "ORIGINAL_E3"
        and specification.phase == "E6_TRANSFER" else SelectedPreparedDerivationRequestV2)
    if type(request) is not expected_request:
        raise TypeError("selected phase requires its exact current request; original-E3 E6 requires the preTRAIN transport policy")
    specification.__post_init__(); request.__post_init__()
    if specification.phase == "E5_OPPORTUNITY" and any(value is not None for value in
            (request.protected_sources, request.original_e3_source, request.original_e3_nomination,
                request.root, request.entry, request.formal_methods, request.operational_resources)):
        raise ValueError("development selections cannot carry protected entry or nominal authority")
    if specification.phase == "E5_OPPORTUNITY" and (request.qualifications or request.source_configs or request.formal_source_inventories):
        raise ValueError("development cannot borrow protected source/formal admission")
    if specification.account == "REVISION" and (request.original_e3_source is not None
            or request.original_e3_nomination is not None or request.interpretations):
        raise ValueError("revision sources cannot select unused E3 recipe or source assumptions")
    if specification.phase != "E5_CONFIRMATION" and request.original_e3_nomination is not None:
        raise ValueError("only CONF may consume a prior preparation nomination")
    if specification.phase == "E5_OPPORTUNITY":
        bank = request.development_sources
        if bank is None or request.protected_sources is not None:
            raise ValueError("development needs its original source bank, without protected source substitution")
        base = {}
        for source in bank.sources:
            key = source.root.root.independent_group_id
            operands = (source.original, source.root, source.initial, source.provenance, source.numerical_design)
            if base.setdefault(key, operands) != operands:
                raise ValueError("matched source bank changes an original start, source, stream or numerical subject")
        existing = {(value.root.root.independent_group_id, value.recipe.identity): value for value in bank.sources}
        values = []
        for group, operands in base.items():
            for _, recipe in specification.arms:
                actual = existing.get((group, recipe.identity))
                if actual is None:
                    digest = sha256(canonical_json_bytes((*operands, recipe))).hexdigest()
                    actual = MatrixPreparationSource("source.selected-declarative." + digest,
                        operands[0], operands[1], operands[2], recipe, operands[3], operands[4])
                values.append(actual)
        ordered = tuple(sorted(values, key=lambda row: row.source_id))
        sources = bank if bank.sources == ordered else MatrixPreparationSourceBank("bank.selected-declarative."
            + sha256(canonical_json_bytes((bank.allocations, ordered))).hexdigest(), bank.allocations, ordered)
    else:
        original = request.protected_sources
        closure = None if original is None else original.closure
        if closure is None or request.development_sources is not None or closure.reservation != request.reservation:
            raise ValueError("protected science needs its exact original reservation/source closure")
        hold = next(arm for arm, recipe in specification.arms if is_baseline_recipe(recipe))
        if specification.phase == "E5_CONFIRMATION" and type(original) is not MatrixConfirmationSources:
            raise ValueError("selected CONF cannot relabel reserved transfer sources")
        if specification.phase == "E6_TRANSFER" and type(original) is not MatrixReservedTransferSources:
            raise ValueError("selected transfer cannot relabel CONF sources")
        sources = (MatrixConfirmationSources("sources.selected-declarative." + sha256(canonical_json_bytes((closure.identity, specification.arms))).hexdigest(), closure,
            specification.arms, hold) if specification.phase == "E5_CONFIRMATION" else
            MatrixReservedTransferSources("sources.selected-declarative." + sha256(canonical_json_bytes((closure.identity, specification.arms))).hexdigest(), closure,
                tuple((coordinate, specification.arms[0][1]) for coordinate in
                    sorted({value.coordinate for value in closure.descriptors}, key=lambda value: value.object_id)), hold))
        if type(original) is type(sources) and replace(sources, record_id=original.record_id) == original:
            sources = original
    rows = tuple((None, value) for value in sources.sources) if type(sources) is MatrixPreparationSourceBank else sources.source_arms()
    groups = {value.root.root.independent_group_id for _, value in rows}
    expected_groups = specification.expected_groups * (2 if specification.phase == "E6_TRANSFER" else 1)
    if len(groups) != expected_groups or len(rows) != specification.expected_sources:
        raise ValueError("selected source derivation changes the complete declared independent group/arm census")
    return sources


def source_arms(specification, sources):
    if type(sources) is MatrixPreparationSourceBank:
        by_recipe = {recipe.identity: arm for arm, recipe in specification.arms}
        return tuple((by_recipe[value.recipe.identity], value) for value in sources.sources)
    return sources.source_arms()


def scientific_key(specification, request):
    # Operational admissions, resources and authority templates do not rename
    # physical/scientific subjects, and cannot create a derivation hash cycle.
    operands = (specification, request.development_sources, request.protected_sources,
        request.reservation, request.original_e3, request.interpretations,
        request.original_e3_nomination, request.revision, request.assay, request.panels)
    return sha256(canonical_json_bytes(operands)).hexdigest()


def revision_programme(specification, request, *, excluded_groups=()):
    """Project declared revision science before attaching its producer evidence."""
    if (specification.account != "REVISION" or request.revision is None
            or request.original_e3 is not None or request.original_e3_products):
        raise ValueError("revision selection needs actual E4 producer references without an E3 fallback")
    sources = derive_sources(specification, request)
    key = scientific_key(specification, request)
    return MatrixRevisionPreparedProgramme("programme.selected-declarative." + key, specification.phase,
        request.revision, sources, request.reservation, specification.arms, specification.expected_groups,
        request.assay, request.panels, specification.criterion, tuple(excluded_groups),
        specification.minimum_recoverable_groups, specification.tie_policy, specification.transfer_domain_claims,
        None if request.revision_evidence is None or request.revision_evidence.preparation_nomination is None
            else request.revision_evidence.preparation_nomination.record)


def make_programme(specification, request, *, e3_package=None, excluded_groups=(), nomination=None):
    if specification.account == "REVISION":
        if request.revision_evidence is None:
            raise ValueError("revision selection needs actual E4 producer references without an E3 fallback")
        programme = revision_programme(specification, request, excluded_groups=excluded_groups)
        key = scientific_key(specification, request)
        evidence = replace(request.revision_evidence, record_id="evidence.selected-declarative." + key, programme=programme.identity)
        validate_entry_evidence(evidence, programme)
    else:
        sources = derive_sources(specification, request)
        key = scientific_key(specification, request)
        rows = source_arms(specification, sources)
        if (request.original_e3 is None or request.revision is not None or request.revision_evidence is not None
                or e3_package is None or package_identity(e3_package) != request.original_e3.original_package):
            raise ValueError("original E3 selection needs its authentic original package and four producers")
        design = MatrixSelectedPointDesign("design.selected-declarative." + key, e3_package, specification.phase,
            specification.expected_groups, specification.arms, tuple((arm, MatrixPreparedPublicSource.from_source(value))
                for arm, value in rows), recipe_interpretations(specification, request))
        if specification.phase == "E5_OPPORTUNITY":
            full = MatrixSelectedOpportunityProgramme("programme.selected-declarative." + key, sources, request.reservation,
                design, request.assay, request.panels, specification.criterion,
                specification.minimum_recoverable_groups, specification.tie_policy)
            programme = public_programme(full)
            evidence = MatrixSelectedOpportunityEvidence("evidence.selected-declarative." + key, full.identity, request.original_e3_products)
            validate_opportunity_evidence(evidence, programme)
        else:
            original = request.original_e3_source
            if original is None:
                raise ValueError("protected original E3 science needs actual complete source qualification")
            full = MatrixSelectedProtectedProgramme("programme.selected-declarative." + key, sources, design,
                request.assay, request.panels, specification.criterion, specification.transfer_domain_claims,
                None if nomination is None else nomination[0], None if nomination is None else nomination[2],
                None if nomination is None else nomination[1])
            programme = MatrixSelectedPublicProgramme.from_programme(full)
            evidence = replace(original, record_id="evidence.selected-declarative." + key, programme=full.identity)
    evidence = committed_entry_evidence(evidence, request.original_commitments)
    validate_evidence(programme, evidence)
    return programme, evidence


@dataclass(frozen=True, slots=True)
class SelectedPreparedDerivedSelectionV4(CanonicalRecord):
    """Direct native inputs with the exact frozen scientific commitments."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-derived-selection-v4"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    request: SelectedPreparedDerivationRequestV2
    programme: MatrixSelectedOpportunityPublicProgramme | MatrixSelectedPublicProgramme | MatrixRevisionPreparedProgramme
    evidence: MatrixSelectedOpportunityEvidenceV2 | MatrixSelectedEntryEvidenceV3 | MatrixRevisionEntryEvidenceV2

    def __post_init__(self):
        _validate_derived_selection(self, SelectedPreparedDerivationRequestV2)

    @property
    def identity(self): return pin(self)


@dataclass(frozen=True, slots=True)
class SelectedPreparedDerivedSelectionV5(CanonicalRecord):
    """Expanded E6: the radius is projected from actual frozen original CAL."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-declarative-derived-selection-v5"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    specification: ObjectIdentity
    request: SelectedPreparedDerivationRequestV3
    programme: MatrixSelectedOpportunityPublicProgramme | MatrixSelectedPublicProgramme | MatrixRevisionPreparedProgramme
    evidence: MatrixSelectedOpportunityEvidenceV2 | MatrixSelectedEntryEvidenceV3 | MatrixRevisionEntryEvidenceV2
    transport_calibration: MatrixE6FrozenCalibrationProjection

    def __post_init__(self):
        _validate_derived_selection(self, SelectedPreparedDerivationRequestV3)
        if type(self.transport_calibration) is not MatrixE6FrozenCalibrationProjection:
            raise TypeError("expanded E6 selection requires its original frozen calibration projection")
        self.transport_calibration.__post_init__()
        from .e6_transport_science import validate_e6_transport_scope, validate_e6_public_calibration_projection
        validate_e6_transport_scope(self.request.transport_policy, self.programme)
        validate_e6_public_calibration_projection(self.transport_calibration, self.request.transport_policy,
            self.programme.point_design.package)

    @property
    def identity(self): return pin(self)


def _validate_derived_selection(selection, request_type):
    validate_stable_id(selection.record_id)
    if type(selection.specification) is not ObjectIdentity or type(selection.request) is not request_type:
        raise TypeError("selected derived metadata requires its exact declaration and current request")
    selection.specification.__post_init__(); selection.request.__post_init__()
    expected_evidence = {
        MatrixSelectedOpportunityPublicProgramme: MatrixSelectedOpportunityEvidenceV2,
        MatrixSelectedPublicProgramme: MatrixSelectedEntryEvidenceV3,
        MatrixRevisionPreparedProgramme: MatrixRevisionEntryEvidenceV2,
    }
    if type(selection.programme) not in expected_evidence:
        raise TypeError("selected derived metadata substitutes its installed programme owner")
    if type(selection.evidence) is not expected_evidence[type(selection.programme)]:
        raise TypeError("selected derived metadata requires its actual commitment-bearing evidence")
    selection.programme.__post_init__()
    validate_evidence(selection.programme, selection.evidence)
    if selection.evidence.original_commitments != selection.request.original_commitments:
        raise ValueError("selected current metadata substitutes original commitment evidence")


def derived_selection_types():
    return SelectedPreparedDerivedSelectionV4, SelectedPreparedDerivedSelectionV5


def validate_evidence(programme, evidence):
    if type(programme) is MatrixRevisionPreparedProgramme: return validate_entry_evidence(evidence, programme)
    if type(programme) is MatrixSelectedOpportunityPublicProgramme: return validate_opportunity_evidence(evidence, programme)
    validator = validate_selected_entry_evidence_v2 if type(evidence) is MatrixSelectedEntryEvidenceV2 else validate_selected_entry_evidence
    return validator(evidence, programme)


def validate_selection(specification, selection):
    if type(selection) not in derived_selection_types():
        raise TypeError("selected preparation requires its current direct-input selection")
    specification.__post_init__(); selection.__post_init__()
    request, programme = selection.request, selection.programme
    if selection.specification != specification.identity:
        raise ValueError("derived selected metadata belongs to another scientific declaration")
    sources = derive_sources(specification, request)
    if (programme.phase != specification.phase or programme.sources != sources
            or programme.assay != request.assay or programme.panels != request.panels
            or programme.criterion != specification.criterion):
        raise ValueError("derived selected programme changes explicit scientific choices")
    if specification.account == "REVISION":
        if type(programme) is not MatrixRevisionPreparedProgramme or make_programme(specification, request,
                excluded_groups=programme.excluded_group_ids) != (programme, selection.evidence):
            raise ValueError("derived revision metadata changes its original package or exact scientific choices")
    else:
        expected_type = MatrixSelectedOpportunityPublicProgramme if specification.phase == "E5_OPPORTUNITY" else MatrixSelectedPublicProgramme
        if type(programme) is not expected_type:
            raise ValueError("derived original-E3 metadata changes its public phase")
        design = programme.point_design
        if selection.evidence.upstream_products != request.original_e3_products:
            raise ValueError("derived E3 metadata changes exact selected original producer or reveal references")
        if specification.phase != "E5_OPPORTUNITY":
            expected_evidence = replace(request.original_e3_source,
                record_id="evidence.selected-declarative." + scientific_key(specification, request), programme=programme.original_programme)
            expected_evidence = committed_entry_evidence(expected_evidence, request.original_commitments)
            if expected_evidence != selection.evidence:
                raise ValueError("derived E3 source custody differs from selected original source/gate records")
        if (design.package != request.original_e3 or design.arms != specification.arms
                or design.expected_groups != specification.expected_groups
                or design.interpretations != recipe_interpretations(specification, request)
                or design.sources != tuple((arm, MatrixPreparedPublicSource.from_source(value)) for arm, value in source_arms(specification, sources))
                or specification.phase == "E5_OPPORTUNITY" and (programme.minimum_recoverable_groups,
                    programme.tie_policy) != (specification.minimum_recoverable_groups, specification.tie_policy)
                or specification.phase != "E5_OPPORTUNITY" and (programme.transfer_domain_claims != specification.transfer_domain_claims
                    or programme.nomination != request.original_e3_nomination)):
            raise ValueError("derived E3 public metadata changes actual package, recipes or assessment choices")
    return programme



def original_locator_records(request):
    """Exact existing metadata locators; no fitted body or permission record."""
    if type(request) not in committed_request_types():
        raise TypeError("prepared locators require their current request owner")
    if request.revision is None:
        originals=request.original_e3_products
        development=(() if request.original_e3_nomination is None else
            (request.original_e3_source.development_nomination,))
    else:
        evidence=request.revision_evidence
        if evidence is None:raise ValueError("revision requires its exact original producer locators")
        originals=(evidence.downstream_nomination,evidence.calibration)
        development=(evidence.revision_fit,evidence.revision_freeze,
            *((evidence.preparation_nomination,) if evidence.preparation_nomination is not None else ()))
    originals=tuple(sorted(originals,key=lambda value:value.record.object_id))
    development=tuple(sorted(development,key=lambda value:value.record.object_id))
    return tuple(("original."+str(index),value) for index,value in enumerate(originals))+tuple(
        ("development."+str(index),value) for index,value in enumerate(development))


def locator_record_types():
    from .selected_development_product import MatrixSelectedDevelopmentProduct
    from .selected_revision_development_product import MatrixRevisionDevelopmentProduct
    from ..matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
    return (MatrixSelectedOriginalProduct,MatrixSelectedDevelopmentProduct,
        MatrixRevisionDevelopmentProduct,SelectedE4DevelopmentProduct)


def validate_locator_records(request,records):
    if tuple(sorted(records))!=tuple(sorted(original_locator_records(request))):
        raise ValueError("prepared inputs change the complete original locator companion census")


@dataclass(frozen=True, slots=True)
class SelectedPreparedInputs:
    request: SelectedPreparedDerivationRequestV2 | SelectedPreparedDerivationRequestV3 | None = None
    selection: SelectedPreparedDerivedSelectionV4 | SelectedPreparedDerivedSelectionV5 | None = None
    files: tuple[tuple[str, PreparedExperimentFile], ...] = ()
    original_locators: tuple = ()


def allocation(programme):
    return _source_allocation(phase=programme.phase, selection_sha256=programme.fingerprint(), roster=programme.roster)


def bind_inputs(specification, records, *, files=None):
    if not isinstance(records,Mapping):raise TypeError("prepared inputs require exact named records")
    companions=tuple(sorted((key,value) for key,value in records.items()
        if key.startswith(("original.","development."))))
    primary={key:value for key,value in records.items() if key not in dict(companions)}
    if (set(primary) not in ({"request"}, {"selection"})
            or files is not None and not isinstance(files, Mapping)):
        raise ValueError("select exactly one explicit request or actual derived selection")
    request, selection = primary.get("request"), primary.get("selection")
    expected = committed_request_types() if request is not None else derived_selection_types()
    value = request if request is not None else selection
    if type(value) not in expected: raise TypeError("selected input role changes its declared record owner")
    value.__post_init__()
    if companions:validate_locator_records(request if selection is None else selection.request,companions)
    assigned = {} if selection is None else {"programme": allocation(validate_selection(specification, selection))}
    return PreparedExperimentInputs(assigned, SelectedPreparedInputs(request, selection,
        tuple(sorted(({} if files is None else files).items())),companions))


def owner_for(specification):
    return revision_owner if specification.account == "REVISION" else opportunity_owner if specification.phase == "E5_OPPORTUNITY" else protected_owner


def project_root(specification, selection):
    request, programme = selection.request, selection.programme
    root = request.root
    if type(root) is not StudyDraft or root.system is None or root.experiment is None:
        raise ValueError("protected derivation needs its explicit genuine root/clock/authority selections")
    if request.cutoff.clock_id not in {value.clock_id for value in root.system.clocks}:
        raise ValueError("selected derivation cutoff lacks its actual declared clock")
    refs = {selection.specification, programme.sources.closure.identity,
        programme.identity if type(programme) is MatrixRevisionPreparedProgramme else programme.original_programme,
        programme.selected_package.identity if type(programme) is MatrixRevisionPreparedProgramme else package_identity(programme.point_design.package)}
    if type(selection) is SelectedPreparedDerivedSelectionV5:
        refs.update((request.transport_policy.identity, selection.transport_calibration.identity))
    designs = {value.input_id: value for value in root.design_inputs}
    for reference in sorted(refs, key=lambda value: value.object_id):
        name = "design.selected-declarative." + reference.object_fingerprint
        designs[name] = DesignInputRecord(name, reference, reference.object_fingerprint, request.cutoff,
            DesignInputRole.READINESS_METADATA, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, request.operator_id)
    rows = tuple(designs[key] for key in sorted(designs))
    groups = tuple(sorted({value.root.root.independent_group_id for _, value in programme.sources.source_arms()}))
    if set(groups).intersection(root.development_unit_ids):
        raise ValueError("protected selected groups overlap declared prior development use")
    return replace(root, draft_id="root.selected-declarative." + specification.fingerprint(), design_inputs=rows,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(value.input_id for value in rows)),
        evaluation_unit_ids=groups, campaign=request.campaign)


def lower(specification, selection):
    programme = validate_selection(specification, selection)
    request, owner = selection.request, owner_for(specification)
    draft_id = "draft.selected-declarative." + scientific_key(specification, request)
    if specification.phase == "E5_OPPORTUNITY":
        if specification.account == "ORIGINAL_E3":
            return owner.lower_selected_opportunity(programme, evidence=selection.evidence,
                campaign=request.campaign, draft_id=draft_id, resources=request.phase_resources,
                produced_input_parents=request.produced_input_parents)
        root = owner.development_root(programme, "study." + specification.fingerprint())
    else:
        root = project_root(specification, selection)
    callback = owner.lower_revision_prepared_programme if specification.account == "REVISION" else owner.lower_selected_protected_programme
    transport = ({"transport_policy": request.transport_policy, "transport_calibration": selection.transport_calibration}
        if type(selection) is SelectedPreparedDerivedSelectionV5 else {})
    lowered = callback(programme, root=root, campaign=request.campaign, draft_id=draft_id,
        entry_evidence=selection.evidence, resources=request.phase_resources,
        produced_input_parents=request.produced_input_parents, **transport)
    if specification.phase != "E5_OPPORTUNITY":
        lowered = replace(lowered, draft=_bind_protected_obligations(lowered.draft, programme, owner))
    return lowered


def _protected_assessor(draft, owner):
    """Resolve the real phase assessor, including its retained verdict ports."""
    declarations = {value.registration().selection: value for value in owner.operation_declarations()}
    matches = tuple((operation, declarations[operation.selection]) for operation in draft.operations
        if declarations[operation.selection].scientific_hooks.adjudication_output_id is not None)
    if len(matches) != 1:
        raise ValueError("selected protected phase requires exactly one actual adjudication producer")
    operation, declaration = matches[0]
    if declaration.scientific_hooks.adjudication_output_id != "adjudication" or not {
            "adjudication", "product"} <= {value.output_id for value in declaration.outputs}:
        raise ValueError("selected protected assessor lacks its exact retained scientific verdict outputs")
    return operation, declaration


def _bind_protected_obligations(draft, programme, owner):
    """Name actual whole-phase proof ownership without declaring any verdict."""
    from empirical_lawhood.kernel.time import CausalPhase
    from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
    root = draft.prospective_draft
    experiment = root.experiment
    assessor, _ = _protected_assessor(draft, owner)
    sources = tuple(value for _, value in programme.sources.source_arms())
    expected = {(value.coordinate.clock_id, value.coordinate.physical_time(value.total_ticks))
        for value in sources}
    actual = {(value.clock_id, value.coordinate) for value in experiment.information_cutoffs}
    if actual != expected or any(value.phase is not CausalPhase.PRE_ACTION or not value.includes_coordinate
            for value in experiment.information_cutoffs):
        raise ValueError("selected protected cutoffs require the complete inclusive pre-action prepared source endpoints")
    # A shared clock/cutoff can cover many sources. Its proof owner must retain
    # every causal prefix, rather than arbitrarily selecting one group's node.
    parents = {}
    for link in draft.links:
        if link.producer_node_id is not None:
            parents.setdefault(link.consumer_node_id, set()).add(link.producer_node_id)
    ancestors, pending = set(), [assessor.node_id]
    while pending:
        node = pending.pop()
        for parent in parents.get(node, ()):
            if parent not in ancestors:
                ancestors.add(parent); pending.append(parent)
    if not {owner.node_id(value, "project") for value in sources} <= ancestors:
        raise ValueError("selected protected cutoff owner lacks the complete causal-prefix ancestry")
    required = set(_required_obligation_ids(experiment))
    operations = tuple(replace(value, obligation_ids=tuple(sorted(set(value.obligation_ids) |
        (required if value.node_id == assessor.node_id else set())))) for value in draft.operations)
    if any(sum(key in value.obligation_ids for value in operations) != 1 for key in required):
        raise ValueError("selected protected canonical obligation requires exactly one actual whole-phase verdict owner")
    return replace(draft, operations=operations)


def _protected_formal_entry(draft, request, owner):
    """Rebind graph addresses of a genuine phase catalog; keep its science."""
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.planning.experiment_entry import validate_experiment_entry
    from empirical_lawhood.planning.formal_analysis import FormalMethodRole, derive_formal_gap_applicability
    from empirical_lawhood.planning.formal_gaps import FormalGapCoverageDisposition
    from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
    root = draft.prospective_draft
    assessor, declaration = _protected_assessor(draft, owner)
    manifest = declaration.manifest()
    entry = request.entry
    candidates = tuple(value for value in request.formal_source_inventories
        if value.denominator_id == entry.coverage.denominator_id)
    if len(candidates) != 1:
        raise ValueError("selected protected formal coverage requires its exact authored phase denominator")
    inventory = candidates[0]
    if inventory.independent_unit_ids != root.evaluation_unit_ids:
        raise ValueError("selected protected formal denominator must retain every assigned whole group")
    inventory = replace(inventory, denominator_id=root.system.system_id,
        source_materializations=tuple(sorted((value.materialization for value in root.source_materializations),
            key=lambda value: value.object_id)))
    applicability = derive_formal_gap_applicability(entry.register, inventory)
    facts = {value.gap_id: value for value in applicability}
    required = set(_required_obligation_ids(root.experiment))
    controls = {value.control_id for value in root.experiment.controls}
    product = next(value for value in declaration.outputs if value.output_id == "product")
    assignments = []
    for assignment in entry.coverage.assignments:
        if assignment.disposition is FormalGapCoverageDisposition.TEST_IN_THIS_ACT:
            if (not set(assignment.obligation_ids) <= required
                    or not set(assignment.obligation_ids) <= set(assessor.obligation_ids)
                    or not set(assignment.selected_control_ids) <= controls):
                raise ValueError("selected protected formal coverage names foreign scientific obligations or controls")
            for role, family in ((FormalMethodRole.ESTIMATOR, assignment.selected_estimator_family_id),
                    (FormalMethodRole.MULTIPLICITY, assignment.selected_multiplicity_family_id)):
                binding = request.formal_methods.resolve(role, family)
                if (binding is None or assignment.gap_id not in binding.supported_gap_ids
                        or (binding.capability_key, binding.capability_version, binding.implementation_sha256) != (
                            manifest.capability_key, manifest.capability_version, manifest.implementation_sha256)
                        or binding.input_schema_id != declaration.config_record_type.SCHEMA
                        or binding.output_schema_id != product.payload_schema
                        or binding.maximum_outcome_access is not declaration.outcome_access
                        or EvidenceCeiling.lowest(binding.maximum_claim_ceiling, manifest.maximum_evidence_ceiling)
                            is not binding.maximum_claim_ceiling
                        or EvidenceCeiling.lowest(facts[assignment.gap_id].requested_claim_ceiling, binding.maximum_claim_ceiling)
                            is not facts[assignment.gap_id].requested_claim_ceiling):
                    raise ValueError("selected protected formal family requires its exact actual phase assessor contract")
            assignment = replace(assignment, output_ids=("adjudication", "product"),
                adjudication_owner_ids=(assessor.node_id,))
        assignments.append(assignment)
    coverage = replace(entry.coverage, candidate_act_id=root.draft_id, denominator_id=root.system.system_id,
        applicability=applicability, assignments=tuple(assignments))
    entry = replace(entry, coverage=coverage, checklist=replace(entry.checklist,
        draft=pin(root, "draft_id"), formal_gap_coverage=pin(coverage, "coverage_id")))
    validate_experiment_entry(root, entry, for_issue=False)
    inventories = tuple(sorted((inventory if value is candidates[0] else value
        for value in request.formal_source_inventories), key=lambda value: value.denominator_id))
    return entry, inventories


def resource_selection(specification, selection, draft):
    controls = selection.request.operational_resources
    if type(controls) is not SelectedE4OperationalResources:
        raise ValueError("protected selected work requires explicit existing operational envelope controls")
    owner = owner_for(specification)
    phases, groups = {}, {}
    by_selection = {value.registration().selection: value for value in owner.operation_declarations()}
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
    for operation in draft.operations:
        declaration = by_selection[operation.selection]
        config = decode_recursive_config_input(operation, declaration.registration()).record
        phase = owner.phase_of(config)
        phases[operation.node_id] = phase
        if phase in owner.NATIVE:
            groups[operation.node_id] = owner.units(config)[0]
    if set(dict(controls.source_request_limits)) != set(owner.PHASES):
        raise ValueError("select every exact installed phase source-request ceiling")
    return controls.for_component(component_id="selected-programme", budgets={value.node_id: value.resource_budget
        for value in draft.operations}, phases=phases, native_groups=groups)


def source_dependencies(draft, request, records):
    """Report every actual byte/config mismatch; never re-sign a changed input."""
    qualifiers = {row.source_id: row for row in request.qualifications}
    configs = {row.source_id: row for row in request.source_configs}
    if len(qualifiers) != len(request.qualifications) or len(configs) != len(request.source_configs):
        raise ValueError("selected source admission repeats a source ID")
    from .selected_produced_inputs import produced_history_parents
    by_input = dict(records)
    sources = tuple(row for row in draft.external_inputs
        if not produced_history_parents(row, by_input.get(row.input_id), request.produced_input_parents))
    dependencies = []
    for row in sources:
        qualification, config = qualifiers.get(row.input_id), configs.get(row.input_id)
        valid = qualification is not None and (
            qualification.materialization.object_id, qualification.materialization.object_schema,
            qualification.materialization.object_fingerprint, qualification.content_sha256,
            qualification.outcome_access, qualification.visibility_ceiling) == (
            row.logical_artifact_id, row.payload_schema, row.expected_content_sha256, row.expected_content_sha256,
            row.outcome_access, row.visibility_ceiling)
        if not valid:
            dependencies.append(ExperimentDependency("matrix.selected-declarative.qualification." + row.input_id,
                DependencyKind.SCIENTIFIC_EVIDENCE, "Supply a genuine current qualification for these exact newly derived bytes.", row.input_id))
        if config is None or (config.content_sha256, config.payload_schema, config.media_type, config.expected_size_bytes,
                config.outcome_access, config.visibility_ceiling) != (row.expected_content_sha256, row.payload_schema,
                row.media_type, row.maximum_size_bytes, row.outcome_access, row.visibility_ceiling):
            dependencies.append(ExperimentDependency("matrix.selected-declarative.source-config." + row.input_id,
                DependencyKind.EXTERNAL_INPUT, "Supply the exact current materialization configuration; old hashes are not relabelled.", row.input_id))
    unexpected = (set(qualifiers) | set(configs)) - {value.input_id for value in sources}
    if unexpected: raise ValueError("selected source admissions contain undeclared old/foreign source IDs")
    return dependencies


def prospective_design(specification, selection):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    from empirical_lawhood.runtime.recursive_storage_codecs import resolve_storage_codec
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from types import SimpleNamespace
    lowered = lower(specification, selection)
    request = selection.request
    if source_dependencies(lowered.draft, request, lowered.input_records):
        raise ValueError("protected design retains exact current source qualification/configuration dependencies")
    if request.entry is None or request.formal_methods is None or not request.formal_source_inventories:
        raise ValueError("protected design retains its genuine entry/formal source prerequisites")
    kinds = {kind.SCHEMA: kind for declaration in owner_for(specification).operation_declarations()
        for kind in declaration.record_codecs.values()}
    versions = {}
    for external in lowered.draft.external_inputs:
        kind = kinds.get(external.payload_schema)
        codec = resolve_storage_codec(MATRIX_STORAGE_CODECS, payload_schema=external.payload_schema, media_type=external.media_type)
        if kind is None and codec is None: raise ValueError("selected source lacks its installed exact storage/record revision")
        versions[external.logical_artifact_id] = kind.VERSION if kind is not None else codec.record_version
    from .selected_produced_inputs import produced_history_parents
    records = dict(lowered.input_records)
    retained = {value.input_id: produced_history_parents(value, records.get(value.input_id),
        request.produced_input_parents) for value in lowered.draft.external_inputs}
    draft = _source_projection(lowered.draft, SimpleNamespace(qualifications=request.qualifications,
        source_configs=request.source_configs), versions,
        retained_history_ids=tuple(sorted(key for key, parents in retained.items() if parents)))
    entry, inventories = _protected_formal_entry(draft, request, owner_for(specification))
    operands = tuple(RecursiveProspectiveOperand(value.logical_artifact_id, value.expected_content_sha256,
        value.maximum_size_bytes, value.payload_schema, value.media_type, value.outcome_access, value.visibility_ceiling,
        retained[value.input_id])
        for value in sorted(draft.external_inputs, key=lambda value: value.logical_artifact_id))
    design = RecursiveProspectiveDesignInputs("prospective.selected-declarative." + specification.fingerprint(), draft,
        entry, request.formal_methods, inventories, request.qualifications,
        draft.prospective_draft.design_inputs, operands)
    return replace(lowered, draft=draft), design, resource_selection(specification, selection, draft)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    specification.__post_init__()
    if type(specification) not in (scientific_choices.SelectedPreparedDevelopmentSpecification, scientific_choices.SelectedPreparedProtectedSpecification):
        raise TypeError("selected declarative preparation requires its exact registered specification")
    if type(execution) is not ExecutionSelection or not isinstance(scientific_inputs, Mapping):
        raise TypeError("selected declarative preparation needs explicit execution and typed inputs")
    execution.__post_init__()
    inputs = SelectedPreparedInputs() if method_inputs is None else method_inputs
    if type(inputs) is not SelectedPreparedInputs: raise TypeError("selected declarative preparation changes input owner")
    dependencies = []
    def missing(code, kind, detail, source=None):
        dependencies.append(ExperimentDependency("matrix.selected-declarative." + code, kind, detail, source))
    selection = inputs.selection
    if inputs.request is not None and type(inputs.request) not in committed_request_types():
        raise TypeError("selected preparation requires its actual commitment-bearing request")
    if selection is not None and type(selection) not in derived_selection_types():
        raise TypeError("selected preparation requires its current direct-input selection")
    if selection is None:
        if inputs.request is not None: derive_sources(specification, inputs.request)
        missing("derivation", DependencyKind.SOFTWARE, "Use public experiment-derive-inputs to authenticate originals and derive current metadata.", "request")
        n, groups = specification.expected_sources, specification.expected_groups * (2 if specification.phase == "E6_TRANSFER" else 1)
        return ExperimentPreparation(specification.identity, ExperimentCensus((("groups", groups), ("sources", n)),
            (("groups", 0), ("sources", 0)), (), (), 0), tuple(dependencies), execution=execution,
            specification_record=specification)
    programme = validate_selection(specification, selection)
    assigned = allocation(programme)
    if scientific_inputs != {"programme": assigned}: raise ValueError("selected preparation changes actual derived whole-group allocation")
    lowered = lower(specification, selection)
    request = selection.request
    resources = None
    if specification.phase != "E5_OPPORTUNITY":
        dependencies.extend(source_dependencies(lowered.draft, request, lowered.input_records))
        for value, code in ((request.entry, "entry"), (request.formal_methods, "formal-methods"),
                (request.formal_source_inventories, "formal-source-inventories")):
            if not value: missing(code, DependencyKind.SCIENTIFIC_EVIDENCE, "Select actual current " + code + ".")
        if not dependencies:
            lowered, _, resources = prospective_design(specification, selection)
            if execution.workers != resources.maximum_parallel_tasks:
                raise ValueError("selected worker profile differs from exact selected protected envelope maximum")
            missing("resource-binding", DependencyKind.SOFTWARE, "Bind the independently compiled candidate's exact extension projection.")
    for name, value, kind in (("workers", execution.workers, DependencyKind.ENVIRONMENT),
            ("environment", execution.environment_id, DependencyKind.ENVIRONMENT),
            ("source-snapshot", execution.source_snapshot, DependencyKind.ENVIRONMENT),
            ("output-root", execution.output_root, DependencyKind.STORAGE)):
        if value is None: missing(name, kind, "Select actual " + name + " before authoring.")
    if protocol_bytes is not None: raise ValueError("select scientific settings through the typed declarative specification")
    wanted = dict(lowered.input_artifacts)
    files = dict(inputs.files)
    for key, artifact in wanted.items():
        value = files.get(key)
        if value is None: missing("file." + key, DependencyKind.EXTERNAL_INPUT, "Select exact original initial/template bytes.", key)
        elif (value.identity, value.record_version, value.maximum_bytes) != (artifact, "1.0.0", artifact.size_bytes):
            raise ValueError("selected source file substitutes actual immutable bytes, revision or bound")
    if set(files) - set(wanted): raise ValueError("selected source files add undeclared roles")
    owner = owner_for(specification)
    declarations = {value.registration().selection: value for value in owner.operation_declarations()}
    operations, outputs, native = Counter(), Counter(), 0
    for operation in lowered.draft.operations:
        declaration = declarations[operation.selection]
        operations[operation.selection.capability_key] += 1
        native += int(declaration.execution_properties.native_effect)
        for output in declaration.outputs: outputs[output.profile.value.lower().replace("_", "-")] += 1
    census = ExperimentCensus((("groups", len(assigned.units)), ("sources", specification.expected_sources)),
        (("groups", len(assigned.units)), ("sources", len(programme.roster.cases))),
        tuple(sorted(operations.items())), tuple(sorted(outputs.items())), native)
    missing_science = any(value.kind is not DependencyKind.SOFTWARE for value in dependencies)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda value: value.code)), assigned,
        None if missing_science else lowered.draft, () if missing_science else lowered.input_records, execution, specification,
        tuple(sorted(((selection.record_id, selection),*original_locator_records(request)))), () if missing_science else inputs.files,
        source_configs=(),
        assessment_limitations=(ExperimentDependency(
            "matrix.selected-declarative.empirical-transport" if type(selection) is SelectedPreparedDerivedSelectionV5 else "matrix.selected-declarative.point-only",
            DependencyKind.SCIENTIFIC_EVIDENCE,
            "Empirical coverage, admission and service are assessed outside the original domain; transported qualification requires its own scientific warrant."
            if type(selection) is SelectedPreparedDerivedSelectionV5 else
            "Original calibration remains original-scope only; downstream uncertainty, transfer and scientific qualification are not established."),))


def validate_instance(*, specification, allocation, draft, source_records):
    rows = tuple(value for _, value in source_records if type(value) in derived_selection_types())
    if len(rows) != 1:
        raise ValueError("selected instance changes exact current derived input census")
    selection = rows[0]
    validate_locator_records(selection.request,tuple((name,value) for name,value in source_records
        if type(value) not in derived_selection_types()))
    expected = lower(specification, selection) if specification.phase == "E5_OPPORTUNITY" else prospective_design(specification, selection)[0]
    if globals()["allocation"](selection.programme) != allocation or expected.draft != draft:
        raise ValueError("selected instance changes exact declaration-derived source/resource/task graph")


def input_record_types():
    return (*committed_request_types(), *derived_selection_types(), MatrixSelectedOperationalResources,*locator_record_types())
