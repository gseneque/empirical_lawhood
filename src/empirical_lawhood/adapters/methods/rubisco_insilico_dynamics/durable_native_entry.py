# SPDX-License-Identifier: MPL-2.0
"""Additive selected child entry; scientific imports occur only after authentication."""

from hashlib import sha256
import importlib.abc
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys


TLEAP_SEARCH_KINDS = ("prep", "lib", "parm", "cmd")


def selected_tleap_command(plan):
    """Use the selected stock wrapper's explicit search paths with its raw binary."""
    root = Path(plan.tleap_path).parent.parent
    return (plan.tleap_path, *("-I" + str(root / "dat/leap" / kind) for kind in TLEAP_SEARCH_KINDS),
            "-f", "tleap.in")


def authenticate_tleap_search_stock(plan, inventory):
    """Bind the entire actual search census; added unselected files cannot be loaded."""
    import os
    from .durable_preparation import file_chunks

    binary = Path(plan.tleap_path)
    if (binary.parent.parent.parent != Path(inventory["selected_engine_root"])
            or not any(row["kind"] == "file" and row["actual_path"] == str(binary)
                       and row["sha256"] == plan.tleap_sha256 for row in inventory["entries"])):
        raise ValueError("selected teLeap search root or executable escapes authenticated stock")
    selected = []
    for kind in TLEAP_SEARCH_KINDS:
        directory = binary.parent.parent / "dat/leap" / kind
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("selected teLeap search directory is missing or substituted")
        expected = {row["actual_path"]: row for row in inventory["entries"]
                    if Path(row["actual_path"]).is_relative_to(directory)}
        actual = {str(path) for path in directory.rglob("*") if path.is_symlink() or not path.is_dir()}
        if not expected or actual != set(expected):
            raise ValueError("selected teLeap search stock changes its complete file census")
        for name, row in sorted(expected.items()):
            path = Path(name)
            if row["kind"] == "file":
                if path.is_symlink():
                    raise ValueError("selected teLeap search stock substitutes a regular file with a link")
                size, digest = 0, sha256()
                for block in file_chunks(path):
                    size += len(block)
                    digest.update(block)
                if (size, digest.hexdigest()) != (row["size"], row["sha256"]):
                    raise ValueError("selected teLeap search stock changes authenticated file bytes")
            elif (row["kind"] != "symlink" or not path.is_symlink()
                  or os.readlink(path) != row["target"] or not path.resolve().is_relative_to(directory)):
                raise ValueError("selected teLeap search stock changes or escapes an authenticated link")
            selected.append(row)
    required = {str(binary.parent.parent / "dat/leap/cmd" / name)
                for name in ("leaprc.protein.ff14SB", "leaprc.water.tip3p", "leaprc.gaff2")}
    if not required.issubset({row["actual_path"] for row in selected if row["kind"] == "file"}):
        raise ValueError("selected teLeap search stock lacks the requested force-field commands")
    return tuple(selected)


def selected_tleap_environment(plan, temporary):
    """Only selected process/scientific settings; never persist inherited secrets."""
    binary = Path(plan.tleap_path)
    result = dict(AMBERHOME=str(binary.parent.parent),
        LD_LIBRARY_PATH=str(binary.parents[2] / "ambertools-runtime-libraries/lib"),
        PATH=str(binary.parent) + ":/usr/bin:/bin", LC_ALL="C", LANG="C",
        TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary))
    result.update({name: "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
        "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})
    return result


def refuse_external_network(log_path):
    """Selected child audit hook refuses implicit acquisition before socket effects."""
    def guard(event, arguments):
        if event in ("socket.connect", "socket.getaddrinfo", "socket.bind", "socket.sendto"):
            # Record the attempted operation, without addresses/credential values.
            if log_path is not None:
                with Path(log_path).open("a") as log:
                    log.write(json.dumps({"event": event, "refused_before_effect": True}, sort_keys=True) + "\n")
            raise PermissionError("selected molecular preparation forbids implicit external network contact")
    sys.addaudithook(guard)


def authenticate_loaded_engine_modules(inventory):
    """Actual imported scientific files must belong to selected complete engine stock."""
    selected = {str(Path(row["actual_path"]).resolve()): row for row in inventory["entries"]
                if row["kind"] == "file"}
    result = []
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    for name, module in sorted(sys.modules.items()):
        if name.split(".")[0] not in {"numpy", "scipy", "openmm", "pdbfixer", "parmed"}:
            continue
        origin = getattr(module, "__file__", None)
        if origin is None:
            continue
        path = Path(origin).resolve()
        row = selected.get(str(path))
        if row is None:
            raise ValueError("actual imported molecular module escapes selected engine stock: " + name)
        size, digest = bounded_file_sha256(path, maximum_bytes=row["size"])
        if size != row["size"] or digest != row["sha256"]:
            raise ValueError("actual imported molecular module changed selected bytes: " + name)
        result.append(dict(module=name, path=str(path), size_bytes=row["size"], sha256=digest))
    return result


def authenticate_engine_stock(stock):
    """Consume every original selected file/link before importing helper science."""
    import os
    from .durable_preparation import file_chunks

    inventory = json.loads(stock["source.engine-inventory"])
    for row in inventory["entries"]:
        path = Path(row["actual_path"])
        if row["kind"] == "file":
            size, digest = 0, sha256()
            for block in file_chunks(path):
                size += len(block)
                digest.update(block)
            if size != row["size"] or digest.hexdigest() != row["sha256"]:
                raise ValueError("selected native engine member changed: " + row["path"])
        elif row["kind"] != "symlink" or not path.is_symlink() or os.readlink(path) != row["target"]:
            raise ValueError("selected native engine link changed: " + row["path"])
    return inventory


class _SelectedSourceLoader(importlib.machinery.SourceFileLoader):
    def __init__(self, fullname, path, digest):
        super().__init__(fullname, str(path))
        self.digest = digest

    def get_code(self, fullname):
        from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
        path = Path(self.path)
        raw = read_bounded_bytes(path, maximum_bytes=path.stat().st_size)
        if sha256(raw).hexdigest() != self.digest:
            raise ValueError("selected molecular helper source bytes changed before import")
        return compile(raw, self.path, "exec", dont_inherit=True)


class _SelectedSourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root, bindings):
        self.root, self.bindings = Path(root), dict(bindings)

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith("empirical_lawhood."):
            return None
        relative = "src/" + fullname.replace(".", "/")
        for suffix in (".py", "/__init__.py"):
            selected = relative + suffix
            names = tuple(name for name in (selected, selected.removeprefix("src/empirical_lawhood/"))
                if name in self.bindings)
            if len(names) > 1:
                raise ValueError("molecular helper source has aliased scientific inventory labels")
            if names:
                loader = _SelectedSourceLoader(fullname, self.root / selected, self.bindings[names[0]])
                return importlib.util.spec_from_loader(fullname, loader, is_package=suffix.startswith("/"))
        raise ValueError("molecular child import is outside authenticated selected source census: " + fullname)


def selected_child(progress, invocation):
    """Consume one sealed invocation; retain all known unit outcomes before guards."""
    raw = invocation.read()
    data = json.loads(raw)
    if set(data) != {"plan", "source", "nomination", "inventory", "coordinates", "definitions", "source_root"}:
        raise ValueError("durable molecular invocation changes complete selected operand census")
    plan_data = json.loads(data["plan"])
    finder = _SelectedSourceFinder(data["source_root"], plan_data["value"]["code_sources"])
    sys.meta_path.insert(0, finder)
    try:
        _authenticated_child(progress, data, invocation.prepared_invocation)
    finally:
        sys.meta_path.remove(finder)


def _prepare_child(data, parent, prepared_contract=None):
    """Original scientific/stock checks, with no progress or native calls."""
    import os
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import AssemblyCoordinates, StructuralInventory
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
    from . import contracts as historical, science
    from .durable_contracts import DurablePreparationPlan
    from .durable_preparation import file_chunks

    def decode(value, kind):
        selected = value.encode()
        return decode_canonical_bytes(selected, kind, maximum_bytes=len(selected))

    plan = decode(data["plan"], DurablePreparationPlan)
    source = decode(data["source"], historical.PreparationSelection)
    nomination = decode(data["nomination"], NominationDossier)
    inventory = decode(data["inventory"], StructuralInventory)
    coordinates = decode(data["coordinates"], AssemblyCoordinates)
    selected = tuple(decode(row, NativeSubworkDefinition) for row in data["definitions"])
    if ((plan.source, plan.nomination, plan.inventory, plan.coordinates)
            != tuple(historical.identity(row) for row in (source, nomination, inventory, coordinates))
            or plan.workdir != source.native_workdir
            or plan.engine_inventory_sha256 != source.engine_inventory_sha256
            or any(row.configuration != plan.identity or row.parent_contact != parent for row in selected)):
        raise ValueError("molecular child substitutes actual source/configuration/parent operands")
    from .durable_roster import definitions
    if (len(selected) != 37 or selected != definitions(plan, parent,
            sources=selected[0].sources, input_materialization_ids=selected[0].input_materialization_ids,
            implementation=None if prepared_contract is None else prepared_contract.implementation,
            source_root=data["source_root"])):
        raise ValueError("molecular child changes its complete original 12/24/metadata roster")
    science.validate_source(source, nomination, inventory, coordinates)
    stock = science.validate_stock(source.source_members)
    engine_inventory = authenticate_engine_stock(stock)
    tleap_search_stock = authenticate_tleap_search_stock(plan, engine_inventory)
    # Both exact executables must be selected stock, not an unverified replacement.
    for path, digest in ((plan.interpreter_path, plan.interpreter_sha256), (plan.tleap_path, plan.tleap_sha256)):
        expected = [row for row in engine_inventory["entries"] if row["kind"] == "file"
                    and row["sha256"] == digest]
        if not expected:
            raise ValueError("selected molecular executable is absent from authenticated full engine stock")
        actual = sha256()
        for block in file_chunks(Path(path).resolve()):
            actual.update(block)
        if actual.hexdigest() != digest:
            raise ValueError("selected molecular executable bytes changed")
    if sha256(Path(data["source_root"]).joinpath("uv.lock").read_bytes()).hexdigest() != plan.dependency_lock_sha256:
        raise ValueError("molecular child selected dependency lock changed")
    if not all(os.environ.get(name) == "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")):
        raise ValueError("molecular child changed CPU/one-thread environment")
    return plan, source, nomination, inventory, coordinates, selected, stock, engine_inventory, tleap_search_stock


def _prepared_embedded_work(prepared_contract, expected_parent, plan, selected, records,
                            *, scientific_unit_ids=None, native_effect_slot_ids=None, record_identities=None):
    """Join embedded canonical bytes to the retained outer input lineage."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork
    from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
    work = prepared_contract.native_work
    if (work is None or expected_parent != prepared_contract.expected_parent_contact
            or work.definitions != selected
            or tuple(row.input_materialization_ids for row in selected)
                != (expected_parent.input_materialization_ids,) * len(selected)):
        raise ValueError("specialist changes its full original parent/materialization/native census")
    original_records = (plan, *records)
    if record_identities is not None and len(record_identities) != len(original_records):
        raise ValueError("specialist changes its explicit original record/lineage census")
    for index, record in enumerate(original_records):
        identity = None if record_identities is None else record_identities[index]
        if identity is not None and (identity.object_schema, identity.object_version, identity.object_fingerprint) != (
                record.SCHEMA, record.VERSION, record.fingerprint()):
            raise ValueError("specialist substitutes its exact original lineage identity/record bytes")
        matched = tuple(row for row in prepared_contract.inputs
            if (row.logical.payload_schema, row.logical.content_sha256)
                == (record.SCHEMA, record.fingerprint())
                and (identity is None or row.artifact_id == identity.object_id))
        if len(matched) != 1:
            raise ValueError("specialist embedded original record lacks unique outer authenticated lineage")
    return PreparedNativeWork(expected_parent,
        work.scientific_unit_ids if scientific_unit_ids is None else scientific_unit_ids,
        work.native_effect_slot_ids if native_effect_slot_ids is None else native_effect_slot_ids,
        selected, (NativeSubworkRoster("selected.native-subwork", expected_parent,
            tuple(row.identity for row in selected)),), work.isolated_selection, work.isolated_environment,
        work.isolated_diagnostics)


def preflight_selected_child(*, invocation, expected_parent, prepared_contract):
    """Inspect the actual selected engine and exact original operands, no science."""
    from types import SimpleNamespace
    data = json.loads(invocation.read())
    if set(data) != {"plan", "source", "nomination", "inventory", "coordinates", "definitions", "source_root"}:
        raise ValueError("durable molecular invocation changes complete selected operand census")
    finder = _SelectedSourceFinder(data["source_root"], json.loads(data["plan"])["value"]["code_sources"])
    sys.meta_path.insert(0, finder)
    try:
        plan, source, nomination, inventory, coordinates, selected, _, engine_inventory, _ = _prepare_child(data, expected_parent, prepared_contract)
        from . import contracts as historical
        from .durable_recursive_translation import native_effect_slot_ids
        work = _prepared_embedded_work(prepared_contract, expected_parent, plan, selected,
            (source, nomination, inventory, coordinates), scientific_unit_ids=(historical.UNIT,),
            native_effect_slot_ids=native_effect_slot_ids(SimpleNamespace(plan=plan, source=source)))
        refuse_external_network(None)
        for name in ("numpy", "scipy", "openmm", "parmed", "pdbfixer"):
            importlib.import_module(name)
        authenticate_loaded_engine_modules(engine_inventory)
        return work
    finally:
        sys.meta_path.remove(finder)


def _authenticated_child(progress, data, prepared_contract=None):
    from io import StringIO
    import subprocess
    import traceback

    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    from .durable_contracts import geometry_id, model_id
    from .durable_instrumentation import instrument_completion, selected_fixer_factory
    from .durable_preparation import DurableCallLedger, complete_unit, copy_completed_geometry
    from .durable_roster import freeze
    from .parameter_audit import assigned_parameter_inventory, realized_atom_origins_from_coordinates
    from .preparation import scoped_boundary_stock, scoped_kcx_stock

    plan, source, nomination, inventory, coordinates, selected, stock, engine_inventory, tleap_search_stock = _prepare_child(data, progress.parent_contact, prepared_contract)
    freeze(progress, selected)
    refuse_external_network(Path(plan.workdir) / "launcher/network-refusals.jsonl")
    # Explicit molecular/helper imports follow complete stock/source/executable
    # authentication. Framework array modules may already be loaded by the
    # shared bridge; every actual loaded molecular module is checked below.
    from . import native
    import numpy as np
    import openmm as mm
    from openmm import app, unit
    from parmed.amber import AmberParameterSet, AmberParm
    from pdbfixer import PDBFixer

    root = Path(plan.workdir)
    native._json(root / "launcher/loaded-engine-modules.json", authenticate_loaded_engine_modules(engine_inventory))
    temporary = root / "temporary"
    temporary.mkdir()
    by_id = {row.subwork_id: row for row in selected}
    base = AmberParameterSet()
    base.load_parameters(StringIO(stock["source.parm10-dat"]))
    base.load_parameters(StringIO(stock["source.ff14sb-frcmod"]))
    custom = scoped_kcx_stock(stock["source.kcx-prepin"], stock["source.kcx-frcmod"], existing_atom_types=base.atom_types)
    boundaries = scoped_boundary_stock(stock["source.parm10-dat"], stock["source.ff14sb-frcmod"])
    for construct_id, view in plan.geometry_census:
        definition = by_id[geometry_id(construct_id, view)]
        if definition.subwork_id not in plan.attempted_geometry_ids:
            continue
        if progress.inspect(definition).state is NativeSubworkState.COMPLETED:
            progress.recover(definition)
            continue
        # Existing UNKNOWN is refused by begin; no guessed restart or native replay.
        entry = progress.begin(definition)
        progress.contact(entry)
        directory = root / definition.subwork_id
        directory.mkdir()
        ledger = DurableCallLedger(progress, plan, root, entry, directory)
        error = None
        original_instrumentation = native.instrument_completion
        native.instrument_completion = instrument_completion
        try:
            construct = next(row for row in source.constructs if row.construct_id == construct_id)
            native._complete(source, inventory, construct, view, directory, ledger, mm, app, unit, np,
                             selected_fixer_factory(PDBFixer, ledger, directory, app))
        except Exception:
            error = traceback.format_exc()
            (directory / "technical-failure.txt").write_text(error)
        finally:
            native.instrument_completion = original_instrumentation
        complete_unit(progress, plan, entry, root, directory, ledger, succeeded=error is None, error=error)

    for construct_id, view, parameters in plan.model_census:
        definition = by_id[model_id(construct_id, view, parameters)]
        if definition.subwork_id not in plan.attempted_model_ids:
            continue
        if progress.inspect(definition).state is NativeSubworkState.COMPLETED:
            progress.recover(definition)
            continue
        entry = progress.begin(definition)
        progress.contact(entry)
        directory = root / definition.subwork_id
        directory.mkdir()
        ledger = DurableCallLedger(progress, plan, root, entry, directory)
        geometry = by_id[geometry_id(construct_id, view)]
        geometry_receipt, error = None, None
        try:
            geometry_receipt = copy_completed_geometry(progress, geometry, directory)
            for filename, member in (("kcx.prepin", "source.kcx-prepin"), ("kcx.frcmod", "source.kcx-frcmod"),
                                     ("cabp.prepi", "source.cabp-prepi"), ("cabp.frcmod", "source.cabp-frcmod")):
                (directory / filename).write_text(stock[member])
            (directory / "kcx-scoped.prepin").write_text(custom.scoped_prepi_utf8)
            (directory / "kcx-scoped.frcmod").write_text(custom.scoped_custom_frcmod_utf8)
            (directory / "kcx-boundaries.frcmod").write_text(boundaries.scoped_boundary_frcmod_utf8)
            origin_path = directory / "atom-origin-provenance.json"
            origin = json.loads(origin_path.read_text())
            (directory / "tleap.in").write_text(native._leap_script(parameters, origin))
            environment = selected_tleap_environment(plan, temporary)
            command = selected_tleap_command(plan)

            def execute():
                with (directory / "tleap.stdout.log").open("xb") as stdout, (directory / "tleap.stderr.log").open("xb") as stderr:
                    return subprocess.run(command, cwd=directory,
                        env=environment, stdout=stdout, stderr=stderr, check=False)

            returned = ledger.call("ambertools.tleap", dict(
                command=command, executable_sha256=plan.tleap_sha256,
                engine_inventory_sha256=plan.engine_inventory_sha256, search_stock=tleap_search_stock,
                environment=environment, cwd=str(directory), chemical_state=source.chemical_state,
                parameter_view=parameters, geometry_definition=json.loads(geometry.identity.canonical_bytes())["value"],
                geometry_receipt=json.loads(geometry_receipt.canonical_bytes())["value"]), execute,
                realization=lambda result: dict(returncode=result.returncode))
            # Every raw file/log/return and its complete receipt already exists.
            if returned.returncode != 0 or not all((directory / name).is_file() for name in ("model.prmtop", "model.inpcrd")):
                raise RuntimeError("known teLeap adverse return or missing full parameter/coordinate output")
            structure = ledger.call("ambertools.parameter-load", dict(
                prmtop=native._evidence_dict(directory / "model.prmtop", root),
                inpcrd=native._evidence_dict(directory / "model.inpcrd", root)),
                lambda: AmberParm(str(directory / "model.prmtop"), str(directory / "model.inpcrd")))
            audit = assigned_parameter_inventory(structure)
            origin["amber_realization"] = realized_atom_origins_from_coordinates(
                structure, origin, (directory / "complete-heavy.pdb").read_text(),
                (directory / "model.inpcrd").read_text())
            native._json(origin_path, origin)
            native._json(directory / "complete-assigned-parameters.json", audit)
        except Exception:
            error = traceback.format_exc()
            (directory / "technical-failure.txt").write_text(error)
        complete_unit(progress, plan, entry, root, directory, ledger, succeeded=error is None, error=error,
            geometry=geometry.identity if geometry_receipt is not None else None, geometry_receipt=geometry_receipt)
    # A full known adverse census is still valuable; no model success implies qualification.
    (root / "child-known-census.txt").write_text(
        f"Frozen12/24 census; selected attempts {len(plan.attempted_geometry_ids)} geometries/"
        f"{len(plan.attempted_model_ids)} models; independent physics unqualified\n")
