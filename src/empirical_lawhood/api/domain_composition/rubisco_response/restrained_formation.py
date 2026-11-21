# SPDX-License-Identifier: MPL-2.0
"""Supported restrained-formation analysis over unchanged native custody."""

from empirical_lawhood.domains.rubisco.rubisco_response.restrained_formation import RestrainedFormationNode, RestrainedFormationSelection, read_restrained_formation, validate_restrained_formation_inputs
from empirical_lawhood.domains.rubisco.rubisco_response.restrained_formation_evidence import RestrainedFormationEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.formation_coordinate import PreparedFormationCoordinate, prepare_formation_coordinate
from empirical_lawhood.api.domain_composition.rubisco_response.native_analysis_export import MEMBERS, export_native_observation_analysis, read_native_observation_analysis


def prepare_formation_atom_correspondence(*,case,wt_representation,mutant_representation,protocol,sources):
    """Derive the complete physical relation by residue, atom name and element.

    Independent solvent molecules without shared physical identities remain
    explicit removals/additions. Native ordinal equality is never a match.
    """
    from hashlib import sha256
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_transform import derive_atomic_transformation
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
    for representation in (wt_representation,mutant_representation):
        exact(representation,MolecularRepresentation)
    after={(atom.residue_id,atom.name,atom.atomic_number):i for i,atom in enumerate(mutant_representation.atoms)}
    common=tuple((i,after[key]) for i,atom in enumerate(wt_representation.atoms)
        if (key:=(atom.residue_id,atom.name,atom.atomic_number)) in after)
    digest=sha256((case.fingerprint()+wt_representation.fingerprint()+mutant_representation.fingerprint()
        +protocol.object_fingerprint).encode('ascii')).hexdigest()
    return derive_atomic_transformation(wt_representation,mutant_representation,
        transformation_id='transformation.formation.'+digest,kind='FINITE_SEQUENCE_SUBSTITUTION',
        common_atoms=common,protocol=protocol,sources=sources,case=case)


def _text(report):
    formation=report['formation']
    value=formation['paired_restrained_free_energy_j_mol']
    integral='UNEVALUABLE' if value is None else str(value['numerator'])+'/'+str(value['denominator'])+' J/mol'
    return ('Paired restrained formation integral\n\n'
        +'Mutant minus WT, fixed selected centers: '+integral+'.\n'
        +'Selected receiver diagnostics: '+formation['selected_receiver_diagnostics']+'.\n'
        +'This is a restrained free-energy difference; an activation barrier and formation-rate ratio remain unavailable.\n'
        +'Every selected trace, failed prefix, dependence group, joint draw and original cost is retained.\n'
        +'Remaining physical connections: '+', '.join(formation['formation_requirements'])+'.\n'
        +'No new native calculation occurred.\n').encode('utf-8')


def export_restrained_formation(*,selection,sources,project_root,artifact_writer,output_relative_path):
    return export_native_observation_analysis(namespace='restrained-formation',selection=selection,sources=sources,
        project_root=project_root,artifact_writer=artifact_writer,output_relative_path=output_relative_path,
        validate=validate_restrained_formation_inputs,read=read_restrained_formation,
        evidence_kind=RestrainedFormationEvidence,render=_text)


def read_restrained_formation_export(*,directory_relative_path,sources,artifact_writer):
    return read_native_observation_analysis(validate=validate_restrained_formation_inputs, directory_relative_path=directory_relative_path,sources=sources,
        artifact_writer=artifact_writer,selection_kind=RestrainedFormationSelection,
        evidence_kind=RestrainedFormationEvidence,read=read_restrained_formation,render=_text)


__all__=('MEMBERS','RestrainedFormationNode','RestrainedFormationSelection','RestrainedFormationEvidence',
    'PreparedFormationCoordinate','prepare_formation_coordinate',
    'read_restrained_formation','validate_restrained_formation_inputs',
    'prepare_formation_atom_correspondence','export_restrained_formation','read_restrained_formation_export')
