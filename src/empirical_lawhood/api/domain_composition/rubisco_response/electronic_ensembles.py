# SPDX-License-Identifier: MPL-2.0
"""Original electronic sampling, conditional pair assessment and closed export."""

from dataclasses import fields
from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.electronic_observations import ElectronicObservationSet
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_records import ElectronicEnsembleRule, ElectronicEnsembleEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.electronic_ensemble_read import validate_electronic_ensemble_inputs, read_electronic_ensembles
from empirical_lawhood.domains.rubisco.rubisco_response.equilibrium_reweighting_read import RetainedEquilibriumTrace
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_equilibrium_selection import ReferenceEquilibriumSelection, ObservedElectronicEquilibriumSelection
from empirical_lawhood.api.domain_composition.rubisco_response.periodic_equilibrium import prepare_reference_equilibrium, author_reference_equilibrium
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, export_native_observation_analysis, read_native_observation_analysis


def prepare_electronic_equilibrium(*, observations, prototype, representation, phase_source,
        initial_angstrom, initial_velocity_nm_per_ps, settings, window=None, convention=None, criteria=None):
    """Extend the supported equilibrium preparation with its full state census."""
    exact(observations,ElectronicObservationSet)
    if prototype not in observations.prototypes:
        raise ValueError('electronic sampling omits its actual donor state from the selected observations')
    ordinary,phase = prepare_reference_equilibrium(prototype=prototype,representation=representation,
        phase_source=phase_source,initial_angstrom=initial_angstrom,initial_velocity_nm_per_ps=initial_velocity_nm_per_ps,
        settings=settings,window=window,convention=convention,criteria=criteria,density_guess_policy='COLD')
    values = {f.name:getattr(ordinary,f.name) for f in fields(ReferenceEquilibriumSelection)}
    values['selection_id'] = 'electronic-equilibrium.'+sha256(ordinary.canonical_bytes()+observations.canonical_bytes()).hexdigest()
    return ObservedElectronicEquilibriumSelection(**values,observations=observations),phase


def _text(report):
    lines = ['Conditional original electronic ensemble assessment','',
        f"Assigned electronic points: {report['assigned_points']}; complete pair configurations: {report['complete_pair_configurations']}.",
        'Every original state, frame, failed point, numerical return and cost remains in the census.',
        'Rates use the declared finite energy-gap slab and original complete equilibrium measure.',
        'Biased sampling time does not supply physical energy-gap memory.',
        'The selected singlet-triplet route retains all three components and bounds spin contamination.',
        'Its isotropic unpolarized population is an explicit conditional model.','']
    for name,row in report['pairs'].items():
        lines.append(name+': '+row['selected_golden_rule_criteria'])
    joint = report['joint']
    lines.extend(('',f"Joint draws: {joint['retained_replicates']}/{joint['requested_replicates']}; failed: {len(joint['failed_replicates'])}.",
        'Joint uncertainty reuses original coupled block indices and all state observations within each configuration.',
        'Chemical, equilibrium, spin and physical-rate admission remain distinct from these conditional numerical assessments.',''))
    return '\n'.join(lines).encode('utf-8')


def export_electronic_ensembles(*, selection, sources, project_root, artifact_writer, output_relative_path):
    return export_native_observation_analysis(namespace='electronic-ensembles',selection=selection,sources=sources,
        project_root=project_root,artifact_writer=artifact_writer,output_relative_path=output_relative_path,
        validate=validate_electronic_ensemble_inputs,read=read_electronic_ensembles,
        evidence_kind=ElectronicEnsembleEvidence,render=_text)


def read_electronic_ensembles_export(*, directory_relative_path, sources, artifact_writer):
    return read_native_observation_analysis(validate=validate_electronic_ensemble_inputs, directory_relative_path=directory_relative_path,sources=sources,
        artifact_writer=artifact_writer,selection_kind=ElectronicEnsembleRule,evidence_kind=ElectronicEnsembleEvidence,
        read=read_electronic_ensembles,render=_text)


__all__ = ('MEMBERS','RetainedEquilibriumTrace','prepare_electronic_equilibrium','author_reference_equilibrium',
    'validate_electronic_ensemble_inputs','read_electronic_ensembles','export_electronic_ensembles','read_electronic_ensembles_export')
