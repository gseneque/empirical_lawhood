# SPDX-License-Identifier: MPL-2.0
"""One complete periodic force evaluation inside the shared native boundary.

The registered caller owns source authentication, native entry and custody.
This function requires a fresh work directory and retains complete diagnostic
operands. It does not authorize execution or assess molecular accuracy.
"""

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import CatalyticPathSelection, validate_catalytic_path_selection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import AmberPeriodicCell, ConstrainedPeriodicForceSettings, PeriodicMMSettings, read_amber_periodic_cell, validate_periodic_force_settings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import GRADIENT_UNIT as GRADIENT_UNIT


ARRAY_KEYS = (
    "embedding_mm_gradient_hartree_per_bohr", "gradient_hartree_per_bohr", "image_shifts",
    "qm_link_gradient_hartree_per_bohr", "remainder_gradient_hartree_per_bohr",
)


def execute_periodic_probe(*, representation, selection, settings, mm_settings, cell,
                           raw_topology, raw_coordinates, directory, density_seed=None, density_bytes=None,
                           accelerated_compute=False, device_memory_bytes=None, molecular_platform=None,
                           host_memory_bytes=None):
    """Retain one actual complete return; the caller captures it before assessment.

    Invalid input bytes refuse before native engines are imported. An exception
    retains all files already written. It never creates a successful raw return.
    """
    for value, kind in ((representation, MolecularRepresentation), (selection, CatalyticPathSelection),
                        (mm_settings, PeriodicMMSettings),
                        (cell, AmberPeriodicCell)):
        exact(value, kind)
    validate_periodic_force_settings(settings)
    validate_catalytic_path_selection(selection, representation)
    if read_amber_periodic_cell(representation, raw_topology, raw_coordinates) != cell:
        raise ValueError("periodic force entry changes its complete original cell or native source")
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError("periodic force entry requires its existing fresh absolute work directory")
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    import numpy as np
    points, _ = read_initial_coordinates(raw_coordinates.decode('ascii'), len(representation.atoms), periodic=True)
    coordinates = np.asarray(points, dtype='<f8')
    del points
    member = representation.arrays.members[0]
    if sha256(coordinates.tobytes(order='C')).hexdigest() != member.sha256:
        raise ValueError("periodic force entry substitutes the complete selected physical coordinate array")
    if density_seed is not None or density_bytes is not None:
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed import PeriodicDensitySeed, read_density_bytes
        from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_density_seed import validate_periodic_probe_model
        exact(density_seed, PeriodicDensitySeed)
        prototype = density_seed.prototype
        validate_periodic_probe_model(prototype, representation)
        if (selection != prototype.path or settings != prototype.electronic
                or mm_settings != prototype.molecular or cell != prototype.cell):
            raise ValueError('periodic restart substitutes its original physical operator')
        read_density_bytes(density_seed, density_bytes)
    return _execute_periodic_at_coordinates(representation=representation, selection=selection, settings=settings,
        mm_settings=mm_settings, cell=cell, raw_topology=raw_topology, raw_coordinates=raw_coordinates,
        coordinates=coordinates, root=root,
        **({'accelerated_compute': True, 'device_memory_bytes': device_memory_bytes,
            'molecular_platform': molecular_platform, 'host_memory_bytes': host_memory_bytes} if accelerated_compute else {}),
        **({'density_seed':density_seed, 'density_bytes':density_bytes} if density_seed is not None else {}))


def _execute_periodic_at_coordinates(*, representation, selection, settings, mm_settings, cell,
        raw_topology, raw_coordinates, coordinates, root, coordinate_records=(), density_seed=None, density_bytes=None,
        accelerated_compute=False, device_memory_bytes=None, molecular_precision_control=False,
        molecular_platform=None, host_memory_bytes=None):
    """Evaluate previously authenticated complete coordinates inside the entered call.

    The original probe and numerical-control owners validate their distinct
    coordinate contracts before calling this implementation helper.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import require_current_periodic_mm_settings
    require_current_periodic_mm_settings(mm_settings)
    import numpy as np
    member = representation.arrays.members[0]
    for name, record in coordinate_records:
        with (root/name).open('xb') as stream:
            stream.write(record.canonical_bytes())
    for name, raw in (("original.prmtop", raw_topology), ("original.inpcrd", raw_coordinates),
                      ("selection.json", selection.canonical_bytes()), ("electronic-settings.json", settings.canonical_bytes()),
                      ("cell.json", cell.canonical_bytes())):
        with (root/name).open('xb') as stream:
            stream.write(raw)
    with (root/'coordinate-array.npy').open('xb') as stream:
        np.save(stream, coordinates, allow_pickle=False)
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import bound_geometry_terms, assess_molecular_geometry
    geometry_terms = bound_geometry_terms(representation, raw_topology)
    geometry_quality = assess_molecular_geometry(coordinates, geometry_terms, policy=mm_settings.geometry_quality,
        cell_angstrom=tuple(map(float, cell.lengths_angstrom)), exempt_bonded_atoms=selection.qm_atom_indices)
    (root/'whole-molecule-quality.json').write_text(json.dumps(geometry_quality, sort_keys=True, indent=2)+'\n')
    if geometry_quality['findings']:
        raise ValueError('whole-molecule quality refused before periodic electronic entry: '+repr(geometry_quality['findings']))
    if density_seed is not None:
        with (root/'initial-density-seed.json').open('xb') as stream:
            stream.write(density_seed.canonical_bytes())
        with (root/'initial-density.bin').open('xb') as stream:
            stream.write(density_bytes)
    with (root/'source-bindings.json').open('x') as stream:
        json.dump(dict(representation=representation.identity.to_document(),
            coordinate_arrays=representation.arrays.identity.to_document(),
            topology_sha256=sha256(raw_topology).hexdigest(), coordinate_source_sha256=sha256(raw_coordinates).hexdigest(),
            coordinate_array_sha256=sha256(coordinates.tobytes(order='C')).hexdigest(),
            original_coordinate_array_sha256=member.sha256, physical_atoms=len(representation.atoms),
            gradient_unit=GRADIENT_UNIT), stream, sort_keys=True, indent=2)
        stream.write('\n')
    # The complete, project-local PySCF corrections are part of the frozen
    # producing package. No installed vendor module is monkeypatched here.
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_mm_remainder as coupling, periodic_images as images
    from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_electronic as electronic
    from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_qmmm import PeriodicCoupledOperator, build_periodic_amber_system
    with (root/'native-observations.jsonl').open('x', buffering=1) as observations:
        def observe(row):
            # Raw diagnostic JSON can retain an observed NaN/Infinity. It is
            # not a canonical scientific record or a successful raw E/G return.
            observations.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')
        original, scales, assignment = build_periodic_amber_system(representation=representation,
            cell=cell, settings=mm_settings, topology_path=root/'original.prmtop', output_directory=root)
        state_capture = {}
        if type(settings) is ConstrainedPeriodicForceSettings:
            from empirical_lawhood.adapters.rubisco.rubisco_response.constrained_electronic_native import record_constrained_state
            state_capture['capture_electronic_state'] = lambda mf, gpu, number, diagnostics: record_constrained_state(
                root, mf=mf, gpu=gpu, state=settings.state, evaluation=number, diagnostics=diagnostics)
        operator = PeriodicCoupledOperator(representation=representation, selection=selection, settings=settings,
            cell=cell, original_system=original, source_scee=scales, coupling=coupling, images=images,
            electronic=electronic, observe=observe,
            **({'accelerated_compute': True, 'device_memory_bytes': device_memory_bytes,
                'molecular_platform': molecular_platform, 'host_memory_bytes': host_memory_bytes} if accelerated_compute else {}),
            **state_capture)
        try:
            with (root/'coupling-audit.json').open('x') as stream:
                json.dump(dict(original_assignment=assignment, remainder=operator.remainder_audit,
                    embedding=operator.embedding_audit), stream, sort_keys=True, indent=2, allow_nan=False)
                stream.write('\n')
            returned = operator.evaluate(coordinates,
                **({'density_seed':density_seed, 'density_bytes':density_bytes} if density_seed is not None else {}))
            # Original values are retained before this wrapper's metadata checks.
            for key in ARRAY_KEYS:
                with (root/(key+'.npy')).open('xb') as stream:
                    np.save(stream, returned[key], allow_pickle=False)
            with (root/'energy_hartree.npy').open('xb') as stream:
                np.save(stream, np.asarray(returned['energy_hartree']), allow_pickle=False)
            metadata = {k:v for k,v in returned.items() if k not in ARRAY_KEYS}
            with (root/'native-return-metadata.json').open('x') as stream:
                json.dump(metadata, stream, sort_keys=True, indent=2, allow_nan=True)
                stream.write('\n')
            if molecular_precision_control:
                from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_mm_precision import retain_molecular_precision
                retain_molecular_precision(system=operator.remainder, context=operator.context,
                    coordinates_angstrom=coordinates, directory=root)
            if returned['gradient_unit'] != GRADIENT_UNIT or returned['bohr_angstrom'] != .52917721092:
                raise ValueError("periodic force return substitutes its exact selected native length unit")
            if operator.evaluations != 1:
                raise ValueError("periodic force entry changes the single selected evaluation denominator")
            return returned
        finally:
            del operator
