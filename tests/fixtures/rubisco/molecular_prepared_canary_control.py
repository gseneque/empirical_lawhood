# SPDX-License-Identifier: MPL-2.0
"""Tiny declared molecular control composition through the accepted TP1 owner.

The root selects the guarded plane, actual interpreter/stock and ordinary
contact. This composition performs no native effect and adds no launcher.
"""

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus, DurableUnitReturn
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy.raw_coupled_return import CoupledEvaluationRequest, return_outputs
from empirical_lawhood.infrastructure.prepared_native_invocation import NativeInputPublication, prepare_native_invocation, validate_prepared_native_invocation
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.native_effects import NativeEffectContact


def prepare_control(plane, selected, provenance, *, run_id, task_id, contact_id,
                    execution_plan, task_identity, visibility, access, phase="success"):
    """Return the joined ports/parent/definitions and exact frozen invocation."""
    if phase not in ("success", "after-completion"):
        raise ValueError("tiny molecular control has a closed exposed lifecycle menu")
    if (provenance.package_sources != selected.code_sources
            or provenance.dependency_lock_sha256 != selected.dependency_lock_sha256):
        raise ValueError("molecular control changes the selected code/lock provenance")
    request = CoupledEvaluationRequest(selected.config_id + ".energy-gradient.request", selected.identity,
        selected.identity, selected.identity, provenance.identity, 8)
    bundle = prepare_native_invocation(plane, visibility=visibility, access=access, publications=(
        NativeInputPublication(selected.config_id, selected), NativeInputPublication(request.request_id, request),
        NativeInputPublication(provenance.identity.object_id, provenance)))
    try:
        parent = NativeEffectContact(run_id, task_id, contact_id, execution_plan, task_identity,
            provenance.observed_git_head, bundle.input_materialization_ids, ())
        outputs = (json_output("files.census", DurableRawFileCensus), raw_output("files.raw"), json_output("unit.return", DurableUnitReturn))
        definitions = tuple(bundle.definition(subwork_id=name, operation_id="development.molecular-interface-canary",
            parent_contact=parent, configuration=request.identity if name.endswith("energy-gradient") else selected.identity,
            sources=(selected.identity,), provenance=provenance,
            outputs=tuple(sorted(outputs + (return_outputs() if name.endswith("energy-gradient") else ()), key=lambda row: row.output_id)))
            for name in ("molecular.canary.energy-gradient", "molecular.canary.preparation"))
        validate_prepared_native_invocation(plane, bundle, definitions, visibility=visibility, access=access)
        invocation = canonical_json_bytes(dict(definitions=tuple(row.canonical_bytes().decode() for row in definitions),
            selection=selected.canonical_bytes().decode(), request=request.canonical_bytes().decode(),
            provenance=provenance.canonical_bytes().decode(), phase=phase))
        return bundle, parent, definitions, request, invocation
    except BaseException:
        bundle.close()
        raise
