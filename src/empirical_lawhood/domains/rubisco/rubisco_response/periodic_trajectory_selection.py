# SPDX-License-Identifier: MPL-2.0
"""Complete phase-space operands for diagnostic reference trajectories.

The two flat arrays use the shared named-array contract and native atom order.
Their source identity records origin, never equilibrium or dividing-ensemble
qualification. Native entry and original source custody belong to the caller.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics import ReferenceDynamicsSettings
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_dynamics_assessment import ReferenceTrajectoryCriteria
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection, validate_periodic_probe_model


PHASE_SCHEMA = 'empirical-lawhood/rubisco-response/reference-phase-space-f64'
MAX_PHASE_BYTES = 64 * 2**20
PHASE_NAMES = ('coordinates-angstrom', 'velocities-nm-per-ps')


@dataclass(frozen=True, slots=True)
class ReferenceTrajectorySelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/reference-trajectory-selection'
    selection_id: str
    prototype: ObjectIdentity
    representation: ObjectIdentity
    phase_source: ObjectIdentity
    arrays: ArrayDatasetManifest
    phase_bytes: ObjectIdentity
    physical_atom_count: int
    mass_sha256: str
    settings: ReferenceDynamicsSettings
    criteria: ReferenceTrajectoryCriteria | None
    density_guess_policy: str
    scope: str = 'DIAGNOSTIC_REFERENCE_TRAJECTORY_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        for pin in (self.prototype, self.representation, self.phase_source, self.phase_bytes):
            exact(pin, ObjectIdentity)
        exact(self.arrays, ArrayDatasetManifest)
        exact(self.settings, ReferenceDynamicsSettings)
        if self.criteria is not None:
            exact(self.criteria, ReferenceTrajectoryCriteria)
        validate_sha256(self.mass_sha256)
        if (type(self.physical_atom_count) is not int or self.physical_atom_count <= 0
                or tuple(m.name for m in self.arrays.members) != PHASE_NAMES
                or any(m.dtype != '<f8' or m.shape != (self.physical_atom_count, 3) or not m.finite_required
                    for m in self.arrays.members)
                or self.arrays.size_bytes > MAX_PHASE_BYTES
                or self.arrays.scientific_references != tuple(sorted(
                    {self.representation, self.phase_source}, key=lambda r:r.object_id))
                or self.phase_bytes.object_schema != PHASE_SCHEMA or self.phase_bytes.object_version != '1.0.0'
                or self.prototype.object_schema != PeriodicProbeSelection.SCHEMA
                or self.density_guess_policy not in {'COLD', 'PREVIOUS_SUCCESSFUL_RKS'}
                or self.scope != 'DIAGNOSTIC_REFERENCE_TRAJECTORY_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'):
            raise ValueError('reference trajectory changes its complete phase space, source or diagnostic scope')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def physical_masses(representation):
    """Project every original source mass without repartition or approximation."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
    exact(representation, MolecularRepresentation)
    values = np.asarray([float(atom.mass_dalton) for atom in representation.atoms], dtype='<f8')
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError('trajectory requires every finite positive original physical mass')
    return values


def validate_trajectory_prototype(selection, prototype):
    exact(selection, ReferenceTrajectorySelection)
    exact(prototype, PeriodicProbeSelection)
    if (selection.prototype != prototype.identity or selection.representation != prototype.representation
            or selection.physical_atom_count != prototype.physical_atom_count
            or selection.density_guess_policy == 'PREVIOUS_SUCCESSFUL_RKS' and prototype.electronic.ks_flavour != 'RKS'):
        raise ValueError('trajectory changes its original fixed operator or selected RKS density policy')


def read_phase_space(selection, representation, raw):
    """Authenticate complete raw arrays before any force construction or entry."""
    import numpy as np
    exact(selection, ReferenceTrajectorySelection)
    masses = physical_masses(representation)
    if (representation.identity != selection.representation or len(masses) != selection.physical_atom_count
            or sha256(masses.tobytes()).hexdigest() != selection.mass_sha256
            or type(raw) is not bytes or len(raw) != selection.arrays.size_bytes
            or sha256(raw).hexdigest() != selection.phase_bytes.object_fingerprint):
        raise ValueError('trajectory substitutes original phase bytes, full atom order or physical masses')
    values, offset = [], 0
    for member in selection.arrays.members:
        block = raw[offset:offset + member.size_bytes]
        if sha256(block).hexdigest() != member.sha256:
            raise ValueError('trajectory substitutes a complete original named phase array')
        array = np.frombuffer(block, dtype=member.dtype).reshape(member.shape)
        if not np.isfinite(array).all():
            raise ValueError('trajectory phase space contains nonfinite physical values')
        values.append(array.copy())
        offset += member.size_bytes
    with np.errstate(over='raise', invalid='raise'):
        kinetic = .5 * float(np.sum(masses[:, None] * values[1] ** 2))
        momentum = np.sum(masses[:, None] * values[1], axis=0)
    if not np.isfinite(kinetic) or not np.isfinite(momentum).all():
        raise ValueError('trajectory phase space has nonfinite physical energy or momentum before native entry')
    return *values, masses


def prepare_reference_trajectory(*, prototype, representation, phase_source, initial_angstrom,
        initial_velocity_nm_per_ps, settings, criteria, density_guess_policy):
    """Freeze supplied phase space; generate no velocities or ensemble claim."""
    import numpy as np
    validate_periodic_probe_model(prototype, representation)
    exact(phase_source, ObjectIdentity)
    arrays = tuple(np.array(value, dtype='<f8', order='C', copy=True)
        for value in (initial_angstrom, initial_velocity_nm_per_ps))
    count = len(representation.atoms)
    if any(a.shape != (count, 3) or not np.isfinite(a).all() for a in arrays):
        raise ValueError('reference trajectory requires both complete finite phase arrays in native atom order')
    raw = b''.join(a.tobytes(order='C') for a in arrays)
    digest = sha256(raw).hexdigest()
    members = tuple(ArrayDatasetMember(name, '<f8', (count, 3), sha256(a.tobytes()).hexdigest())
        for name, a in zip(PHASE_NAMES, arrays, strict=True))
    manifest = ArrayDatasetManifest('arrays.reference-phase.'+digest, members,
        tuple(sorted({representation.identity, phase_source}, key=lambda r:r.object_id)))
    exact(settings, ReferenceDynamicsSettings)
    if criteria is not None:
        exact(criteria, ReferenceTrajectoryCriteria)
    selection_digest = sha256((manifest.fingerprint()+prototype.fingerprint()+settings.fingerprint()
        +(criteria.fingerprint() if criteria is not None else 'NONE')+str(density_guess_policy)).encode('ascii')).hexdigest()
    selected = ReferenceTrajectorySelection('selection.reference-trajectory.'+selection_digest, prototype.identity,
        representation.identity, phase_source, manifest,
        ObjectIdentity('bytes.reference-phase.'+digest, PHASE_SCHEMA, '1.0.0', digest), count,
        sha256(physical_masses(representation).tobytes()).hexdigest(), settings, criteria, density_guess_policy)
    validate_trajectory_prototype(selected, prototype)
    read_phase_space(selected, representation, raw)
    return selected, raw
