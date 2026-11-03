# SPDX-License-Identifier: MPL-2.0
"""Bounded exact E2 analysis custody for the prospective curve amendment."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_researcher_programme import curve_amendment as domain
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from .matrix_researcher_programme_lineage import read_published_record


def evidence_snapshots(specification):
    """Read only the explicitly selected small originals, never derived arrays."""
    rows = []
    for selection in specification.analyses:
        for member, selected in selection.files:
            path = Path(selected.path)
            if any(value.is_symlink() for value in (path, *path.parents)):
                raise ValueError('amendment evidence refuses linked source paths')
            raw = read_bounded_bytes(path, maximum_bytes=selected.size_bytes)
            if (len(raw), sha256(raw).hexdigest()) != (selected.size_bytes, selected.sha256):
                raise PermissionError('amendment evidence changes its selected original bytes')
            rows.append(domain.MatrixAmendmentEvidenceSnapshot(
                'amendment-evidence.' + specification.fingerprint() + '.' + selection.analysis + '.' + member,
                selection.analysis, member, selected, raw.decode('utf-8')))
    return tuple(rows)


def validate_evidence(specification, snapshots, exposure, provenance):
    expected = tuple((selection.analysis, member, selected)
        for selection in specification.analyses for member, selected in selection.files)
    if tuple((row.analysis, row.member, row.original) for row in snapshots) != expected:
        raise PermissionError('amendment changes its complete exact exposed evidence census')
    for row in snapshots:
        row.__post_init__()
    selected = {(row.analysis, row.member): row for row in snapshots}
    documents = {(analysis, member): json.loads(row.utf8_text)
        for (analysis, member), row in selected.items() if member != 'report'}
    roots = dict(exposure.exposed_roots)['e2']
    protocols = dict(exposure.e2_protocols)
    for analysis in domain.ANALYSES:
        spec = documents[analysis, 'specification']
        complete = documents[analysis, 'completion']
        if (tuple(spec.get('root_ids', ())) != roots or set(spec.get('protocols', {})) != set(roots)
                or any(spec['protocols'][root].get('sha256') != protocols[root].object_fingerprint for root in roots)
                or spec.get('new_native_acquisitions') != 0 or complete.get('new_native_acquisitions') != 0):
            raise PermissionError('amendment analysis substitutes an original E2 root/protocol or new acquisition')
        manifest = documents[analysis, 'manifest']
        members = manifest.get('files' if analysis == domain.ANALYSES[0] else 'members', ())
        paths = [row['path'] for row in members]
        if len(paths) != len(set(paths)):
            raise PermissionError('amendment analysis aliases distinct manifest members')
        members = dict(zip(paths, members, strict=True))
        for member in ('specification', 'report'):
            original = selected[analysis, member].original
            relative = Path(original.path).relative_to(Path(selected[analysis, 'manifest'].original.path).parent).as_posix()
            actual = members.get(relative, {})
            if (actual.get('sha256'), actual.get('size_bytes', actual.get('bytes'))) != (original.sha256, original.size_bytes):
                raise PermissionError('amendment analysis drops its original specification/report manifest binding')
        manifest_key = 'artifact_manifest_sha256' if analysis == domain.ANALYSES[0] else 'manifest_sha256'
        if complete.get(manifest_key) != selected[analysis, 'manifest'].original.sha256:
            raise PermissionError('amendment analysis changes its original completion/manifest binding')
    first, followup = domain.ANALYSES
    initial, later = documents[first, 'completion'], documents[followup, 'completion']
    if (documents[first, 'specification'].get('producing_commit') != provenance.observed_git_head
            or initial.get('status') != 'COMPLETED_ALL_AVAILABLE_REQUIRED_STAGES'
            or initial.get('root_count') != len(roots) or initial.get('view_count') != 2 * len(roots)
            or initial.get('original_endpoints_unchanged') is not True
            or later.get('status') != 'COMPLETE_ALL_96_ROOTS_BOTH_VIEWS'
            or later.get('original_scientific_disposition') != 'UNCHANGED'
            or later.get('report_sha256') != selected[followup, 'report'].original.sha256
            or documents[followup, 'specification'].get('root_denominator') != len(roots)):
        raise PermissionError('amendment changes the exposed analyses original completion, source or scientific standing')
    prior = documents[followup, 'specification'].get('prior_pins', {})
    for member in ('completion', 'manifest', 'specification'):
        original = selected[first, member].original
        if prior.get(Path(original.path).name) != original.sha256:
            raise PermissionError('amendment follow-up loses the exact original analysis it extended')


def publish_evidence(writer, specification, snapshots, metadata_directory, *, admit_output):
    """Publish exposed source snapshots without occupying reserved sidecar names."""
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeProducedInput
    rows = []
    for snapshot in snapshots:
        path = Path(metadata_directory) / 'exposed-evidence' / (snapshot.analysis + '.' + snapshot.member + '.snapshot.json')
        raw = snapshot.canonical_bytes()
        admit_output(raw)
        relative = path.relative_to(writer.root.contract.canonical_path).as_posix()
        publication = writer.write(ArtifactWriteRequest(snapshot.record_id, relative, snapshot.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, 'application/json', specification.specification_id,
            Path(relative).parent.as_posix(), raw, VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        rows.append(MatrixProgrammeProducedInput(snapshot.identity, publication))
    return tuple(rows)


def read_evidence(writer, record, provenance):
    """Reopen published snapshots; original external analysis paths are provenance."""
    from .selected_e4_bank_recipe import _publication_from_manifest
    rows = []
    for selected in record.evidence:
        publication = selected.publication
        if (publication.logical.outcome_access, publication.logical.visibility_ceiling) != (
                OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY):
            raise PermissionError('amendment cannot relabel exposed analysis as blind or confirmatory')
        relative = publication.materialization.relative_path
        row = read_published_record(writer, relative, domain.MatrixAmendmentEvidenceSnapshot,
            publication.materialization.size_bytes)
        selected.require_record(row, row.identity)
        if _publication_from_manifest(writer, writer.read_manifest(relative)) != replace(publication, created=False):
            raise PermissionError('amendment changes exact published analysis custody')
        rows.append(row)
    validate_evidence(record.specification, tuple(rows), record.exposure, provenance)
    return tuple(rows)
