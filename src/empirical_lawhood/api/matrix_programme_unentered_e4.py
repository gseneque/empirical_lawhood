# SPDX-License-Identifier: MPL-2.0
"""Retain stopped E4 input preparation during an explicit source handoff."""
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import os
import stat

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes


def _input_snapshot(writer, plan, run_id, *, retain_paths=None):
    from .recursive_unentered import require_input_only_run
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    require_input_only_run(writer, plan, run_id)
    root = writer.root.resolve('runs/' + run_id + '/inputs', for_write=False)
    if not root.exists():
        return sha256(canonical_json_bytes(())).hexdigest()
    maximum = writer.custody_limits.publication_members
    rows, pending = [], [root]
    paths = {}
    while pending:
        directory = pending.pop()
        paths[directory] = _path_identity(directory)
        for path in sorted(directory.iterdir()):
            if path.is_symlink():
                raise PermissionError('unentered E4 source handoff refuses symbolic input custody')
            relative = path.relative_to(writer.root.contract.canonical_path).as_posix()
            writer.root.resolve(relative, for_write=False)
            if path.is_dir():
                rows.append((relative, 'directory', None))
                pending.append(path)
            elif path.is_file():
                size, digest = bounded_file_sha256(path,
                    maximum_bytes=writer.custody_limits.in_memory_payload_bytes)
                rows.append((relative, size, digest))
                paths[path] = _path_identity(path)
            else:
                raise PermissionError('unentered E4 source handoff requires ordinary input files')
            if maximum is not None and len(rows) > maximum:
                raise ValueError('unentered E4 input custody exceeds the selected member bound')
    if retain_paths is not None:
        retain_paths.update(paths)
    return sha256(canonical_json_bytes(tuple(sorted(rows)))).hexdigest()


def _path_identity(path):
    value = os.stat(path, follow_symlinks=False)
    if not (stat.S_ISREG(value.st_mode) or stat.S_ISDIR(value.st_mode)):
        raise PermissionError('unentered E4 input custody requires ordinary files and directories')
    return value.st_mode, value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _require_input_paths(writer, run_id, paths):
    """Check the complete namespace between the initial and final byte reads.

    The ordinary execution lock remains held. Strict verification still uses
    the full byte snapshot at every checkpoint; reduced verification owns one
    final full comparison, including unpublished partial input controls.
    """
    root = writer.root.resolve('runs/' + run_id, for_write=False)
    if (root.is_symlink() or not root.is_dir()
            or any(path.name not in ('inputs', '.native-execution.lock') for path in root.iterdir())):
        raise PermissionError('unentered E4 run acquired execution custody')
    inputs = root / 'inputs'
    lock = root / '.native-execution.lock'
    if lock.exists() or lock.is_symlink():
        identity = _path_identity(lock)
        if not stat.S_ISREG(identity[0]) or identity[3]:
            raise PermissionError('unentered E4 run changes its coordination lock')
    current, pending = {}, [inputs] if inputs.exists() or inputs.is_symlink() else []
    while pending:
        directory = pending.pop()
        current[directory] = _path_identity(directory)
        for path in directory.iterdir():
            identity = _path_identity(path)
            current[path] = identity
            if len(current) > len(paths):
                raise PermissionError('unentered E4 source handoff adds partial input custody')
            if stat.S_ISDIR(identity[0]):
                pending.append(path)
    if current != paths:
        raise PermissionError('unentered E4 source handoff changes original partial input custody')


@dataclass(frozen=True)
class UnenteredE4Custody:
    binding: ObjectIdentity
    packet: ObjectIdentity
    plan: ObjectIdentity
    run_id: str
    inputs_sha256: str
    require_current: object

    @property
    def fields(self):
        return self.binding, self.packet, self.plan, self.run_id, self.inputs_sha256


@contextmanager
def unentered_e4_custody(context, *, expected=None):
    """Hold the ordinary execution lock and refuse any actual execution record."""
    from .experiment_execution_read import load_development_execution_controls
    from .matrix_researcher_programme_lineage import read_published_record
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.progress import report_progress
    if 'e4.development' not in context.bindings:
        if expected is not None:
            raise PermissionError('unentered E4 handoff lost its original authored binding')
        yield None
        return
    if context.pending_bindings:
        raise PermissionError('unentered E4 handoff refuses an incomplete binding publication')
    binding = context.binding('e4.development')
    from .selected_e4_bank_recipe import _publication_from_manifest
    from dataclasses import replace
    for publication in binding.publications:
        manifest = context.writer.read_manifest(publication.materialization.relative_path)
        if _publication_from_manifest(context.writer, manifest) != replace(publication, created=False):
            raise PermissionError('unentered E4 handoff changes original derived input publication custody')
        context.writer.verify_manifest(manifest)
    report_progress(phase='matrix.continuation.stopped-e4.controls')
    packet, run, plan, _, _, access = load_development_execution_controls(
        directory=context.child_directory('e4.development'), artifact_writer=context.writer)
    members = tuple(row.identity for row in packet.members if row.filename == 'experiment-specification.json')
    if len(members) != 1 or (members[0].object_schema, members[0].object_version, members[0].object_fingerprint) != (
            binding.specification.identity.object_schema, binding.specification.identity.object_version,
            binding.specification.identity.object_fingerprint):
        raise PermissionError('unentered E4 handoff substitutes the bound scientific child')
    plan_pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    store = ExternalNativeEffectContactStore(plane=context.writer, execution_plan=plan_pin,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    with store.execution_lock(run.run_plan_id):
        report_progress(phase='matrix.continuation.stopped-e4.inputs')
        paths = {}
        inputs_sha256 = _input_snapshot(context.writer, plan, run.run_plan_id, retain_paths=paths)
        fields = (binding.identity, ObjectIdentity.from_record(packet.packet_id, packet),
            plan_pin, run.run_plan_id, inputs_sha256)
        if expected is not None and fields != (expected.unentered_e4_binding, expected.unentered_e4_packet,
                expected.unentered_e4_plan, expected.unentered_e4_run_id, expected.unentered_e4_inputs_sha256):
            raise PermissionError('unentered E4 handoff changes the original stopped child or partial inputs')
        live = True

        def require_current(*, final=False):
            if not live:
                raise PermissionError('unentered E4 custody escaped its execution lock')
            relative = (context.directory / 'bindings/e4.development.json').relative_to(
                context.writer.root.contract.canonical_path).as_posix()
            if read_published_record(context.writer, relative, MatrixProgrammePhaseBinding, 64 * 1024**2) != binding:
                raise PermissionError('unentered E4 source handoff changes its original binding')
            from empirical_lawhood.infrastructure.artifacts import _ScopedArtifactPlane
            reduced = (type(context.writer) is _ScopedArtifactPlane
                and context.writer._reduced_read_verification())
            if final or not reduced:
                if _input_snapshot(context.writer, plan, run.run_plan_id) != inputs_sha256:
                    raise PermissionError('unentered E4 source handoff changes original partial input custody')
            else:
                _require_input_paths(context.writer, run.run_plan_id, paths)
            if access is not None:
                access.require_current()
            context.writer.require_verification_snapshot()

        try:
            yield UnenteredE4Custody(*fields, require_current)
        finally:
            try:
                require_current(final=True)
            finally:
                live = False
