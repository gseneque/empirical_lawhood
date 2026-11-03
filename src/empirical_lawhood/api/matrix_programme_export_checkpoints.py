# SPDX-License-Identifier: MPL-2.0
"""Durable completed export stages behind original source and current custody."""

from contextlib import contextmanager
from dataclasses import replace
from decimal import getcontext
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.infrastructure.numerical_provenance import (
    numerical_runtime_observation, observe_implementation_source,
)
from empirical_lawhood.infrastructure.read_checkpoint import (
    authenticate_read_file_pins, verified_read_file_pins,
)
from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes, canonical_json_document_bytes
from empirical_lawhood.runtime.artifacts import (
    ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, derived_outcome_access,
    lineage_parent_sort_key,
)
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_enabled

SCHEMA = 'empirical-lawhood/operational/matrix-export-checkpoint'
MAX_CHECKPOINT_BYTES = 512 * 1024**2
# Exact first-version transport owner and one byte-pinned local-report inventory
# update. All other package members, runtime, lock and operation bindings stay exact.
_V1_WRITER_SHA256 = 'a7d67ee368fe1d05043699828cd411e0ccff6303bbe2efa2353ccfdfb2341142'
_WRITER_MEMBER = 'api/matrix_programme_export_checkpoints.py'
_POLICY_MEMBER = 'infrastructure/source_policy.py'
_V1_POLICY_SHA256 = 'bdcceede975971cd9711d507ebac5a9eb71cdd4a881ae81f30c7c3373be6cf64'
_V2_POLICY_SHA256 = '69686706b4aafb6359e62148822ae1273c6d46b86e52e8faf96e9a24384bb813'
_V1_TRANSPORT_REPAIRS = (
    ('api/current_result_custody.py', '3b169d365ef7afbbc0e5bf991fe41e7dc3ab976c18677f7c51c0f2eacc0f8617', '01b20bf25f1633ffc30219a999f0299b7e5576f10f8f0fe19c64a4a2532efb12'),
    ('api/matrix_programme_products.py', '2ea61fdb3946359241a5a4d579a20711ba8687ff2b18d0ab91a687d5ab5e8646', 'fe37e39e7c087a125d53faf0dd2a65285077cf0243f4dfb6d06caf0938339e9f'),
    ('api/matrix_programme_structural_prediction.py', '278a0cd0e523bccdfdb74f8f0eefa249d7f32c0a07b5b6b84d4fd0daf9cca69d', '044166496a8d64198959628cea92abb6485068574b052f5246208622e68d1479'),
    ('api/matrix_researcher_programme.py', '344cbc91633382b2bc3e018fc99084b6c393bb35aaa09deccd1c30e0500bb2bc', '58d7e5ffe5df64082f1a3d608077cd19735c1048ce91a4eaa8ee6a4554326ec5'),
    ('infrastructure/read_checkpoint.py', '00d300a44cc47ce80e40ae38415411d07e4b86b388cc085963a8e35c39894618', '96250c48a209e942a1e17b291bd7c6271663a8cc40da3652121e72dc8d736701'),
)


def _source(project_root):
    _, code, lock, commit, _ = observe_implementation_source(project_root)
    return {'code_sha256': code, 'lock_sha256': lock, 'commit': commit}


class ProgrammeExportCheckpoints:
    """Reuse only complete stage reports from this exact selected operation.

    Completed phase reports can finish delivery through recorded lineage.
    Actual execution/access owners and exact consumed bytes remain current.
    A saved report is not permission to reopen a protected body.
    """

    def __init__(self, owner, reading, selection, plan, operation, manifests, independent_reads):
        self.owner, self.reading, self.selection = owner, reading, selection
        self.manifests = manifests
        self.independent_reads = independent_reads
        self.prefix = selection.output_relative_path + '/checkpoints/'
        self.source = _source(owner.service.project_root)
        decimal = getcontext()
        self.binding = canonical_json_document_bytes({
            'selection': selection.identity.to_document(), 'programme': plan.identity.to_document(),
            'operation': None if operation is None else operation.to_document(),
            'root': owner.writer.root.contract.to_document(), 'source': self.source,
            'runtime': numerical_runtime_observation(),
            'decimal': {'precision': decimal.prec, 'rounding': decimal.rounding,
                'emin': decimal.Emin, 'emax': decimal.Emax, 'clamp': decimal.clamp,
                'traps': sorted(key.__name__ for key, enabled in decimal.traps.items() if enabled)},
            'scientific_reconstruction': 'full' if scientific_reconstruction_enabled() else 'off'})
        self.reused = []
        self.completed = {}
        self.reused_sources = {}
        self.runtime_relocations = {}

    def _runtime_matches(self, recorded, current):
        if recorded == current:
            return True
        if (not isinstance(recorded, dict) or set(recorded) != set(current)
                or {key: value for key, value in recorded.items() if key != 'threadpools'} !=
                    {key: value for key, value in current.items() if key != 'threadpools'}):
            return False
        def key(row):
            return canonical_json_document_bytes({name: value for name, value in row.items() if name != 'filepath'})
        old, new = recorded.get('threadpools'), current.get('threadpools')
        if (not isinstance(old, list) or not isinstance(new, list) or len(old) != len(new)
                or any(not isinstance(row, dict) for row in (*old, *new))):
            return False
        pins = {}
        for before, after in zip(sorted(old, key=key), sorted(new, key=key), strict=True):
            if key(before) != key(after):
                return False
            left, right = before.get('filepath'), after.get('filepath')
            if left == right:
                continue
            if (not isinstance(left, str) or not isinstance(right, str)
                    or not Path(left).is_absolute() or not Path(right).is_absolute()
                    or Path(left).name != Path(right).name):
                return False
            a = bounded_file_sha256(Path(left), maximum_bytes=256 * 1024**2)
            b = bounded_file_sha256(Path(right), maximum_bytes=256 * 1024**2)
            if a != b:
                return False
            pins[left], pins[right] = a, b
        self.runtime_relocations.update(pins)
        return True

    def _binding_matches(self, binding, *, version, stage):
        if canonical_json_document_bytes(binding) == self.binding:
            return True
        if version != '1.0.0' or stage == 'programme-report':
            return False
        expected = json.loads(self.binding)
        source = binding.get('source', {})
        commit = source.get('commit')
        if (set(source) != set(self.source) or not isinstance(commit, str) or len(commit) != 40
                or any(char not in '0123456789abcdef' for char in commit)
                or source.get('lock_sha256') != self.source['lock_sha256']):
            return False
        rows, _, _, _, _ = observe_implementation_source(self.owner.service.project_root)
        if dict(rows).get(_POLICY_MEMBER) not in (_V1_POLICY_SHA256, _V2_POLICY_SHA256):
            return False
        replacements = {_WRITER_MEMBER: _V1_WRITER_SHA256, _POLICY_MEMBER: _V1_POLICY_SHA256}
        for name, before, after in _V1_TRANSPORT_REPAIRS:
            if dict(rows).get(name) != after:
                return False
            replacements[name] = before
        previous = tuple((name, replacements.get(name, digest)) for name, digest in rows)
        if (not any(name == _WRITER_MEMBER for name, _ in rows)
                or source.get('code_sha256') != sha256(canonical_json_bytes(previous)).hexdigest()):
            return False
        if not self._runtime_matches(binding.get('runtime'), expected['runtime']):
            return False
        expected['source'] = source
        expected['runtime'] = binding['runtime']
        return canonical_json_document_bytes(binding) == canonical_json_document_bytes(expected)

    @staticmethod
    def _report_pin(report):
        raw = canonical_json_document_bytes(dict(report))
        return {'size_bytes': len(raw), 'sha256': sha256(raw).hexdigest()}

    def _stored_report(self, stage, report):
        if stage != 'programme-report':
            return dict(report), 'INLINE'
        phases = []
        for row in report['phases']:
            phase = row['phase']
            pin = self.completed.get(phase)
            if pin is None or pin['report'] != self._report_pin(row['report']):
                raise PermissionError('aggregate checkpoint requires its exact completed phase reports')
            phases.append({**{key: value for key, value in row.items() if key != 'report'},
                'report_checkpoint': pin})
        return {**report, 'phases': tuple(phases)}, 'COMPLETED_PHASE_REFERENCES'

    def _loaded_report(self, stage, value, context):
        encoding = value.get('report_encoding', 'INLINE')
        report = value['report']
        if encoding == 'INLINE':
            return report
        if stage != 'programme-report' or encoding != 'COMPLETED_PHASE_REFERENCES':
            raise PermissionError('Matrix export checkpoint changes its report encoding')
        phases = []
        for row in report['phases']:
            phase = row['phase']
            pin = self.completed.get(phase)
            observation = context.observations.get(phase)
            if (pin is None or pin != row['report_checkpoint'] or observation is None
                    or not observation.complete or pin['report'] != self._report_pin(observation.report)):
                raise PermissionError('aggregate checkpoint changes its authenticated phase report')
            phases.append({**{key: item for key, item in row.items() if key != 'report_checkpoint'},
                'report': dict(observation.report)})
        return {**report, 'phases': tuple(phases)}

    def require_source_current(self):
        if _source(self.owner.service.project_root) != self.source:
            raise PermissionError('Matrix export checkpoint changes its selected implementation source')
        for path, pin in self.runtime_relocations.items():
            if bounded_file_sha256(Path(path), maximum_bytes=pin[0]) != pin:
                raise PermissionError('Matrix export checkpoint changes a relocated numerical library')

    def present(self, stage):
        path = self.owner.writer.root.resolve(self.prefix + stage + '.json', for_write=False)
        return path.exists() or path.is_symlink()

    @contextmanager
    def context(self, owner, plan, operation):
        """Choose saved-report finalization before any full predecessor read.

        Other frontiers retain the ordinary full reader. The recorded context
        opens and closes with reconstruction disabled; only already completed
        reports are delivered as full science within its yielded lifetime.
        """
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.source_continuation import COMPLETED_E4_PHASES
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.e4_structural_prediction import E4MatchedRelationSelection
        from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeProjectionContext
        from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation

        supported = (*COMPLETED_E4_PHASES, 'e4.revision')
        if any(self.present(phase) for phase in supported):
            with scientific_reconstruction_operation('off'), owner._context(plan, operation=operation) as context:
                complete = (type(context) is MatrixProgrammeProjectionContext and context.bindings
                    and not context.pending_bindings and set(context.bindings).issubset(supported)
                    and all(self.present(phase) for phase in context.bindings)
                    and ('e4.development' not in context.bindings or 'e4.revision' in context.bindings)
                    and ('e4.revision' not in context.bindings
                        or type(context.design.e4_structure.prediction) is E4MatchedRelationSelection))
                if complete:
                    with scientific_reconstruction_operation('full'):
                        yield context, True
                    return
        with owner._context(plan, operation=operation) as context:
            yield context, False

    def observe_completed(self, context, stage, report):
        """Restore an authenticated owner report without its acquisition hooks."""
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.frontier import MatrixProgrammeObservation
        from empirical_lawhood.api.matrix_researcher_programme import _phase_complete

        if stage not in self.completed or not _phase_complete(stage, report):
            raise PermissionError('Matrix export finalization requires its complete authenticated phase report')
        context.observations[stage] = MatrixProgrammeObservation(stage, report, True)

    def revision_read(self, context, require_current):
        """Join saved DEV/revision reports to their original receipted fit/freeze.

        The completed checkpoint already binds the scientific validation and
        every input byte. This consumer checks the exact original products;
        it does not call the acquisition replay or fit owner again.
        """
        from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4DevelopmentProgramme
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicRevisionDecision
        from empirical_lawhood.api.matrix_researcher_programme_e4_lineage import MatrixProgrammeRevisionRead
        from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.kernel.status import OperationalStatus

        if not {'e4.development', 'e4.revision'}.issubset(self.completed):
            raise PermissionError('Matrix export revision requires both authenticated completed reports')
        development_report = context.report('e4.development')
        structure = development_report.get('scientific_result', development_report)['structure']
        raw = canonical_json_document_bytes(structure['original_programme'])
        development = decode_canonical_bytes(raw, SelectedE3E4DevelopmentProgramme, maximum_bytes=len(raw))
        report = context.report('e4.revision')

        def product(kind):
            rows = tuple(row for row in report['retained_product_index'] if row['schema'] == kind.SCHEMA)
            if len(rows) != 1:
                raise PermissionError('Matrix export revision requires one exact original product per role')
            row, = rows
            pin = decode_canonical_bytes(canonical_json_document_bytes(row['producing_receipt']),
                ObjectIdentity, maximum_bytes=1024**2)
            require_current()
            receipt = ExternalTaskReceiptStore(self.reading).read_by_receipt_id(
                report['run_id'], row['task_id'], pin.object_id)
            if (receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED
                    or ObjectIdentity.from_record(receipt.receipt_id, receipt) != pin):
                raise PermissionError('Matrix export revision changes its original producing receipt')
            manifest = self.manifests.get(row['relative_path'])
            if (manifest is None or manifest.logical not in receipt.output_logical_artifacts
                    or manifest.materialization not in receipt.output_materializations
                    or (manifest.logical.logical_artifact_id, manifest.logical.payload_schema,
                        manifest.logical.content_sha256, manifest.materialization.size_bytes) !=
                        (row['logical_artifact_id'], row['schema'], row['sha256'], row['size_bytes'])):
                raise PermissionError('Matrix export revision changes its exact saved product custody')
            require_current()
            from empirical_lawhood.infrastructure.canonical_record_read import read_verified_canonical_record
            record = read_verified_canonical_record(self.reading, manifest, kind,
                maximum_bytes=manifest.materialization.size_bytes)
            require_current()
            return record

        nomination, frozen = product(methods.SelectedE4RevisionNomination), product(methods.SelectedE4FrozenRevision)
        decision = SelectedE4PublicRevisionDecision.from_products(development, nomination, frozen,
            record_id='decision.' + context.namespace + '.revision')
        if (report['scientific_disposition'] != decision.trigger_disposition
                or report['joint_freeze'] != frozen.to_document()):
            raise PermissionError('Matrix export revision changes its saved scientific disposition or freeze')
        context.observations['e4.revision'] = replace(context.observations['e4.revision'],
            revision_trigger=decision.trigger_disposition)
        return MatrixProgrammeRevisionRead(None, None, development, nomination, frozen, decision)

    def load(self, stage, *, context, execution, require_current):
        from empirical_lawhood.runtime.progress import report_progress
        report_progress(phase='matrix_export.checkpoint.resume.' + stage)
        require_current()
        self.require_source_current()
        relative = self.prefix + stage + '.json'
        manifest = self.reading.read_manifest(relative)
        if manifest.logical.payload_schema != SCHEMA or manifest.materialization.size_bytes > MAX_CHECKPOINT_BYTES:
            raise PermissionError('Matrix export checkpoint changes its bounded operational schema')
        self.reading.verify_manifest(manifest)
        raw = read_bounded_bytes(self.reading.root.resolve(relative, for_write=False), maximum_bytes=MAX_CHECKPOINT_BYTES)
        if (len(raw), sha256(raw).hexdigest()) != (
                manifest.materialization.size_bytes, manifest.materialization.physical_sha256):
            raise PermissionError('Matrix export checkpoint changes its committed bytes')
        document = json.loads(raw)
        if canonical_json_document_bytes(document) != raw:
            raise PermissionError('Matrix export checkpoint is not exact canonical JSON')
        value = document['value']
        expected = self._stage_binding(context, execution, compact=document['version'] == '2.0.0')
        if (document['schema'] != SCHEMA or document['version'] not in ('1.0.0', '2.0.0')
                or value['status'] != 'STAGE_COMPLETE' or value['stage'] != stage
                or not self._binding_matches(value['binding'], version=document['version'], stage=stage)
                or canonical_json_document_bytes(value['stage_binding']) != canonical_json_document_bytes(expected)):
            raise PermissionError('Matrix export checkpoint changes its source, selection, inputs or execution census')
        authenticate_read_file_pins(self.reading, value['files'], require_current=require_current)
        for path in value['manifests']:
            # These are sidecars and publication markers, not protected bodies.
            # Their exact joins share the live read's metadata and final guard.
            original = self.reading.read_manifest(path)
            if original.publication is None:
                raise PermissionError('Matrix export checkpoint loses original complete publication custody')
        require_current()
        report = self._loaded_report(stage, value, context)
        self.completed[stage] = {'path': relative, 'size_bytes': len(raw), 'sha256': sha256(raw).hexdigest(),
            'report': self._report_pin(report)}
        self.reused.append(stage)
        self.reused_sources[stage] = value['binding']['source']
        return report

    @staticmethod
    def _stage_binding(context, execution, *, compact=False):
        return {'bindings': {phase: row.identity.to_document() for phase, row in sorted(context.bindings.items())},
            'pending': dict(context.pending_bindings),
            'execution': ProgrammeExportCheckpoints._report_pin(execution) if compact else execution}

    def save(self, stage, report, *, context, execution, require_current):
        from empirical_lawhood.runtime.progress import report_progress
        report_progress(phase='matrix_export.checkpoint.seal.' + stage)
        require_current()
        self.require_source_current()
        files = dict(self.independent_reads.files)
        current_files = verified_read_file_pins(self.reading)
        current_names = {row[0] for row in current_files}
        for name, size, digest in current_files:
            if files.setdefault(name, (size, digest)) != (size, digest):
                raise PermissionError('Matrix export checkpoint changes independently consumed bytes')
        files = tuple((name, *value) for name, value in sorted(files.items()) if not name.startswith(self.prefix))
        # A child can close before later work in this stage. Rehash its unique
        # inputs at publication and retain them in the parent's final census.
        authenticate_read_file_pins(self.reading, tuple(row for row in files if row[0] not in current_names),
            require_current=require_current)
        originals = tuple(row for name, row in sorted(self.manifests.items()) if not name.startswith(self.prefix))
        parents = tuple(sorted({ArtifactLineageParent(
            ObjectIdentity.from_record('source.' + row.logical.fingerprint(), row.logical),
            row.logical.visibility_ceiling, row.logical.outcome_access) for row in originals}, key=lineage_parent_sort_key))
        access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(row.outcome_access for row in parents))
        ceilings = tuple(row.visibility_ceiling for row in parents)
        stored_report, encoding = self._stored_report(stage, report)
        value = {'stage': stage, 'status': 'STAGE_COMPLETE', 'export_status': 'IN_PROGRESS',
            'binding': json.loads(self.binding), 'stage_binding': self._stage_binding(context, execution, compact=True),
            'files': files, 'manifests': tuple(row.materialization.relative_path for row in originals),
            'report': stored_report, 'report_encoding': encoding, 'reused_stage_sources': dict(self.reused_sources),
            'runtime_relocation_files': tuple((path, *pin) for path, pin in sorted(self.runtime_relocations.items())),
            'scientific_qualification': 'NOT_ESTABLISHED'}
        raw = canonical_json_document_bytes({'schema': SCHEMA, 'version': '2.0.0', 'value': value})
        if len(raw) > MAX_CHECKPOINT_BYTES:
            raise ValueError('Matrix export checkpoint exceeds its operational byte bound')
        require_current()
        name = self.selection.record_id + '.checkpoint.' + stage
        self.owner.writer.write(ArtifactWriteRequest(name, self.prefix + stage + '.json', SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', name, self.prefix.rstrip('/'), raw,
            inherited_visibility(ceilings, access), ceilings, access, lineage_parents=parents))
        self.completed[stage] = {'path': self.prefix + stage + '.json', 'size_bytes': len(raw),
            'sha256': sha256(raw).hexdigest(), 'report': self._report_pin(report)}
        report_progress(phase='matrix_export.checkpoint.saved.' + stage, done=1, total=1)


__all__ = ['ProgrammeExportCheckpoints']
