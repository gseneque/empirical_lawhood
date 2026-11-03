# SPDX-License-Identifier: MPL-2.0
"""Cold, single-attempt xTB gradient callback for selected ASH QM/MM callers.

The selected caller owns source admission, bounded process execution and custody.
This owner performs no filesystem access, lookup, subprocess, ASH import or native
initialization. Every call requests one unrestricted gradient, even when ASH
requests only energy. Primitive controls do not acquire scientific authority.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite
from numbers import Real
from pathlib import PurePosixPath
import re

from empirical_lawhood.adapters.simulators.rubisco_electronic.rr_xtb_repair import (
    ANGSTROM_PER_BOHR, ELEMENT_VALENCE, ELEMENT_Z, MAXIMUM_FIELD_ATOMS,
    MAXIMUM_NATIVE_FILE_BYTES, MAXIMUM_QM_ATOMS, PARAMETER_SHA256, RELEASE_TAG,
    RUNTIME_BUILD, NativeAtomV1, NativeFieldRowV1, angstrom_to_bohr, encode_coord,
    encode_pcem, parse_gradient,
)

BINARY_SHA256 = 'debf27a9e0fa4bfb5ca75aafe4b90d8211f08ec2f4a482f375a4987212eaa12a'
ASH_ANGSTROM_PER_BOHR = Decimal('0.5291772109303')
MAXIMUM_CALLBACKS = 120
MODEL_ID = 'rr-gfn2-xtb-6.7.1-hardness99-ash-single-point-v1'
_COORDINATE_TOLERANCE_ANGSTROM = Decimal('1e-10')
_NATIVE_VALUE_BOUND = Decimal('1e12')


def _absolute_path(value):
    return (type(value) is str and 0 < len(value) <= 4096 and value.isascii()
            and not any(c.isspace() for c in value) and '\x00' not in value
            and PurePosixPath(value).is_absolute() and '..' not in PurePosixPath(value).parts)


def _decimal(value):
    if isinstance(value, bool) or isinstance(value, (str, bytes)):
        raise ValueError('finite numeric input required')
    if type(value) is Decimal:
        result = value
    elif type(value) is int:
        result = Decimal(value)
    else:
        if not isinstance(value, Real):
            raise ValueError('real numeric input required')
        try:
            native = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('finite numeric input required') from exc
        if not isfinite(native):
            raise ValueError('finite numeric input required')
        # Preserve the actual ASH/NumPy binary64 input, not a rounded display.
        result = Decimal.from_float(native)
    if not result.is_finite():
        raise ValueError('finite numeric input required')
    return result


def _rows(values, count):
    try:
        if len(values) != count:
            raise ValueError('complete numeric Cartesian rows required')
        rows = []
        for row in values:
            if len(row) != 3:
                raise ValueError('complete numeric Cartesian rows required')
            rows.append(tuple(_decimal(v) for v in row))
        rows = tuple(rows)
    except TypeError as exc:
        raise ValueError('complete numeric Cartesian rows required') from exc
    if len(rows) != count or any(len(row) != 3 for row in rows):
        raise ValueError('complete numeric Cartesian rows required')
    return rows


def native_gradient_to_ash(value):
    """Chain rule for x_A=b_native*x_native=b_ASH*x_ASH."""
    if type(value) is not Decimal or not value.is_finite() or abs(value) > _NATIVE_VALUE_BOUND:
        raise ValueError('finite bounded native gradient required')
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        return value * ASH_ANGSTROM_PER_BOHR / ANGSTROM_PER_BOHR


@dataclass(frozen=True, slots=True)
class XtbSinglePointPlanV1:
    """Pure execution request; paths and source claims require caller admission."""
    execution_id: str
    output_locator: str
    executable_path: str
    parameter_path: str
    atoms: tuple[NativeAtomV1, ...]
    field_rows: tuple[NativeFieldRowV1, ...]
    formal_charge: int
    unpaired_electrons: int
    embedded: bool
    model_id: str = field(init=False, default=MODEL_ID)
    binary_sha256: str = field(init=False, default=BINARY_SHA256)
    parameter_sha256: str = field(init=False, default=PARAMETER_SHA256)
    release_tag: str = field(init=False, default=RELEASE_TAG)
    runtime_build: str = field(init=False, default=RUNTIME_BUILD)
    coordinate_bytes: bytes = field(init=False)
    pcem_bytes: bytes | None = field(init=False)
    control_bytes: bytes = field(init=False)
    input_files: tuple[tuple[str, bytes], ...] = field(init=False)
    program_argv: tuple[str, ...] = field(init=False)
    coordinates_bohr: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    native_field_ids: tuple[str, ...] = field(init=False)
    excluded_exact_zero_field_ids: tuple[str, ...] = field(init=False)
    native_serialized_field_charge_sum: Fraction = field(init=False)
    native_field_rounding_delta: Fraction = field(init=False)
    all_electron_count: int = field(init=False)
    valence_electron_count: int = field(init=False)
    identity: str = field(init=False)

    def __post_init__(self):
        if (type(self.execution_id) is not str or re.fullmatch(r'call-[0-9]{4}', self.execution_id) is None
                or not all(_absolute_path(v) for v in (self.output_locator, self.executable_path, self.parameter_path))
                or type(self.atoms) is not tuple or not 1 <= len(self.atoms) <= MAXIMUM_QM_ATOMS
                or any(type(a) is not NativeAtomV1 for a in self.atoms)
                or type(self.field_rows) is not tuple or len(self.field_rows) > MAXIMUM_FIELD_ATOMS
                or any(type(r) is not NativeFieldRowV1 for r in self.field_rows)
                or type(self.formal_charge) is not int or not -20 <= self.formal_charge <= 20
                or type(self.unpaired_electrons) is not int or not 0 <= self.unpaired_electrons <= 20
                or type(self.embedded) is not bool or (not self.embedded and self.field_rows)):
            raise ValueError('bounded immutable selected single-point request required')
        qmids = tuple(a.atom_id for a in self.atoms)
        mmids = tuple(r.atom_id for r in self.field_rows)
        if len(set(qmids)) != len(qmids) or len(set(mmids)) != len(mmids) or set(qmids) & set(mmids):
            raise ValueError('unique disjoint QM and point-charge row identities required')
        nonzero_xyz = {r.coordinates_angstrom for r in self.field_rows if r.exact_charge}
        if any(a.coordinates_angstrom in nonzero_xyz for a in self.atoms):
            raise ValueError('coincident QM and nonzero point charge refuses execution')
        all_e = sum(ELEMENT_Z[a.element] for a in self.atoms) - self.formal_charge
        val_e = sum(ELEMENT_VALENCE[a.element] for a in self.atoms) - self.formal_charge
        if (min(all_e, val_e) <= 0 or self.unpaired_electrons > min(all_e, val_e)
                or (all_e - self.unpaired_electrons) % 2 or (val_e - self.unpaired_electrons) % 2):
            raise ValueError('charge/UHF electron ledger differs')
        xyz = tuple(tuple(angstrom_to_bohr(v) for v in a.coordinates_angstrom) for a in self.atoms)
        coord = encode_coord(self.atoms, xyz)
        pc, native_ids, omitted, total = encode_pcem(self.field_rows)
        control = (['$embedding', ' es=true', ' input=pointcharges', ' gradient=pcgrad'] if self.embedded else [])
        control += ['$scc', ' iterations=250', ' temp=300', '$end']
        rawcontrol = ('\n'.join(control) + '\n').encode('ascii')
        files = (('input.coord', coord), ('xcontrol.inp', rawcontrol))
        if self.embedded:
            files += (('pointcharges', pc),)
        argv = (self.executable_path, 'input.coord', '--gfn', '2', '--vparam', self.parameter_path,
                '--chrg', str(self.formal_charge), '--uhf', str(self.unpaired_electrons),
                '--etemp', '300', '--acc', '0.05', '--iterations', '250', '--input', 'xcontrol.inp',
                '--parallel', '1', '--norestart', '--verbose', '--grad')
        payload = {'model_id': MODEL_ID, 'execution_id': self.execution_id, 'output_locator': self.output_locator,
                   'argv': argv, 'binary': BINARY_SHA256, 'parameters': PARAMETER_SHA256,
                   'qm': [(a.atom_id, a.element, tuple(str(v) for v in a.coordinates_angstrom)) for a in self.atoms],
                   'field': [(r.atom_id, tuple(str(v) for v in r.coordinates_angstrom),
                              r.exact_charge.numerator, r.exact_charge.denominator) for r in self.field_rows],
                   'files': [(n, sha256(raw).hexdigest()) for n, raw in files]}
        identity = sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        values = {'coordinate_bytes': coord, 'pcem_bytes': pc if self.embedded else None,
                  'control_bytes': rawcontrol, 'input_files': files, 'program_argv': argv,
                  'coordinates_bohr': xyz, 'native_field_ids': native_ids,
                  'excluded_exact_zero_field_ids': omitted, 'native_serialized_field_charge_sum': total,
                  'native_field_rounding_delta': total - sum((r.exact_charge for r in self.field_rows), Fraction()),
                  'all_electron_count': all_e, 'valence_electron_count': val_e, 'identity': identity}
        for name, value in values.items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class XtbSinglePointCaptureV1:
    """Raw caller capture. Costs and full file census belong to its sidecar."""
    plan_identity: str
    execution_id: str
    output_locator: str
    program_argv: tuple[str, ...]
    returncode: int | None
    stdout: bytes
    stderr: bytes
    gradient_bytes: bytes | None = None
    pcgrad_bytes: bytes | None = None
    native_failure_files: tuple[str, ...] = ()
    operational_refusal: str | None = None

    def __post_init__(self):
        if (type(self.plan_identity) is not str or re.fullmatch('[0-9a-f]{64}', self.plan_identity) is None
                or type(self.execution_id) is not str or re.fullmatch(r'call-[0-9]{4}', self.execution_id) is None
                or not _absolute_path(self.output_locator) or type(self.program_argv) is not tuple
                or not self.program_argv or any(type(v) is not str for v in self.program_argv)
                or (self.returncode is not None and type(self.returncode) is not int)
                or (self.returncode is None and self.operational_refusal is None)
                or type(self.native_failure_files) is not tuple
                or any(type(v) is not str or not v or '/' in v or '\x00' in v for v in self.native_failure_files)
                or len(set(self.native_failure_files)) != len(self.native_failure_files)
                or (self.operational_refusal is not None and
                    (type(self.operational_refusal) is not str or not 0 < len(self.operational_refusal) <= 1024))):
            raise ValueError('typed raw execution/custody capture required')
        for raw in (self.stdout, self.stderr, self.gradient_bytes, self.pcgrad_bytes):
            if raw is not None and (type(raw) is not bytes or len(raw) > MAXIMUM_NATIVE_FILE_BYTES):
                raise ValueError('bounded original native output bytes required')
        if type(self.stdout) is not bytes or type(self.stderr) is not bytes:
            raise ValueError('complete original stdout/stderr bytes required')


def _native_number(token):
    try:
        value = Decimal(token.replace('D', 'E').replace('d', 'e'))
    except Exception as exc:
        raise ValueError('invalid native numeric token') from exc
    if not value.is_finite() or abs(value) > _NATIVE_VALUE_BOUND:
        raise ValueError('finite bounded native numeric token required')
    return value


def _setup_numbers(text, label):
    return tuple(_native_number(v) for v in re.findall(
        r'^\s*:?[ \t]*' + re.escape(label) + r'[ \t]+([^\s:]+)', text, re.MULTILINE))


@dataclass(frozen=True, slots=True)
class XtbSinglePointObservationV1:
    plan: XtbSinglePointPlanV1
    capture: XtbSinglePointCaptureV1
    energy_hartree: Decimal = field(init=False)
    qm_gradient_native: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    pc_gradient_native: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    qm_gradient_ash: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    pc_gradient_ash: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    native_gradient_coordinates_bohr: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    scc_iterations: int = field(init=False)

    def __post_init__(self):
        p, c = self.plan, self.capture
        if type(p) is not XtbSinglePointPlanV1 or type(c) is not XtbSinglePointCaptureV1:
            raise ValueError('typed plan and original capture required')
        if (c.plan_identity != p.identity or c.execution_id != p.execution_id
                or c.output_locator != p.output_locator or c.program_argv != p.program_argv):
            raise ValueError('capture belongs to a different selected plan/locator/argv')
        if c.operational_refusal or c.returncode != 0 or c.native_failure_files:
            raise ValueError('native or operational execution refused')
        text, err = c.stdout.decode('utf8'), c.stderr.decode('utf8')
        if err.splitlines().count('normal termination of xtb') != 1:
            raise ValueError('complete official normal termination witness required')
        if re.search(r'cannot be satisfied|did not converge|SCF not converged|FAILED TO CONVERGE|abnormal termination|\[ERROR\]', text+'\n'+err, re.IGNORECASE):
            raise ValueError('native convergence/error refusal')
        versions = re.findall(r'xtb version\s+(\d+\.\d+\.\d+)\s+\(([a-f0-9]+)\)', text)
        calls = re.findall(r'^\s*program call\s*:\s*(.+)$', text, re.MULTILINE)
        if versions != [(RELEASE_TAG, RUNTIME_BUILD)] or len(calls) != 1 or tuple(calls[0].split()) != p.program_argv:
            raise ValueError('realized native release or exact program argv differs')
        expected = {'# electrons': p.valence_electron_count, 'max. iterations': 250,
                    'electronic temp.': 300, 'accuracy': Decimal('0.05'),
                    'net charge': p.formal_charge, 'unpaired electrons': p.unpaired_electrons}
        if p.embedded:
            expected['-> # point charges'] = len(p.native_field_ids)
        for label, value in expected.items():
            observed = _setup_numbers(text, label)
            if not observed or any(v != value for v in observed):
                raise ValueError('realized native setup differs: '+label)
        if not re.search(r'Hamiltonian\s+GFN2-xTB', text):
            raise ValueError('realized Hamiltonian differs')
        for label, expected_flag in (('GBSA solvation', 'false'), ('restarted?', 'false'),
                                      ('PC potential', 'true' if p.embedded else 'false')):
            flags = re.findall(re.escape(label)+r'\s+(\S+)', text)
            if not flags or any(v != expected_flag for v in flags):
                raise ValueError('unselected solvent/restart/embedding realization')
        if p.embedded:
            with localcontext() as ctx:
                ctx.prec = 50
                target = Decimal(p.native_serialized_field_charge_sum.numerator) / Decimal(p.native_serialized_field_charge_sum.denominator)
                totals = _setup_numbers(text, '-> sum of PC')
                if not totals or any(abs(v-target) > Decimal('5.0001e-8') for v in totals):
                    raise ValueError('native serialized point-charge sum differs')
        solves = tuple(int(v) for v in re.findall(r'convergence criteria satisfied after\s+(\d+)\s+iterations', text))
        if len(solves) != 1 or not 1 <= solves[0] <= 250 or re.search(r'fixed atom positions|GEOMETRY OPTIMIZATION|\bCYCLE\s+\d+', text):
            raise ValueError('one converged unrestricted SCC objective required')
        energies = re.findall(r'^\s*\|\s+TOTAL ENERGY\s+(\S+)\s+Eh\s+\|\s*$', text, re.MULTILINE)
        if len(energies) != 1 or c.gradient_bytes is None:
            raise ValueError('complete native energy and QM gradient required')
        energy, coords, qgrad, norm = parse_gradient(c.gradient_bytes, p.atoms)
        for value in (energy, norm, *(v for row in qgrad for v in row)):
            if abs(value) > _NATIVE_VALUE_BOUND:
                raise ValueError('native gradient/energy exceeds numeric bound')
        with localcontext() as ctx:
            ctx.prec = 50
            ctx.rounding = ROUND_HALF_EVEN
            if abs(energy-_native_number(energies[0])) > Decimal('1e-10'):
                raise ValueError('gradient-file and stdout energy differ')
            if any(abs(v-w)*ANGSTROM_PER_BOHR > _COORDINATE_TOLERANCE_ANGSTROM
                   for row, expected_xyz in zip(coords, p.coordinates_bohr, strict=True)
                   for v, w in zip(row, expected_xyz, strict=True)):
                raise ValueError('native gradient coordinates differ from exact input')
            fullnorm = sum((v*v for row in qgrad for v in row), Decimal()).sqrt()
            if abs(norm-fullnorm) > Decimal('5.0001e-7'):
                raise ValueError('reported six-decimal QM gradient norm differs')
        pcgrad = []
        if p.embedded:
            if type(c.pcgrad_bytes) is not bytes:
                raise ValueError('complete original PC gradient required')
            lines = c.pcgrad_bytes.decode('ascii').splitlines()
            if len(lines) != len(p.native_field_ids):
                raise ValueError('complete ordered PC gradient row census differs')
            for line in lines:
                tokens = line.split()
                if len(tokens) != 3:
                    raise ValueError('three finite PC gradient components required')
                pcgrad.append(tuple(_native_number(v) for v in tokens))
        elif c.pcgrad_bytes is not None:
            raise ValueError('unembedded objective supplies unexpected PC gradient')
        # Restore exact-zero rows to ASH's full field order with exact zero force.
        by_id = dict(zip(p.native_field_ids, pcgrad, strict=True))
        fullpc = tuple(by_id.get(r.atom_id, (Decimal(0),)*3) for r in p.field_rows)
        values = {'energy_hartree': energy, 'qm_gradient_native': qgrad, 'pc_gradient_native': fullpc,
                  'qm_gradient_ash': tuple(tuple(native_gradient_to_ash(v) for v in row) for row in qgrad),
                  'pc_gradient_ash': tuple(tuple(native_gradient_to_ash(v) for v in row) for row in fullpc),
                  'native_gradient_coordinates_bohr': coords, 'scc_iterations': solves[0]}
        for name, value in values.items():
            object.__setattr__(self, name, value)


class StrictQmmmXtbTheoryV1:
    """ASH-compatible adapter; explicit executor and retention hooks own effects."""
    theorytype = 'QM'
    theorynamelabel = MODEL_ID
    analytic_hessian = False

    def __init__(self, *, executable_path, parameter_path, output_root, executor, retain_capture,
                 maximum_callbacks=MAXIMUM_CALLBACKS):
        if (not all(_absolute_path(v) for v in (executable_path, parameter_path, output_root))
                or not callable(executor) or not callable(retain_capture)
                or type(maximum_callbacks) is not int or not 1 <= maximum_callbacks <= MAXIMUM_CALLBACKS):
            raise ValueError('explicit selected paths, bounded executor and custody hooks required')
        self.executable_path, self.parameter_path, self.output_root = executable_path, parameter_path, output_root
        self.executor, self.retain_capture = executor, retain_capture
        self.maximum_callbacks = maximum_callbacks
        self.numcores = 1
        self.callback_reservations = 0
        self.last_observation = None

    def set_numcores(self, numcores):
        if type(numcores) is not int or numcores != 1:
            raise ValueError('selected callback uses one native thread')
        self.numcores = 1

    def run(self, current_coords=None, current_MM_coords=None, MMcharges=None, qm_elems=None,
            mm_elems=None, elems=None, Grad=False, PC=False, numcores=None, label=None, charge=None, mult=None):
        if (type(Grad) is not bool or type(PC) is not bool or type(charge) is not int
                or type(mult) is not int or not 1 <= mult <= 21 or (numcores is not None and numcores != 1)
                or (label is not None and (type(label) is not str or len(label) > 256))):
            raise ValueError('explicit bounded charge/multiplicity and one-thread ASH call required')
        self.set_numcores(self.numcores if numcores is None else numcores)
        try:
            element_rows = qm_elems if qm_elems is not None else elems
            if not 1 <= len(element_rows) <= MAXIMUM_QM_ATOMS:
                raise ValueError('bounded complete QM element roster required')
            elements = tuple(element_rows)
        except TypeError as exc:
            raise ValueError('complete explicit QM elements required') from exc
        if elems is not None and qm_elems is not None and tuple(elems) != elements:
            raise ValueError('conflicting QM element rosters')
        coords = _rows(current_coords, len(elements))
        atoms = tuple(NativeAtomV1(f'qm-{i:04d}', element, xyz)
                      for i, (element, xyz) in enumerate(zip(elements, coords, strict=True), 1))
        if PC:
            try:
                if len(MMcharges) > MAXIMUM_FIELD_ATOMS:
                    raise ValueError('bounded complete PC charge roster required')
                charges = tuple(_decimal(v) for v in MMcharges)
            except TypeError as exc:
                raise ValueError('complete explicit PC charge roster required') from exc
            mmcoords = _rows(current_MM_coords, len(charges))
            if mm_elems is not None and len(tuple(mm_elems)) != len(charges):
                raise ValueError('PC element/coordinate census differs')
            field_rows = tuple(NativeFieldRowV1(f'pc-{i:05d}', xyz, Fraction(q))
                               for i, (xyz, q) in enumerate(zip(mmcoords, charges, strict=True), 1))
        else:
            if MMcharges is not None and len(MMcharges):
                raise ValueError('unembedded callback cannot ignore supplied charges')
            if current_MM_coords is not None and len(current_MM_coords):
                raise ValueError('unembedded callback cannot ignore supplied PC coordinates')
            field_rows = ()
        if self.callback_reservations >= self.maximum_callbacks:
            raise ValueError('finite callback reservation ceiling reached')
        name = f'call-{self.callback_reservations+1:04d}'
        plan = XtbSinglePointPlanV1(name, str(PurePosixPath(self.output_root)/name),
                                  self.executable_path, self.parameter_path, atoms, field_rows, charge, mult-1, PC)
        # An attempted executor call consumes its reservation even if it refuses.
        self.callback_reservations += 1
        self.last_observation = None
        capture = self.executor(plan)
        self.retain_capture(plan, capture)
        observation = XtbSinglePointObservationV1(plan, capture)
        self.last_observation = observation
        if not Grad:
            return float(observation.energy_hartree)
        # Only selected gradient return needs NumPy, for ASH's array arithmetic.
        import numpy as np
        qm = np.asarray(observation.qm_gradient_ash, dtype=float)
        if PC:
            return float(observation.energy_hartree), qm, np.asarray(observation.pc_gradient_ash, dtype=float).reshape((-1, 3))
        return float(observation.energy_hartree), qm
