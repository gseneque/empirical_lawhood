"""Native acquisition and external-format binding for the domain science."""

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import file_chunks
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_density_seed import (
    DENSITY_SCHEMA as _science_DENSITY_SCHEMA,
    MAX_CHECKPOINT_BYTES as _science_MAX_CHECKPOINT_BYTES,
    MAX_DENSITY_BYTES as _science_MAX_DENSITY_BYTES,
    PeriodicDensitySeed as _science_PeriodicDensitySeed,
    density_electron_populations as _science_density_electron_populations,
    read_density_bytes as _science_read_density_bytes,
)

def molecule_signature(mol):
    """Bind actual shell contractions, AO order and complete QM/link geometry."""
    import numpy as np

    def array_hash(value):
        return sha256(np.asarray(value, dtype='<f8', order='C').tobytes()).hexdigest()

    shells = tuple((int(mol.bas_atom(i)), int(mol.bas_angular(i)), int(mol.bas_nprim(i)),
        int(mol.bas_nctr(i)), int(mol.bas_kappa(i)), array_hash(mol.bas_exp(i)),
        array_hash(mol.bas_ctr_coeff(i))) for i in range(mol.nbas))
    record = dict(cart=bool(mol.cart), charge=int(mol.charge), spin=int(mol.spin),
        atoms=tuple(int(v) for v in mol.atom_charges()), coordinates_bohr_sha256=array_hash(mol.atom_coords()),
        shells=shells, ao_locations=tuple(int(v) for v in mol.ao_loc_nr()), ao_labels=mol.ao_labels(fmt=False))
    return sha256(json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')).hexdigest()


def validate_density_electrons(density, mol):
    """Check each selected spin population in the original AO overlap metric."""
    import numpy as np
    overlap = mol.intor_symmetric('int1e_ovlp')
    expected = mol.nelectron if density.ndim == 2 else np.asarray(mol.nelec)
    return _science_density_electron_populations(density, overlap, expected)


def validate_checkpoint_layout(path, coefficient_shape, orbital_shape):
    """Refuse indirect or oversized datasets before PySCF materializes arrays."""
    import h5py
    import math
    if math.prod(coefficient_shape)*8 > _science_MAX_DENSITY_BYTES:
        raise ValueError('checkpoint orbitals exceed the bounded complete density allocation')
    with h5py.File(path, 'r') as handle:
        if (set(handle) != {'mol', 'scf'}
                or any(type(handle.get(name, getlink=True)) is not h5py.HardLink for name in ('mol', 'scf'))
                or not isinstance(handle['scf'], h5py.Group)
                or set(handle['scf']) != {'e_tot', 'mo_coeff', 'mo_energy', 'mo_occ'}):
            raise ValueError('checkpoint changes its complete direct original molecular/SCF dataset census')
        shapes = {'mol':(), 'scf/e_tot':(), 'scf/mo_coeff':coefficient_shape,
            'scf/mo_energy':orbital_shape, 'scf/mo_occ':orbital_shape}
        for name, shape in shapes.items():
            if type(handle.get(name, getlink=True)) is not h5py.HardLink:
                raise ValueError('checkpoint contains an indirect dataset')
            dataset = handle[name]
            if (not isinstance(dataset, h5py.Dataset) or dataset.shape != shape
                    or dataset.is_virtual or dataset.external or dataset.compression is not None
                    or name == 'mol' and h5py.check_string_dtype(dataset.dtype) is None
                    or name != 'mol' and (dataset.dtype.kind != 'f' or dataset.dtype.itemsize != 8)):
                raise ValueError('checkpoint changes a complete bounded original dataset shape or representation')


def density_for_operator(seed, raw, *, mol, representation, path, settings, cell, coordinates):
    """Authenticate the original molecular and actual native AO contexts at entry."""
    import numpy as np
    exact(seed, _science_PeriodicDensitySeed)
    prototype = seed.prototype
    validate_periodic_probe_model(prototype, representation)
    if (path != prototype.path or settings != prototype.electronic or cell != prototype.cell
            or sha256(np.asarray(coordinates, dtype='<f8', order='C').tobytes()).hexdigest()
                != prototype.coordinates.members[0].sha256
            or molecule_signature(mol) != seed.molecule_sha256):
        raise ValueError('density seed changes its original physical coordinates, basis or ordered AO context')
    density = _science_read_density_bytes(seed, raw)
    expected_shape = (mol.nao, mol.nao) if settings.ks_flavour == 'RKS' else (2, mol.nao, mol.nao)
    if density.shape != expected_shape:
        raise ValueError('density seed omits the complete selected AO population')
    populations = validate_density_electrons(density, mol)
    return density, populations


def prepare_checkpoint_density(*, source_config, source_definition, representation, raw_sources,
        checkpoint_path, checkpoint):
    """Read a frozen intermediate checkpoint; perform no SCF, energy or gradient.

    The supplied checkpoint hash comes from retained original custody. A live,
    mutable solver file is not a replacement for that fixed source selection.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeConfig, native_input_records
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_native import original_coordinates
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_remainder import linked_qm_coordinates
    exact(source_config, PeriodicProbeConfig)
    exact(source_definition, NativeSubworkDefinition)
    exact(checkpoint, FileEvidence)
    if type(checkpoint.byte_count) is not int or not 0 < checkpoint.byte_count <= _science_MAX_CHECKPOINT_BYTES:
        raise ValueError('checkpoint exceeds its complete original file byte bound')
    native_input_records(source_config, representation, raw_sources)
    path = Path(checkpoint_path)
    if not path.is_absolute() or path.is_symlink() or not path.is_file() or path.name != Path(checkpoint.relative_path).name:
        raise ValueError('checkpoint density requires its original frozen regular file')
    for _ in file_chunks(path, expected=checkpoint):
        pass
    import numpy as np
    from pyscf import gto
    from pyscf.scf import chkfile, hf, uhf
    prototype = source_config.selection
    coordinate_bytes = original_coordinates(prototype, representation, raw_sources)
    xyz = np.frombuffer(coordinate_bytes, dtype='<f8').reshape((len(representation.atoms), 3))
    selected = prototype.path
    links = tuple((row.qm_atom_index, row.mm_atom_index, float(row.link_distance_angstrom)) for row in selected.boundaries)
    qxyz, _ = linked_qm_coordinates(xyz, selected.qm_atom_indices, links)
    numbers = [representation.atoms[i].atomic_number for i in selected.qm_atom_indices] + [1]*len(links)
    expected_mol = gto.M(atom=list(zip(numbers, qxyz, strict=True)), unit='Angstrom', basis=prototype.electronic.basis,
        charge=selected.qm_formal_charge, spin=selected.spin_multiplicity-1, verbose=0)
    restricted = prototype.electronic.ks_flavour == 'RKS'
    nao = expected_mol.nao
    shapes = ((nao, nao), (nao,)) if restricted else ((2, nao, nao), (2, nao))
    validate_checkpoint_layout(path, *shapes)
    mol, record = chkfile.load_scf(str(path))
    signature = molecule_signature(mol)
    if signature != molecule_signature(expected_mol):
        raise ValueError('checkpoint molecule differs from the complete original selected QM/link geometry and basis')
    coefficient = np.asarray(record['mo_coeff'])
    occupation = np.asarray(record['mo_occ'])
    orbital_energy = np.asarray(record['mo_energy'])
    if (coefficient.shape != shapes[0] or occupation.shape != shapes[1] or orbital_energy.shape != shapes[1]
            or any(np.iscomplexobj(value) or not np.isfinite(value).all() for value in (coefficient, occupation, orbital_energy))
            or not np.isin(occupation, (0, 2) if restricted else (0, 1)).all()
            or not np.isfinite(record['e_tot'])):
        raise ValueError('checkpoint omits finite complete original orbitals or integral occupations')
    density = (hf if restricted else uhf).make_rdm1(coefficient, occupation)
    density = np.asarray(density, dtype='<f8', order='C')
    raw = density.tobytes()
    digest = sha256(raw).hexdigest()
    member = ArrayDatasetMember('initial-density', '<f8', density.shape, digest)
    arrays = ArrayDatasetManifest('arrays.checkpoint-density.'+digest, (member,), tuple(sorted(
        {prototype.identity, source_config.identity, source_definition.identity}, key=lambda row:row.object_id)))
    seed_digest = sha256((arrays.fingerprint()+checkpoint.fingerprint()+signature).encode('ascii')).hexdigest()
    seed = _science_PeriodicDensitySeed('seed.periodic-density.'+seed_digest, source_config.identity, prototype,
        source_config.provenance, source_definition, checkpoint, Decimal(str(float(record['e_tot']))), signature,
        arrays, ObjectIdentity('bytes.checkpoint-density.'+digest, _science_DENSITY_SCHEMA, '1.0.0', digest))
    density_for_operator(seed, raw, mol=expected_mol, representation=representation, path=prototype.path,
        settings=prototype.electronic, cell=prototype.cell, coordinates=xyz)
    for _ in file_chunks(path, expected=checkpoint):
        pass
    return seed, raw
