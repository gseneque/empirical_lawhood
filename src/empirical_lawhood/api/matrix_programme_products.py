# SPDX-License-Identifier: MPL-2.0
"""Deliver original Matrix science by exact custody references, without work."""
from contextlib import ExitStack, contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import PHASES
from empirical_lawhood.adapters.methods.matrix_researcher_programme.product_export import (
    MatrixProgrammePortableProductExportSelection, MatrixProgrammeProductExportSelection,
)
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.infrastructure.read_checkpoint import completed_read_checkpoints
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_document_bytes
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactManifest, ArtifactProfile, ArtifactWriteRequest,
    CanonicalTaskReceipt, artifact_publication_commit_relative_path, derived_outcome_access,
    lineage_parent_sort_key,
)
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled

EXPORT_SCHEMA = 'empirical-lawhood/operational/matrix-programme-product-delivery'


@contextmanager
def _export_context(owner, plan, operation, checkpoints):
    if checkpoints is not None:
        with checkpoints.context(owner, plan, operation) as result:
            yield result
    else:
        with owner._context(plan, operation=operation) as context:
            yield context, False


def _document(schema, value):
    return canonical_json_document_bytes({'schema': schema, 'version': '1.0.0', 'value': value})


def _read_exact(writer, manifest):
    raw = read_bounded_bytes(writer.root.resolve(manifest.materialization.relative_path, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes)
    if (len(raw), sha256(raw).hexdigest()) != (
            manifest.materialization.size_bytes, manifest.materialization.physical_sha256):
        raise PermissionError('Matrix delivery changes exact original evidence bytes')
    return raw


def _phase_census(context, frontier):
    skipped, waiting = dict(frontier['unentered']), dict(frontier['waiting'])
    return tuple({'phase': phase,
        'binding': None if phase not in context.bindings else context.bindings[phase].identity.to_document(),
        'observation': 'RETAINED_OWNER_REPORT' if phase in context.observations else
            'BINDING_PUBLICATION_PENDING' if phase in context.pending_bindings else
            skipped.get(phase, 'NOT_OBSERVED'),
        'operational_completion': phase in context.observations and context.observations[phase].complete,
        'eligible': phase in frontier['eligible'],
        'waiting_for': waiting.get(phase, ()),
        'entry_without_receipt': 'NOT_INFERRED'} for phase in PHASES)


def _current_grants(context, authority_writer, *, include_execution_records=False):
    """Retain exact bindings, never an authorization decision, for this export."""
    from empirical_lawhood.api.matrix_programme_e4_phases import programme_e4_request
    from empirical_lawhood.api.recursive_qualified_parents import _require_parent_authorities_current
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore

    bindings = []
    for phase in ('e1', 'e3', 'e4.source-cal', 'e4.calibration', 'e4.source-conf',
            'e4.confirmation', 'e5.source', 'e5.confirmation', 'e6.source', 'e6'):
        observation = context.observations.get(phase)
        if observation is None:
            origin = getattr(context, 'phase_origins', {}).get(phase)
            if origin is not None:
                observation = origin.observations.get(phase)
        if (observation is None or (not include_execution_records
                and observation.report.get('read_scope') == 'EXECUTION_RECORDS')
                or observation.report.get('state') in (
                'AUTHORING_REQUIRED', 'DEPENDENCIES_REQUIRED',
                'UNENTERED_REVISION_NOT_TRIGGERED', 'UNENTERED_REVISION_UNEVALUABLE',
                'UNENTERED_REVISION_FIT_UNAVAILABLE', 'UNENTERED_REQUIRED_SR_BR_FIT_UNAVAILABLE')):
            continue
        components = (None,)
        if phase in ('e4.calibration', 'e4.confirmation'):
            request = programme_e4_request(context, phase)
            components = tuple(row.component_id for row in request.components)
        for component in components:
            _, _, authority, package, _, _ = context.authority(phase, component)
            reveal = ExternalStudyOperationAuthorityStore(authority_writer).load(authority.reveal_authority_id)
            binding = SimpleNamespace(
                issued_study=ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study),
                execution_authority=ObjectIdentity.from_record(package.execution_authority.authority_id,
                    package.execution_authority),
                reveal_authority=ObjectIdentity.from_record(reveal.authority_id, reveal))
            bindings.append((binding, package))
    def current():
        original_access = getattr(context, 'require_original_access', None)
        if original_access is not None:
            original_access()
        _require_parent_authorities_current(tuple(bindings), authority_writer)
    current()
    return current


def _receipt_products(writer, manifests, require_current):
    """Only an actual producing receipt can classify a scientific product."""
    receipts, science, controls = [], {}, {}
    for manifest in sorted(tuple(manifests.values()), key=lambda row: row.materialization.relative_path):
        if manifest.logical.payload_schema != CanonicalTaskReceipt.SCHEMA:
            continue
        require_current()
        raw = _read_exact(writer, manifest)
        receipt = decode_canonical_bytes(raw, CanonicalTaskReceipt, maximum_bytes=len(raw))
        if not receipt.canonical_equals(raw) or receipt.fingerprint() != manifest.logical.content_sha256:
            raise PermissionError('Matrix delivery changes its exact producing receipt')
        receipt_pin = ObjectIdentity.from_record(receipt.receipt_id, receipt)
        receipts.append({'receipt': receipt_pin.to_document(), 'reference': manifest.materialization.relative_path,
            'record': receipt.to_document()})
        logicals = {row.logical_artifact_id: row for row in receipt.output_logical_artifacts}
        for material in receipt.output_materializations:
            actual = manifests.get(material.relative_path)
            if actual is None or (actual.logical, actual.materialization) != (
                    logicals[material.logical_artifact_id], material):
                raise PermissionError('Matrix delivery omits or substitutes a receipted original output')
            row = {'producing_run_id': receipt.run_id, 'producing_task_id': receipt.task_id,
                'producing_receipt': receipt_pin.to_document(), 'reference': material.relative_path,
                'manifest': ObjectIdentity.from_record('manifest.' + actual.fingerprint(), actual).to_document()}
            # Runtime completion and contact controls are custody, rather than
            # scientific findings. Native arrays and actual adjudications stay
            # in the scientific census with their original access classes.
            target = (controls if actual.logical.payload_schema.startswith('empirical-lawhood/runtime/')
                and actual.logical.payload_schema != ScientificAdjudicationRecord.SCHEMA else science)
            key = (receipt.receipt_id, actual.logical.logical_artifact_id)
            if target.setdefault(key, row) != row:
                raise PermissionError('Matrix delivery aliases distinct original scientific products')
    return tuple(receipts), tuple(science[key] for key in sorted(science)), tuple(controls[key] for key in sorted(controls))


def _evidence_references(manifests, metadata, payload_paths):
    rows = []
    for path, manifest in sorted(manifests.items()):
        publication = manifest.publication
        if publication is None:
            raise PermissionError('Matrix delivery requires actual original committed publication custody')
        rows.append({'relative_path': path, 'manifest_relative_path': path + '.manifest.json',
            'manifest_size_bytes': metadata[path + '.manifest.json'][0],
            'manifest_physical_sha256': metadata[path + '.manifest.json'][1],
            'payload_validation': 'ORIGINAL_RECEIPT_JOIN_AND_EXACT_FINAL_BYTES' if path in payload_paths
                else 'METADATA_REFERENCE_ONLY_ORIGINAL_OWNER_REQUIRED',
            'publication_commit_relative_path': artifact_publication_commit_relative_path(
                publication.publication_scope, publication.publication_batch_id),
            'manifest': manifest.to_document()})
    return tuple(rows)


def _require_snapshot(writer, manifests, require_current, metadata, payload_paths):
    """Recheck immutable facts after owning scientific readers have accepted them.

    This is a physical final guard, not a replacement scientific decoder or a
    new authority source. Every original body remains behind current grants.
    Sidecar decoding replays its exact original commit/member join.
    """
    require_current()
    for path, manifest in sorted(tuple(manifests.items())):
        if writer.read_manifest(path) != manifest:
            raise PermissionError('Matrix delivery changes original manifest or publication custody')
        if path in payload_paths:
            require_current()
            writer.verify(manifest.materialization)
    for path, expected in sorted(metadata.items()):
        if bounded_file_sha256(writer.root.resolve(path, for_write=False), maximum_bytes=expected[0]) != expected:
            raise PermissionError('Matrix delivery changes exact original sidecar or commit bytes')
    require_current()


def export_programme_products(owner, *, directory, selection_path, programme_request_path=None):
    """Publish original references and an explicitly selected physical replica."""
    path = Path(selection_path)
    if any(value.is_symlink() for value in (path, *path.parents)) or '..' in path.parts:
        raise ValueError('Matrix product delivery refuses linked or traversing selections')
    raw = read_bounded_bytes(path, maximum_bytes=1024**2)
    kinds = {kind.SCHEMA: kind for kind in (
        MatrixProgrammeProductExportSelection, MatrixProgrammePortableProductExportSelection)}
    document = json.loads(raw)
    kind = kinds.get(document.get('schema')) if type(document) is dict else None
    if kind is None:
        raise ValueError('Matrix delivery requires a supported product export selection')
    selection = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
    if not selection.canonical_equals(raw):
        raise ValueError('Matrix product delivery requires exact canonical selection bytes')
    plan = owner._plan(directory)
    if selection.programme != plan.identity:
        raise PermissionError('Matrix product delivery substitutes its actual original programme')
    destination = owner.writer.root.resolve(selection.output_relative_path, for_write=True)
    original = Path(directory)
    if destination.is_relative_to(original) or original.is_relative_to(destination):
        raise ValueError('Matrix product delivery must be outside the closed original programme')
    operation = owner._request(plan, programme_request_path)
    manifests, metadata = {}, {}
    replica = None
    def observe(manifest):
        if type(manifest) is not ArtifactManifest:
            raise TypeError('Matrix delivery requires exact authenticated artifact manifests')
        key = manifest.materialization.relative_path
        if key.startswith(selection.output_relative_path + '/'):
            # Operational checkpoints are derived delivery state, never original
            # producing evidence. Their own read lifetime still checks them.
            return
        if manifests.setdefault(key, manifest) != manifest:
            raise PermissionError('Matrix delivery changes its original evidence census')
        sidecar = key + '.manifest.json'
        if sidecar not in metadata:
            metadata[sidecar] = bounded_file_sha256(owner.writer.root.resolve(sidecar, for_write=False),
                maximum_bytes=owner.writer.custody_limits.manifest_bytes)
        publication = manifest.publication
        if publication is not None:
            expected = (publication.commit_marker_size_bytes, publication.commit_marker_sha256)
            if metadata.setdefault(publication.commit_marker_relative_path, expected) != expected:
                raise PermissionError('Matrix delivery changes an original publication commit')

    # The normal readers own all typed science, source and current access
    # checks. The callback only records their actual verified closure.
    from empirical_lawhood.api.selected_e3_access import original_e3_authority_read_context
    with original_e3_authority_read_context(owner.writer), \
            completed_read_checkpoints(owner.writer.root.contract, observe_manifest=observe) as independent_reads, \
            owner.writer.read_context(observe_manifest=observe) as reading:
        service = replace(owner.service, artifact_writer=reading)
        scoped = type(owner)(service=service, descriptor=owner.descriptor)
        checkpoints = None
        if scientific_reconstruction_enabled():
            from empirical_lawhood.api.matrix_programme_export_checkpoints import ProgrammeExportCheckpoints
            from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import (
                METADATA_PHASES, MatrixProgrammeObservation,
            )
            checkpoints = ProgrammeExportCheckpoints(owner, reading, selection, plan, operation, manifests, independent_reads)
        with _export_context(scoped, plan, operation, checkpoints) as (context, finalizing), ExitStack() as lifetime:
            authorities = lifetime.enter_context(owner.writer.read_context(observe_manifest=observe))
            execution_reports = {}
            originals, current, structural = None, None, None
            if finalizing:
                from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
                # Gather each live execution census once, before opening any
                # saved protected body. Recorded original products keep both
                # the current E3 and imported model producers' reveals live.
                with scientific_reconstruction_operation('off'):
                    for phase in PHASES:
                        if phase not in context.bindings:
                            continue
                        execution = scoped._read_phase(context, phase, execution_only=True)
                        if execution.get('execution_complete') is not True:
                            raise PermissionError('Matrix export finalization loses complete original execution')
                        execution_reports[phase] = execution
                        context.observations[phase] = MatrixProgrammeObservation(phase, execution, False,
                            execution_complete=True)
                    if 'e3' in context.bindings:
                        originals = lifetime.enter_context(context.programme_e3_products())
                    current = _current_grants(context, authorities, include_execution_records=True)
                for phase, execution in execution_reports.items():
                    report = checkpoints.load(phase, context=context, execution=execution, require_current=current)
                    checkpoints.observe_completed(context, phase, report)
                if 'e4.revision' in context.observations:
                    from empirical_lawhood.api.matrix_programme_structural_prediction import programme_structural_prediction
                    revision = checkpoints.revision_read(context, current)
                    structural = programme_structural_prediction(context, revision=revision)
            elif checkpoints is not None:
                for phase in PHASES:
                    if phase not in context.bindings:
                        continue
                    reports = None
                    if phase not in METADATA_PHASES and checkpoints.present(phase):
                        execution = scoped._read_phase(context, phase, execution_only=True)
                        if execution.get('execution_complete') is not True:
                            raise PermissionError('Matrix export checkpoint loses complete original execution')
                        context.observations[phase] = MatrixProgrammeObservation(phase, execution, False,
                            execution_complete=True)
                        current = _current_grants(context, authorities, include_execution_records=True)
                        reports = {phase: checkpoints.load(phase, context=context, execution=execution,
                            require_current=current)}
                        execution_reports[phase] = execution
                    scoped._observe(context, phases=(phase,), reports=reports)
                    if (phase not in METADATA_PHASES and reports is None
                            and context.observations[phase].complete):
                        execution = scoped._read_phase(context, phase, execution_only=True)
                        if execution.get('execution_complete') is not True:
                            raise PermissionError('Matrix export checkpoint lacks complete original execution')
                        current = _current_grants(context, authorities)
                        checkpoints.save(phase, context.observations[phase].report, context=context,
                            execution=execution, require_current=current)
                        execution_reports[phase] = execution
            else:
                scoped._observe(context)
            if current is None:
                current = _current_grants(context, authorities)
            if checkpoints is not None and checkpoints.present('programme-report'):
                report = checkpoints.load('programme-report', context=context, execution=execution_reports,
                    require_current=current)
            else:
                report = scoped._report(context, **({} if structural is None else {'structural_prediction': structural}))
                if checkpoints is not None and report['state'] == 'COMPLETE':
                    checkpoints.save('programme-report', report, context=context, execution=execution_reports,
                        require_current=current)
            if not finalizing and 'e3' in context.observations and context.observations['e3'].complete:
                originals = lifetime.enter_context(context.e3_originals())
            # Grant loads get their own small custody lifetime. Never attach
            # fresh authority validation to the growing scientific snapshot.
            current_grants = current if finalizing else _current_grants(context, authorities)
            def require_access():
                if originals is not None:
                    originals.require_access()
                current_grants()

            def require_current():
                if originals is not None:
                    originals.require_current()
                current_grants()
                if checkpoints is not None:
                    checkpoints.require_source_current()
            require_current()
            receipts, products, control_products = _receipt_products(owner.writer, manifests, require_access)
            payload_paths = frozenset(row['reference'] for row in (*receipts, *products, *control_products))
            references = _evidence_references(manifests, metadata, payload_paths)
            if any((owner.writer.root.resolve(row['relative_path'], for_write=False)).is_relative_to(destination)
                    for row in references):
                raise ValueError('Matrix product delivery overlaps its original evidence closure')
            parents = tuple(sorted({ArtifactLineageParent(
                ObjectIdentity.from_record('source.' + row.logical.fingerprint(), row.logical),
                row.logical.visibility_ceiling, row.logical.outcome_access) for row in manifests.values()},
                key=lineage_parent_sort_key))
            access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(row.outcome_access for row in parents))
            ceilings = tuple(row.visibility_ceiling for row in parents)
            visibility = inherited_visibility(ceilings, access)
            # The ordinary programme report already contains every phase
            # report. Retain each body once, with exact encoding digests.
            encoded = canonical_json_document_bytes(report)
            readout = {'report': report, 'encoded_report_size_bytes': len(encoded),
                'encoded_report_sha256': sha256(encoded).hexdigest()}
            phase_readouts = []
            for phase in report['phases']:
                encoded_phase = canonical_json_document_bytes(phase['report'])
                phase_readouts.append({'phase': phase['phase'], 'encoded_report_size_bytes': len(encoded_phase),
                    'encoded_report_sha256': sha256(encoded_phase).hexdigest()})
            delivery = {'selection': selection.identity.to_document(), 'programme': plan.identity.to_document(),
                'original_artifact_root': owner.writer.root.contract.to_document(),
                'delivery_mode': 'ORIGINAL_CUSTODY_REFERENCES_NO_ARRAY_DUPLICATION',
                'access_prerequisites': 'ORIGINAL_ROOT_AUTHENTICATED_ISSUE_HISTORICAL_EXECUTION_CURRENT_REVEAL',
                'scientific_product_scope': 'COMPLETE_RECEIPTED_OUTPUTS_IN_AUTHENTICATED_PHASE_AND_DEPENDENCY_CLOSURE',
                'phase_census': _phase_census(context, report['frontier']), 'programme_readout': readout,
                'phase_readouts': tuple(phase_readouts),
                'scientific_products': products, 'producing_receipts': receipts,
                'operational_products': control_products, 'evidence_references': references,
                'new_native_contact_count': 0, 'scientific_qualification': 'NOT_ESTABLISHED',
                'denominator_aggregation': 'SEPARATE_SCOPES_NO_CROSS_PHASE_SUM'}
            payload = _document(EXPORT_SCHEMA, delivery)
            write = ArtifactWriteRequest(selection.record_id, selection.output_relative_path + '/products.json',
                EXPORT_SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', selection.record_id,
                selection.output_relative_path, payload, visibility, ceilings, access, lineage_parents=parents)
            _require_snapshot(owner.writer, manifests, require_access, metadata, payload_paths)
            if read_bounded_bytes(path, maximum_bytes=len(raw)) != raw:
                raise PermissionError('Matrix product delivery selection changed before publication')
            require_current()
            publications = owner.writer.write_batch((write,))
            _require_snapshot(owner.writer, manifests, require_access, metadata, payload_paths)
            require_current()
            if type(selection) is MatrixProgrammePortableProductExportSelection:
                from empirical_lawhood.infrastructure.artifact_replication import replicate_artifact_publications
                from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot

                # Only receipt-joined outputs and receipts are selected for
                # physical delivery. Metadata-only references confer no body
                # access. The replication owner retains complete atomic batches.
                copied = tuple(manifests[key] for key in sorted(payload_paths))
                copied += (owner.writer.read_manifest(write.relative_path),)

                def current_copy():
                    require_access()
                    if read_bounded_bytes(path, maximum_bytes=len(raw)) != raw:
                        raise PermissionError('Matrix portable delivery selection changed during copying')

                def finish_copy():
                    _require_snapshot(owner.writer, manifests, require_access, metadata, payload_paths)
                    reading.require_verification_snapshot()
                    require_current()
                    current_copy()

                replica = replicate_artifact_publications(owner.writer,
                    GuardedExternalRoot(selection.replica_root), publications=copied,
                    receipt_path=Path(selection.replica_receipt_path), maximum_bytes=selection.maximum_bytes,
                    maximum_files=selection.maximum_files, require_current=current_copy,
                    before_complete=finish_copy, resume=True)
                require_current()
    return {'selection': selection.identity.to_document(), 'programme': plan.identity.to_document(),
        'path': str(destination / 'products.json'), 'phase_count': len(PHASES),
        'programme_readout': {'json_pointer': '/value/programme_readout/report',
            'state': report['state'], 'read_scope': report['read_scope'],
            'scientific_reconstruction': report['scientific_reconstruction'],
            'encoded_report_size_bytes': readout['encoded_report_size_bytes'],
            'encoded_report_sha256': readout['encoded_report_sha256']},
        'observed_phase_count': len(report['phases']), 'scientific_product_count': len(products),
        'reused_export_stages': () if checkpoints is None else tuple(checkpoints.reused),
        'delivery_mode': delivery['delivery_mode'], 'new_native_contact_count': 0,
        'portable_replica': None if replica is None else {
            'status': 'COMPLETE', 'receipt_path': str(replica.receipt_path),
            'root': replica.target_contract.to_document(), 'file_count': len(replica.files),
            'total_bytes': sum(row.size_bytes for row in replica.files),
            'scope': 'RECEIPTED_OUTPUT_PUBLICATIONS_RECEIPTS_AND_PROGRAMME_REPORT',
            'metadata_only_references_require_original_custody': True},
        'scientific_qualification': 'NOT_ESTABLISHED',
        'publications': tuple(row.to_document() for row in publications)}
