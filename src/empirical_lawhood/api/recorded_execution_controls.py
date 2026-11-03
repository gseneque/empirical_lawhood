# SPDX-License-Identifier: MPL-2.0
"""Read a completed predecessor's exact operational controls, without reissue.

The caller supplies a terminal identity from an authenticated continuation.
That terminal pins the recovery index and frozen plan. This reader supplies no
scientific products, access permission or executable operands.
"""
from hashlib import sha256
import json

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes


def _document(writer, relative, *, schema, version, expected=None, maximum_bytes):
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    manifest = writer.read_manifest(relative)
    if (manifest.logical.payload_schema != schema or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or manifest.logical.media_type != 'application/json' or manifest.materialization.relative_path != relative
            or manifest.materialization.storage_root_id != writer.root.contract.storage_root_id
            or manifest.materialization.compression != 'none' or manifest.materialization.partition_selector is not None
            or maximum_bytes is not None and manifest.materialization.size_bytes > maximum_bytes
            or writer.custody_limits.exceeds('in_memory_payload_bytes', manifest.materialization.size_bytes)):
        raise PermissionError('recorded execution requires exact bounded canonical controls')
    writer.verify_manifest(manifest)
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=manifest.materialization.size_bytes)
    document = json.loads(raw)
    digest = sha256(raw).hexdigest()
    if (set(document) != {'schema', 'version', 'value'} or document['schema'] != schema
            or document['version'] != version or canonical_json_document_bytes(document) != raw
            or digest != manifest.logical.content_sha256 or digest != manifest.materialization.physical_sha256
            or expected is not None and (schema, version, digest) != (
                expected.object_schema, expected.object_version, expected.object_fingerprint)):
        raise PermissionError('recorded execution changes its exact published control bytes')
    return document['value'], manifest


def _identity(document, field):
    return ObjectIdentity(document['value'][field], document['schema'], document['version'],
        sha256(canonical_json_document_bytes(document)).hexdigest())


def _issued_source(document):
    from empirical_lawhood.runtime.study_issue import IssuedExecutableStudyManifest, IssuedStudyManifest
    if (document['schema'], document['version']) == (IssuedExecutableStudyManifest.SCHEMA, IssuedExecutableStudyManifest.VERSION):
        document = document['value']['base']
    if (document['schema'], document['version']) != (IssuedStudyManifest.SCHEMA, IssuedStudyManifest.VERSION):
        raise PermissionError('recorded execution requires its original issued source contract')
    return document['value']['source_closure']['value']['implementation_commit']


def completed_issued_execution(*, writer, locator, candidate, terminal, observe_controls=None):
    from .models import ExperimentPackage
    from .codecs import MAX_CAMPAIGN_PACKAGE_BYTES
    from .current_result_custody import _current_control
    from .experiment_execution_read import read_execution_records
    from empirical_lawhood.runtime.plans import ExecutionPlan, RunPlan
    from empirical_lawhood.runtime.recovery import build_run_recovery_index
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
    run_id = locator.run_id
    package, package_manifest = _document(writer, 'runs/' + run_id + '/plans/campaign-package.json',
        schema=ExperimentPackage.SCHEMA, version=ExperimentPackage.VERSION,
        expected=locator.package, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    if (package['package_id'] != locator.package.object_id or package['run_plan_id'] != run_id
            or _identity(package['issued_study']['value']['candidate'], 'candidate_id') != candidate
            or package_manifest.logical.logical_artifact_id != 'campaign-package.' + run_id):
        raise PermissionError('recorded execution changes its exact original package or candidate')
    parent = ArtifactLineageParent(locator.package, package_manifest.logical.visibility_ceiling,
        package_manifest.logical.outcome_access)
    run, run_manifest = _document(writer, 'runs/' + run_id + '/plans/run-plan.json',
        schema=RunPlan.SCHEMA, version=RunPlan.VERSION, maximum_bytes=writer.custody_limits.control_record_bytes)
    if (run['run_plan_id'] != run_id or run_manifest.logical.logical_artifact_id != 'run-plan.' + run_id
            or run_manifest.logical.lineage_parents != (parent,)
            or run['candidate'] != candidate.to_document()):
        raise PermissionError('recorded execution changes its package-bound original run plan')
    run_pin = ObjectIdentity(run_id, RunPlan.SCHEMA, RunPlan.VERSION, run_manifest.logical.content_sha256)
    run_parent = ArtifactLineageParent(run_pin, parent.visibility_ceiling, parent.outcome_access)
    plan = _current_control(writer=writer, run_id=run_id, name='execution-plan', record_type=ExecutionPlan,
        maximum_bytes=writer.custody_limits.control_record_bytes,
        expected_lineage=tuple(sorted((parent, run_parent), key=lineage_parent_sort_key)))
    if (plan.source_plan != run_pin or plan.execution_plan_id != package['execution_plan_id']
            or plan.candidate != candidate or plan.implementation_commit != run['implementation_commit']
            or plan.implementation_commit != _issued_source(package['issued_study'])):
        raise PermissionError('recorded execution changes its frozen source, plan or candidate')
    authorities = tuple(sorted((_identity(package['scientific_approval'], 'authorization_id'),
        _identity(package['execution_authority'], 'authority_id')), key=lambda value: value.object_id))
    index = build_run_recovery_index(plan, run_id=run_id, wave_id='wave.' + package['package_id'],
        authority_identities=authorities)
    report = read_execution_records(writer=writer, plan=plan, index=index, observe_controls=observe_controls)
    if report.get('terminal') != terminal.to_document() or report.get('execution_complete') is not True:
        raise PermissionError('recorded execution loses its original complete terminal and receipt census')
    return report
