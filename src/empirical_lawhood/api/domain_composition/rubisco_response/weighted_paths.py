# SPDX-License-Identifier: MPL-2.0
"""Author exact weighted descendants through the existing native operations."""

from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeRawSources, prepare_raw_sources
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import ReferenceEquilibriumSelection
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_continuation import PreparedWeightedContinuation, prepare_weighted_continuation
from empirical_lawhood.domains.rubisco.rubisco_response.weighted_path_population import WeightedPathCampaign, WeightedPathEvidence, read_weighted_path_campaign, validate_weighted_path_campaign_inputs
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory, preflight_output_directory
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.storage.contracts.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, lineage_parent_sort_key
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import _parents, export_native_observation_analysis, read_native_observation_analysis
from empirical_lawhood.api.domain_composition.rubisco_response.periodic_trajectory import author_reference_trajectory
from empirical_lawhood.api.domain_composition.rubisco_response.periodic_equilibrium import author_reference_equilibrium


def author_weighted_continuation(*, prepared, histories, raw_sources, project_root,
        work_directory, artifact_writer, output_dir):
    """Authenticate all parents, freeze preparation and author every child.

    Returned child paths belong to the ordinary recursive author. No task IDs,
    execution plans, native contacts or scientific permissions are invented here.
    An incomplete authoring keeps its files; another destination may be selected.
    """
    exact(prepared, PreparedWeightedContinuation)
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root),
        artifact_writer=artifact_writer)
    work = preflight_output_directory(directory=Path(work_directory))
    if work == destination or work.is_relative_to(destination) or destination.is_relative_to(work):
        raise ValueError('weighted native work and authoring custody need separate selected destinations')
    if type(raw_sources) is not tuple or any(type(s) is not PeriodicProbeRawSources for s in raw_sources):
        raise TypeError('weighted authoring requires complete original raw-source records')
    raw_by_id = {s.identity:s for s in raw_sources}
    originals = tuple(s for h in histories for s in h.segments)
    needed = {s.config.original.raw_sources for s in originals}
    if len(raw_by_id) != len(raw_sources) or set(raw_by_id) != needed:
        raise ValueError('weighted authoring changes its complete original raw-source census')
    for source in originals:
        raw = raw_by_id[source.config.original.raw_sources]
        prototype = source.config.original.selection
        checked = prepare_raw_sources(prototype, raw.topology_utf8.encode('ascii'), raw.coordinates_utf8.encode('ascii'))
        if checked != raw:
            raise ValueError('weighted authoring substitutes original raw source bytes')
        original_coordinates(prototype, source.representation, raw)
    reproduced = prepare_weighted_continuation(rule=prepared.rule, resampling=prepared.resampling,
        histories=histories, assessor_source=prepared.assessor_source)
    if reproduced['prepared'] != prepared:
        raise ValueError('weighted authoring substitutes the independently derived continuation')
    root = Path(artifact_writer.root.contract.canonical_path)
    relative = destination.relative_to(root).as_posix()
    parents = _parents(originals)
    artifact_writer.write(ArtifactWriteRequest(prepared.preparation_id, relative+'/preparation.json', prepared.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', prepared.preparation_id, relative, prepared.canonical_bytes(),
        VisibilityCeiling.DEVELOPMENT_ONLY, tuple(p.visibility_ceiling for p in parents), OutcomeAccess.DEVELOPMENT_VISIBLE,
        lineage_parents=parents))
    preparation_parent = ArtifactLineageParent(prepared.identity, VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE)
    children = {}
    for child in prepared.children:
        parent = reproduced['parent_readouts'][child.parent_path_id]
        source = parent['source']
        raw = raw_by_id[source.config.original.raw_sources]
        author = author_reference_equilibrium if type(child.selection) is ReferenceEquilibriumSelection else author_reference_trajectory
        children[child.path_id] = author(selection=child.selection, prototype=source.config.original.selection,
            representation=source.representation, raw_topology=raw.topology_utf8.encode('ascii'),
            raw_coordinates=raw.coordinates_utf8.encode('ascii'), phase_bytes=reproduced['phase_bytes'][child.path_id],
            project_root=project_root, work_directory=work/child.path_id, artifact_writer=artifact_writer,
            output_dir=destination/'children'/child.path_id,
            lineage_parents=tuple(sorted((*parents, preparation_parent), key=lineage_parent_sort_key)))
    recheck_original_native_outputs(originals, description='weighted continuation authoring')
    return dict(preparation_path=str(destination/'preparation.json'), children=children, new_native_calls=0,
        phase_source_scope='EXACT_AUTHENTICATED_ORIGINAL_ENDPOINTS')


def read_weighted_continuation_preparation(*, relative_path, histories, artifact_writer, maximum_bytes):
    """Authenticate the retained preparation and derive every original phase again."""
    manifest = artifact_writer.read_manifest(relative_path)
    artifact_writer.verify_manifest(manifest)
    if (manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or manifest.logical.lineage_parents != _parents(tuple(s for h in histories for s in h.segments))):
        raise ValueError('weighted preparation changes its original receipt ancestry or evidence lane')
    raw = read_bounded_bytes(artifact_writer.root.resolve(relative_path, for_write=False), maximum_bytes=maximum_bytes)
    prepared = decode_canonical_bytes(raw, PreparedWeightedContinuation, maximum_bytes=maximum_bytes)
    current = prepare_weighted_continuation(rule=prepared.rule, resampling=prepared.resampling,
        histories=histories, assessor_source=prepared.assessor_source)
    if current['prepared'] != prepared:
        raise ValueError('weighted preparation differs from independently read original histories')
    artifact_writer.verify_manifest(manifest)
    return current


def _read_campaign(**kwargs):
    result = read_weighted_path_campaign(**kwargs)
    return result['report'], result['arrays']


def _render(report):
    return ('Conditional weighted physical path analysis\n\n'
        f"Retained populations: {len(report['populations'])}; assigned originals: {len(report['original_cost_census'])}.\n"
        'Every parent history, descendant, terminal weight and original completion remains in the census.\n'
        'Costs include original attempts with zero offspring. Resampling creates no physical time or independent unit.\n'
        'Numerical path and continuity checks do not admit an entry ensemble, transport model, memoryless rate or biological prediction.\n'
        'Computationally lost paths remain unknown; empirical probability bounds are not confidence intervals.\n').encode('utf-8')


def export_weighted_path_campaign(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='weighted-path', selection=selection, sources=sources,
        project_root=project_root, artifact_writer=artifact_writer, output_relative_path=output_relative_path,
        validate=validate_weighted_path_campaign_inputs, read=_read_campaign, evidence_kind=WeightedPathEvidence, render=_render)


def read_weighted_path_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_weighted_path_campaign_inputs, directory_relative_path=directory_relative_path, sources=sources,
        artifact_writer=artifact_writer, selection_kind=WeightedPathCampaign, evidence_kind=WeightedPathEvidence,
        read=_read_campaign, render=_render)


__all__ = ('WeightedPathCampaign', 'read_weighted_path_campaign', 'prepare_weighted_continuation',
    'author_weighted_continuation', 'read_weighted_continuation_preparation', 'export_weighted_path_campaign',
    'read_weighted_path_export')
