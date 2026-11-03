# SPDX-License-Identifier: MPL-2.0
"""Finite-dt instrument certification; never a future numerical-outcome promise.

The new certificate is a deliberate semantic projection relative to a disjoint
future source population. Its prerequisites retain their original DEV lanes.
Construction, serialization and publication convey no authentication: the API
owner must reconstruct it from the actual complete public TRAIN execution.
"""
from dataclasses import dataclass, fields
from hashlib import sha256
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as train
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import ConfiguredE3Measurement
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterFactorNumericalDesign
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as phase
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import require_e4_reserved_physical_exclusion
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity, NamedDecimal
from empirical_lawhood.kernel.serialization import (CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids,
    require_sorted_unique_strings, validate_relative_locator, validate_sha256, validate_stable_id)
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.evidence_profiles import EvidenceProfileSelection
from empirical_lawhood.planning.metatheory import (MetatheoryApplicability, MetatheoryCellDisposition,
    MetatheoryEvidenceCeiling, MetatheoryMethodSelection)
from empirical_lawhood.planning.scientific_source_qualification import (ScientificSourceGateEvidence,
    ScientificSourceGateKind, ScientificSourceGateSpec, ScientificSourceInvalidUnitPolicy,
    ScientificSourceQualificationSpec)
from empirical_lawhood.planning.source_pipelines import SourcePipelineProfile, SourcePipelineQualificationReceipt
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave

NAMESPACE = "matrix-source.finite-dt-instrument"
GATES = tuple(kind for kind in ScientificSourceGateKind
    if kind is not ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE)
STANDING = "FINITE_DT_INSTRUMENT_ONLY_MANDATORY_INDEPENDENT_CONTROLS_AND_NONUSE_NO_CONTINUUM_SAMPLING_OR_TRANSPORT"
BLIND, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


def pin(record, field="record_id"):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _exact(reference, kind):
    if (type(reference) is not ObjectIdentity or reference.object_schema != kind.SCHEMA
            or reference.object_version != kind.VERSION):
        raise ValueError("finite-dt source substitutes an exact typed scientific operand")
    reference.__post_init__()


def template_bytes(artifact):
    """Scientific template bytes, preserving separately recorded logical aliases."""
    return artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes


def instrument_signature(protocol):
    """Versioned exact assay semantics without per-root identity/source labels.

    Every response field enters the signature. Only protocol/source IDs and
    scientific-equivalent instrument labels are projected: original artifacts
    and protocols remain exact receipt-backed evidence in the acquisition.
    """
    if type(protocol) is not ScheduledResponseProtocol:
        raise TypeError("finite-dt instrument signature requires its exact actual response protocol")
    protocol.__post_init__()
    excluded = {"protocol_id", "public_source", "mechanical_model", "actions", "templates"}
    selected = tuple((field.name, getattr(protocol, field.name)) for field in fields(protocol) if field.name not in excluded)
    mechanical = tuple((field.name, getattr(protocol.mechanical_model, field.name)) for field in fields(protocol.mechanical_model)
        if field.name != "model_id")
    actions = tuple(sorted((value.role, value.amplitude, value.force_norm, value.pulse_steps) for value in protocol.actions))
    templates = template_bytes(protocol.templates.array_artifact), protocol.templates.members
    return sha256(canonical_json_bytes(("MATRIX_FINITE_DT_INSTRUMENT_SEMANTICS_V1", selected, mechanical, actions, templates))).hexdigest()


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtTrainingLocator(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-training-locator"
    authored_directory: str
    run_id: str
    packet: ObjectIdentity
    execution_plan: ObjectIdentity

    def __post_init__(self):
        validate_relative_locator(self.authored_directory)
        validate_stable_id(self.run_id)
        _exact(self.packet, AuthoredRecursiveWave)
        _exact(self.execution_plan, DevelopmentExecutionPlan)


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtRootControl(CanonicalRecord):
    """Only control/nonuse verdicts and exact original links; no target values."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-root-control"
    root_id: str
    group_id: str
    source: ObjectIdentity
    prefix: ObjectIdentity
    numerical: ObjectIdentity
    causal_prefix: ObjectIdentity
    frame_assessment: ObjectIdentity
    physical_forecast: ObjectIdentity
    responses: ObjectIdentity
    score: ObjectIdentity
    receipts: tuple[ObjectIdentity, ...]
    prefix_controls_pass: bool
    frame_controls_pass: bool
    frame_controls_violated: bool
    response_controls_pass: bool
    response_control_count: int
    causal_disposition: str
    response_disposition: str

    def __post_init__(self):
        validate_stable_id(self.root_id)
        validate_stable_id(self.group_id)
        for value, kind in ((self.source, scheduled.ScheduledSource), (self.prefix, train.NativeTrainingPrefixHistory),
                (self.numerical, train.NativeTrainingNumericalAssessment),
                (self.causal_prefix, train.NativeTrainingCausalPrefix),
                (self.frame_assessment, train.NativeTrainingFrameAssessment),
                (self.physical_forecast, train.NativeTrainingPhysicalForecast),
                (self.responses, train.NativeTrainingResponse), (self.score, train.NativeTrainingScore)):
            _exact(value, kind)
        require_sorted_unique_ids(self.receipts, attribute="object_id", field_name="actual TRAIN producer receipts")
        if not self.receipts or any(value.object_schema != CanonicalTaskReceipt.SCHEMA for value in self.receipts):
            raise ValueError("finite-dt controls omit actual TRAIN producer receipts")
        if (type(self.prefix_controls_pass) is not bool or type(self.frame_controls_pass) is not bool
                or type(self.frame_controls_violated) is not bool or type(self.response_controls_pass) is not bool
                or type(self.response_control_count) is not int or self.response_control_count < 0
                or self.causal_disposition not in ("AVAILABLE", "NO_ORIGIN", "UNEVALUABLE")
                or self.response_disposition not in ("COMPLETED", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or (self.response_disposition == "COMPLETED") != (self.response_control_count > 0)
                or self.response_disposition != "COMPLETED" and self.response_controls_pass
                or self.frame_controls_violated and self.frame_controls_pass):
            raise ValueError("finite-dt controls erase nonuse or invent an exercised response instrument")


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtInstrumentCertificate(CanonicalRecord):
    """New semantic projection for separately assigned future units, not raw TRAIN.

    Original receipt links remain development-visible. The public certificate
    discloses only whether mandatory independent implementation checks ran;
    it conveys no target value, prediction, source freshness or global warrant.
    """
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-instrument-certificate"
    record_id: str
    locator: MatrixFiniteDtTrainingLocator
    specification: ObjectIdentity
    request: ObjectIdentity
    acquisition: ObjectIdentity
    original_future_reservation: ObjectIdentity
    measurement: ConfiguredE3Measurement
    numerical: ObjectIdentity
    factor_numerical: ObjectIdentity
    instrument_sha256: str
    criterion: ObjectIdentity
    provenances: tuple[ObjectIdentity, ...]
    templates: tuple[ArtifactIdentity, ...]
    training_effective_seeds: tuple[int, ...]
    reserved_future_effective_seeds: tuple[int, ...]
    controls: tuple[MatrixFiniteDtRootControl, ...]
    future_bank: ObjectIdentity
    future_group_ids: tuple[str, ...]
    cutoff: InformationCutoff
    prerequisite_outcome_access: OutcomeAccess = OutcomeAccess.DEVELOPMENT_VISIBLE
    prerequisite_visibility_ceiling: VisibilityCeiling = VisibilityCeiling.DEVELOPMENT_ONLY
    standing: str = STANDING

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.locator) is not MatrixFiniteDtTrainingLocator or type(self.measurement) is not ConfiguredE3Measurement:
            raise TypeError("finite-dt certificate needs its exact public TRAIN locator and measurement")
        self.locator.__post_init__()
        self.measurement.__post_init__()
        for value, kind in ((self.specification, train.NativeTrainingAcquisitionSpecification),
                (self.request, train.NativeTrainingAcquisitionRequest), (self.acquisition, train.NativeTrainingAcquisitionSeal),
                (self.original_future_reservation, scheduled.ScheduledReservation),
                (self.numerical, MatrixParameterNumericalDesign), (self.factor_numerical, MatrixParameterFactorNumericalDesign),
                (self.future_bank, phase.SelectedE4PhaseBank)):
            _exact(value, kind)
        validate_sha256(self.instrument_sha256)
        require_sorted_unique_ids(self.provenances, attribute="object_id", field_name="actual producing numerical profiles")
        require_sorted_unique_ids(self.templates, attribute="artifact_id", field_name="actual complete instrument templates")
        require_sorted_unique_ids(self.controls, attribute="root_id", field_name="complete TRAIN control census")
        require_sorted_unique_strings(self.future_group_ids, field_name="separately assigned future groups", allow_empty=False)
        if (not self.controls or not self.templates or not self.provenances
                or any(type(value) is not MatrixFiniteDtRootControl for value in self.controls)
                or self.training_effective_seeds != tuple(sorted(set(self.training_effective_seeds)))
                or not self.training_effective_seeds
                or any(type(value) is not int or value < 0 for value in self.training_effective_seeds)
                or type(self.reserved_future_effective_seeds) is not tuple
                or not self.reserved_future_effective_seeds
                or self.reserved_future_effective_seeds != tuple(sorted(set(self.reserved_future_effective_seeds)))
                or any(type(value) is not int or value < 0 for value in self.reserved_future_effective_seeds)
                or set(self.training_effective_seeds).intersection(self.reserved_future_effective_seeds)
                or len({value.group_id for value in self.controls}) != len(self.controls)
                or {value.group_id for value in self.controls}.intersection(self.future_group_ids)
                or type(self.cutoff) is not InformationCutoff
                or self.prerequisite_outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or self.prerequisite_visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or self.standing != STANDING):
            raise ValueError("finite-dt certificate changes original exposure, units or its instrument-only scope")
        for value in self.controls:
            value.__post_init__()
        self.cutoff.__post_init__()

    @property
    def identity(self):
        return pin(self)

    @property
    def instrument_checks_pass(self):
        return (all(value.prefix_controls_pass and not value.frame_controls_violated
                and (value.causal_disposition != "AVAILABLE" or value.frame_controls_pass) for value in self.controls)
            and any(value.response_disposition == "COMPLETED" for value in self.controls)
            and all(value.response_controls_pass for value in self.controls if value.response_disposition == "COMPLETED"))

    @property
    def original_evidence_links(self):
        values = {self.locator.packet, self.locator.execution_plan, self.specification, self.request, self.acquisition}
        for value in self.controls:
            values.update((value.source, value.prefix, value.numerical, value.causal_prefix, value.frame_assessment, value.physical_forecast, value.responses, value.score, *value.receipts))
        return tuple(sorted(values, key=lambda value: value.object_id))


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-source-scope"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    reservation: ObjectIdentity
    original_future_reservation: ObjectIdentity
    assay: ObjectIdentity
    numerical: ObjectIdentity
    certificate: ObjectIdentity
    cutoff: InformationCutoff
    group_ids: tuple[str, ...]
    profile: SourcePipelineProfile
    pipeline_receipt: SourcePipelineQualificationReceipt
    evidence_profile: EvidenceProfileSelection
    publication: ObjectIdentity
    recovery: ObjectIdentity
    resource_budget: ResourceBudget
    standing: str = STANDING

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
        validate_stable_id(self.record_id)
        for value, kind in ((self.programme, phase.SelectedE4PhaseProgramme), (self.bank, phase.SelectedE4PhaseBank),
                (self.reservation, scheduled.ScheduledReservation), (self.original_future_reservation, scheduled.ScheduledReservation),
                (self.assay, ScheduledResponseSelection), (self.numerical, MatrixParameterNumericalDesign),
                (self.certificate, MatrixFiniteDtInstrumentCertificate)):
            _exact(value, kind)
        for value, kind in ((self.cutoff, InformationCutoff), (self.profile, SourcePipelineProfile),
                (self.pipeline_receipt, SourcePipelineQualificationReceipt),
                (self.evidence_profile, EvidenceProfileSelection), (self.resource_budget, ResourceBudget)):
            if type(value) is not kind:
                raise TypeError("finite-dt source requires exact configured original source owners")
            value.__post_init__()
        require_sorted_unique_strings(self.group_ids, field_name="complete future source groups", allow_empty=False)
        if (self.standing != STANDING or self.profile.outcome_access is not BLIND
                or self.profile.visibility_ceiling is not PROSPECTIVE
                or self.pipeline_receipt.profile != pin(self.profile, "profile_id")
                or self.pipeline_receipt.outcome_access is not BLIND
                or self.pipeline_receipt.visibility_ceiling is not PROSPECTIVE
                or self.profile.observation_operator != self.assay
                or self.profile.causal_cutoff != pin(self.cutoff, "cutoff_id")
                or self.numerical.object_id not in self.profile.numerical_view_ids):
            raise ValueError("finite-dt source scope changes source/assay/cutoff/access or makes a broader claim")

    @property
    def identity(self):
        return pin(self)

    @property
    def operands(self):
        return tuple(sorted((self.identity, self.programme, self.bank, self.reservation, self.original_future_reservation,
            self.assay, self.numerical, self.certificate, pin(self.cutoff, "cutoff_id")), key=lambda value: value.object_id))


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtGateConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-gate-config"
    config_id: str
    scope: ObjectIdentity
    gate_kind: ScientificSourceGateKind
    group_ids: tuple[str, ...]
    resource_budget: ResourceBudget

    def __post_init__(self):
        validate_stable_id(self.config_id)
        _exact(self.scope, MatrixFiniteDtSourceScope)
        if self.gate_kind not in GATES or type(self.resource_budget) is not ResourceBudget:
            raise ValueError("finite-dt source gate changes its installed kind or explicit resources")
        self.resource_budget.__post_init__()
        require_sorted_unique_strings(self.group_ids, field_name="complete gate units", allow_empty=False)

    @property
    def identity(self):
        return pin(self, "config_id")



def gate_configs(scope):
    scope.__post_init__()
    if type(scope) is not MatrixFiniteDtSourceScope:
        raise TypeError("finite-dt source requires its exact source scope")
    return tuple(MatrixFiniteDtGateConfig("config." + scope.record_id + "." + kind.value.lower(),
        scope.identity, kind, scope.group_ids, scope.resource_budget) for kind in GATES)


def qualification_specification(scope):
    from .matrix_finite_dt_source_bindings import gate_declaration
    configs = {value.gate_kind: value for value in gate_configs(scope)}
    gates = []
    for kind in ScientificSourceGateKind:
        required = kind in GATES
        config = configs.get(kind)
        method = (MetatheoryMethodSelection("method." + scope.record_id + "." + kind.value.lower(),
            gate_declaration(kind).capability_key, "1.0.0", config.identity,
            gate_declaration(kind).manifest().implementation_sha256) if required else None)
        gates.append(ScientificSourceGateSpec("gate." + scope.record_id + "." + kind.value.lower(), kind,
            MetatheoryApplicability.REQUIRED if required else MetatheoryApplicability.NOT_APPLICABLE,
            method, scope.operands if required else (), "unit.actual-whole-independent-matched-group",
            "operation.finite-dt-declared-measurement-instrument", ("falsifier.exact-native-independent-control-census",) if required else (),
            () if required else ("NONSTATIONARY_PREPARATION_NO_STATIONARITY_OR_SAMPLING_CLAIM",)))
    return ScientificSourceQualificationSpec("specification." + scope.record_id,
        pin(scope.profile, "profile_id"), pin(scope.pipeline_receipt, "receipt_id"),
        pin(scope.evidence_profile, "selection_id"), scope.bank, scope.pipeline_receipt.output_artifact,
        tuple(sorted(gates, key=lambda value: value.gate_id)), scope.group_ids, len(scope.group_ids),
        ScientificSourceInvalidUnitPolicy.UNEVALUABLE, scope.reservation, scope.assay, scope.numerical,
        pin(scope.cutoff, "cutoff_id"), EvidenceCeiling.MEASUREMENT,
        MetatheoryEvidenceCeiling.CONTRACT_CONFORMANCE, BLIND, PROSPECTIVE)



def require_source_stream_separation(certificate, bank, original_reservation, group_ids):
    """Reject consumed or pre-TRAIN-reserved effective streams before acquisition.

    The owning API reconstructs the certificate's reserved union from exact
    original rootnoise plus authenticated four-phase response selections.
    Historical requests without panel commitments retain only their actual
    rootnoise; this field never establishes reservation timeliness or freshness.
    """
    if (type(certificate) is not MatrixFiniteDtInstrumentCertificate
            or type(bank) is not phase.SelectedE4PhaseBank or type(original_reservation) is not scheduled.ScheduledReservation):
        raise TypeError("finite-dt source separation requires exact original certificate/bank/reservation owners")
    certificate.__post_init__()
    training_groups = {value.group_id for value in certificate.controls}
    original = original_reservation.allocation
    prior_groups = {value.root.independent_group_id for value in original.roots}
    prior_root_seeds = {stream.effective_seed for value in original.roots for stream in value.streams}
    reserved = set(certificate.reserved_future_effective_seeds)
    if not prior_root_seeds <= reserved:
        raise ValueError("finite-dt certificate drops actual original future rootnoise")
    all_seeds = {stream.effective_seed for root in bank.reservation.allocation.roots for stream in root.streams}
    all_seeds.update(stream.effective_seed for _, panels in bank.response_selection.panels
        for panel in panels for stream in panel.streams)
    if ((training_groups | prior_groups).intersection(group_ids)
            or all_seeds.intersection(set(certificate.training_effective_seeds) | reserved)):
        raise ValueError("finite-dt source reuses a TRAIN or reserved original future unit or effective stream")


def require_checked_implementation(certificate, bank):
    """Require the exact numerical implementation actually checked by TRAIN."""
    if {value.identity for value in bank.provenances} != set(certificate.provenances):
        raise ValueError("finite-dt source changes the actually checked numerical implementation/profile")


def validate_gate_operands(config, scope, records):
    """Pure scientific joins. The API must additionally authenticate certificate custody."""
    if type(scope) is not MatrixFiniteDtSourceScope or type(config) is not MatrixFiniteDtGateConfig:
        raise TypeError("finite-dt source requires its exact gate and instrument scope")
    if set(records) != {"scope", "programme", "bank", "reservation", "original-reservation",
            "assay", "numerical", "cutoff", "certificate"}:
        raise ValueError("finite-dt source changes its complete exact scientific operand census")
    config.__post_init__()
    scope.__post_init__()
    if config.scope != scope.identity or config not in gate_configs(scope):
        raise ValueError("finite-dt gate changes its complete configured scope")
    programme, bank, certificate = records["programme"], records["bank"], records["certificate"]
    phase.validate_selected_phase_bank(programme, bank)
    certificate.__post_init__()
    if (programme.identity != scope.programme or bank.identity != scope.bank
            or programme.group_ids != scope.group_ids or scheduled.identity(bank.reservation) != scope.reservation
            or records["reservation"] != bank.reservation
            or scheduled.identity(records["original-reservation"]) != scope.original_future_reservation
            or records["assay"] != bank.response_selection or bank.response_selection.identity != scope.assay
            or scheduled.identity(records["numerical"]) != scope.numerical
            or scheduled.identity(bank.specification.selection.numerical_design) != scope.numerical
            or records["cutoff"] != scope.cutoff or certificate.identity != scope.certificate
            or certificate.future_bank != scope.bank or certificate.future_group_ids != scope.group_ids
            or certificate.original_future_reservation != scope.original_future_reservation
            or certificate.numerical != scope.numerical or certificate.cutoff != scope.cutoff):
        raise ValueError("finite-dt source substitutes actual source/preparation/instrument/complete-unit/cutoff operands")
    actual = {scope.identity, programme.identity, bank.identity, scheduled.identity(records["reservation"]),
        scheduled.identity(records["original-reservation"]), records["assay"].identity,
        scheduled.identity(records["numerical"]), certificate.identity, pin(scope.cutoff, "cutoff_id")}
    if actual != set(scope.operands):
        raise ValueError("finite-dt source changes its complete exact scientific operand census")
    require_e4_reserved_physical_exclusion(bank.reservation.allocation.coordinates, records["original-reservation"])
    require_source_stream_separation(certificate, bank, records["original-reservation"], scope.group_ids)
    require_checked_implementation(certificate, bank)
    expected_templates = {template_bytes(value.templates.array_artifact) for value in bank.response_selection.protocols}
    if (expected_templates != {template_bytes(value) for value in certificate.templates}
            or {instrument_signature(value) for value in bank.response_selection.protocols} != {certificate.instrument_sha256}
            or {scheduled.identity(value.public_source.policy.factor_numerical_design)
                for value in bank.response_selection.protocols} != {certificate.factor_numerical}):
        raise ValueError("finite-dt source changes the actually checked instrument, numeric tolerances or template bytes")
    measurement = certificate.measurement
    for protocol in bank.response_selection.protocols:
        public = protocol.public_source
        if (protocol.horizon_steps != measurement.horizons or protocol.receiver_count != measurement.receiver_count
                or protocol.criterion != certificate.criterion
                or public.coordinate.primary_view.timestep != measurement.primary_timestep
                or public.coordinate.fine_view.timestep != measurement.fine_timestep
                or public.policy.cutoff_tick != measurement.origin_tick
                or scope.cutoff.clock_id != public.root.clock_id
                or not scope.cutoff.phase.precedes_or_equals(programme.cases[0].information_cutoff.phase)
                or scope.cutoff.coordinate is not None and scope.cutoff.coordinate >
                    public.coordinate.physical_time(public.policy.cutoff_tick)):
            raise ValueError("finite-dt source changes the checked assay, paired timestep or pre-outcome causal contract")
    if len(bank.sources) != len(programme.cases) or len(programme.cases) != len(scope.group_ids) * bank.design.cases_per_group:
        raise ValueError("finite-dt source omits a nested case or independent assigned group")
    spec = qualification_specification(scope)
    gate, = (value for value in spec.gates if value.gate_kind is config.gate_kind)
    supported = config.gate_kind is not ScientificSourceGateKind.NUMERICAL_OR_INSTRUMENT_VALIDITY or certificate.instrument_checks_pass
    metrics = (NamedDecimal("assigned-future-groups", Decimal(len(scope.group_ids)), "whole-independent-groups"),)
    reasons = () if supported else ("ACTUAL_NATIVE_PREFIX_OR_RESPONSE_INSTRUMENT_CHECKS_NOT_ESTABLISHED",)
    return ScientificSourceGateEvidence("evidence." + config.config_id, pin(spec, "spec_id"), pin(gate, "gate_id"),
        scope.operands, gate.evaluator, scope.group_ids, scope.group_ids if supported else (),
        () if supported else scope.group_ids, metrics, scope.publication, scope.recovery,
        (certificate.identity,),
        MetatheoryCellDisposition.SUPPORTED if supported else MetatheoryCellDisposition.UNEVALUABLE, reasons)
