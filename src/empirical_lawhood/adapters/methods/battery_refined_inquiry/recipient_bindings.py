# SPDX-License-Identifier: MPL-2.0
"""Receipt-ordered later preparation operations with complete external custody."""
from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration, RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveScientificHooks

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec, AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, require_sorted_unique_ids
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from . import contracts as c, science
from .operation_bindings import BUDGET, MEDIA, MAX_BYTES, NAMESPACE, QUESTION, UNIT, record_identity, SourcePolicyAdmission

FOREGROUND_MODELS = (*c.REDUCED, 'dfn-primary')
COMPARATORS = {'chen': ('chen-spme', 'chen-choice'), 'direct-dfn': ('dfn-primary', 'direct-choice')}

STEPS = ('validate', 'forecast', 'choose', 'complete', 'assess')
OPERATIONS = tuple(f'{step}-{phase}-{count}' for phase in ('use', 'reuse') for count in (45, 54) for step in STEPS)
SMALL_INPUTS = (('instance', c.Instance), ('policy', c.NumericalPolicy), ('selection', c.NumericalSelection),
                ('source', c.RefinedSource), ('supplier', c.Supply))


def parts(operation):
    if operation not in OPERATIONS:
        raise ValueError('unknown refined recipient operation')
    step, phase, count = operation.split('-')
    return step, phase, int(count)


def node_id(operation):
    return NAMESPACE + '.' + operation


def ports(prefix, count):
    return tuple(f'{prefix}-{n:03d}' for n in range(count))


@dataclass(frozen=True, slots=True)
class RecipientOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-refined-inquiry/recipient-operation-config'
    config_id: str
    operation: str
    source: c.RefinedSource
    policy: c.NumericalPolicy
    selection: c.NumericalSelection
    diagnostic: ObjectIdentity
    source_admission: ObjectIdentity
    supplier: c.Supply
    instance: c.Instance
    supplier_traces: tuple[ObjectIdentity, ...]
    prior_use: c.AssessedInstance | None
    prior_traces: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        _, phase, count = parts(self.operation)
        if self.config_id != 'config.' + node_id(self.operation):
            raise ValueError('recipient operation changes exact config identity')
        if (self.selection != self.policy.selection or self.source.policy != c.identity(self.policy)
                or self.source.diagnostic != self.diagnostic or self.policy.diagnostic != self.diagnostic
                or self.source.protocol_sha256 != self.selection.fingerprint()
                or self.supplier.source != self.source or self.supplier.policy != self.policy
                or count != (54 if self.policy.tolerance_probe else 45)):
            raise ValueError('recipient config changes selected source/policy/history/supplier')
        if self.source_admission.object_schema != SourcePolicyAdmission.SCHEMA:
            raise ValueError('recipient config substitutes actual source-policy admission')
        self.supplier.__post_init__()
        if self.instance != science.compatible_instance(self.supplier, phase, prior_use=self.prior_use):
            raise ValueError('recipient config changes original supplier/actual prior-use lineage')
        require_sorted_unique_ids(self.supplier_traces, attribute='object_id', field_name='supplier_traces')
        require_sorted_unique_ids(self.prior_traces, attribute='object_id', field_name='prior_traces')
        if self.supplier_traces != self.supplier.qualification.traces:
            raise ValueError('recipient config substitutes complete supplier trace identities')
        if self.prior_traces != (() if self.prior_use is None else self.prior_use.assessment.traces):
            raise ValueError('recipient config substitutes complete actual prior-use trace identities')

    @property
    def operands(self):
        records = (self.source, self.policy, self.selection, self.supplier, self.instance)
        values = [record_identity(r) for r in records] + [self.diagnostic, self.source_admission, *self.supplier_traces, *self.prior_traces]
        if self.prior_use is not None:
            values.append(c.identity(self.prior_use))
        return tuple(sorted(values, key=lambda row: row.object_id))


@dataclass(frozen=True, slots=True)
class RecipientAdmission(CanonicalRecord):
    """Complete supplier/actual prior-use validation, without later outcome reveal."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-refined-inquiry/recipient-admission'
    admission_id: str
    source: ObjectIdentity
    policy: ObjectIdentity
    selection: ObjectIdentity
    diagnostic: ObjectIdentity
    source_admission: ObjectIdentity
    supplier: ObjectIdentity
    instance: ObjectIdentity
    supplier_traces: tuple[ObjectIdentity, ...]
    prior_use: ObjectIdentity | None
    prior_traces: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if self.admission_id not in ('admission.' + NAMESPACE + '.use', 'admission.' + NAMESPACE + '.reuse'):
            raise ValueError('recipient admission changes phase identity')
        schemas = (c.RefinedSource.SCHEMA, c.NumericalPolicy.SCHEMA, c.NumericalSelection.SCHEMA,
                   self.diagnostic.object_schema, SourcePolicyAdmission.SCHEMA, c.Supply.SCHEMA, c.Instance.SCHEMA)
        if self.diagnostic.object_schema not in c.HISTORY_SCHEMAS or tuple(r.object_schema for r in (self.source, self.policy, self.selection, self.diagnostic,
                                         self.source_admission, self.supplier, self.instance)) != schemas:
            raise ValueError('recipient admission substitutes typed scientific operands')
        require_sorted_unique_ids(self.supplier_traces, attribute='object_id', field_name='supplier_traces')
        require_sorted_unique_ids(self.prior_traces, attribute='object_id', field_name='prior_traces')
        reuse = self.admission_id.endswith('.reuse')
        if reuse != (self.prior_use is not None) or (not reuse and self.prior_traces):
            raise ValueError('recipient admission substitutes actual prior-use census')
        if self.prior_use is not None and self.prior_use.object_schema != c.AssessedInstance.SCHEMA:
            raise ValueError('recipient admission substitutes prior-use product')


def admission_identity(record):
    return ObjectIdentity.from_record(record.admission_id, record)


def expected_admission(config):
    _, phase, _ = parts(config.operation)
    return RecipientAdmission('admission.' + NAMESPACE + '.' + phase, c.identity(config.source), c.identity(config.policy),
        record_identity(config.selection), config.diagnostic, config.source_admission, c.identity(config.supplier), c.identity(config.instance),
        config.supplier_traces, c.identity(config.prior_use) if config.prior_use is not None else None, config.prior_traces)


@dataclass(frozen=True, slots=True)
class ComparatorChoice(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-refined-inquiry/comparator-choice'
    product_id: str
    arm_id: str
    model_view: str
    choice: c.ChoiceCommitment

    def __post_init__(self):
        if type(self.choice) is not c.ChoiceCommitment:
            raise ValueError('comparator requires its exact typed choice')
        if self.arm_id not in COMPARATORS or self.model_view != COMPARATORS[self.arm_id][0]:
            raise ValueError('comparator choice substitutes its frozen forecast model')
        if self.product_id != 'choice.' + NAMESPACE + '.comparator.' + self.arm_id + '.' + self.choice.choice_id.rsplit('.', 1)[-1]:
            raise ValueError('comparator choice relabels its persisted scientific choice')
        self.choice.__post_init__()


@dataclass(frozen=True, slots=True)
class ComparatorAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/battery-refined-inquiry/comparator-assessment'
    product_id: str
    choice: ComparatorChoice
    assessment: c.Assessment

    def __post_init__(self):
        if type(self.choice) is not ComparatorChoice or type(self.assessment) is not c.Assessment:
            raise ValueError('comparator requires exact typed assessment/choice')
        self.choice.__post_init__()
        self.assessment.__post_init__()
        if self.assessment.choice != self.choice.choice or self.product_id != 'assessment.' + self.choice.product_id:
            raise ValueError('comparator assessment substitutes actual persisted choice')


def selected_forecasts(config, foreground, model_view=None):
    if tuple(row.config for row in foreground) != forecast_configs(config):
        raise ValueError('foreground substitutes complete nine forecast ordinals')
    model = config.supplier.qualification.selected_model if model_view is None else model_view
    return tuple(row for row in foreground if row.config.component_view == model)


def comparator_choice(config, foreground, arm_id):
    model, _ = COMPARATORS[arm_id]
    rows = selected_forecasts(config, foreground, model)
    checks = tuple(science.check_trace(row) for row in rows)
    ties = science.best_recipes(dict(zip(c.RECIPES, checks, strict=True)))
    choice = c.ChoiceCommitment('choice.' + NAMESPACE + '.comparator.' + arm_id + '.' + config.instance.phase,
        c.identity(config.supplier), c.identity(config.instance), tuple(c.identity(row) for row in rows), checks,
        ties[0] if ties else None, ties)
    return ComparatorChoice(choice.choice_id, arm_id, model, choice)


def assess_comparator(config, traces, choice):
    ordered, rows = science._rows(config.source, config.policy, config.instance.phase, traces)
    foreground = tuple(rows[row.initial_temperature_k, row.recipe, row.component_view] for row in forecast_configs(config))
    if choice != comparator_choice(config, foreground, choice.arm_id):
        raise ValueError('comparator substitutes actual foreground-only choice')
    selected = choice.choice
    # Reuse the exact independent receiver/admission/tie algorithm, changing
    # only its explicitly declared forecast model; retain the actual supplier.
    checks = tuple(science.check_trace(row) for row in ordered)
    indexed = {(row.config.initial_temperature_k, row.config.recipe, row.config.component_view): check
               for row, check in zip(ordered, checks, strict=True)}
    comparisons = science._comparisons(config.policy, rows)
    reference = {recipe: indexed[config.instance.initial_temperature_k, recipe, 'dfn-refined'] for recipe in c.RECIPES}
    best = science.best_recipes(reference)
    if any(row.disposition is not AssessmentDisposition.SATISFIED for row in comparisons):
        instance = admission = joined = overall = AssessmentDisposition.UNEVALUABLE
        reasons = ('independent-recipient-reference-precision-unresolved',)
    else:
        instance = AssessmentDisposition.SATISFIED
        why = science._model_admission(tuple((config.instance.initial_temperature_k, recipe) for recipe in c.RECIPES), indexed, choice.model_view)
        admission = AssessmentDisposition.UNEVALUABLE if 'forecast-or-reference-integrity-unresolved' in why else AssessmentDisposition.FALSIFIED if why or selected.selected_recipe is not None and selected.selected_recipe not in best else AssessmentDisposition.SATISFIED
        joined = reference[selected.selected_recipe].disposition if selected.selected_recipe is not None else AssessmentDisposition.REFUSED
        overall = AssessmentDisposition.SATISFIED if admission is joined is AssessmentDisposition.SATISFIED else AssessmentDisposition.UNEVALUABLE if admission is AssessmentDisposition.UNEVALUABLE else AssessmentDisposition.FALSIFIED if admission is AssessmentDisposition.FALSIFIED or joined is AssessmentDisposition.FALSIFIED else AssessmentDisposition.REFUSED
        reasons = tuple(sorted(set(why) | ({'no-feasible-delivery-selected'} if selected.selected_recipe is None else set())))
    assessment = c.Assessment('product.' + NAMESPACE + '.comparator.' + choice.arm_id + '.' + config.instance.phase,
        c.identity(config.supplier), config.instance, selected, c.identity(selected), tuple(c.identity(row) for row in ordered), checks,
        comparisons, best, instance, admission, joined, overall, reasons, sum(row.native_provider_attempts for row in ordered),
        sum(row.backend_solve_calls for row in ordered), sum((row.cpu_seconds for row in ordered), c.D(0)), sum((row.wall_seconds for row in ordered), c.D(0)))
    return ComparatorAssessment('assessment.' + choice.product_id, choice, assessment)


def forecast_configs(config):
    return tuple(science.native_config(config.source, config.policy, config.instance.phase,
        config.instance.initial_temperature_k, recipe, model) for model in FOREGROUND_MODELS for recipe in c.RECIPES)


def validate_comparator_assessment(config, assessment, traces):
    if type(assessment) is not ComparatorAssessment or assessment != assess_comparator(config, traces, assessment.choice):
        raise ValueError('comparator assessment differs from independent complete raw reduction')


def remaining_configs(config):
    selected = set(forecast_configs(config))
    return tuple(row for row in science.configurations(config.source, config.policy, config.instance.phase) if row not in selected)


def external_inputs(operation):
    step, phase, count = parts(operation)
    values = list(SMALL_INPUTS)
    if step in ('validate', 'assess'):
        values.append(('source-admission', SourcePolicyAdmission))
        values.extend((name, c.Trace) for name in ports('supplier-trace', count))
        if phase == 'reuse':
            values.append(('prior-use', c.AssessedInstance))
            values.extend((name, c.Trace) for name in ports('prior-trace', 18 if count == 54 else 15))
    return tuple(sorted(values))


def dependency_inputs(operation):
    step, phase, count = parts(operation)
    values = []
    if step != 'validate':
        values.append(('admission', RecipientAdmission, f'validate-{phase}-{count}', 'admission'))
    if step in ('choose', 'assess'):
        values.extend((name, c.Trace, f'forecast-{phase}-{count}', name) for name in ports('forecast', 9))
    if step in ('complete', 'assess'):
        values.append(('choice', c.ChoiceCommitment, f'choose-{phase}-{count}', 'choice'))
        values.extend((name, ComparatorChoice, f'choose-{phase}-{count}', name) for _, name in COMPARATORS.values())
    if step == 'assess':
        values.extend((name, c.Trace, f'complete-{phase}-{count}', name) for name in ports('trace', 9 if count == 54 else 6))
    return tuple(sorted(values))


def operation_inputs(operation):
    return tuple(sorted((*external_inputs(operation), *((name, record) for name, record, _, _ in dependency_inputs(operation)))))


def operation_outputs(operation):
    step, phase, count = parts(operation)
    if step == 'validate':
        values = [('admission', RecipientAdmission), ('source-admission', SourcePolicyAdmission), ('supplier-product', c.Supply)]
        values.extend((name, c.Trace) for name in ports('supplier-trace', count))
        if phase == 'reuse':
            values.append(('prior-use', c.AssessedInstance))
            values.extend((name, c.Trace) for name in ports('prior-trace', 18 if count == 54 else 15))
        return tuple(sorted(values))
    if step == 'forecast':
        return tuple((name, c.Trace) for name in ports('forecast', 9))
    if step == 'choose':
        return tuple(sorted((('choice', c.ChoiceCommitment), *((name, ComparatorChoice) for _, name in COMPARATORS.values()))))
    if step == 'complete':
        return tuple((name, c.Trace) for name in ports('trace', 9 if count == 54 else 6))
    return (('assessed', c.AssessedInstance), ('assessment', c.Assessment), ('chen-assessment', ComparatorAssessment), ('direct-assessment', ComparatorAssessment))


def operation_stage(operation):
    step, _, _ = parts(operation)
    return ScientificStage.ADMISSION if step == 'validate' else ScientificStage.ACQUIRE if step in ('forecast', 'complete') else ScientificStage.TRANSFORM if step == 'choose' else ScientificStage.QUALIFY


def scientific_operand_sha256s(config):
    return tuple(sorted({row.object_fingerprint for row in config.operands}))


def scientific_unit_ids(config):
    return (UNIT,)


def native_effect_slot_ids(config):
    step, _, _ = parts(config.operation)
    natives = forecast_configs(config) if step == 'forecast' else remaining_configs(config) if step == 'complete' else ()
    return tuple(sorted('native.' + NAMESPACE + '.' + sha256(canonical_json_bytes({
        'original_physics': config.source.original, 'native_source_members': config.source.source_members,
        'phase': row.phase, 'initial_temperature_k': row.initial_temperature_k, 'recipe': row.recipe,
        'chamber_temperature_k': row.chamber_temperature_k, 'model_view': row.model_view,
        'electrode_points': row.numerical_view.electrode_points, 'particle_points': row.numerical_view.particle_points,
        'localization_epsilon_k': row.localization_epsilon_k, 'rtol': row.rtol, 'atol': row.atol,
    })).hexdigest() for row in natives))


def development_root(config, *, study_id):
    selected_scope = c.scope(config.source)
    claim = ClaimSpec('claim.' + NAMESPACE + '.recipient', selected_scope.world_id,
        'population.battery-thermal-inquiry.exposed-lgm50', QUESTION,
        'Exact original qualified supplier and actual prior-use custody; forecast-only choice before remaining independent reference acquisition.',
        UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        'Conditional finite-path numerical results; zero physical units or whole-time certification.',
        ('assumption.exposed-lgm50-model-family',), numerical_view_ids=('view.' + NAMESPACE + '.recipient',))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(selected_scope.system_id, config.source.original),
        selected_scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (UNIT,), ('view.' + NAMESPACE + '.recipient',), (claim,), config.operands)


def scientific_root_validator(config, context):
    step, _, _ = parts(config.operation)
    native = step in ('forecast', 'complete')
    node = node_id(config.operation)
    if (context.root != development_root(config, study_id=context.root.study_id) or context.node_id != node
            or context.stage is not operation_stage(config.operation) or context.unit_ids != (UNIT,)
            or context.selected_unit_ids != (UNIT,) or context.complete_unit_census != native
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError('recipient scientific root/config/stage/unit/access differs')
    incoming = tuple(row for row in context.links if row.consumer_node_id == node)
    external, internal = dict(external_inputs(config.operation)), {name: (producer, output) for name, _, producer, output in dependency_inputs(config.operation)}
    if len(incoming) != len(external) + len(internal) or {row.consumer_input_id for row in incoming} != external.keys() | internal.keys():
        raise ValueError('recipient graph omits exact external/dependency census')
    for link in incoming:
        name = link.consumer_input_id
        if name in external:
            role = 'MODEL' if name == 'supplier' else 'OUTCOME' if name == 'prior-use' else 'HISTORY' if name == 'source-admission' or name.startswith(('supplier-trace-', 'prior-trace-')) else 'SOURCE'
            if link.external_input_id is None or link.scientific_role != role:
                raise ValueError('recipient graph substitutes external scientific roles')
        else:
            producer, output = internal[name]
            if (link.external_input_id is not None or link.producer_node_id != node_id(producer)
                    or link.producer_output_id != output or link.scientific_role != ('MODEL' if name == 'admission' else 'OUTCOME')):
                raise ValueError('recipient graph substitutes exact internal choice/trace/gate dependency')
    configs = {row.node_id: row.record for row in context.config_inputs}
    _, phase, count = parts(config.operation)
    expected_nodes = {node_id(f'{s}-{phase}-{count}') for s in STEPS}
    if configs.keys() != expected_nodes or any(type(row) is not RecipientOperationConfig or row.operands != config.operands
            or key != node_id(row.operation) for key, row in configs.items()):
        raise ValueError('recipient graph substitutes exact five-operation lineage')
    from .recursive_translation import validate_recipient_requirement_config
    validate_recipient_requirement_config(config, context.requirements, context.connections)


def project_recipient_assessments(record, requirement, connection):
    if type(record) is not c.AssessedInstance:
        return ()
    from .recursive_translation import validate_recipient_requirement_record
    validate_recipient_requirement_record(record, requirement, connection)
    dispositions = {AssessmentPhase.PROCEDURE: record.supplier.disposition,
        AssessmentPhase.INSTANCE: record.assessment.instance_disposition,
        AssessmentPhase.ADMISSION: record.assessment.admission_disposition,
        AssessmentPhase.JOINED: record.assessment.joined_disposition}
    return tuple(RequirementSupplyAssessment('assessment.' + NAMESPACE + '.recipient.' + record.assessment.instance.phase + '.' +
        requirement.requirement_id + '.' + phase.value.lower(),
        ObjectIdentity.from_record(requirement.requirement_id, requirement), ObjectIdentity.from_record(connection.connection_id, connection),
        phase, disposition, record.product_id, (c.identity(record),), () if disposition is AssessmentDisposition.SATISFIED else
        record.assessment.reason_codes or ('recipient-' + disposition.value.lower(),)) for phase, disposition in dispositions.items())


def operation_declarations():
    from functools import partial
    from .operation_bindings import output_codecs as all_codecs, describe_contributions, next_wave_builder, inquiry_endpoint_validator, inquiry_outcome_projector, inquiry_evidence_projector
    return tuple((RecursiveOperationDeclaration(
        capability_key=NAMESPACE + '.' + operation, capability_version='1.0.0',
        implementation_id=NAMESPACE + '.receipt-ordered-recipient-v1.' + operation,
        kind=CapabilityKind.SIMULATOR if parts(operation)[0] in ('forecast', 'complete') else CapabilityKind.ANALYSIS,
        config_record_type=RecipientOperationConfig, stage=operation_stage(operation),
        input_ports=tuple((RecursivePortContract(name, record.SCHEMA, MEDIA, MAX_BYTES) for name, record in operation_inputs(operation))),
        outputs=tuple((OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json') for name, record in operation_outputs(operation))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET,
        conformance_check_ids=('authenticated-original-supplier-and-prior-use', 'choices-before-remaining-reference-acquisition', 'full-recipient-census'),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        runner_factory=partial(RecipientRunner, operation), record_codecs=all_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_recipient_assessments if parts(operation)[0] == 'assess' else None,
            scientific_operand_sha256s=scientific_operand_sha256s, scientific_unit_ids=scientific_unit_ids,
            native_effect_slot_ids=native_effect_slot_ids if parts(operation)[0] in ('forecast', 'complete') else None,
            scientific_root_validator=scientific_root_validator,
        ),
        execution_properties=RecursiveExecutionProperties(
            native_effect=parts(operation)[0] in ('forecast', 'complete'),
            complete_unit_census=parts(operation)[0] in ('forecast', 'complete'),
        ),
        inquiry_hooks=RecursiveInquiryHooks(
            contribution_describer=describe_contributions, next_wave_builder=next_wave_builder,
            inquiry_endpoint_validator=inquiry_endpoint_validator, inquiry_outcome_projector=inquiry_outcome_projector,
            inquiry_evidence_projector=inquiry_evidence_projector,
        ),
    ) for operation in OPERATIONS))


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {record.SCHEMA: record for record in (RecipientOperationConfig, RecipientAdmission, c.RefinedSource,
        c.NumericalPolicy, c.NumericalSelection, SourcePolicyAdmission, c.Trace, c.Qualification, c.Supply, c.Instance,
        c.ChoiceCommitment, c.Assessment, c.AssessedInstance, ComparatorChoice, ComparatorAssessment)}


def _validate_raw_history(config, records):
    source_admission = records['source-admission']
    expected = SourcePolicyAdmission('admission.' + NAMESPACE + '.source-policy', c.identity(config.source),
        c.identity(config.policy), record_identity(config.selection), config.diagnostic)
    if source_admission != expected or record_identity(source_admission) != config.source_admission:
        raise ValueError('recipient substitutes actual authenticated source-policy admission')
    supplied = tuple(records[name] for name in ports('supplier-trace', len(config.supplier_traces)))
    if tuple(c.identity(row) for row in supplied) != config.supplier_traces:
        raise ValueError('recipient substitutes exact external supplier raw trace closure')
    science.validate_qualification(config.source, config.policy, config.supplier.qualification, supplied)
    if config.prior_use is not None:
        prior = tuple(records[name] for name in ports('prior-trace', len(config.prior_traces)))
        if records['prior-use'] != config.prior_use or tuple(c.identity(row) for row in prior) != config.prior_traces:
            raise ValueError('recipient substitutes actual previous-use raw closure')
        science.validate_assessment(config.supplier, config.prior_use.assessment, prior)


class RecipientRunner:
    def __init__(self, operation):
        parts(operation)
        self.operation = operation
        self.manifest = next(row for row in operation_manifests() if row.capability_key == node_id(operation))

    def execute(self, context):
        try:
            operation = self.operation
            step, phase, count = parts(operation)
            node = node_id(operation)
            expected = operation_inputs(operation)
            schemas = {record.SCHEMA: record for _, record in expected} | {RecipientOperationConfig.SCHEMA: RecipientOperationConfig}
            if (context.task_id != node or context.permissions != self.manifest.permissions or context.resource_budget != BUDGET
                    or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE or len(context.input_ports) != len(expected) + 1):
                raise ValueError('recipient worker substitutes task/input/access/resource contract')
            decoded = []
            for port in context.input_ports:
                if (port.payload_schema not in schemas or port.media_type != MEDIA or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                        or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
                    raise ValueError('recipient worker receives undeclared/protected input')
                raw = port.read()
                if len(raw) != port.size_bytes:
                    raise ValueError('recipient input size differs')
                decoded.append((port, decode_canonical_bytes(raw, schemas[port.payload_schema], maximum_bytes=None)))
            config_rows = [(p, r) for p, r in decoded if type(r) is RecipientOperationConfig]
            if len(config_rows) != 1:
                raise ValueError('recipient worker omits exact selected config')
            config_port, config = config_rows[0]
            if (config_port.kind is not WorkerInputKind.EXTERNAL or config_port.artifact_id != context.config.artifact_id
                    or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256 or config.operation != operation):
                raise ValueError('recipient worker substitutes immutable config')
            external_expected = {name: getattr(config, name) for name, _ in SMALL_INPUTS}
            if step in ('validate', 'assess'):
                external_expected['source-admission'] = config.source_admission
                external_expected.update(zip(ports('supplier-trace', count), config.supplier_traces, strict=True))
                if phase == 'reuse':
                    external_expected['prior-use'] = config.prior_use
                    external_expected.update(zip(ports('prior-trace', len(config.prior_traces)), config.prior_traces, strict=True))
            records, used = {}, {id(config_port)}
            for name, value in external_expected.items():
                matches = [(p, r) for p, r in decoded if id(p) not in used and p.kind is WorkerInputKind.EXTERNAL
                           and (record_identity(r) == value if isinstance(value, ObjectIdentity) else r == value)]
                if len(matches) != 1:
                    raise ValueError('recipient worker substitutes exact external origin/closure: ' + name)
                p, r = matches[0]
                records[name] = r
                used.add(id(p))
            producers = set()
            for name, record_type, producer_operation, output in dependency_inputs(operation):
                producer = node_id(producer_operation)
                key = f'artifact.{context.run_id}.{producer}.{output}'
                matches = [(p, r) for p, r in decoded if id(p) not in used and p.artifact_id == key and type(r) is record_type
                           and p.kind is WorkerInputKind.DEPENDENCY and any(receipt.task_id == producer
                           and p.materialization_id in receipt.output_materialization_ids for receipt in context.dependency_receipts)]
                if len(matches) != 1:
                    raise ValueError('recipient worker requires actual receipt-backed dependency: ' + name)
                p, r = matches[0]
                records[name] = r
                used.add(id(p))
                producers.add(producer)
            if len(used) != len(decoded) or len(context.dependency_receipts) != len(producers) or {r.task_id for r in context.dependency_receipts} != producers:
                raise ValueError('recipient worker duplicates or adds undeclared dependency/input')
            if step in ('validate', 'assess'):
                _validate_raw_history(config, records)
            admission = expected_admission(config)
            if step != 'validate' and records['admission'] != admission:
                raise ValueError('recipient worker substitutes actual complete-custody admission')
            outputs = operation_outputs(operation)
            if (tuple((p.output_id, p.payload_schema) for p in context.output_ports) != tuple((node + '.' + name, record.SCHEMA) for name, record in outputs)
                    or any(p.profile is not ArtifactProfile.CANONICAL_JSON or p.media_type != MEDIA for p in context.output_ports)):
                raise ValueError('recipient worker changes canonical output census')
            if step == 'validate':
                relays = {'admission': admission, 'source-admission': records['source-admission'], 'supplier-product': config.supplier}
                relays.update((name, records[name]) for name in ports('supplier-trace', count))
                if phase == 'reuse':
                    relays['prior-use'] = records['prior-use']
                    relays.update((name, records[name]) for name in ports('prior-trace', len(config.prior_traces)))
                results = tuple(relays[name] for name, _ in outputs)
            elif step in ('forecast', 'complete'):
                if step == 'complete':
                    choice = records['choice']
                    if any(records[name].arm_id != arm or records[name].model_view != model
                           for arm, (model, name) in COMPARATORS.items()):
                        raise ValueError('recipient complete task substitutes persisted comparator arms')
                    choices = (choice, *(records[name].choice for _, name in COMPARATORS.values()))
                    if any(row.instance != c.identity(config.instance) or row.supplier != c.identity(config.supplier) for row in choices):
                        raise ValueError('recipient complete task substitutes actual persisted choices lineage')
                from .native import acquire
                configs = forecast_configs(config) if step == 'forecast' else remaining_configs(config)
                results = tuple(acquire(row) for row in configs)
                if any(type(trace) is not c.Trace or trace.config != row for trace, row in zip(results, configs, strict=True)):
                    raise ValueError('recipient native provider substitutes complete exact configs')
            elif step == 'choose':
                forecasts = tuple(records[name] for name in ports('forecast', 9))
                if tuple(row.config for row in forecasts) != forecast_configs(config):
                    raise ValueError('recipient choice substitutes three forecast ordinals')
                choices = {'choice': science.commit_choice(config.supplier, config.instance, selected_forecasts(config, forecasts))}
                choices.update((name, comparator_choice(config, forecasts, arm)) for arm, (_, name) in COMPARATORS.items())
                results = tuple(choices[name] for name, _ in outputs)
            else:
                forecasts = tuple(records[name] for name in ports('forecast', 9))
                remaining = tuple(records[name] for name in ports('trace', 9 if count == 54 else 6))
                if tuple(row.config for row in forecasts) != forecast_configs(config) or tuple(row.config for row in remaining) != remaining_configs(config):
                    raise ValueError('recipient assessment substitutes exact raw forecast/reference ordinals')
                actual = tuple(sorted((*forecasts, *remaining), key=lambda row: row.trace_id))
                choice = records['choice']
                assessment = science.assess_instance(config.supplier, config.instance, actual, choice, c.identity(choice), prior_use=config.prior_use)
                assessed = c.AssessedInstance('product.' + NAMESPACE + '.assessed-' + phase, config.supplier,
                    assessment, config.prior_use.assessment if config.prior_use is not None else None)
                results = (assessed, assessment, assess_comparator(config, actual, records['chen-choice']),
                           assess_comparator(config, actual, records['direct-choice']))
            return RunnerResult(tuple(TaskOutputPayload(port.output_id, record.canonical_bytes())
                for port, record in zip(context.output_ports, results, strict=True)), (ReceiptCheck('complete-custody-choice-ordered-recipient', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()
