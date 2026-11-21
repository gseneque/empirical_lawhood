# SPDX-License-Identifier: MPL-2.0
"""Closed derived-observation packages over authenticated original native returns."""

from decimal import Decimal
from hashlib import sha256
import json
import time

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs, scoped_original_reference
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.adapters.matrix_storage.matrix_array_io import encode_matrix_arrays, decode_matrix_arrays, NPZMemberSelection
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.domains.matrix.input_contracts import MatrixArrayMember, MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import validate_relative_locator, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key
from empirical_lawhood.execution.public_source_acquisition import RAW_SOURCE_SCHEMA
from empirical_lawhood.execution.operational_configuration import scientific_reconstruction_enabled


MEMBERS = ('selection.json', 'evidence.json', 'readout.json', 'arrays.npz', 'report.txt')
MAXIMUM_BYTES = MAXIMUM_MATRIX_ARRAY_BYTES


def _json(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


def _originals(sources):
    originals = tuple((s, ObjectIdentity.from_record(s.original_result.result_id, s.original_result))
        for s in sources if s.original_result is not None)
    counts = {}
    for _, pin in originals:
        counts[pin.object_id] = counts.get(pin.object_id, 0)+1
    # Preserve the exact representation of existing single-result packages.
    # Colliding local labels get separate canonical references, never altered
    # native records, fabricated completions or renamed original result IDs.
    return tuple(sorted((scoped_original_reference(s).identity if counts[pin.object_id]>1 else pin
        for s, pin in originals), key=lambda p:p.object_id))


def _parents(sources):
    return tuple(sorted({ArtifactLineageParent(ObjectIdentity.from_record(s.original_result.receipt.receipt_id,
        s.original_result.receipt), VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
        for s in sources if s.original_result is not None}, key=lineage_parent_sort_key))


def _bind_scoped_references(report, sources):
    references = _originals(sources)
    scoped = {pin for pin in references if pin.object_schema == 'empirical-lawhood/rubisco-response/scoped-original-native-reference'}
    if scoped:
        records = tuple(scoped_original_reference(s) for s in sources if s.original_result is not None)
        return dict(report, scoped_original_references=tuple(r.to_document() for r in sorted(records, key=lambda r:r.identity.object_id)
            if r.identity in scoped))
    return report


def export_native_observation_analysis(*, namespace, selection, sources, project_root, artifact_writer,
        output_relative_path, validate, read, evidence_kind, render):
    """Authenticate originals and atomically publish the complete analysis package.

    Original carriers must use the existing native-subwork custody owner.
    This development analysis neither enters a worker nor changes an original.
    """
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    validate_relative_locator(output_relative_path)
    validate_stable_id(namespace)
    validate(selection, sources)
    for name in MEMBERS:
        path = artifact_writer.root.resolve(output_relative_path+'/'+name, for_write=True)
        if path.exists():
            raise ValueError('native observation analysis requires a fresh complete export destination')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    cpu, wall = time.process_time(), time.perf_counter()
    report, arrays = read(selection=selection, sources=sources, assessor_source=provenance.identity)
    report = _bind_scoped_references(report, sources)
    readout = _json(report)
    raw, members = encode_matrix_arrays(arrays)
    references = tuple(sorted((selection.identity, provenance.identity, *_originals(sources)), key=lambda p:p.object_id))
    logical = tuple(ArrayDatasetMember(m.name, m.dtype, m.shape, m.sha256, m.finite_required) for m in members)
    digest = sha256(selection.canonical_bytes()+provenance.canonical_bytes()+raw+readout).hexdigest()
    dataset = ArrayDatasetManifest('dataset.'+namespace+'.'+digest, logical, references)
    artifact = ArtifactIdentity('arrays.'+namespace+'.'+sha256(raw).hexdigest(), namespace+'-arrays',
        RAW_SOURCE_SCHEMA, sha256(raw).hexdigest(), 'application/zip', len(raw))
    recheck_original_native_outputs(sources, description=namespace+' analysis')
    cpu_seconds, wall_seconds = Decimal.from_float(time.process_time()-cpu), Decimal.from_float(time.perf_counter()-wall)
    evidence_digest = sha256((digest+str(cpu_seconds)+str(wall_seconds)).encode('ascii')).hexdigest()
    evidence = evidence_kind('evidence.'+namespace+'.'+evidence_digest, selection.identity, provenance,
        dataset, artifact, FileEvidence('readout.json', len(readout), sha256(readout).hexdigest()), _originals(sources),
        cpu_seconds, wall_seconds)
    records = {'selection.json':selection, 'evidence.json':evidence}
    payloads = {name:record.canonical_bytes() for name,record in records.items()}
    payloads.update({'readout.json':readout, 'arrays.npz':raw, 'report.txt':render(report)})
    if any(len(value) > MAXIMUM_BYTES for value in payloads.values()):
        raise ValueError('complete native observation analysis exceeds its declared export member allocation')
    package = 'package.'+namespace+'.'+sha256(b''.join(sha256(payloads[n]).digest() for n in MEMBERS)).hexdigest()
    parents = _parents(sources)
    writes = []
    for name in MEMBERS:
        profile = ArtifactProfile.CANONICAL_JSON if name in records else ArtifactProfile.RAW_SOURCE_BYTES if name == 'arrays.npz' else ArtifactProfile.TEXT_PARAMETERS
        schema = records[name].SCHEMA if name in records else RAW_SOURCE_SCHEMA if name == 'arrays.npz' else 'empirical-lawhood/rubisco-response/'+namespace+'-text'
        media = 'application/zip' if name == 'arrays.npz' else 'application/json' if name.endswith('.json') else 'text/plain'
        writes.append(ArtifactWriteRequest(namespace+'.'+sha256(payloads[name]).hexdigest()+'.'+name.replace('.','-'),
            output_relative_path+'/'+name, schema, profile, media, package, output_relative_path, payloads[name],
            VisibilityCeiling.DEVELOPMENT_ONLY, tuple(p.visibility_ceiling for p in parents),
            OutcomeAccess.DEVELOPMENT_VISIBLE, lineage_parents=parents))
    publications = artifact_writer.write_batch(tuple(writes))
    return dict(evidence=evidence, report=json.loads(readout), package_id=package, new_native_calls=0,
        paths={name:str(artifact_writer.root.resolve(output_relative_path+'/'+name, for_write=False)) for name in MEMBERS},
        publications=publications)


def read_native_observation_analysis(*, directory_relative_path, sources, artifact_writer, selection_kind, evidence_kind, validate, read, render):
    """Read original retained results; reconstruct only when explicitly selected.

    Both modes authenticate the complete publication, original receipt lineage,
    source contract and original output bytes. Reconstruction adds an independent
    numerical comparison; it never replaces the retained result or its identity.
    JSON containers use their persisted representation in both export and read.
    """
    validate_relative_locator(directory_relative_path)
    reconstruct = scientific_reconstruction_enabled()
    source_checked = False
    manifest = artifact_writer.read_manifest(directory_relative_path+'/evidence.json')
    def exposed(member):
        if (member.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or member.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError('native observation analysis export changes its original evidence lane')
    def consume(members):
        nonlocal source_checked
        expected = {directory_relative_path+'/'+n:n for n in MEMBERS}
        if set(members) != set(expected):
            raise ValueError('native observation analysis export changes the complete closed member census')
        payloads = {name:read_bounded_bytes(artifact_writer.root.resolve(path, for_write=False), maximum_bytes=MAXIMUM_BYTES)
            for path,name in expected.items()}
        selection = decode_canonical_bytes(payloads['selection.json'], selection_kind, maximum_bytes=MAXIMUM_BYTES)
        evidence = decode_canonical_bytes(payloads['evidence.json'], evidence_kind, maximum_bytes=MAXIMUM_BYTES)
        if (evidence.selection != selection.identity or evidence.original_results != _originals(sources)
                or evidence.readout.byte_count != len(payloads['readout.json'])
                or evidence.readout.sha256 != sha256(payloads['readout.json']).hexdigest()):
            raise ValueError('native observation analysis export substitutes its original selection, result or readout')
        validate(selection, sources)
        physical = tuple(MatrixArrayMember(m.name, m.dtype, m.shape, m.sha256, m.finite_required) for m in evidence.arrays.members)
        original_arrays = decode_matrix_arrays(payloads['arrays.npz'], NPZMemberSelection(evidence.array_artifact, physical))
        report = json.loads(payloads['readout.json'])
        if (type(report) is not dict or _json(report) != payloads['readout.json']
                or render(report) != payloads['report.txt']):
            raise ValueError('native observation analysis export changes its original report representation')
        parents = _parents(sources)
        if any(member.logical.lineage_parents != parents for member in members.values()):
            raise ValueError('native observation analysis export changes its original receipt ancestry')
        recheck_original_native_outputs(sources, description='retained analysis entry')
        source_checked = True
        if reconstruct:
            import numpy as np
            current_report, current_arrays = read(selection=selection, sources=sources,
                assessor_source=evidence.provenance.identity)
            current_report = _bind_scoped_references(current_report, sources)
            if (payloads['readout.json'] != _json(current_report)
                    or set(original_arrays) != set(current_arrays)
                    or any(not np.array_equal(original_arrays[key], current_arrays[key]) for key in original_arrays)):
                raise ValueError('native observation analysis export differs from its independently reread original evidence')
        return dict(selection=selection, evidence=evidence, report=report, arrays=original_arrays,
            new_native_calls=0, scientific_reconstruction_performed=reconstruct,
            verification=('ORIGINAL_RECEIPTS_AND_FULL_NUMERICAL_RECONSTRUCTION' if reconstruct
                else 'ORIGINAL_RECEIPTS_AND_RETAINED_RESULTS'))
    try:
        return artifact_writer.verify_manifest_members(manifest, validate_members=consume, before_member=exposed)
    finally:
        if source_checked:
            recheck_original_native_outputs(sources, description='retained analysis closing')
