# SPDX-License-Identifier: MPL-2.0
"""Declared molecular interface controls for TP2; never Gp qualification.

The root selects actual native entry. Exposed executable doubles use the same
domain commands, custody and array publication. This module is frozen as a
selected child, through the existing isolated runner; it adds no launcher.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import traceback
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_native_entry import (
    authenticate_engine_stock, authenticate_loaded_engine_modules, authenticate_tleap_search_stock,
    selected_tleap_command, selected_tleap_environment,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import (
    DurableCallLedger, complete_unit, file_chunks,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import prospective_xtb as xtb
from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import raw_coupled_return as raw


TLEAP_SCRIPT = "\n".join(("source leaprc.protein.ff14SB", "source leaprc.water.tip3p",
    "source leaprc.gaff2", "model = sequence { ACE ALA GLY ALA NME }", "check model",
    "solvateBox model TIP3PBOX 3.0", "check model", "saveAmberParm model model.prmtop model.inpcrd",
    "savePDB model model.pdb", "quit", ""))


@dataclass(frozen=True, slots=True)
class MolecularPreparedCanarySelection(CanonicalRecord):
    """Closed tiny development protocol, with explicit real/exposed stock."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/development/molecular-prepared-canary"
    config_id: str
    workdir: str
    mode: str
    tleap_path: str
    tleap_sha256: str
    xtb_path: str
    xtb_sha256: str
    parameter_path: str
    parameter_sha256: str
    engine_inventory_path: str
    engine_inventory_sha256: str
    coordinates_angstrom_hex: tuple[tuple[str, str, str], ...]
    input_origin_path: str
    input_origin_sha256: str
    source_root: str
    code_sources: tuple[tuple[str, str], ...]
    dependency_lock_sha256: str
    scientific_claim: str = "DEVELOPMENT_INTERFACE_ACCEPTANCE_ONLY_NOT_GP_OR_BACKEND_QUALIFICATION"
    elements: tuple[str, ...] = ("C", "C", "H", "H", "H", "H", "H", "H")
    gradient_component_denominator: int = 24
    point_charge_count: int = 0
    formal_charge: int = 0
    unpaired_electrons: int = 0

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.mode not in ("ACTUAL_INTERFACE_CANARY", "EXPOSED_EXECUTABLE_DOUBLE"):
            raise ValueError("canary needs an explicit selected actual/exposed native route")
        for name in ("workdir", "tleap_path", "xtb_path", "parameter_path", "engine_inventory_path", "input_origin_path", "source_root"):
            path = Path(getattr(self, name))
            if not path.is_absolute() or ".." in path.parts:
                raise ValueError("canary requires selected absolute source/output paths")
        for name in ("tleap_sha256", "xtb_sha256", "parameter_sha256", "engine_inventory_sha256", "input_origin_sha256", "dependency_lock_sha256"):
            validate_sha256(getattr(self, name))
        if (self.elements != ("C", "C", "H", "H", "H", "H", "H", "H")
                or type(self.coordinates_angstrom_hex) is not tuple or len(self.coordinates_angstrom_hex) != 8
                or any(type(row) is not tuple or len(row) != 3 for row in self.coordinates_angstrom_hex)
                or any(type(getattr(self, name)) is not int for name in ("gradient_component_denominator", "point_charge_count", "formal_charge", "unpaired_electrons"))
                or self.gradient_component_denominator != 24 or self.point_charge_count != 0
                or self.formal_charge != 0 or self.unpaired_electrons != 0
                or self.scientific_claim != "DEVELOPMENT_INTERFACE_ACCEPTANCE_ONLY_NOT_GP_OR_BACKEND_QUALIFICATION"):
            raise ValueError("canary changes its whole unembedded8/24 denominator or scope")
        for row in self.coordinates_angstrom_hex:
            for token in row:
                if type(token) is not str or not Decimal.from_float(float.fromhex(token)).is_finite():
                    raise ValueError("canary loses exact finite original binary64 coordinate operands")
        if not self.code_sources or tuple(name for name, _ in self.code_sources) != tuple(sorted(set(name for name, _ in self.code_sources))):
            raise ValueError("canary omits complete selected source closure")
        for name, digest in self.code_sources:
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError("canary source closure escapes selected cache")
            validate_sha256(digest)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


def _decode(value, kind):
    data = value.encode()
    return decode_canonical_bytes(data, kind, maximum_bytes=len(data))


def _authenticate(path, digest):
    observed = sha256()
    for chunk in file_chunks(path):
        observed.update(chunk)
    if observed.hexdigest() != digest:
        raise ValueError("molecular canary selected source/native bytes changed: " + str(path))


def _immutable(path, value):
    with Path(path).open("xb") as stream:
        stream.write(value)


def _native_command(argv, directory, environment):
    """One actual selected subprocess; entire native file return precedes guards."""
    _immutable(directory / "selected-command.json", json.dumps({"argv": argv, "environment": environment}, sort_keys=True).encode() + b"\n")
    with (directory / "stdout.bin").open("xb") as stdout, (directory / "stderr.bin").open("xb") as stderr:
        result = subprocess.run(argv, cwd=directory, env=environment, stdin=subprocess.DEVNULL,
            stdout=stdout, stderr=stderr, check=False)
    _immutable(directory / "selected-argv.json", json.dumps({"argv": argv}, sort_keys=True).encode() + b"\n")
    _immutable(directory / "subprocess-return.json", json.dumps({"argv": argv, "returncode": result.returncode}, sort_keys=True).encode() + b"\n")
    if result.returncode != 0:
        raise RuntimeError("selected canary native command returned " + str(result.returncode))
    return result


def exposed_child(progress, invocation):
    """Real selected IPC child; root separately owns actual canary entry."""
    data = json.loads(invocation.read())
    if set(data) != {"definitions", "selection", "request", "provenance", "phase"}:
        raise ValueError("molecular canary invocation changes its complete operand census")
    selected = _decode(data["selection"], MolecularPreparedCanarySelection)
    request = _decode(data["request"], raw.CoupledEvaluationRequest)
    provenance = _decode(data["provenance"], NumericalProducingProvenance)
    definitions = tuple(_decode(value, NativeSubworkDefinition) for value in data["definitions"])
    if (tuple(row.subwork_id for row in definitions) != ("molecular.canary.energy-gradient", "molecular.canary.preparation")
            or data["phase"] not in ("success", "after-completion")
            or any(row.code_sources_sha256 != provenance.code_sources_sha256
                or row.dependency_lock_sha256 != selected.dependency_lock_sha256 for row in definitions)
            or provenance.package_sources != selected.code_sources
            or provenance.dependency_lock_sha256 != selected.dependency_lock_sha256
            or request.protocol != selected.identity or request.prepared_material != selected.identity
            or request.physical_coordinates != selected.identity or request.producing_provenance != provenance.identity
            or request.physical_atom_count != 8):
        raise ValueError("molecular canary changes actual source/provenance/native denominators")
    for name, digest in selected.code_sources:
        _authenticate(Path(selected.source_root) / name, digest)
    _authenticate(Path(selected.source_root) / "uv.lock", selected.dependency_lock_sha256)
    inventory_bytes = Path(selected.engine_inventory_path).read_bytes()
    _authenticate(selected.engine_inventory_path, selected.engine_inventory_sha256)
    _authenticate(selected.input_origin_path, selected.input_origin_sha256)
    origin = json.loads(Path(selected.input_origin_path).read_bytes())
    coordinate_tokens = origin.get("value", origin).get("coordinates_angstrom_hex")
    if coordinate_tokens is None or tuple(tuple(row) for row in coordinate_tokens) != selected.coordinates_angstrom_hex:
        raise ValueError("canary substitutes the authenticated original whole8 coordinate operands")
    inventory = json.loads(inventory_bytes)
    if selected.mode == "ACTUAL_INTERFACE_CANARY":
        inventory = authenticate_engine_stock({"source.engine-inventory": inventory_bytes})
        if selected.xtb_sha256 != xtb.BINARY_SHA256 or selected.parameter_sha256 != xtb.PARAMETER_SHA256:
            raise ValueError("actual canary substitutes selected native xTB binary/parameters")
    for path, digest in ((selected.tleap_path, selected.tleap_sha256), (selected.xtb_path, selected.xtb_sha256),
            (selected.parameter_path, selected.parameter_sha256)):
        _authenticate(path, digest)
    authenticate_tleap_search_stock(selected, inventory)
    root = Path(selected.workdir)
    if root.exists():
        raise ValueError("canary requires fresh working outputs; completed native work is never replayed")
    root.mkdir()
    by_id = {row.subwork_id: row for row in definitions}
    definition = by_id["molecular.canary.preparation"]
    if definition.configuration != selected.identity:
        raise ValueError("preparation canary substitutes selected entered configuration")
    entry = progress.begin(definition)
    progress.contact(entry)
    directory = root / definition.subwork_id
    directory.mkdir()
    _immutable(directory / "tleap.in", TLEAP_SCRIPT.encode())
    temporary = directory / "temporary"
    temporary.mkdir()
    ledger = DurableCallLedger(progress, selected, root, entry, directory)
    argv = selected_tleap_command(selected)
    environment = selected_tleap_environment(selected, temporary)
    # Temporary directory is selected outside the flat raw file census.
    temporary.rmdir()
    environment.update(TMPDIR=str(root), TMP=str(root), TEMP=str(root))
    try:
        ledger.call("canary.tleap-preparation", {"argv": argv, "script_sha256": sha256(TLEAP_SCRIPT.encode()).hexdigest()},
            lambda: _native_command(argv, directory, environment),
            realization=lambda result: {"returncode": result.returncode, "argv": result.args})
    except Exception:
        complete_unit(progress, selected, entry, root, directory, ledger, succeeded=False, error=traceback.format_exc())
        raise
    complete_unit(progress, selected, entry, root, directory, ledger, succeeded=True)

    definition = by_id["molecular.canary.energy-gradient"]
    if definition.configuration != request.identity:
        raise ValueError("E/G canary substitutes actual entered request")
    entry = progress.begin(definition)
    progress.contact(entry)
    directory = root / definition.subwork_id
    directory.mkdir()
    atoms = tuple(xtb.NativeAtomV1("qm-" + str(index).zfill(4), element,
        tuple(Decimal.from_float(float.fromhex(token)) for token in coords))
        for index, (element, coords) in enumerate(zip(selected.elements, selected.coordinates_angstrom_hex, strict=True), 1))
    plan = xtb.XtbSinglePointPlanV2("call-0001", str(directory), selected.xtb_path, selected.parameter_path,
        atoms, (), 0, 0, False)
    for name, payload in plan.input_files:
        _immutable(directory / name, payload)
    ledger = DurableCallLedger(progress, selected, root, entry, directory)
    try:
        ledger.call("canary.xtb-energy-gradient", {"argv": plan.program_argv, "plan_identity": plan.identity},
            lambda: _native_command(plan.program_argv, directory, dict(PATH="/usr/bin:/bin", LC_ALL="C", LANG="C",
                OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")),
            realization=lambda result: {"returncode": result.returncode, "argv": result.args})
        # Full exact native gradient/stdout/stderr are already in completed custody.
        energy, _, gradient, _ = xtb.parse_gradient((directory / "gradient").read_bytes(), atoms)
        import numpy as np
        if selected.mode == "ACTUAL_INTERFACE_CANARY":
            loaded = authenticate_loaded_engine_modules(inventory)
            _immutable(directory / "loaded-engine-modules.json", json.dumps(loaded, sort_keys=True).encode() + b"\n")
        capture = raw.capture_native_return(request, float(energy), np.asarray(tuple(tuple(
            float(xtb.native_gradient_to_ash(value)) for value in row) for row in gradient), dtype=np.float64), progress, entry)
        if capture.capture_failures:
            raise ValueError("canary has a retained full native return but unsupported array capture")
    except Exception:
        complete_unit(progress, selected, entry, root, directory, ledger, succeeded=False, error=traceback.format_exc())
        raise
    complete_unit(progress, selected, entry, root, directory, ledger, succeeded=True)
    if data["phase"] == "after-completion":
        os._exit(95)


