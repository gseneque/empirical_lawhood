# SPDX-License-Identifier: MPL-2.0
"""Additive point-field callback with complete prospective scientific operands.

Historical rr_qmmm_xtb/rr_xtb_repair bytes stay unchanged. Source numerical,
electron/spin, encoding, SCC250/accuracy0.05/temp300/no-restart and unrestricted
gradient interpretation are preserved. Arbitrary callback, atom-count and raw
file-byte ceilings are absent. Raw capture is required before interpretation.
Selected parser token widths and finite numerical criteria remain scientific
contracts. No import performs native work, acquisition or environment mutation.

This concrete point-charge Hamiltonian is not a finite-width Gaussian model.
The selected caller must authenticate sources, native stock, allocation, exact
apparatus and every complete file/call return, using existing custody owners.
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
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.contracts import FileEvidence, SourceMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from empirical_lawhood.adapters.simulators.rubisco_electronic.rr_xtb_repair import (
    ANGSTROM_PER_BOHR, ELEMENT_VALENCE, ELEMENT_Z, PARAMETER_SHA256, RELEASE_TAG,
    RUNTIME_BUILD, NativeAtomV1, NativeFieldRowV1, angstrom_to_bohr, encode_coord,
    _coordinates, _number,
)

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
    return raw, tuple(native_ids), tuple(r.atom_id for r in rows if not r.exact_charge), native_sum

def parse_coord(raw, atoms):
    if type(raw) is not bytes:
        raise ValueError('complete native coordinate bytes required')
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
    if type(raw) is not bytes:
        raise ValueError('complete native gradient bytes required')
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

BINARY_SHA256 = 'debf27a9e0fa4bfb5ca75aafe4b90d8211f08ec2f4a482f375a4987212eaa12a'
ASH_ANGSTROM_PER_BOHR = Decimal('0.5291772109303')
MODEL_ID = 'gfn2-xtb-6.7.1-hardness99-ash-prospective-single-point-v2'
_COORDINATE_TOLERANCE_ANGSTROM = Decimal('1e-10')
_NATIVE_VALUE_BOUND = Decimal('1e12')


def _absolute_path(value):
    return (type(value) is str and 0 < len(value) <= 4096 and value.isascii()
            and not any(c.isspace() for c in value) and '\x00' not in value
            and PurePosixPath(value).is_absolute() and '..' not in PurePosixPath(value).parts)


def _stock_file(row):
    path = row['path']
    resolved = row.get('resolved_path', path)
    if not _absolute_path(path) or not _absolute_path(resolved):
        raise ValueError('selected xTB stock changes its absolute source locator')
    evidence = FileEvidence(row.get('relative_path', path.lstrip('/')),
                            row.get('size_bytes', row.get('bytes')), row['sha256'])
    if type(evidence.byte_count) is not int or evidence.byte_count <= 0:
        raise ValueError('selected xTB stock omits its exact regular-file bytes')
    return path, resolved, evidence


def _stock_source(member, row):
    if type(member) is not SourceMember:
        raise ValueError('selected xTB stock needs original typed source bytes')
    member.__post_init__()
    path, _, evidence = _stock_file(row)
    if (member.original_url, len(member.raw_utf8.encode()), member.sha256) != (
            path, evidence.byte_count, evidence.sha256):
        raise ValueError('selected xTB source differs from its authenticated stock binding')


def _stock_projection(selected):
    for member in (selected.stock_proof, selected.version_stdout, selected.unit_source, selected.build_terminal):
        if type(member) is not SourceMember:
            raise ValueError('selected xTB stock needs original typed source bytes')
        member.__post_init__()
        if not _absolute_path(member.original_url):
            raise ValueError('selected xTB stock omits its exact local source locator')
    proof = json.loads(selected.stock_proof.raw_utf8)
    if proof.get('schema') != 'el.xtb.official-upstream-native-stock.v1':
        raise ValueError('selected xTB stock needs its explicit source/build proof')
    commit = proof['source_commit']
    if not isinstance(commit, str) or re.fullmatch('[a-f0-9]{40}', commit) is None:
        raise ValueError('selected xTB stock omits its immutable source commit')
    operands = proof['qualification_operands']
    executable, parameter = _stock_file(operands['executable']), _stock_file(operands['parameter'])
    if parameter[2].sha256 != PARAMETER_SHA256:
        raise ValueError('selected stock changes the declared GFN2 parameter bytes')
    versions = tuple(row for row in proof['metadata_processes']
                     if tuple(row['argv']) == (executable[0], '--version'))
    if (len(versions) != 1 or type(versions[0]['return_code']) is not int
            or versions[0]['return_code'] != 0):
        raise ValueError('selected xTB stock lacks its known successful version observation')
    _stock_source(selected.version_stdout, versions[0]['stdout'])
    banner = re.findall(r'xtb version\s+(\d+\.\d+\.\d+)\s+\(([a-f0-9]+)\)',
                        selected.version_stdout.raw_utf8)
    if banner != [(RELEASE_TAG, commit)]:
        raise ValueError('selected xTB version observation differs from its source/build')
    _stock_source(selected.unit_source, operands['unit_source'])
    units = re.findall(r'\bautoaa\s*=\s*([0-9.]+)_wp', selected.unit_source.raw_utf8)
    if units != [str(ANGSTROM_PER_BOHR)] or Decimal(operands['native_unit_angstrom_per_bohr']) != ANGSTROM_PER_BOHR:
        raise ValueError('selected stock changes the declared native gradient/coordinate unit')
    _stock_source(selected.build_terminal, proof['known_build_terminal'])
    terminal = json.loads(selected.build_terminal.raw_utf8)
    if (type(terminal.get('exit_code')) is not int or terminal.get('exit_code') != 0
            or terminal.get('tool_authoritatively_terminal') is not True
            or terminal.get('selected_source_commit') != commit):
        raise ValueError('selected xTB stock lacks its known source-bound build terminal')
    runtime = tuple(_stock_file(dict(path=row['selected_path'], resolved_path=row['resolved_path'],
                                    size_bytes=row['size_bytes'], sha256=row['sha256']))
                    for row in proof['runtime_external_members'])
    if not runtime or len({row[0] for row in runtime}) != len(runtime):
        raise ValueError('selected xTB stock loses its complete runtime file census')
    if set(operands['library_closure']) != {'elf_dynamic', 'elf_header', 'elf_program_headers', 'ldd'}:
        raise ValueError('selected xTB stock omits its exact loader closure observations')
    closure = tuple(_stock_file(row) for _, row in sorted(operands['library_closure'].items()))
    return executable, parameter, runtime, closure, banner[0]


@dataclass(frozen=True, slots=True)
class SelectedXtbStockV1(CanonicalRecord):
    """Exact source-built stock evidence; no I/O, qualification or entry authority.

    The caller authenticates every file_binding using the existing custody/I/O
    owner before contact. Interpreter and ASH/Reference closure remain separate
    caller operands. An independently assessed control supplies scientific use.
    """
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-coupled/selected-xtb-stock'
    selection_id: str
    stock_proof: SourceMember
    version_stdout: SourceMember
    unit_source: SourceMember
    build_terminal: SourceMember

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        _stock_projection(self)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)

    @property
    def file_bindings(self):
        executable, parameter, runtime, closure, _ = _stock_projection(self)
        sources = tuple(_stock_file(dict(path=row.original_url, size_bytes=len(row.raw_utf8.encode()),
                                         sha256=row.sha256))
                        for row in (self.stock_proof, self.version_stdout, self.unit_source, self.build_terminal))
        return tuple(sorted((*sources, executable, parameter, *runtime, *closure), key=lambda row: row[0]))


def _request_identity_payload(plan, binary, parameters, argv, files):
    return {'model_id': MODEL_ID, 'execution_id': plan.execution_id, 'output_locator': plan.output_locator,
            'argv': argv, 'binary': binary, 'parameters': parameters,
            'qm': [(a.atom_id, a.element, tuple(str(v) for v in a.coordinates_angstrom)) for a in plan.atoms],
            'field': [(r.atom_id, tuple(str(v) for v in r.coordinates_angstrom),
                       r.exact_charge.numerator, r.exact_charge.denominator) for r in plan.field_rows],
            'files': [(name, sha256(raw).hexdigest()) for name, raw in files]}


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
class XtbSinglePointPlanV2:
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
        if (type(self.execution_id) is not str or re.fullmatch(r'call-[0-9]{4,}', self.execution_id) is None
                or not all(_absolute_path(v) for v in (self.output_locator, self.executable_path, self.parameter_path))
                or type(self.atoms) is not tuple or not self.atoms
                or any(type(a) is not NativeAtomV1 for a in self.atoms)
                or type(self.field_rows) is not tuple
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
        payload = _request_identity_payload(self, BINARY_SHA256, PARAMETER_SHA256, argv, files)
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
class XtbSinglePointPlanV3(XtbSinglePointPlanV2):
    """Same scientific encoding with an explicit source-built stock identity."""
    selected_stock: SelectedXtbStockV1 = field(kw_only=True)

    def __post_init__(self):
        XtbSinglePointPlanV2.__post_init__(self)
        if type(self.selected_stock) is not SelectedXtbStockV1:
            raise ValueError('new-stock single point needs its exact typed source selection')
        self.selected_stock.__post_init__()
        executable, parameter, _, _, version = _stock_projection(self.selected_stock)
        if (self.executable_path, self.parameter_path) != (executable[0], parameter[0]):
            raise ValueError('new-stock single point substitutes its selected executable/parameter path')
        for name, value in (('binary_sha256', executable[2].sha256),
                            ('parameter_sha256', parameter[2].sha256),
                            ('release_tag', version[0]), ('runtime_build', version[1])):
            object.__setattr__(self, name, value)
        payload = _request_identity_payload(self, self.binary_sha256, self.parameter_sha256,
                                            self.program_argv, self.input_files)
        payload['selected_stock'] = self.selected_stock.identity.to_document()
        object.__setattr__(self, 'identity', sha256(json.dumps(
            payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest())


@dataclass(frozen=True, slots=True)
class XtbSinglePointCaptureV2:
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
                or type(self.execution_id) is not str or re.fullmatch(r'call-[0-9]{4,}', self.execution_id) is None
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
            if raw is not None and (type(raw) is not bytes):
                raise ValueError('complete original native output bytes required')
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
class XtbSinglePointObservationV2:
    plan: XtbSinglePointPlanV2
    capture: XtbSinglePointCaptureV2
    energy_hartree: Decimal = field(init=False)
    qm_gradient_native: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    pc_gradient_native: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    qm_gradient_ash: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    pc_gradient_ash: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    native_gradient_coordinates_bohr: tuple[tuple[Decimal, Decimal, Decimal], ...] = field(init=False)
    scc_iterations: int = field(init=False)

    def __post_init__(self):
        p, c = self.plan, self.capture
        if type(p) not in (XtbSinglePointPlanV2, XtbSinglePointPlanV3) or type(c) is not XtbSinglePointCaptureV2:
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
        if versions != [(p.release_tag, p.runtime_build)] or len(calls) != 1 or tuple(calls[0].split()) != p.program_argv:
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
    """Prospective ASH ABI; no callback/capture/atom count ceiling.

    The class name retains the existing coupling structural ABI; the selected
    module, MODEL_ID and V2 plan identity disclose this additive successor.
    Actual issue/entry/limits are never inferred from this adapter.
    """
    theorytype = 'QM'
    theorynamelabel = MODEL_ID
    analytic_hessian = False

    def __init__(self, *, executable_path, parameter_path, output_root, executor, retain_capture,
                 selected_stock=None):
        if (not all(_absolute_path(v) for v in (executable_path, parameter_path, output_root))
                or not callable(executor) or not callable(retain_capture)):
            raise ValueError('explicit selected paths, executor and custody hooks required')
        if selected_stock is not None:
            if type(selected_stock) is not SelectedXtbStockV1:
                raise ValueError('new-stock callback needs its typed source selection')
            selected_stock.__post_init__()
            executable, parameter, _, _, _ = _stock_projection(selected_stock)
            if (executable_path, parameter_path) != (executable[0], parameter[0]):
                raise ValueError('new-stock callback substitutes its selected executable/parameter path')
        self.selected_stock = selected_stock
        self.executable_path, self.parameter_path, self.output_root = executable_path, parameter_path, output_root
        self.executor, self.retain_capture = executor, retain_capture
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
            if not len(element_rows):
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
        name = f'call-{self.callback_reservations+1:04d}'
        operands = (name, str(PurePosixPath(self.output_root)/name), self.executable_path,
                    self.parameter_path, atoms, field_rows, charge, mult-1, PC)
        plan = (XtbSinglePointPlanV2(*operands) if self.selected_stock is None else
                XtbSinglePointPlanV3(*operands, selected_stock=self.selected_stock))
        # An attempted executor call consumes its reservation even if it refuses.
        self.callback_reservations += 1
        self.last_observation = None
        capture = self.executor(plan)
        self.retain_capture(plan, capture)
        observation = XtbSinglePointObservationV2(plan, capture)
        self.last_observation = observation
        if not Grad:
            return float(observation.energy_hartree)
        # Only selected gradient return needs NumPy, for ASH's array arithmetic.
        import numpy as np
        qm = np.asarray(observation.qm_gradient_ash, dtype=float)
        if PC:
            return float(observation.energy_hartree), qm, np.asarray(observation.pc_gradient_ash, dtype=float).reshape((-1, 3))
        return float(observation.energy_hartree), qm
