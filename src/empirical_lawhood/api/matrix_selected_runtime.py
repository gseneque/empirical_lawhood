# SPDX-License-Identifier: MPL-2.0
"""Current issued custody for selected protected Matrix prepared workers.

The complete original scientific entry is assessed once by its actual entry
task. Later leaves authenticate that successful entry receipt and exact current
inputs; they do not reconstruct the complete source roster in every worker.
No authority, qualification, retry or publication is created here.
"""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustodySupplier
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedEntryEvidenceV3, MatrixSelectedProtectedRootConfigV3
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import (
    reference, validate_selected_entry_evidence,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry_v2 import (
    MatrixSelectedEntryEvidenceV2, validate_selected_entry_evidence_v2,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedRootConfig
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import MatrixSelectedProtectedEntrySeal
from .recursive_qualified_parents import (
    MAX_PARENT_BYTES, _output_payload, _semantic_writer,
)
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import artifact_custody_limits


def _published_input(writer, run_id, spec, kind, *, custody=None):
    """Authenticate one actual plan-selected control without consuming a port."""
    relative, _, _ = provider_input_location(writer, run_id, spec.logical_artifact_id)
    limit = artifact_custody_limits(writer).manifest_bytes
    manifest = decode_artifact_manifest(read_bounded_bytes(writer.root.resolve(relative + ".manifest.json", for_write=False),
        maximum_bytes=limit), maximum_bytes=limit)
    if (manifest.materialization.relative_path != relative
            or manifest.materialization.storage_root_id != writer.root.contract.storage_root_id
            or manifest.logical.logical_artifact_id != spec.logical_artifact_id
            or manifest.logical.payload_schema != kind.SCHEMA
            or any(expected is not None and actual != expected for actual, expected in (
                (manifest.logical.payload_schema, spec.expected_payload_schema),
                (manifest.logical.content_sha256, spec.expected_content_sha256),
                (manifest.materialization.size_bytes, spec.expected_size_bytes),
                (manifest.logical.media_type, spec.expected_media_type),
                (manifest.logical.outcome_access, spec.expected_outcome_access),
                (manifest.logical.visibility_ceiling, spec.expected_visibility_ceiling)))):
        raise PermissionError("selected entry changes its actual plan-selected persisted control")
    # Legacy plans omit these optional fields. Preserve the control owner's
    # blind/prospective defaults; never infer a broader lane from stored bytes.
    lane = {}
    if spec.expected_outcome_access is not None:
        lane["expected_outcome_access"] = spec.expected_outcome_access
    if spec.expected_visibility_ceiling is not None:
        lane["expected_visibility_ceiling"] = spec.expected_visibility_ceiling
    from .current_task_custody import CurrentDevelopmentTaskCustody
    if type(custody) is CurrentDevelopmentTaskCustody:
        return custody.control_record(manifest,kind,manifest.materialization.size_bytes)
    read=(CurrentIssuedTaskCustody(writer=writer).control_record if custody is None else custody.immutable_control_record)
    return read(manifest,kind,manifest.materialization.size_bytes,**lane)


def _issued_configuration_lane(task):
    """Derive input custody only from the exact frozen compiler CONFIG census.

    This pure metadata join grants no authority and opens no body. The issued
    task/input owner must already authenticate the actual plan and copy facts.
    """
    from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
    validated_task_scientific_input_edges(task)
    spec,=(value for value in task.external_inputs if value.input_id=='config')
    return {'expected_outcome_access':spec.expected_outcome_access,
        'expected_visibility_ceiling':spec.expected_visibility_ceiling}


def _entry_task(plan):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_bindings import ENTRY_ORIGINAL_COMMITMENTS_KEY
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_e6_transport_config import ENTRY_TRANSPORT_KEY

    tasks = tuple(task for task in plan.tasks if task.capability.capability_key in (ENTRY_ORIGINAL_COMMITMENTS_KEY, ENTRY_TRANSPORT_KEY))
    if len(tasks) != 1:
        raise PermissionError("selected programme omits or repeats its actual installed entry task")
    return tasks[0]


def _current_source_qualifications(package, task):
    """Retain exact source qualifications from this actual issued programme."""
    root = package.issued_study.candidate.authoring_package.base.draft
    sources = {value.source_id: value for value in root.source_materializations}
    qualified = {reference(value, "receipt_id"): value for value in package.issued_study.materialization_qualifications}
    for item in task.external_inputs:
        # The compiler-owned config is authenticated by current_task/control_record;
        # it is not an independently acquired scientific source materialization.
        if item.logical_artifact_id == task.capability.config.artifact_id:
            continue
        candidates = tuple(value for value in sources.values() if value.materialization.object_id == item.logical_artifact_id)
        if len(candidates) != 1:
            raise PermissionError("selected entry loses its actual issued source materialization")
        source, = candidates
        receipt = qualified.get(source.qualification_receipt)
        if (receipt is None or receipt.source_id != source.source_id or receipt.materialization != source.materialization
                or receipt.content_sha256 != source.content_sha256 or source.content_sha256 != item.expected_content_sha256
                or source.evidence_world_id != receipt.evidence_world_id
                or source.observation_operator != receipt.observation_operator
                or source.numerical_view_ids != receipt.numerical_view_ids
                or (receipt.outcome_access, receipt.visibility_ceiling) != (item.expected_outcome_access, item.expected_visibility_ceiling)):
            raise PermissionError("selected entry substitutes its genuine issued materialization qualification")


def _publication(writer, pin, publication):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    import json

    authenticate_publication(writer, publication)
    raw = read_bounded_bytes(writer.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=publication.materialization.size_bytes)
    document = json.loads(raw)
    if (sha256(raw).hexdigest() != pin.object_fingerprint or len(raw) != publication.materialization.size_bytes
            or type(document) is not dict or (document.get("schema"), document.get("version")) != (pin.object_schema, pin.object_version)):
        raise PermissionError("selected entry substitutes original scientific publication bytes or revision")


def reconstruct_selected_package(public_package, calibration):
    """Join original sealed calibration to its exact public frozen projection."""
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family

    family = selected_e3_product_family(public_package.specification)
    MatrixSelectedFrozenPackage, MatrixSelectedPublicPackage = family.package_type, family.public_type

    if type(public_package) is not MatrixSelectedPublicPackage:
        raise TypeError("selected parent requires its exact public frozen package")
    package = MatrixSelectedFrozenPackage(public_package.original_package.object_id,
        public_package.specification, public_package.allocation, public_package.prefit, public_package.models,
        public_package.model_freeze, calibration, public_package.calibrated_freeze, public_package.selection_unit_ids)
    if package.identity != public_package.original_package or MatrixSelectedPublicPackage.from_package(package) != public_package:
        raise PermissionError("selected public projection substitutes its exact original scientific sealed frozen package")
    return package


def _reconstruct_entry_programme(programme, calibration, nomination=None):
    """Recover sealed scientific joins only inside authenticated parent custody.

    Children retain public projections. The original calibration bank arrives
    from its original issued/revealed producer, never from a relabelled control.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_point import MatrixSelectedPointDesign
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPointPayload
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme

    if type(programme) is not MatrixSelectedPublicProgramme:
        raise TypeError("selected parent requires its exact public programme projection")
    public_design, public_package = programme.point_design, programme.point_design.package
    package = reconstruct_selected_package(public_package, calibration)
    from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
    MatrixSelectedPublicPackage = selected_e3_product_family(public_package.specification).public_type
    design = MatrixSelectedPointDesign(public_design.original_design.object_id, package, public_design.phase,
        public_design.expected_groups, public_design.arms, public_design.sources, public_design.interpretations)
    original = MatrixSelectedProtectedProgramme(programme.original_programme.object_id, programme.sources,
        design, programme.assay, programme.panels, programme.criterion, programme.transfer_domain_claims,
        nomination, programme.nomination_publication, programme.nomination_receipt)
    if (package.identity != public_package.original_package or MatrixSelectedPublicPackage.from_package(package) != public_package
            or design.identity != public_design.original_design or MatrixSelectedPointPayload.from_design(design) != public_design
            or original.identity != programme.original_programme or MatrixSelectedPublicProgramme.from_programme(original) != programme):
        raise PermissionError("selected public projection changes its exact original scientific package, design or programme")
    return original


def _authenticate_entry(writer, programme, evidence, codecs, *, source_scan_bytes, transport_policy=None, transport_calibration=None,current_access=None):
    from .matrix_prepared_original_commitments import authenticate_prepared_original_commitments
    original_commitments = authenticate_prepared_original_commitments(writer=writer, programme=programme, evidence=evidence, source_scan_bytes=source_scan_bytes,
            **({} if current_access is None else {"current_access":current_access}))
    original = authenticate_selected_original_products(writer, programme, evidence, codecs,current_access=current_access)
    if transport_policy is not None:
        request, future = original_commitments
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import authenticate_e6_transport_policy
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import (
            validate_e6_transport_scope, validate_e6_calibration_projection,
        )
        authenticate_e6_transport_policy(writer, request, transport_policy, future_selections=future)
        validate_e6_transport_scope(transport_policy, programme)
        if transport_calibration is not None:
            validate_e6_calibration_projection(transport_calibration, transport_policy, original.point_design.package)
    elif transport_calibration is not None:
        raise ValueError("a calibrated E6 projection requires its actual preTRAIN policy")
    return original


def authenticate_selected_original_products(writer, programme, evidence, codecs,*,current_access=None):
    """Reopen exact original producer/source operands without granting entry."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from .matrix_sampling_runtime import _original_product, _original_products
    from .matrix_source_runtime import authenticate_matrix_source_qualification, matrix_source_publication_references
    from empirical_lawhood.api.matrix_selected_producer_scope import selected_original_producer_scope

    validate_evidence = (validate_selected_entry_evidence_v2 if type(evidence) is MatrixSelectedEntryEvidenceV2
                         else validate_selected_entry_evidence)
    validate_evidence(evidence, programme)
    closure, package = programme.sources.closure, programme.point_design.package
    read_scope = None
    authenticate_publication(writer, evidence.reservation_publication, closure.reservation)
    authenticate_publication(writer, closure.reservation.publication, closure.reservation.allocation)
    authenticate_publication(writer, closure.audit_publication, closure.audit)
    upstream = {reference(record, "record_id"): record for record in (
        package.models, package.model_freeze, package.calibrated_freeze)}
    producer_scope = selected_original_producer_scope(programme)
    calibration, nomination = None, None
    nomination_pin = None if programme.nomination is None else programme.nomination.original_nomination
    e3_originals = tuple(original for original in evidence.upstream_products
        if original.record in upstream or original.record == package.calibration)
    from .selected_prepared_access import _selected
    selected_originals=_selected(e3_originals,current_access)
    payloads = _original_products(writer, tuple((original, original.record) for original in selected_originals),
        codecs, scope_validator=producer_scope)
    original_payloads = {original.record: raw for original, raw in zip(selected_originals, payloads, strict=True)}
    for original in _selected(evidence.upstream_products,current_access):
        raw = (original_payloads[original.record] if original.record in original_payloads else
            _original_product(writer, original, original.record, codecs, read_scope, scope_validator=producer_scope))
        if original.record == package.calibration:
            from empirical_lawhood.api.matrix_selected_e3_family import selected_e3_product_family
            family = selected_e3_product_family(package.specification)
            calibration = decode_canonical_bytes(raw, family.calibration_type, maximum_bytes=MAX_PARENT_BYTES)
            if reference(calibration, "record_id") != package.calibration or calibration.canonical_bytes() != raw:
                raise PermissionError("selected entry substitutes its actual original sealed calibration")
        elif original.record == nomination_pin:
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.science import MatrixPreparationNomination
            nomination = decode_canonical_bytes(raw, MatrixPreparationNomination, maximum_bytes=MAX_PARENT_BYTES)
            receipt, publication = programme.nomination_receipt, programme.nomination_publication
            binding = original.prior_execution
            if (reference(nomination, "result_id") != nomination_pin or nomination.canonical_bytes() != raw
                    or reference(receipt, "receipt_id") != binding.receipt
                    or (receipt.run_id, receipt.task_id, publication.logical.logical_artifact_id) !=
                        (binding.run_id, binding.task_id, binding.logical_artifact_id)):
                raise PermissionError("selected confirmation substitutes its actual original nomination producer or receipt")
            authenticate_publication(writer, publication, nomination)
        elif raw != upstream[original.record].canonical_bytes():
            raise PermissionError("selected entry substitutes actual original fitted or calibrated product bytes")
    if type(evidence) in (MatrixSelectedEntryEvidenceV2, MatrixSelectedEntryEvidenceV3) and evidence.development_nomination is not None:
        from .matrix_selected_opportunity_runtime import authenticate_selected_development_nomination

        original_package = reconstruct_selected_package(package, calibration)
        nomination, receipt, publication = authenticate_selected_development_nomination(writer, evidence.development_nomination,
            package=original_package, criterion=programme.criterion,
            nomination_pin=programme.nomination.original_nomination,read_access=current_access)
        if (receipt != programme.nomination_receipt or publication != programme.nomination_publication
                or nomination.identity != programme.nomination.original_nomination):
            raise PermissionError("selected confirmation substitutes its actual development nomination custody")
    programme = _reconstruct_entry_programme(programme, calibration, nomination)
    validate_evidence(evidence, programme)
    package = programme.point_design.package
    from .prepared_source_replay import is_prepared_source_result, partition_prepared_source_publications
    if is_prepared_source_result(evidence.source_result):
        scientific_publications, bootstrap_publications = partition_prepared_source_publications(
            writer=writer, publications=evidence.publications)
    else:
        scientific_publications, bootstrap_publications = evidence.publications, ()
    pubs, prefit_refs = dict(scientific_publications), set()
    for _, artifact, materialization_id, _ in package.prefit.publications:
        matches = tuple((pin, publication) for pin, publication in evidence.publications
            if publication.logical.logical_artifact_id == artifact.artifact_id
                and publication.materialization.materialization_id == materialization_id
                and publication.logical.payload_schema == artifact.payload_schema
                and publication.logical.content_sha256 == artifact.sha256
                and publication.materialization.size_bytes == artifact.size_bytes)
        if len(matches) != 1:
            raise PermissionError("selected entry loses an actual original pre-fit reservation/role/selection publication")
        _publication(writer, *matches[0])
        prefit_refs.add(matches[0][0])
    source_refs = matrix_source_publication_references(evidence.source_specification, evidence.source_result, evidence.pipeline)
    if set(pubs) != set(source_refs) | prefit_refs:
        raise PermissionError("selected entry changes its complete original pre-fit and source publication census")
    # The shared source owner replays original pipeline, independent scientific
    # gate methods/configurations, complete result and original receipt closure.
    authenticate_matrix_source_qualification(writer=writer, specification=evidence.source_specification,
        result=evidence.source_result, pipeline=evidence.pipeline, executions=evidence.qualification_executions,
        publications=tuple(sorted((*( (pin, pubs[pin]) for pin in source_refs), *bootstrap_publications),
            key=lambda row: row[0].object_id)), codecs=codecs, read_scope=read_scope,
        consumer_programme=programme, prepared_source_current_access=current_access)

    return programme


def _authenticate_spent_entry(writer, package, plan, task, receipts, codecs):
    """Use the actual entry receipt without rereading its complete source bank."""
    entry = _entry_task(plan)
    receipt = receipts.get(entry.task_id)
    if entry.task_id not in task.dependency_task_ids or receipt is None:
        raise PermissionError("selected worker has no actual successful entry dependency")
    outputs = tuple(value for value in receipt.output_logical_artifacts if value.payload_schema == MatrixSelectedProtectedEntrySeal.SCHEMA)
    if len(outputs) != 1:
        raise PermissionError("selected worker lacks its one actual entry seal output")
    semantic = _semantic_writer(package, plan, writer, codecs)
    raw = _output_payload(semantic, receipt, outputs[0], MAX_PARENT_BYTES)
    seal = decode_canonical_bytes(raw, MatrixSelectedProtectedEntrySeal, maximum_bytes=MAX_PARENT_BYTES)
    if seal.canonical_bytes() != raw:
        raise PermissionError("selected entry seal changes its original canonical bytes")
    return seal


def prepare_selected_matrix(supplier, context, runner):
    """Fresh current authority precedes every original or scientific read."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_bindings import MatrixPreparationOperationConfig, MatrixPreparationOperationConfigV2
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_future import MatrixSelectedFutureConfig, MatrixSelectedFutureConfigV2
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_programme import MatrixSelectedPreparedConfig
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_workers import SelectedProtectedWorker
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_e6_transport_config import (
        MatrixSelectedTransportRootConfig, MatrixSelectedTransportPointConfig,
        MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig,
    )
    from empirical_lawhood.api.recursive_operations import operation_catalog

    if type(runner) is not SelectedProtectedWorker or runner.prepared_scope is not None:
        raise PermissionError("selected preparation requires its installed unprepared worker")
    custody = getattr(supplier, "custody", None)
    if custody is None:
        custody = CurrentIssuedTaskCustody(writer=supplier.writer, reveal_authority_id=supplier.reveal_authority_id)
    elif (type(custody) is not CurrentIssuedTaskCustody or custody.writer is not supplier.writer
            or custody.reveal_authority_id != supplier.reveal_authority_id):
        raise TypeError("shared Matrix custody changes its exact writer or reveal selection")
    package, plan, task = custody.current_task(context, runner)
    receipts, controls = custody.task_inputs(context, task)
    codecs = {kind.SCHEMA: kind for kind in (MatrixSelectedProtectedRootConfig, MatrixSelectedProtectedRootConfigV3, MatrixPreparationOperationConfig,
        MatrixSelectedPreparedConfig, MatrixSelectedFutureConfig, MatrixPreparationOperationConfigV2, MatrixSelectedFutureConfigV2,
        MatrixSelectedTransportRootConfig, MatrixSelectedTransportPointConfig, MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig)}
    manifest = controls.get(context.config.artifact_id)
    kind = None if manifest is None else codecs.get(manifest.logical.payload_schema)
    if kind is None:
        raise PermissionError("selected worker changes its actual registered configuration type")
    config = custody.control_record(manifest, kind, manifest.materialization.size_bytes,
        **_issued_configuration_lane(task))
    if config.fingerprint() != context.config.content_sha256 or config.config_id != context.config.config_id:
        raise PermissionError("selected worker changes its actual issued configuration identity")
    _, _, installed = operation_catalog()
    if runner.phase == "entry":
        if type(config) not in (MatrixSelectedProtectedRootConfigV3, MatrixSelectedTransportRootConfig) or config.phase != "entry" or _entry_task(plan) != task:
            raise PermissionError("selected entry substitutes its actual complete programme task")
        _current_source_qualifications(package, task)
        evidence_kind = MatrixSelectedEntryEvidenceV3
        inputs = tuple(value for value in task.external_inputs if
            (value.expected_payload_schema, value.expected_content_sha256) ==
            (evidence_kind.SCHEMA, config.entry_evidence.object_fingerprint))
        if len(inputs) != 1:
            raise PermissionError("selected entry omits its actual supplied evidence input")
        evidence = _published_input(supplier.writer, context.run_id, inputs[0], evidence_kind, custody=custody)
        if evidence.identity != config.entry_evidence:
            raise PermissionError("selected entry substitutes its declared original evidence")
        _authenticate_entry(supplier.writer, config.programme, evidence, installed,
            source_scan_bytes=context.resource_budget.source_scan_bytes,
            transport_policy=getattr(config, "transport_policy", None),
            transport_calibration=getattr(config, "transport_calibration", None),current_access=getattr(supplier,"current_access",None))
        from .domain_composition.matrix_selected_declarative.derivation import require_evidence_produced_input_parents
        require_evidence_produced_input_parents(supplier.writer, config.produced_input_parents, evidence,read_access=getattr(supplier,"current_access",None))
    else:
        with supplier.writer.verification_scope() as writer:
            seal = _authenticate_spent_entry(writer, package, plan, task, receipts, installed)
            programme_pin = config.programme.identity if type(config) in (MatrixSelectedProtectedRootConfig, MatrixSelectedProtectedRootConfigV3, MatrixSelectedTransportRootConfig) else getattr(config, "programme", None)
            source = config.source if type(config) in (MatrixPreparationOperationConfig, MatrixPreparationOperationConfigV2, MatrixSelectedFutureConfig, MatrixSelectedFutureConfigV2, MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig) else getattr(config, "public_source", None)
            if ((programme_pin is not None and programme_pin != seal.programme)
                    or (source is not None and (source.source_id if hasattr(source, "source_id") else source.source.object_id) not in seal.source_ids)
                    or type(config) in (MatrixSelectedFutureConfig, MatrixSelectedFutureConfigV2, MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig) and (config.point_design, config.frozen_package) != (seal.point_design, seal.package)):
                raise PermissionError("selected worker changes its actual entry-bound source, package or programme")
            if hasattr(config, "transport_policy"):
                original_entry = _entry_task(plan)
                entry_specs = tuple(row for row in original_entry.external_inputs
                    if row.logical_artifact_id == original_entry.capability.config.artifact_id)
                if len(entry_specs) != 1:
                    raise PermissionError("expanded E6 omits its actual entry configuration")
                entry_config = _published_input(writer, context.run_id, entry_specs[0], MatrixSelectedTransportRootConfig, custody=custody)
                if (config.transport_policy, config.transport_calibration) != (entry_config.transport_policy, entry_config.transport_calibration):
                    raise PermissionError("expanded E6 changes its actual entry-bound policy or original calibration")
            writer.require_verification_snapshot()
    if custody.current_task(context, runner) != (package, plan, task):
        raise PermissionError("selected current grant or issued source changed during preparation")
    return runner.with_prepared_scope((context.run_id, context.task_id, context.input_materialization_ids,
        ObjectIdentity.from_record(plan.execution_plan_id, plan)))


class SelectedMatrixRuntimeInputSupplier(CurrentIssuedTaskCustodySupplier):
    def __init__(self, supplier, *, writer, reveal_authority_id=None, custody=None,original_input_access=None,read_access=None):
        if custody is not None and (type(custody) is not CurrentIssuedTaskCustody
                or custody.writer is not writer or custody.reveal_authority_id != reveal_authority_id):
            raise TypeError("selected Matrix custody changes its exact writer or reveal selection")
        if custody is not None and getattr(custody,"original_input_access",None) is not original_input_access:
            raise TypeError("selected Matrix custody substitutes its actual original input scope")
        self.original_input_access=original_input_access
        self.current_access=read_access if original_input_access is None else original_input_access.current_access
        if original_input_access is not None:original_input_access.require_current()
        self.supplier, self.writer, self.reveal_authority_id = supplier, writer, reveal_authority_id
        self.custody = custody if custody is not None else CurrentIssuedTaskCustody(
            writer=writer, reveal_authority_id=reveal_authority_id,original_input_access=original_input_access)

    def resolve_input(self, spec):
        return self.supplier.resolve_input(spec)

    def prepare_selected_matrix(self, context, runner):
        with self.custody.preparation_scope():
            return prepare_selected_matrix(self, context, runner)


def bind_selected_matrix_handoff(handoff, *, writer, reveal_authority_id=None,original_input_access=None,read_access=None):
    """Bind an actual authored selected programme to existing parent preparation."""
    from .recursive_prospective_authoring import RecursiveProspectiveApplicationHandoff
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_e6_transport_config import MatrixSelectedTransportRootConfig

    if type(handoff) is not RecursiveProspectiveApplicationHandoff:
        raise TypeError("selected Matrix binding requires its exact public prospective handoff")
    if not any(type(value.record) in (MatrixSelectedProtectedRootConfigV3, MatrixSelectedTransportRootConfig) and value.record.phase == "entry"
            for value in handoff.compilation.config_inputs):
        raise ValueError("selected Matrix handoff omits its actual source-entry configuration")
    custody = CurrentIssuedTaskCustody(writer=writer, reveal_authority_id=reveal_authority_id,original_input_access=original_input_access)
    ports = []
    for platform in handoff.platform_ports:
        if type(platform.port) is not RecursiveOperationInputPort:
            raise TypeError("selected Matrix handoff changes its exact input port owner")
        supplier = SelectedMatrixRuntimeInputSupplier(platform.port.supplier, writer=writer,
            reveal_authority_id=reveal_authority_id, custody=custody,original_input_access=original_input_access,read_access=read_access)
        ports.append(ExecutablePlatformPort(platform.port_key, RecursiveOperationInputPort(supplier)))
    return replace(handoff, platform_ports=tuple(ports))
