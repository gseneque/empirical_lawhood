# SPDX-License-Identifier: MPL-2.0
"""Closed SDK release source acts; NEVER a production qualification provider.

The six gates test explicitly disclosed structural source premises. Their real
new issue/receipts prove software lifecycle conformance only. They do not prove
freshness, numerical accuracy, sampling, transfer or scientific eligibility.
No declaration in this file is installed in the production aggregate.
"""

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from functools import partial
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.adapters.methods import matrix_source_evidence as shared
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as phase
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import MatrixParameterNumericalDesign
from empirical_lawhood.adapters.methods.backbone_structural_transport import source_free_property_transport_source_input_parts as template
from empirical_lawhood.kernel.authority import AuthorityAction, ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id, require_sorted_unique_ids
from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
from empirical_lawhood.planning.evidence_profiles import EvidenceProfileSelection
from empirical_lawhood.planning.metatheory import MetatheoryApplicability, MetatheoryCellDisposition, MetatheoryEvidenceCeiling, MetatheoryMethodSelection
from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceGateKind, ScientificSourceGateSpec, ScientificSourceGateEvidence, ScientificSourceQualificationSpec, ScientificSourceInvalidUnitPolicy
from empirical_lawhood.planning.source_pipelines import SourcePipelineArtifactProfile, SourcePipelineProfile, SourcePipelineQualificationReceipt, SourcePipelineEdgeAccounting
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission, CapabilityRegistry
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload
from empirical_lawhood.runtime.plans import ScientificStage, OutputTemplate
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from tests.matrix_selected_e4_public_fixture import DISCLOSURE, ROOT, publication, task_budget, original_preparation, _source_admissions

KEY = "matrix-release-selected-e4-source"
GATES = tuple(value for value in ScientificSourceGateKind if value is not ScientificSourceGateKind.STATIONARITY_OR_RECURRENCE)
BLIND, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


def pin(value, field="record_id"):
    return ObjectIdentity.from_record(getattr(value, field), value)


def implementation_sha():
    return sha256(Path(__file__).read_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class ReleaseSourceRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-source-row"
    root_id: str
    group_id: str
    source: ObjectIdentity
    invalid_disposition: str
    requested_action_status: str
    receiver_status: str

    def __post_init__(self):
        validate_stable_id(self.root_id)
        validate_stable_id(self.group_id)
        if (self.invalid_disposition != "DECLARED_SOURCE_NOT_YET_OBSERVED"
                or self.requested_action_status != "NO_NATIVE_ACTION_REQUESTED"
                or self.receiver_status != "NO_NATIVE_RECEIVER_OBSERVED"):
            raise ValueError("source metadata cannot assert a future valid scientific outcome")


@dataclass(frozen=True, slots=True)
class ReleaseSourceRows(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-source-rows"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    rows: tuple[ReleaseSourceRow, ...]
    scope: str = DISCLOSURE

    def __post_init__(self):
        validate_stable_id(self.record_id)
        require_sorted_unique_ids(self.rows, attribute="root_id", field_name="complete source metadata rows")
        if not self.rows or self.scope != DISCLOSURE:
            raise ValueError("release source projection cannot drop its disclosed scope")

    @classmethod
    def from_bank(cls, programme, bank, record_id):
        phase.validate_selected_phase_bank(programme, bank)
        return cls(record_id, programme.identity, bank.identity,
            tuple(ReleaseSourceRow(value.root_id, value.independent_group_id, value.source,
                "DECLARED_SOURCE_NOT_YET_OBSERVED", "NO_NATIVE_ACTION_REQUESTED", "NO_NATIVE_RECEIVER_OBSERVED")
                for value in programme.cases))


@dataclass(frozen=True, slots=True)
class ReleaseSourceAct(CanonicalRecord):
    """Actual operation metadata; no asserted qualification/evidence rung."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-source-act"
    record_id: str
    operation: str
    operands: tuple[ObjectIdentity, ...]
    group_ids: tuple[str, ...]
    root_ids: tuple[str, ...]
    implementation_sha256: str
    scope: str = DISCLOSURE


@dataclass(frozen=True, slots=True)
class ReleaseGateScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-source-gate-scope"
    record_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    reservation: ObjectIdentity
    assay: ObjectIdentity
    numerical: ObjectIdentity
    cutoff: InformationCutoff
    group_ids: tuple[str, ...]
    profile: SourcePipelineProfile
    pipeline_receipt: SourcePipelineQualificationReceipt
    evidence_profile: EvidenceProfileSelection
    publication: ObjectIdentity
    recovery: ObjectIdentity
    witness: ObjectIdentity
    scope: str = DISCLOSURE

    @property
    def identity(self):
        return pin(self)

    @property
    def operands(self):
        return tuple(sorted((self.programme, self.bank, self.reservation, self.assay, self.numerical,
            ObjectIdentity.from_record(self.cutoff.cutoff_id, self.cutoff)), key=lambda value: value.object_id))


@dataclass(frozen=True, slots=True)
class ReleaseGateConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-source-gate-config"
    config_id: str
    common: ReleaseGateScope
    gate_kind: ScientificSourceGateKind

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if type(self.common) is not ReleaseGateScope or self.gate_kind not in GATES or self.common.scope != DISCLOSURE:
            raise ValueError("only closed exposed release source gates can use this test config")

    @property
    def identity(self):
        return pin(self, "config_id")


def gate_configs(scope):
    return tuple(ReleaseGateConfig("config." + scope.record_id + "." + kind.value.lower(), scope, kind) for kind in GATES)


def gate_specification(scope):
    configs = {value.gate_kind: value for value in gate_configs(scope)}
    gates = []
    for kind in ScientificSourceGateKind:
        required = kind in GATES
        config = configs.get(kind)
        method = None if not required else MetatheoryMethodSelection("method." + kind.value.lower(),
            KEY + "." + kind.value.lower(), "1.0.0", config.identity, gate_declaration(kind).manifest().implementation_sha256)
        gates.append(ScientificSourceGateSpec("gate." + kind.value.lower(), kind,
            MetatheoryApplicability.REQUIRED if required else MetatheoryApplicability.NOT_APPLICABLE,
            method, scope.operands if required else (), "unit.selected-e4.whole-group",
            "operation.selected-e4.release-source-structural-conformance", ("complete-original-source-scope",) if required else (),
            () if required else ("FINITE_SOURCE_METADATA_CANNOT_ESTABLISH_STATIONARITY_OR_SAMPLING",)))
    return ScientificSourceQualificationSpec("specification." + scope.record_id,
        shared.reference(scope.profile, "profile_id"), shared.reference(scope.pipeline_receipt, "receipt_id"),
        shared.reference(scope.evidence_profile, "selection_id"), scope.bank, scope.pipeline_receipt.output_artifact,
        tuple(sorted(gates, key=lambda value: value.gate_id)), scope.group_ids, len(scope.group_ids),
        ScientificSourceInvalidUnitPolicy.UNEVALUABLE, scope.reservation, scope.assay, scope.numerical,
        ObjectIdentity.from_record(scope.cutoff.cutoff_id, scope.cutoff), EvidenceCeiling.MEASUREMENT,
        MetatheoryEvidenceCeiling.PROSPECTIVE_TARGET_LOCAL, BLIND, PROSPECTIVE)


def gate_product(config):
    spec = gate_specification(config.common)
    gate, = (value for value in spec.gates if value.gate_kind is config.gate_kind)
    return ScientificSourceGateEvidence("evidence." + config.config_id, shared.reference(spec, "spec_id"),
        shared.reference(gate, "gate_id"), config.common.operands, gate.evaluator,
        config.common.group_ids, config.common.group_ids, (), (), config.common.publication, config.common.recovery,
        (config.common.witness,), MetatheoryCellDisposition.SUPPORTED, ())


def validate_gate_inputs(config, records):
    common = config.common
    programme, bank = records["programme"], records["bank"]
    phase.validate_selected_phase_bank(programme, bank)
    index = bank.source_index()
    numerical = {old.identity(bank.source(value.root_id, index=index).numerical_design) for value in bank.sources}
    if (programme.identity != common.programme or bank.identity != common.bank or programme.group_ids != common.group_ids
            or old.identity(records["reservation"]) != common.reservation or records["reservation"] != bank.reservation
            or records["assay"] != bank.response_selection or common.assay != bank.response_selection.identity
            or numerical != {common.numerical} or old.identity(records["numerical"]) != common.numerical
            or records["cutoff"] != common.cutoff or any(value.information_cutoff.clock_id != common.cutoff.clock_id
                or not common.cutoff.phase.precedes_or_equals(value.information_cutoff.phase)
                or (common.cutoff.coordinate is not None and value.information_cutoff.coordinate is not None
                    and common.cutoff.coordinate > value.information_cutoff.coordinate) for value in programme.cases)
            or len(bank.sources) != len(programme.cases)
            or any(source.coordinate.physical_time(source.policy.cutoff_tick) != value.information_cutoff.coordinate
                for value in programme.cases for source in (bank.source(value.root_id, index=index),))):
        raise ValueError("release gate refuses incomplete, substituted or causally different whole-source operands")
    if set(common.operands) != {programme.identity, bank.identity, old.identity(records["reservation"]),
            records["assay"].identity, old.identity(records["numerical"]), ObjectIdentity.from_record(records["cutoff"].cutoff_id, records["cutoff"])}:
        raise ValueError("release source gate changes its closed exact scientific operand census")
    return gate_product(config)


class ReleaseGateWorker:
    def __init__(self, kind):
        self.kind, self.manifest = kind, gate_declaration(kind).manifest()

    def execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read
        if type(context) is not TaskContext:
            raise PermissionError("release gate needs actual issued prepared context")
        try:
            context.__post_init__()
            prepared = context.prepared_invocation
            if (prepared is None or prepared.manifest != self.manifest or prepared.native_effect
                    or context.outcome_access is not BLIND or context.permissions != self.manifest.permissions
                    or context.dependency_receipts or not self.manifest.resource_ceiling.contains(context.resource_budget)
                    or prepared.execution_task_record.stage is not ScientificStage.QUALIFY
                    or any(value.outcome_access is not BLIND or value.visibility_ceiling is not PROSPECTIVE
                        for value in prepared.execution_task_record.outputs)):
                raise PermissionError("release gate cannot replace the actual issue/input/worker contract")
            ports = {value.artifact_id: value for value in context.input_ports}
            contracts = {value.artifact_id: value for value in prepared.inputs}
            config_ports = tuple(value for value in context.input_ports if value.payload_schema == ReleaseGateConfig.SCHEMA)
            config_port, = config_ports
            config_contract, = (value for value in prepared.inputs if value.artifact_id == config_port.artifact_id)
            config = _read(config_port, config_contract, ReleaseGateConfig)
            if config.gate_kind is not self.kind or config.fingerprint() != context.config.content_sha256:
                raise PermissionError("release gate substitutes frozen configuration")
            kinds = input_kinds()
            records = {}
            for name, kind in kinds.items():
                candidates = tuple(value for value in context.input_ports if value.payload_schema == kind.SCHEMA)
                port, = candidates
                contract, = (value for value in prepared.inputs if value.artifact_id == port.artifact_id)
                records[name] = _read(port, contract, kind)
            if len(ports) != len(kinds) + 1 or len(contracts) != len(ports):
                raise PermissionError("release gate has extra or absent physical inputs")
            product = validate_gate_inputs(config, records)
            output, = context.output_ports
            if output.output_id != context.task_id + ".product" or output.payload_schema != product.SCHEMA:
                raise PermissionError("release gate changes exact original scientific output")
            return RunnerResult((TaskOutputPayload(output.output_id, product.canonical_bytes()),),
                (ReceiptCheck("release-source-structural-operands-replayed", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def input_kinds():
    return {"programme": phase.SelectedE4PhaseProgramme, "bank": phase.SelectedE4PhaseBank,
        "reservation": old.ScheduledReservation, "assay": ScheduledResponseSelection,
        "numerical": MatrixParameterNumericalDesign, "cutoff": InformationCutoff}


def gate_declaration(kind):
    from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
    return RecursiveOperationDeclaration(KEY + "." + kind.value.lower(), "1.0.0",
        "exposed-release-source-gate-v1." + implementation_sha(), CapabilityKind.NUMERICAL_QUALIFIER,
        ReleaseGateConfig, ScientificStage.QUALIFY,
        tuple(RecursivePortContract(name, value.SCHEMA, "application/json", None)
            for name, value in sorted(input_kinds().items())),
        (OutputTemplate("product", ScientificSourceGateEvidence.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.NON_PROMOTABLE, BLIND, PROSPECTIVE, ResourceBudget(1, None, 0, None, None, None),
        ("release-source-structural-operands-replayed",), partial(ReleaseGateWorker, kind),
        {value.SCHEMA: value for value in (*input_kinds().values(), ReleaseGateConfig, ScientificSourceGateEvidence)},
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,))


@dataclass(frozen=True, slots=True)
class ReleaseSourceCloseoutConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/selected-e4-source-closeout-config"
    config_id: str
    products: tuple[ObjectIdentity, ...]
    scope: str = DISCLOSURE

    def __post_init__(self):
        validate_stable_id(self.config_id)
        require_sorted_unique_ids(self.products, attribute="object_id", field_name="source closeout products")
        if len(self.products) != len(GATES) + 2 or self.scope != DISCLOSURE:
            raise ValueError("source closeout requires all eight actual TEST products without scientific promotion")


class ReleaseSourceCloseoutWorker:
    """Retain an explicit UNEVALUABLE scientific terminal for metadata-only work."""
    def __init__(self):
        self.manifest = source_closeout_declaration().manifest()

    def execute(self, context):
        from empirical_lawhood.adapters.methods.matrix_factor_response.protected_prefix_workers import _read
        from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord, AdjudicationEvaluability
        from empirical_lawhood.kernel.status import ScientificStatus, AdmissionStatus
        from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationResult
        try:
            context.__post_init__()
            prepared, adjudication = context.prepared_invocation, context.scientific_adjudication_context
            if (prepared is None or prepared.manifest != self.manifest or prepared.native_effect
                    or adjudication is None or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                    or len(context.dependency_receipt_ids) != len(GATES) + 2):
                raise PermissionError("source TEST closeout needs all actual issued PURE producer dependencies")
            contracts = {value.artifact_id: value for value in prepared.inputs}
            config_port, = (value for value in context.input_ports if value.payload_schema == ReleaseSourceCloseoutConfig.SCHEMA)
            config = _read(config_port, contracts[config_port.artifact_id], ReleaseSourceCloseoutConfig)
            if config.fingerprint() != context.config.content_sha256:
                raise PermissionError("source closeout changes its frozen TEST configuration")
            kinds = {kind.SCHEMA: (kind, field) for kind, field in (
                (ScientificSourceGateEvidence, "evidence_id"), (SourcePipelineQualificationReceipt, "receipt_id"),
                (ScientificSourceQualificationResult, "result_id"))}
            actual = []
            for port in context.input_ports:
                if port is config_port:
                    continue
                kind, field = kinds[port.payload_schema]
                record = _read(port, contracts[port.artifact_id], kind)
                actual.append(ObjectIdentity.from_record(getattr(record, field), record))
            if tuple(sorted(actual, key=lambda value: value.object_id)) != config.products:
                raise PermissionError("source closeout changes an actual independent producer product")
            output, = context.output_ports
            record = ScientificAdjudicationRecord("adjudication." + context.run_id + "." + context.task_id,
                context.run_id, context.task_id, adjudication.execution_plan, tuple(sorted(context.input_materialization_ids)),
                (output.logical_artifact_id,), context.dependency_receipt_ids, adjudication.evidence_world_id,
                adjudication.evidence_world_kind, adjudication.relation, adjudication.independent_unit_id,
                adjudication.information_cutoffs, adjudication.visibility_ceiling, adjudication.outcome_access,
                AdjudicationEvaluability.UNEVALUABLE, ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE,
                ("EXPOSED_SOURCE_METADATA_ONLY", "SCIENTIFIC_QUALIFICATION_NOT_ESTABLISHED"))
            return RunnerResult((TaskOutputPayload(output.output_id, record.canonical_bytes()),),
                (ReceiptCheck("source-test-products-authenticated-science-unevaluable", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def source_closeout_declaration():
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    from empirical_lawhood.planning.scientific_source_qualification import ScientificSourceQualificationResult
    from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
    ports = tuple((kind.value.lower(), ScientificSourceGateEvidence.SCHEMA) for kind in GATES) + (
        ("pipeline", SourcePipelineQualificationReceipt.SCHEMA), ("qualification", ScientificSourceQualificationResult.SCHEMA))
    return RecursiveOperationDeclaration(KEY + ".adjudicate", "1.0.0", "exposed-source-closeout-v1." + implementation_sha(),
        CapabilityKind.REPORTER, ReleaseSourceCloseoutConfig, ScientificStage.REPORT,
        tuple(RecursivePortContract(name, schema, "application/json", None) for name, schema in sorted(ports)),
        (OutputTemplate("product", ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
        (CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS),
        EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        ResourceBudget(1, None, 0, None, None, None),
        ("source-test-products-authenticated-science-unevaluable",), ReleaseSourceCloseoutWorker,
        {kind.SCHEMA: kind for kind in (ReleaseSourceCloseoutConfig, ScientificAdjudicationRecord,
            ScientificSourceGateEvidence, SourcePipelineQualificationReceipt, ScientificSourceQualificationResult)},
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        scientific_hooks=RecursiveScientificHooks(adjudication_output_id="product"))


def _publish(writer, record, publications, field="record_id"):
    reference = pin(record, field)
    stored = publication(writer, record, "source." + reference.object_id)
    publications[reference] = stored
    return reference


def _raw_artifact(writer, *, name, raw, relative):
    from empirical_lawhood.kernel.references import ArtifactIdentity
    stored = writer.write(ArtifactWriteRequest(name, relative,
        "empirical-lawhood/source/checksummed-uninterpreted-public-bytes",
        ArtifactProfile.RAW_SOURCE_BYTES, "text/plain", "publication." + name,
        str(Path(relative).parent), raw, PROSPECTIVE, (), BLIND))
    identity = ArtifactIdentity(name, "disclosed-release-source-runtime-bytes", stored.logical.payload_schema,
        sha256(raw).hexdigest(), stored.logical.media_type, len(raw))
    return identity, stored


def _transformation_manifest(*, writer, selected, namespace, source, output, rows, cutoff, transform,
        transform_config, source_scope, destination_scope, control_scope, envelope, publications):
    """Use the real manifest grammar; no issue-shaped or fake-schema record."""
    from empirical_lawhood.planning import dataset_manifests as dm
    from empirical_lawhood.planning.datasets import DatasetMaterialization, DatasetMaterializationClass, DatasetEvidenceClass, DatasetSelectorRef, DatasetSelectorKind, CustodyState
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.runtime.datasets import DatasetCapabilityLimits, DatasetEvidenceVerifierRegistration
    selector = DatasetSelectorRef("selector." + namespace, DatasetSelectorKind.COMPLETE_RELEASE, rows.SCHEMA, rows.fingerprint(), True)
    materialization = DatasetMaterialization("dataset-source." + namespace, "release." + namespace,
        DatasetMaterializationClass.METADATA_OBSERVATION, DatasetEvidenceClass.METADATA_ONLY, BLIND,
        source.materialization.storage_root_id, source.materialization.relative_path, selector,
        source.logical.content_sha256, source.materialization.size_bytes, 1, "application/json", "selected-e4-source-roster",
        None, CustodyState.UNVERIFIED, None, None, None, None, (), None, None,
        ("NEW_RELEASE_METADATA_ARTIFACT_VERIFIED_SEPARATELY_BY_GUARDED_PIPELINE",))
    _publish(writer, materialization, publications, "materialization_id")
    limits = DatasetCapabilityLimits(len(rows.canonical_bytes()), selected.output_bytes_per_task, len(rows.rows), 2, 0)
    inspector = replace(transform, capability_key="release-source-inspector." + namespace, kind=CapabilityKind.SOURCE,
        output_schema_ids=("empirical-lawhood/runtime/dataset-inspection",))
    verifier_capability = replace(inspector, capability_key="release-source-verifier." + namespace,
        permissions=(CapabilityPermission.READ_EXTERNAL_ARTIFACTS,), output_schema_ids=("empirical-lawhood/runtime/dataset-evidence-verification",))
    verifier = DatasetEvidenceVerifierRegistration("release-source-verifier." + namespace, verifier_capability, (rows.SCHEMA,), limits)
    config_ref = CapabilityConfigRef("config-reference." + namespace, transform_config.SCHEMA,
        sha256(transform_config.SCHEMA.encode()).hexdigest(), transform_config.fingerprint(), transform_config.record_id)
    runtime, _ = _raw_artifact(writer, name="runtime." + namespace, raw=Path(__file__).read_bytes(),
        relative="sources/" + namespace + "/source-runtime.py")
    environment, _ = _raw_artifact(writer, name="environment." + namespace,
        raw=(Path(__file__).resolve().parents[1] / "uv.lock").read_bytes(),
        relative="sources/" + namespace + "/uv.lock")
    bindings = []
    records = ((dm.DatasetCapabilityKind.INSPECTOR, inspector, "capability_key"),
        (dm.DatasetCapabilityKind.EVIDENCE_VERIFIER, verifier, "registry_id"),
        (dm.DatasetCapabilityKind.TRANSFORM, transform, "capability_key"),
        (dm.DatasetCapabilityKind.CONFIG, config_ref, "config_id"),
        (dm.DatasetCapabilityKind.RUNTIME, runtime, "artifact_id"),
        (dm.DatasetCapabilityKind.ENVIRONMENT, environment, "artifact_id"))
    for kind, record, field in records:
        identifier = getattr(record, field)
        reference = _publish(writer, record, publications, field)
        bindings.append(dm.DatasetCapabilityBinding("binding." + namespace + "." + kind.value.lower(), kind, identifier, reference))
    fields = tuple(dm.DatasetFieldContract(name, {"physical-unit": "group_id", "invalid-disposition": "invalid_disposition", "root": "root_id"}[name], index, dm.DatasetFieldDataType.STRING,
        dm.DatasetFieldRole.INDEPENDENT_UNIT if name == "physical-unit" else dm.DatasetFieldRole.VALIDITY
            if name == "invalid-disposition" else dm.DatasetFieldRole.NESTED_OBSERVATION,
        None, None, None, CausalPhase.PREPARATION, BLIND, PROSPECTIVE, False)
        for index, name in enumerate(("physical-unit", "invalid-disposition", "root")))
    fields += (dm.DatasetFieldContract("requested-action-status", "requested_action_status", 3, dm.DatasetFieldDataType.STRING,
        dm.DatasetFieldRole.REQUESTED_ACTION, "1", "declared-metadata-status", cutoff.clock_id, CausalPhase.ACTION_REQUESTED,
        BLIND, PROSPECTIVE, False),
        dm.DatasetFieldContract("receiver-status", "receiver_status", 4, dm.DatasetFieldDataType.STRING,
        dm.DatasetFieldRole.RECEIVER, "1", "declared-metadata-status", cutoff.clock_id, CausalPhase.RECEIVER,
        BLIND, PROSPECTIVE, False))
    parent = pin(materialization, "materialization_id")
    output_contract = dm.DatasetOutputContract("output." + namespace, "dataset-output." + namespace,
        dm.DatasetOutputRole.CANONICAL_SOURCE, output.materialization.relative_path, rows.SCHEMA,
        "application/json", "selected-e4-source-roster", tuple(sorted(fields, key=lambda value: value.field_id)), (parent.object_id,),
        output.logical.content_sha256, len(rows.canonical_bytes()), len(rows.canonical_bytes()), 1, len(rows.rows), len(rows.rows),
        BLIND, PROSPECTIVE)
    manifest = dm.DatasetTransformationManifest("transformation." + namespace, "release." + namespace,
        (dm.DatasetTransformInput("input." + namespace, parent, source_scope, selector, None, None, ()),),
        destination_scope, control_scope, tuple(sorted(bindings, key=lambda value: value.binding_id)), (output_contract,), (),
        dm.DatasetSplitContract("split." + namespace, "release.whole-group.fixed-partition",
            ("physical-unit",), ("root",), ("declared",), (), BLIND, True),
        dm.DatasetCausalContract("causal." + namespace, cutoff, (), ("requested-action-status",), ("receiver-status",), False, False),
        (dm.DatasetExpectedInvariant("invariant." + namespace, dm.DatasetInvariantKind.PARENT_CLOSED,
            (parent.object_id,), "release.exact-whole-roster-validator", True),),
        envelope, BLIND, PROSPECTIVE, ())
    _publish(writer, manifest, publications, "manifest_id")
    return manifest


def source_pipeline(*, originals, programme, bank, selected, namespace, publications):
    from empirical_lawhood.planning.datasets import DatasetEvidenceClass, DatasetMaterializationClass
    from empirical_lawhood.planning.dataset_authority import (
        DatasetStorageScope, DatasetWorkEnvelope, DatasetFileLimits, DatasetControlLimits,
        DatasetAuthorizationIssuerRegistration, issue_dataset_operation_authorization,
    )
    from empirical_lawhood.runtime.datasets import DatasetCapabilityLimits, DatasetCapabilityRegistry
    from empirical_lawhood.runtime.source_pipelines import compile_source_pipeline, SourcePipelineExecutionEvidence, SourcePipelineValidatorEvidence
    from empirical_lawhood.runtime.sources import SourceResult
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    current_implementation = implementation_binding(ROOT)
    writer = originals.writer
    rows = ReleaseSourceRows.from_bank(programme, bank, "source-rows." + namespace)
    raw = rows.canonical_bytes()
    if len(raw) > min(selected.source_bytes_per_task, selected.output_bytes_per_task):
        raise ValueError("actual complete source metadata exceeds selected source/output reservations")
    # Both payloads are actual bounded publications, preserving every source.
    source = writer.write(ArtifactWriteRequest("source." + namespace, "sources/" + namespace + "/rows.json",
        rows.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "source." + namespace,
        "sources/" + namespace, raw, PROSPECTIVE, (), BLIND))
    output = writer.write(ArtifactWriteRequest("output." + namespace, "derived/" + namespace + "/rows.json",
        rows.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "output." + namespace,
        "derived/" + namespace, raw, PROSPECTIVE, (), BLIND))
    source_manifest = writer.read_manifest(source.materialization.relative_path)
    output_manifest = writer.read_manifest(output.materialization.relative_path)
    writer.verify_manifest(source_manifest)
    writer.verify_manifest(output_manifest)
    reread = read_bounded_bytes(writer.root.resolve(source.materialization.relative_path, for_write=False), maximum_bytes=len(raw))
    if reread != raw or decode_canonical_bytes(reread, ReleaseSourceRows, maximum_bytes=len(raw)) != rows:
        raise PermissionError("source identity transform lost actual original canonical rows")
    if read_bounded_bytes(writer.root.resolve(output.materialization.relative_path, for_write=False), maximum_bytes=len(raw)) != raw:
        raise PermissionError("source identity transform changed output bytes")
    numerical = old.identity(bank.source(bank.sources[0].root_id, index=bank.source_index()).numerical_design)
    cutoff = InformationCutoff("cutoff." + namespace + ".before-source-entry",
        programme.cases[0].information_cutoff.clock_id, CausalPhase.PREPARATION, Decimal(0))
    operands = tuple(sorted((programme.identity, bank.identity, old.identity(bank.reservation), bank.response_selection.identity,
        numerical, ObjectIdentity.from_record(cutoff.cutoff_id, cutoff)), key=lambda value: value.object_id))
    act = ReleaseSourceAct("act." + namespace, "EXACT_CANONICAL_IDENTITY_TRANSFORM_COMPLETE_SOURCE_ROSTER",
        operands, programme.group_ids, tuple(value.root_id for value in programme.cases), implementation_sha())
    validator = ReleaseSourceAct("validator." + namespace, "REPLAY_TYPED_BANK_AND_COMPARE_EVERY_GROUP_ROOT_SOURCE",
        operands, programme.group_ids, tuple(value.root_id for value in programme.cases), implementation_sha())
    recovery = ReleaseSourceAct("recovery." + namespace, "VERIFY_BOTH_PUBLISHED_MANIFESTS_AND_IDENTICAL_CANONICAL_PAYLOADS",
        operands, programme.group_ids, tuple(value.root_id for value in programme.cases), implementation_sha())
    for record in (act, validator, recovery):
        _publish(writer, record, publications)
    budget = replace(task_budget(selected), wall_time_seconds=60)
    profile, adapter, registry, datasets = template._profile(label=namespace)
    transform = replace(registry.capabilities[0], capability_key="release-source-identity." + namespace,
        config_schema=act.SCHEMA, config_schema_sha256=sha256(act.SCHEMA.encode()).hexdigest(),
        input_schema_ids=(rows.SCHEMA,), output_schema_ids=(rows.SCHEMA,),
        implementation_sha256=implementation_sha(), resource_ceiling=budget)
    registration = replace(datasets.transforms[0], capability=transform,
        accepted_media_types=("application/json",), produced_media_types=("application/json",),
        source_format_profile_ids=("selected-e4-source-roster",), destination_format_profile_ids=("selected-e4-source-roster",),
        limits=DatasetCapabilityLimits(selected.source_bytes_per_task, selected.output_bytes_per_task, len(rows.rows), 2, 0))
    registry = CapabilityRegistry("registry." + namespace, (transform,))
    datasets = DatasetCapabilityRegistry("datasets." + namespace, (), (), (registration,), (), (), ())
    edge = replace(profile.transform_edges[0], edge_id="edge." + namespace,
        dataset_transform_registry_id=transform.registry_id,
        selection=replace(profile.transform_edges[0].selection, capability_key=transform.capability_key,
            implementation_sha256=transform.implementation_sha256),
        config=pin(act), domain_schema=rows.SCHEMA, codomain_schema=rows.SCHEMA,
        source_media_type="application/json", destination_media_type="application/json",
        source_format_profile_id="selected-e4-source-roster", destination_format_profile_id="selected-e4-source-roster",
        semantic_validator=pin(validator), resource_budget=budget)
    # The third coordinate represents each actual root nested within a group.
    coordinates = tuple(replace(value, coordinate_id="coordinate." + namespace + "." + str(index),
        field_id=("physical-unit", "invalid-disposition", "root")[index], clock_id=cutoff.clock_id)
        for index, value in enumerate(profile.input_coordinates))
    edge = replace(edge, input_coordinates=coordinates, output_coordinates=coordinates)
    contract_pin = ObjectIdentity.from_record(writer.root.contract.storage_root_id, writer.root.contract)
    source_scope = DatasetStorageScope("scope." + namespace + ".source", contract_pin, "sources/" + namespace)
    destination_scope = DatasetStorageScope("scope." + namespace + ".destination", contract_pin, "derived/" + namespace)
    control_scope = DatasetStorageScope("scope." + namespace + ".control", contract_pin, "dataset-operations/" + namespace)
    envelope = DatasetWorkEnvelope(budget, DatasetFileLimits(2, 2, 0, max(len(raw), 1)),
        DatasetControlLimits(1024**2, max(len(rows.rows), 1), 1024**2, 32))
    dataset_manifest = _transformation_manifest(writer=writer, selected=selected, namespace=namespace, source=source, output=output,
        rows=rows, cutoff=cutoff, transform=transform, transform_config=act, source_scope=source_scope,
        destination_scope=destination_scope, control_scope=control_scope, envelope=envelope, publications=publications)
    profile = replace(profile, profile_id="profile." + namespace, source_id="source." + namespace,
        source_selection=replace(profile.source_selection, capability_key="release-source-adapter." + namespace,
            implementation_sha256=implementation_sha()), source_config=pin(act),
        source_materialization=ObjectIdentity.from_record(source.materialization.materialization_id, source.materialization),
        expected_source_sha256=source.logical.content_sha256, expected_source_size_bytes=len(raw),
        licence_id="EXPOSED_RELEASE_VALIDATION_ONLY", operator_storage_root_id=writer.root.contract.storage_root_id,
        source_relative_locator=source.materialization.relative_path, source_schema=rows.SCHEMA, source_media_type="application/json",
        source_format_profile_id="selected-e4-source-roster", input_coordinates=coordinates, transform_edges=(edge,),
        output_schema=rows.SCHEMA, output_media_type="application/json", output_filename_suffix=".json",
        output_artifact_profile=SourcePipelineArtifactProfile.CANONICAL_JSON, output_coordinates=coordinates,
        semantic_validators=(pin(validator),), causal_cutoff=ObjectIdentity.from_record(cutoff.cutoff_id, cutoff),
        dataset_transformation_manifest=pin(dataset_manifest, "manifest_id"), resource_ceiling=budget,
        maximum_row_count=len(rows.rows), maximum_physical_unit_count=len(programme.group_ids),
        scratch_namespace="scratch/" + namespace, output_relative_locator=output.materialization.relative_path,
        evidence_world_id=original_preparation(originals).root.system.world.world_id,
        observation_operator=bank.response_selection.identity, numerical_view_ids=(numerical.object_id,),
        receiver_semantics_id="receiver." + namespace, validity_contract_id="validity." + namespace,
        uncertainty_contract_id="uncertainty." + namespace)
    adapter = replace(adapter, capability_key=profile.source_selection.capability_key,
        implementation_sha256=implementation_sha(), output_schema_ids=(rows.SCHEMA,), resource_budget=budget)
    request = template._dataset_request(profile)
    now = datetime.now(UTC).replace(microsecond=0)
    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    policy = replace(template._dataset_policy(profile, request), policy_id="policy." + namespace,
        source_scopes=(source_scope,), destination_scope=destination_scope, control_write_scope=control_scope,
        work_envelope_ceiling=envelope, implementation_commit=current_implementation.observed_git_head,
        evidence_class=DatasetEvidenceClass.METADATA_ONLY, materialization_class=DatasetMaterializationClass.METADATA_OBSERVATION,
        issued_by="issuer.release-source-validation", authorized_approver_id="approver.release-source-validation",
        valid_from_utc=at, valid_until_utc=(now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        reason_codes=("EXPOSED_RELEASE_VALIDATION_ONLY",))
    request = replace(request, request_id="request." + namespace, policy=pin(policy, "policy_id"),
        implementation_commit=current_implementation.observed_git_head,
        evidence_class=DatasetEvidenceClass.METADATA_ONLY, materialization_class=DatasetMaterializationClass.METADATA_OBSERVATION,
        valid_from_utc=at, valid_until_utc=policy.valid_until_utc, requested_by="operator.release-validation-source",
        reason_codes=("EXPOSED_RELEASE_VALIDATION_ONLY",), source_scopes=(source_scope,), destination_scope=destination_scope, control_write_scope=control_scope, work_envelope=envelope)
    # New deterministic TEST signer, explicitly disclosed; no original grant is
    # copied or relabelled and no production trust registration is installed.
    signer = template._Signer()
    issuer = DatasetAuthorizationIssuerRegistration("issuer." + namespace, "issuer.release-source-validation",
        frozenset((AuthorityAction.DATASET_TRANSFORMATION,)), implementation_sha(), "1.0.0",
        signer.signature_algorithm, signer.signature_version, signer.verification_key_hex, BLIND)
    authorization = issue_dataset_operation_authorization(policy=policy, request=request, authorization_id="authorization." + namespace,
        approved_by=policy.authorized_approver_id, issuer_registration=issuer, signer=signer,
        clock=template._Clock("clock." + namespace, at))
    compilation = compile_source_pipeline(profile, source_manifest=adapter, capability_registry=registry,
        dataset_registry=datasets, dataset_operation_request=request)
    output_identity = ObjectIdentity.from_record(output_manifest.logical.logical_artifact_id, output_manifest)
    roster_sha = sha256(("\n".join(programme.group_ids) + "\n").encode()).hexdigest()
    accounting = SourcePipelineEdgeAccounting(edge.edge_id, profile.source_materialization, output_identity,
        len(rows.rows), len(rows.rows), 0, 0, len(programme.group_ids), roster_sha, roster_sha, 0, coordinates, coordinates)
    result = SourceResult(compilation.source_request.request_id, profile.source_id, rows.SCHEMA,
        source.materialization, source.logical.content_sha256, len(raw), "verified")
    execution = SourcePipelineExecutionEvidence("execution." + namespace, policy, authorization, issuer, result, (accounting,),
        output_manifest, (SourcePipelineValidatorEvidence(pin(validator), pin(validator), True),), pin(recovery))
    config = shared.MatrixSourcePipelineConfig("config.pipeline." + namespace, profile, adapter, registry, datasets, request,
        execution, "clock." + namespace, at)
    receipt = config.assess()
    publication_record = output_manifest.publication
    _publish(writer, publication_record, publications, "publication_batch_id")
    for record, field in ((profile, "profile_id"), (cutoff, "cutoff_id"), (config, "config_id")):
        _publish(writer, record, publications, field)
    return SimpleNamespace(config=config, receipt=receipt, cutoff=cutoff, act=act, recovery=recovery, validator=validator, rows=rows)


def _closed_sdk(declarations):
    """Add only these six test workers to the installed SDK composition."""
    from empirical_lawhood.adapters.composition.discovery import bundle
    from empirical_lawhood.adapters.composition.generated_extension_bundles import EXTENSION_BUNDLE_CONTRIBUTIONS
    from empirical_lawhood.adapters.composition.generated_executable_bindings import (
        EXECUTABLE_BINDING_CONTRIBUTIONS, EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY,
    )
    from empirical_lawhood.runtime.extension_bundles import ExtensionContributionKind, compose_extension_bundle_aggregate
    from empirical_lawhood.runtime.executable_bindings import (
        ExecutableBindingContribution, ExecutableCapabilityProviderFactoryRegistry, compose_executable_binding_aggregate,
    )
    contributions, factories = [], []
    for declaration in declarations:
        manifest = declaration.manifest()
        contribution, components = bundle(manifest.capability_key.removeprefix(KEY + "."),
            ExtensionContributionKind.METHOD, manifest, (), None, namespace=KEY, maximum_config_bytes=16 * 1024**2)
        contributions.append(contribution)
        factories.append(declaration.provider_factory(components=tuple(sorted(components, key=lambda value: value.registration_id))))
    discovery = compose_extension_bundle_aggregate((*EXTENSION_BUNDLE_CONTRIBUTIONS, *contributions))
    binding = ExecutableBindingContribution(KEY + ".closed-test-factories", "1.0.0",
        tuple(sorted((value.binding for value in factories), key=lambda value: value.binding_id)))
    aggregate = compose_executable_binding_aggregate((*EXECUTABLE_BINDING_CONTRIBUTIONS, binding), discovery_aggregate=discovery)
    installed = tuple(EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.factory(key)
        for key in EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.binding_ids)
    registry = ExecutableCapabilityProviderFactoryRegistry(aggregate=aggregate,
        factories=tuple(sorted((*installed, *factories), key=lambda value: value.binding.binding_id)))
    return registry, discovery


def _source_root(originals, programme, common, *, namespace, budget):
    """New TEST metadata contract over the genuine source's declared subject.

    Keep the numerical system/views as the subject being checked. The
    estimand is exact finite metadata agreement; no original response, sampling,
    numerical convergence, calibration, or scientific qualification is tested.
    """
    from empirical_lawhood.kernel.experiments import (
        AssignmentKind, AssignmentSpec, ControlKind, ControlSpec, PrecisionGoal, RevealBarrierSpec,
    )
    from empirical_lawhood.kernel.obligations import (
        ClosureSpec, ComputabilityEvidence, FalsifierKind, FalsifierSpec, ObligationStatus,
        ScientificObligations, StructuralConvergenceSpec, SupportSpec, UncertaintySpec, ValiditySpec,
    )
    from empirical_lawhood.kernel.status import ReadinessStatus
    from empirical_lawhood.kernel.quantities import QuantityKind, QuantitySpec, ResponseDirection
    from empirical_lawhood.kernel.time import AvailabilitySpec
    from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
    from empirical_lawhood.kernel.worlds import WorldKind
    preparation = original_preparation(originals)
    root, cutoff = preparation.root, common.cutoff
    designs = tuple(DesignInputRecord("design." + namespace + "." + str(index), reference,
        reference.object_fingerprint, cutoff, DesignInputRole.READINESS_METADATA, BLIND, PROSPECTIVE,
        "human.release-validation-explicit-test-authority") for index, reference in enumerate(common.operands))
    clocks = {value.clock_id: value for value in root.system.clocks}
    clocks[cutoff.clock_id] = replace(root.system.clocks[0], clock_id=cutoff.clock_id)
    policy = replace(root.system.authority_policy, policy_id="policy." + namespace, budget_ceiling=budget)
    denominator = QuantitySpec("quantity." + namespace + ".declared-groups", "Declared source groups",
        QuantityKind.DENOMINATOR, "count", "groups", "canonical-source-metadata", cutoff.clock_id,
        AvailabilitySpec(cutoff.clock_id, CausalPhase.PREPARATION, BLIND, cutoff.coordinate))
    receiver = QuantitySpec("quantity." + namespace + ".metadata-mismatches", "Canonical source metadata mismatches",
        QuantityKind.RECEIVER, "count", "metadata mismatches", "canonical-source-metadata", cutoff.clock_id,
        AvailabilitySpec(cutoff.clock_id, CausalPhase.RECEIVER, BLIND), ResponseDirection.LOWER_IS_BETTER)
    relation = replace(root.system.relation, relation_id="relation." + namespace + ".metadata-agreement",
        denominator_quantity_ids=(denominator.quantity_id,), history_quantity_ids=(), memoryless=True,
        action_quantity_ids=(), receiver_quantity_ids=(receiver.quantity_id,))
    system = replace(root.system, world=replace(root.system.world, kind=WorldKind.NUMERICAL_SIMULATOR),
        clocks=tuple(clocks[key] for key in sorted(clocks)), authority_policy=policy, relation=relation,
        quantities=tuple(sorted((*root.system.quantities, denominator, receiver), key=lambda value: value.quantity_id)))
    claims = tuple(replace(value, claim_id="claim." + namespace + "." + str(index),
        proposition="Closed TEST source metadata agrees with the entire declared bank, reservation, assay, numerical profile and cutoff.",
        estimand="Exact finite group/root and canonical identity agreement only; no native response or statistical estimand.",
        relation_id=relation.relation_id, requested_rung=None, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        promotion_rule="EXPOSED_TEST_CONFORMANCE_ONLY_NO_SCIENTIFIC_QUALIFICATION_OR_FRESHNESS",
        assumption_ids=("assumption." + namespace + ".declared-source-metadata-only",),
        derivation_parent_ids=(), parent_visibility_ceilings=())
        for index, value in enumerate(root.experiment.claims))
    source_identity = KEY + ".source_identity"
    control = ControlSpec("control." + namespace + ".substituted-identity", ControlKind.BASELINE_COMPARATOR,
        source_identity, system.relation.receiver_quantity_ids,
        "Refuse a substituted source/reservation/assay/profile/cutoff pin; inspect declarations, never future receiver values.")
    goal = PrecisionGoal("precision." + namespace + ".exact-finite-roster", receiver.quantity_id,
        Decimal(1), "metadata mismatches", len(programme.group_ids),
        "Stop only after the complete assigned group/root census and exact canonical joins; any mismatch refuses; no interval is estimated.")
    required, inapplicable = ObligationStatus.REQUIRED, ObligationStatus.NOT_APPLICABLE
    obligations = ScientificObligations("obligations." + namespace,
        SupportSpec("support." + namespace + ".declared-roster", system.relation.relation_id,
            system.independent_unit.unit_id, len(programme.group_ids), 0, cutoff.cutoff_id,
            ("chart." + namespace + ".declared-source-metadata",), tuple(sorted(value.root_id for value in programme.cases)), (), required),
        ValiditySpec("validity." + namespace + ".exact-identities", ("domain." + namespace + ".immutable-metadata",),
            ("assumption." + namespace + ".declared-source-metadata-only",),
            ("NO_SCIENTIFIC_SOURCE_OR_NUMERICAL_VALIDITY_CLAIM",), required),
        UncertaintySpec("uncertainty." + namespace + ".statistical-inference-inapplicable",
            "method.exact-finite-metadata-comparison", system.independent_unit.unit_id, programme.design.confidence,
            (goal.metric_id,), ("EXACT_FINITE_METADATA_CENSUS_NO_STATISTICAL_INTERVAL",), inapplicable),
        (FalsifierSpec("falsifier." + namespace + ".substituted-operand", FalsifierKind.NEGATIVE_CONTROL,
            source_identity, "Substituted typed source operand or incomplete frozen roster.",
            "A different canonical pin, dropped group/root or future cutoff must refuse.", required),),
        ClosureSpec("closure." + namespace + ".dynamic-closure-inapplicable",
            ("cell." + namespace + ".finite-metadata-roster",), ("factor." + namespace + ".identity-substitution",),
            system.relation.history_quantity_ids, inapplicable),
        StructuralConvergenceSpec("convergence." + namespace + ".native-convergence-inapplicable",
            ("structure." + namespace + ".declared-numerical-profile-only",),
            tuple(value.view_id for value in system.numerical_views), (), inapplicable),
        ComputabilityEvidence("computability." + namespace + ".bounded-metadata-only",
            system.computability_envelopes[0].envelope_id, tuple(value.view_id for value in system.numerical_views),
            ReadinessStatus.REQUIRES_PROTOCOL_FREEZE, ("SOURCE_METADATA_TASKS_NOT_YET_EXECUTED",)))
    development = preparation.training_allocation.unit_ids("development")
    if not development or set(development) & set(programme.group_ids):
        raise ValueError("source TEST framing needs its genuine distinct exposed TRAIN census")
    # Required prospective API framing refers only to this new TEST metadata
    # intent. It never certifies freshness or reveal authority for E3/E4 science.
    barrier = RevealBarrierSpec("barrier." + namespace + ".test-metadata-only", development,
        "cohort." + namespace + ".test-source-contract", sha256(common.canonical_bytes()).hexdigest(),
        ("intent." + namespace + ".test-source-metadata-only",), OutcomeAccess.EVALUATION_SEALED, True)
    experiment = replace(root.experiment, experiment_id="experiment." + namespace, claims=claims, relation=relation,
        measurement_quantity_ids=(receiver.quantity_id,),
        assignment=AssignmentSpec("assignment." + namespace, AssignmentKind.OBSERVATIONAL,
            system.independent_unit.unit_id, system.relation.action_quantity_ids,
            "Compare declared action/source metadata only; execute no native intervention.",
            ("restriction." + namespace + ".source-metadata-only",)),
        controls=(control,), precision_goals=(goal,), information_cutoffs=(cutoff,),
        reveal_barrier=barrier, obligations=obligations, authority_policy_id=policy.policy_id,
        readiness=ReadinessStatus.AUTHORITY_REQUIRED, authorization_record_id=None,
        predecessor_experiment_ids=(), extensions=())
    substitutions = {ObjectIdentity.from_record(root.experiment.experiment_id, root.experiment):
        ObjectIdentity.from_record(experiment.experiment_id, experiment)}
    substitutions.update((ObjectIdentity.from_record(before.claim_id, before), ObjectIdentity.from_record(after.claim_id, after))
        for before, after in zip(root.experiment.claims, claims, strict=True))
    campaign = replace(root.campaign, campaign_id="campaign." + namespace, objective=DISCLOSURE,
        nodes=tuple(replace(value, object_identity=substitutions.get(value.object_identity, value.object_identity))
            for value in root.campaign.nodes), budget=budget,
        authority_policy=ObjectIdentity.from_record(policy.policy_id, policy),
        decision_rights=tuple(replace(value, authority_policy_id=policy.policy_id) for value in root.campaign.decision_rights),
        target_claim_ids=tuple(value.claim_id for value in claims), evidence_state=(), predecessor_campaign_ids=())
    return replace(root, draft_id="draft." + namespace, question=DISCLOSURE,
        system=system, experiment=experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(root.design_origin, origin_id="origin." + namespace,
            declared_input_ids=tuple(value.input_id for value in designs)),
        development_unit_ids=development, evaluation_unit_ids=programme.group_ids, development_seed_ids=(), evaluation_seed_ids=(),
        source_materializations=(), capability_selections=(), unresolved_decisions=(), resource_ceiling=budget,
        conditional_successor=None)


def _source_obligation_owners(root, namespace):
    """Explicit proof owners for this TEST metadata contract, never E3 science."""
    from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
    experiment, obligations = root.experiment, root.experiment.obligations
    def node(value):
        return namespace + "." + value
    def suffix(value):
        return experiment.experiment_id + "." + value
    owners = {
        node("source_identity"): (obligations.validity.validity_id,
            *(value.control_id for value in experiment.controls), *(value.falsifier_id for value in obligations.falsifiers)),
        node("physical_unit_completeness"): (obligations.support.support_id, obligations.uncertainty.uncertainty_id,
            *(value.goal_id for value in experiment.precision_goals), suffix("independent-split"), suffix("stopping")),
        node("numerical_or_instrument_validity"): (obligations.structural_convergence.convergence_id,),
        node("observation_operator"): (obligations.closure.closure_id,),
        node("preparation"): (suffix("conditional-nonattempt"),),
        node("causal_cutoff"): (experiment.reveal_barrier.barrier_id,
            *(value.cutoff_id for value in experiment.information_cutoffs),
            suffix("causal-no-outcome-construction"), suffix("seal-reveal-separation")),
        node("pipeline"): (obligations.computability.computability_id, suffix("authority"),
            suffix("source-readiness"), suffix("mandatory-hold"), suffix("reachability")),
        node("qualification"): (obligations.obligations_id,),
        node("adjudicate"): (suffix("admission"), suffix("required-outputs")),
    }
    declared = tuple(value for values in owners.values() for value in values)
    if len(declared) != len(set(declared)) or set(declared) != set(_required_obligation_ids(experiment)):
        raise ValueError("source metadata canonical obligations require exact unique declared proof owners")
    return owners


def _source_draft(originals, programme, bank, scope, pipeline, qualification, selected, namespace):
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft, RecursiveOperationSpec, RecursiveExternalInput, RecursiveInputLink
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    declarations = (*tuple(gate_declaration(kind) for kind in GATES), *shared.source_declarations(), source_closeout_declaration())
    closeout = ReleaseSourceCloseoutConfig("config.closeout." + namespace,
        tuple(sorted((shared.reference(value, field) for value, field in (
            *tuple((value, "evidence_id") for value in qualification.gate_evidence),
            (pipeline.receipt, "receipt_id"), (qualification.assess(), "result_id"))), key=lambda value: value.object_id)))
    configs = (*gate_configs(scope), pipeline.config, qualification, closeout)
    by_schema_kind = {ReleaseGateConfig.SCHEMA: {value.gate_kind: declaration for value, declaration
        in zip(configs[:len(GATES)], declarations[:len(GATES)], strict=True)}}
    operations, external, records, links = [], [], {}, []
    root = _source_root(originals, programme, scope, namespace=namespace,
        budget=ResourceBudget.aggregate(task_budget(selected) for _ in configs))
    proof_owners = _source_obligation_owners(root, namespace)
    for config in configs:
        declaration = (by_schema_kind[ReleaseGateConfig.SCHEMA][config.gate_kind]
            if type(config) is ReleaseGateConfig else source_closeout_declaration() if type(config) is ReleaseSourceCloseoutConfig
            else shared.source_declarations()[0 if type(config) is shared.MatrixSourcePipelineConfig else 1])
        node = namespace + "." + (config.gate_kind.value.lower() if type(config) is ReleaseGateConfig
            else "adjudicate" if type(config) is ReleaseSourceCloseoutConfig
            else "pipeline" if type(config) is shared.MatrixSourcePipelineConfig else "qualification")
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declaration.registration().selection,
            config_id=config.config_id, config=config,
            obligation_ids=tuple(sorted(("obligation." + node, *proof_owners[node]))), resource_budget=task_budget(selected)))
        if type(config) is ReleaseGateConfig:
            for name, record in (("programme", programme), ("bank", bank), ("reservation", bank.reservation),
                    ("assay", bank.response_selection), ("numerical", bank.source(bank.sources[0].root_id, index=bank.source_index()).numerical_design),
                    ("cutoff", scope.cutoff)):
                identifier = (programme.programme_id if name == "programme" else bank.bank_id if name == "bank"
                    else scope.cutoff.cutoff_id if name == "cutoff" else old.identity(record).object_id)
                reference = ObjectIdentity.from_record(identifier, record)
                external_id = "external." + namespace + "." + name
                row = RecursiveExternalInput(external_id, reference.object_id, record.SCHEMA, "application/json",
                    len(record.canonical_bytes()), BLIND, PROSPECTIVE, record.fingerprint())
                if external_id not in records:
                    external.append(row)
                    records[external_id] = record
                links.append(RecursiveInputLink("edge." + node + "." + name, node, name,
                    external_input_id=external_id, scientific_role="SOURCE"))
    for operation in operations[:-1]:
        name = operation.node_id.removeprefix(namespace + ".")
        links.append(RecursiveInputLink("edge." + namespace + ".adjudicate." + name, namespace + ".adjudicate", name,
            producer_node_id=operation.node_id, producer_output_id="product", scientific_role="SOURCE"))
    draft = RecursiveStudyDraft("recursive." + namespace, DISCLOSURE, root.campaign, (), (), (),
        tuple(sorted(operations, key=lambda value: value.node_id)),
        tuple(sorted(external, key=lambda value: value.input_id)),
        tuple(sorted(links, key=lambda value: value.edge_id)), tuple(sorted(value.node_id for value in operations)),
        prospective_draft=root)
    source_configs, qualifications = _source_admissions(draft, tuple(sorted(records.items())), (), root=root, prefix=namespace,
        observation_operator=pipeline.config.profile.observation_operator)
    draft = _source_projection(draft, SimpleNamespace(source_configs=source_configs, qualifications=qualifications),
        {row.logical_artifact_id: records[row.input_id].VERSION for row in draft.external_inputs})
    return draft, tuple(sorted(records.items())), source_configs, qualifications, declarations


def _resources(draft, selected, namespace):
    from empirical_lawhood.runtime.execution_envelope import NonTimeResourceBudget, ExecutionResourceTaskCellSpec, ChildResourceTokenLimit
    from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
    budget = task_budget(selected)
    cells = tuple(ExecutionResourceTaskCellSpec("cell." + row.node_id, row.node_id, "child." + namespace,
        None, None, 1, 0, 0, False,
        NonTimeResourceBudget("budget." + row.node_id, budget.cpu_cores, budget.memory_bytes,
            budget.output_bytes, 100, budget.source_scan_bytes), None, None, None) for row in draft.operations)
    return ExecutionResourceSelection("resources." + namespace, tuple(sorted(cells, key=lambda value: value.cell_id)),
        (ChildResourceTokenLimit("child." + namespace, 0, 0),), (), (), (), None, None,
        selected.workers, selected.workers * budget.memory_bytes, (), (),
        sha256((DISCLOSURE + namespace).encode()).hexdigest(), True, True, True, True)


def _sdk_execution(originals, handoff, issued, directory, selected, *, executor_factory=None):
    """Actual installed execution owner with the closed six-worker SDK extension."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
    from empirical_lawhood.api.execution import CampaignExecutionService
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.infrastructure.execution import DurableExecutionResourceEnvelopeCoordinator
    from empirical_lawhood.infrastructure.execution_resource_envelopes import ExternalExecutionResourceEnvelopeStore
    from empirical_lawhood.infrastructure.sql import create_catalog_engine, upgrade_catalog
    from empirical_lawhood.infrastructure.study_issue import ExternalIssuedExtensionPayloadSource, ExternalIssuedStudyPublisher, GitStudySourceClosureInspector
    from empirical_lawhood.runtime.executable_bindings import LayeredCampaignRuntimeProviderResolver
    from empirical_lawhood.runtime.issued_extension_payloads import IssuedExtensionPayloadResolver
    from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry
    from tests.test_matrix_e3_public_programme import _ObservedProcessExecutor
    _, factories, _, writer, _, package, reveal, approval, authorities = issued
    directory.mkdir(parents=True, exist_ok=True)
    package_path = directory / "package.json"
    package_path.write_bytes(package.canonical_bytes())
    catalog = directory / "catalog.sqlite3"

    def engine_factory():
        engine = create_catalog_engine("sqlite+pysqlite:///" + str(catalog))
        upgrade_catalog(engine)
        return engine

    executor = (_ObservedProcessExecutor(writer.root, directory / "worker-ready")
        if executor_factory is None else executor_factory(writer.root))
    service = CampaignExecutionService(repo_root=ROOT, artifact_plane=writer,
        engine_factory=engine_factory, catalog_path=catalog, providers=CampaignRuntimeProviderRegistry(()),
        provider_resolver=LayeredCampaignRuntimeProviderResolver(precomposed=CampaignRuntimeProviderRegistry(()), factories=factories),
        executable_binding_aggregate=factories.aggregate,
        issued_extension_payload_resolver=IssuedExtensionPayloadResolver(source=ExternalIssuedExtensionPayloadSource(
            ExternalIssuedStudyPublisher(artifact_plane=writer, authority_store=authorities, grantee_id="operator.issue-service")),
            codecs=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY),
        executable_platform_ports=handoff.platform_ports, approval_service=approval, study_authority_store=authorities,
        study_source_closure_inspector=GitStudySourceClosureInspector(ROOT), executor=executor,
        enforce_git_identity=True, maximum_parallel_tasks=selected.workers,
        execution_resource_envelope_coordinator=DurableExecutionResourceEnvelopeCoordinator(ExternalExecutionResourceEnvelopeStore(writer.root)))
    api = EmpiricalLawhoodApi(repo_root=ROOT, external_root=Path(writer.root.contract.canonical_path),
        execution_service=service, approval_service=approval, study_authority_store=authorities)
    return SimpleNamespace(service=service, api=api, executor=executor, package=package,
        package_path=package_path, reveal=reveal, catalog=catalog)


def _actual_bindings(writer, package, plan, expected, codecs):
    from empirical_lawhood.api.current_result_custody import retained_output_artifact_plane
    from empirical_lawhood.api.recursive_qualified_parents import _collect_receipt_closure, _verify_receipt_closure, _output_payload
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    semantic = retained_output_artifact_plane(package, plan, writer, codecs)
    with semantic.verification_scope() as guarded:
        closure = _collect_receipt_closure(package, plan, guarded, None,
            tuple(sorted(value.capability_key for value in package.registry.capabilities)))
        _verify_receipt_closure(guarded, closure)
        result = []
        for task in plan.tasks:
            if task.task_id not in expected:
                if task.capability.capability_key != source_closeout_declaration().capability_key:
                    raise PermissionError("source predecessor has an undeclared producer")
                continue
            record, field = expected[task.task_id]
            receipt = closure.by_task[task.task_id]
            logical, = (value for value in receipt.output_logical_artifacts if value.payload_schema == record.SCHEMA)
            raw = _output_payload(guarded, receipt, logical, len(record.canonical_bytes()))
            if raw != record.canonical_bytes():
                raise PermissionError("actual source predecessor product differs from independently replayed inputs")
            result.append(RecursivePriorExecutionBinding("binding." + task.task_id,
                ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
                ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
                ObjectIdentity.from_record(package.package_id, package), ObjectIdentity.from_record(plan.execution_plan_id, plan),
                package.run_plan_id, task.task_id, ObjectIdentity.from_record(receipt.receipt_id, receipt),
                logical.logical_artifact_id, shared.reference(record, field), record_id_field=field))
        guarded.require_verification_snapshot()
    return tuple(sorted(result, key=lambda value: value.record.object_id))


def selected_e4_source_predecessor(*, project_root, originals, programme, bank, selected, directory, monkeypatch, measurements):
    """Run eight actual issued producers under newly disclosed TEST authority.

    No fixture qualification is promoted into a real scientific statement. The
    public native consumer must still authenticate all these actual producer
    receipts, publications and gates through its unchanged strict admission.
    """
    from empirical_lawhood.api import recursive_prospective_authoring as author
    from empirical_lawhood.api.facade import EmpiricalLawhoodApi
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.results import RunCampaignRequest, CampaignStatusRequest, ResumeCampaignRequest
    from empirical_lawhood.api.matrix_source_runtime import authenticate_matrix_source_qualification, matrix_source_publication_references
    from empirical_lawhood.api.recursive_qualified_parents import _ParentReadScope
    from empirical_lawhood.runtime.experiment_resources import bind_execution_resources
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from tests.experiment_entry_support import standard_authoring_for_draft
    from tests.runtime_platform.test_study_issue import _issue_api_fixture
    from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff
    from tests.test_matrix_selected_e4_public_programme import NeverExecute
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY

    if Path(project_root).resolve(strict=True) != ROOT or selected.workers < 4:
        raise ValueError("release source predecessors require the sole checkout and explicit >=4 worker slots")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    writer, namespace = originals.writer, selected.namespace + "." + bank.phase.lower() + ".source"
    if not directory.resolve().is_relative_to(Path(writer.root.contract.canonical_path).resolve()):
        raise ValueError("source predecessors must use the selected actual guarded EL writer")
    publications = {}
    pipeline = measurements.call(namespace + ".pipeline", source_pipeline, originals=originals, programme=programme,
        bank=bank, selected=selected, namespace=namespace, publications=publications)
    # Use actual owning profile identities; this selects no inferential rung
    # and supplies no empirical premise or scientific qualification.
    from empirical_lawhood.planning.evidence_profiles import (
        EvidenceWorldKind, bind_profile_selection, build_observation_evidence_world_registry,
    )
    evidence_registry = build_observation_evidence_world_registry()
    world, = (value for value in evidence_registry.world_profiles
        if value.world_kind is EvidenceWorldKind.DETERMINISTIC_SIMULATOR)
    profile = bind_profile_selection(selection_id="selection." + namespace, draft_id="draft." + namespace,
        registry=evidence_registry, world_profile_id=world.profile_id,
        objective_profile_id="objective.observation-order", requested_rungs=())
    numerical = bank.source(bank.sources[0].root_id, index=bank.source_index()).numerical_design
    common = ReleaseGateScope("scope." + namespace, programme.identity, bank.identity, old.identity(bank.reservation),
        bank.response_selection.identity, old.identity(numerical), pipeline.cutoff, programme.group_ids,
        pipeline.config.profile, pipeline.receipt, profile, pin(pipeline.act), pin(pipeline.recovery), pin(pipeline.validator))
    configs, specification = gate_configs(common), gate_specification(common)
    gates = tuple(sorted((gate_product(config) for config in configs), key=lambda value: value.evidence_id))
    gate_declarations = tuple(gate_declaration(kind) for kind in GATES)
    gate_registry = CapabilityRegistry("registry." + namespace,
        tuple(sorted((value.manifest() for value in gate_declarations), key=lambda value: value.registry_id)))
    qualification = shared.MatrixSourceQualificationConfig("config.qualification." + namespace,
        specification, pipeline.receipt, gate_registry, gates)
    result = qualification.assess()
    pipeline_evidence = shared.MatrixSourcePipelineEvidence("pipeline-evidence." + namespace,
        pipeline.config, pipeline.receipt, qualification, profile)
    for record, field in ((programme, "programme_id"), (bank, "bank_id"), (bank.reservation, "reservation_id"),
            (bank.response_selection, "selection_id"), (numerical, "design_id"), (profile, "selection_id"),
            (specification, "spec_id"), (qualification, "config_id"), (common, "record_id")):
        _publish(writer, record, publications, field)
    for config in configs:
        _publish(writer, config, publications, "config_id")
    draft, records, source_configs, qualifications, declarations = _source_draft(originals, programme, bank,
        common, pipeline, qualification, selected, namespace)
    custom_declarations = (*gate_declarations, source_closeout_declaration())
    sdk_factories, discovery = _closed_sdk(custom_declarations)
    installed_registrations, installed_registry, installed_codecs = operation_catalog()
    registrations = (*installed_registrations, *(value.registration() for value in custom_declarations))
    registry = CapabilityRegistry("registry." + namespace + ".all",
        tuple(sorted((*installed_registry.capabilities, *(value.manifest() for value in custom_declarations)), key=lambda value: value.registry_id)))
    codecs = {**installed_codecs, **{schema: kind for value in declarations for schema, kind in value.record_codecs.items()}}
    composition = (registrations, registry, codecs)
    implementation = implementation_binding(ROOT)
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit=implementation.observed_git_head, qualifications=qualifications,
        known_design_inputs=draft.prospective_draft.design_inputs, output_codecs=codecs,
        implementation_sha256=implementation.code_sources_sha256)
    standard, formal = standard_authoring_for_draft(compilation.candidate_draft, compilation.candidate_context,
        formal_method_capability_key=gate_declarations[0].capability_key)
    input_dir = directory / "inputs"
    input_dir.mkdir()
    bindings = []
    for external_id, record in records:
        external, = (value for value in draft.external_inputs if value.input_id == external_id)
        path = input_dir / (sha256(external.logical_artifact_id.encode()).hexdigest() + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append((external.logical_artifact_id, path))
    for config in source_configs:
        path = input_dir / (config.fingerprint() + ".json")
        path.write_bytes(config.canonical_bytes())
        bindings.append((config.fingerprint(), path))
    operands = tuple(RecursiveProspectiveOperand(value.logical_artifact_id, value.expected_content_sha256,
        value.maximum_size_bytes, value.payload_schema, value.media_type, value.outcome_access, value.visibility_ceiling)
        for value in sorted(draft.external_inputs, key=lambda value: value.logical_artifact_id))
    design = RecursiveProspectiveDesignInputs("prospective." + namespace, draft, standard.entry_package,
        formal.formal_methods, formal.source_inventories, qualifications, draft.prospective_draft.design_inputs, operands)

    def api_factory(*, repo_root, candidate_context_provider, candidate_capability_catalog):
        return EmpiricalLawhoodApi(repo_root=repo_root, external_root=None, candidate_context_provider=candidate_context_provider,
            candidate_capability_catalog=candidate_capability_catalog, extension_bundle_aggregate=discovery,
            executable_binding_aggregate=sdk_factories.aggregate, executable_factory_registry=sdk_factories,
            study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY)

    preview = measurements.call(namespace + ".preview", author.preview_recursive_prospective_candidate,
        design_inputs=design, project_root=ROOT, artifact_writer=writer, input_bindings=tuple(bindings),
        composition=composition, api_factory=api_factory, candidate_catalog=discovery.candidate_capability_catalog)
    resources = bind_execution_resources(_resources(draft, selected, namespace), issued_extensions=preview.issued_extensions)
    spec = design.bind_resources(resources)
    authoring_directory = directory / "authoring"
    measurements.call(namespace + ".author", author.author_recursive_prospective, spec=spec, project_root=ROOT,
        artifact_writer=writer, output_dir=authoring_directory, input_bindings=tuple(bindings),
        composition=composition, api_factory=api_factory, candidate_catalog=discovery.candidate_capability_catalog,
        expected_preview=preview)
    handoff = author.load_recursive_prospective_handoff(directory=authoring_directory, root=ROOT,
        storage_profile=originals.profile, artifact_writer=writer, composition=composition,
        candidate_catalog=discovery.candidate_capability_catalog)
    author.prove_recursive_prospective_handoff(handoff, factory_registry=sdk_factories)
    # The issue fixture selects new independent test approver/issuer acts. The
    # source closure and every real provider remain current sole-checkout bytes.
    issue_dir = directory / "issue"
    issue_dir.mkdir()
    scaffold_api, paths, _, custody = _issue_api_fixture(issue_dir,
        standard_fixture=lambda: (handoff.authoring.base, handoff.context.resolve_standard(handoff.authoring.base).context))
    parts = (handoff, sdk_factories, discovery, writer, b"", scaffold_api, paths, custody)
    issued = _issue_public_handoff(issue_dir, monkeypatch, handoff_parts=parts, namespace=namespace,
        compiled_candidate=preview.candidate)
    control = _sdk_execution(originals, handoff, issued, directory / "execution", selected)
    before = len(control.executor.completed)
    run = measurements.call(namespace + ".run", control.api.run_campaign, RunCampaignRequest(control.package_path,
        confirmed=True, reveal_authority_id=control.reveal.authority_id))
    if not run.succeeded:
        raise AssertionError((run.reason_codes, run.errors))
    if len(control.executor.completed) - before != len(draft.operations) or len(draft.operations) != 9:
        raise AssertionError("source predecessor must execute eight independent producers and one UNEVALUABLE closeout exactly once")
    status = measurements.call(namespace + ".read", control.api.campaign_status,
        CampaignStatusRequest(control.package.run_plan_id, include_attempt_history=True))
    if not status.succeeded:
        raise AssertionError((status.reason_codes, status.errors))
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    expected = {}
    for task in plan.tasks:
        if task.capability.capability_key == source_closeout_declaration().capability_key:
            continue
        if task.capability.capability_key == shared.source_declarations()[0].capability_key:
            expected[task.task_id] = pipeline.receipt, "receipt_id"
        elif task.capability.capability_key == shared.source_declarations()[1].capability_key:
            expected[task.task_id] = result, "result_id"
        else:
            config, = (value for value in configs if value.gate_kind.value.lower() == task.capability.capability_key.removeprefix(KEY + "."))
            expected[task.task_id] = gate_product(config), "evidence_id"
    executions = _actual_bindings(writer, control.package, plan, expected, codecs)
    references = matrix_source_publication_references(specification, result, pipeline_evidence)
    if not set(references).issubset(publications):
        raise AssertionError("missing actual source publication: " + repr(set(references).difference(publications)))
    source = native.SelectedE4SourceQualification("qualification." + namespace, specification, result,
        pipeline_evidence, executions, tuple((reference, publications[reference]) for reference in references))
    with writer.verification_scope() as guarded:
        authenticate_matrix_source_qualification(writer=guarded, specification=specification, result=result,
            pipeline=pipeline_evidence, executions=executions, publications=source.publications,
            codecs=codecs, read_scope=_ParentReadScope(guarded))
        guarded.require_verification_snapshot()
    recovery = _sdk_execution(originals, handoff, issued, directory / "completed-recovery", selected, executor_factory=NeverExecute)
    recovered = measurements.call(namespace + ".recover", recovery.api.resume_campaign,
        ResumeCampaignRequest(control.package.run_plan_id, confirmed=True, reveal_authority_id=control.reveal.authority_id))
    if not recovered.succeeded or recovery.executor.calls:
        raise AssertionError(("source predecessor completed recovery must not reenter any worker", recovered, recovery.executor.calls))
    return SimpleNamespace(source=source, controls=(control, recovery), run=run, status=status, recovered=recovered,
        sdk_composition_claim="CUSTOM_CLOSED_TEST_SDK_EIGHT_ACTUAL_PRODUCERS_NOT_DEFAULT_INSTALLED_CLI",
        qualification="NOT_ESTABLISHED", source_scope=DISCLOSURE)
