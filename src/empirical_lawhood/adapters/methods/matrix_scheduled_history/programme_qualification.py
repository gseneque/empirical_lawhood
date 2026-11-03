# SPDX-License-Identifier: MPL-2.0
"""Software conformance of bounded programme declarations, without authority.

This checks installed v2 contracts and frozen declarations. It does not call
the old scientific-root compiler on a subset, fabricate its context, or prove
issued programme execution. Separate runtime owners check actual collector
providers; this pure declaration proof does not establish their execution.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord

from .compact_bindings import operation_factories
from .compact_records import NAMESPACE, ScheduledCompactBank, compact_native_contract
from .source_index import ScheduledSourceIndex
from .programme_composition import (
    NATIVE_PHASES, ScheduledProgrammeNativeContract, ScheduledProgrammeWavePlan,
    compile_programme_wave, phase_roles,
)
from .programme_records import validate_programme_bank


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWaveConformance(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-conformance'
    plan: ObjectIdentity
    phase_task_count: int
    native_task_count: int
    collector_terminal_count: int
    existing_phase_provider_count: int
    collector_provider_available: bool = False
    issued_execution_proved: bool = False
    scientific_authority: str = 'NONE'

    def __post_init__(self):
        if (self.plan.object_schema != ScheduledProgrammeWavePlan.SCHEMA
                or any(type(n) is not int or n < 1 for n in (self.phase_task_count, self.native_task_count,
                    self.collector_terminal_count, self.existing_phase_provider_count))
                or self.collector_provider_available is not False or self.issued_execution_proved is not False
                or self.scientific_authority != 'NONE'):
            raise ValueError('programme declaration conformance cannot create provider/execution/scientific authority')


def validate_programme_wave(plan, programme, bank, template_bytes):
    """Reauthenticate exact bytes and independently check installed contracts."""
    if type(plan) is not ScheduledProgrammeWavePlan or type(bank) is not ScheduledCompactBank:
        raise ValueError('programme conformance requires exact typed wave and original bank')
    validate_programme_bank(programme, bank)
    if plan.programme != programme.identity or plan.bank != programme.bank or plan.wave not in programme.waves:
        raise ValueError('programme wave substitutes its global scope or whole-group partition')
    owners = tuple(sorted((owner, operation.node_id) for operation in plan.operations for owner in operation.obligation_ids))
    budgets = {operation.node_id: operation.resource_budget for operation in plan.operations}
    rebuilt, _ = compile_programme_wave(programme=programme, bank=bank, wave_id=plan.wave.wave_id,
        proof_owners=owners, operational_budgets=budgets, template_bytes=template_bytes)
    if rebuilt != plan:
        raise ValueError('programme wave changes exact source/configuration/phase/link/parent/native closure')

    factories = {f.registration.selection: f for f in operation_factories()}
    operations = {o.node_id: o for o in plan.operations}
    external = {e.input_id: e for e in plan.external_inputs}
    registrations, native = {}, []
    index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
        specification=bank.specification, provenances=bank.provenances)
    roots = {s.root_id: index.resolve(s) for s in bank.sources if s.root_id in plan.wave.root_ids}
    expected_tasks = {NAMESPACE+'.'+root+'.'+role for root, source in roots.items()
        for role in phase_roles(source, bank.forecast_design)}
    if set(operations) != expected_tasks:
        raise ValueError('programme wave drops or adds an original case phase')
    for operation in plan.operations:
        factory = factories.get(operation.selection)
        if factory is None or factory.manifest.capability_key != operation.selection.capability_key:
            raise ValueError('programme wave has no exact installed v2 phase provider declaration')
        registration = factory.registration
        config = decode_canonical_bytes(operation.config_payload.encode(), registration.config_record_type,
            maximum_bytes=4*1024**2)
        role = operation.selection.capability_key.rsplit('.', 1)[-1]
        source = roots.get(config.root_id)
        if (source is None or operation.node_id != NAMESPACE+'.'+config.root_id+'.'+role
                or config.config_id != operation.config_id
                or registration.scientific_unit_ids(config) != (source.root.root.independent_group_id,)
                or not registration.resource_ceiling.contains(operation.resource_budget)):
            raise ValueError('programme wave changes existing phase identity, complete group or resource declaration')
        registrations[operation.node_id] = registration
        if role in NATIVE_PHASES:
            if not registration.native_effect or not registration.complete_unit_census:
                raise ValueError('programme wave erases native complete-unit declarations')
            configuration, task, native_operation, operands = compact_native_contract(source, role, bank=bank)
            if configuration != operation.config_identity:
                raise ValueError('programme wave changes original native configuration bytes')
            native.append(ScheduledProgrammeNativeContract(task, config.root_id, source.root.root.independent_group_id,
                role, configuration, native_operation, operands, registration.native_effect_slot_ids(config)))
        elif registration.native_effect:
            raise ValueError('programme wave introduces undeclared native science')
    if tuple(sorted(native, key=lambda n: n.task_id)) != plan.native_contracts:
        raise ValueError('programme wave changes exact existing native task/operation/operand census')

    # Each port is checked against installed registrations, including actual
    # output IDs, arrays, stream multiplicities, schema and media type. This
    # supplements exact recomposition without manufacturing a root context.
    for operation in plan.operations:
        registration = registrations[operation.node_id]
        incoming = tuple(e for e in plan.links if e.consumer_node_id == operation.node_id)
        matched = set()
        for port in registration.input_ports:
            links = tuple(e for e in incoming if port.matches(e.consumer_input_id))
            if len(links) < port.minimum_count or port.maximum_count is not None and len(links) > port.maximum_count:
                raise ValueError('programme wave omits a complete installed phase port census')
            for link in links:
                matched.add(link.edge_id)
                if link.external_input_id is not None:
                    actual = external[link.external_input_id]
                    schema, media, maximum = actual.payload_schema, actual.media_type, actual.maximum_size_bytes
                else:
                    outputs = registrations[link.producer_node_id].outputs
                    actual = next((o for o in outputs if o.output_id == link.producer_output_id), None)
                    if actual is None:
                        raise ValueError('programme wave substitutes an original dependency output ID')
                    schema, media, maximum = actual.payload_schema, actual.media_type, None
                if schema != port.payload_schema or media != port.media_type:
                    raise ValueError('programme wave substitutes an installed phase input schema/media contract')
                if port.maximum_size_bytes is not None and maximum is not None and maximum > port.maximum_size_bytes:
                    raise ValueError('programme wave widens an installed bounded scientific input')
        if matched != {e.edge_id for e in incoming}:
            raise ValueError('programme wave adds an undeclared installed phase input')
        role = operation.selection.capability_key.rsplit('.', 1)[-1]
        if role in ('forecast', 'forecast-calibrated', 'physical-forecast'):
            if any(e.consumer_input_id in ('source', 'bank', 'allocation', 'selection', 'checkpoint', 'provenance')
                    or e.consumer_input_id.startswith('streams.') for e in incoming):
                raise ValueError('programme predictor exposes protected native source/future inputs')
    expected_terminals = {}
    for root, source in roots.items():
        roles = phase_roles(source, bank.forecast_design)
        for port, role in (('forecasts', roles[5]), ('scores', roles[10]), ('full-numericals', roles[7])):
            expected_terminals[port+'.'+root] = NAMESPACE+'.'+root+'.'+role
    if ({e.consumer_input_id: e.producer_node_id for e in plan.collector_inputs} != expected_terminals
            or any(e.consumer_node_id != plan.collector_task_id or e.producer_output_id != 'product'
                or e.external_input_id is not None or e.scientific_role != 'OUTCOME' for e in plan.collector_inputs)):
        raise ValueError('programme wave collector omits exact original forecast/score/full-numerical terminals')
    return ScheduledProgrammeWaveConformance(plan.identity, len(plan.operations), len(plan.native_contracts),
        len(plan.collector_inputs), len({o.selection for o in plan.operations}))
