# SPDX-License-Identifier: MPL-2.0
"""Cold source-bound GFN2-xTB coordinate-repair plans and native admission.

Draft selected-release adapter; no executable lookup, I/O, imports of native
libraries or subprocess execution. The external selected launcher must bind the
actual 6.7.1 binary/runtime/source revision and enforce the finite budgets.
Pure primitive records support software controls, not scientific source claims.
"""
from dataclasses import asdict, dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite, sqrt
from pathlib import PurePosixPath
import re

from empirical_lawhood.adapters.physical.rubisco_kinetics.rr_coupled_embedding import (
    MODEL_ID as FIELD_MODEL_ID, RrEmbeddingFieldV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr_coupled_preparation import (
    PreparedAtomV1, RrCoupledSourceV1, RrInitialContextV1, SOURCE_BINDINGS, construct_rr_initial_context,
)

RELEASE_TAG = '6.7.1'
TAG_COMMIT = '26b28010e805f7d1aeeef39813feb473e69cc4be'
RUNTIME_BUILD = 'edcfbbe'  # Official binary; not a claim that it was built from TAG_COMMIT.
RECALC_ENERGY_TOLERANCE_HARTREE = Decimal('1e-6')
PARAMETER_SHA256 = 'f6f05c6c5264cb2f75c54f8ac6838044541c1e493b16f1a4d4ee4fa64de5f545'
# Legacy tagged src/mctc/convert.f90 convention; deliberately not PySCF/CODATA.
ANGSTROM_PER_BOHR = Decimal('0.52917726')
FIXED_COORDINATE_TOLERANCE_ANGSTROM = Decimal('1e-10')
MODEL_ID = 'rr-gfn2-xtb-6.7.1-hardness99-constrained-coordinate-repair-v1'
LBFGS_MODEL_ID = 'rr-gfn2-xtb-6.7.1-hardness99-lbfgs-constrained-coordinate-repair-v1'
MAXIMUM_NATIVE_FILE_BYTES = 16 * 1024 ** 2
MAXIMUM_QM_ATOMS = 100
MAXIMUM_FIELD_ATOMS = 14000
PHOSPHATE_ANCHORS = frozenset(('P1', 'P2', 'O1P', 'O2P', 'O3P', 'O4P', 'O5P', 'O6P', 'O1', 'O5'))
ELEMENT_Z = {'H': 1, 'C': 6, 'N': 7, 'O': 8, 'Mg': 12, 'P': 15}
ELEMENT_VALENCE = {'H': 1, 'C': 4, 'N': 5, 'O': 6, 'Mg': 2, 'P': 5}
INITIAL_CONTEXT_PINS = {
    ('unedited-reference', 'V2'): 'fbb6858ccb92685c2f0d7d07dd8e819d0c837fd3a8e4c41033327df3f259406c',
    ('unedited-reference', 'V3'): '36ceacc1a4b25dfd2b78cac47c8b4d1d9bae5d1ea68af53cb1dbc39ad7237b0d',
    ('D263N', 'V2'): '6778512b4d25ac9a853a6d8aab975786bc66d7ac933f166f8b4ea9cf52545874',
    ('D263N', 'V3'): '0ba03a0899048474c23ba0ede9ab37baf70e7d6163277ce163157e63654ab6bf',
    ('H287N', 'V2'): 'e1a9d66fdd181d010ec672333015704b8e07f316320202f255aaf5b63f2c7476',
    ('H287N', 'V3'): '4ce643fb0a849b75995e27f9a9f5abf452778330f5d854311985a83ef4ead681',
}


def _rawjson(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def _identifier(value):
    return type(value) is str and 0 < len(value) <= 128 and value.isascii() and not any(c.isspace() for c in value)


def _coordinates(value):
    return (type(value) is tuple and len(value) == 3
            and all(type(v) is Decimal and v.is_finite() and abs(v) <= Decimal('10000') for v in value))


def angstrom_to_bohr(value):
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError('finite Decimal Angstrom coordinate required')
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return value / ANGSTROM_PER_BOHR


def bohr_to_angstrom(value):
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError('finite Decimal Bohr coordinate required')
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return value * ANGSTROM_PER_BOHR


def gradient_hartree_per_angstrom(value):
    """Chain rule: an Eh/Bohr derivative is divided by Angstrom/Bohr."""
    return angstrom_to_bohr(value)


def gfn2_damped_coulomb_kernel(distance_bohr, qm_shell_hardness, external_hardness=99.0):
    """Tagged GFN2 kernel only: arithmetic hardness mean, not singular 1/r."""
    values = (distance_bohr, qm_shell_hardness, external_hardness)
    if any(type(v) not in (int, float) or not isfinite(v) for v in values):
        raise ValueError('finite native-kernel operands required')
    if distance_bohr < 0 or qm_shell_hardness <= 0 or external_hardness != 99:
        raise ValueError('nonnegative distance, positive shell hardness and selected99 required')
    combined = (qm_shell_hardness + external_hardness) / 2
    return 1 / sqrt(distance_bohr ** 2 + 1 / combined ** 2)


@dataclass(frozen=True, slots=True)
class XtbRepairSettingsV1:
    optimizer_engine: str = 'rf'
    release_tag: str = field(init=False, default=RELEASE_TAG)
    model_id: str = field(init=False, default=MODEL_ID)
    electronic_temperature_kelvin: int = field(init=False, default=300)
    accuracy: Decimal = field(init=False, default=Decimal('0.05'))
    maximum_scc_iterations: int = field(init=False, default=250)
    requested_anc_cycles: int = field(init=False, default=60)
    anc_microcycles: int = field(init=False, default=20)
    maximum_realized_anc_cycles: int = field(init=False, default=99)
    maximum_objective_evaluations: int = field(init=False, default=120)
    native_cpu_seconds_per_case: int = field(init=False, default=300)
    native_wall_seconds_per_case: int = field(init=False, default=600)
    native_memory_bytes: int = field(init=False, default=4 * 1024 ** 3)
    native_threads: int = field(init=False, default=1)
    maximum_roster_native_cpu_seconds: int = field(init=False, default=1800)
    unpaired_electrons: int = field(init=False, default=0)
    external_hardness: int = field(init=False, default=99)
    angstrom_per_bohr: Decimal = field(init=False, default=ANGSTROM_PER_BOHR)
    native_effects: int = field(init=False, default=0)

    def __post_init__(self):
        if type(self.optimizer_engine) is not str or self.optimizer_engine not in ('rf', 'lbfgs'):
            raise ValueError('explicit selected RF or LBFGS optimizer required')
        if self.optimizer_engine == 'lbfgs':
            object.__setattr__(self, 'model_id', LBFGS_MODEL_ID)


@dataclass(frozen=True, slots=True)
class NativeAtomV1:
    atom_id: str
    element: str
    coordinates_angstrom: tuple[Decimal, Decimal, Decimal]

    def __post_init__(self):
        if not _identifier(self.atom_id) or type(self.element) is not str or self.element not in ELEMENT_Z or not _coordinates(self.coordinates_angstrom):
            raise ValueError('bounded immutable native coordinate row required')


@dataclass(frozen=True, slots=True)
class NativeFieldRowV1:
    atom_id: str
    coordinates_angstrom: tuple[Decimal, Decimal, Decimal]
    exact_charge: Fraction

    def __post_init__(self):
        if (not _identifier(self.atom_id) or not _coordinates(self.coordinates_angstrom)
                or type(self.exact_charge) is not Fraction or abs(self.exact_charge) > 4):
            raise ValueError('bounded immutable exact source-charge row required')


@dataclass(frozen=True, slots=True)
class NativeCoordinateContractV1:
    """Primitive row contract; standalone instances supply no source authority."""
    atoms: tuple[NativeAtomV1, ...]
    field_rows: tuple[NativeFieldRowV1, ...]
    fixed_atom_ids: tuple[str, ...]
    formal_charge: int
    identity: str = field(init=False)
    all_electron_count: int = field(init=False)
    valence_electron_count: int = field(init=False)

    def __post_init__(self):
        if (type(self.atoms) is not tuple or not 1 <= len(self.atoms) <= MAXIMUM_QM_ATOMS
                or any(type(a) is not NativeAtomV1 for a in self.atoms)
                or type(self.field_rows) is not tuple or len(self.field_rows) > MAXIMUM_FIELD_ATOMS
                or any(type(r) is not NativeFieldRowV1 for r in self.field_rows)
                or type(self.fixed_atom_ids) is not tuple or any(not _identifier(i) for i in self.fixed_atom_ids)
                or type(self.formal_charge) is not int or not -20 <= self.formal_charge <= 20):
            raise ValueError('bounded immutable primitive native contract required')
        ids = tuple(a.atom_id for a in self.atoms)
        mmids = tuple(a.atom_id for a in self.field_rows)
        if (len(set(ids)) != len(ids) or len(set(mmids)) != len(mmids) or set(ids) & set(mmids)
                or len(set(self.fixed_atom_ids)) != len(self.fixed_atom_ids) or not set(self.fixed_atom_ids) <= set(ids)
                or set(self.fixed_atom_ids) == set(ids)):
            raise ValueError('native identities and complete fixed/free partition differ')
        nonzero_xyz = {r.coordinates_angstrom for r in self.field_rows if r.exact_charge}
        if any(a.coordinates_angstrom in nonzero_xyz for a in self.atoms):
            raise ValueError('coincident QM/nonzero-field nucleus refuses native use')
        all_e = sum(ELEMENT_Z[a.element] for a in self.atoms) - self.formal_charge
        val_e = sum(ELEMENT_VALENCE[a.element] for a in self.atoms) - self.formal_charge
        if all_e <= 0 or val_e <= 0 or all_e % 2 or val_e % 2:
            raise ValueError('selected zero-UHF electron ledger must be positive/even')
        payload = {'qm': [(a.atom_id, a.element, tuple(str(v) for v in a.coordinates_angstrom)) for a in self.atoms],
            'full_field': [(r.atom_id, tuple(str(v) for v in r.coordinates_angstrom), r.exact_charge.numerator,
                            r.exact_charge.denominator) for r in self.field_rows],
            'fixed_atom_ids': self.fixed_atom_ids, 'formal_charge': self.formal_charge, 'model_id': MODEL_ID}
        object.__setattr__(self, 'identity', sha256(_rawjson(payload)).hexdigest())
        object.__setattr__(self, 'all_electron_count', all_e)
        object.__setattr__(self, 'valence_electron_count', val_e)


def select_fixed_atom_ids(atoms, bonds):
    """Common chemical roles; moving proton IDs never select the fixed shell."""
    if type(atoms) is not tuple or any(type(a) is not PreparedAtomV1 for a in atoms):
        raise ValueError('immutable declared chemical atoms required')
    by_id = {a.atom_id: a for a in atoms}
    if len(by_id) != len(atoms) or type(bonds) is not tuple:
        raise ValueError('unique chemical atoms/immutable graph required')
    adjacency = {i: set() for i in by_id}
    for edge in bonds:
        if type(edge) is not tuple or len(edge) != 2 or edge[0] == edge[1]:
            raise ValueError('valid immutable chemical bond required')
        if edge[0] in adjacency and edge[1] in adjacency:
            adjacency[edge[0]].add(edge[1]);adjacency[edge[1]].add(edge[0])
    fixed = set()
    for atom in atoms:
        if atom.element == 'Mg' or atom.component == 'CAP' or (
                atom.component == 'RUB' and atom.name in PHOSPHATE_ANCHORS):
            fixed.add(atom.atom_id)
        if atom.name == 'CB' and atom.component != 'RUB':
            fixed.add(atom.atom_id)
            fixed.update(i for i in adjacency[atom.atom_id] if by_id[i].element == 'H')
    return tuple(a.atom_id for a in atoms if a.atom_id in fixed)


def _closed_context_document(c):
    """Exact e973a0... cold-child projection; preserves original record layout."""
    atoms = c.physical_atoms + tuple(a for a in c.quantum_atoms if a.component == 'CAP')
    proton_records = []
    for p in c.proton_transfers:
        value = asdict(p)
        for key in ('original_coordinates', 'new_coordinates'):
            value[key] = [str(v) for v in value[key]]
        proton_records.append(value)
    return {'role': 'unrelaxed-initial-coupled-inventory-not-a-ready-QM-job', 'variant': c.variant,
        'proton_view': c.proton_view, 'protocol_sha256': c.protocol_sha256, 'source_bindings': c.source.source_bindings,
        'atom_columns': ('atom_id', 'author_chain', 'author_position', 'component', 'atom_name', 'element',
            'current_x_decimal', 'current_y_decimal', 'current_z_decimal', 'parent_atom_index',
            'coordinate_and_recipe_origin', 'donor_atom_index'),
        'atom_rows': [[a.atom_id, a.chain, a.author_position, a.component, a.name, a.element,
            *[str(v) for v in a.coordinates], a.parent_atom_index, a.origin, a.donor_atom_index] for a in atoms],
        'physical_atom_ids': [a.atom_id for a in c.physical_atoms],
        'quantum_atom_ids': [a.atom_id for a in c.quantum_atoms], 'environment_atom_ids': [a.atom_id for a in c.environment_atoms],
        'candidate_bonds': c.candidate_bonds, 'candidate_qm_lewis_bonds': c.candidate_qm_lewis_bonds,
        'candidate_qm_formal_charges': c.candidate_qm_formal_charges,
        'removed_parent_atom_indices': c.removed_parent_atom_indices, 'changed_atom_ids': c.changed_atom_ids,
        'mutation_audits': [asdict(v) for v in c.mutation_audits], 'proton_transfers': proton_records,
        'caps': [asdict(v) for v in c.caps], 'formula': c.formula, 'formal_quantum_charge': c.formal_quantum_charge,
        'electron_count': c.electron_count, 'enolate_geometry': asdict(c.enolate_geometry),
        'changed_atom_contacts': [asdict(v) for v in c.changed_atom_contacts],
        'nearest_quantum_environment_pair': c.nearest_quantum_environment_pair, 'status': c.status, 'failures': c.failures,
        'inventory_passed': c.inventory_passed, 'executable_mm_hamiltonian': c.executable_mm_hamiltonian,
        'exact_assay_parent_admitted': c.exact_assay_parent_admitted, 'ground_state_certified': c.ground_state_certified,
        'selected_singlet_hypothesis': c.selected_singlet_hypothesis, 'native_effects': c.native_effects}


@dataclass(frozen=True, slots=True)
class RrXtbRepairInputV1:
    source: RrCoupledSourceV1
    sealed_initial_context_bytes: bytes
    settings: XtbRepairSettingsV1 = field(default_factory=XtbRepairSettingsV1)
    context: RrInitialContextV1 = field(init=False)
    embedding: RrEmbeddingFieldV1 = field(init=False)
    native_contract: NativeCoordinateContractV1 = field(init=False)
    initial_context_sha256: str = field(init=False)
    context_reconstitutions: int = field(init=False, default=1)
    native_effects: int = field(init=False, default=0)

    def __post_init__(self):
        raw = self.sealed_initial_context_bytes
        if (type(self.source) is not RrCoupledSourceV1 or self.source.source_bindings != SOURCE_BINDINGS
                or type(raw) is not bytes or len(raw) > MAXIMUM_NATIVE_FILE_BYTES
                or type(self.settings) is not XtbRepairSettingsV1):
            raise ValueError('exact admitted source/sealed initial context/fixed model required')
        digest = sha256(raw).hexdigest()
        matches = [k for k, pin in INITIAL_CONTEXT_PINS.items() if digest == pin]
        if len(matches) != 1:
            raise ValueError('selected closed initial context hash differs')
        variant, view = matches[0]
        c = construct_rr_initial_context(self.source, variant=variant, proton_view=view)
        if _rawjson(_closed_context_document(c)) != raw:
            raise ValueError('reconstituted chemical projection differs from exact sealed bytes')
        e = RrEmbeddingFieldV1(c)
        if e.model_id != FIELD_MODEL_ID:
            raise ValueError('selected source-charge field model differs')
        zero_ids = tuple(r.atom.atom_id for r in e.field_atoms if not r.field_charge.numerator)
        if set(zero_ids) != {t.ca_atom_id for t in e.boundary_transfers} or len(zero_ids) != 5:
            raise ValueError('native zero filter must be exactly five declared cut CAs')
        atoms = tuple(NativeAtomV1(a.atom_id, a.element, a.coordinates) for a in c.quantum_atoms)
        rows = tuple(NativeFieldRowV1(r.atom.atom_id, r.atom.coordinates, r.field_charge.as_fraction()) for r in e.field_atoms)
        native = NativeCoordinateContractV1(atoms, rows, select_fixed_atom_ids(c.quantum_atoms, c.candidate_bonds), c.formal_quantum_charge)
        if len(native.fixed_atom_ids) != 31 or {'amber:6900', 'amber:6901'} & set(native.fixed_atom_ids):
            raise ValueError('common31 anchors or persistent physical Ha/Hb mobility differs')
        if native.all_electron_count != c.electron_count or native.valence_electron_count != {'unedited-reference': 266, 'D263N': 266, 'H287N': 258}[variant]:
            raise ValueError('all-electron/native-valence inventories differ')
        for key, value in (('context', c), ('embedding', e), ('native_contract', native), ('initial_context_sha256', digest)):
            object.__setattr__(self, key, value)


def encode_coord(atoms, coordinates_bohr):
    if type(atoms) is not tuple or type(coordinates_bohr) is not tuple or len(atoms) != len(coordinates_bohr):
        raise ValueError('complete immutable native coordinate census required')
    rows = ['$coord']
    for atom, xyz in zip(atoms, coordinates_bohr, strict=True):
        if type(atom) is not NativeAtomV1 or not _coordinates(xyz):
            raise ValueError('finite bounded native Bohr coordinate required')
        rows.append(' '.join(format(v, '.17E') for v in xyz) + ' ' + atom.element.lower())
    return ('\n'.join(rows) + '\n$end\n').encode('ascii')


def encode_pcem(rows):
    if type(rows) is not tuple or any(type(r) is not NativeFieldRowV1 for r in rows):
        raise ValueError('immutable full exact scientific field required')
    selected = tuple(r for r in rows if r.exact_charge)
    lines = [str(len(selected))];native_ids = [];native_sum = Fraction()
    with localcontext() as ctx:
        ctx.prec = 50;ctx.rounding = ROUND_HALF_EVEN
        for r in selected:
            q = Decimal(r.exact_charge.numerator) / Decimal(r.exact_charge.denominator)
            tokens = (format(q, '.17E'), *(format(angstrom_to_bohr(v), '.17E') for v in r.coordinates_angstrom), '99')
            if any(len(t) >= 48 for t in tokens):
                raise ValueError('native PCEM token exceeds tagged parser width')
            lines.append(' '.join(tokens));native_ids.append(r.atom_id);native_sum += Fraction(tokens[0])
    raw = ('\n'.join(lines) + '\n').encode('ascii')
    if len(raw) > MAXIMUM_NATIVE_FILE_BYTES:
        raise ValueError('native PCEM file exceeds bounded output')
    return raw, tuple(native_ids), tuple(r.atom_id for r in rows if not r.exact_charge), native_sum


@dataclass(frozen=True, slots=True)
class XtbStagePlanV1:
    """Pure plan; primitive controls have no admitted Rr identity or authority."""
    contract: NativeCoordinateContractV1
    stage: str
    coordinates_bohr: tuple[tuple[Decimal, Decimal, Decimal], ...]
    previous_objective_evaluations: int = 0
    settings: XtbRepairSettingsV1 = field(default_factory=XtbRepairSettingsV1)
    coordinate_bytes: bytes = field(init=False)
    pcem_bytes: bytes = field(init=False)
    control_bytes: bytes = field(init=False)
    native_field_ids: tuple[str, ...] = field(init=False)
    excluded_exact_zero_field_ids: tuple[str, ...] = field(init=False)
    native_serialized_field_charge_sum: Fraction = field(init=False)
    native_field_rounding_delta: Fraction = field(init=False)
    atom_index_id_map: tuple[tuple[int, str], ...] = field(init=False)
    fixed_atom_indices: tuple[int, ...] = field(init=False)
    identity: str = field(init=False)

    def __post_init__(self):
        if (type(self.contract) is not NativeCoordinateContractV1 or self.stage not in ('fixed-optimization', 'final-unfixed-gradient')
                or type(self.settings) is not XtbRepairSettingsV1 or type(self.previous_objective_evaluations) is not int
                or not 0 <= self.previous_objective_evaluations < self.settings.maximum_objective_evaluations):
            raise ValueError('typed bounded native stage plan required')
        coord = encode_coord(self.contract.atoms, self.coordinates_bohr)
        pcem, native_ids, omitted, total = encode_pcem(self.contract.field_rows)
        fixed = tuple(i for i, a in enumerate(self.contract.atoms, 1) if a.atom_id in self.contract.fixed_atom_ids) if self.stage == 'fixed-optimization' else ()
        control = ['$embedding', ' es=true', ' input=pointcharges', ' gradient=pcgrad', '$scc', ' iterations=250', ' temp=300']
        if self.stage == 'fixed-optimization':
            control += ['$opt', ' engine=' + self.settings.optimizer_engine, ' microcycle=20', ' maxcycle=60', '$fix', ' atoms: ' + ','.join(map(str, fixed))]
        control.append('$end')
        rawcontrol = ('\n'.join(control) + '\n').encode('ascii')
        indexmap = tuple((i, a.atom_id) for i, a in enumerate(self.contract.atoms, 1))
        values = {'coordinate_bytes': coord, 'pcem_bytes': pcem, 'control_bytes': rawcontrol,
            'native_field_ids': native_ids, 'excluded_exact_zero_field_ids': omitted,
            'native_serialized_field_charge_sum': total,
            'native_field_rounding_delta': total - sum((r.exact_charge for r in self.contract.field_rows), Fraction()),
            'atom_index_id_map': indexmap, 'fixed_atom_indices': fixed}
        identity = {'model_id': MODEL_ID, 'contract': self.contract.identity, 'stage': self.stage,
            'previous_objectives': self.previous_objective_evaluations,
            'payload_sha256': tuple(sha256(r).hexdigest() for r in (coord, pcem, rawcontrol))}
        # Preserve all frozen RF identities. The additive selected engine has
        # explicit provenance even for its engine-agnostic gradient stage.
        if self.settings.optimizer_engine == 'lbfgs':
            identity['model_id'] = self.settings.model_id
            identity['optimizer_engine'] = self.settings.optimizer_engine
        values['identity'] = sha256(_rawjson(identity)).hexdigest()
        for key, value in values.items():
            object.__setattr__(self, key, value)

    def argv(self, absolute_parameter_file):
        if (type(absolute_parameter_file) is not str or not PurePosixPath(absolute_parameter_file).is_absolute()
                or '\x00' in absolute_parameter_file or '\n' in absolute_parameter_file):
            raise ValueError('selected exact absolute GFN2 parameter file required')
        args = ('input.coord', '--gfn', '2', '--vparam', absolute_parameter_file, '--chrg', str(self.contract.formal_charge),
            '--uhf', '0', '--etemp', '300', '--acc', '0.05', '--iterations', '250', '--input', 'xcontrol.inp',
            '--parallel', '1', '--norestart', '--verbose')
        return args + (('--opt', 'vtight', '--cycles', '60') if self.stage == 'fixed-optimization' else ('--grad',))


def plan_fixed_optimization(job):
    if type(job) is not RrXtbRepairInputV1:
        raise ValueError('source-bound reconstituted Rr repair input required')
    coordinates = tuple(tuple(angstrom_to_bohr(v) for v in a.coordinates_angstrom) for a in job.native_contract.atoms)
    return XtbStagePlanV1(job.native_contract, 'fixed-optimization', coordinates, settings=job.settings)


def _number(token):
    try:value = Decimal(token.replace('D', 'E').replace('d', 'e'))
    except Exception as exc:raise ValueError('invalid native numeric token') from exc
    if not value.is_finite():
        raise ValueError('nonfinite native numeric token')
    return value


def parse_coord(raw, atoms):
    if type(raw) is not bytes or len(raw) > MAXIMUM_NATIVE_FILE_BYTES:
        raise ValueError('bounded native coordinate bytes required')
    lines = tuple(s.strip() for s in raw.decode('ascii').splitlines() if s.strip() and not s.lstrip().startswith('#'))
    if len(lines) != len(atoms) + 2 or lines[0].lower() != '$coord' or lines[-1].lower() != '$end':
        raise ValueError('native Bohr coord group/count differs')
    coordinates = []
    for atom, line in zip(atoms, lines[1:-1], strict=True):
        tokens = line.split()
        if len(tokens) != 4 or tokens[3].lower() != atom.element.lower():
            raise ValueError('complete native atom order/element mapping differs')
        xyz = tuple(_number(t) for t in tokens[:3])
        if not _coordinates(xyz):
            raise ValueError('native coordinate out of bound')
        coordinates.append(xyz)
    return tuple(coordinates)


def parse_gradient(raw, atoms):
    if type(raw) is not bytes or len(raw) > MAXIMUM_NATIVE_FILE_BYTES:
        raise ValueError('bounded native gradient bytes required')
    lines = tuple(s.strip() for s in raw.decode('ascii').splitlines() if s.strip())
    n = len(atoms)
    if len(lines) != 2 * n + 3 or lines[0] != '$grad' or lines[-1] != '$end':
        raise ValueError('complete native gradient group/count differs')
    header = re.fullmatch(r'cycle\s*=\s*1\s+SCF energy\s*=\s*(\S+)\s+\|dE/dxyz\|\s*=\s*(\S+)', lines[1])
    if header is None:
        raise ValueError('native gradient header differs')
    energy, reported_norm = tuple(_number(t) for t in header.groups())
    coord = parse_coord(('$coord\n' + '\n'.join(lines[2:2+n]) + '\n$end\n').encode(), atoms)
    gradients = []
    for line in lines[2+n:-1]:
        tokens = line.split()
        if len(tokens) != 3:
            raise ValueError('native gradient component count differs')
        gradients.append(tuple(_number(t) for t in tokens))
    if reported_norm < 0:
        raise ValueError('negative reported gradient norm')
    return energy, coord, tuple(gradients), reported_norm


def _setup_numbers(text, label):
    pattern = r'^\s*:?[ \t]*' + re.escape(label) + r'[ \t]+([^\s:]+)'
    return tuple(_number(t) for t in re.findall(pattern, text, flags=re.MULTILINE))


def _check_setup(plan, text):
    expected = {'# electrons': plan.contract.valence_electron_count, 'max. iterations': 250,
        '-> # point charges': len(plan.native_field_ids), 'electronic temp.': 300,
        'accuracy': Decimal('0.05'), 'net charge': plan.contract.formal_charge, 'unpaired electrons': 0}
    for label, value in expected.items():
        observed = _setup_numbers(text, label)
        if not observed or any(v != value for v in observed):
            raise ValueError('realized native setup differs: ' + label)
    totals = _setup_numbers(text, '-> sum of PC')
    with localcontext() as ctx:
        ctx.prec = 50
        target = Decimal(plan.native_serialized_field_charge_sum.numerator) / Decimal(plan.native_serialized_field_charge_sum.denominator)
    with localcontext() as ctx:
        ctx.prec = 50;ctx.rounding = ROUND_HALF_EVEN
        if not totals or any(abs(t-target) > Decimal('5.0001e-8') for t in totals):
            raise ValueError('native-reported full PC sum differs beyond fixed7decimal rounding')
    if not re.search(r'Hamiltonian\s+GFN2-xTB', text):
        raise ValueError('native Hamiltonian differs')
    for label in ('GBSA solvation', 'restarted?'):
        flags = re.findall(re.escape(label) + r'\s+(\S+)', text)
        if not flags or any(flag != 'false' for flag in flags):
            raise ValueError('unselected or unidentified solvent/restart realization')
    if not re.search(r'PC potential\s+true', text, re.IGNORECASE):
        raise ValueError('native external potential not realized')


def _parse_stage(plan, returncode, stdout, stderr, coordinate_bytes, gradient_bytes, native_failure_files, expected_runtime_version,
                 expected_program_argv):
    if returncode:
        raise ValueError('native process returned ' + str(returncode))
    if native_failure_files:
        raise ValueError('native failure marker retained')
    if stderr.decode('utf8').splitlines().count('normal termination of xtb') != 1:
        raise ValueError('complete official native normal-termination witness required')
    text = stdout.decode('utf8');err = stderr.decode('utf8')
    program_call = ()
    if expected_program_argv is not None or plan.settings.optimizer_engine == 'lbfgs':
        if expected_program_argv is None:
            raise ValueError('selected LBFGS stage requires exact caller-bound program argv')
        try:
            parameter = expected_program_argv[expected_program_argv.index('--vparam')+1]
        except (ValueError, IndexError) as exc:
            raise ValueError('complete native parameter/argv binding required') from exc
        if (not PurePosixPath(expected_program_argv[0]).is_absolute()
                or expected_program_argv[1:] != plan.argv(parameter)):
            raise ValueError('caller-bound native argv differs from exact selected plan')
        calls = re.findall(r'^\s*program call\s*:\s*(.+)$', text, re.MULTILINE)
        if len(calls) != 1 or tuple(calls[0].split()) != expected_program_argv:
            raise ValueError('native program-call echo differs from exact selected argv')
        program_call = expected_program_argv
    version = re.findall(r'xtb version\s+(\d+\.\d+\.\d+)\s+\(([a-f0-9]+)\)', text)
    if expected_runtime_version != RELEASE_TAG or not version or any(v != (RELEASE_TAG, RUNTIME_BUILD) for v in version):
        raise ValueError('realized native runtime version differs from selected profile')
    combined = text + '\n' + err
    if re.search(r'cannot be satisfied|did not converge|SCF not converged|FAILED TO CONVERGE|abnormal termination|\[ERROR\]', combined, re.IGNORECASE):
        raise ValueError('native convergence/error refusal')
    _check_setup(plan, text)
    successes = tuple(int(v) for v in re.findall(r'convergence criteria satisfied after\s+(\d+)\s+iterations', text))
    if any(not 1 <= v <= 250 for v in successes):
        raise ValueError('reported native SCC iteration ceiling exceeded')
    energy_tokens = re.findall(r'^\s*\|\s+TOTAL ENERGY\s+(\S+)\s+Eh\s+\|\s*$', text, re.MULTILINE)
    if len(energy_tokens) != 1:
        raise ValueError('complete final native energy witness required')
    final_energy = _number(energy_tokens[0])
    coords = parse_coord(coordinate_bytes, plan.contract.atoms)
    if plan.stage == 'fixed-optimization':
        selected_lbfgs = plan.settings.optimizer_engine == 'lbfgs'
        suffix = 'CYCLES' if selected_lbfgs else 'ITERATIONS'
        convergence = re.findall(r'GEOMETRY OPTIMIZATION CONVERGED AFTER\s+(\d+)\s+' + suffix, text)
        if len(convergence) != 1 or len(successes) != 2:
            raise ValueError('complete optimization and initial/final SCC convergence evidence required')
        steps = int(convergence[0]);cycles = tuple(int(i) for i in re.findall(r'\bCYCLE\s+(\d+)\b', text))
        if not 1 <= steps <= 99 or cycles != tuple(range(1, steps+1)):
            raise ValueError('complete ordered realized ANC cycles exceed declared overshoot bound')
        if selected_lbfgs:
            if (text.count('L-ANC optimizer') != 1 or _setup_numbers(text, 'Hessian reset') != (Decimal(20),)
                    or _setup_numbers(text, 'LBFGS images') != (Decimal(20),)
                    or _setup_numbers(text, 'energy convergence') != (Decimal('1e-7'),)
                    or _setup_numbers(text, 'grad. convergence') != (Decimal('2e-4'),)):
                raise ValueError('native selected L-ANC engine/vtight/microcycle setup differs')
        else:
            if _setup_numbers(text, 'max. optcycles') != (Decimal(60),) or _setup_numbers(text, 'ANC micro-cycles') != (Decimal(20),):
                raise ValueError('native requested ANC/microcycle setup differs')
            if not re.search(r'optimization level\s+verytight', text, re.IGNORECASE):
                raise ValueError('native vtight realization differs')
        fixed_count = re.findall(r'\*\s+(\d+)\s+fixed atom positions, i.e. in gradient', text)
        if fixed_count != [str(len(plan.fixed_atom_indices))]:
            raise ValueError('native complete fixed atom count differs')
        fixed_section = re.search(r'fixed atom positions, i.e. in gradient\s*\n\s*\n[^\n]*position/Å\s*\n((?:[ \t]*\d+[^\n]*\n)+)[ \t]*\n', text)
        if fixed_section is None:
            raise ValueError('complete native fixed-coordinate table required')
        rows = re.findall(r'^\s*(\d+)\s+(\d+)\s+([A-Za-z]{1,2})\s+(\S+)\s+(\S+)\s+(\S+)\s*$', fixed_section[1], re.MULTILINE)
        if len(rows) != len(fixed_section[1].splitlines()):
            raise ValueError('native fixed-coordinate table contains extra rows')
        if tuple(int(r[0]) for r in rows) != plan.fixed_atom_indices:
            raise ValueError('native fixed index roster differs')
        for r, index in zip(rows, plan.fixed_atom_indices, strict=True):
            atom = plan.contract.atoms[index-1]
            if int(r[1]) != ELEMENT_Z[atom.element] or r[2].lower() != atom.element.lower() or any(not _number(v).is_finite() for v in r[3:]):
                raise ValueError('native fixed atom element/finite-coordinate evidence differs')
        with localcontext() as ctx:
            ctx.prec = 50
            for index in plan.fixed_atom_indices:
                if any(abs((v-initial)*ANGSTROM_PER_BOHR) > FIXED_COORDINATE_TOLERANCE_ANGSTROM
                       for v, initial in zip(coords[index-1], plan.coordinates_bohr[index-1], strict=True)):
                    raise ValueError('native optimizer moved a fixed source coordinate')
        if gradient_bytes is not None:
            raise ValueError('opt stage supplies coordinates; only separate unfixed grad is admitted')
        objective_count = steps + 2
        return dict(final_coordinates_bohr=coords, explicit_scc_iterations=successes,
            source_inferred_converged_inner_scc_solves=steps, realized_anc_cycles=steps,
            native_objective_evaluations=objective_count, unmasked_gradient_hartree_per_bohr=(),
            full_gradient_norm_hartree_per_bohr=None, free_gradient_norm_hartree_per_bohr=None,
            energy_hartree=final_energy, realized_optimizer_engine=plan.settings.optimizer_engine,
            observed_native_program_call=program_call)
    if len(successes) != 1 or re.search(r'fixed atom positions|GEOMETRY OPTIMIZATION|\bCYCLE\s+\d+', text):
        raise ValueError('final gradient requires one SCC solve with no fixing or optimization')
    energy, gradcoords, gradients, reported_norm = parse_gradient(gradient_bytes, plan.contract.atoms)
    with localcontext() as ctx:
        ctx.prec = 50;ctx.rounding = ROUND_HALF_EVEN
        if abs(energy-final_energy) > Decimal('1e-10'):
            raise ValueError('native final energy differs from gradient-file witness')
    with localcontext() as ctx:
        ctx.prec = 50
        for xyz, expected, witness in zip(coords, plan.coordinates_bohr, gradcoords, strict=True):
            for v, initial, native in zip(xyz, expected, witness, strict=True):
                if max(abs(v-initial), abs(native-initial))*ANGSTROM_PER_BOHR > FIXED_COORDINATE_TOLERANCE_ANGSTROM:
                    raise ValueError('unfixed gradient moved geometry or differs from coordinate witness')
    fullnorm = sqrt(sum(float(v)**2 for row in gradients for v in row))
    free_components = tuple(float(v) for a,row in zip(plan.contract.atoms,gradients,strict=True)
                            if a.atom_id not in plan.contract.fixed_atom_ids for v in row)
    freenorm = sqrt(sum(v*v for v in free_components))
    free_rms = freenorm / sqrt(len(free_components))
    free_maximum = max(abs(v) for v in free_components)
    fixed_components = tuple(float(v) for a,row in zip(plan.contract.atoms,gradients,strict=True)
                             if a.atom_id in plan.contract.fixed_atom_ids for v in row)
    fixed_norm = sqrt(sum(v*v for v in fixed_components))
    fixed_rms = fixed_norm / sqrt(len(fixed_components)) if fixed_components else 0.0
    fixed_maximum = max((abs(v) for v in fixed_components), default=0.0)
    full_rms = fullnorm / sqrt(3*len(gradients))
    full_maximum = max(abs(float(v)) for row in gradients for v in row)
    with localcontext() as ctx:
        ctx.prec = 50;ctx.rounding = ROUND_HALF_EVEN
        if not isfinite(fullnorm) or not isfinite(freenorm) or abs(Decimal(str(fullnorm))-reported_norm) > Decimal('5.0001e-7'):
            raise ValueError('unmasked full gradient norm differs from native6decimal report')
    return dict(final_coordinates_bohr=coords, explicit_scc_iterations=successes,
        source_inferred_converged_inner_scc_solves=0, realized_anc_cycles=0, native_objective_evaluations=1,
        unmasked_gradient_hartree_per_bohr=gradients, full_gradient_norm_hartree_per_bohr=fullnorm,
        free_gradient_norm_hartree_per_bohr=freenorm,
        free_gradient_rms_hartree_per_bohr=free_rms,
        free_gradient_maximum_component_hartree_per_bohr=free_maximum,
        fixed_gradient_norm_hartree_per_bohr=fixed_norm,
        fixed_gradient_rms_hartree_per_bohr=fixed_rms,
        fixed_gradient_maximum_component_hartree_per_bohr=fixed_maximum,
        full_gradient_rms_hartree_per_bohr=full_rms,
        full_gradient_maximum_component_hartree_per_bohr=full_maximum, energy_hartree=energy,
        realized_optimizer_engine=None, observed_native_program_call=program_call)


@dataclass(frozen=True, slots=True)
class XtbStageResultV1:
    """Bounded raw native observation; every admission refusal retains raw bytes."""
    plan: XtbStagePlanV1
    returncode: int
    stdout: bytes
    stderr: bytes
    coordinate_bytes: bytes
    gradient_bytes: bytes | None
    expected_runtime_version: str
    native_failure_files: tuple[tuple[str, bytes], ...] = ()
    expected_program_argv: tuple[str, ...] | None = None
    status: str = field(init=False)
    failures: tuple[str, ...] = field(init=False)
    final_coordinates_bohr: tuple = field(init=False, default=())
    explicit_scc_iterations: tuple[int, ...] = field(init=False, default=())
    source_inferred_converged_inner_scc_solves: int | None = field(init=False, default=None)
    realized_anc_cycles: int | None = field(init=False, default=None)
    native_objective_evaluations: int | None = field(init=False, default=None)
    unmasked_gradient_hartree_per_bohr: tuple = field(init=False, default=())
    full_gradient_norm_hartree_per_bohr: float | None = field(init=False, default=None)
    free_gradient_norm_hartree_per_bohr: float | None = field(init=False, default=None)
    free_gradient_rms_hartree_per_bohr: float | None = field(init=False, default=None)
    free_gradient_maximum_component_hartree_per_bohr: float | None = field(init=False, default=None)
    fixed_gradient_norm_hartree_per_bohr: float | None = field(init=False, default=None)
    fixed_gradient_rms_hartree_per_bohr: float | None = field(init=False, default=None)
    fixed_gradient_maximum_component_hartree_per_bohr: float | None = field(init=False, default=None)
    full_gradient_rms_hartree_per_bohr: float | None = field(init=False, default=None)
    full_gradient_maximum_component_hartree_per_bohr: float | None = field(init=False, default=None)
    energy_hartree: Decimal | None = field(init=False, default=None)
    realized_optimizer_engine: str | None = field(init=False, default=None)
    observed_native_program_call: tuple[str, ...] = field(init=False, default=())
    parser_native_executions: int = field(init=False, default=0)
    scientific_geometry_admitted: bool = field(init=False, default=False)

    def __post_init__(self):
        if (type(self.plan) is not XtbStagePlanV1 or type(self.returncode) is not int
                or any(type(r) is not bytes or len(r) > MAXIMUM_NATIVE_FILE_BYTES for r in (self.stdout,self.stderr,self.coordinate_bytes))
                or self.gradient_bytes is not None and (type(self.gradient_bytes) is not bytes or len(self.gradient_bytes)>MAXIMUM_NATIVE_FILE_BYTES)
                or type(self.expected_runtime_version) is not str or not re.fullmatch(r'\d+\.\d+\.\d+',self.expected_runtime_version)
                or type(self.native_failure_files) is not tuple or any(type(r) is not tuple or len(r)!=2
                    or r[0] not in ('.sccnotconverged','NOT_CONVERGED') or type(r[1]) is not bytes
                    or len(r[1])>MAXIMUM_NATIVE_FILE_BYTES for r in self.native_failure_files)
                or self.expected_program_argv is not None and (type(self.expected_program_argv) is not tuple
                    or not 1 <= len(self.expected_program_argv) <= 64
                    or any(type(v) is not str or not v or len(v)>4096 or not v.isascii()
                           or any(c.isspace() for c in v) for v in self.expected_program_argv))):
            raise ValueError('bounded immutable native raw observation required')
        try:
            values = _parse_stage(self.plan,self.returncode,self.stdout,self.stderr,self.coordinate_bytes,self.gradient_bytes,
                self.native_failure_files,self.expected_runtime_version,self.expected_program_argv)
            if self.plan.previous_objective_evaluations+values['native_objective_evaluations']>120:
                raise ValueError('cumulative native objective ceiling exceeded')
        except (ValueError, UnicodeError, ArithmeticError) as exc:
            object.__setattr__(self,'status','NATIVE_STAGE_REFUSED');object.__setattr__(self,'failures',(str(exc),))
        else:
            for key,value in values.items():object.__setattr__(self,key,value)
            object.__setattr__(self,'status','NATIVE_STAGE_PASSED');object.__setattr__(self,'failures',())


def plan_final_unfixed_gradient(job, optimization):
    if (type(job) is not RrXtbRepairInputV1 or type(optimization) is not XtbStageResultV1
            or optimization.status!='NATIVE_STAGE_PASSED' or optimization.plan.stage!='fixed-optimization'
            or optimization.plan != plan_fixed_optimization(job)):
        raise ValueError('matching admitted fixed-optimization coordinates required')
    return XtbStagePlanV1(job.native_contract,'final-unfixed-gradient',optimization.final_coordinates_bohr,
        previous_objective_evaluations=optimization.native_objective_evaluations,settings=job.settings)


@dataclass(frozen=True, slots=True)
class XtbRepairPairAssessmentV1:
    """Same-geometry fresh-SCC consistency; no kinetic/geometry qualification."""
    optimization: XtbStageResultV1
    diagnostic: XtbStageResultV1
    status: str = field(init=False)
    energy_difference_hartree: Decimal | None = field(init=False, default=None)
    native_objective_evaluations: int | None = field(init=False)
    parser_native_executions: int = field(init=False, default=0)
    scientific_geometry_admitted: bool = field(init=False, default=False)

    def __post_init__(self):
        opt, diag = self.optimization, self.diagnostic
        if (type(opt) is not XtbStageResultV1 or type(diag) is not XtbStageResultV1
                or opt.plan.stage != 'fixed-optimization' or diag.plan.stage != 'final-unfixed-gradient'
                or opt.plan.contract != diag.plan.contract or opt.plan.settings != diag.plan.settings
                or diag.plan.previous_objective_evaluations != opt.native_objective_evaluations
                or diag.plan.coordinates_bohr != opt.final_coordinates_bohr):
            raise ValueError('exact paired optimized-geometry/full-field diagnostic join required')
        counts = (opt.native_objective_evaluations, diag.native_objective_evaluations)
        total = None if any(n is None for n in counts) else sum(counts)
        object.__setattr__(self, 'native_objective_evaluations', total)
        if opt.status != 'NATIVE_STAGE_PASSED' or diag.status != 'NATIVE_STAGE_PASSED':
            object.__setattr__(self, 'status', 'NATIVE_STAGE_REFUSED')
            return
        with localcontext() as ctx:
            ctx.prec = 50
            ctx.rounding = ROUND_HALF_EVEN
            difference = diag.energy_hartree - opt.energy_hartree
        object.__setattr__(self, 'energy_difference_hartree', difference)
        object.__setattr__(self, 'status', 'RECALC_DISAGREEMENT' if abs(difference) > RECALC_ENERGY_TOLERANCE_HARTREE
                           else 'FRESH_SCC_ENERGY_CONSISTENT')
