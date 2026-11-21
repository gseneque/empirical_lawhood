# SPDX-License-Identifier: MPL-2.0
"""Retain small CPU controls when the GPU environment has stock PySCF.

The CPU producer needs the selected CVHF allocation build. These exposed
software fixtures are not enzyme results or scientific qualification evidence.
"""

from hashlib import sha256
import json
from pathlib import Path


def source_bindings():
    from empirical_lawhood.domains.rubisco.rubisco_response import periodic_memory
    from empirical_lawhood.methods import electrostatics
    from empirical_lawhood.methods.electronic_structure import diis
    from empirical_lawhood.adapters.rubisco.rubisco_response import periodic_qmmm
    root = Path(periodic_qmmm.__file__).parent
    names = ('periodic_qmmm.py', 'pyscf_periodic_electronic.py', 'pyscf_periodic_mm_mole.py',
        'pyscf_periodic_dft.py', 'pyscf_periodic_jk.py', 'pyscf_periodic_diis.py')
    result = {name:sha256((root/name).read_bytes()).hexdigest() for name in names}
    domain = Path(periodic_memory.__file__).parent
    result.update({name:sha256((domain/name).read_bytes()).hexdigest()
        for name in ('periodic_images.py', 'periodic_mm_remainder.py', 'periodic_memory.py',
            'periodic_force_contracts.py')})
    result['methods/electronic_structure/diis.py'] = sha256(Path(diis.__file__).read_bytes()).hexdigest()
    result['electrostatics.py'] = sha256(Path(electrostatics.__file__).read_bytes()).hexdigest()
    fixture = Path(__file__).with_name('test_rubisco_periodic_density_reuse.py')
    result['numeric_fixture'] = sha256(fixture.read_bytes()).hexdigest()
    return result


def read_reference(path, digest, *, flavour, charge, operator, coordinates):
    import numpy as np
    raw = Path(path).read_bytes()
    assert len(raw) <= 8*2**20 and sha256(raw).hexdigest() == digest
    data = json.loads(raw)
    assert data['schema'] == 'exposed-rubisco-cpu-control-v1'
    assert data['source_bindings'] == source_bindings()
    assert len(data['controls']) == 4
    rows = [row for row in data['controls'] if (row['flavour'], row['charge']) == (flavour, charge)]
    assert len(rows) == 1
    row = rows[0]
    assert row['settings_sha256'] == sha256(operator.settings.canonical_bytes()).hexdigest()
    np.testing.assert_array_equal(row['coordinates_angstrom'], coordinates)
    gradient = np.asarray(row['gradient_hartree_per_bohr'])
    assert gradient.shape == coordinates.shape and np.isfinite(gradient).all()
    assert np.isfinite(row['energy_hartree']) and row['complete_returns'] == 1
    print(json.dumps(dict(control='retained-independent-cpu-reference', flavour=flavour,
        charge=charge, sha256=digest, producer=data['producer'])))
    return dict(energy_hartree=row['energy_hartree'], gradient_hartree_per_bohr=gradient)


def main():
    import argparse
    import importlib.metadata
    import sys
    from datetime import datetime, timezone
    from pyscf import lib
    from tests.test_rubisco_periodic_density_reuse import numeric_operator
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    library = Path(lib.__file__).parent/'libcvhf.so'
    producer = dict(interpreter=sys.executable, recorded_utc=datetime.now(timezone.utc).isoformat(),
        cvhf_sha256=sha256(library.read_bytes()).hexdigest(),
        versions={name:importlib.metadata.version(name) for name in ('pyscf','openmm','numpy','scipy')})
    controls = []
    fixture = numeric_operator.__wrapped__()
    make = next(fixture)
    try:
        for flavour, charge in (('RKS',0), ('UKS',0), ('RKS',2), ('UKS',-2)):
            operator, coordinates, observations = make(flavour, False)
            operator.selection.qm_formal_charge = charge
            returned = operator.evaluate(coordinates)
            controls.append(dict(flavour=flavour, charge=charge,
                coordinates_angstrom=coordinates.tolist(),
                settings_sha256=sha256(operator.settings.canonical_bytes()).hexdigest(),
                energy_hartree=returned['energy_hartree'],
                gradient_hartree_per_bohr=returned['gradient_hartree_per_bohr'].tolist(),
                complete_returns=sum(row['event']=='return' for row in observations),
                observations=observations))
    finally:
        try:
            next(fixture)
        except StopIteration:
            pass
    record = dict(schema='exposed-rubisco-cpu-control-v1', producer=producer,
        source_bindings=source_bindings(), controls=controls, enzyme_calls=0)
    raw = (json.dumps(record, indent=2, allow_nan=False)+'\n').encode()
    with args.output.open('xb') as stream:
        stream.write(raw)
    print(json.dumps(dict(output=str(args.output), sha256=sha256(raw).hexdigest(),
        complete_cpu_returns=len(controls), enzyme_calls=0)))


if __name__ == '__main__':
    main()
