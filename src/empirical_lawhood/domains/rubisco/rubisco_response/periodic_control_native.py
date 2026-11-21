# SPDX-License-Identifier: MPL-2.0
"""One prospectively selected periodic numerical point under shared native custody."""
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import point_coordinates, validate_control_prototype
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform, validate_periodic_probe_model, periodic_operator_options
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import read_amber_periodic_cell


def original_coordinates(prototype, representation, sources):
    """Authenticate the untouched original Amber cell and complete coordinate array."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import prepare_raw_sources
    import numpy as np
    validate_periodic_probe_model(prototype, representation)
    raw_topology, raw_coordinates = sources.topology_utf8.encode('ascii'), sources.coordinates_utf8.encode('ascii')
    if prepare_raw_sources(prototype, raw_topology, raw_coordinates) != sources:
        raise ValueError('periodic numerical point changes its original Amber source')
    if read_amber_periodic_cell(representation, raw_topology, raw_coordinates) != prototype.cell:
        raise ValueError('periodic numerical point changes its original cell')
    points, _ = read_initial_coordinates(sources.coordinates_utf8, len(representation.atoms), periodic=True)
    return np.asarray(points, dtype='<f8').tobytes(order='C')


def execute_periodic_control(*, prototype, protocol, point, representation, sources, directory):
    """Keep original sources intact and evaluate exactly the selected derived point."""
    validate_control_prototype(protocol, prototype)
    raw = original_coordinates(prototype, representation, sources)
    coordinates = point_coordinates(protocol, point, raw)
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or any(root.iterdir()):
        raise ValueError('periodic numerical entry requires its existing fresh absolute work directory')
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import _execute_periodic_at_coordinates
    return _execute_periodic_at_coordinates(representation=representation, selection=prototype.path,
        settings=point.electronic, mm_settings=point.molecular, cell=prototype.cell,
        raw_topology=sources.topology_utf8.encode('ascii'), raw_coordinates=sources.coordinates_utf8.encode('ascii'),
        coordinates=coordinates, root=root,
        coordinate_records=(('control-protocol.json', protocol), ('control-point.json', point)),
        molecular_precision_control=point.role == 'BASELINE' and periodic_molecular_platform(prototype.engine) == 'CUDA',
        **periodic_operator_options(prototype.engine))
