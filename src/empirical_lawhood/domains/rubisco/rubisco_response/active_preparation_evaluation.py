# SPDX-License-Identifier: MPL-2.0
"""Complete native returns retained before optimizer acceptance or publication."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import BOHR_ANGSTROM, HARTREE_KJ_MOL
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT


@dataclass(frozen=True, slots=True)
class CompletePreparationEvaluation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/complete-preparation-evaluation'
    evaluation_id: str
    configuration: ObjectIdentity
    seed: ObjectIdentity
    prototype: ObjectIdentity
    ordinal: int
    arrays: ArrayDatasetManifest
    energy_hartree: Decimal
    gradient_unit: str = GRADIENT_UNIT
    scope: str = 'COMPLETE_NATIVE_EVALUATION_WITHOUT_OPTIMIZER_ACCEPTANCE_OR_SCIENTIFIC_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.evaluation_id)
        for pin in (self.configuration, self.seed, self.prototype):
            exact(pin, ObjectIdentity)
        exact(self.arrays, ArrayDatasetManifest)
        validate_decimal(self.energy_hartree, field_name='energy_hartree')
        members = self.arrays.members
        if (type(self.ordinal) is not int or self.ordinal < 1
                or tuple(m.name for m in members) != ('coordinates-angstrom', 'gradient-hartree-per-bohr')
                or self.arrays.scientific_references != tuple(sorted(
                    {self.configuration, self.seed, self.prototype}, key=lambda p: p.object_id))
                or any(m.dtype != '<f8' or not m.finite_required or m.shape != members[0].shape for m in members)
                or len(members[0].shape) != 2 or members[0].shape[0] < 1 or members[0].shape[1] != 3
                or self.gradient_unit != GRADIENT_UNIT
                or self.scope != 'COMPLETE_NATIVE_EVALUATION_WITHOUT_OPTIMIZER_ACCEPTANCE_OR_SCIENTIFIC_ADMISSION'):
            raise ValueError('preparation evaluation changes complete arrays, native units or source scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evaluation_id, self)


def publish_evaluation_files(directory, *, configuration, seed, prototype, number, coordinates, result):
    """Publish complete arrays and then seal their original native-return binding."""
    import numpy as np
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError('preparation return requires its original native directory')
    if (result['gradient_unit'] != GRADIENT_UNIT or float(result['bohr_angstrom']) != BOHR_ANGSTROM
            or float(result['hartree_kj_mol']) != HARTREE_KJ_MOL):
        raise ValueError('preparation return substitutes original physical units')
    arrays = {'coordinates-angstrom': np.asarray(coordinates, dtype='<f8'),
              'gradient-hartree-per-bohr': np.asarray(result['gradient_hartree_per_bohr'], dtype='<f8')}
    if any(not np.isfinite(a).all() for a in arrays.values()):
        raise ValueError('preparation return is incomplete or nonfinite')
    members = tuple(ArrayDatasetMember(name, '<f8', a.shape, sha256(a.tobytes()).hexdigest()) for name, a in arrays.items())
    refs = tuple(sorted({configuration, seed, prototype}, key=lambda p: p.object_id))
    provisional = ArrayDatasetManifest('arrays.preparation-evaluation.pending', members, refs)
    manifest = replace(provisional, dataset_id='arrays.preparation-evaluation.' + provisional.fingerprint())
    provisional = CompletePreparationEvaluation('evaluation.preparation.pending', configuration, seed, prototype,
        number, manifest, Decimal.from_float(float(result['energy_hartree'])))
    record = replace(provisional, evaluation_id='evaluation.preparation.' + provisional.fingerprint())
    prefix = 'evaluation-' + f'{number:08d}'
    for name, array in arrays.items():
        with (root / (prefix + '.' + name + '.npy')).open('xb') as stream:
            np.save(stream, array, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
    with (root / (prefix + '.json')).open('xb') as stream:
        for chunk in record.canonical_chunks():
            stream.write(chunk)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return record


def read_evaluation_files(record, files, *, configuration, seed, prototype):
    """Reconstruct a receipted complete return without constructing a native engine."""
    import numpy as np
    exact(record, CompletePreparationEvaluation)
    if (record.configuration, record.seed, record.prototype) != (configuration, seed, prototype):
        raise ValueError('preparation evaluation substitutes the selected original sources')
    arrays = {}
    prefix = 'evaluation-' + f'{record.ordinal:08d}'
    for member in record.arrays.members:
        data = files[prefix + '.' + member.name + '.npy']
        if type(data) is not bytes or len(data) > member.size_bytes + 4096:
            raise ValueError('preparation evaluation escapes its complete array envelope')
        stream = BytesIO(data)
        array = np.load(stream, allow_pickle=False)
        if (type(array) is not np.ndarray or array.shape != member.shape or array.dtype != np.dtype('<f8')
                or not np.isfinite(array).all() or stream.tell() != len(data)
                or sha256(array.tobytes(order='C')).hexdigest() != member.sha256):
            raise ValueError('preparation evaluation changes complete original array bytes')
        arrays[member.name] = array
    return (record.ordinal, arrays['coordinates-angstrom'], dict(energy_hartree=float(record.energy_hartree),
        gradient_hartree_per_bohr=arrays['gradient-hartree-per-bohr'], gradient_unit=GRADIENT_UNIT,
        bohr_angstrom=BOHR_ANGSTROM, hartree_kj_mol=HARTREE_KJ_MOL))
