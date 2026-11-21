# SPDX-License-Identifier: MPL-2.0
"""Frozen complete operands for a single periodic enzyme force probe.

The full molecular record is a separate direct input. This small selection
never replaces its complete atom table or grants native execution authority.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import file_chunks
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_native import MolecularForceProbe
from empirical_lawhood.domains.rubisco.rubisco_response.catalytic_path_selection import CatalyticPathSelection, validate_catalytic_path_selection
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import AmberPeriodicCell, PeriodicForceSettings, ConstrainedPeriodicForceSettings, PeriodicMMSettingsRecord, validate_periodic_force_settings, validate_periodic_mm_settings
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id


NUMERIC_PACKAGES = ('OpenMM.libs', 'h5py', 'h5py.libs', 'numpy', 'numpy.libs', 'openmm', 'pyscf', 'scipy', 'scipy.libs')
GPU_NUMERIC_PACKAGES = tuple(sorted((*NUMERIC_PACKAGES, 'cupy', 'cupy_backends', 'cupyx', 'cutensor',
    'fastrlock', 'gpu4pyscf', 'gpu4pyscf_cuda12x.libs', 'nvidia', 'pyscf_dispersion.libs')))
NATIVE_PREFIXES = frozenset(('h5py', 'numpy', 'openmm', 'pyscf', 'scipy'))
NUMERICAL_THREAD_SETTINGS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
    'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'NUMBA_NUM_THREADS', 'BLIS_NUM_THREADS', 'OPENMM_CPU_THREADS')
OPEN_REQUIREMENTS = (
    'requirement.molecular.active-protonation-ensemble',
    'requirement.molecular.physical-and-chemical-model-admission',
    'requirement.periodic-force.complete-derivative-assessment',
    'requirement.periodic-force.numerical-refinement',
)


def periodic_worker_environment(environment):
    """Freeze the selected OpenMM count across this coupled numerical worker.

    The shared worker checks the declared CPU allocation; the numerical-engine
    census independently requires this count to equal its actual selection.
    """
    if type(environment) is not dict or any(type(k) is not str or type(v) is not str
            for k, v in environment.items()):
        raise ValueError('periodic worker selection requires exact string settings')
    selected = dict(environment)
    threads = selected.get('OPENMM_CPU_THREADS', '1')
    if not threads.isascii() or not threads.isdecimal() or threads.startswith('0'):
        raise ValueError('periodic worker requires an explicit positive numerical thread count')
    selected.update(dict.fromkeys(NUMERICAL_THREAD_SETTINGS, threads))
    return selected


def _absolute(value):
    if type(value) is not str:
        raise ValueError('periodic force source requires an exact absolute path')
    path = PurePosixPath(value)
    if not path.is_absolute() or str(path) != value or '..' in path.parts:
        raise ValueError('periodic force source requires an exact absolute path')


@dataclass(frozen=True, slots=True)
class PeriodicNumericEngine(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-numeric-engine'
    engine_id: str
    site_packages: str
    files: tuple[FileEvidence, ...]
    interpreter: str
    interpreter_sha256: str
    numerical_threads: int = 1

    def __post_init__(self):
        _validate_numeric_engine(self, NUMERIC_PACKAGES)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.engine_id, self)


def _validate_numeric_engine(engine, packages):
    self = engine
    validate_stable_id(self.engine_id)
    _absolute(self.site_packages)
    _absolute(self.interpreter)
    validate_sha256(self.interpreter_sha256)
    if type(self.numerical_threads) is not int or self.numerical_threads < 1:
        raise ValueError('periodic force needs an explicit positive numerical thread selection')
    if type(self.files) is not tuple or not self.files:
        raise ValueError('periodic force engine omits its complete original numerical file census')
    for row in self.files:
        exact(row, FileEvidence)
    if (tuple(r.relative_path for r in self.files) != tuple(sorted({r.relative_path for r in self.files}))
            or {PurePosixPath(r.relative_path).parts[0] for r in self.files} != set(packages)):
        raise ValueError('periodic force engine changes its complete numerical package population')

@dataclass(frozen=True, slots=True, kw_only=True)
class AcceleratedPeriodicNumericEngine(PeriodicNumericEngine):
    """Separate GPU environment; historical CPU engine bytes remain unchanged."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-periodic-numeric-engine'
    host_memory_bytes: int
    device_memory_bytes: int
    package_roots: tuple[str, ...] = GPU_NUMERIC_PACKAGES

    def __post_init__(self):
        if (type(self.package_roots) is not tuple
                or self.package_roots != tuple(sorted(set(self.package_roots)))
                or not set(GPU_NUMERIC_PACKAGES).issubset(self.package_roots)):
            raise ValueError('GPU engine requires its complete selected numerical package roots')
        for name in self.package_roots:
            if type(name) is not str or PurePosixPath(name).name != name or name in ('.', '..'):
                raise ValueError('GPU numerical package root must be one exact directory name')
        _validate_numeric_engine(self, self.package_roots)
        if any(type(value) is not int or value <= 0 for value in
               (self.host_memory_bytes, self.device_memory_bytes)):
            raise ValueError('GPU engine requires explicit positive host and device memory allocations')


@dataclass(frozen=True, slots=True, kw_only=True)
class GpuReferencePeriodicNumericEngine(AcceleratedPeriodicNumericEngine):
    """Explicit GPU electronic solver with the binary64 Reference MM platform.

    This separate selection preserves historical CPU and CUDA engine bytes.
    It never arises from an automatic fallback after a failed native contact.
    """

    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gpu-reference-periodic-numeric-engine'


def accelerated_engine(engine):
    if type(engine) not in (PeriodicNumericEngine, AcceleratedPeriodicNumericEngine, GpuReferencePeriodicNumericEngine):
        raise TypeError('periodic force requires an exact CPU or accelerated engine selection')
    return type(engine) is not PeriodicNumericEngine


def periodic_molecular_platform(engine):
    return 'CUDA' if accelerated_engine(engine) and type(engine) is AcceleratedPeriodicNumericEngine else 'Reference'


def periodic_operator_options(engine):
    """Project the explicit backend selection into the shared complete operator."""
    if not accelerated_engine(engine):
        return {}
    options = {'accelerated_compute': True, 'device_memory_bytes': engine.device_memory_bytes}
    if type(engine) is GpuReferencePeriodicNumericEngine:
        options['molecular_platform'] = 'Reference'
        options['host_memory_bytes'] = engine.host_memory_bytes
    return options


def authenticate_periodic_engine(engine, *, loaded=False):
    """Read complete selected stock; loaded modules must use those exact files."""
    import os
    import sys
    accelerated = accelerated_engine(engine)
    packages = engine.package_roots if accelerated else NUMERIC_PACKAGES
    prefixes = NATIVE_PREFIXES | frozenset(('cupy', 'cupy_backends', 'cupyx', 'cutensor',
        'fastrlock', 'gpu4pyscf', 'nvidia')) if accelerated else NATIVE_PREFIXES
    root = Path(engine.site_packages)
    if root.is_symlink() or root.resolve() != root or Path(sys.executable).resolve() != Path(engine.interpreter):
        raise ValueError('periodic force execution substitutes its selected numerical environment')
    if sha256(Path(engine.interpreter).read_bytes()).hexdigest() != engine.interpreter_sha256:
        raise ValueError('periodic force execution changes its selected interpreter bytes')
    for name in NUMERICAL_THREAD_SETTINGS:
        if os.environ.get(name) != str(engine.numerical_threads):
            raise ValueError('periodic force execution changes its selected numerical thread count: '+name)
    actual = []
    for name in packages:
        directory = root/name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError('periodic force numerical package root is absent or substituted')
        for path in directory.rglob('*'):
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError('periodic force numerical stock contains an undeclared link or special member')
            if path.is_file():
                actual.append(path.relative_to(root).as_posix())
    if tuple(sorted(actual)) != tuple(r.relative_path for r in engine.files):
        raise ValueError('periodic force complete numerical file census changed')
    for row in engine.files:
        for _ in file_chunks(root/row.relative_path, expected=row):
            pass
    observed = []
    if loaded:
        selected = {str(root/r.relative_path):r for r in engine.files}
        for name, module in sorted(sys.modules.items()):
            if name.split('.')[0] not in prefixes:
                continue
            origin = getattr(module, '__file__', None)
            if origin is None:
                continue
            path = Path(origin).resolve()
            row = selected.get(str(path))
            if row is None:
                raise ValueError('imported numerical module escapes the selected complete stock: '+name)
            for _ in file_chunks(path, expected=row):
                pass
            observed.append((name, str(path), row.sha256))
    return tuple(observed)


@dataclass(frozen=True, slots=True)
class PeriodicProbeSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-probe-selection'
    selection_id: str
    representation: ObjectIdentity
    coordinates: ArrayDatasetManifest
    physical_atom_count: int
    path: CatalyticPathSelection
    cell: AmberPeriodicCell
    electronic: PeriodicForceSettings | ConstrainedPeriodicForceSettings
    molecular: PeriodicMMSettingsRecord
    engine: PeriodicNumericEngine | AcceleratedPeriodicNumericEngine | GpuReferencePeriodicNumericEngine
    sources: tuple[ObjectIdentity, ...]
    scope: str = 'ONE_COMPLETE_PERIODIC_FORCE_PROBE_WITHOUT_ENSEMBLE_OR_KINETIC_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        for value, kind in ((self.representation,ObjectIdentity), (self.coordinates,ArrayDatasetManifest),
                            (self.path,CatalyticPathSelection), (self.cell,AmberPeriodicCell)):
            exact(value, kind)
        validate_periodic_force_settings(self.electronic)
        validate_periodic_mm_settings(self.molecular)
        accelerated_engine(self.engine)
        if type(self.electronic) is ConstrainedPeriodicForceSettings:
            state = self.electronic.state
            if (not accelerated_engine(self.engine) or state.representation != self.representation
                    or state.qm_atom_indices != self.path.qm_atom_indices
                    or state.qm_formal_charge != self.path.qm_formal_charge
                    or state.spin_multiplicity != self.path.spin_multiplicity):
                raise ValueError('constrained periodic selection changes its selected GPU, atom partition, charge or spin')
        if (self.representation.object_schema != MolecularRepresentation.SCHEMA
                or self.representation.object_version != MolecularRepresentation.VERSION
                or type(self.physical_atom_count) is not int or self.physical_atom_count <= 0
                or self.path.representation != self.representation
                or self.path.physical_atom_count != self.physical_atom_count
                or self.cell.physical_atom_count != self.physical_atom_count
                or len(self.coordinates.members) != 1
                or self.coordinates.members[0].name != 'coordinates-angstrom'
                or self.coordinates.members[0].shape != (self.physical_atom_count,3)
                or self.coordinates.members[0].dtype != '<f8'
                or not self.coordinates.members[0].finite_required
                or self.coordinates.scientific_references != tuple(sorted(
                    (self.cell.raw_topology,self.cell.raw_coordinates),key=lambda r:r.object_id))):
            raise ValueError('periodic force selection changes its complete molecular/coordinate/cell denominator')
        if (self.molecular.cutoff_angstrom >= min(self.cell.lengths_angstrom)/2
                or self.electronic.real_cutoff_angstrom >= min(self.cell.lengths_angstrom)
                or self.electronic.ks_flavour == 'RKS' and self.path.spin_multiplicity != 1):
            raise ValueError('periodic force selection changes its explicit numerical or spin convention')
        identities(self.sources)
        if not {self.representation,self.coordinates.identity,self.path.identity,self.engine.identity,
                self.electronic.identity,self.molecular.identity,
                ObjectIdentity.from_record(self.cell.cell_id,self.cell),*self.path.sources}.issubset(self.sources):
            raise ValueError('periodic force selection omits its complete actual source closure')
        if self.scope != 'ONE_COMPLETE_PERIODIC_FORCE_PROBE_WITHOUT_ENSEMBLE_OR_KINETIC_ADMISSION':
            raise ValueError('periodic force selection cannot establish ensemble or kinetic admission')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    @property
    def probe(self):
        return MolecularForceProbe('probe.periodic.'+self.fingerprint(), self.representation, self.coordinates.identity,
            self.physical_atom_count, self.identity, self.identity, self.engine.identity,
            tuple(sorted({self.identity,*self.sources},key=lambda r:r.object_id)), OPEN_REQUIREMENTS)


def prepare_periodic_probe_selection(*, representation, path, cell, electronic, molecular, engine):
    """Derive the selected single probe from the full original molecular record."""
    exact(representation,MolecularRepresentation)
    validate_catalytic_path_selection(path,representation)
    if (cell.raw_topology != representation.raw_topology or cell.raw_coordinates != representation.raw_coordinates
            or cell.physical_atom_count != len(representation.atoms)):
        raise ValueError('periodic force preparation substitutes its complete original molecular sources')
    sources = tuple(sorted({representation.identity,representation.arrays.identity,path.identity,engine.identity,
        electronic.identity,molecular.identity,ObjectIdentity.from_record(cell.cell_id,cell),
        *representation.sources,*path.sources},key=lambda r:r.object_id))
    digest = sha256(''.join(row.object_fingerprint for row in sources).encode('ascii')).hexdigest()
    return PeriodicProbeSelection('selection.periodic-probe.'+digest,representation.identity,representation.arrays,
        len(representation.atoms),path,cell,electronic,molecular,engine,sources)


def validate_periodic_probe_model(selection, representation):
    """Join the separate full atom table before any preparation or native call."""
    exact(selection,PeriodicProbeSelection)
    exact(representation,MolecularRepresentation)
    if prepare_periodic_probe_selection(representation=representation,path=selection.path,cell=selection.cell,
            electronic=selection.electronic,molecular=selection.molecular,engine=selection.engine) != selection:
        raise ValueError('periodic force input substitutes its full original molecular record')
