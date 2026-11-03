# SPDX-License-Identifier: MPL-2.0
"""Retain a complete E4 bank publication before any child was authored.

This read-only exception authenticates the original six metadata products.
It admits no partial publication, arbitrary directory or successor execution.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.runtime.artifacts import ArtifactPublicationScope, artifact_publication_member


def _namespace(context, directory, *, paths=None, locks=()):
    from itertools import islice

    if (directory.is_symlink() or not directory.is_dir()
            or tuple(islice(directory.iterdir(), 2)) != (directory / 'original-banks',)):
        raise PermissionError('completed source handoff requires only the exact retained E4 bank directory')
    bank = directory / 'original-banks'
    if bank.is_symlink() or not bank.is_dir():
        raise PermissionError('completed source handoff refuses a symbolic or missing E4 bank directory')
    if paths is None:
        names = {phase + '.' + kind + '.json' for phase in ('development', 'calibration', 'confirmation')
            for kind in ('bank', 'programme')}
        files = names | {name + '.manifest.json' for name in names}
        pair_locks = {'.artifact-pair.' + sha256((name + '\0' + name + '.manifest.json').encode()).hexdigest()[:24] + '.lock'
            for name in names}
        children = tuple(islice(bank.iterdir(), len(files | pair_locks) + 2))
        if (len(children) > len(files | pair_locks) + 1 or not files <= {path.name for path in children}
                or any(path.is_symlink() or path.name not in files | pair_locks | {'.publication-batches'}
                    or (not path.is_dir() if path.name == '.publication-batches' else not path.is_file())
                    or path.name in pair_locks and path.stat().st_size != 0 for path in children)):
            raise PermissionError('completed source handoff refuses incomplete or foreign E4 metadata')
        return
    pending = [bank]
    seen = set()
    while pending:
        parent = pending.pop()
        for path in parent.iterdir():
            if path.is_symlink() or path not in paths or path in seen:
                raise PermissionError('completed source handoff E4 metadata namespace changed')
            context.writer.root.resolve(path.relative_to(context.writer.root.contract.canonical_path).as_posix(), for_write=False)
            seen.add(path)
            if path in locks:
                if not path.is_file() or path.stat().st_size != 0:
                    raise PermissionError('completed source handoff E4 metadata lock changed')
            elif paths[path] == 'directory':
                if not path.is_dir():
                    raise PermissionError('completed source handoff E4 metadata directory changed')
                pending.append(path)
            elif not path.is_file():
                raise PermissionError('completed source handoff E4 metadata member changed')
    if seen != set(paths):
        raise PermissionError('completed source handoff E4 metadata member disappeared')


def _authenticate_members(context, directory, requests):
    writer = context.writer
    root = Path(writer.root.contract.canonical_path)
    if len(requests) != 6:
        raise PermissionError('completed source handoff requires the exact six original E4 metadata members')
    manifests = []
    for request in requests:
        manifest = writer.read_manifest(request.relative_path)
        logical, physical, publication = manifest.logical, manifest.materialization, manifest.publication
        digest = sha256(request.payload).hexdigest()
        expected_scope = ArtifactPublicationScope(request.publication_scope_id, writer.root.contract.storage_root_id,
            request.publication_scope_relative_root, request.visibility_ceiling, request.outcome_access)
        if (publication is None or publication.publication_scope != expected_scope
                or (logical.logical_artifact_id, logical.payload_schema, logical.profile, logical.media_type,
                    logical.content_sha256, logical.outcome_access, logical.visibility_ceiling,
                    logical.parent_visibility_ceilings, logical.lineage_parents) !=
                (request.logical_artifact_id, request.payload_schema, request.profile, request.media_type,
                    digest, request.outcome_access, request.visibility_ceiling,
                    request.parent_visibility_ceilings, request.lineage_parents)
                or (physical.relative_path, physical.storage_root_id, physical.size_bytes, physical.physical_sha256,
                    physical.compression, physical.partition_selector) !=
                (request.relative_path, writer.root.contract.storage_root_id, len(request.payload), digest, 'none', None)):
            raise PermissionError('completed source handoff changes its exact original E4 bank publication')
        manifests.append(manifest)
    publications = {value.publication for value in manifests}
    if len(publications) != 1:
        raise PermissionError('completed source handoff requires one complete original E4 metadata publication')
    publication, = publications
    if set(publication.members) != {artifact_publication_member(value.logical, value.materialization) for value in manifests}:
        raise PermissionError('completed source handoff E4 metadata publication includes a foreign member')
    paths, locks = {}, set()
    for manifest in manifests:
        path = root / manifest.materialization.relative_path
        paths[path] = paths[Path(str(path) + '.manifest.json')] = 'file'
        token = sha256((path.name + '\0' + path.name + '.manifest.json').encode()).hexdigest()[:24]
        lock = path.parent / ('.artifact-pair.' + token + '.lock')
        if lock.exists():
            paths[lock] = 'file'; locks.add(lock)
    commit = root / publication.commit_marker_relative_path
    paths[commit] = 'file'
    paths[commit.parent] = paths[commit.parent.parent] = 'directory'
    lock = commit.parent / ('.publication-batch.' + sha256(str(commit).encode()).hexdigest()[:24] + '.lock')
    if lock.exists():
        paths[lock] = 'file'; locks.add(lock)
    _namespace(context, directory, paths=paths, locks=locks)
    writer.verify_manifests(tuple(manifests))
    return lambda: _namespace(context, directory, paths=paths, locks=locks)


@contextmanager
def retained_e4_bank_metadata(context):
    from .matrix_programme_completed_continuation import require_unentered_successors
    from .matrix_programme_e4_inputs import authenticated_programme_e4_banks, programme_e4_bank_requests
    from .matrix_programme_e4_phases import _source_request

    directory = context.metadata_directory('e4.development')
    if not directory.exists() and not directory.is_symlink():
        yield None
        return
    # This shape-only pass performs no publication or source handoff. Complete
    # original scientific and publication authentication must precede the yield.
    require_unentered_successors(context, retained_metadata=lambda: _namespace(context, directory))
    with context.e3_originals(publish=False) as original:
        request = _source_request(context, 'e4.development', original)
        with authenticated_programme_e4_banks(artifact_writer=context.writer,
                input_commitments=request.input_commitments, original_e3=request.original_e3,
                original_preparation=request.original_preparation, original_assay=request.original_assay,
                original_products=request.original_products, native_training_locator=request.native_training_locator,
                maximum_source_bytes=request.source_budget.source_scan_bytes) as composed:
            requests = programme_e4_bank_requests(composed, original_e3=request.original_e3,
                prefix=(directory / 'original-banks').relative_to(context.writer.root.contract.canonical_path).as_posix())
            original.require_current()
            require_namespace = _authenticate_members(context, directory, requests)
            # Exact published bytes now belong to the live snapshot census.
            # Their temporary expected byte copies are no longer needed.
            del requests, request

            def require_current():
                original.require_current()
                require_namespace()
                context.writer.require_verification_snapshot()

            require_current()
            try:
                yield require_current
            finally:
                require_current()
