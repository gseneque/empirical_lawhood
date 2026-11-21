# SPDX-License-Identifier: MPL-2.0
"""Source-bound accepted preparation checkpoints and independent array reading.

Native files remain provisional until their ordinary native-subwork publication
and receipt authenticate them. A checkpoint is not a stationary endpoint,
equilibrium sample, physical-time observation or kinetic supplier.
"""

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
from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2
from empirical_lawhood.domains.rubisco.rubisco_response.geometry_minimizer_state import GeometryMinimizerState
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT

BOHR_ANGSTROM = .52917721092
HARTREE_KJ_MOL = COULOMB_KJ_NM_PER_MOL_E2 / (BOHR_ANGSTROM / 10)
ARRAY_NAMES = ('coordinates-angstrom', 'curvature-rho-mol-per-kj', 'curvature-s-nm',
               'curvature-y-kj-mol-nm', 'gradient-hartree-per-bohr',
               'optimizer-coordinates-nm', 'optimizer-gradient-kj-mol-nm')


@dataclass(frozen=True, slots=True)
class ActivePreparationCheckpoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-checkpoint'
    checkpoint_id: str
    configuration: ObjectIdentity
    seed: ObjectIdentity
    prototype: ObjectIdentity
    arrays: ArrayDatasetManifest
    native_evaluation: int
    energy_hartree: Decimal
    optimizer_energy_kj_mol: Decimal
    initial_energy_kj_mol: Decimal
    maximum_gradient_kj_mol_nm: Decimal
    phase: str
    iterations: int
    evaluations: int
    invalid_trials: int
    curvature_skips: int
    descent_iterations: int
    gradient_unit: str = GRADIENT_UNIT
    continuation: str = 'OPTIMIZER_STATE_WITH_AUTHENTICATED_COMPLETED_EVALUATION_REPLAY'
    scope: str = 'ACCEPTED_PREPARATION_STATE_WITHOUT_STATIONARITY_POPULATION_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.checkpoint_id)
        for pin in (self.configuration, self.seed, self.prototype):
            exact(pin, ObjectIdentity)
        exact(self.arrays, ArrayDatasetManifest)
        expected_sources = tuple(sorted({self.configuration, self.seed, self.prototype}, key=lambda p: p.object_id))
        members = self.arrays.members
        if (tuple(m.name for m in members) != ARRAY_NAMES
                or self.arrays.scientific_references != expected_sources
                or any(m.dtype != '<f8' or not m.finite_required for m in members)):
            raise ValueError('preparation checkpoint changes complete arrays or original source bindings')
        by = {m.name: m for m in members}
        shape = by['coordinates-angstrom'].shape
        if len(shape) != 2 or shape[0] < 1 or shape[1] != 3:
            raise ValueError('preparation checkpoint loses its complete physical atom census')
        size = shape[0] * 3
        history_shape = by['curvature-s-nm'].shape
        if (len(history_shape) != 2 or not 0 <= history_shape[0] <= 20 or history_shape[1] != size
                or by['curvature-y-kj-mol-nm'].shape != history_shape
                or by['curvature-rho-mol-per-kj'].shape != (history_shape[0],)
                or by['gradient-hartree-per-bohr'].shape != shape
                or any(by[name].shape != (size,) for name in
                       ('optimizer-coordinates-nm', 'optimizer-gradient-kj-mol-nm'))):
            raise ValueError('preparation checkpoint changes optimizer dimensions or curvature memory')
        counts = (self.native_evaluation, self.iterations, self.evaluations, self.invalid_trials,
                  self.curvature_skips, self.descent_iterations)
        if (any(type(n) is not int or n < 0 for n in counts)
                or self.native_evaluation < 1 or self.evaluations < self.iterations + 1
                or self.native_evaluation > self.evaluations
                or self.descent_iterations + self.curvature_skips > self.iterations
                or history_shape[0] > self.iterations - self.descent_iterations
                or self.phase not in ('initial-scaled-descent', 'domain-lbfgs')
                or self.phase == 'initial-scaled-descent' and history_shape[0]):
            raise ValueError('preparation checkpoint changes accepted-step and native-work accounting')
        for value in (self.energy_hartree, self.optimizer_energy_kj_mol, self.initial_energy_kj_mol):
            validate_decimal(value, field_name='checkpoint_energy')
        validate_decimal(self.maximum_gradient_kj_mol_nm, field_name='maximum_gradient', minimum=Decimal(0))
        if (not self.maximum_gradient_kj_mol_nm or self.gradient_unit != GRADIENT_UNIT
                or self.continuation != 'OPTIMIZER_STATE_WITH_AUTHENTICATED_COMPLETED_EVALUATION_REPLAY'
                or self.scope != 'ACCEPTED_PREPARATION_STATE_WITHOUT_STATIONARITY_POPULATION_OR_RATE_ADMISSION'):
            raise ValueError('preparation checkpoint changes physical units or its limited continuation meaning')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.checkpoint_id, self)


def prepare_checkpoint(*, state, native_coordinates, native_result, native_evaluation,
                       configuration, seed, prototype):
    """Bind an accepted optimizer state to its actual complete native evaluation."""
    import numpy as np
    exact(state, GeometryMinimizerState)
    if state.proposal_filter_contract is not None:
        raise ValueError('active reference checkpoint cannot add a construction proposal filter')
    xyz = np.asarray(native_coordinates, dtype='<f8')
    gradient = np.asarray(native_result['gradient_hartree_per_bohr'], dtype='<f8')
    if (native_result['gradient_unit'] != GRADIENT_UNIT
            or float(native_result['bohr_angstrom']) != BOHR_ANGSTROM
            or float(native_result['hartree_kj_mol']) != HARTREE_KJ_MOL):
        raise ValueError('preparation checkpoint substitutes native physical units')
    size = state.coordinates.size
    arrays = {'coordinates-angstrom': xyz,
              'gradient-hartree-per-bohr': gradient,
              'optimizer-coordinates-nm': state.coordinates,
              'optimizer-gradient-kj-mol-nm': state.gradient,
              'curvature-s-nm': np.array([row[0] for row in state.history], dtype='<f8').reshape((-1, size)),
              'curvature-y-kj-mol-nm': np.array([row[1] for row in state.history], dtype='<f8').reshape((-1, size)),
              'curvature-rho-mol-per-kj': np.array([row[2] for row in state.history], dtype='<f8')}
    arrays = {name: np.ascontiguousarray(arrays[name], dtype='<f8') for name in ARRAY_NAMES}
    refs = tuple(sorted({configuration, seed, prototype}, key=lambda p: p.object_id))
    members = tuple(ArrayDatasetMember(name, '<f8', arrays[name].shape, sha256(arrays[name].tobytes()).hexdigest())
                    for name in ARRAY_NAMES)
    provisional = ArrayDatasetManifest('arrays.preparation-checkpoint.pending', members, refs)
    manifest = replace(provisional, dataset_id='arrays.preparation-checkpoint.' + provisional.fingerprint())
    provisional = ActivePreparationCheckpoint('checkpoint.preparation.pending', configuration, seed, prototype,
        manifest, native_evaluation, Decimal.from_float(float(native_result['energy_hartree'])),
        Decimal.from_float(state.energy), Decimal.from_float(state.initial_energy),
        Decimal.from_float(state.maximum_gradient), state.phase, state.iterations, state.evaluations,
        state.invalid_trials, state.curvature_skips, state.descent_iterations)
    record = replace(provisional, checkpoint_id='checkpoint.preparation.' + provisional.fingerprint())
    read_checkpoint_arrays(record, arrays, configuration=configuration, seed=seed, prototype=prototype)
    return record, arrays


def read_checkpoint_arrays(record, arrays, *, configuration, seed, prototype):
    """Independently authenticate every array and reconstruct the optimizer state."""
    import numpy as np
    exact(record, ActivePreparationCheckpoint)
    if ((record.configuration, record.seed, record.prototype) != (configuration, seed, prototype)
            or type(arrays) is not dict or tuple(sorted(arrays)) != ARRAY_NAMES):
        raise ValueError('preparation checkpoint changes the selected source or complete member census')
    for member in record.arrays.members:
        values = arrays[member.name]
        if (type(values) is not np.ndarray or values.dtype != np.dtype('<f8') or values.shape != member.shape
                or not np.isfinite(values).all() or sha256(values.tobytes(order='C')).hexdigest() != member.sha256):
            raise ValueError('preparation checkpoint changes complete original array bytes')
    xyz = arrays['coordinates-angstrom']
    x = arrays['optimizer-coordinates-nm']
    g = arrays['gradient-hartree-per-bohr']
    optimizer_gradient = arrays['optimizer-gradient-kj-mol-nm']
    if (not (np.array_equal((xyz / 10).reshape(-1), x) or np.array_equal(x.reshape(xyz.shape) * 10, xyz))
            or not np.array_equal((g * HARTREE_KJ_MOL * 10 / BOHR_ANGSTROM).reshape(-1), optimizer_gradient)
            or float(record.energy_hartree) * HARTREE_KJ_MOL != float(record.optimizer_energy_kj_mol)):
        raise ValueError('preparation checkpoint is not its original complete force/energy in optimizer units')
    history = tuple((s, y, float(rho)) for s, y, rho in zip(arrays['curvature-s-nm'],
        arrays['curvature-y-kj-mol-nm'], arrays['curvature-rho-mol-per-kj'], strict=True))
    return GeometryMinimizerState(x, float(record.optimizer_energy_kj_mol), optimizer_gradient,
        float(record.initial_energy_kj_mol), history, record.phase, record.iterations, record.evaluations,
        record.invalid_trials, record.curvature_skips, record.descent_iterations,
        float(record.maximum_gradient_kj_mol_nm), None)


def publish_checkpoint_files(directory, record, arrays):
    """Write native operands first and the immutable accepted-state seal last."""
    import numpy as np
    root = Path(directory)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError('checkpoint publication requires its original absolute native directory')
    read_checkpoint_arrays(record, arrays, configuration=record.configuration, seed=record.seed, prototype=record.prototype)
    prefix = 'accepted-' + f'{record.iterations:08d}'
    for name in ARRAY_NAMES:
        with (root / (prefix + '.' + name + '.npy')).open('xb') as stream:
            np.save(stream, arrays[name], allow_pickle=False)
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
    return prefix + '.json'


def read_checkpoint_files(record, files, *, configuration, seed, prototype):
    """Read already authenticated native members, rejecting trailers and substitution."""
    import numpy as np
    arrays = {}
    prefix = 'accepted-' + f'{record.iterations:08d}'
    for member in record.arrays.members:
        data = files[prefix + '.' + member.name + '.npy']
        if type(data) is not bytes or len(data) > member.size_bytes + 4096:
            raise ValueError('preparation checkpoint exceeds its selected array envelope')
        stream = BytesIO(data)
        values = np.load(stream, allow_pickle=False)
        if stream.tell() != len(data):
            raise ValueError('preparation checkpoint array has an unbound trailer')
        arrays[member.name] = values
    state = read_checkpoint_arrays(record, arrays, configuration=configuration, seed=seed, prototype=prototype)
    return state, arrays
