# SPDX-License-Identifier: MPL-2.0
"""Prepare, author, read and export original finite-slab reactive-flux work."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeRawSources, prepare_raw_sources
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_records import PreparedReactiveFlux, ReactiveFluxRule, ReactiveFluxEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_preparation import prepare_reactive_flux
from empirical_lawhood.domains.rubisco.rubisco_response.reactive_flux_read import RetainedReactiveFluxShot, validate_reactive_flux_inputs, read_reactive_flux
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory, preflight_output_directory
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, _parents, export_native_observation_analysis, read_native_observation_analysis
from empirical_lawhood.api.domain_composition.rubisco_response.periodic_trajectory import author_reference_trajectory


def author_reactive_flux(*, prepared, sources, raw_sources, project_root, work_directory, artifact_writer, output_dir):
    """Reproduce every selected phase and author all returned shot IDs once.

    The shared trajectory author owns drafts, plans and direct inputs. Its
    ordinary run/recovery route retains native attempt authority. This action
    starts no native task and grants no scientific or spending permission.
    """
    exact(prepared,PreparedReactiveFlux)
    destination = preflight_authoring_output_directory(directory=Path(output_dir),repo_root=Path(project_root),artifact_writer=artifact_writer)
    work = preflight_output_directory(directory=Path(work_directory))
    if work == destination or work.is_relative_to(destination) or destination.is_relative_to(work):
        raise ValueError('flux native work and authoring custody require separate selected destinations')
    if type(raw_sources) is not tuple or any(type(s) is not PeriodicProbeRawSources for s in raw_sources):
        raise TypeError('flux authoring requires complete original raw-source records')
    raw_by_id = {s.identity:s for s in raw_sources}
    needed = {s.config.original.raw_sources for s in sources}
    if len(raw_by_id) != len(raw_sources) or set(raw_by_id) != needed:
        raise ValueError('flux authoring changes the complete original raw-source census')
    for source in sources:
        raw = raw_by_id[source.config.original.raw_sources]
        prototype = source.config.original.selection
        if prepare_raw_sources(prototype,raw.topology_utf8.encode('ascii'),raw.coordinates_utf8.encode('ascii')) != raw:
            raise ValueError('flux authoring substitutes original raw source bytes')
        original_coordinates(prototype,source.representation,raw)
    current = prepare_reactive_flux(rule=prepared.rule,sources=sources,assessor_source=prepared.assessor_source)
    if current['prepared'] != prepared:
        raise ValueError('flux authoring changes the independently derived complete phase census')
    if not prepared.complete_equilibrium_census or not prepared.shots:
        raise ValueError('flux authoring has no complete original dividing-configuration population')
    root = Path(artifact_writer.root.contract.canonical_path)
    relative = destination.relative_to(root).as_posix()
    parents = _parents(sources)
    artifact_writer.write(ArtifactWriteRequest(prepared.preparation_id,relative+'/preparation.json',prepared.SCHEMA,
        ArtifactProfile.CANONICAL_JSON,'application/json',prepared.preparation_id,relative,prepared.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY,tuple(p.visibility_ceiling for p in parents),OutcomeAccess.DEVELOPMENT_VISIBLE,
        lineage_parents=parents))
    preparation_parent = ArtifactLineageParent(prepared.identity,VisibilityCeiling.DEVELOPMENT_ONLY,OutcomeAccess.DEVELOPMENT_VISIBLE)
    ancestry = tuple(sorted((*parents,preparation_parent),key=lineage_parent_sort_key))
    originals = {s.trace_id:s for s in sources}
    children = {}
    for shot in prepared.shots:
        source = originals[shot.phase_source.trace_id]
        raw = raw_by_id[source.config.original.raw_sources]
        children[shot.shot_id] = author_reference_trajectory(selection=shot.selection,prototype=source.config.original.selection,
            representation=source.representation,raw_topology=raw.topology_utf8.encode('ascii'),raw_coordinates=raw.coordinates_utf8.encode('ascii'),
            phase_bytes=current['phase_bytes'][shot.shot_id],project_root=project_root,work_directory=work/shot.shot_id,
            artifact_writer=artifact_writer,output_dir=destination/'shots'/shot.shot_id,lineage_parents=ancestry)
    recheck_original_native_outputs(sources,description='reactive-flux authoring')
    return dict(preparation_path=str(destination/'preparation.json'),shots=children,new_native_calls=0,
        phase_source_scope='ORIGINAL_EQUILIBRIUM_CONFIGURATIONS_WITH_DECLARED_ANTITHETIC_MAXWELL_MOMENTA')


def read_reactive_flux_preparation(*, relative_path, sources, artifact_writer, maximum_bytes):
    manifest = artifact_writer.read_manifest(relative_path)
    artifact_writer.verify_manifest(manifest)
    if (manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or manifest.logical.lineage_parents != _parents(sources)):
        raise ValueError('flux preparation changes its original receipt ancestry or evidence lane')
    raw = read_bounded_bytes(artifact_writer.root.resolve(relative_path,for_write=False),maximum_bytes=maximum_bytes)
    prepared = decode_canonical_bytes(raw,PreparedReactiveFlux,maximum_bytes=maximum_bytes)
    current = prepare_reactive_flux(rule=prepared.rule,sources=sources,assessor_source=prepared.assessor_source)
    if current['prepared'] != prepared:
        raise ValueError('flux preparation changes independently reconstructed original phases')
    artifact_writer.verify_manifest(manifest)
    return current


def _text(report):
    lines = ['Conditional finite-slab reactive-flux assessment','',
        f"Assigned shots: {report['assigned_shots']}; supplied results: {report['supplied_results']}; complete shots: {report['complete_shots']}.",
        'Every original equilibrium window, shot, failure and cost remains in the source census.',
        'The positive-flux prefactor uses natural masses and explicit unconstrained Cartesian Maxwell momenta.',
        'The finite slab approximates a dividing delta measure. Its zero-time signed antithetic correlation is zero.',
        'Plateau, width, coordinate, physical-step and committor controls remain explicit.',
        'Negative transmission and incomplete bootstrap draws are retained without clipping or successful-subset selection.','']
    for key,row in report['cases'].items():
        lines.append(key+': '+row['conditional_flux_assessment'])
    lines.extend(('', 'The joint block estimate retains every original momentum pair within its configuration.',
        'It does not guarantee coverage of hidden equilibrium modes or unseen momentum tails.',
        'Classical dynamics, chemical accuracy, ensemble validity and physical-rate admission remain UNEVALUABLE.',''))
    return '\n'.join(lines).encode('utf-8')


def export_reactive_flux(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='reactive-flux',selection=selection,sources=sources,
        project_root=project_root,artifact_writer=artifact_writer,output_relative_path=output_relative_path,
        validate=validate_reactive_flux_inputs,read=read_reactive_flux,evidence_kind=ReactiveFluxEvidence,render=_text)


def read_reactive_flux_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_reactive_flux_inputs, directory_relative_path=directory_relative_path,sources=sources,
        artifact_writer=artifact_writer,selection_kind=ReactiveFluxRule,evidence_kind=ReactiveFluxEvidence,
        read=read_reactive_flux,render=_text)


__all__ = ('MEMBERS','RetainedReactiveFluxShot','prepare_reactive_flux','author_reactive_flux',
    'read_reactive_flux_preparation','validate_reactive_flux_inputs','read_reactive_flux',
    'export_reactive_flux','read_reactive_flux_export')
