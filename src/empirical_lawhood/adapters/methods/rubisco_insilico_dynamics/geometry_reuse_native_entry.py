# SPDX-License-Identifier: MPL-2.0
"""Selected fresh Amber models from authentic independently assessed geometry.

The isolated child never invokes geometry construction. Original geometry and
its adverse sibling models retain their original identities and whole custody.
"""

from hashlib import sha256
import json
from pathlib import Path
import sys


def selected_child(progress, invocation):
    from .durable_native_entry import _SelectedSourceFinder

    data = json.loads(invocation.read())
    if set(data) != {"plan", "source", "nomination", "inventory", "coordinates", "definitions",
                     "source_root", "supplies", "assessments"}:
        raise ValueError("fresh model invocation changes complete selected original operand census")
    plan_data = json.loads(data["plan"])
    finder = _SelectedSourceFinder(data["source_root"], plan_data["value"]["code_sources"])
    sys.meta_path.insert(0, finder)
    try:
        _authenticated_child(progress, data, invocation.prepared_invocation)
    finally:
        sys.meta_path.remove(finder)


def _prepare_child(data, parent, prepared_contract=None):
    """Authenticate original geometry, source and stock without entering work."""
    import os

    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import AssemblyCoordinates, StructuralInventory
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
    from . import contracts as c, science
    from .durable_native_entry import (
        authenticate_engine_stock, authenticate_tleap_search_stock,
    )
    from .durable_preparation import file_chunks
    from .geometry_reuse import (
        GeometryReusePlan, GeometryReuseSupply, invocation_bytes, _scan_archive,
    )
    from .preamber_geometry_integrity import PreAmberGeometryIntegrity

    def decode(value, kind):
        raw = value.encode()
        return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))

    plan = decode(data["plan"], GeometryReusePlan)
    source = decode(data["source"], c.PreparationSelection)
    nomination = decode(data["nomination"], NominationDossier)
    inventory = decode(data["inventory"], StructuralInventory)
    coordinates = decode(data["coordinates"], AssemblyCoordinates)
    selected = tuple(decode(row, NativeSubworkDefinition) for row in data["definitions"])
    supplies = tuple(decode(row, GeometryReuseSupply) for row in data["supplies"])
    assessments = tuple(decode(row, PreAmberGeometryIntegrity) for row in data["assessments"])
    invocation_bytes(plan, source, nomination, inventory, coordinates, selected,
                     data["source_root"], supplies, assessments,
                     implementation=None if prepared_contract is None else prepared_contract.implementation)
    if any(row.parent_contact != parent for row in selected):
        raise ValueError("fresh model child substitutes actual native parent")
    if prepared_contract is None:
        # Historical descriptors retain their original labels and exact guard.
        for relative, expected in (*plan.code_sources, ("uv.lock", plan.dependency_lock_sha256)):
            digest = sha256()
            for block in file_chunks(Path(data["source_root"]) / relative):
                digest.update(block)
            if digest.hexdigest() != expected:
                raise ValueError("fresh model producing source/lock changed: " + relative)
    stock = science.validate_stock(source.source_members)
    engine_inventory = authenticate_engine_stock(stock)
    search_stock = authenticate_tleap_search_stock(plan, engine_inventory)
    for path, expected in ((plan.interpreter_path, plan.interpreter_sha256), (plan.tleap_path, plan.tleap_sha256)):
        if not any(row["kind"] == "file" and row["sha256"] == expected for row in engine_inventory["entries"]):
            raise ValueError("fresh model executable is outside authentic installed stock")
        digest = sha256()
        for block in file_chunks(Path(path).resolve()):
            digest.update(block)
        if digest.hexdigest() != expected:
            raise ValueError("fresh model selected executable changed")
    if not all(os.environ.get(name) == "1" for name in ("OPENMM_CPU_THREADS", "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")):
        raise ValueError("fresh model child changed selected one-thread environment")
    archives = dict(plan.archive_inputs)
    for supply in supplies:
        _scan_archive(archives[supply.identity], supply.definition, supply.census, supply.archive_evidence)
    return plan, source, nomination, inventory, coordinates, selected, supplies, assessments, stock, engine_inventory, search_stock


def preflight_selected_child(*, invocation, expected_parent, prepared_contract):
    """Read complete original geometry through the installed entry before contact."""
    import importlib
    from types import SimpleNamespace
    from .durable_native_entry import (
        _SelectedSourceFinder, _prepared_embedded_work, authenticate_loaded_engine_modules, refuse_external_network)
    from .geometry_recursive_translation import native_effect_slot_ids
    from . import contracts as historical

    data = json.loads(invocation.read())
    if set(data) != {"plan", "source", "nomination", "inventory", "coordinates", "definitions",
                     "source_root", "supplies", "assessments"}:
        raise ValueError("fresh model invocation changes complete original operand census")
    finder = _SelectedSourceFinder(data["source_root"], json.loads(data["plan"])["value"]["code_sources"])
    sys.meta_path.insert(0, finder)
    try:
        plan, source, nomination, inventory, coordinates, selected, supplies, assessments, _, engine_inventory, _ = _prepare_child(
            data, expected_parent, prepared_contract)
        work = _prepared_embedded_work(prepared_contract, expected_parent, plan, selected,
            (source, nomination, inventory, coordinates, *supplies, *assessments),
            scientific_unit_ids=(historical.UNIT,),
            native_effect_slot_ids=native_effect_slot_ids(SimpleNamespace(plan=plan, source=source, supplies=supplies)))
        refuse_external_network(None)
        for name in ("numpy", "scipy", "openmm", "parmed"):
            importlib.import_module(name)
        authenticate_loaded_engine_modules(engine_inventory)
        return work
    finally:
        sys.meta_path.remove(finder)


def _authenticated_child(progress, data, prepared_contract=None):
    from io import StringIO
    import os
    import subprocess
    import traceback
    from empirical_lawhood.runtime.native_subwork import NativeSubworkState
    from .durable_contracts import model_id
    from .durable_native_entry import (
        authenticate_loaded_engine_modules, refuse_external_network, selected_tleap_command, selected_tleap_environment)
    from .durable_preparation import DurableCallLedger, complete_unit, file_chunks
    from .durable_roster import freeze
    from .geometry_reuse import materialize_geometry_inputs
    from .parameter_audit import assigned_parameter_inventory, realized_atom_origins_from_coordinates
    from .preparation import scoped_boundary_stock, scoped_kcx_stock

    plan, source, _, _, _, selected, supplies, assessments, stock, engine_inventory, search_stock = _prepare_child(
        data, progress.parent_contact, prepared_contract)
    freeze(progress, selected)
    root = Path(plan.workdir)
    refuse_external_network(root / "launcher/network-refusals.jsonl")
    reused = root / "reused-geometry"
    reused.mkdir()
    by_geometry = {}
    archives = dict(plan.archive_inputs)
    for supply, assessment in zip(supplies, assessments, strict=True):
        destination = reused / supply.definition.subwork_id
        destination.mkdir()
        materialize_geometry_inputs(archives[supply.identity], supply.definition, supply.census,
                                    supply.archive_evidence, destination)
        by_geometry[supply.definition.subwork_id] = (supply, assessment, destination)
    # Original geometry is now fully authenticated; only the genuine two-file
    # supply is copied. No PDBFixer/OpenMM constructor is needed on this route.
    from . import native
    from parmed.amber import AmberParameterSet, AmberParm

    native._json(root / "launcher/loaded-engine-modules.json", authenticate_loaded_engine_modules(engine_inventory))
    temporary = root / "temporary"
    temporary.mkdir()
    base = AmberParameterSet()
    base.load_parameters(StringIO(stock["source.parm10-dat"]))
    base.load_parameters(StringIO(stock["source.ff14sb-frcmod"]))
    custom = scoped_kcx_stock(stock["source.kcx-prepin"], stock["source.kcx-frcmod"], existing_atom_types=base.atom_types)
    boundaries = scoped_boundary_stock(stock["source.parm10-dat"], stock["source.ff14sb-frcmod"])
    by_id = {row.subwork_id: row for row in selected}
    for construct_id, view, parameters in plan.model_census:
        definition = by_id[model_id(construct_id, view, parameters)]
        if definition.subwork_id not in plan.attempted_model_ids:
            continue
        if progress.inspect(definition).state is NativeSubworkState.COMPLETED:
            progress.recover(definition)
            continue
        supply, assessment, input_directory = by_geometry["geometry." + construct_id + "." + view]
        entry = progress.begin(definition)
        progress.contact(entry)
        directory = root / definition.subwork_id
        directory.mkdir()
        ledger = DurableCallLedger(progress, plan, root, entry, directory)
        error = None
        try:
            for evidence in (assessment.heavy_file, assessment.origin_file):
                name = Path(evidence.relative_path).name
                with (directory / name).open("xb") as output:
                    for block in file_chunks(input_directory / name, expected=evidence):
                        output.write(block)
                    output.flush()
                    os.fsync(output.fileno())
            native._json(directory / "geometry-reuse-parent.json", dict(
                supply=json.loads(supply.identity.canonical_bytes()),
                original_geometry=json.loads(supply.definition.identity.canonical_bytes()),
                original_geometry_receipt=json.loads(supply.geometry_receipt.canonical_bytes()),
                independent_integrity=json.loads(supply.independent_integrity.canonical_bytes()),
                original_archive=json.loads(supply.archive_evidence.canonical_bytes())))
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
                    return subprocess.run(command, cwd=directory, env=environment,
                                          stdout=stdout, stderr=stderr, check=False)

            returned = ledger.call("ambertools.tleap", dict(command=command, executable_sha256=plan.tleap_sha256,
                engine_inventory_sha256=plan.engine_inventory_sha256, search_stock=search_stock,
                environment=environment, cwd=str(directory), chemical_state=source.chemical_state,
                parameter_view=parameters, geometry_definition=json.loads(supply.definition.identity.canonical_bytes())["value"],
                geometry_receipt=json.loads(supply.geometry_receipt.canonical_bytes())["value"],
                geometry_supply=json.loads(supply.identity.canonical_bytes())["value"],
                independent_integrity=json.loads(supply.independent_integrity.canonical_bytes())["value"]), execute,
                realization=lambda result: dict(returncode=result.returncode))
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
                      geometry=supply.definition.identity, geometry_receipt=supply.geometry_receipt)
    (root / "child-known-census.txt").write_text(
        f"Frozen12/24 census; selected {len(plan.attempted_model_ids)} fresh models, zero new geometry attempts; "
        "original successful geometry retained independently; downstream adequacy unevaluable\n")
