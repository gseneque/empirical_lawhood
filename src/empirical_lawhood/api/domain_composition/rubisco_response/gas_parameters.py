# SPDX-License-Identifier: MPL-2.0
"""Public preparation, authoring and original-custody reading of gas parameters."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_records import GasParameterEngine, GasParameterSource, MAX_METADATA, prepare_gas_parameter_source
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_operation import GasParameterConfig, GasParameterPairResult, GasParameterReturn, assess_parameter_return
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_translation import gas_parameter_draft
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import GpRepairNumericEngine, NUMERIC_PACKAGES
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.storage.bounded_io import bounded_file_sha256
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


def select_gas_parameter_engine(*, site_packages, interpreter):
    """Bind the existing selected numerical environment without native imports."""
    root, executable = Path(site_packages), Path(interpreter)
    if (not root.is_absolute() or root.is_symlink() or root.resolve() != root
            or not executable.is_absolute() or executable.resolve() != executable):
        raise ValueError('gas parameter environment requires its exact selected real paths')
    numeric, parmed = [], []
    for package in (*NUMERIC_PACKAGES, 'parmed'):
        directory = root/package
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('gas parameter environment is missing its selected package: '+package)
        rows = parmed if package == 'parmed' else numeric
        for path in sorted(directory.rglob('*')):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError('gas parameter environment contains a link or special member')
            if path.is_file():
                size, digest = bounded_file_sha256(path, maximum_bytes=None)
                rows.append(FileEvidence(path.relative_to(root).as_posix(), size, digest))
    numeric, parmed = (tuple(sorted(rows, key=lambda row: row.relative_path)) for rows in (numeric, parmed))
    interpreter_sha = bounded_file_sha256(executable, maximum_bytes=None)[1]
    digest = sha256((''.join(row.fingerprint() for row in numeric)+interpreter_sha).encode('ascii')).hexdigest()
    engine = GpRepairNumericEngine('engine.gas-parameter-numerical.'+digest, str(root), numeric, str(executable), interpreter_sha)
    return GasParameterEngine(engine, parmed)


def author_gas_parameter_pair(*, source, project_root, work_directory, artifact_writer, output_dir):
    """Freeze the complete two-gas wave through the shared author; make no call."""
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.numerical_provenance import capture_numerical_provenance
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest
    exact(source, GasParameterSource)
    source.__post_init__()
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root),
        artifact_writer=artifact_writer)
    inputs = destination.with_name(destination.name+'-native-inputs')
    if inputs.exists() or inputs.is_symlink():
        raise ValueError('gas parameter authoring requires fresh direct-input custody')
    implementation = implementation_binding(project_root)
    provenance = capture_numerical_provenance(project_root=project_root,
        expected_code_sha256=implementation.code_sources_sha256, expected_lock_sha256=implementation.dependency_lock_sha256)
    config = GasParameterConfig('config.gas-parameters.'+source.fingerprint(), source.identity, source.canonical_size_bytes(),
        implementation, provenance, str(work_directory))
    draft = gas_parameter_draft(config)
    relative = inputs.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    scope = 'gas-parameters.native-inputs.'+config.fingerprint()
    records = {'native-source': source, 'native-provenance': provenance}
    bindings = []
    for row in draft.external_inputs:
        name = row.input_id.removeprefix('external.gas-parameters.')
        path = relative+'/'+name+'.json'
        block_size = min(row.maximum_size_bytes, 2**20)
        chunks = (chunk[start:start+block_size] for chunk in records[name].canonical_chunks()
            for start in range(0, len(chunk), block_size))
        artifact_writer.write_stream(ArtifactStreamWriteRequest(row.logical_artifact_id, path, row.payload_schema,
            ArtifactProfile.CANONICAL_JSON, row.media_type, scope, relative, chunks,
            maximum_bytes=row.maximum_size_bytes, maximum_chunk_bytes=block_size,
            expected_size_bytes=row.maximum_size_bytes, expected_physical_sha256=row.expected_content_sha256,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
        bindings.append((row.input_id, artifact_writer.root.resolve(path, for_write=False)))
    result = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=tuple(bindings))
    return {**result, 'native_input_paths': {name: str(path) for name, path in bindings}}


def read_gas_parameter_pair(*, source, original_result, native_subwork):
    """Reassess both authenticated original returns without any reconstruction call."""
    exact(source, GasParameterSource)
    exact(original_result, GasParameterPairResult)
    if original_result.source != source.identity:
        raise ValueError('gas parameter retained read substitutes its original selected source')
    units = []
    for original in original_result.units:
        definition = original.definition
        completed = native_subwork.recover(definition)
        if (completed is None or completed.completion != original.completion or completed.receipt != original.receipt
                or definition.configuration != source.identity):
            raise ValueError('gas parameter retained read loses its original native receipt')
        returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'build.return')),
            GasParameterReturn, maximum_bytes=MAX_METADATA)
        if returned != original.returned:
            raise ValueError('gas parameter retained read substitutes its original raw return')
        units.append(assess_parameter_return(source, definition, returned, completed, native_subwork))
    return GasParameterPairResult(source.identity, tuple(units))


__all__ = ('GasParameterEngine', 'GasParameterSource', 'select_gas_parameter_engine', 'prepare_gas_parameter_source',
    'author_gas_parameter_pair', 'read_gas_parameter_pair')
