# SPDX-License-Identifier: MPL-2.0
"""Selected exposed child; no native engine, scientific inputs or qualification."""

import json
import os
from pathlib import Path

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurablePreparationPlan
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_preparation import DurableCallLedger, complete_unit
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import freeze


def exposed_child(progress, invocation):
    data = json.loads(invocation.read())
    plan = decode_canonical_bytes(data["plan"].encode(), DurablePreparationPlan, maximum_bytes=None)
    selected = tuple(decode_canonical_bytes(row.encode(), NativeSubworkDefinition, maximum_bytes=None)
                     for row in data["definitions"])
    freeze(progress, selected)
    if data["phase"] == "before-begin":
        os._exit(81)
    attempted = set((*plan.attempted_geometry_ids, *plan.attempted_model_ids))
    for definition in selected:
        if definition.subwork_id not in attempted:
            continue
        entry = progress.begin(definition)
        if data["phase"] == "after-begin":
            os._exit(82)
        progress.contact(entry)
        directory = Path(plan.workdir) / definition.subwork_id
        directory.mkdir()
        if data["phase"] == "after-contact":
            os._exit(83)
        ledger = DurableCallLedger(progress, plan, Path(plan.workdir), entry, directory)
        def actual():
            (directory / "full-return.bin").write_bytes(bytes(range(256)) * 1000)
            return {"returncode": data["returncode"]}
        result = ledger.call("exposed.preparation-return", {"scope": "software-only-full-return"},
                             actual, realization=lambda value: value)
        if data["phase"] == "after-call-completion":
            os._exit(84)
        succeeded = result["returncode"] == 0
        complete_unit(progress, plan, entry, Path(plan.workdir), directory, ledger,
                      succeeded=succeeded, error=None if succeeded else "disclosed exposed adverse return")
        if data["phase"] == "after-unit-completion":
            os._exit(85)
