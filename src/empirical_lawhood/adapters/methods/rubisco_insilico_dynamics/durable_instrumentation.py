# SPDX-License-Identifier: MPL-2.0
"""Full native completion operands around unchanged selected helper science."""

from dataclasses import asdict
import json
import struct


def selected_value(value):
    """Keep full values/units; unfamiliar native objects are never repr summaries."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        return {"binary64_hex": value.hex(), "ieee754_binary64_be": struct.pack(">d", value).hex()}
    if isinstance(value, (tuple, list)):
        return [selected_value(row) for row in value]
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("native request dictionary changes full string key census")
        return {key: selected_value(row) for key, row in value.items()}
    if type(value).__module__.startswith("numpy") and hasattr(value, "tobytes"):
        if value.dtype.hasobject or value.dtype.kind not in "biufc":
            raise ValueError("native numeric operands cannot encode object or nonnumeric arrays")
        return {"dtype": value.dtype.str, "shape": list(value.shape),
                "source_strides": list(getattr(value, "strides", ())), "byte_order": "C",
                "full_native_bytes_hex": value.tobytes(order="C").hex()}
    if hasattr(value, "unit") and hasattr(value, "value_in_unit"):
        return {"unit": str(value.unit), "value": selected_value(value.value_in_unit(value.unit))}
    # Vec3 supports complete index-based coordinates, without a summarized repr.
    if type(value).__name__ == "Vec3":
        return [selected_value(value[index]) for index in range(3)]
    if hasattr(value, "getName") and type(value).__name__ == "Platform":
        return {"platform": value.getName()}
    raise ValueError("unrepresented complete native request type: " + type(value).__name__)


def write_full_positions(path, value):
    """Stream complete requested numeric operands into raw files, not control JSON."""
    with path.open("x") as output:
        def write(row):
            if hasattr(row, "unit") and hasattr(row, "value_in_unit"):
                output.write('{"unit":' + json.dumps(str(row.unit)) + ',"value":')
                write(row.value_in_unit(row.unit))
                output.write("}")
            elif type(row).__module__.startswith("numpy") and hasattr(row, "shape") and row.shape:
                if row.dtype.hasobject or row.dtype.kind not in "biufc":
                    raise ValueError("native positions cannot contain object/non-numeric arrays")
                header = dict(dtype=row.dtype.str, shape=list(row.shape),
                              source_strides=list(row.strides), byte_order="C")
                output.write(json.dumps(header, sort_keys=True, separators=(",", ":"))[:-1])
                output.write(',"full_native_bytes_hex":"')
                # A NumPy scalar extracted from a non-native-endian array can
                # normalize byte order. Bounded array blocks retain the exact
                # original dtype and C-order bytes, including NaN payloads.
                import numpy as np
                for block in np.nditer(row, flags=["external_loop", "buffered", "zerosize_ok"],
                        op_flags=["readonly"], order="C", buffersize=max(1, (1024 * 1024) // row.dtype.itemsize)):
                    output.write(block.tobytes(order="C").hex())
                output.write('"}')
            elif isinstance(row, (tuple, list)) or type(row).__name__ == "Vec3":
                output.write("[")
                for index, scalar in enumerate(row):
                    if index:
                        output.write(",")
                    write(scalar)
                output.write("]")
            else:
                output.write(json.dumps(selected_value(row), sort_keys=True, separators=(",", ":")))
        write(value)
        output.write("\n")


def selected_fixer_factory(PDBFixer, ledger, directory, app):
    """Keep full mutated topology/coordinates before unchanged helper guards."""
    from . import native as historical_native
    current = None
    sequence = 0
    roles = {"completion.pdbfixer-constructor", "completion.pdbfixer",
             "completion.pdbfixer.apply-mutations", "completion.pdbfixer.find-missing-atoms"}

    def snapshot():
        nonlocal sequence
        sequence += 1
        prefix = directory / ("durable-fixer-" + str(sequence).zfill(6))
        pdb_path = prefix.with_suffix(".pdb")
        with pdb_path.open("w") as output:
            app.PDBFile.writeFile(current.topology, current.positions, output, keepIds=True)
        atom_rows = tuple(dict(index=atom.index, name=atom.name,
            residue_index=atom.residue.index, residue_id=atom.residue.id,
            residue_name=atom.residue.name, chain_index=atom.residue.chain.index,
            chain_id=atom.residue.chain.id,
            element=None if atom.element is None else atom.element.symbol)
            for atom in current.topology.atoms())
        positions_path = prefix.with_suffix(".positions.json")
        write_full_positions(positions_path, current.positions)
        payload = dict(positions_file=historical_native._evidence_dict(positions_path, ledger.root), atoms=atom_rows,
            bonds=tuple((left.index, right.index) for left, right in current.topology.bonds()),
            missing_residues=tuple((list(key), list(value)) for key, value in sorted(getattr(current, "missingResidues", {}).items())),
            missing_atoms=tuple(dict(residue_index=residue.index,
                atoms=tuple(dict(name=atom.name, element=None if atom.element is None else atom.element.symbol)
                            for atom in atoms)) for residue, atoms in sorted(
                                getattr(current, "missingAtoms", {}).items(), key=lambda pair: pair[0].index)),
            missing_terminals=tuple(dict(residue_index=residue.index, names=list(names)) for residue, names in sorted(
                getattr(current, "missingTerminals", {}).items(), key=lambda pair: pair[0].index)))
        state_path = prefix.with_suffix(".json")
        historical_native._json(state_path, payload)
        return dict(full_native_fixer_state=historical_native._evidence_dict(state_path, ledger.root),
                    full_native_fixer_pdb=historical_native._evidence_dict(pdb_path, ledger.root))

    def project_request(role):
        return snapshot() if role in roles and current is not None else {}

    def project_return(role, result):
        return snapshot() if role in roles and current is not None else {}

    ledger.request_projector, ledger.returned_projector = project_request, project_return

    def create(*args, **kwargs):
        nonlocal current
        current = PDBFixer(*args, **kwargs)
        # The constructor's original selected helper role is completion.pdbfixer.
        for name, role in (("applyMutations", "completion.pdbfixer.apply-mutations"),
                           ("findMissingAtoms", "completion.pdbfixer.find-missing-atoms")):
            original = getattr(current, name)
            def wrapped(*arguments, _original=original, _role=role, **keywords):
                return ledger.call(_role, dict(args=selected_value(arguments), kwargs=selected_value(keywords)),
                                   lambda: _original(*arguments, **keywords))
            setattr(current, name, wrapped)
        return current

    return create


def instrument_completion(mm, ledger, directory):
    """Actual snapshots precede mutation/minimization/steps; raw values precede guards."""
    from . import native as historical_native
    original_context, original_integrator = mm.Context, mm.LangevinIntegrator
    original_minimize = mm.LocalEnergyMinimizer.minimize
    patched, contexts = [], {}
    sequence = 0

    def xml(value, kind):
        nonlocal sequence
        sequence += 1
        path = directory / ("durable-" + kind + "-" + str(sequence).zfill(6) + ".xml")
        path.write_text(mm.XmlSerializer.serialize(value))
        return historical_native._evidence_dict(path, ledger.root)

    def operand(context, *, snapshot=True):
        system, integrator, getter, context_binding = contexts[id(context)]
        selected = dict(system=xml(system, "system"), integrator=xml(integrator, "integrator"),
                        context_call=context_binding,
                        force_field_scope="PDBFIXER_GEOMETRIC_REPULSION_NOT_DYNAMICS_FORCE_FIELD")
        if snapshot:
            state = ledger.call("completion.snapshot", selected,
                lambda: getter(getPositions=True, getVelocities=True, getParameters=True,
                               enforcePeriodicBox=False),
                realization=lambda returned: dict(state=xml(returned, "state")))
            selected["state"] = xml(state, "selected-current-state")
        return selected

    def context(system, integrator, *args, **kwargs):
        selected = dict(system=xml(system, "system"), integrator=xml(integrator, "integrator"),
                        args=selected_value(args), kwargs=selected_value(kwargs),
                        force_field_scope="PDBFIXER_GEOMETRIC_REPULSION_NOT_DYNAMICS_FORCE_FIELD")

        def realized(value):
            platform = value.getPlatform()
            return dict(platform=platform.getName(), platform_properties={
                name: platform.getPropertyValue(value, name) for name in platform.getPropertyNames()})

        result = ledger.call("completion.context", selected,
            lambda: original_context(system, integrator, *args, **kwargs), realization=realized)
        binding = asdict(ledger.call_definitions[-1].identity)
        getter, setter = result.getState, result.setPositions
        state_setter, parameter_setter = result.setState, result.setParameter
        contexts[id(result)] = system, integrator, getter, binding
        # Platform interpretation happens after actual context return/files/receipt.
        actual = ledger.calls[-1]
        properties = json.loads(actual.realized_json)
        if properties["platform"] != "CPU" or properties["platform_properties"].get("Threads") != "1":
            raise ValueError("native completion changed selected CPU/one-thread allocation; raw context retained")

        def get_state(*args, **kwargs):
            requested = operand(result, snapshot=False)
            requested.update(args=selected_value(args), kwargs=selected_value(kwargs))
            return ledger.call("completion.receiver", requested, lambda: getter(*args, **kwargs),
                               realization=lambda state: dict(state=xml(state, "receiver")))

        def set_positions(positions):
            requested = operand(result)
            path = directory / ("durable-requested-positions-" + str(ledger.counter + 1).zfill(6) + ".json")
            write_full_positions(path, positions)
            requested["full_requested_positions"] = historical_native._evidence_dict(path, ledger.root)
            return ledger.call("completion.set-positions", requested, lambda: setter(positions))

        def set_state(state):
            requested = operand(result)
            requested["full_requested_state"] = xml(state, "requested-state")
            return ledger.call("completion.set-state", requested, lambda: state_setter(state))

        def set_parameter(name, value):
            requested = operand(result)
            requested.update(name=name, value=selected_value(value))
            return ledger.call("completion.set-parameter", requested, lambda: parameter_setter(name, value))

        result.getState, result.setPositions = get_state, set_positions
        result.setState, result.setParameter = set_state, set_parameter
        patched.append((result, ("getState", "setPositions", "setState", "setParameter")))
        return result

    def integrator(*args, **kwargs):
        result = ledger.call("completion.integrator", dict(args=selected_value(args), kwargs=selected_value(kwargs)),
            lambda: original_integrator(*args, **kwargs), realization=lambda value: dict(integrator=xml(value, "integrator")))
        step, seed_setter = result.step, result.setRandomNumberSeed

        def set_seed(seed):
            if type(seed) is not int:
                raise ValueError("native seed needs exact actual integer")
            return ledger.call("completion.set-random-seed",
                dict(seed=seed, integrator=xml(result, "pre-seed-integrator")), lambda: seed_setter(seed),
                realization=lambda _: dict(integrator=xml(result, "post-seed-integrator")))

        def integrate(steps):
            if type(steps) is not int or steps < 0:
                raise ValueError("native integration step count needs exact nonnegative integer")
            matches = [key for key, (_, selected_integrator, _, _) in contexts.items() if selected_integrator is result]
            if len(matches) != 1:
                raise ValueError("integration lacks its actual unique native context/state binding")
            selected_context = next(instance for instance, _ in patched if id(instance) == matches[0])
            requested = operand(selected_context)
            requested["steps"] = steps
            return ledger.call("completion.integration", requested, lambda: step(steps),
                realization=lambda _: dict(integrator=xml(result, "post-step-integrator")))

        result.step, result.setRandomNumberSeed = integrate, set_seed
        patched.append((result, ("step", "setRandomNumberSeed")))
        return result

    def minimize(context, *args, **kwargs):
        requested = operand(context)
        requested.update(args=selected_value(args), kwargs=selected_value(kwargs),
                         native_internal_iteration_count="NOT_EXPOSED_BY_NATIVE_API")
        return ledger.call("completion.minimization", requested,
                           lambda: original_minimize(context, *args, **kwargs))

    mm.Context, mm.LangevinIntegrator = context, integrator
    mm.LocalEnergyMinimizer.minimize = minimize

    def restore():
        mm.Context, mm.LangevinIntegrator = original_context, original_integrator
        mm.LocalEnergyMinimizer.minimize = original_minimize
        for instance, names in reversed(patched):
            for name in names:
                delattr(instance, name)
        patched.clear()
        contexts.clear()

    return restore
