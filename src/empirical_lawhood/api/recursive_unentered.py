# SPDX-License-Identifier: MPL-2.0
"""Recognize interrupted input preparation without erasing its custody."""
from pathlib import Path


def require_input_only_run(writer, plan, run_id):
    """Refuse every execution record; authenticate any already committed input.

    An incomplete pair is preserved for the ordinary writer's exact recovery.
    The caller must still authenticate all inputs before it dispatches a task.
    """
    root = writer.root.resolve('runs/' + run_id, for_write=False)
    if not root.exists() and not root.is_symlink():
        return
    if root.is_symlink() or not root.is_dir() or any(p.name not in ('inputs', '.native-execution.lock') for p in root.iterdir()):
        raise PermissionError('unentered recovery requires an absent or input-only run namespace')
    lock = root / '.native-execution.lock'
    if lock.exists() or lock.is_symlink():
        if lock.is_symlink() or not lock.is_file() or lock.stat().st_size:
            raise PermissionError('unentered run changes its coordination lock')
    selected = {}
    for task in plan.tasks:
        for spec in task.external_inputs:
            previous = selected.get(spec.logical_artifact_id)
            if previous is not None:
                from dataclasses import replace
                if replace(spec, input_id=previous.input_id) != previous:
                    raise PermissionError('unentered run has conflicting input contracts')
            selected[spec.logical_artifact_id] = spec
    inputs = root / 'inputs'
    if not inputs.exists():
        return
    if inputs.is_symlink() or not inputs.is_dir():
        raise PermissionError('unentered run input namespace is not a directory')
    # The writer owns hidden publication controls and exact partial-pair repair.
    # Unknown visible members cannot become an implicit recovery permission.
    for path in inputs.iterdir():
        if path.is_symlink():
            raise PermissionError('unentered run contains a symbolic input')
        if path.name.startswith('.'):
            if not (path.name.startswith('.artifact-pair.') or path.name == '.publication-batches'):
                raise PermissionError('unentered run contains a foreign input control')
            continue
        if path.name.endswith('.manifest.json'):
            continue
        if path.name == 'producing-provenance.json':
            # The ordinary execution owner writes this before its input
            # materialization loop. It is retained preparation, not contact.
            from .recursive_execution import _provenance
            provenance = _provenance(plane=writer, run_id=run_id)
            if provenance.observed_git_head != plan.implementation_commit:
                raise PermissionError('unentered run changes its original producing source')
            continue
        if not path.is_file() or not path.name.startswith('input-') or path.suffix not in ('.json', '.npz'):
            raise PermissionError('unentered run contains a foreign input member')
        sidecar = Path(str(path) + '.manifest.json')
        if sidecar.exists():
            relative = path.relative_to(writer.root.contract.canonical_path).as_posix()
            manifest = writer.read_manifest(relative)
            spec = selected.get(manifest.logical.logical_artifact_id)
            if spec is None or (manifest.logical.content_sha256, manifest.logical.payload_schema,
                    manifest.logical.media_type, manifest.materialization.size_bytes) != (
                    spec.expected_content_sha256, spec.expected_payload_schema,
                    spec.expected_media_type, spec.expected_size_bytes):
                raise PermissionError('unentered run changes its frozen input identity')
            writer.verify_manifest(manifest)
