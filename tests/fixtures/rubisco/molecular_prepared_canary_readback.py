# SPDX-License-Identifier: MPL-2.0
"""Independent literal readback of the declared TP2 canary, never qualification.

Only Python standard-library arithmetic/parsing is used. All archive members
and all array bytes are consumed before returned operands are interpreted.
Neither producer science nor native molecular software is imported or rerun.
"""

import ast
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import PurePosixPath
import re
import struct
import zlib


CHUNK_BYTES = 1024 * 1024
RAW_MAGIC = b"EL-RUBISCO-NATIVE-FILES-1\n"
NATIVE_ANGSTROM_PER_BOHR = Fraction("0.52917726")
ASH_ANGSTROM_PER_BOHR = Fraction("0.5291772109303")


def record_value(document, schema, version="1.0.0"):
    if (type(document) is not dict or set(document) != {"schema", "value", "version"}
            or document["schema"] != schema or document["version"] != version or type(document["value"]) is not dict):
        raise ValueError("canary substitutes an exact nested canonical record/revision")
    return document["value"]


def _gunzip(chunks):
    reader = zlib.decompressobj(wbits=31)
    for chunk in chunks:
        pending = chunk
        while pending:
            block = reader.decompress(pending, CHUNK_BYTES)
            pending = reader.unconsumed_tail
            if reader.unused_data:
                raise ValueError("canary gzip contains undeclared trailing members")
            if block:
                yield block
    while True:
        block = reader.decompress(b"", CHUNK_BYTES)
        if not block:
            break
        yield block
    if not reader.eof or reader.unused_data:
        raise ValueError("canary gzip omits complete original bytes/trailer")


class _Reader:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.buffer = b""

    def take(self, count):
        while len(self.buffer) < count:
            block = next(self.chunks, None)
            if block is None:
                raise ValueError("canary archive is truncated")
            self.buffer += block
        value, self.buffer = self.buffer[:count], self.buffer[count:]
        return value

    def finish(self):
        if self.buffer or next(self.chunks, None) is not None:
            raise ValueError("canary archive appends undeclared bytes")


def authenticate_archive(chunks, census_bytes, subwork_id, selected_names):
    """Authenticate every member, keeping only the tiny consumer operands."""
    census = json.loads(census_bytes)
    if (census.get("schema") != "empirical-lawhood/rubisco-insilico-dynamics/durable-raw-file-census"
            or census.get("version") != "1.0.0"):
        raise ValueError("canary raw archive substitutes the completed census contract")
    files = census["value"]["files"]
    stream = _Reader(_gunzip(chunks))
    if stream.take(len(RAW_MAGIC)) != RAW_MAGIC:
        raise ValueError("canary raw archive substitutes complete native file framing")
    size = int.from_bytes(stream.take(8), "big")
    if size != len(census_bytes) or stream.take(size) != census_bytes:
        raise ValueError("canary raw archive changes its authenticated exact typed census")
    names, selected, total = [], {}, 0
    for row in files:
        row = record_value(row, "empirical-lawhood/rubisco-insilico-dynamics/file-evidence")
        path = PurePosixPath(row["relative_path"])
        if path.parts != (subwork_id, path.name) or path.name in names:
            raise ValueError("canary raw member substitutes its exact closed unit path")
        names.append(path.name)
        if type(row["byte_count"]) is not int or row["byte_count"] < 0:
            raise ValueError("canary raw census changes exact native file size")
        digest, remaining, kept = sha256(), row["byte_count"], []
        while remaining:
            block = stream.take(min(remaining, CHUNK_BYTES))
            digest.update(block)
            if path.name in selected_names:
                kept.append(block)
            remaining -= len(block)
        if digest.hexdigest() != row["sha256"]:
            raise ValueError("canary completed native bytes differ from exact full census")
        if path.name in selected_names:
            selected[path.name] = b"".join(kept)
        total += row["byte_count"]
    stream.finish()
    if set(selected) != set(selected_names):
        raise ValueError("canary archive omits declared consumer operands")
    return dict(files=selected, member_count=len(files), byte_count=total, names=tuple(names))


def _number(token):
    try:
        return Fraction(token.replace("D", "E").replace("d", "e"))
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("canary native operand is not a finite exact number") from error


def read_gradient(input_coord, native_gradient):
    coords = input_coord.decode("ascii").splitlines()
    returned = native_gradient.decode("ascii").splitlines()
    if len(coords) != 10 or coords[0] != "$coord" or coords[-1] != "$end":
        raise ValueError("canary needs all8 exact selected native coordinates")
    if len(returned) != 19 or returned[0] != "$grad" or returned[-1] != "$end":
        raise ValueError("canary needs full8/24 native gradient return")
    match = re.fullmatch(r"cycle\s*=\s*1\s+SCF energy\s*=\s*(\S+)\s+\|dE/dxyz\|\s*=\s*(\S+)", returned[1].strip())
    if match is None or _number(match[2]) < 0:
        raise ValueError("canary loses native energy/norm header")
    for actual, chosen, element in zip(returned[2:10], coords[1:-1], ("c", "c", "h", "h", "h", "h", "h", "h"), strict=True):
        a, b = actual.split(), chosen.split()
        if (len(a) != 4 or len(b) != 4 or a[3].lower() != element or b[3].lower() != element
                or any(abs(_number(a[axis]) - _number(b[axis])) > Fraction("0.0000000000000051") for axis in range(3))):
            raise ValueError("canary native coordinate/element order differs from full physical8")
    gradient = tuple(tuple(_number(token) for token in line.split()) for line in returned[10:18])
    if any(len(row) != 3 for row in gradient):
        raise ValueError("canary loses complete24 gradient components")
    return _number(match[1]), gradient


def authenticate_coordinate_input(input_coord, coordinate_hex):
    rows = input_coord.decode("ascii").splitlines()
    if len(rows) != 10 or rows[0] != "$coord" or rows[-1] != "$end" or len(coordinate_hex) != 8:
        raise ValueError("canary loses exact full8 coordinate input")
    for row, original in zip(rows[1:-1], coordinate_hex, strict=True):
        tokens = row.split()
        if len(tokens) != 4 or len(original) != 3:
            raise ValueError("canary input loses physical Cartesian denominator")
        for token, source in zip(tokens[:3], original, strict=True):
            expected = Fraction.from_float(float.fromhex(source)) / NATIVE_ANGSTROM_PER_BOHR
            # Native input serializes 18 significant decimal digits. Its final
            # half-ULP is derived from the declared exponent, not an E/G gate.
            decimal = re.fullmatch(r"[+-]?\d\.\d{17}E([+-]\d+)", token)
            if decimal is None:
                raise ValueError("canary input substitutes original native17E serialization")
            exponent = int(decimal[1]) - 17
            half_ulp = Fraction(10) ** exponent / 2
            if abs(_number(token) - expected) > half_ulp:
                raise ValueError("canary input changes exact original binary64/Bohr operands")


def read_array(chunks, capture, shape):
    """Authenticate the entire no-pickle NPY before numerical interpretation."""
    raw = b"".join(_gunzip(chunks))
    if (len(raw), sha256(raw).hexdigest()) != (capture["uncompressed_bytes"], capture["uncompressed_sha256"]):
        raise ValueError("canary array bytes differ from complete returned operand")
    if raw[:8] != b"\x93NUMPY\x02\x00":
        raise ValueError("canary array changes its no-pickle NPY2 encoding")
    header_size = int.from_bytes(raw[8:12], "little")
    header = ast.literal_eval(raw[12:12 + header_size].decode("latin1").strip())
    if (set(header) != {"descr", "fortran_order", "shape"} or header["descr"] not in ("<f8", ">f8")
            or header["fortran_order"] is not False or header["shape"] != shape
            or capture["shape"] != list(shape) or capture["npy_header_bytes"] != 12 + header_size):
        raise ValueError("canary array changes exact complete shape/dtype/header")
    count = math.prod(shape) if shape else 1
    payload = raw[12 + header_size:]
    endian = header["descr"][0]
    if len(payload) != count * 8:
        raise ValueError("canary array thins/appends the complete operand denominator")
    return payload, endian, dict(shape=shape, elements=count, bytes=len(raw), sha256=sha256(raw).hexdigest())


def compare_array(payload, endian, expected):
    if len(payload) != 8 * len(expected):
        raise ValueError("canary array/expected full denominator differs")
    if payload != b"".join(struct.pack(endian + "d", float(value)) for value in expected):
        raise ValueError("canary returned array changes independently read energy/gradient units or bits")


def authenticate_array(chunks, capture, shape, expected):
    payload, endian, report = read_array(chunks, capture, shape)
    compare_array(payload, endian, expected)
    return report


def read_amber(prmtop, inpcrd, pdb):
    """Full fixed-width table/census and coordinate readback; no parameter fitness claim."""
    lines = prmtop.decode("ascii").splitlines()
    if not lines or not lines[0].startswith("%VERSION"):
        raise ValueError("canary preparation lacks original Amber topology")
    tables, index = {}, 1
    while index < len(lines):
        if not lines[index].startswith("%FLAG "):
            raise ValueError("canary topology has unaccounted original lines")
        name = lines[index][6:].strip()
        if name in tables:
            raise ValueError("canary topology duplicates a full source table")
        index += 1
        while index < len(lines) and lines[index].startswith("%COMMENT"):
            index += 1
        fmt = re.fullmatch(r"%FORMAT\((\d+)([AaIiEeFfDd])(\d+)(?:\.(\d+))?\)", lines[index])
        if fmt is None:
            raise ValueError("canary topology has unsupported fixed-width native format")
        repeat, kind, width = int(fmt[1]), fmt[2].upper(), int(fmt[3])
        index += 1
        values = []
        while index < len(lines) and not lines[index].startswith("%FLAG "):
            row = lines[index]
            if len(row) > repeat * width:
                raise ValueError("canary topology appends undeclared columns")
            for offset in range(0, len(row), width):
                token = row[offset:offset + width].strip()
                if token:
                    values.append(token if kind == "A" else int(token) if kind == "I" else _number(token))
            index += 1
        tables[name] = tuple(values)
    pointers = tables.get("POINTERS", ())
    if len(pointers) != 31 or pointers[0] <= 0 or pointers[27] != 1:
        raise ValueError("canary preparation loses declared periodic complete atom census")
    count = pointers[0]
    for name in ("ATOM_NAME", "AMBER_ATOM_TYPE", "CHARGE", "MASS", "ATOM_TYPE_INDEX", "NUMBER_EXCLUDED_ATOMS"):
        if len(tables.get(name, ())) != count:
            raise ValueError("canary topology loses full atom table: " + name)
    if not {"ACE", "ALA", "GLY", "NME", "WAT"}.issubset(tables.get("RESIDUE_LABEL", ())):
        raise ValueError("canary topology substitutes tiny capped peptide/water roster")
    for name in ("RESIDUE_LABEL", "RESIDUE_POINTER"):
        if len(tables.get(name, ())) != pointers[11]:
            raise ValueError("canary topology changes complete residue denominator")
    coords = inpcrd.decode("ascii").splitlines()
    if len(coords) < 3 or coords[1].split() != [str(count)]:
        raise ValueError("canary inpcrd changes complete atom denominator")
    values = tuple(_number(line[offset:offset + 12].strip()) for line in coords[2:]
        for offset in range(0, len(line), 12) if line[offset:offset + 12].strip())
    if len(values) != 3 * count + 6 or any(value <= 0 for value in values[-6:]):
        raise ValueError("canary inpcrd loses complete coordinates/periodic box")
    atoms = tuple(row for row in pdb.decode("ascii").splitlines() if row[:6] in ("ATOM  ", "HETATM"))
    if len(atoms) != count:
        raise ValueError("canary PDB thins full prepared atoms")
    for index, row in enumerate(atoms):
        for axis in range(3):
            if abs(_number(row[30 + 8 * axis:38 + 8 * axis].strip()) - values[3 * index + axis]) > Fraction("0.0005001"):
                raise ValueError("canary PDB/inpcrd coordinates differ beyond printed precision")
    return dict(atom_count=count, coordinate_components=3 * count, residue_count=pointers[11],
        full_table_counts={name: len(values) for name, values in sorted(tables.items())},
        claim="COMPLETE_NATIVE_INTERFACE_READBACK_ONLY_NO_ASSIGNMENT_OR_CHEMICAL_QUALIFICATION")


def read_completed_control(reader, definitions, selected, request):
    """Read a closed genuine or exposed episode through existing receipt recovery.

Root authenticates process/host closure before invoking this receiver. Here
every selected/conditional receipt and raw member precedes tiny-domain math.
This function writes nothing and cannot create/contact/replay native subwork.
"""
    units = ("molecular.canary.energy-gradient", "molecular.canary.preparation")
    if tuple(row.subwork_id for row in definitions) != units:
        raise ValueError("canary receiver changes the complete selected2 denominator")
    parent = definitions[0].parent_contact
    expected = {"engine.metadata", "engine.launch", *units,
        *(name + ".call.000001" for name in units), *(name + ".call.000001.operand" for name in units)}
    all_definitions = {}
    for roster in reader.iter_rosters(parent):
        for definition in reader.iter_roster_definitions(parent, roster.roster_id):
            if definition.subwork_id in all_definitions:
                raise ValueError("canary receiver duplicates a conditional native definition")
            all_definitions[definition.subwork_id] = definition
    if set(all_definitions) != expected:
        raise ValueError("canary receiver loses/adds actual metadata/unit/call/operand census")
    if any(all_definitions[row.subwork_id] != row for row in definitions):
        raise ValueError("canary receiver replaces selected frozen unit definitions")
    before, archives, reports = {}, {}, []
    for name, definition in sorted(all_definitions.items()):
        receipt = reader.recover(definition)
        if receipt is None or receipt.completion.omitted_output_ids:
            raise ValueError("canary receiver has unknown/incomplete actual native return")
        before[name] = receipt
        outputs = {row.output_id for row in definition.outputs}
        if "files.raw" in outputs:
            typed = b"".join(reader.iter_completed_output(definition, "files.census", maximum_chunk_bytes=65536))
            names = ("input.coord", "gradient", "selected-command.json", "subprocess-return.json") if name == units[0] else (
                "model.prmtop", "model.inpcrd", "model.pdb", "selected-command.json", "subprocess-return.json", "tleap.in") if name == units[1] else ()
            archives[name] = authenticate_archive(reader.iter_completed_output(definition, "files.raw", maximum_chunk_bytes=65536), typed, name.split(".call.")[0], names)
            reports.append(dict(unit=name, members=archives[name]["member_count"], bytes=archives[name]["byte_count"]))
    eg = all_definitions[units[0]]
    capture = record_value(json.loads(b"".join(reader.iter_completed_output(eg, "raw.return"))), "empirical-lawhood/rubisco-coupled/raw-return")
    if (capture["request"] != json.loads(request.identity.canonical_bytes()) or capture["capture_failures"]
            or capture["native_disposition"] != "RETURNED" or capture["scientific_admission"] != "NOT_ATTEMPTED"):
        raise ValueError("canary receiver substitutes actual request or manufactures scientific admission")
    energy_capture = record_value(capture["energy"], "empirical-lawhood/rubisco-coupled/raw-array-capture")
    gradient_capture = record_value(capture["gradient"], "empirical-lawhood/rubisco-coupled/raw-array-capture")
    energy_bytes, energy_endian, energy_report = read_array(reader.iter_completed_output(eg, "raw.energy"), energy_capture, ())
    gradient_bytes, gradient_endian, gradient_report = read_array(reader.iter_completed_output(eg, "raw.gradient"), gradient_capture, (8, 3))
    # All actual native/raw-array bytes have authenticated. Only now interpret.
    files = archives[units[0]]["files"]
    authenticate_coordinate_input(files["input.coord"], selected.coordinates_angstrom_hex)
    energy, gradient = read_gradient(files["input.coord"], files["gradient"])
    compare_array(energy_bytes, energy_endian, (energy,))
    compare_array(gradient_bytes, gradient_endian, tuple(value * ASH_ANGSTROM_PER_BOHR / NATIVE_ANGSTROM_PER_BOHR for row in gradient for value in row))
    prepared = archives[units[1]]["files"]
    amber = read_amber(prepared["model.prmtop"], prepared["model.inpcrd"], prepared["model.pdb"])
    expected_script = "\n".join(("source leaprc.protein.ff14SB", "source leaprc.water.tip3p", "source leaprc.gaff2",
        "model = sequence { ACE ALA GLY ALA NME }", "check model", "solvateBox model TIP3PBOX 3.0", "check model",
        "saveAmberParm model model.prmtop model.inpcrd", "savePDB model model.pdb", "quit", "")).encode()
    if prepared["tleap.in"] != expected_script:
        raise ValueError("canary receiver substitutes selected capped peptide/3Angstrom TIP3P recipe")
    for name in units:
        definition = all_definitions[name]
        unit = record_value(json.loads(b"".join(reader.iter_completed_output(definition, "unit.return"))), "empirical-lawhood/rubisco-insilico-dynamics/durable-unit-return")
        call = all_definitions[name + ".call.000001"]
        if (not unit["known_return"] or not unit["preparation_succeeded"] or unit["reason_codes"]
                or unit["physical_independent_units"] != 0 or unit["plan"] != json.loads(selected.identity.canonical_bytes())
                or unit["native_calls"] != [json.loads(call.identity.canonical_bytes())]):
            raise ValueError("canary receiver replaces actual known return/native-call denominator")
        returned = record_value(json.loads(b"".join(reader.iter_completed_output(call, "call.return"))), "empirical-lawhood/rubisco-insilico-dynamics/native-call")
        if returned["termination"] != "COMPLETED" or returned["error_text"] is not None:
            raise ValueError("canary receiver lacks actual completed native command")
        command = json.loads(archives[name]["files"]["selected-command.json"])
        result = json.loads(archives[name]["files"]["subprocess-return.json"])
        if command["argv"] != result["argv"] or result["returncode"] != 0:
            raise ValueError("canary receiver substitutes original native argv/return")
        if name == units[0]:
            expected_argv = [selected.xtb_path, "input.coord", "--gfn", "2", "--vparam", selected.parameter_path,
                "--chrg", "0", "--uhf", "0", "--etemp", "300", "--acc", "0.05", "--iterations", "250",
                "--input", "xcontrol.inp", "--parallel", "1", "--norestart", "--verbose", "--grad"]
            expected_environment = dict(PATH="/usr/bin:/bin", LC_ALL="C", LANG="C", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
            if command != dict(argv=expected_argv, environment=expected_environment):
                raise ValueError("canary receiver changes exact selected E/G command/environment")
        else:
            from pathlib import Path
            amber_root = Path(selected.tleap_path).parent.parent
            expected_argv = [selected.tleap_path, *("-I" + str(amber_root / "dat/leap" / kind) for kind in ("prep", "lib", "parm", "cmd")), "-f", "tleap.in"]
            if command["argv"] != expected_argv or command["environment"]["AMBERHOME"] != str(amber_root):
                raise ValueError("canary receiver changes exact selected Amber search command")
    if any(reader.recover(all_definitions[name]) != receipt for name, receipt in before.items()):
        raise ValueError("canary receiver changed authentic original receipts during readback")
    return dict(claim="DEVELOPMENT_INTERFACE_ACCEPTANCE_ONLY_NOT_GP_OR_BACKEND_QUALIFICATION",
        mode=selected.mode, full_native_definition_count=len(all_definitions), actual_native_calls=2,
        physical_atom_count=8, complete_gradient_components=24, point_charge_count=0,
        full_raw_custody=reports, energy=energy_report, gradient=gradient_report, preparation=amber,
        actual_scientific_admission="NOT_ATTEMPTED", original_receipts_unchanged=True)
