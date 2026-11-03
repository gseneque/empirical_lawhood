# SPDX-License-Identifier: MPL-2.0
"""Selected isolated native molecular preparation; imports remain cold."""

from dataclasses import asdict
from decimal import Decimal
from hashlib import sha256
from io import StringIO
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import time
import traceback

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

from . import contracts as c, science
from .coordinate_plan import THREE, pdb_plan
from .parameter_audit import assigned_parameter_inventory, realized_atom_origins_from_coordinates
from .preparation import scoped_boundary_stock, scoped_kcx_stock


def _hash(path):
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file(path, root):
    return c.FileEvidence(
        path.relative_to(root).as_posix(), path.stat().st_size, _hash(path)
    )


def _evidence_dict(path, root):
    return asdict(_file(path, root))


def _json(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def verify_engine(source):
    """Verify every installed member before importing the selected model engine."""
    stock = science.validate_stock(source.source_members)
    inventory = json.loads(stock["source.engine-inventory"])
    for row in inventory["entries"]:
        path = Path(row["actual_path"])
        if row["kind"] == "file":
            if path.stat().st_size != row["size"] or _hash(path) != row["sha256"]:
                raise ValueError(
                    "selected native engine member changed: " + row["path"]
                )
        elif not path.is_symlink() or os.readlink(path) != row["target"]:
            raise ValueError("selected native engine link changed: " + row["path"])
    return stock


class CallLedger:
    """Actual nested attempts; inclusive clocks are never summed as fresh costs."""

    def __init__(self, root):
        self.root = root
        self.calls = []
        self.current_parent = None
        self.model_id = "preparation.shared"
        self.counter = 0

    def call(self, role, request, function, *, realization=None, files=()):
        self.counter += 1
        call_id = "native-call." + str(self.counter).zfill(6)
        parent = self.current_parent
        self.current_parent = call_id
        start = time.perf_counter()
        start_cpu = time.process_time()
        child_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        termination = "COMPLETED"
        error = None
        realized = {}
        try:
            result = function()
            if realization is not None:
                realized = realization(result)
            return result
        except BaseException:
            termination = "TECHNICAL_FAILURE"
            error = traceback.format_exc()
            raise
        finally:
            child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
            row = c.NativeCall(
                call_id,
                parent,
                self.model_id,
                role,
                json.dumps(request, sort_keys=True, separators=(",", ":"), default=str),
                json.dumps(
                    realized, sort_keys=True, separators=(",", ":"), default=str
                ),
                Decimal(str(time.perf_counter() - start)),
                Decimal(
                    str(
                        time.process_time()
                        - start_cpu
                        + child_after.ru_utime
                        + child_after.ru_stime
                        - child_before.ru_utime
                        - child_before.ru_stime
                    )
                ),
                termination,
                error,
                tuple(files),
            )
            self.calls.append(row)
            with (self.root / "native-calls.jsonl").open("ab") as stream:
                stream.write(row.canonical_bytes() + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            self.current_parent = parent


def instrument_completion(mm, ledger, directory):
    """Instrument PDBFixer's actual contexts, minimizers, steps and receivers.

    It uses a geometric repulsion System. The complete native XML is retained
    before each context, separately from the later chemical force-field audit.
    The original selected PDBFixer/OpenMM distribution is not edited.
    """
    original_context = mm.Context
    original_integrator = mm.LangevinIntegrator
    original_minimize = mm.LocalEnergyMinimizer.minimize
    counters = {"context": 0, "receiver": 0}
    patched = []

    def context(system, integrator, *args, **kwargs):
        counters["context"] += 1
        name = "completion-system-" + str(counters["context"]).zfill(3) + ".xml"
        path = directory / name
        path.write_text(mm.XmlSerializer.serialize(system))
        request = dict(
            system=_evidence_dict(path, ledger.root),
            particles=system.getNumParticles(),
            force_classes=tuple(type(f).__name__ for f in system.getForces()),
            model="PDBFIXER_GEOMETRIC_REPULSION_NOT_DYNAMICS_FORCE_FIELD",
            native_integrator_xml=mm.XmlSerializer.serialize(integrator),
        )

        def actual_platform(value):
            platform = value.getPlatform()
            properties = {
                name: platform.getPropertyValue(value, name)
                for name in platform.getPropertyNames()
            }
            if platform.getName() != "CPU" or properties.get("Threads") != "1":
                raise ValueError(
                    "native completion substitutes selected CPU/one-thread allocation"
                )
            return dict(platform=platform.getName(), platform_properties=properties)

        result = ledger.call(
            "completion.context",
            request,
            lambda: original_context(system, integrator, *args, **kwargs),
            realization=actual_platform,
            files=(_file(path, ledger.root),),
        )
        getter = result.getState
        setter = result.setPositions
        setstate = result.setState
        setparameter = result.setParameter

        def get_state(*args, **kwargs):
            counters["receiver"] += 1
            destination = directory / (
                "completion-state-" + str(counters["receiver"]).zfill(5) + ".xml"
            )

            def realize(state):
                destination.write_text(mm.XmlSerializer.serialize(state))
                return dict(state=_evidence_dict(destination, ledger.root))

            return ledger.call(
                "completion.receiver",
                dict(args=args, kwargs=kwargs),
                lambda: getter(*args, **kwargs),
                realization=realize,
            )

        def set_positions(positions):
            path = directory / (
                "requested-positions-" + str(ledger.counter + 1).zfill(6) + ".json"
            )
            # Preserve the complete native Quantity representation and its unit.
            # OpenMM Quantity iteration gives each Vec3 component with units.
            _json(
                path,
                dict(
                    unit=str(getattr(positions, "unit", "native-default-nanometer")),
                    values=tuple(
                        tuple(str(value) for value in row) for row in positions
                    ),
                ),
            )
            return ledger.call(
                "completion.set-positions",
                dict(
                    particle_count=len(positions),
                    full_requested_positions=_evidence_dict(path, ledger.root),
                ),
                lambda: setter(positions),
                files=(_file(path, ledger.root),),
            )

        def set_parameter(name, value):
            return ledger.call(
                "completion.set-parameter",
                dict(name=name, value=str(value)),
                lambda: setparameter(name, value),
            )

        def set_state(state):
            path = directory / (
                "requested-state-" + str(ledger.counter + 1).zfill(6) + ".xml"
            )
            path.write_text(mm.XmlSerializer.serialize(state))
            return ledger.call(
                "completion.set-state",
                dict(state=_evidence_dict(path, ledger.root)),
                lambda: setstate(state),
                files=(_file(path, ledger.root),),
            )

        result.getState = get_state
        result.setPositions = set_positions
        result.setState = set_state
        result.setParameter = set_parameter
        patched.append(
            (result, ("getState", "setPositions", "setState", "setParameter"))
        )
        return result

    def integrator(*args, **kwargs):
        result = ledger.call(
            "completion.integrator",
            dict(args=args, kwargs=kwargs),
            lambda: original_integrator(*args, **kwargs),
            realization=lambda value: dict(
                native_xml=mm.XmlSerializer.serialize(value)
            ),
        )
        step = result.step
        seedsetter = result.setRandomNumberSeed
        result.setRandomNumberSeed = lambda seed: ledger.call(
            "completion.set-random-seed", dict(seed=int(seed)), lambda: seedsetter(seed)
        )
        result.step = lambda steps: ledger.call(
            "completion.integration",
            dict(steps=int(steps), step_size_picoseconds=str(result.getStepSize())),
            lambda: step(steps),
        )
        patched.append((result, ("step", "setRandomNumberSeed")))
        return result

    def minimize(context, *args, **kwargs):
        return ledger.call(
            "completion.minimization",
            dict(
                args=args,
                kwargs=kwargs,
                native_internal_iteration_count="NOT_EXPOSED_BY_NATIVE_API",
            ),
            lambda: original_minimize(context, *args, **kwargs),
        )

    mm.Context = context
    mm.LangevinIntegrator = integrator
    mm.LocalEnergyMinimizer.minimize = minimize

    def restore():
        mm.Context = original_context
        mm.LangevinIntegrator = original_integrator
        mm.LocalEnergyMinimizer.minimize = original_minimize
        for instance, names in patched:
            for name in names:
                delattr(instance, name)
        patched.clear()

    return restore


def _rotate_met(fixer, construct, view, unit, np):
    target = (
        95
        if construct.construct_id.startswith("gp.i95m.")
        else 98
        if construct.construct_id == "te.p415a.v98m"
        else None
    )
    if target is None:
        return []
    angle = (
        float(next(row[2] for row in c.JOINT_VIEWS if row[0] == view)) * math.pi / 180
    )
    positions = np.asarray(
        fixer.positions.value_in_unit(unit.nanometers), dtype=float
    ).copy()
    changed = []
    for chain in fixer.topology.chains():
        residues = list(chain.residues())
        expected_length = len(construct.ssu_sequence)
        if len(residues) != expected_length:
            continue
        residue = next((row for row in residues if int(row.id) == target), None)
        if residue is None or residue.name != "MET":
            raise ValueError("actual completed mutant lacks target Met in one SSU")
        atoms = {atom.name: atom.index for atom in residue.atoms()}
        if not {"N", "CA", "CB", "CG", "SD", "CE"}.issubset(atoms):
            raise ValueError("actual completed Met lacks full heavy atom geometry")
        p0, p1, p2, p3 = (positions[atoms[name]] for name in ("N", "CA", "CB", "CG"))
        axis = p2 - p1
        axis /= np.linalg.norm(axis)
        v, w = p0 - p1, p3 - p2
        v -= np.dot(v, axis) * axis
        w -= np.dot(w, axis) * axis
        current = math.atan2(np.dot(np.cross(axis, v), w), np.dot(v, w))
        delta = angle - current
        for name in ("CG", "SD", "CE"):
            offset = positions[atoms[name]] - p2
            positions[atoms[name]] = (
                p2
                + offset * math.cos(delta)
                + np.cross(axis, offset) * math.sin(delta)
                + axis * np.dot(axis, offset) * (1 - math.cos(delta))
            )
        changed.append(
            dict(
                chain=chain.id,
                position=target,
                original_chi1_radian=current,
                requested_chi1_radian=angle,
                moved_atoms=("CG", "SD", "CE"),
                status="DECLARED_INITIAL_GEOMETRY_NOT_OBSERVED_MUTANT",
            )
        )
    if len(changed) != 8:
        raise ValueError("Met initialization omits one of the eight mutant SSUs")
    fixer.positions = positions * unit.nanometers
    return changed


def _project_native_disulfides(topology, plan, *, rename=False):
    expected = {
        tuple(sorted(tuple(partner) for partner in row["partners"]))
        for row in plan["authenticated_disulfides"]
    }
    actual = {
        tuple(sorted((atom.residue.chain.id, int(atom.residue.id)) for atom in bond))
        for bond in topology.bonds()
        if all(atom.name == "SG" for atom in bond)
    }
    if actual != expected:
        raise ValueError(
            "native geometric topology changes authenticated disulfide bonds"
        )
    if rename:
        endpoints = {partner for bond in expected for partner in bond}
        for residue in topology.residues():
            if (residue.chain.id, int(residue.id)) in endpoints:
                if residue.name != "CYS":
                    raise ValueError("authentic disulfide residue is not native CYS")
                residue.name = "CYX"


def _complete(
    source, inventory, construct, view, directory, ledger, mm, app, unit, np, PDBFixer
):
    plan = pdb_plan(source, inventory, construct, view)
    (directory / "source-selected.pdb").write_text(plan.pop("pdb_text"))
    fixer = ledger.call(
        "completion.pdbfixer-constructor",
        dict(
            input_pdb=_evidence_dict(directory / "source-selected.pdb", ledger.root),
            selected_platform="CPU",
            selected_cpu_threads=1,
        ),
        lambda: PDBFixer(
            filename=str(directory / "source-selected.pdb"),
            platform=mm.Platform.getPlatformByName("CPU"),
        ),
    )
    _project_native_disulfides(fixer.topology, plan)
    # These are exact missing positions from the authenticated full sequence,
    # including termini. The incomplete observed topology never becomes full.
    fixer.missingResidues = {
        (index, position): names for index, position, names in plan["missing_residues"]
    }
    by_chain = {}
    for chain, mutation in plan["mutations"]:
        by_chain.setdefault(chain, []).append(mutation)
    for chain, mutations in by_chain.items():
        fixer.applyMutations(mutations, chain)
    fixer.findMissingAtoms()
    restore = instrument_completion(mm, ledger, directory)
    try:
        seed = next(row[1] for row in c.JOINT_VIEWS if row[0] == view)
        ledger.call(
            "completion.pdbfixer",
            dict(seed=seed, source_revision="94cfa4c0ca551cdc5f13320f9a658efd59f2b881"),
            lambda: fixer.addMissingAtoms(seed=seed),
        )
    finally:
        restore()
    plan["methionine_initialization"] = _rotate_met(fixer, construct, view, unit, np)
    _project_native_disulfides(fixer.topology, plan, rename=True)
    states = {
        (chain, int(position)): name
        for chain, position, name in plan["desired_histidine_states"]
    }
    for residue in fixer.topology.residues():
        if residue.name == "HIS":
            residue.name = states.get((residue.chain.id, int(residue.id)), "HIE")
    realized_chains = []
    for chain in fixer.topology.chains():
        residues = list(chain.residues())
        expected = next(
            (row for row in plan["complete_chains"] if row["chain"] == chain.id), None
        )
        if expected is None:
            continue
        # Independently inspect actual names/positions, allowing declared charge
        # state names and activated KCX, before any Amber dynamics construction.
        reverse = {name: letter for letter, name in THREE.items()}
        reverse.update(KCX="K", HID="H", HIE="H", HIP="H", CYX="C")
        sequence = "".join(reverse.get(residue.name, "?") for residue in residues)
        positions = tuple(int(row.id) for row in residues)
        if sequence != expected["sequence"] or positions != tuple(
            range(1, len(sequence) + 1)
        ):
            raise ValueError("actual native completion omits/substitutes full genotype")
        realized_chains.append(
            expected | dict(actual_residue_names=tuple(row.name for row in residues))
        )
    if len(realized_chains) != 16:
        raise ValueError("actual completed model omits an L8S8 chain")
    plan["complete_chains"] = realized_chains
    originals = {
        (row["chain"], int(row["position"]), row["atom"]): row
        for row in plan["selected_atom_origins"]
    }
    # Every realized heavy atom is explicitly joined or marked as constructed.
    # Sidechain atoms changed by intervention cannot inherit observed WT status.
    changed_positions = {
        (chain, int(mutation.split("-")[1])) for chain, mutation in plan["mutations"]
    }
    plan["complete_heavy_atoms"] = []
    for atom in fixer.topology.atoms():
        key = (atom.residue.chain.id, int(atom.residue.id), atom.name)
        original = originals.get(key)
        changed = key[:2] in changed_positions and atom.name not in (
            "N",
            "CA",
            "C",
            "O",
            "OXT",
            "CB",
        )
        plan["complete_heavy_atoms"].append(
            dict(
                chain=key[0],
                position=key[1],
                atom=key[2],
                component=atom.residue.name,
                element=atom.element.symbol if atom.element is not None else None,
                source_origin=original
                if original is not None and not changed
                else None,
                status="INHERITED_OBSERVED_SOURCE"
                if original is not None and not changed
                else "DECLARED_CONSTRUCTED_MUTANT_OR_MISSING_ATOM",
            )
        )
    with (directory / "complete-heavy.pdb").open("w") as stream:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, stream, keepIds=True)
    _json(directory / "atom-origin-provenance.json", plan)


def _leap_script(parameter_view, plan):
    common = [
        "source leaprc.protein.ff14SB",
        "source leaprc.water.tip3p",
        "source leaprc.gaff2",
    ]
    if parameter_view == "scoped-kcx-aliases":
        element = dict(C="C", CT="C", H="H", H1="H", HC="H", N="N", O="O", O2="O")
        hybrid = dict(
            C="sp2", CT="sp3", H="sp3", H1="sp3", HC="sp3", N="sp2", O="sp2", O2="sp2"
        )
        common.append(
            "addAtomTypes { "
            + " ".join(
                '{ "' + alias + '" "' + element[typ] + '" "' + hybrid[typ] + '" }'
                for typ, alias in c.KCX_ALIASES
            )
            + " }"
        )
        common += [
            "loadAmberPrep kcx-scoped.prepin",
            "loadAmberParams kcx-boundaries.frcmod",
            "loadAmberParams kcx-scoped.frcmod",
        ]
    else:
        common += ["loadAmberPrep kcx.prepin", "loadAmberParams kcx.frcmod"]
    common += [
        "loadAmberPrep cabp.prepi",
        "loadAmberParams cabp.frcmod",
        "model = loadPDB complete-heavy.pdb",
    ]
    offsets = {}
    offset = 0
    for chain in plan["complete_chains"]:
        offsets[chain["chain"]] = offset
        offset += len(chain["sequence"])
    for bond in plan["authenticated_disulfides"]:
        left, right = bond["partners"]
        common.append(
            f"bond model.{offsets[left[0]] + left[1]}.SG model.{offsets[right[0]] + right[1]}.SG"
        )
    common += [
        "check model",
        "solvateBox model TIP3PBOX 10.0",
        "addIons model Na+ 0",
        "addIons model Cl- 0",
        "check model",
        "saveAmberParm model model.prmtop model.inpcrd",
        "quit",
    ]
    return "\n".join(common) + "\n"


def _prepare_worker(source, nomination, inventory, coordinates, root):
    science.validate_source(source, nomination, inventory, coordinates)
    stock = verify_engine(source)
    # Native imports are inside the explicitly selected operation only.
    import numpy as np
    import openmm as mm
    from openmm import app, unit
    from parmed.amber import AmberParameterSet, AmberParm
    from pdbfixer import PDBFixer

    ledger = CallLedger(root)
    base = AmberParameterSet()
    base.load_parameters(StringIO(stock["source.parm10-dat"]))
    base.load_parameters(StringIO(stock["source.ff14sb-frcmod"]))
    custom = scoped_kcx_stock(
        stock["source.kcx-prepin"],
        stock["source.kcx-frcmod"],
        existing_atom_types=base.atom_types,
    )
    boundaries = scoped_boundary_stock(
        stock["source.parm10-dat"], stock["source.ff14sb-frcmod"]
    )
    models, assets = [], []
    geometry_cache = {}
    for construct_id, view, parameters in c.model_roster():
        construct = next(
            row for row in source.constructs if row.construct_id == construct_id
        )
        model_id = "model." + construct_id + "." + view + "." + parameters
        directory = root / model_id
        directory.mkdir()
        call_ids = []
        census = ()
        atom_count = 0
        disposition = A.UNEVALUABLE
        reasons = []
        provenance = None
        try:
            key = (construct_id, view)
            if key not in geometry_cache:
                geometry = root / ("geometry." + construct_id + "." + view)
                geometry.mkdir()
                ledger.model_id = "geometry." + construct_id + "." + view
                prior = {row.call_id for row in ledger.calls}
                try:
                    _complete(
                        source,
                        inventory,
                        construct,
                        view,
                        geometry,
                        ledger,
                        mm,
                        app,
                        unit,
                        np,
                        PDBFixer,
                    )
                    geometry_cache[key] = (
                        geometry,
                        tuple(
                            row.call_id
                            for row in ledger.calls
                            if row.call_id not in prior
                        ),
                        None,
                    )
                except Exception:
                    geometry_cache[key] = (
                        geometry,
                        tuple(
                            row.call_id
                            for row in ledger.calls
                            if row.call_id not in prior
                        ),
                        traceback.format_exc(),
                    )
            geometry, geometry_calls, error = geometry_cache[key]
            call_ids.extend(geometry_calls)
            for file in sorted(geometry.iterdir()):
                if file.is_file():
                    (directory / file.name).write_bytes(file.read_bytes())
            if error is not None:
                raise RuntimeError(
                    "declared complete-coordinate preparation failed:\n" + error
                )
            for filename, member in (
                ("kcx.prepin", "source.kcx-prepin"),
                ("kcx.frcmod", "source.kcx-frcmod"),
                ("cabp.prepi", "source.cabp-prepi"),
                ("cabp.frcmod", "source.cabp-frcmod"),
            ):
                (directory / filename).write_text(stock[member])
            (directory / "kcx-scoped.prepin").write_text(custom.scoped_prepi_utf8)
            (directory / "kcx-scoped.frcmod").write_text(
                custom.scoped_custom_frcmod_utf8
            )
            (directory / "kcx-boundaries.frcmod").write_text(
                boundaries.scoped_boundary_frcmod_utf8
            )
            origin_path = directory / "atom-origin-provenance.json"
            origin = json.loads(origin_path.read_text())
            (directory / "tleap.in").write_text(_leap_script(parameters, origin))
            environment = dict(
                os.environ,
                AMBERHOME=c.ENGINE_ROOT + "/ambertools24-tleap",
                LD_LIBRARY_PATH=c.ENGINE_ROOT + "/ambertools-runtime-libraries/lib",
            )
            ledger.model_id = model_id
            prior = {row.call_id for row in ledger.calls}

            def execute():
                with (
                    (directory / "tleap.stdout.log").open("wb") as out,
                    (directory / "tleap.stderr.log").open("wb") as err,
                ):
                    result = subprocess.run(
                        [
                            c.ENGINE_ROOT + "/ambertools24-tleap/bin/tleap",
                            "-f",
                            "tleap.in",
                        ],
                        cwd=directory,
                        env=environment,
                        stdout=out,
                        stderr=err,
                        check=False,
                    )
                if (
                    result.returncode != 0
                    or not (directory / "model.prmtop").is_file()
                    or not (directory / "model.inpcrd").is_file()
                ):
                    raise RuntimeError(
                        "actual teLeap failed or omitted parameter/coordinate output; returncode="
                        + str(result.returncode)
                    )
                return result

            try:
                ledger.call(
                    "ambertools.tleap",
                    dict(
                        script=_evidence_dict(directory / "tleap.in", root),
                        chemical_state=source.chemical_state,
                        parameter_view=parameters,
                        ordinary_protein_parameters="GLOBAL_CUSTOM_OVERRIDE"
                        if parameters == "published-global-kcx-override"
                        else "UNCHANGED_FF14SB_WITH_EXPLICIT_KCX_BOUNDARIES",
                    ),
                    execute,
                    realization=lambda result: dict(returncode=result.returncode),
                )
            finally:
                call_ids.extend(
                    row.call_id for row in ledger.calls if row.call_id not in prior
                )
            structure = AmberParm(
                str(directory / "model.prmtop"), str(directory / "model.inpcrd")
            )
            audit = assigned_parameter_inventory(structure)
            origin["amber_realization"] = realized_atom_origins_from_coordinates(
                structure, origin, (directory / "complete-heavy.pdb").read_text(),
                (directory / "model.inpcrd").read_text())
            _json(origin_path, origin)
            _json(directory / "complete-assigned-parameters.json", audit)
            census = tuple(sorted(audit["term_census"].items()))
            atom_count = len(structure.atoms)
            provenance = (
                (directory / "atom-origin-provenance.json").relative_to(root).as_posix()
            )
            disposition = A.SATISFIED
            reasons.append(
                "FULL_NATIVE_MODEL_AND_PARAMETER_CENSUS_COMPLETE_NOT_DYNAMICS_OR_KINETICS"
            )
        except Exception:
            (directory / "technical-failure.txt").write_text(traceback.format_exc())
            reasons.append("TECHNICAL_MOLECULAR_PREPARATION_UNEVALUABLE")
        files = tuple(
            c.NativeTextFile(_file(path, root), path.read_text())
            for path in sorted(directory.iterdir())
            if path.is_file()
        )
        bundle = c.ModelAssets(
            "product.assets." + construct_id + "." + view + "." + parameters,
            c.identity(source),
            construct_id,
            view,
            parameters,
            files,
        )
        assets.append(bundle)
        models.append(
            c.PreparedModel(
                model_id,
                construct,
                view,
                parameters,
                disposition,
                tuple(reasons),
                tuple(row.evidence for row in files),
                c.identity(bundle),
                atom_count,
                census,
                provenance,
                tuple(call_ids),
            )
        )
    product = c.PreparationProduct(
        "product." + c.NAMESPACE + ".preparation",
        c.identity(source),
        source.structural_inventory,
        source.structural_coordinates,
        source.nomination,
        tuple(models),
        tuple(sorted(ledger.calls, key=lambda row: row.call_id)),
        (_file(root / "native-calls.jsonl", root),)
        if (root / "native-calls.jsonl").is_file()
        else (),
        1,
    )
    (root / "preparation.json").write_bytes(product.canonical_bytes())
    for index, bundle in enumerate(assets):
        (root / ("assets-" + str(index).zfill(2) + ".json")).write_bytes(
            bundle.canonical_bytes()
        )
    return product, tuple(assets)


def prepare(source, nomination, inventory, coordinates, *, workdir, context=None, native_subwork=None):
    """Use the original science through the common prepared specialist gate."""
    from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
    from empirical_lawhood.infrastructure.isolated_native_subwork import run_isolated_native_entry
    from .durable_preparation import publish_directory, publish_record
    from .ordinary_preparation import check_preparation_only_root, LAUNCH

    if context is None or context.prepared_invocation is None or native_subwork is None:
        raise ValueError("SOFTWARE: original preparation requires the common complete specialist contract and progress")
    contract = context.prepared_invocation
    contract.validate_context(context)
    work = contract.native_work
    if (work is None or work.isolated_selection is None or len(work.definitions) != 1
            or work.definitions[0].subwork_id != LAUNCH or native_subwork.parent_contact != contract.expected_parent_contact):
        raise ValueError("original preparation substitutes its exact prepared specialist parent/launcher scope")
    science.validate_source(source, nomination, inventory, coordinates)
    root = Path(workdir)
    if str(root) != source.native_workdir:
        raise ValueError("native preparation substitutes selected operational root")
    check_preparation_only_root(root)
    definition = work.definitions[0]
    selection = work.isolated_selection
    if selection.invocation_path != str(root / ".preparation/invocation.json"):
        raise ValueError("original preparation changes its explicit frozen operational invocation")
    native_subwork.freeze_roster(NativeSubworkRoster("selected.native-subwork", native_subwork.parent_contact,
        (definition.identity,)), definitions=(definition,))
    entry = native_subwork.begin(definition)
    for name, record in (("source", source), ("nomination", nomination), ("inventory", inventory), ("coordinates", coordinates)):
        with (root / (name + ".json")).open("xb") as output:
            output.write(record.canonical_bytes())
    (root / "temporary").mkdir()
    with (root / "isolated-worker.stdout.log").open("xb") as stdout, (root / "isolated-worker.stderr.log").open("xb") as stderr:
        returned = run_isolated_native_entry(selection, native_subwork, lifecycle_entry=entry,
            start_output_id="process.start", return_output_id="process.return",
            environment=dict(work.isolated_environment.selected_environment), cwd=root, stdout=stdout, stderr=stderr,
            prepared_contract=contract, entry_preflight="preflight_selected_child")
    product, assets, failure = None, (), None
    if returned.returncode == 0:
        try:
            product = decode_canonical_bytes((root / "preparation.json").read_bytes(), c.PreparationProduct, maximum_bytes=None)
            assets = tuple(decode_canonical_bytes((root / ("assets-" + str(index).zfill(2) + ".json")).read_bytes(),
                c.ModelAssets, maximum_bytes=None) for index in range(len(c.model_roster())))
            publish_record(native_subwork, entry, "preparation", product)
            for index, asset in enumerate(assets):
                publish_record(native_subwork, entry, "assets-" + str(index).zfill(2), asset)
        except Exception as error:
            failure = error
    publish_directory(native_subwork, entry, root, root)
    succeeded = returned.returncode == 0 and failure is None
    native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED if succeeded else OperationalStatus.FAILED,
        cost=InquiryCost(returned.inclusive_cpu_seconds, returned.wall_seconds, None),
        cost_scope="Actual original full-model specialist+relay inclusive window; per-model cost unmeasured",
        reason_codes=() if succeeded else ("known-original-preparation-adverse-return-or-output-refusal",))
    if not succeeded:
        raise RuntimeError("original specialist adverse return; full original process/raw custody retained") from failure
    return product, assets


def _main():
    raise SystemExit("Use the installed prepared full-model operation; historical private bootstrap is retired")


if __name__ == "__main__":
    _main()
