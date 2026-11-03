# SPDX-License-Identifier: MPL-2.0
"""Bounded storage waves of one frozen E4 programme, without execution authority.

The root phase configurations and native identities are the existing v2
contracts. A wave is neither a new study nor a per-wave calibration. Its
collector is an ordinary sealed completion declaration; this module supplies
no runtime collector factory, qualifications, issue or native effects.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult

from .compact_records import (
    NAMESPACE as COMPACT_NAMESPACE, ScheduledCompactBank,
    ScheduledCompactCommitmentConfig, ScheduledCompactConfig, ScheduledCompactForecastConfig,
    ScheduledCompactPhysicalForecastConfig, ScheduledCompactResponseConfig,
    compact_committed, compact_identity, compact_native_contract,
)
from .forecast import CALIBRATED_QUERY, ScheduledPublicSource
from .operation_bindings import BUDGET
from .programme_records import ScheduledProgramme, ScheduledProgrammeWave, validate_programme_bank
from .commitment import ScheduledCommitment
from .records import identity
from .source_index import ScheduledSourceIndex

MAXIMUM_WAVE_PLAN_BYTES = 16 * 1024**2
NATIVE_PHASES = frozenset(('prefix', 'continue', 'continue-development', 'responses', 'responses-development'))
_EXPECTED_COMMITMENTS = {}


def expected_global_commitment(bank):
    """Memoize pure derivation for an exact immutable object, never custody."""
    cached = _EXPECTED_COMMITMENTS.get(id(bank))
    if cached is not None and cached[0] is bank:
        return cached[1]
    result = compact_committed(ScheduledCompactCommitmentConfig('config.'+COMPACT_NAMESPACE+'.commit', bank))
    if len(_EXPECTED_COMMITMENTS) == 4:
        _EXPECTED_COMMITMENTS.pop(next(iter(_EXPECTED_COMMITMENTS)))
    _EXPECTED_COMMITMENTS[id(bank)] = (bank, result)
    return result


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeNativeContract(CanonicalRecord):
    """Exact existing native declaration, requiring later ordinary authority."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/native-contract'
    task_id: str
    root_id: str
    independent_group_id: str
    phase: str
    configuration: ObjectIdentity
    native_operation_id: str
    operands: tuple[ObjectIdentity, ...]
    slot_ids: tuple[str, ...]

    def __post_init__(self):
        for name in ('task_id', 'root_id', 'independent_group_id', 'native_operation_id'):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_strings(self.slot_ids, field_name='existing native slots', allow_empty=False)
        if (self.phase not in NATIVE_PHASES or self.task_id != COMPACT_NAMESPACE+'.'+self.root_id+'.'+self.phase
                or self.configuration.object_id != 'config.'+self.task_id or len(self.operands) != 6):
            raise ValueError('programme changes an existing native task/configuration/operand declaration')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWavePlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-plan'
    plan_id: str
    programme: ObjectIdentity
    bank: ObjectIdentity
    wave: ScheduledProgrammeWave
    global_commitment: ObjectIdentity
    model_parents: tuple[ArtifactWriteResult, ...]
    required_calibration: ObjectIdentity | None
    operations: tuple[RecursiveOperationSpec, ...]
    external_inputs: tuple[RecursiveExternalInput, ...]
    links: tuple[RecursiveInputLink, ...]
    collector_task_id: str
    collector_inputs: tuple[RecursiveInputLink, ...]
    native_contracts: tuple[ScheduledProgrammeNativeContract, ...]

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        if (self.programme.object_schema != ScheduledProgramme.SCHEMA
                or self.bank.object_schema != ScheduledCompactBank.SCHEMA
                or self.global_commitment.object_schema != ScheduledCommitment.SCHEMA
                or self.global_commitment.object_version != ScheduledCommitment.VERSION
                or type(self.wave) is not ScheduledProgrammeWave
                or self.collector_task_id != self.wave.wave_id+'.collect'):
            raise ValueError('programme wave changes its exact global scope/commitment/collector identity')
        node_ids = tuple(o.node_id for o in self.operations)
        external_ids = tuple(e.input_id for e in self.external_inputs)
        for values, label in ((node_ids, 'existing phase tasks'), (external_ids, 'source references'),
                (tuple(e.edge_id for e in self.links), 'phase links'),
                (tuple(e.edge_id for e in self.collector_inputs), 'collector links'),
                (tuple(n.task_id for n in self.native_contracts), 'native task census')):
            require_sorted_unique_strings(values, field_name=label, allow_empty=False)
        if len(self.operations) != 11*len(self.wave.root_ids) or len(self.native_contracts) != 3*len(self.wave.root_ids):
            raise ValueError('programme wave omits complete eleven phases or three native phases per case')
        if len(self.model_parents) != 3 or any(type(p) is not ArtifactWriteResult for p in self.model_parents):
            raise ValueError('programme wave omits its original presealed model/training/criterion parents')
        endpoints = set()
        for link in (*self.links, *self.collector_inputs):
            collector = link in self.collector_inputs
            if (link.consumer_node_id != self.collector_task_id if collector else link.consumer_node_id not in node_ids):
                raise ValueError('programme wave link has no declared consumer')
            if (link.producer_node_id is not None and link.producer_node_id not in node_ids
                    or link.external_input_id is not None and link.external_input_id not in external_ids):
                raise ValueError('programme wave link has no declared source/producer')
            endpoint = (link.consumer_node_id, link.consumer_input_id)
            if endpoint in endpoints:
                raise ValueError('programme wave aliases a consumer input')
            endpoints.add(endpoint)
        if len(self.collector_inputs) != 3*len(self.wave.root_ids):
            raise ValueError('programme wave collector omits full forecast/score/numerical terminal census')
        if len(self.canonical_bytes()) > MAXIMUM_WAVE_PLAN_BYTES:
            raise ValueError('programme wave exceeds its unchanged 16MiB closed member bound')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.plan_id, self)

    @property
    def task_ids(self):
        return tuple(sorted((*(o.node_id for o in self.operations), self.collector_task_id)))


def phase_roles(source, design):
    suffix = '-development' if source.root.root.role.value == 'DEVELOPMENT' else ''
    forecast = 'forecast-calibrated' if dict(design.source_scopes)[source.root_id] == CALIBRATED_QUERY else 'forecast'
    return ('prefix', 'numerical', 'measure', 'check', 'project', forecast, 'continue'+suffix,
        'full-numerical'+suffix, 'physical-forecast', 'responses'+suffix, 'response-score'+suffix)


def programme_wave_task_ids(programme, bank, wave_id):
    """Expose the exact phase census so callers can supply owners and budgets."""
    validate_programme_bank(programme, bank)
    wave = next((w for w in programme.waves if w.wave_id == wave_id), None)
    if wave is None:
        raise ValueError('programme has no such frozen whole-group wave')
    return tuple(sorted(COMPACT_NAMESPACE+'.'+s.root_id+'.'+role for s in bank.sources
        if s.root_id in wave.root_ids for role in phase_roles(s, bank.forecast_design)))


def compile_programme_wave(*, programme, bank, wave_id, proof_owners, operational_budgets, template_bytes):
    """Compile exact v2 declarations; existing publications are prerequisites.

    The required global commitment identity is computed from original bytes.
    This is an expected prerequisite, not a claim that a receipt/publication
    exists. Actual entry must authenticate that receipt and the presealed
    model parents. Calibrated queries similarly declare their required sealed
    calibration; this pure compiler establishes no qualified-parent authority.
    """
    from .compact_bindings import PHASES, operation_registrations

    validate_programme_bank(programme, bank)
    wave = next((w for w in programme.waves if w.wave_id == wave_id), None)
    if wave is None or tuple(sorted(set(proof_owners))) != proof_owners:
        raise ValueError('programme wave requires frozen whole-group membership and explicit ordered proof owners')
    index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
        specification=bank.specification, provenances=bank.provenances)
    selected = tuple(index.resolve(s) for s in bank.sources if s.root_id in wave.root_ids)
    design, response = bank.forecast_design, bank.response_selection
    descriptors = {s.root_id: s for s in bank.sources}
    registrations = {r.selection.capability_key.rsplit('.', 1)[-1]: r for r in operation_registrations()}
    phases = {p[0]: p for p in PHASES}
    commitment = expected_global_commitment(bank)
    external, records, operations, links, collector, native = {}, {}, [], [], [], []

    def add(record, logical_id=None, publication=None):
        logical_id = publication.logical.logical_artifact_id if publication else logical_id
        if logical_id is None:
            logical_id = record.identity.object_id if type(record) is NumericalProducingProvenance else record.coordinate_id if hasattr(record, 'coordinate_id') else identity(record).object_id
        name = 'external.'+logical_id
        value = RecursiveExternalInput(name, logical_id, record.SCHEMA, 'application/json', len(record.canonical_bytes()),
            publication.logical.outcome_access if publication else OutcomeAccess.OUTCOME_BLIND,
            publication.logical.visibility_ceiling if publication else VisibilityCeiling.PROSPECTIVE,
            record.fingerprint(), 'HISTORY' if publication and publication.logical.outcome_access is OutcomeAccess.EVALUATION_SEALED else 'SOURCE')
        if external.setdefault(name, value) != value or records.setdefault(logical_id, record) != record:
            raise ValueError('programme wave aliases distinct immutable shared source bytes')
        return name

    def edge(task, port, *, source=None, producer=None, output='product', terminal=False):
        value = RecursiveInputLink('edge.'+task+'.'+port, task, port, external_input_id=source,
            producer_node_id=producer, producer_output_id=output if producer else None,
            scientific_role='SOURCE' if source else 'HISTORY' if producer.endswith('.prefix') else 'OUTCOME')
        (collector if terminal else links).append(value)

    bank_external = add(bank, bank.bank_id)
    commitment_external = add(commitment, commitment.commitment_id)
    # The expected commitment bytes are a prerequisite, not newly published
    # evidence. Public API custody must distinguish this required record.
    records.pop(commitment.commitment_id)
    collector_id = wave.wave_id+'.collect'
    for source in selected:
        descriptor = descriptors[source.root_id]
        protocol, panels = response.validate_source(source)
        roles = phase_roles(source, design)
        forecast_role = roles[5]
        for role in roles:
            task = COMPACT_NAMESPACE+'.'+source.root_id+'.'+role
            config_id = 'config.'+task
            if role in ('forecast', 'forecast-calibrated'):
                config = ScheduledCompactForecastConfig(config_id, ScheduledPublicSource.from_source(source), identity(design), role == 'forecast-calibrated')
            elif role == 'physical-forecast':
                config = ScheduledCompactPhysicalForecastConfig(config_id, protocol)
            elif role.startswith('response'):
                config = ScheduledCompactResponseConfig(config_id, role, descriptor, response.identity, programme.bank)
            else:
                config = ScheduledCompactConfig(config_id, role, descriptor, programme.bank)
            owners = tuple(o for o, n in proof_owners if n == task)
            budget = operational_budgets.get(task)
            if not owners or budget is None or not BUDGET.contains(budget):
                raise ValueError('programme wave omits an explicit proof owner or contained operational budget')
            registration = registrations[role]
            operations.append(RecursiveOperationSpec.from_config(node_id=task, selection=registration.selection,
                config_id=config_id, config=config, obligation_ids=owners, resource_budget=budget))
            if role in NATIVE_PHASES:
                configuration, native_task, operation, operands = compact_native_contract(source, role, bank=bank)
                native.append(ScheduledProgrammeNativeContract(native_task, source.root_id, source.root.root.independent_group_id,
                    role, configuration, operation, operands, registration.native_effect_slot_ids(config)))
            for port, _ in phases[role][1]:
                if port == 'templates':
                    artifact = protocol.templates.array_artifact
                    raw = template_bytes.get(artifact.artifact_id)
                    if type(raw) is not bytes or len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256:
                        raise ValueError('programme wave omits exact original pre-future template bytes')
                    name = 'external.'+artifact.artifact_id
                    value = RecursiveExternalInput(name, artifact.artifact_id, artifact.payload_schema, artifact.media_type,
                        artifact.size_bytes, OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, artifact.sha256, 'SOURCE')
                    if external.setdefault(name, value) != value or records.setdefault(artifact.artifact_id, raw) != raw:
                        raise ValueError('programme wave aliases original template bytes')
                    edge(task, port, source=name)
                elif port == 'streams':
                    for stream in source.root.streams:
                        edge(task, 'streams.'+stream.purpose, source=add(stream, source.root.stream_identity(stream).object_id))
                    if role.startswith('responses'):
                        for panel in panels:
                            if panel.role == 'INDEPENDENT_FUTURE':
                                for stream in panel.streams:
                                    edge(task, 'streams.future.'+stream.purpose, source=add(stream, panel.stream_identity(stream).object_id))
                elif port == 'bank':
                    edge(task, port, source=bank_external)
                elif port == 'commitment':
                    edge(task, port, source=commitment_external)
                elif port == 'calibration':
                    publication = design.calibration_publication
                    name = 'external.'+publication.logical.logical_artifact_id
                    external[name] = RecursiveExternalInput(name, publication.logical.logical_artifact_id,
                        publication.logical.payload_schema, publication.logical.media_type, publication.materialization.size_bytes,
                        publication.logical.outcome_access, publication.logical.visibility_ceiling,
                        publication.logical.content_sha256, 'HISTORY')
                    edge(task, port, source=name)
                elif port in ('source', 'allocation', 'selection', 'coordinate', 'provenance', 'forecast-design', 'response-selection'):
                    record, publication = {'source': (descriptor, None), 'allocation': (source.allocation, source.reservation.publication),
                        'selection': (source.specification.selection, source.specification.publication), 'coordinate': (source.coordinate, None),
                        'provenance': (source.provenance, None), 'forecast-design': (design, None),
                        'response-selection': (response, bank.response_selection_publication)}[port]
                    edge(task, port, source=add(record, publication=publication))
                else:
                    owner = 'prefix' if port.startswith('history') or port == 'checkpoint' else 'project' if port.startswith('causal') or port == 'feature' else forecast_role if port in ('forecast', 'error-forecast') else roles[9] if port.startswith('responses') else port.removesuffix('-arrays')
                    edge(task, port, producer=COMPACT_NAMESPACE+'.'+source.root_id+'.'+owner,
                        output='arrays' if port.endswith('-arrays') else 'feature' if port == 'feature' else 'checkpoint' if port == 'checkpoint' else 'product')
        for port, role in (('forecasts', forecast_role), ('scores', roles[10]), ('full-numericals', roles[7])):
            edge(collector_id, port+'.'+source.root_id, producer=COMPACT_NAMESPACE+'.'+source.root_id+'.'+role, terminal=True)
    tasks = {o.node_id for o in operations}
    if set(operational_budgets) != tasks or {n for _, n in proof_owners} != tasks:
        raise ValueError('programme wave explicit owner/budget census differs from exact selected phases')
    plan = ScheduledProgrammeWavePlan('plan.'+wave.wave_id, programme.identity, programme.bank, wave,
        compact_identity(commitment), (design.model_publication, design.training_publication, design.criterion_publication),
        design.calibration, tuple(sorted(operations, key=lambda o: o.node_id)),
        tuple(sorted(external.values(), key=lambda e: e.input_id)), tuple(sorted(links, key=lambda e: e.edge_id)),
        collector_id, tuple(sorted(collector, key=lambda e: e.edge_id)), tuple(sorted(native, key=lambda n: n.task_id)))
    return plan, records


def validate_programme_wave(plan, programme, bank, template_bytes):
    """Public pure preflight seam; scientific qualification remains external."""
    from .programme_qualification import validate_programme_wave as validate
    return validate(plan, programme, bank, template_bytes)


def programme_wave_runtime_task_ids(programme, bank, wave_id):
    return tuple(sorted((*programme_wave_task_ids(programme, bank, wave_id), wave_id+'.open', wave_id+'.collect')))


def programme_wave_draft(*, root, programme, bank, wave_id, global_parent, global_parent_publication,
        global_parent_receipt, global_parent_receipt_publication,
        global_parent_binding,
        proof_owners, operational_budgets, template_bytes, draft_id):
    """Compose a real bounded wave beneath the caller's full scientific root.

    The existing global publication is supplied, never manufactured here.
    Qualification and guarded original receipt custody are API prerequisites.
    The ordinary collector joins every original phase, including negatives.
    """
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
    from empirical_lawhood.planning.study_authoring import StudyDraft
    from .programme_bindings import (
        ScheduledProgrammeWaveAdmission, ScheduledProgrammeWaveAdmissionConfig,
        ScheduledProgrammeWaveCollectorConfig, operation_registrations,
    )
    from .programme_global import GLOBAL_CONFIG_ID, ScheduledProgrammeGlobalCommitConfig, global_committed
    from .records import _publication

    if type(root) is not StudyDraft or root.campaign is None or root.experiment is None:
        raise ValueError('programme wave requires its actual complete global prospective StudyDraft')
    if programme.mode == 'E4_CONFIRMATION':
        raise ValueError('programme confirmation runtime requires the original genuine qualified-parent bridge before authoring')
    validate_programme_bank(programme, bank)
    expected_parent = global_committed(ScheduledProgrammeGlobalCommitConfig(GLOBAL_CONFIG_ID, programme, programme.bank), bank)
    if global_parent != expected_parent:
        raise ValueError('programme wave substitutes its genuine global wrapper scientific scope')
    _publication(global_parent_publication, global_parent)
    _publication(global_parent_receipt_publication, global_parent_receipt)
    tasks = programme_wave_task_ids(programme, bank, wave_id)
    plan, operands = compile_programme_wave(programme=programme, bank=bank, wave_id=wave_id,
        proof_owners=tuple((owner, task) for owner, task in proof_owners if task in tasks),
        operational_budgets={task: operational_budgets[task] for task in tasks}, template_bytes=template_bytes)
    registrations = {r.selection.capability_key.rsplit('.', 1)[-1]: r for r in operation_registrations()}
    operations = [replace(o, selection=registrations[o.selection.capability_key.rsplit('.', 1)[-1]].selection)
        for o in plan.operations]
    admission_config = ScheduledProgrammeWaveAdmissionConfig('config.'+wave_id+'.open', programme, programme.bank,
        plan.wave, global_parent.identity, compact_identity(global_parent.semantic_commitment),
        global_parent_publication, ObjectIdentity.from_record(global_parent_receipt.receipt_id, global_parent_receipt), global_parent_binding)
    admission = ScheduledProgrammeWaveAdmission('admission.'+wave_id,
        ObjectIdentity.from_record(admission_config.config_id, admission_config), programme, programme.bank, plan.wave, global_parent,
        global_parent_publication, global_parent_receipt, global_parent_binding)
    collector_config = ScheduledProgrammeWaveCollectorConfig('config.'+wave_id+'.collect', programme.identity,
        programme.bank, plan.wave, admission.identity, programme.mode)
    for task, role, config in ((wave_id+'.open', 'open', admission_config),
            (wave_id+'.collect', collector_config.operation, collector_config)):
        owners = tuple(owner for owner, node in proof_owners if node == task)
        budget = operational_budgets.get(task)
        if not owners or budget is None or not BUDGET.contains(budget):
            raise ValueError('programme wave controls omit explicit owners or contained budgets')
        operations.append(RecursiveOperationSpec.from_config(node_id=task, selection=registrations[role].selection,
            config_id=config.config_id, config=config, obligation_ids=owners, resource_budget=budget))
    links = []
    for link in plan.links:
        if link.consumer_input_id == 'commitment':
            links.append(replace(link, edge_id='edge.'+link.consumer_node_id+'.admission', consumer_input_id='admission',
                producer_node_id=wave_id+'.open', producer_output_id='product', external_input_id=None))
        else:
            links.append(link)
    bank_external = next(e.input_id for e in plan.external_inputs if e.payload_schema == ScheduledCompactBank.SCHEMA)
    global_external = 'external.'+global_parent_publication.logical.logical_artifact_id
    external = [e for e in plan.external_inputs if e.payload_schema != ScheduledCommitment.SCHEMA]
    external.append(RecursiveExternalInput(global_external, global_parent_publication.logical.logical_artifact_id,
        global_parent.SCHEMA, 'application/json', global_parent_publication.materialization.size_bytes,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, global_parent.fingerprint(), 'SOURCE'))
    operands[global_parent_publication.logical.logical_artifact_id] = global_parent
    receipt_external = 'external.'+global_parent_receipt_publication.logical.logical_artifact_id
    external.append(RecursiveExternalInput(receipt_external, global_parent_receipt_publication.logical.logical_artifact_id,
        global_parent_receipt.SCHEMA, 'application/json', global_parent_receipt_publication.materialization.size_bytes,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, global_parent_receipt.fingerprint(), 'SOURCE'))
    operands[global_parent_receipt_publication.logical.logical_artifact_id] = global_parent_receipt
    for task, port, producer, source in ((wave_id+'.open', 'bank', None, bank_external),
            (wave_id+'.open', 'global-parent', None, global_external),
            (wave_id+'.open', 'global-parent-receipt', None, receipt_external), (wave_id+'.collect', 'bank', None, bank_external),
            (wave_id+'.collect', 'admission', wave_id+'.open', None)):
        links.append(RecursiveInputLink('edge.'+task+'.'+port, task, port, producer_node_id=producer,
            producer_output_id='product' if producer else None, external_input_id=source, scientific_role='SOURCE'))
    for operation in plan.operations:
        role = operation.selection.capability_key.rsplit('.', 1)[-1]
        port = 'products.'+role.removesuffix('-development').replace('forecast-calibrated', 'forecast')+'.'+operation.node_id.removeprefix(COMPACT_NAMESPACE+'.').removesuffix('.'+role)
        links.append(RecursiveInputLink('edge.'+wave_id+'.collect.'+port, wave_id+'.collect', port,
            producer_node_id=operation.node_id, producer_output_id='product', scientific_role='OUTCOME'))
    expected_tasks = {o.node_id for o in operations}
    if set(operational_budgets) != expected_tasks or {node for _, node in proof_owners} != expected_tasks:
        raise ValueError('programme wave actual explicit owner/budget census differs from the admitted graph')
    draft = RecursiveStudyDraft(draft_id, root.question, root.campaign, (), (), (),
        tuple(sorted(operations, key=lambda o: o.node_id)), tuple(sorted(external, key=lambda e: e.input_id)),
        tuple(sorted(links, key=lambda e: e.edge_id)), tuple(sorted(expected_tasks)), prospective_draft=root)
    return draft, operands
