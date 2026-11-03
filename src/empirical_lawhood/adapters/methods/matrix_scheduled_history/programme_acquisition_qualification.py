# SPDX-License-Identifier: MPL-2.0
"""A distinct local acquisition root beneath one immutable global programme."""

from hashlib import sha256

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.plans import ScientificStage

from .compact_records import NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactConfig, ScheduledCompactForecastConfig, ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig, compact_identity
from .programme_composition import NATIVE_PHASES
from .programme_acquisition import _local_root, _validate_local_root


def scientific_root_validator(config, context):
    from .compact_qualification import _qualification
    from .programme_acquisition import ScheduledProgrammeAcquisitionAdmissionConfig, ScheduledProgrammeAcquisitionCollectorConfig
    declarations = tuple(row for row in context.config_inputs if type(row.record) is ScheduledProgrammeAcquisitionAdmissionConfig)
    if len(declarations) != 1:
        raise ValueError('programme wave requires one actual complete global admission declaration')
    admission = declarations[0].record
    programme, wave = admission.programme, admission.wave
    views = tuple(sorted({view.view_id for row in context.config_inputs
        if type(row.record) is ScheduledCompactPhysicalForecastConfig
        for view in (row.record.protocol.public_source.coordinate.primary_view, row.record.protocol.public_source.coordinate.fine_view)}))
    _validate_local_root(admission.scope, context.root, _local_root(admission.scope, views))
    if not {value.object_identity for value in context.root.design_inputs} <= {value.object_identity for value in context.known_design_inputs}:
        raise ValueError('acquisition root omits actual declared original global design inputs')
    _qualification(context.root, context, admission.bank.object_id, admission.bank.object_schema,
        admission.bank.object_fingerprint, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, admission.bank.object_version)
    if declarations[0].node_id != wave.wave_id+'.open':
        raise ValueError('programme wave substitutes its actual admission task')
    cases = {c.root_id: c for c in programme.cases if c.root_id in wave.root_ids}
    suffix = '-development' if programme.mode == 'E4_DEVELOPMENT' else ''
    forecast = 'forecast-calibrated' if programme.mode == 'E4_CONFIRMATION' else 'forecast'
    roles = ('prefix', 'numerical', 'measure', 'check', 'project', forecast, 'continue'+suffix,
        'full-numerical'+suffix, 'physical-forecast', 'responses'+suffix, 'response-score'+suffix)
    expected = {COMPACT_NAMESPACE+'.'+root+'.'+role for root in wave.root_ids for role in roles}
    expected |= {wave.wave_id+'.open', wave.wave_id+'.collect'}
    if {row.node_id for row in context.config_inputs} != expected:
        raise ValueError('programme wave omits complete eleven phases of each whole nine-case group or its controls')
    if type(config) is ScheduledProgrammeAcquisitionAdmissionConfig:
        if (config != admission or context.node_id != wave.wave_id+'.open' or context.stage is not ScientificStage.FREEZE
                or context.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or context.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE or context.unit_ids != wave.group_ids):
            raise ValueError('programme admission changes global frozen scope or actual blind stage')
        binding = admission.global_parent_binding
        parent_port = 'confirmation-global-parent' if programme.mode == 'E4_CONFIRMATION' else 'global-parent'
        for port, subject in ((parent_port, binding.parent.identity),
                ('global-parent-receipt', ObjectIdentity.from_record(binding.receipt.receipt_id, binding.receipt))):
            incoming = tuple(e for e in context.links if e.consumer_node_id == context.node_id and e.consumer_input_id == port)
            if len(incoming) != 1 or incoming[0].external_input_id is None:
                raise ValueError('programme wave requires its actual prior published global parent and receipt')
            qualifications = tuple(q for q in context.qualifications if q.source_id == incoming[0].external_input_id)
            if len(qualifications) != 1:
                raise ValueError('programme admission omits its actual global parent/receipt source qualification')
            _qualification(context.root, context, qualifications[0].materialization.object_id, subject.object_schema,
                subject.object_fingerprint, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, subject.object_version)
        return
    if type(config) is ScheduledProgrammeAcquisitionCollectorConfig:
        if (context.node_id != wave.wave_id+'.collect' or config.programme != programme.identity
                or config.bank != programme.bank or config.wave != wave or config.mode != programme.mode
                or config.scope != admission.scope.identity
                or context.stage is not ScientificStage.TRANSFORM or context.unit_ids != wave.group_ids
                or context.outcome_access is not (OutcomeAccess.DEVELOPMENT_VISIBLE if suffix else OutcomeAccess.EVALUATION_SEALED)
                or context.visibility_ceiling is not (VisibilityCeiling.DEVELOPMENT_ONLY if suffix else VisibilityCeiling.PROSPECTIVE)):
            raise ValueError('programme collector substitutes actual admitted scope or sealed/development boundary')
        incoming = tuple(e for e in context.links if e.consumer_node_id == context.node_id)
        endpoints = {e.consumer_input_id: e for e in incoming}
        wanted = {'bank', 'admission', *(f'products.{role.removesuffix("-development").replace("forecast-calibrated", "forecast")}.{root}'
            for root in wave.root_ids for role in roles)}
        if set(endpoints) != wanted or len(endpoints) != len(incoming):
            raise ValueError('programme collector thins its complete eleven-stage dependency census')
        if endpoints['admission'].producer_node_id != wave.wave_id+'.open' or endpoints['admission'].producer_output_id != 'product':
            raise ValueError('programme collector substitutes its actual admission dependency')
        for root in wave.root_ids:
            for role in roles:
                name = f'products.{role.removesuffix("-development").replace("forecast-calibrated", "forecast")}.{root}'
                if endpoints[name].producer_node_id != COMPACT_NAMESPACE+'.'+root+'.'+role or endpoints[name].producer_output_id != 'product':
                    raise ValueError('programme collector substitutes an original phase terminal')
        return
    if type(config) not in (ScheduledCompactConfig, ScheduledCompactForecastConfig,
            ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig):
        raise ValueError('programme wave receives an unsupported actual v2 phase configuration')
    case = cases.get(config.root_id)
    role = config.operation if hasattr(config, 'operation') else 'physical-forecast'
    if case is None or role not in roles or context.node_id != COMPACT_NAMESPACE+'.'+case.root_id+'.'+role:
        raise ValueError('programme wave substitutes an original case or operation identity')
    from .compact_bindings import PHASES
    from .operation_bindings import phase_access, phase_visibility
    phase = next(p for p in PHASES if p[0] == role)
    if (context.stage is not phase[3] or context.outcome_access is not phase_access(role)
            or context.visibility_ceiling is not phase_visibility(role)):
        raise ValueError('programme wave changes an original scientific stage or outcome boundary')
    incoming = tuple(e for e in context.links if e.consumer_node_id == context.node_id)
    expected_ports = {'admission' if name == 'commitment' else name for name, _ in phase[1] if name != 'streams'}
    if any(name == 'streams' for name, _ in phase[1]):
        from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES
        expected_ports.update('streams.'+purpose for purpose in HISTORY_PURPOSES)
        if role.startswith('responses'):
            expected_ports.update('streams.future.'+purpose for purpose in HISTORY_PURPOSES)
    if {e.consumer_input_id for e in incoming} != expected_ports or len(incoming) != len(expected_ports):
        raise ValueError('programme wave changes its complete actual phase input census')
    if context.unit_ids != (case.independent_group_id,):
        raise ValueError('programme wave treats coordinate cases as independent units')
    if type(config) in (ScheduledCompactConfig, ScheduledCompactResponseConfig):
        source = config.source
        if (config.bank != programme.bank or compact_identity(source) != case.source
                or source.coordinate != case.coordinate or source.root.root.independent_group_id != case.independent_group_id
                or source.root.root.role.value != case.role
                or sha256(canonical_json_bytes(source.root.streams)).hexdigest() != case.streams_sha256):
            raise ValueError('programme wave substitutes original source, stream or shared bank identities')
        _qualification(context.root, context, source.source_id, source.SCHEMA, source.fingerprint(),
            OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, source.VERSION)
    else:
        public = config.public_source if type(config) is ScheduledCompactForecastConfig else config.protocol.public_source
        if (public.source != case.source or public.root.root_id != case.root_id
                or public.root.independent_group_id != case.independent_group_id
                or public.root.role.value != case.role or public.reservation != programme.reservation
                or public.allocation != programme.allocation
                or ObjectIdentity.from_record(public.coordinate.coordinate_id, public.coordinate) != case.coordinate
                or ObjectIdentity.from_record('public.'+case.root_id, public) not in
                    {d.object_identity for d in context.root.design_inputs}):
            raise ValueError('programme predictor substitutes its original public scientific source')
        if type(config) is ScheduledCompactForecastConfig and config.design != programme.forecast_design:
            raise ValueError('programme predictor substitutes its original presealed design')
        if any(e.consumer_input_id in ('bank', 'source', 'allocation', 'selection', 'checkpoint', 'provenance', 'admission')
                or e.consumer_input_id.startswith('streams.') for e in context.links if e.consumer_node_id == context.node_id):
            raise ValueError('programme predictor receives protected source/admission/future inputs')
    if role in NATIVE_PHASES:
        if not context.complete_unit_census or context.selected_unit_ids != wave.group_ids:
            raise ValueError('programme native phase thins the admitted whole-group census')
        links = tuple(e for e in context.links if e.consumer_node_id == context.node_id and e.consumer_input_id == 'admission')
        if len(links) != 1 or links[0].producer_node_id != wave.wave_id+'.open' or links[0].producer_output_id != 'product':
            raise ValueError('programme native phase loses its real typed admission dependency')
