# SPDX-License-Identifier: MPL-2.0
"""Exact pending-roster inspection and ordinary canonical manifest verification.

These declarations belong to the actual functions invoked by the finite-dt
materializer. They do not register another scientific gate or generic ETL path.
Both current pending-roster families require their actual committed
transformation manifest at the selected dataset control scope's fixed member.
"""
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_pipeline as finite_dt_rows_owner
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import BLIND, PROSPECTIVE
from empirical_lawhood.infrastructure import dataset_evidence
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.dataset_manifests import DatasetCapabilityKind, DatasetTransformationManifest
from empirical_lawhood.planning.datasets import EvidenceReference, EvidenceReferenceKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityManifest, CapabilityPermission, CapabilityRegistry
from empirical_lawhood.runtime.datasets import (
    DatasetCapabilityLimits, DatasetCapabilityRegistry, DatasetEvidenceOwnerKind,
    DatasetEvidenceVerificationRequest, DatasetEvidenceVerifierRegistration,
    DatasetFormatInspectorRegistration, DatasetTransformRegistration,
)

MANIFEST_FILENAME = "dataset-transformation.json"


def select_rows_owner(row_kind):
    """Select one exact current row type, without a default family."""
    from empirical_lawhood.adapters.methods import matrix_prepared_source_pipeline as prepared
    if row_kind is finite_dt_rows_owner.MatrixFiniteDtPendingSourceRows:
        return finite_dt_rows_owner
    if row_kind is prepared.MatrixPreparedPendingSourceRows:
        return prepared
    raise TypeError('pending-source metadata requires an exact installed source row family')


def dataset_registries(resources, *, maximum_rows, row_kind):
    """Bind actual typed reader, identity transform and existing stable verifier."""
    rows_owner = select_rows_owner(row_kind)
    selected_namespace = rows_owner.NAMESPACE
    inspector_key = selected_namespace + ".pending-source-inspector"
    verifier_key = selected_namespace + ".canonical-dataset-evidence"
    resources.__post_init__()
    if (type(maximum_rows) is not int or maximum_rows < 1
            or type(resources.source_scan_bytes) is not int or resources.source_scan_bytes < 2
            or type(resources.output_bytes) is not int or resources.output_bytes < 1):
        raise ValueError("pending-source declarations require explicit finite bytes and complete row capacity")
    transform = rows_owner.transform_capability(resources)
    common = dict(capability_version="1.0.0", kind=CapabilityKind.SOURCE,
        config_schema=transform.config_schema,
        config_schema_sha256=transform.config_schema_sha256,
        permissions=(CapabilityPermission.READ_EXTERNAL_ARTIFACTS,),
        maximum_evidence_ceiling=EvidenceCeiling.MEASUREMENT, maximum_outcome_access=BLIND,
        resource_ceiling=resources, deterministic=True, seed_required=False,
        language_id="python", runtime_id="python-current", requires_clean_commit=False,
        requires_active_mount=True, requires_network=False)
    inspector = CapabilityManifest(capability_key=inspector_key,
        input_schema_ids=(row_kind.SCHEMA,),
        output_schema_ids=(row_kind.SCHEMA,),
        conformance_check_ids=("finite-dt-exact-typed-pending-source-publication",),
        implementation_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), **common)
    verifier_capability = CapabilityManifest(capability_key=verifier_key,
        input_schema_ids=dataset_evidence.EXTERNAL_DATASET_EVIDENCE_SCHEMA_IDS,
        output_schema_ids=("empirical-lawhood/runtime/dataset-evidence-verification",),
        conformance_check_ids=("dataset-evidence-stable-two-pass-canonical-manifest",),
        implementation_sha256=sha256(Path(dataset_evidence.__file__).read_bytes()).hexdigest(), **common)
    inspector_registration = DatasetFormatInspectorRegistration(inspector, ("application/json",),
        (rows_owner.FORMAT_ID,), DatasetCapabilityLimits(resources.source_scan_bytes, resources.output_bytes,
            maximum_rows, 1, 0))
    verifier = DatasetEvidenceVerifierRegistration(verifier_key, verifier_capability,
        dataset_evidence.EXTERNAL_DATASET_EVIDENCE_SCHEMA_IDS,
        DatasetCapabilityLimits(resources.source_scan_bytes // 2, resources.output_bytes, 2, 2, 0))
    transform_registration = DatasetTransformRegistration(transform, ("application/json",), ("application/json",),
        (rows_owner.FORMAT_ID,), (rows_owner.FORMAT_ID,),
        DatasetCapabilityLimits(resources.source_scan_bytes, resources.output_bytes, maximum_rows, 2, 0))
    capabilities = CapabilityRegistry(selected_namespace + ".dataset-capabilities",
        tuple(sorted((inspector, verifier_capability, transform), key=lambda value: value.registry_id)))
    datasets = DatasetCapabilityRegistry(selected_namespace + ".dataset-registrations", (), (inspector_registration,),
        (transform_registration,), (), (), (verifier,))
    return capabilities, datasets


def authenticate_dataset_contract(*, writer, profile, registry, capabilities, request, rows, rule, source_publication):
    """Verify the actual published manifest through its real registered reader.

    The metadata declares expected scope/outputs; it creates no verified Dataset
    materialization, scientific result or decision. The operational grant is
    still replayed independently by the original dataset authority owner.
    """
    rows_owner = select_rows_owner(type(rows))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    expected_capabilities, expected_registry = dataset_registries(profile.resource_ceiling, maximum_rows=len(rows.rows), row_kind=type(rows))
    if (registry != expected_registry or capabilities != expected_capabilities
            or profile.source_format_profile_id != rows_owner.FORMAT_ID
            or profile.transform_edges[0].destination_format_profile_id != rows_owner.FORMAT_ID):
        raise PermissionError("finite-dt source substitutes the actual installed pending inspector/transform/evidence verifier")
    relative = request.control_write_scope.relative_prefix + "/" + MANIFEST_FILENAME
    retained = writer.read_manifest(relative)
    if retained.materialization.size_bytes > expected_registry.evidence_verifiers[0].limits.max_input_bytes:
        raise PermissionError("finite-dt dataset manifest exceeds its selected stable verifier read bound")
    publication = _publication_from_manifest(writer, retained)
    authenticate_publication(writer, publication)
    if (retained.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or retained.logical.media_type != "application/json" or retained.logical.outcome_access is not BLIND
            or retained.logical.visibility_ceiling is not PROSPECTIVE):
        raise PermissionError("finite-dt dataset manifest loses its actual blind canonical publication")
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False),
        maximum_bytes=retained.materialization.size_bytes)
    manifest = decode_canonical_bytes(raw, DatasetTransformationManifest, maximum_bytes=len(raw))
    manifest_pin = ObjectIdentity.from_record(manifest.manifest_id, manifest)
    if raw != manifest.canonical_bytes() or manifest_pin != profile.dataset_transformation_manifest or manifest_pin != request.manifest:
        raise PermissionError("finite-dt source changes its actual signed transformation manifest")
    inspector, = expected_registry.inspectors
    verifier, = expected_registry.evidence_verifiers
    transform, = expected_registry.transforms
    config = CapabilityConfigRef(rule.record_id, rule.SCHEMA, transform.capability.config_schema_sha256,
        rule.fingerprint(), rule.record_id)
    expected = {
        DatasetCapabilityKind.INSPECTOR: ObjectIdentity.from_record(inspector.capability_key, inspector.capability),
        DatasetCapabilityKind.EVIDENCE_VERIFIER: ObjectIdentity.from_record(verifier.registry_id, verifier),
        DatasetCapabilityKind.TRANSFORM: ObjectIdentity.from_record(transform.capability_key, transform.capability),
        DatasetCapabilityKind.CONFIG: ObjectIdentity.from_record(config.config_id, config),
    }
    selected = {binding.kind: binding.implementation for binding in manifest.capabilities}
    if any(selected.get(kind) != value for kind, value in expected.items()):
        raise PermissionError("finite-dt manifest binds an unimplemented or substituted dataset reader")
    from empirical_lawhood.planning.datasets import DatasetSelectorKind, DatasetSelectorRef
    source_scopes = tuple(value for value in request.source_scopes
        if value.storage_root.object_id == source_publication.materialization.storage_root_id
        and (source_publication.materialization.relative_path == value.relative_prefix
            or source_publication.materialization.relative_path.startswith(value.relative_prefix + "/")))
    root_pin = ObjectIdentity.from_record(writer.root.contract.storage_root_id, writer.root.contract)
    if (len(source_scopes) != 1 or len(manifest.inputs) != 1 or len(manifest.outputs) != 1
            or any(value.storage_root != root_pin for value in
                (*request.source_scopes, request.destination_scope, request.control_write_scope))):
        raise PermissionError("finite-dt manifest changes its complete actual source/root/scope census")
    source, output = manifest.inputs[0], manifest.outputs[0]
    selector = DatasetSelectorRef(source.selector.selector_id, DatasetSelectorKind.COMPLETE_RELEASE,
        rows.SCHEMA, rows.fingerprint(), True)
    parent = _pending_materialization(source_publication, rows, selector,
        materialization_id=source.materialization.object_id, release_id=manifest.release_id)
    expected_parent = ObjectIdentity.from_record(parent.materialization_id, parent)
    cutoff = manifest.causal_contract.information_cutoff
    if (source.scope != source_scopes[0] or source.selector != selector or source.materialization != expected_parent
            or source.selector_manifest_scope is not None or source.selector_manifest_byte_size is not None
            or source.selected_members or manifest.destination_scope != request.destination_scope
            or manifest.control_write_scope != request.control_write_scope
            or manifest.work_envelope != request.work_envelope
            or output.parent_materialization_ids != (parent.materialization_id,)
            or output.relative_locator != profile.output_relative_locator
            or output.expected_physical_sha256 != rows.fingerprint() or output.output_schema != rows.SCHEMA
            or output.media_type != "application/json" or output.format_profile_id != rows_owner.FORMAT_ID
            or output.expected_byte_count_minimum != len(rows.canonical_bytes())
            or output.expected_byte_count_maximum != len(rows.canonical_bytes()) or output.expected_file_count != 1
            or output.expected_row_count_minimum != len(rows.rows) or output.expected_row_count_maximum != len(rows.rows)
            or output.outcome_access is not BLIND or output.visibility_ceiling is not PROSPECTIVE
            or manifest.outcome_access is not BLIND or manifest.visibility_ceiling is not PROSPECTIVE
            or ObjectIdentity.from_record(cutoff.cutoff_id, cutoff) != profile.causal_cutoff
            or manifest.split_contract.independent_unit_field_ids != (profile.physical_unit_field_id,)
            or manifest.comparison_targets or manifest.exception_codes):
        raise PermissionError("finite-dt manifest changes actual source/parent/output/cutoff/whole-unit expectations")
    reference = EvidenceReference(manifest.manifest_id, EvidenceReferenceKind.MANIFEST, manifest.SCHEMA,
        manifest.fingerprint(), retained.materialization.storage_root_id, relative)
    verification_request = DatasetEvidenceVerificationRequest(DatasetEvidenceOwnerKind.RELEASE, manifest.release_id,
        reference, None, None, None, None, None, None)
    implementation = dataset_evidence.ExternalDatasetEvidenceVerifier(verifier, (writer.root,))
    verified = implementation.verify(verification_request, maximum_bytes=len(raw))
    if not verified.validates(verification_request):
        raise PermissionError("actual finite-dt dataset manifest failed registered stable canonical evidence verification")
    return manifest


def inspect_pending_source(*, writer, programme, bank, rows, rule, publication, registration):
    """Actual read-only inspector used before the identity transform writes."""
    rows_owner = select_rows_owner(type(rows))
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import _read_rows
    _, expected = dataset_registries(registration.capability.resource_ceiling, maximum_rows=len(rows.rows), row_kind=type(rows))
    if registration != expected.inspectors[0]:
        raise PermissionError("pending-source inspector differs from its actual implemented owner")
    rows_owner.validate_source_rows(programme, bank, rows, rule)
    return _read_rows(writer, publication, rows)


def make_dataset_manifest(*, namespace, source_publication, output_relative_path, rows, rule, cutoff,
        source_scope, destination_scope, control_scope, envelope, runtime, environment):
    """Declare one exact expected identity transform using actual owner bindings.

    Runtime/environment ArtifactIdentity values name caller-selected original
    publications. The caller authenticates/publishes their actual bodies; this
    pure grammar does not execute or assert verified dataset custody for them.
    """
    rows_owner = select_rows_owner(type(rows))
    from empirical_lawhood.planning import dataset_manifests as dm
    from empirical_lawhood.planning.datasets import DatasetSelectorKind, DatasetSelectorRef
    from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
    from empirical_lawhood.kernel.time import CausalPhase
    _, datasets = dataset_registries(envelope.resources, maximum_rows=len(rows.rows), row_kind=type(rows))
    inspector, = datasets.inspectors
    verifier, = datasets.evidence_verifiers
    transform, = datasets.transforms
    selector = DatasetSelectorRef("selector." + namespace, DatasetSelectorKind.COMPLETE_RELEASE,
        rows.SCHEMA, rows.fingerprint(), True)
    source = source_publication
    materialization = _pending_materialization(source, rows, selector,
        materialization_id="dataset-source." + namespace, release_id="release." + namespace)
    config = CapabilityConfigRef(rule.record_id, rule.SCHEMA, transform.capability.config_schema_sha256,
        rule.fingerprint(), rule.record_id)
    records = ((dm.DatasetCapabilityKind.INSPECTOR, inspector.capability, inspector.capability_key),
        (dm.DatasetCapabilityKind.EVIDENCE_VERIFIER, verifier, verifier.registry_id),
        (dm.DatasetCapabilityKind.TRANSFORM, transform.capability, transform.capability_key),
        (dm.DatasetCapabilityKind.CONFIG, config, config.config_id),
        (dm.DatasetCapabilityKind.RUNTIME, runtime, runtime.artifact_id),
        (dm.DatasetCapabilityKind.ENVIRONMENT, environment, environment.artifact_id))
    bindings = tuple(dm.DatasetCapabilityBinding("binding." + namespace + "." + kind.value.lower(), kind,
        identifier, ObjectIdentity.from_record(identifier, record)) for kind, record, identifier in records)
    fields = tuple(dm.DatasetFieldContract(name, column, index, dm.DatasetFieldDataType.STRING, role,
        None, None, None, CausalPhase.PREPARATION, BLIND, PROSPECTIVE, False)
        for index, (name, column, role) in enumerate((
            ("physical-unit", "group_id", dm.DatasetFieldRole.INDEPENDENT_UNIT),
            ("invalid-disposition", "invalid_disposition", dm.DatasetFieldRole.VALIDITY),
            ("root", "root_id", dm.DatasetFieldRole.NESTED_OBSERVATION))))
    fields += (dm.DatasetFieldContract("requested-action-status", "requested_action_status", 3,
        dm.DatasetFieldDataType.STRING, dm.DatasetFieldRole.REQUESTED_ACTION, "1", "declared-metadata-status",
        cutoff.clock_id, CausalPhase.ACTION_REQUESTED, BLIND, PROSPECTIVE, False),
        dm.DatasetFieldContract("receiver-status", "receiver_status", 4, dm.DatasetFieldDataType.STRING,
        dm.DatasetFieldRole.RECEIVER, "1", "declared-metadata-status", cutoff.clock_id, CausalPhase.RECEIVER,
        BLIND, PROSPECTIVE, False))
    parent = ObjectIdentity.from_record(materialization.materialization_id, materialization)
    output = dm.DatasetOutputContract("output." + namespace, "dataset-output." + namespace,
        dm.DatasetOutputRole.CANONICAL_SOURCE, output_relative_path, rows.SCHEMA, "application/json", rows_owner.FORMAT_ID,
        tuple(sorted(fields, key=lambda value: value.field_id)), (parent.object_id,), rows.fingerprint(),
        len(rows.canonical_bytes()), len(rows.canonical_bytes()), 1, len(rows.rows), len(rows.rows), BLIND, PROSPECTIVE)
    manifest = dm.DatasetTransformationManifest("transformation." + namespace, "release." + namespace,
        (dm.DatasetTransformInput("input." + namespace, parent, source_scope, selector, None, None, ()),),
        destination_scope, control_scope, tuple(sorted(bindings, key=lambda value: value.binding_id)), (output,), (),
        dm.DatasetSplitContract("split." + namespace, "matrix-finite-dt.complete-declared-whole-groups",
            ("physical-unit",), ("root",), ("declared",), (), BLIND, True),
        dm.DatasetCausalContract("causal." + namespace, cutoff, (), ("requested-action-status",),
            ("receiver-status",), False, False),
        (dm.DatasetExpectedInvariant("invariant." + namespace, dm.DatasetInvariantKind.PARENT_CLOSED,
            (parent.object_id,), rule.record_id, True),), envelope, BLIND, PROSPECTIVE, ())
    metadata = ((parent, materialization), *tuple((ObjectIdentity.from_record(identifier, record), record)
        for _, record, identifier in records))
    return manifest, metadata


def _pending_materialization(source, rows, selector, *, materialization_id, release_id):
    """Exact metadata projection; ordinary dataset custody is not fabricated."""
    rows_owner = select_rows_owner(type(rows))
    from empirical_lawhood.planning.datasets import (
        CustodyState, DatasetEvidenceClass, DatasetMaterialization, DatasetMaterializationClass,
    )
    return DatasetMaterialization(materialization_id, release_id,
        DatasetMaterializationClass.METADATA_OBSERVATION, DatasetEvidenceClass.METADATA_ONLY, BLIND,
        source.materialization.storage_root_id, source.materialization.relative_path, selector,
        source.logical.content_sha256, source.materialization.size_bytes, 1, "application/json", rows_owner.FORMAT_ID,
        None, CustodyState.UNVERIFIED, None, None, None, None, (), None, None,
        ("PENDING_ROSTER_METADATA_COMMITTED_PUBLICATION_CUSTODY_CHECKED_SEPARATELY",))
