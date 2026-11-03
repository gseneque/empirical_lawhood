# SPDX-License-Identifier: MPL-2.0
"""Authenticate actual C/E3/TRAIN operands and publish their existing E4 banks."""
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import (
    ConfiguredProtectedE3PreparationSelection, configured_preparation_types, validate_selection_science,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_publications import validate_request_programme_inputs
from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_records import NativeTrainingAcquisitionRequest
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_assembly import source_assembly_request_types
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_researcher_programme.e4_inputs import compose_programme_e4_banks
from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import _require_assay
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.api.matrix_sampling_runtime import _original_product_metadata
from empirical_lawhood.api.matrix_selected_e3_e4_runtime import (
    authenticate_selected_e3_assay, authenticate_selected_e3_public_package, authenticate_selected_e3_training_banks,
)
from empirical_lawhood.api.native_training_banks import _read_instance
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import _retained_plans
from empirical_lawhood.api.recursive_operations import operation_catalog
from empirical_lawhood.api.selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest, _read_exact_record
from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticated_programme_inputs
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, derived_outcome_access, lineage_parent_sort_key,
)


@dataclass(frozen=True, slots=True)
class PublishedMatrixProgrammeE4Inputs:
    """Operation-local authenticated bodies and ordinary publication results."""
    original_e3: ConfiguredMatrixSelectedPublicPackage
    original_preparation: ConfiguredProtectedE3PreparationSelection
    original_assay: ScheduledResponseProtocol
    training_request: NativeTrainingAcquisitionRequest
    banks: tuple
    programmes: tuple
    publications: tuple


@dataclass(frozen=True, slots=True)
class _AuthenticatedE4Originals:
    """Already consumed operands, valid only inside their owning read."""
    composed: object
    preparation: object
    assay: object
    training_request: object
    require_current: object


def original_e3_lineage(*, original_e3):
    """Retain the exact produced parent and its original scientific lineage.

    This projection grants no access. Its caller must hold the authenticated
    original-product context while reading or publishing dependent bodies.
    """
    logical = original_e3.publication.logical
    return tuple(sorted({*logical.lineage_parents,
        ArtifactLineageParent(original_e3.record, logical.visibility_ceiling, logical.outcome_access)},
        key=lineage_parent_sort_key))


def prepared_source_lineage(*, original_e3, development_product):
    """Preserve the actual original E3 and completed DEV exposure parents."""
    development_product.__post_init__()
    logical = development_product.publication.logical
    return tuple(sorted({*original_e3_lineage(original_e3=original_e3), *logical.lineage_parents,
        ArtifactLineageParent(development_product.record, logical.visibility_ceiling, logical.outcome_access),
        ArtifactLineageParent(development_product.receipt, logical.visibility_ceiling, logical.outcome_access)},
        key=lineage_parent_sort_key))


@contextmanager
def _original_e3_metadata_context(writer):
    """Reuse immutable original controls while reloading each actual grant."""
    from .current_result_custody import CurrentResultPlanReader
    from empirical_lawhood.infrastructure.artifacts import _has_stock_manifest_reads
    from empirical_lawhood.infrastructure.study_issue import (
        ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_ISSUE_GRANTEE_ID,
    )

    stock = _has_stock_manifest_reads(writer)
    publisher = ExternalIssuedStudyPublisher(artifact_plane=writer,
        authority_store=ExternalStudyOperationAuthorityStore(writer), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
    active = True
    try:
        with (publisher.read_context() if stock else nullcontext(None)) as issued:
            options = ({'_control_reader': CurrentResultPlanReader(writer), '_issued_reader': issued}
                if stock else {})

            def read_metadata(original):
                if not active:
                    raise PermissionError('original E3 metadata context has ended')
                writer.require_active_verification_scope()
                return _original_product_metadata(writer, original, original.record, **options)

            yield read_metadata
    finally:
        active = False


def _require_original_e3_access(*, writer, original_e3, original_products, read_metadata=None):
    """Refresh actual original grants and receipt metadata before export bytes."""
    metadata = tuple(_original_product_metadata(writer, value, value.record)
        if read_metadata is None else read_metadata(value) for value in original_products)
    groups = {}
    for original, value in zip(original_products, metadata, strict=True):
        custody = (value[0], value[1], value[2], value[5])
        if groups.setdefault(original.prior_execution.run_id, custody) != custody:
            raise PermissionError("programme E4 changes original E3 package, authority or capability census")
    # The complete scientific product reader separately authenticates the
    # unfinished continuation when these four products have two producers.
    if len(groups) not in (1, 2):
        raise PermissionError('programme E4 adds unrelated original product producers')
    parents = tuple(sorted({ArtifactLineageParent(pin, value[4].visibility_ceiling, value[4].outcome_access)
        for original, value in zip(original_products, metadata, strict=True)
        for pin in (original.record, original.prior_execution.receipt)}, key=lineage_parent_sort_key))
    access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(value.outcome_access for value in parents))
    ceilings = tuple(value.visibility_ceiling for value in parents)
    logical = original_e3.publication.logical
    if (logical.lineage_parents != parents or logical.parent_visibility_ceilings != ceilings
            or logical.outcome_access is not access or logical.visibility_ceiling is not inherited_visibility(ceilings, access)):
        raise PermissionError("programme E4 original E3 export changes its actual producer lineage or inherited access")


def _require_original_preparation(inputs, public, preparation, assay):
    """Exact scientific operands, independently of their publication custody."""
    design, original = inputs.scientific_design, inputs.commitments
    future, manifest = inputs.phase("e3.calibration"), preparation.manifest
    provenance = inputs.producing_provenance
    retention = getattr(preparation, "retention", None)
    if retention is not None:
        preparation.__post_init__()
        if retention.response_provenance != provenance:
            raise PermissionError("programme E4 changes the actual continued E3 producing source")
        provenance, = manifest.provenances
    scalar = design.training_protocol.scalar_definition
    scalar_pin = ObjectIdentity.from_record(scalar.definition_id, scalar)
    scalar_publication, = (value.publication for value in original.scalar_definitions if value.record == scalar_pin)
    root = preparation.root
    if (root.system is None or root.experiment is None
            or root.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.system.world.maximum_evidence is EvidenceCeiling.NON_PROMOTABLE):
        raise ValueError("programme E4 requires its genuine original E3 numerical scientific root")
    if (public.specification != design.e3 or preparation.mathematical_protocol != design.training_protocol.mathematical_protocol
            or manifest.reservation != future.reservation or manifest.native_specification != future.native_specification
            or manifest.provenances != (provenance,) or manifest.audit != inputs.exposure_audit
            or manifest.audit_publication != original.exposure_audit.publication
            or manifest.reservation_publication != original.phase("e3.calibration").reservation.publication
            or manifest.scalar_definition != scalar or manifest.scalar_definition_publication != scalar_publication
            or assay not in preparation.protocols):
        raise PermissionError("programme E4 substitutes original E3/TRAIN/C preparation operands or publications")
    validate_selection_science(public.specification, public.allocation, preparation)
    _require_assay(assay, design.training_assay)
    prototype = assay.public_source.coordinate
    for coordinate in design.e4_preparation_coordinates:
        if (coordinate.member, coordinate.primary_view, coordinate.fine_view, coordinate.clock_id, coordinate.q,
                coordinate.initial_state_rule_id, coordinate.preparation_rule_id) != (
                prototype.member, prototype.primary_view, prototype.fine_view, prototype.clock_id, prototype.q,
                prototype.initial_state_rule_id, prototype.preparation_rule_id):
            raise PermissionError("programme E4 substitutes original E3 paired numerical/member/initial conventions")
    reference, = (value for value in preparation.sources if value.root_id == assay.public_source.root.root_id)
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    assay.public_source.validate_source(index.resolve(reference))


def _original_assay_provider_publications(*, writer, public, original_products, assay, template, require_current,
        read_metadata=None):
    """Resolve the original forecast's exact persisted input publications.

    Exported assay controls and C's pre-E3 instrument publication retain their
    own custody. They cannot substitute the original run's provider copies.
    This bounded metadata join grants no access and replays no scientific work.
    """
    from .current_result_custody import authenticate_current_execution_plan
    from .matrix_selected_e3_family import selected_e3_product_family
    from .matrix_selected_producer_scope import _installed_task
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges

    if not callable(require_current):
        raise TypeError("programme E4 original inputs require their current access guard")
    require_current()
    selected, = (value for value in original_products if value.record == ObjectIdentity.from_record(
        public.models.record_id, public.models))
    binding = selected.prior_execution
    package, issued, _, _, _, _ = (_original_product_metadata(writer, selected, selected.record)
        if read_metadata is None else read_metadata(selected))
    from .retained_e3_evidence import current_e3_evidence
    evidence = current_e3_evidence(writer)
    plan = (evidence.reader.authenticate_execution_plan(package=package, issued=issued, run_id=binding.run_id)
        if evidence is not None else authenticate_current_execution_plan(
            package=package, issued=issued, run_id=binding.run_id, writer=writer))
    if (ObjectIdentity.from_record(package.package_id, package) != binding.package
            or ObjectIdentity.from_record(plan.execution_plan_id, plan) != binding.execution_plan):
        raise PermissionError("programme E4 original inputs change their actual issued package or plan")
    family = selected_e3_product_family(public.specification)
    declarations = {value.capability_key: value for value in family.operation_declarations()}
    keys = {family.namespace + '.physical-forecast'}
    if family.configured:
        keys.add(family.namespace + '.retained-physical-forecast')
    tasks = tuple(value for value in plan.tasks if value.capability.capability_key in keys
        and any(spec.expected_payload_schema == assay.SCHEMA
            and spec.expected_content_sha256 == assay.fingerprint() for spec in value.external_inputs))
    if len(tasks) != 1:
        raise PermissionError("programme E4 original inputs require one exact installed forecast task")
    task, = tasks
    declaration = declarations[task.capability.capability_key]
    _installed_task(task, package, declaration)
    scientific = validated_task_scientific_input_edges(task)
    assay_specs = tuple(value for value in task.external_inputs
        if value.expected_payload_schema == assay.SCHEMA and value.expected_content_sha256 == assay.fingerprint())
    template_specs = tuple(value for value in task.external_inputs
        if (value.logical_artifact_id, value.expected_payload_schema, value.expected_content_sha256,
            value.expected_media_type) == (template.artifact_id, template.payload_schema,
                template.sha256, template.media_type))
    if len(assay_specs) != 1 or len(template_specs) != 1:
        raise PermissionError("programme E4 original inputs lose their exact assay or instrument census")
    publications = []
    for spec, size in ((assay_specs[0], len(assay.canonical_bytes())), (template_specs[0], template.size_bytes)):
        expected = (spec.logical_artifact_id, spec.expected_payload_schema, spec.expected_content_sha256,
            spec.expected_media_type, spec.expected_outcome_access, spec.expected_visibility_ceiling)
        edges = tuple(value for value in scientific
            if value.operational_logical_artifact_id == spec.logical_artifact_id)
        if (any(value is None for value in expected) or type(size) is not int or size <= 0
                or spec.expected_size_bytes not in (None, size) or len(edges) != 1
                or size > edges[0].maximum_size_bytes):
            raise PermissionError("programme E4 original inputs change their frozen metadata or scientific bounds")
        relative, _, _ = provider_input_location(writer, binding.run_id, spec.logical_artifact_id)
        require_current()
        manifest = writer.read_manifest(relative)
        if (manifest.materialization.relative_path != relative or manifest.materialization.size_bytes != size
                or (manifest.logical.logical_artifact_id, manifest.logical.payload_schema,
                    manifest.logical.content_sha256, manifest.logical.media_type, manifest.logical.outcome_access,
                    manifest.logical.visibility_ceiling) != expected):
            raise PermissionError("programme E4 original inputs substitute their exact provider publication")
        require_current()
        publications.append(_publication_from_manifest(writer, manifest))
        require_current()
    return tuple(publications)


def _preparation_kind(handle):
    kinds = tuple(kind for kind in configured_preparation_types()
        if (handle.record.object_schema, handle.record.object_version) == (kind.SCHEMA, kind.VERSION))
    if len(kinds) != 1:
        raise ValueError('programme E4 requires an exact supported original preparation edition')
    return kinds[0]


def _recorded_training_operands(writer, locator):
    """Read the actual pinned TRAIN request without reconstructing its graph.

    These operands supply no completion or execution authority. E3's original
    fit receipts and native bank seals independently bind this acquisition.
    """
    from hashlib import sha256
    from .experiment_execution_read import load_development_execution_controls
    from .retained_e3_evidence import current_e3_evidence
    from empirical_lawhood.infrastructure.recursive_custody import read_exposed_recursive_payload
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    evidence = current_e3_evidence(writer)
    if evidence is not None:
        evidence.require_access()
        writer = evidence.writer
    cached = None if evidence is None else evidence.training.get(locator)
    if cached is not None:
        writer.require_active_verification_scope()
        return cached
    prefix = locator.authored_directory
    packet, run, plan, _, _, _ = load_development_execution_controls(
        directory=writer.root.resolve(prefix, for_write=False), artifact_writer=writer)
    if ObjectIdentity.from_record(packet.packet_id, packet) != locator.packet:
        raise PermissionError('programme E4 changes its actual original TRAIN packet')
    # Packet member names and owning record identifiers are different contracts.
    # The control reader authenticates the member bytes; join the locator to the
    # decoded plan's actual identifier, schema, revision and fingerprint.
    if ObjectIdentity.from_record(plan.execution_plan_id, plan) != locator.execution_plan:
        raise PermissionError('programme E4 changes its pinned original TRAIN execution plan')
    if run.run_plan_id != locator.run_id or run.draft != packet.draft:
        raise PermissionError('programme E4 changes its original TRAIN run')
    members = {row.filename: row for row in packet.members}
    payloads = {}

    def read(name):
        member = members[name]
        manifest = writer.read_manifest(prefix + '/' + name)
        raw = read_exposed_recursive_payload(writer, manifest, maximum_bytes=member.size_bytes)
        if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.identity.object_fingerprint:
            raise PermissionError('programme E4 changes an original TRAIN request member')
        payloads[name] = raw
        return raw

    read('experiment-specification.json')
    raw = read('experiment-instance.json')
    instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
    for reference in instance.sources:
        if (reference.object_schema, reference.object_version) == (
                NativeTrainingAcquisitionRequest.SCHEMA, NativeTrainingAcquisitionRequest.VERSION):
            read('experiment-source-' + sha256(reference.object_id.encode()).hexdigest() + '.json')
    specification, request, _ = _read_instance(payloads)
    result = specification, request
    if evidence is not None:
        evidence.training[locator] = result
    return result


@contextmanager
def authenticated_programme_e4_banks(*, artifact_writer, input_commitments, original_e3,
        original_preparation, original_assay, original_products, native_training_locator, maximum_source_bytes,
        _retain_originals=False):
    """Authenticate actual C/E3/TRAIN through the last dependent publication.

    The returned pure view has no source, issue or access authority. The caller
    must keep this context open while consuming its shared parents or publishing
    derived metadata, and must perform its own current source admission.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
        MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput, MatrixProgrammeProducedInput,
    )
    if type(maximum_source_bytes) is not int or maximum_source_bytes < 1:
        raise ValueError("programme E4 requires an explicit positive source byte budget")
    for selected, kind, handle in ((input_commitments, MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput),
            (original_e3, ConfiguredMatrixSelectedPublicPackage, MatrixProgrammeProducedInput),
            (original_preparation, _preparation_kind(original_preparation), MatrixProgrammePublishedInput),
            (original_assay, ScheduledResponseProtocol, MatrixProgrammePublishedInput)):
        if type(selected) is not handle:
            raise TypeError("programme E4 requires its actual typed original publication handles")
        selected.__post_init__()
        selected.require_kind(kind)
    if (type(original_products) is not tuple or len(original_products) != 4
            or any(type(value) is not MatrixSelectedOriginalProduct for value in original_products)
            or tuple(value.record.object_id for value in original_products) !=
                tuple(sorted({value.record.object_id for value in original_products}))):
        raise ValueError("programme E4 requires the four exact distinct original E3 product locators")
    for value in original_products:
        value.__post_init__()
    if type(native_training_locator) is not MatrixFiniteDtTrainingLocator:
        raise TypeError("programme E4 requires its actual native TRAIN locator")
    native_training_locator.__post_init__()
    selected_records = ((original_e3, ConfiguredMatrixSelectedPublicPackage),
        (original_preparation, _preparation_kind(original_preparation)),
        (original_assay, ScheduledResponseProtocol))
    original_bytes = sum(value.publication.materialization.size_bytes for value, _ in selected_records)
    if original_bytes >= maximum_source_bytes:
        raise ValueError("programme E4 original operands exceed the selected source byte limit")
    # Callers can retain a separate publication scope while these original
    # operands stay open. Give the effect-free reader its own verification
    # state so entering it cannot turn the caller's writer into a read view.
    with artifact_writer.verification_scope() as original_reader, original_reader.read_context() as writer, ExitStack() as lifetime:
        read_metadata = lifetime.enter_context(_original_e3_metadata_context(writer))

        def require_current():
            _require_original_e3_access(writer=writer, original_e3=original_e3,
                original_products=original_products, read_metadata=read_metadata)

        require_current()
        records = []
        for selected, kind in selected_records:
            record = _read_exact_record(writer, selected.publication, kind,
                maximum_bytes=maximum_source_bytes - original_bytes + selected.publication.materialization.size_bytes)
            pin = (record.identity if kind is ConfiguredMatrixSelectedPublicPackage else
                ObjectIdentity.from_record(record.selection_id if kind in configured_preparation_types()
                    else record.protocol_id, record))
            selected.require_record(record, pin)
            records.append(record)
        public, preparation, assay = records
        from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled
        if getattr(preparation, 'retention', None) is not None and scientific_reconstruction_enabled():
            from .configured_e3_retained_read import retained_execution_read
            lifetime.enter_context(retained_execution_read(writer=writer, retention=preparation.retention))
        with authenticated_programme_inputs(writer=writer, commitment=input_commitments,
                maximum_source_bytes=maximum_source_bytes - original_bytes) as inputs:
            from empirical_lawhood.infrastructure.matrix_completed_source import original_e3_commitment, original_e3_programme_inputs
            e3_inputs = lifetime.enter_context(original_e3_programme_inputs(writer=writer, inputs=inputs,
                maximum_source_bytes=maximum_source_bytes - original_bytes))
            e3_commitment = original_e3_commitment(writer, inputs, input_commitments)
            _require_original_preparation(e3_inputs, public, preparation, assay)
            # Authenticate the supplied locator and original request, not an
            # executable object synthesized from a product's observed fields.
            directory_train = writer.root.resolve(native_training_locator.authored_directory, for_write=False)
            if scientific_reconstruction_enabled():
                packet, draft, _, payloads = load_authored_wave(directory=directory_train, artifact_writer=writer, lazy_payloads=True)
                training_specification, training_request, _ = _read_instance(payloads)
                run, plan, _ = _retained_plans(payloads, draft)
                locator = MatrixFiniteDtTrainingLocator(native_training_locator.authored_directory, run.run_plan_id,
                    ObjectIdentity.from_record(packet.packet_id, packet), ObjectIdentity.from_record(plan.execution_plan_id, plan))
                if locator != native_training_locator:
                    raise PermissionError("programme E4 changes the exact original TRAIN packet/run/plan or C publication")
                del packet, draft, payloads, run, plan
            else:
                locator = native_training_locator
                training_specification, training_request = _recorded_training_operands(writer, locator)
            training_inputs = e3_inputs
            if training_request.input_commitments != e3_commitment:
                from empirical_lawhood.infrastructure.matrix_retained_training import authenticated_retained_training_source
                retained, training_inputs = lifetime.enter_context(authenticated_retained_training_source(
                    writer=writer, inputs=e3_inputs, maximum_source_bytes=maximum_source_bytes - original_bytes))
                if (retained.training_locator != locator or retained.input_commitments != training_request.input_commitments
                        or retained.export_adoption.request != training_request.identity
                        or retained.export_adoption.specification != training_specification.identity):
                    raise PermissionError('programme E4 changes its exact retained TRAIN source lineage')
            validate_request_programme_inputs(training_request, training_inputs)
            coordinates = inputs.phase("e4.development").reservation.allocation.coordinates
            authenticate_selected_e3_public_package(writer=writer, public=public, upstream_products=original_products,
                codecs=operation_catalog()[2], response_criterion=preparation.mathematical_protocol,
                prefix_policies=(assay.public_source.policy,), original_preparation=preparation,
                downstream_coordinates=coordinates)
            authenticate_selected_e3_training_banks(public=public, upstream_products=original_products,
                training_specification=training_specification, training_request=training_request, writer=writer)
            template = inputs.scientific_design.training_assay.array_artifact
            assay_publication, template_publication = _original_assay_provider_publications(writer=writer,
                public=public, original_products=original_products, assay=assay, template=template,
                require_current=require_current, read_metadata=read_metadata)
            criterion_publication = authenticate_selected_e3_assay(public=public, upstream_products=original_products,
                assay=assay, assay_publication=assay_publication,
                template_publication=template_publication, criterion=preparation.mathematical_protocol, writer=writer)
            composed = compose_programme_e4_banks(inputs, original_e3=public, criterion_publication=criterion_publication)
            if _retain_originals:
                # Publication needs these exact operands. Keep their existing
                # objects and current guards instead of decoding copies through
                # the separate unscoped publication writer.
                yield _AuthenticatedE4Originals(composed, preparation, assay,
                    training_request, require_current)
            else:
                del records, public, preparation, assay, record
                del training_specification, training_request, training_inputs
                yield composed
            require_current()


def programme_e4_bank_requests(composed, *, original_e3, prefix):
    """Use one exact publication contract for new and retained bank metadata."""
    parents = original_e3_lineage(original_e3=original_e3)
    access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(value.outcome_access for value in parents))
    ceilings = tuple(value.visibility_ceiling for value in parents)
    return tuple(ArtifactWriteRequest("programme-e4." + name + "." + record.fingerprint(),
        prefix + "/" + phase.lower() + "." + name + ".json", record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json",
        "programme-e4." + composed.inputs.commitments.record_id, prefix, record.canonical_bytes(),
        inherited_visibility(ceilings, access), ceilings, access, lineage_parents=parents)
        for name, values in (("bank", composed.banks), ("programme", composed.programmes))
        for phase, record in values)


@contextmanager
def published_programme_e4_inputs(*, request, project_root, artifact_writer, metadata_directory, execution):
    """Derive no allocation or streams; authenticate all original joins first.

    The actual original E3 forecast supplies the criterion publication. Banks
    therefore have the same identities in DEV/CAL/CONF callers regardless of
    the selected metadata output directory. No recipe index is manufactured.
    """
    if type(request) not in source_assembly_request_types():
        raise TypeError("programme E4 composition requires its exact current C-backed source request")
    request.__post_init__()
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    directory = Path(metadata_directory)
    plane = Path(artifact_writer.root.contract.canonical_path)
    if (not directory.is_absolute() or directory != directory.resolve(strict=False) or directory == plane
            or not directory.is_relative_to(plane) or directory.is_relative_to(root)):
        raise ValueError("programme E4 metadata requires its exact separate guarded destination")
    prefix = directory.relative_to(plane).as_posix()
    artifact_writer.root.resolve(prefix + "/development.bank.json", for_write=True)
    budget = request.source_budget
    original_bytes = sum(value.publication.materialization.size_bytes
        for value in (request.original_e3, request.original_preparation, request.original_assay))
    if original_bytes > budget.memory_bytes:
        raise ValueError("programme E4 original operands exceed the selected memory byte limit")
    with authenticated_programme_e4_banks(artifact_writer=artifact_writer,
            input_commitments=request.input_commitments, original_e3=request.original_e3,
            original_preparation=request.original_preparation, original_assay=request.original_assay,
            original_products=request.original_products, native_training_locator=request.native_training_locator,
            maximum_source_bytes=budget.source_scan_bytes, _retain_originals=True) as originals:
        composed = originals.composed
        provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
        if provenance != composed.inputs.producing_provenance or provenance.observed_git_head != admitted.implementation_commit:
            raise ValueError("programme E4 changes C's actual selected numerical/source provenance")
        originals.require_current()
        writes = programme_e4_bank_requests(composed, original_e3=request.original_e3, prefix=prefix)
        for value in writes:
            _metadata_record_size(artifact_writer, len(value.payload))
        total = sum(len(value.payload) for value in writes)
        if total > budget.output_bytes or total + original_bytes > budget.memory_bytes:
            raise ValueError("programme E4 bank metadata exceeds its selected output or materialized byte limit")
        require_admitted_target_source_current(root, admitted)
        originals.require_current()
        results = artifact_writer.write_batch(tuple(writes))
        publications = tuple(_publication_from_manifest(artifact_writer, artifact_writer.read_manifest(value.materialization.relative_path))
            for value in results)
        yield PublishedMatrixProgrammeE4Inputs(composed.original_e3, originals.preparation,
            originals.assay, originals.training_request,
            composed.banks, composed.programmes, publications)
        require_admitted_target_source_current(root, admitted)


def publish_programme_e4_inputs(*, request, project_root, artifact_writer, metadata_directory, execution):
    """Standalone publication with its final original-input guards before return."""
    with published_programme_e4_inputs(request=request, project_root=project_root,
            artifact_writer=artifact_writer, metadata_directory=metadata_directory, execution=execution) as result:
        return result
