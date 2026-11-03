# SPDX-License-Identifier: MPL-2.0
"""Retained exposed original E3 custody for current E4 acceptance controls.

This test adapter creates no issue, grant or qualification. The E3 input was
already exposed. Only actual retained E3 products supply the selected model;
these helpers perform no new scientific acquisition.
"""

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace


from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_assay_method import MatrixPreparedAssayMethod
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import adapt_e3_frozen_package
from empirical_lawhood.adapters.methods.matrix_factor_response import protected_experiment_methods as e3
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import statistical_task_id
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseProtocol
from empirical_lawhood.api.codecs import MAX_CAMPAIGN_PACKAGE_BYTES
from empirical_lawhood.api.domain_composition.matrix_protected_response import scientific_read as original_reader
from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
from empirical_lawhood.api.matrix_selected_runtime import _published_input
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.api.prospective_experiment import load_retained_prospective_experiment
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_sha256
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult, ExternalRootContract
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile, resolve_external_root_contract
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding


SELECTION_KEYS = frozenset(('operator_profile_path', 'e3_authoring_relative_path', 'e3_package_path',
    'e3_reveal_authority_id', 'e3_package_sha256', 'e3_commit', 'reader_root_contract_path', 'reader_root_contract_sha256'))
EL_ROOT = Path('/media/chevre/EL/empirical-lawhood')


def read_selection(path):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(EL_ROOT):
        raise ValueError('selected opportunity conformance inputs must be explicitly retained on EL')
    selected = json.loads(read_bounded_bytes(path, maximum_bytes=64 * 1024))
    if (type(selected) is not dict or set(selected) != SELECTION_KEYS
            or any(type(value) is not str or not value for value in selected.values())):
        raise ValueError('retained opportunity test selection changes its closed string operand census')
    validate_relative_locator(selected['e3_authoring_relative_path'])
    validate_sha256(selected['e3_package_sha256'])
    validate_sha256(selected['reader_root_contract_sha256'])
    if len(selected['e3_commit']) != 40 or any(value not in '0123456789abcdef' for value in selected['e3_commit']):
        raise ValueError('original E3 commit requires its exact hexadecimal identity')
    for name in ('operator_profile_path', 'e3_package_path', 'reader_root_contract_path'):
        value = Path(selected[name])
        if not value.is_absolute() or not value.resolve(strict=True).is_relative_to(EL_ROOT):
            raise ValueError('original test operands must use explicitly selected absolute EL paths')
    return selected


def _external_bytes(writer, run_id, spec):
    """Authenticate one actual plan-selected original binary input after grants."""
    relative, _, _ = provider_input_location(writer, run_id, spec.logical_artifact_id)
    limit = writer.custody_limits.manifest_bytes
    manifest = writer.read_manifest(relative, maximum_bytes=limit)
    if (manifest.materialization.relative_path != relative
            or manifest.materialization.storage_root_id != writer.root.contract.storage_root_id
            or manifest.logical.logical_artifact_id != spec.logical_artifact_id
            or any(expected is not None and actual != expected for actual, expected in (
                (manifest.logical.payload_schema, spec.expected_payload_schema), (manifest.logical.content_sha256, spec.expected_content_sha256),
                (manifest.materialization.size_bytes, spec.expected_size_bytes), (manifest.logical.media_type, spec.expected_media_type),
                (manifest.logical.outcome_access, spec.expected_outcome_access), (manifest.logical.visibility_ceiling, spec.expected_visibility_ceiling)))):
        raise PermissionError('original assay bytes lose their exact issued input binding')
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=manifest.materialization.size_bytes)
    if (len(raw) != manifest.materialization.size_bytes or sha256(raw).hexdigest() != manifest.logical.content_sha256
            or sha256(raw).hexdigest() != manifest.materialization.physical_sha256):
        raise PermissionError('original assay template bytes differ from their actual publication')
    return raw


def original_selected_package(*, project_root, selection):
    profile = decode_canonical_bytes(read_bounded_bytes(Path(selection['operator_profile_path']), maximum_bytes=1024**2),
        OperatorStorageProfile, maximum_bytes=1024**2)
    selected_contract = resolve_external_root_contract(profile, repo_root=project_root, home_root=Path.home())
    contract_raw = read_bounded_bytes(Path(selection['reader_root_contract_path']), maximum_bytes=1024**2)
    if sha256(contract_raw).hexdigest() != selection['reader_root_contract_sha256']:
        raise PermissionError('selected operational reader contract bytes changed')
    contract = decode_canonical_bytes(contract_raw, ExternalRootContract, maximum_bytes=1024**2)
    # This is explicitly selected reader configuration, not evidence that a
    # contract record existed at original execution. Its storage ID must still
    # join actual manifests; the current EL mount/guard is checked independently.
    if ((contract.canonical_path, contract.required_mount_path) != (selected_contract.canonical_path, selected_contract.required_mount_path)
            or not Path(contract.canonical_path).is_relative_to(EL_ROOT)
            or Path(contract.required_mount_path).resolve(strict=True) != Path('/media/chevre/EL').resolve(strict=True)
            or not Path(contract.required_mount_path).is_mount()):
        raise ValueError('selected reader contract differs from the explicit profile paths or actual EL mount')
    writer = ExternalArtifactPlane(GuardedExternalRoot(contract), validators=integration_artifact_profile_validators())
    writer.root.verify(for_write=False)
    raw = read_bounded_bytes(Path(selection['e3_package_path']), maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    if sha256(raw).hexdigest() != selection['e3_package_sha256']:
        raise PermissionError('original E3 package changes the explicitly selected bytes')
    package = decode_canonical_bytes(raw, ExperimentPackage, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    if package.canonical_bytes() != raw or package.implementation_commit != selection['e3_commit']:
        raise PermissionError('original E3 package/commit differs from actual retained control custody')
    retained = load_retained_prospective_experiment(directory=writer.root.resolve(selection['e3_authoring_relative_path'], for_write=False),
        project_root=project_root, storage_profile=profile, artifact_writer=writer)
    # The existing public scientific owner replays actual current original
    # issue/execution/reveal grants and complete terminal/receipt custody first.
    checked = original_reader.read_protected_e3_original_products(selected=retained, artifact_writer=writer,
        run_id=package.run_plan_id, expected_package=package, reveal_authority_id=selection['e3_reveal_authority_id'])
    assert checked.report['typed_product_validation'] == 'COMPLETE'
    specification, allocation = checked.specification, checked.allocation
    assert tuple(len(allocation.unit_ids(role)) for role in ('train', 'calibration', 'evaluation')) == (64, 64, 64)
    plan, receipts = checked.execution_plan, checked.receipts
    products, bindings = {}, []
    reveal = ExternalStudyOperationAuthorityStore(writer).load(selection['e3_reveal_authority_id'])
    requests = (('models', 'fit', '', e3.ProtectedE3ModelSet), ('model_freeze', 'freeze', 'model', e3.ProtectedE3FrozenProducts),
        ('calibration', 'calibrate', '', e3.ProtectedE3Calibration), ('calibrated_freeze', 'freeze', 'calibration', e3.ProtectedE3FrozenProducts))
    for name, operation, mode, kind in requests:
        task_id = statistical_task_id(specification.identity, allocation.identity, operation, mode=mode)
        product = getattr(checked, name)
        products[name] = product
        receipt = receipts[task_id]
        logical, = (row for row in receipt.output_logical_artifacts if row.payload_schema == kind.SCHEMA)
        binding = RecursivePriorExecutionBinding('binding.selected-e5.' + name,
            ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
            ObjectIdentity.from_record(package.execution_authority.authority_id, package.execution_authority),
            ObjectIdentity.from_record(package.package_id, package), ObjectIdentity.from_record(plan.execution_plan_id, plan),
            package.run_plan_id, task_id, ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id,
            ObjectIdentity.from_record(product.record_id, product), (ProtectedE3PreFitJoin.SCHEMA,) if name == 'models' else ())
        bindings.append(MatrixSelectedOriginalProduct(binding, ObjectIdentity.from_record(reveal.authority_id, reveal)))
    prefit = checked.prefit
    frozen = adapt_e3_frozen_package(record_id='selected.retained-public-e3.' + package.fingerprint(),
        specification=specification, allocation=allocation, prefit=prefit, **products,
        selection_unit_ids=tuple(sorted((*allocation.unit_ids('calibration'), *allocation.unit_ids('evaluation')))))
    # Read the original four-action method and its actual declared template
    # input, rather than replacing the selected assay with older zero fixtures.
    task = next(row for row in plan.tasks if row.capability.capability_key == 'matrix-e3-protected.physical-forecast')
    semantic = original_reader._retained_scientific_writer(package, plan, writer)
    protocol_spec, = (row for row in task.external_inputs if row.expected_payload_schema == ScheduledResponseProtocol.SCHEMA)
    assay_protocol = _published_input(semantic, package.run_plan_id, protocol_spec, ScheduledResponseProtocol)
    template_spec, = (row for row in task.external_inputs if row.logical_artifact_id == assay_protocol.templates.array_artifact.artifact_id)
    template_raw = _external_bytes(semantic, package.run_plan_id, template_spec)
    return SimpleNamespace(writer=writer, profile=profile, package=frozen, issued_package=package, original_plan=plan,
        retained=retained, bindings=tuple(sorted(bindings, key=lambda row: row.record.object_id)),
        assay=MatrixPreparedAssayMethod.from_protocol('assay.retained-selected-e3', assay_protocol), template_raw=template_raw,
        original_receipts=tuple(sorted((task_id, receipt.receipt_id, receipt.fingerprint()) for task_id, receipt in receipts.items())))




def actual_publication(writer, manifest):
    """Reconstruct a write-result descriptor solely from its actual sidecar."""
    relative = manifest.materialization.relative_path + '.manifest.json'
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=writer.custody_limits.manifest_bytes)
    actual = writer.read_manifest(manifest.materialization.relative_path, maximum_bytes=writer.custody_limits.manifest_bytes)
    if (actual.logical, actual.materialization) != (manifest.logical, manifest.materialization):
        raise PermissionError('selected nomination changes actual original publication')
    sidecar = writer._manifest_materialization(logical_artifact_id=actual.logical.logical_artifact_id, relative_path=relative, payload=raw)
    writer.verify_manifest(actual)
    writer.verify(sidecar)
    return ArtifactWriteResult(actual.logical, actual.materialization, sidecar, False)
