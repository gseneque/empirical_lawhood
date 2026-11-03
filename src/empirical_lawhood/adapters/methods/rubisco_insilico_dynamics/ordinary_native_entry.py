# SPDX-License-Identifier: MPL-2.0
"""Cold specialist entry for the unchanged full-model preparation science."""

import json


def _inputs(invocation, expected_parent, contract):
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import StructuralInventory, AssemblyCoordinates
    from . import contracts as c, science
    from .durable_native_entry import _prepared_embedded_work
    from .ordinary_preparation import launch_definition
    from .operation_bindings import native_effect_slot_ids

    data = json.loads(invocation.read())
    if set(data) != {"config", "source", "nomination", "inventory", "coordinates", "definition"}:
        raise ValueError("original preparation changes its complete sealed operand census")
    types = {"config": c.PreparationOperationConfig, "source": c.PreparationSelection,
        "nomination": NominationDossier, "inventory": StructuralInventory, "coordinates": AssemblyCoordinates,
        "definition": NativeSubworkDefinition}
    values = {name: decode_canonical_bytes(data[name].encode(), kind, maximum_bytes=None) for name, kind in types.items()}
    config, definition = values["config"], values["definition"]
    identities = tuple(c.identity(values[name]) for name in ("source", "nomination", "inventory", "coordinates"))
    if (config.operation != "prepare" or config.source != values["source"]
            or config.prior_nomination_scope != values["nomination"].scope
            or config.operands != tuple(sorted(identities, key=lambda row: row.object_id))
            or definition != launch_definition(config, expected_parent, contract.implementation)):
        raise ValueError("original preparation changes its exact nomination/source/config/current launcher scope")
    science.validate_source(values["source"], values["nomination"], values["inventory"], values["coordinates"])
    work = _prepared_embedded_work(contract, expected_parent, config, (definition,),
        tuple(values[name] for name in ("source", "nomination", "inventory", "coordinates")),
        scientific_unit_ids=(c.UNIT,), native_effect_slot_ids=native_effect_slot_ids(config),
        record_identities=(ObjectIdentity.from_record(contract.config.artifact_id, config), *identities))
    return config, values, work


def preflight_selected_child(*, invocation, expected_parent, prepared_contract):
    import importlib
    from . import science
    from .durable_native_entry import authenticate_engine_stock, authenticate_loaded_engine_modules, refuse_external_network
    config, values, work = _inputs(invocation, expected_parent, prepared_contract)
    stock = science.validate_stock(config.source.source_members)
    inventory = authenticate_engine_stock(stock)
    refuse_external_network(None)
    for name in ("numpy", "scipy", "openmm", "parmed", "pdbfixer"):
        importlib.import_module(name)
    authenticate_loaded_engine_modules(inventory)
    return work


def selected_child(progress, invocation):
    from pathlib import Path
    from . import native
    from .durable_native_entry import refuse_external_network
    contract = invocation.prepared_invocation
    if contract is None:
        raise ValueError("SOFTWARE: original preparation requires its complete actual specialist contract")
    config, values, _ = _inputs(invocation, progress.parent_contact, contract)
    root = Path(config.source.native_workdir)
    refuse_external_network(None)
    native._prepare_worker(values["source"], values["nomination"], values["inventory"], values["coordinates"], root)
