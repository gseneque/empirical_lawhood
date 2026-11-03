# SPDX-License-Identifier: MPL-2.0
"""Cold read of the original registered history/seal route; never replay.

The caller supplies an authorized plane. Candidate custody authenticates bytes,
not issue, execution, qualification or scientific admission. Blind prefix and
later sealed/development Native stores retain their original separate scopes.
"""

from dataclasses import dataclass
from types import SimpleNamespace

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from empirical_lawhood.runtime.plans import CandidateExecutionPlan, EnvelopeExecutionPlan, ExecutionPlan, PlanLane

from . import science
from .commitment import authenticate_prior_publications, committed
from .continuation import ScheduledFullHistory
from .forecast import ScheduledForecastConfig, ScheduledForecastFeature, ScheduledPublicSource, causal_feature, forecast_public
from .operation_bindings import BLIND, NAMESPACE, PHASES, PROSPECTIVE, phase_access, phase_visibility
from .records import ScheduledConfig, identity
from .source_index import ScheduledSourceIndex, ScheduledNativeSourceContext, ResolvedScheduledSource
from .retained import _manifest, _read_output


@dataclass(frozen=True, slots=True)
class _RetainedRoute:
    namespace: str
    phases: tuple
    declaration: object
    commitment: object
    source: object
    shared: object
    compact: bool = False

    def task_id(self, role):
        return self.namespace+'.commit' if role == 'commit' else self.namespace+'.'+self.source.root_id+'.'+role

    def config(self, role):
        name = 'config.'+self.task_id(role)
        if role == 'commit':
            return self.declaration
        if self.compact:
            from .compact_records import (ScheduledCompactConfig, ScheduledCompactForecastConfig,
                ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig, compact_identity)
            bank = compact_identity(self.shared)
            if role in ('forecast', 'forecast-calibrated'):
                return ScheduledCompactForecastConfig(name, ScheduledPublicSource.from_source(self.source),
                    ObjectIdentity.from_record(self.commitment.forecast_design.design_id, self.commitment.forecast_design),
                    role == 'forecast-calibrated')
            if role == 'physical-forecast':
                return ScheduledCompactPhysicalForecastConfig(name, self.commitment.response_selection.validate_source(self.source)[0])
            if role.startswith('response'):
                return ScheduledCompactResponseConfig(name, role, self.source.reference, self.commitment.response_selection.identity, bank)
            return ScheduledCompactConfig(name, role, self.source.reference, bank)
        from .forecast import ScheduledCalibratedForecastConfig
        from .response_selection import ScheduledPhysicalForecastConfig, ScheduledResponseConfig
        if role in ('forecast', 'forecast-calibrated'):
            cls = ScheduledCalibratedForecastConfig if role == 'forecast-calibrated' else ScheduledForecastConfig
            return cls(name, ScheduledPublicSource.from_source(self.source), self.commitment.forecast_design)
        if role == 'physical-forecast':
            return ScheduledPhysicalForecastConfig(name, self.commitment.response_selection.validate_source(self.source)[0])
        if role.startswith('response'):
            return ScheduledResponseConfig(name, role, self.source.reference,
                self.commitment.response_selection.identity, identity(self.commitment))
        return ScheduledConfig(name, role, self.source.reference, identity(self.commitment))

    def native_context(self, role='prefix'):
        return ScheduledNativeSourceContext(self.source, self.config(role), self.shared)

    def authenticate(self, plane):
        if self.compact:
            from .compact_records import authenticate_prior_publications as authenticate_compact
            authenticate_compact(plane, (SimpleNamespace(record=self.declaration),))
        else:
            authenticate_prior_publications(plane, (SimpleNamespace(record=self.declaration),))

    def committed(self):
        if self.compact:
            from .compact_records import compact_committed
            return compact_committed(self.declaration)
        return committed(self.declaration)


def _route(commitment, root_id, source=None):
    from .commitment import ScheduledCommitmentConfig
    from .compact_records import NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactCommitmentConfig
    if type(commitment) is ScheduledCompactCommitmentConfig:
        from .compact_bindings import PHASES as COMPACT_PHASES
        descriptor = next((s for s in commitment.bank.sources if s.root_id == root_id), None)
        if descriptor is None or root_id not in commitment.bank.selected_root_ids:
            raise ValueError('compact retained case is outside its complete selected bank')
        index = ScheduledSourceIndex.from_shared(reservation=commitment.bank.reservation,
            specification=commitment.bank.specification, provenances=commitment.bank.provenances)
        expected_source = index.resolve(descriptor)
        if source is not None and (type(source) is not ResolvedScheduledSource
                or source.reference != expected_source.reference):
            raise ValueError('compact retained source differs from its actual selected bank')
        return _RetainedRoute(COMPACT_NAMESPACE, COMPACT_PHASES, commitment,
            commitment.bank.commitment_config(), expected_source, commitment.bank, True)
    if type(commitment) is not ScheduledCommitmentConfig:
        raise ValueError('scheduled retained route requires its exact current shared commitment')
    reference = next((s for s in commitment.sources if s.root_id == root_id), None)
    if reference is None or root_id not in commitment.selected_root_ids:
        raise ValueError('scheduled retained case is outside complete selected commitment')
    index = ScheduledSourceIndex.from_shared(reservation=commitment.reservation,
        specification=commitment.specification, provenances=commitment.provenances)
    expected_source = index.resolve(reference)
    if source is not None and (type(source) is not ResolvedScheduledSource or source.reference != reference):
        raise ValueError('scheduled retained source differs from its actual selected commitment')
    from .response_bindings import RESPONSE_PHASES
    return _RetainedRoute(NAMESPACE, (*PHASES, *RESPONSE_PHASES), commitment, commitment, expected_source, commitment)


def _shared_inputs(plane, task, manifests, route, role):
    """Join bounded references to the actual shared scientific input bytes."""
    source, bank = route.source, route.shared
    expected = {'bank': bank if route.compact else None,
        'commitment-config': None if route.compact else route.commitment,
        'source': source.reference, 'allocation': source.allocation,
        'selection': source.specification.selection, 'coordinate': source.coordinate, 'provenance': source.provenance,
        'forecast-design': bank.forecast_design, 'audit': bank.audit, 'model': bank.forecast_design.model_record,
        'training': bank.forecast_design.training_record, 'criterion': bank.forecast_design.criterion_record,
        'prior-census': bank.audit.census, 'response-selection': bank.response_selection}
    expected.update(('source.'+s.root_id, s) for s in bank.sources)
    expected.update(('prior-coordinates.'+c.coordinate_id, c) for c in bank.audit.prior_scheduled_coordinates)
    expected.update(('streams.'+s.purpose, s) for s in source.root.streams)
    if role.startswith('responses'):
        _, panels = bank.response_selection.validate_source(source)
        expected.update(('streams.future.'+s.purpose, s) for p in panels if p.role == 'INDEPENDENT_FUTURE' for s in p.streams)
    declared = {port for port, cls in next(p for p in route.phases if p[0] == role)[1] if cls is not None}
    required = {name for name, record in expected.items() if record is not None
        and (name in declared or name.split('.', 1)[0] in declared)
        and not (role == 'commit' and name == 'source')
        and not (role != 'commit' and name.startswith('source.'))}
    received = {}
    for spec in task.external_inputs:
        name = spec.input_id
        if name == 'config' or name == 'calibration' or name not in declared and name.split('.', 1)[0] not in declared:
            continue
        record = expected.get(name)
        if record is None:
            raise ValueError('compact retained input changes its complete declared scientific operand')
        matches = tuple(m for m in manifests if m.logical.logical_artifact_id == spec.logical_artifact_id)
        if (len(matches) != 1 or matches[0].logical.payload_schema != record.SCHEMA
                or matches[0].logical.content_sha256 != record.fingerprint()
                or matches[0].materialization.size_bytes != len(record.canonical_bytes())):
            raise ValueError('compact retained input substitutes its original shared scientific bytes')
        raw = read_bounded_bytes(plane.root.resolve(matches[0].materialization.relative_path, for_write=False),
            maximum_bytes=matches[0].materialization.size_bytes)
        if raw != record.canonical_bytes():
            raise ValueError('compact retained input changes exact canonical shared operand content')
        # The current typed record was validated at the shared boundary. Exact
        # canonical-byte equality joins this physical operand without decoding
        # its entire population again for each retained phase.
        received[name] = record
    if not required <= set(received):
        raise ValueError('compact retained phase omits its exact shared source/stream operand census')
    if 'bank' in declared and received.get('bank') != bank:
        raise ValueError('compact retained phase omits its actual complete shared bank')
    if 'source' in declared and role != 'commit' and received.get('source') != source.reference:
        raise ValueError('retained source changes its exact shared-parent and root binding')


def _selected_receipt(plane, store, plan, task, attempt, role):
    q = store.read(plan.source_plan.object_id, task.task_id, attempt)
    if (q is None or q.operational_status is not OperationalStatus.SUCCEEDED
            or q.implementation_commit != plan.implementation_commit
            or task.capability.requested_outcome_access is not phase_access(role)
            or len(q.output_logical_artifacts) != len(task.outputs)):
        raise ValueError('scheduled selected phase lacks original known successful ordinary receipt')
    actual = {a.logical_artifact_id: a for a in q.output_logical_artifacts}
    physical = {p.logical_artifact_id: p for p in q.output_materializations}
    if (set(actual) != {o.logical_artifact_id for o in task.outputs} or set(physical) != set(actual)
            or any((actual[o.logical_artifact_id].payload_schema, actual[o.logical_artifact_id].profile,
                    actual[o.logical_artifact_id].media_type, actual[o.logical_artifact_id].outcome_access,
                    actual[o.logical_artifact_id].visibility_ceiling, physical[o.logical_artifact_id].relative_path) !=
                   (o.payload_schema, o.profile, o.media_type, phase_access(role), phase_visibility(role), o.relative_path)
                for o in task.outputs)):
        raise ValueError('scheduled ordinary output substitutes original complete plan/media/path/access scope')
    bound = task.capability.requested_resources.output_bytes
    if bound is not None and sum(p.size_bytes for p in q.output_materializations) > bound:
        raise ValueError('scheduled receipt exceeds explicit operational output allowance')
    return q


def _inputs(plane, task, receipt, manifests, preceding, config):
    for m in manifests:
        plane.verify_manifest(m)
    if (tuple(sorted(m.materialization.materialization_id for m in manifests)) != receipt.input_materialization_ids
            or len({m.logical.logical_artifact_id for m in manifests}) != len(manifests)):
        raise ValueError('scheduled phase changes original complete input materialization census')
    actual = {m.logical.logical_artifact_id: m for m in manifests}
    expected = {e.logical_artifact_id for e in task.external_inputs} | {
        e.operational_logical_artifact_id for e in task.scientific_inputs if e.producer_task_id is not None}
    if set(actual) != expected:
        raise ValueError('scheduled phase drops or adds original declared scientific inputs')
    for e in task.external_inputs:
        m = actual[e.logical_artifact_id]
        if (m.logical.payload_schema != e.expected_payload_schema or m.logical.content_sha256 != e.expected_content_sha256
                or e.expected_media_type is not None and m.logical.media_type != e.expected_media_type
                or e.expected_size_bytes is not None and m.materialization.size_bytes != e.expected_size_bytes
                or e.expected_outcome_access is not None and m.logical.outcome_access is not e.expected_outcome_access
                or e.expected_visibility_ceiling is not None and m.logical.visibility_ceiling is not e.expected_visibility_ceiling):
            raise ValueError('scheduled phase changes original exact external descriptors')
    config_inputs = tuple(m for m in manifests if m.logical.logical_artifact_id == task.capability.config.artifact_id)
    if (len(config_inputs) != 1 or config_inputs[0].logical.content_sha256 != config.fingerprint()
            or task.capability.config.config_id != config.config_id or task.capability.config.config_schema != config.SCHEMA
            or task.capability.config.content_sha256 != config.fingerprint()):
        raise ValueError('scheduled selected plan changes actual original phase config')
    deps = {q.task_id: q for q in preceding}
    if task.dependency_task_ids != tuple(sorted(deps)):
        raise ValueError('scheduled phase changes original ordinary dependency tasks')
    for e in task.scientific_inputs:
        if e.producer_task_id is None:
            continue
        m, q = actual[e.operational_logical_artifact_id], deps.get(e.producer_task_id)
        if (q is None or m.logical not in q.output_logical_artifacts or m.materialization not in q.output_materializations
                or (m.logical.payload_schema, m.logical.media_type, m.logical.outcome_access, m.logical.visibility_ceiling) !=
                   (e.payload_schema, e.media_type, e.outcome_access, e.visibility_ceiling)
                or e.maximum_size_bytes is not None and m.materialization.size_bytes > e.maximum_size_bytes):
            raise ValueError('scheduled phase changes original receipt/dependency member or information scope')


def _native(plane, plan_pin, task, receipt, manifests, evidence, *, access, visibility):
    parent = evidence.definition.parent_contact
    if (parent.execution_plan != plan_pin or parent.execution_task != ObjectIdentity.from_record(task.task_id, task)
            or (parent.run_id, parent.task_id, parent.attempt_id, parent.input_materialization_ids) !=
               (receipt.run_id, receipt.task_id, receipt.attempt_id, receipt.input_materialization_ids)):
        raise ValueError('scheduled original nested native parent changes exact ordinary plan/task/run/attempt/inputs')
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=plan_pin, outcome_access=access, visibility_ceiling=visibility)
    if contacts.read(parent.run_id, parent.task_id) != parent:
        raise ValueError('scheduled native reader lacks original entered parent contact')
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts, parent_contact=parent, parent_inputs=manifests)
    roster = store.read_roster(parent)
    if roster is None or roster.subworks != (evidence.definition.identity,):
        raise ValueError('scheduled original native roster changes exact subwork census')
    found = store.inspect(evidence.definition)
    if (found.state is not NativeSubworkState.COMPLETED
            or found.receipt != evidence.receipt or found.completion != evidence.completion):
        raise ValueError('scheduled original nested completion differs; no unknown replay')
    return store


def read_history(*, plane, run_id, execution_plan, commitment, root_id, original_inputs, receipt_locators, calibration_record=None, source=None):
    """Keep all retained history and array joins in one effect-free read lifetime."""
    with plane.read_context() as reading:
        return _read_history(plane=reading, run_id=run_id, execution_plan=execution_plan,
            commitment=commitment, root_id=root_id, original_inputs=original_inputs,
            receipt_locators=receipt_locators, calibration_record=calibration_record, source=source)


def _read_history(*, plane, run_id, execution_plan, commitment, root_id, original_inputs, receipt_locators,
        calibration_record=None, source=None, selected_route=None):
    """Read nine actual original phases for one case of the committed bank.

    Prefix custody precedes forecast FREEZE; later full history is authenticated
    separately. This is raw-history proof, not pulse-response error assessment.
    """
    route = _route(commitment, root_id, source) if selected_route is None else selected_route
    source, commitment = route.source, route.commitment
    suffix = '-development' if source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else ''
    from .forecast import CALIBRATED_QUERY
    forecast_role = 'forecast-calibrated' if dict(commitment.forecast_design.source_scopes)[root_id] == CALIBRATED_QUERY else 'forecast'
    physical_roles = ('physical-forecast',) if commitment.response_selection is not None else ()
    roles = ('commit', 'prefix', 'numerical', 'measure', 'check', 'project', forecast_role, *physical_roles, 'continue'+suffix, 'full-numerical'+suffix)
    if tuple(r for r, _ in original_inputs) != roles or tuple(r for r, _ in receipt_locators) != roles:
        raise ValueError('scheduled reader requires all original phase/input/attempt locators')
    route.authenticate(plane)
    manifest = _manifest(plane, 'runs/'+run_id+'/plans/execution-plan.json')
    cls = {p.SCHEMA: p for p in (ExecutionPlan, CandidateExecutionPlan, EnvelopeExecutionPlan)}.get(manifest.logical.payload_schema)
    if cls is None:
        raise ValueError('scheduled retained plan is not a stock typed execution plan')
    plan = decode_canonical_bytes(read_bounded_bytes(plane.root.resolve(manifest.materialization.relative_path, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes), cls, maximum_bytes=None)
    if (ObjectIdentity.from_record(plan.execution_plan_id, plan) != execution_plan or plan.source_plan.object_id != run_id
            or plan.lane is not PlanLane.PROSPECTIVE or plan.implementation_commit != source.provenance.observed_git_head):
        raise ValueError('scheduled original selected plan changes run/lane/producing source')
    store, qs, tasks, products = ExternalTaskReceiptStore(plane), {}, {}, {}
    phase_inputs = dict(original_inputs)
    for role, attempt in receipt_locators:
        name = route.task_id(role)
        task = next((t for t in plan.tasks if t.task_id == name), None)
        phase = next(p for p in route.phases if p[0] == role)
        if task is None or task.capability.capability_key != route.namespace+'.'+role or task.stage is not phase[3]:
            raise ValueError('scheduled original plan substitutes actual capability/stage')
        q = _selected_receipt(plane, store, plan, task, attempt, role)
        config = route.config(role)
        if not set(task.dependency_task_ids) <= set(qs):
            raise ValueError('scheduled retained continuation lacks preceding original pre-future receipt')
        _inputs(plane, task, q, phase_inputs[role], tuple(qs[n] for n in task.dependency_task_ids), config)
        _shared_inputs(plane, task, phase_inputs[role], route, role)
        # Recheck canonical config bytes rather than only its logical digest.
        config_manifest = next(m for m in phase_inputs[role] if m.logical.logical_artifact_id == task.capability.config.artifact_id)
        raw = read_bounded_bytes(plane.root.resolve(config_manifest.materialization.relative_path, for_write=False), maximum_bytes=config_manifest.materialization.size_bytes)
        if decode_canonical_bytes(raw, type(config), maximum_bytes=None) != config:
            raise ValueError('scheduled retained phase substitutes actual config content')
        qs[name], tasks[role] = q, task
        products[role] = decode_canonical_bytes(_read_output(plane, q, schema=phase[2].SCHEMA), phase[2], maximum_bytes=None)
    q = lambda role: qs[route.task_id(role)]
    expected_commitment = route.committed()
    if type(products['commit']) is not type(expected_commitment) or products['commit'] != expected_commitment:
        raise ValueError('scheduled original freeze differs from complete actual source/audit/model commitment')
    history, numerical, witness, frames, causal, seal = (products[r] for r in roles[1:7])
    native_context = route.native_context()
    history.validate_source(source, native_context=native_context)
    native = _native(plane, execution_plan, tasks['prefix'], q('prefix'), phase_inputs['prefix'], history.native,
        access=BLIND, visibility=PROSPECTIVE)
    raw = _read_output(plane, q('prefix'), artifact=history.arrays.array_artifact)
    if (b''.join(native.iter_completed_output(history.native.definition, 'arrays')) != raw
            or b''.join(native.iter_completed_output(history.native.definition, 'checkpoint')) != history.checkpoint.canonical_bytes()):
        raise ValueError('scheduled ordinary prefix changes exact original nested archive/checkpoint bytes')
    if science.assess_prefix(source, history, science.consume_prefix(source, history.arrays, raw),
            native_context=native_context) != numerical:
        raise ValueError('scheduled original independent prefix controls changed')
    diagnostic = _read_output(plane, q('measure'), artifact=witness.arrays.array_artifact)
    if science.check_frames(source, history, numerical, witness, raw, diagnostic,
            native_context=native_context) != frames:
        raise ValueError('scheduled original raw-state eigenpair/frame witness changed')
    causal_raw = _read_output(plane, q('project'), artifact=causal.arrays.array_artifact)
    _, expected = science.causal_delivery(source, history, numerical, witness, frames, raw, diagnostic,
        artifact_id=causal.arrays.array_artifact.artifact_id, raw=causal_raw, native_context=native_context)
    feature = decode_canonical_bytes(_read_output(plane, q('project'), schema=ScheduledForecastFeature.SCHEMA), ScheduledForecastFeature, maximum_bytes=None)
    if (causal != expected or feature != causal_feature(commitment.forecast_design, source, causal, witness,
            decode_matrix_arrays(causal_raw, causal.arrays), decode_matrix_arrays(diagnostic, witness.arrays), feature_id=feature.feature_id)
            or seal != forecast_public(commitment.forecast_design, ScheduledPublicSource.from_source(source), causal, feature, seal_id=seal.seal_id, calibration_record=calibration_record)):
        raise ValueError('scheduled actual causal projection/feature/pre-future forecast seal changed')
    full, assessment = products[roles[-2]], products[roles[-1]]
    if type(full) is not ScheduledFullHistory:
        raise ValueError('scheduled continuation substitutes historical full source record')
    physical = products.get('physical-forecast')
    if physical is not None:
        from . import response_forecast
        protocol = commitment.response_selection.validate_source(source)[0]
        template_port = next(m for m in phase_inputs['physical-forecast'] if m.logical.logical_artifact_id == protocol.templates.array_artifact.artifact_id)
        template_raw = read_bounded_bytes(plane.root.resolve(template_port.materialization.relative_path, for_write=False), maximum_bytes=protocol.templates.array_artifact.size_bytes)
        frozen_raw = _read_output(plane, q('physical-forecast'), artifact=physical.arrays.array_artifact)
        if response_forecast.forecast(protocol, causal, decode_matrix_arrays(causal_raw, causal.arrays),
                decode_matrix_arrays(template_raw, protocol.templates), artifact_id=physical.arrays.array_artifact.artifact_id,
                retained=decode_matrix_arrays(frozen_raw, physical.arrays), raw=frozen_raw)[1] != physical:
            raise ValueError('scheduled continuation changes exact original physical pre-future forecast')
    full.validate_source(source, history, causal, seal, physical, native_context=native_context)
    native = _native(plane, execution_plan, tasks[roles[-2]], q(roles[-2]), phase_inputs[roles[-2]], full.native,
        access=phase_access(roles[-2]), visibility=phase_visibility(roles[-2]))
    full_raw = _read_output(plane, q(roles[-2]), artifact=full.arrays.array_artifact)
    if b''.join(native.iter_completed_output(full.native.definition, 'arrays')) != full_raw:
        raise ValueError('scheduled ordinary full archive changes exact original native bytes')
    values = decode_matrix_arrays(full_raw, full.arrays)
    before = science.consume_prefix(source, history.arrays, raw)
    if any(not (values[n][:len(a)] == a).all() for n, a in before.items()):
        raise ValueError('scheduled full history changes actual completed original prefix rows')
    if science.assess_full(source, full, values) != assessment:
        raise ValueError('scheduled full independent numerical controls changed')
    return products


def read_response(*, plane, run_id, execution_plan, commitment, root_id, original_inputs, receipt_locators, calibration_record=None, source=None):
    """Keep prefix, continuation and response custody in one effect-free read lifetime."""
    with plane.read_context() as reading:
        return _read_response(plane=reading, run_id=run_id, execution_plan=execution_plan,
            commitment=commitment, root_id=root_id, original_inputs=original_inputs,
            receipt_locators=receipt_locators, calibration_record=calibration_record, source=source)


def _read_response(*, plane, run_id, execution_plan, commitment, root_id, original_inputs, receipt_locators, calibration_record=None, source=None):
    """Original ordinary/native custody plus independent full scheduled response.

    All raw-prefix/full-history clocks and frame equations are checked first;
    the physical forecast is then rederived from its retained spectral witnesses
    without a producer, followed by all48 literal Native path controls and240
    signed receiver cells. No issue, contact, noise replay or eigensolve occurs.
    """
    from . import response_forecast, response_science
    from .response_records import ScheduledResponseForecast, ScheduledResponseNative, ScheduledResponseScore
    route = _route(commitment, root_id, source)
    source, scientific_commitment = route.source, route.commitment
    suffix = '-development' if source.evidence_role == 'EXPOSED_DEVELOPMENT_NONPROMOTABLE' else ''
    extras = ('physical-forecast', 'responses'+suffix, 'response-score'+suffix)
    if tuple(r for r, _ in original_inputs)[-2:] != extras[-2:] or tuple(r for r, _ in receipt_locators)[-2:] != extras[-2:]:
        raise ValueError('scheduled response reader omits complete original three-phase pulse evidence')
    products = _read_history(plane=plane, run_id=run_id, execution_plan=execution_plan, commitment=commitment,
        root_id=root_id, original_inputs=original_inputs[:-2], receipt_locators=receipt_locators[:-2], calibration_record=calibration_record,
        source=source, selected_route=route)
    manifest = _manifest(plane, 'runs/'+run_id+'/plans/execution-plan.json')
    cls = {p.SCHEMA: p for p in (ExecutionPlan, CandidateExecutionPlan, EnvelopeExecutionPlan)}[manifest.logical.payload_schema]
    plan = decode_canonical_bytes(read_bounded_bytes(plane.root.resolve(manifest.materialization.relative_path, for_write=False),
        maximum_bytes=manifest.materialization.size_bytes), cls, maximum_bytes=None)
    store, inputs, locators = ExternalTaskReceiptStore(plane), dict(original_inputs), dict(receipt_locators)
    receipts = {}
    for role, attempt in receipt_locators:
        task_id = route.task_id(role)
        q = store.read(run_id, task_id, attempt)
        if q is None:
            raise ValueError('scheduled response reader lacks original successful ordinary receipt')
        receipts[task_id] = q
    protocol, panels = scientific_commitment.response_selection.validate_source(source)
    tasks = {}
    for role in extras:
        task = next(t for t in plan.tasks if t.task_id == route.task_id(role))
        phase = next(p for p in route.phases if p[0] == role)
        if task.capability.capability_key != route.namespace+'.'+role or task.stage is not phase[3]:
            raise ValueError('scheduled retained pulse plan substitutes frozen actual phase')
        # The receipt verifier only needs the same five-field phase/output shape.
        q = _selected_receipt(plane, store, plan, task, locators[role], role)
        config = route.config(role)
        _inputs(plane, task, q, inputs[role], tuple(receipts[t] for t in task.dependency_task_ids), config)
        _shared_inputs(plane, task, inputs[role], route, role)
        config_manifest = next(m for m in inputs[role] if m.logical.logical_artifact_id == task.capability.config.artifact_id)
        config_raw = read_bounded_bytes(plane.root.resolve(config_manifest.materialization.relative_path, for_write=False),
            maximum_bytes=config_manifest.materialization.size_bytes)
        if decode_canonical_bytes(config_raw, type(config), maximum_bytes=None) != config:
            raise ValueError('scheduled retained pulse substitutes actual canonical config content')
        products[role] = decode_canonical_bytes(_read_output(plane, q, schema=phase[2].SCHEMA), phase[2], maximum_bytes=None)
        tasks[role] = task
    history, causal = products['prefix'], products['project']
    physical, responses, score = (products[r] for r in extras)
    if (type(physical) is not ScheduledResponseForecast or type(responses) is not ScheduledResponseNative or type(score) is not ScheduledResponseScore):
        raise ValueError('scheduled cold response substitutes old P or other scientific records')
    def receipt(role):
        return receipts[route.task_id(role)]
    prefix_raw = _read_output(plane, receipt('prefix'), artifact=history.arrays.array_artifact)
    prefix = science.consume_prefix(source, history.arrays, prefix_raw)
    causal_raw = _read_output(plane, receipt('project'), artifact=causal.arrays.array_artifact)
    causal_arrays = decode_matrix_arrays(causal_raw, causal.arrays)
    template_port = next(m for m in inputs['physical-forecast'] if m.logical.logical_artifact_id == protocol.templates.array_artifact.artifact_id)
    template_raw = read_bounded_bytes(plane.root.resolve(template_port.materialization.relative_path, for_write=False), maximum_bytes=protocol.templates.array_artifact.size_bytes)
    templates = decode_matrix_arrays(template_raw, protocol.templates)
    frozen_raw = _read_output(plane, receipt('physical-forecast'), artifact=physical.arrays.array_artifact)
    frozen = decode_matrix_arrays(frozen_raw, physical.arrays)
    if response_forecast.forecast(protocol, causal, causal_arrays, templates, artifact_id=physical.arrays.array_artifact.artifact_id,
            retained=frozen, raw=frozen_raw)[1] != physical:
        raise ValueError('scheduled original physical forecast changes retained independent origin witness')
    forecast_role = 'forecast-calibrated' if 'forecast-calibrated' in products else 'forecast'
    error = products[forecast_role]
    responses.validate_source(source, scientific_commitment.response_selection, history, causal, physical, error,
        native_context=route.native_context(extras[1]))
    raw = _read_output(plane, receipt(extras[1]), artifact=responses.arrays.array_artifact)
    if responses.native:
        native = _native(plane, execution_plan, tasks[extras[1]], receipt(extras[1]), inputs[extras[1]], responses.native[0],
            access=phase_access(extras[1]), visibility=phase_visibility(extras[1]))
        if b''.join(native.iter_completed_output(responses.native[0].definition, 'arrays')) != raw:
            raise ValueError('scheduled ordinary response archive differs from original Native completed bytes')
    arrays = decode_matrix_arrays(raw, responses.arrays)
    expected = response_science.assess_responses(source, causal, history, prefix, error, physical, frozen, protocol, panels,
        responses, arrays, score_id=score.score_id)
    if expected != score:
        raise ValueError('scheduled retained independent response controls/signed scores/full15 targets changed')
    return products
