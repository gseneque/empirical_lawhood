# SPDX-License-Identifier: MPL-2.0
"""Named geometry substitutions for existing nonphysical software custody controls.

These fixtures contain padding atoms and deliberately incomplete Amber tables.
They can test lifecycle, derivative algebra and complete custody, never molecule
quality. Real geometry gates and source conversions have separate independent
numerical controls in test_rubisco_whole_molecule_quality and quality_read.
"""
from hashlib import sha256
from types import SimpleNamespace


def install_exposed_geometry(monkeypatch):
    from empirical_lawhood.domains.rubisco.rubisco_response import molecular_quality, molecular_quality_read
    def source(model, raw):
        assert sha256(raw).hexdigest() == model.raw_topology.object_fingerprint
        return SimpleNamespace(atomic_numbers=tuple(a.atomic_number for a in model.atoms),
            scope='EXPOSED_SOFTWARE_TOPOLOGY_SUBSTITUTION')
    def screen(coordinates, terms, **kwargs):
        return dict(disposition='SCREEN_PASSED', findings=[],
            counts=dict(atoms=len(coordinates), hydrogens=terms.atomic_numbers.count(1)), metrics={},
            gross_contact_pairs=0, contact_candidates=0,
            scope='EXPOSED_SOFTWARE_GEOMETRY_SUBSTITUTION_NOT_MOLECULAR_EVIDENCE')
    for module in (molecular_quality, molecular_quality_read):
        monkeypatch.setattr(module, 'bound_geometry_terms', source)
        monkeypatch.setattr(module, 'assess_molecular_geometry', screen)


def retain_exposed_source_coordinates(kwargs):
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
    points, _ = read_initial_coordinates(kwargs['raw_coordinates'].decode('ascii'),
        len(kwargs['representation'].atoms), periodic=True)
    root = kwargs['directory']
    (root/'original.prmtop').write_bytes(kwargs['raw_topology'])
    np.save(root/'coordinate-array.npy', np.asarray(points, dtype='<f8'), allow_pickle=False)
