# SPDX-License-Identifier: MPL-2.0
"""Selected complete neutral-gas relaxation inside the ordinary native boundary."""

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_selection import validate_gas_relaxation_model


def gas_relaxation_coordinates(*, selection, representation, raw_topology, raw_coordinates):
    """Authenticate the complete selected input before any native library contact."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import read_amber_periodic_cell

    validate_gas_relaxation_model(selection, representation)
    prototype = selection.prototype
    if read_amber_periodic_cell(representation, raw_topology, raw_coordinates) != prototype.cell:
        raise ValueError('gas relaxation substitutes its original periodic cell or complete Amber sources')
    points, _ = read_initial_coordinates(raw_coordinates.decode('ascii'), len(representation.atoms), periodic=True)
    coordinates = np.asarray(points, dtype='<f8')
    if sha256(coordinates.tobytes()).hexdigest() != prototype.coordinates.members[0].sha256:
        raise ValueError('gas relaxation substitutes its complete original coordinate array')
    return coordinates


def execute_gas_relaxation(*, selection, representation, raw_topology, raw_coordinates, directory):
    """Retain all original calls and endpoint arrays before numerical assessment."""
    import numpy as np

    xyz = gas_relaxation_coordinates(selection=selection, representation=representation,
        raw_topology=raw_topology, raw_coordinates=raw_coordinates)
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError('gas relaxation requires its fresh absolute native working directory')
    prototype = selection.prototype
    for name, raw in (('gas-selection.json', selection.canonical_bytes()),
            ('original.prmtop', raw_topology), ('original.inpcrd', raw_coordinates)):
        with (root/name).open('xb') as stream:
            stream.write(raw)
    with (root/'initial-coordinates-angstrom.npy').open('xb') as stream:
        np.save(stream, xyz, allow_pickle=False)
    bindings = dict(selection=selection.identity.to_document(), representation=representation.identity.to_document(),
        prototype=prototype.identity.to_document(), original_host=selection.augmentation.original_representation.to_document(),
        selected_seed=selection.seed.identity.to_document(), topology_sha256=sha256(raw_topology).hexdigest(),
        coordinate_source_sha256=sha256(raw_coordinates).hexdigest(), initial_coordinate_sha256=sha256(xyz.tobytes()).hexdigest(),
        physical_atoms=len(xyz), gas_atom_indices=prototype.path.gas_atom_indices,
        cell=prototype.cell.to_document(), scope=selection.scope)
    (root/'source-bindings.json').write_text(json.dumps(bindings, sort_keys=True, indent=2)+'\n')
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_mm_remainder as coupling, periodic_images as images
    from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic as electronic
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_native import minimize_reference_geometry
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_operator_options
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import PeriodicCoupledOperator, build_periodic_amber_system

    with (root/'native-observations.jsonl').open('x', buffering=1) as native_log, (root/'relaxation-evaluations.jsonl').open('x', buffering=1) as relaxation_log:
        def native_observe(row):
            native_log.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')

        def observe(row):
            relaxation_log.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')

        original, scales, assignment = build_periodic_amber_system(representation=representation,
            cell=prototype.cell, settings=prototype.molecular, topology_path=root/'original.prmtop', output_directory=root)
        operator = PeriodicCoupledOperator(representation=representation, selection=prototype.path,
            settings=prototype.electronic, cell=prototype.cell, original_system=original,
            source_scee=scales, coupling=coupling, images=images, electronic=electronic, observe=native_observe,
            reuse_converged_density=prototype.electronic.ks_flavour == 'RKS',
            **periodic_operator_options(prototype.engine))
        try:
            (root/'coupling-audit.json').write_text(json.dumps(dict(original_assignment=assignment,
                remainder=operator.remainder_audit, embedding=operator.embedding_audit), sort_keys=True, indent=2, allow_nan=False)+'\n')
            final_xyz, final, summary = minimize_reference_geometry(operator=operator, initial_angstrom=xyz,
                settings=selection.settings, observe=observe)
            for name, value in (('final-coordinates-angstrom.npy', final_xyz),
                    ('final-gradient-hartree-per-bohr.npy', final['gradient_hartree_per_bohr']),
                    ('final-energy-hartree.npy', np.asarray(final['energy_hartree'], dtype='<f8'))):
                with (root/name).open('xb') as stream:
                    np.save(stream, value, allow_pickle=False)
            if summary['complete_reference_evaluations'] != operator.evaluations:
                raise ValueError('gas relaxation loses its original complete reference call denominator')
            (root/'relaxation-summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False)+'\n')
            return summary
        finally:
            del operator
