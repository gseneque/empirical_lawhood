# SPDX-License-Identifier: MPL-2.0
"""Prospective factorial criteria and a distinct protected confirmation route.

The exposed development declaration remains unchanged. These records retain
original source identities and describe no source freshness or authority of
their own. Parent-side installed services replay actual current grants, the
ordinary pre-acquisition freeze and original acquisition custody before a
worker receives its identity-bound evidence. Conditional numerical results do
not authenticate the common-normal scientific assumption.
"""

from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_sampling_assessment import MatrixSamplingAdmission
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ScientificRequirementSpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult, CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import ExecutionPlan
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding

from .programme_factorial import FAMILY_IDS, ScheduledFactorialAssessment, ScheduledFactorialFamilySlot, ScheduledFactorialSpecification
from .programme_qualified_parent import ScheduledProgrammeQualifiedParentDeclaration
from .programme_records import NAMESPACE, ScheduledProgramme
from .programme_selection import ScheduledRevisionDataBank
from .programme_reduction import ScheduledProgrammeReduction

FREEZE = NAMESPACE+".factorial-criteria-freeze"
ASSESS = NAMESPACE+".factorial-confirmation-assess"
INPUT_SEAL = NAMESPACE+".factorial-confirmation-input-seal"


def _confirmation(programme, specification):
    if (type(programme) is not ScheduledProgramme or programme.mode != "E4_CONFIRMATION"
            or type(specification) is not ScheduledFactorialSpecification or specification.programme != programme.identity
            or specification.target.criterion != programme.criterion):
        raise ValueError("protected factorial requires its exact original confirmation programme and explicit statistical criteria")
    programme.__post_init__()
    specification.__post_init__()


def freeze_node_id(specification):
    return FREEZE+"."+specification.fingerprint()[:24]


def assess_node_id(specification):
    return ASSESS+"."+specification.fingerprint()[:24]


def input_seal_node_id(specification):
    return INPUT_SEAL+"."+specification.fingerprint()[:24]


def protected_sampling_requirement(specification):
    """Bind the unchanged scientific condition to this distinct consumer."""
    return replace(specification.sampling_requirement,
        requirement_id="requirement.factorial-confirmation."+specification.fingerprint()[:24],
        consumer_operation_id=assess_node_id(specification))


@dataclass(frozen=True, slots=True)
class ScheduledFactorialCriteriaConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-criteria-config"
    config_id: str
    programme: ScheduledProgramme
    specification: ScheduledFactorialSpecification
    bank: ObjectIdentity
    qualified_parent: ScheduledProgrammeQualifiedParentDeclaration

    def __post_init__(self):
        _confirmation(self.programme, self.specification)
        if (self.config_id != "config."+freeze_node_id(self.specification) or self.bank != self.programme.bank
                or type(self.qualified_parent) is not ScheduledProgrammeQualifiedParentDeclaration):
            raise ValueError("factorial criteria freeze substitutes original bank, qualified-parent declaration or derived config")
        self.qualified_parent.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialFrozenCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-frozen-criteria"
    record_id: str
    configuration: ScheduledFactorialCriteriaConfig
    family_ids: tuple[str, ...]
    sampling_requirement: ScientificRequirementSpec

    def __post_init__(self):
        if (type(self.configuration) is not ScheduledFactorialCriteriaConfig
                or self.record_id != "criteria."+self.configuration.specification.specification_id or self.family_ids != FAMILY_IDS
                or self.sampling_requirement != protected_sampling_requirement(self.configuration.specification)):
            raise ValueError("factorial freeze changes its original full statistical design or twelve comparison slots")
        self.configuration.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialCriteriaBinding(CanonicalRecord):
    """Ordinary blind product/receipt locators, never a scientific qualification."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-criteria-binding"
    binding_id: str
    record: ScheduledFactorialFrozenCriteria
    publication: ArtifactWriteResult
    receipt: CanonicalTaskReceipt
    receipt_publication: ArtifactWriteResult
    execution_plan: ExecutionPlan
    execution_plan_publication: ArtifactWriteResult
    configuration_publication: ArtifactWriteResult
    prior_execution: RecursivePriorExecutionBinding

    def __post_init__(self):
        from .programme_factorial_confirmation_custody import validate_criteria_binding
        validate_criteria_binding(self)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.binding_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialAcquisitionLocator(CanonicalRecord):
    """Exact issued execution controls, without a caller-provided status flag."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-acquisition-locator"
    wave_id: str
    run_id: str
    issued_study: ObjectIdentity
    execution_authority: ObjectIdentity
    package: ObjectIdentity
    execution_plan: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.wave_id)
        validate_stable_id(self.run_id)
        for value, schema in ((self.issued_study, "empirical-lawhood/runtime/issued-executable-study-manifest"),
                (self.execution_authority, "empirical-lawhood/planning/study-operation-authority"),
                (self.package, "empirical-lawhood/api/experiment-package"), (self.execution_plan, ExecutionPlan.SCHEMA)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (schema, "1.0.0"):
                raise ValueError("factorial acquisition locator substitutes an original issued control type")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialConfirmationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-confirmation-config"
    config_id: str
    programme: ScheduledProgramme
    specification: ScheduledFactorialSpecification
    bank: ObjectIdentity
    criteria: ScheduledFactorialCriteriaBinding
    acquisitions: tuple[ScheduledFactorialAcquisitionLocator, ...]
    reduction: ObjectIdentity | None
    data: ObjectIdentity | None

    def __post_init__(self):
        _confirmation(self.programme, self.specification)
        if (self.config_id != "config."+assess_node_id(self.specification) or self.bank != self.programme.bank
                or type(self.criteria) is not ScheduledFactorialCriteriaBinding
                or self.criteria.record.configuration.programme != self.programme
                or self.criteria.record.configuration.specification != self.specification
                or self.criteria.record.configuration.bank != self.bank
                or type(self.acquisitions) is not tuple or any(type(value) is not ScheduledFactorialAcquisitionLocator for value in self.acquisitions)
                or tuple(value.wave_id for value in self.acquisitions) != tuple(value.wave_id for value in self.programme.waves)
                or len({value.run_id for value in self.acquisitions}) != len(self.acquisitions)
                or (self.reduction is None) != (self.data is None)
                or self.reduction is not None and (type(self.reduction) is not ObjectIdentity or self.reduction.object_schema != ScheduledProgrammeReduction.SCHEMA)
                or self.data is not None and (type(self.data) is not ObjectIdentity or self.data.object_schema != ScheduledRevisionDataBank.SCHEMA)):
            raise ValueError("factorial confirmation changes original criteria, full acquisition roster or paired-input association")
        self.criteria.__post_init__()
        for value in self.acquisitions:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialConfirmationSealConfig(CanonicalRecord):
    """Seal input selection, without replacing the original scientific freeze."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-confirmation-seal-config"
    config_id: str
    assessment: ScheduledFactorialConfirmationConfig

    def __post_init__(self):
        if (type(self.assessment) is not ScheduledFactorialConfirmationConfig
                or self.config_id != "config."+input_seal_node_id(self.assessment.specification)):
            raise ValueError("factorial input seal requires its exact original confirmation input design")
        self.assessment.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)

    @property
    def programme(self):
        return self.assessment.programme

    @property
    def specification(self):
        return self.assessment.specification

    @property
    def bank(self):
        return self.assessment.bank

    @property
    def criteria(self):
        return self.assessment.criteria


@dataclass(frozen=True, slots=True)
class ScheduledFactorialConfirmationInputSeal(CanonicalRecord):
    """Blind selection metadata; neither scientific criteria nor authority."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-confirmation-input-seal"
    record_id: str
    configuration: ScheduledFactorialConfirmationSealConfig
    family_ids: tuple[str, ...] = FAMILY_IDS

    def __post_init__(self):
        if (type(self.configuration) is not ScheduledFactorialConfirmationSealConfig
                or self.record_id != "input-seal."+self.configuration.specification.specification_id
                or self.family_ids != FAMILY_IDS):
            raise ValueError("factorial input seal changes its distinct input design or complete comparison family")
        self.configuration.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def confirmation_input_seal(config):
    """Derive distinct metadata bytes from the exact original selection."""
    configuration = ScheduledFactorialConfirmationSealConfig("config."+input_seal_node_id(config.specification), config)
    return ScheduledFactorialConfirmationInputSeal("input-seal."+config.specification.specification_id, configuration)


@dataclass(frozen=True, slots=True)
class ScheduledFactorialCaseCustody(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-case-custody"
    root_id: str
    group_id: str
    state: str
    phase_states: tuple[tuple[str, str], ...]
    receipts: tuple[ObjectIdentity, ...]
    contacts: tuple[ObjectIdentity, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        from .programme_acquisition_custody import acquisition_phase_roles
        validate_stable_id(self.root_id)
        validate_stable_id(self.group_id)
        phases = acquisition_phase_roles("E4_CONFIRMATION")
        states = ("SUCCEEDED", "FAILED", "UNKNOWN", "UNENTERED", "BLOCKED")
        if (type(self.phase_states) is not tuple or type(self.receipts) is not tuple or type(self.contacts) is not tuple
                or tuple(name for name, _ in self.phase_states) != phases or any(value not in states for _, value in self.phase_states)
                or self.state not in ("COMPLETED", "FAILED", "UNKNOWN", "UNENTERED", "INCOMPLETE")
                or len({value.object_id for value in self.receipts}) != len(self.receipts)
                or not sum(value == "SUCCEEDED" for _, value in self.phase_states) <= len(self.receipts) <= len(phases)
                or any(type(value) is not ObjectIdentity or value.object_schema != CanonicalTaskReceipt.SCHEMA for value in self.receipts)
                or len({value.object_id for value in self.contacts}) != len(self.contacts)
                or any(type(value) is not ObjectIdentity or value.object_schema != "empirical-lawhood/runtime/native-effect-contact" for value in self.contacts)
                or self.state != case_custody_state(self.phase_states)
                or self.state != "COMPLETED" and not self.reason_codes):
            raise ValueError("factorial case custody loses original phase states or invents completed scientific evidence")
        require_sorted_unique_strings(self.reason_codes, field_name="factorial original case custody reasons")


def case_custody_state(phase_states):
    """Conservative projection of actual ordinary phases; never infer no entry."""
    values = tuple(value for _, value in phase_states)
    return ("COMPLETED" if all(value == "SUCCEEDED" for value in values) else "UNKNOWN" if "UNKNOWN" in values
        else "FAILED" if "FAILED" in values else "UNENTERED" if all(value == "UNENTERED" for value in values) else "INCOMPLETE")


@dataclass(frozen=True, slots=True)
class ScheduledFactorialWaveCustody(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-wave-custody"
    wave_id: str
    state: str
    receipt: ObjectIdentity | None
    run_terminal: ObjectIdentity | None
    terminal_status: str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent
        validate_stable_id(self.wave_id)
        if (self.state not in ("SUCCEEDED", "FAILED", "UNKNOWN", "UNENTERED", "BLOCKED")
                or self.receipt is not None and (type(self.receipt) is not ObjectIdentity
                    or self.receipt.object_schema != CanonicalTaskReceipt.SCHEMA)
                or self.state == "SUCCEEDED" and self.receipt is None
                or (self.run_terminal is None) != (self.terminal_status is None)
                or self.run_terminal is not None and (type(self.run_terminal) is not ObjectIdentity
                    or (self.run_terminal.object_schema, self.run_terminal.object_version) != (RunRecoveryTerminalEvent.SCHEMA, RunRecoveryTerminalEvent.VERSION)
                    or self.terminal_status not in ("SUCCEEDED", "FAILED", "BLOCKED"))
                or self.run_terminal is None and "MISSING_ORIGINAL_RUN_TERMINAL" not in self.reason_codes
                or self.state != "SUCCEEDED" and not self.reason_codes):
            raise ValueError("factorial wave custody invents successful collector evidence or loses an actual adverse state")
        require_sorted_unique_strings(self.reason_codes, field_name="factorial original collector custody reasons")


def confirmation_deferred_reasons(programme, *, paired_data, cases, waves):
    """Project authenticated custody facts without upgrading missing controls."""
    if (type(programme) is not ScheduledProgramme or programme.mode != "E4_CONFIRMATION"
            or type(cases) is not tuple or any(type(value) is not ScheduledFactorialCaseCustody for value in cases)
            or tuple((value.root_id, value.group_id) for value in cases)
                != tuple((value.root_id, value.independent_group_id) for value in programme.cases)
            or type(waves) is not tuple or any(type(value) is not ScheduledFactorialWaveCustody for value in waves)
            or tuple(value.wave_id for value in waves) != tuple(value.wave_id for value in programme.waves)):
        raise ValueError("factorial deferred readout cannot omit or substitute its original full64/576 acquisition census")
    for value in (*cases, *waves):
        value.__post_init__()
    deferred = set()
    if any(value.state != "COMPLETED" for value in cases) or any(value.state != "SUCCEEDED" for value in waves):
        deferred.add("INCOMPLETE_ORIGINAL_ACQUISITION_CUSTODY")
    if any(value.run_terminal is None for value in waves):
        deferred.add("MISSING_ORIGINAL_RUN_TERMINAL")
    if any(value.terminal_status not in (None, "SUCCEEDED") for value in waves):
        deferred.add("ORIGINAL_RUN_TERMINAL_NOT_SUCCESSFUL")
    if paired_data is None:
        deferred.add("MISSING_ORIGINAL_PAIRED_DATA_BANK")
    return tuple(sorted(deferred))


@dataclass(frozen=True, slots=True)
class ScheduledFactorialConfirmationReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-confirmation-readout"
    record_id: str
    configuration: ObjectIdentity
    programme: ObjectIdentity
    criteria: ObjectIdentity
    group_ids: tuple[str, ...]
    cases: tuple[ScheduledFactorialCaseCustody, ...]
    waves: tuple[ScheduledFactorialWaveCustody, ...]
    calculation: ScheduledFactorialAssessment | None
    family_ids: tuple[str, ...]
    family_slots: tuple[ScheduledFactorialFamilySlot, ...]
    sampling_assumption_status: str
    scientific_admission: str
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        from .programme_factorial import ASSUMPTION_STATUS
        validate_stable_id(self.record_id)
        if (self.configuration.object_schema != ScheduledFactorialConfirmationConfig.SCHEMA
                or self.programme.object_schema != ScheduledProgramme.SCHEMA or self.criteria.object_schema != ScheduledFactorialCriteriaBinding.SCHEMA
                or len(self.group_ids) != 64 or self.group_ids != tuple(sorted(set(self.group_ids))) or len(self.cases) != 576
                or tuple(value.root_id for value in self.cases) != tuple(sorted({value.root_id for value in self.cases}))
                or tuple(sorted({value.group_id for value in self.cases})) != self.group_ids
                or any(sum(value.group_id == group for value in self.cases) != 9 for group in self.group_ids)
                or not self.waves or len({value.wave_id for value in self.waves}) != len(self.waves)
                or self.family_ids != FAMILY_IDS or self.sampling_assumption_status != ASSUMPTION_STATUS
                or tuple(value.comparison_id for value in self.family_slots) != FAMILY_IDS
                or self.calculation is None and any(value.p_value is not None or value.adjusted_p_value is not None
                    or value.conditional_disposition != "UNEVALUABLE" for value in self.family_slots)
                or self.scientific_admission != "UNEVALUABLE" or not self.reason_codes
                or self.calculation is not None and (type(self.calculation) is not ScheduledFactorialAssessment
                    or self.calculation.programme != self.programme or self.calculation.mode != "E4_CONFIRMATION"
                    or tuple(value.group_id for value in self.calculation.groups) != self.group_ids
                    or self.family_slots != self.calculation.family_slots
                    or any(value.state != "COMPLETED" for value in self.cases)
                    or any(value.state != "SUCCEEDED" or value.terminal_status != "SUCCEEDED" for value in self.waves))):
            raise ValueError("protected factorial readout changes full64/576 scope or turns conditional numbers into qualification")
        for value in self.cases:
            value.__post_init__()
        for value in self.waves:
            value.__post_init__()
        for value in self.family_slots:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def scientific_root_validator(config, context):
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.plans import ScientificStage
    from .programme_global import validate_programme_root
    from .programme_factorial_confirmation_custody import require_original_criteria_design
    freezing = type(config) is ScheduledFactorialCriteriaConfig
    sealing = type(config) is ScheduledFactorialConfirmationSealConfig
    assessing = type(config) is ScheduledFactorialConfirmationConfig
    if not (freezing or sealing or assessing):
        raise ValueError("protected factorial root substitutes an installed configuration type")
    config.__post_init__()
    node = (freeze_node_id(config.specification) if freezing else input_seal_node_id(config.specification)
        if sealing else assess_node_id(config.specification))
    access = OutcomeAccess.EVALUATOR_REVEAL if assessing else OutcomeAccess.OUTCOME_BLIND
    visibility = VisibilityCeiling.OUTCOME_VISIBLE if assessing else VisibilityCeiling.PROSPECTIVE
    if freezing:
        expected_configs = ((node, config),)
    else:
        seal = config if sealing else confirmation_input_seal(config).configuration
        expected_configs = tuple(sorted(((input_seal_node_id(config.specification), seal),
            (assess_node_id(config.specification), seal.assessment))))
    if (context.node_id != node or context.stage is not (ScientificStage.EVALUATE if assessing else ScientificStage.FREEZE)
            or context.outcome_access is not access or context.visibility_ceiling is not visibility
            or context.unit_ids != config.programme.group_ids or context.selected_unit_ids != config.programme.group_ids
            or context.complete_unit_census
            or tuple(sorted((value.node_id, value.record) for value in context.config_inputs)) != expected_configs):
        raise ValueError("protected factorial changes its original stage, complete64 groups or declared outcome boundary")
    validate_programme_root(config.programme, context)
    if config.specification.identity not in {value.object_identity for value in context.root.design_inputs}:
        raise ValueError("protected factorial root omits its exact original statistical specification")
    if not freezing:
        require_original_criteria_design(context.root, config.criteria)
    declaration = operation_declarations()[0 if freezing else 2 if sealing else 1]
    expected = {port.port_id for port in declaration.input_ports
        if port.minimum_count or getattr(config, port.port_id, None) is not None}
    links = tuple(value for value in context.links if value.consumer_node_id == node)
    if (len(links) != len(expected) or {value.consumer_input_id for value in links} != expected
            or any(value.scientific_role != "SOURCE" or value.requirement_id is not None or value.connection_id is not None
                or ((value.producer_node_id, value.producer_output_id, value.external_input_id)
                    != (input_seal_node_id(config.specification), "product", None) if value.consumer_input_id == "input-seal"
                    else value.producer_node_id is not None or value.external_input_id is None)
                for value in links)):
        raise ValueError("protected factorial substitutes original external inputs or introduces a same-wave chronology bypass")


class ScheduledFactorialProtectedWorker:
    """Pure calculation after parent-side original issue/custody/reveal replay."""
    def __init__(self, role, manifest=None, verified=None):
        if role not in ("freeze", "assess", "seal"):
            raise ValueError("unknown protected factorial role")
        self.role = role
        self.manifest = manifest or operation_declarations()[0 if role == "freeze" else 2 if role == "seal" else 1].manifest()
        self.verified = verified

    def _inputs(self, context):
        from empirical_lawhood.kernel.decoding import decode_canonical_bytes
        from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
        from empirical_lawhood.kernel.worlds import WorldKind
        from empirical_lawhood.runtime.execution import WorkerInputKind
        from .compact_records import ScheduledCompactBank
        from .programme_records import validate_programme_bank
        from .programme_qualified_parent import validate_qualified_parent_declaration
        from .programme_factorial_confirmation_custody import VerifiedFactorialInvocation
        freezing = self.role == "freeze"
        sealing = self.role == "seal"
        assessing = self.role == "assess"
        if (type(self.verified) is not VerifiedFactorialInvocation or context.permissions != self.manifest.permissions
                or context.outcome_access is not (OutcomeAccess.EVALUATOR_REVEAL if assessing else OutcomeAccess.OUTCOME_BLIND)
                or not self.manifest.resource_ceiling.contains(context.resource_budget)):
            raise PermissionError("protected factorial requires installed current authority/custody preparation before any input read")
        self.verified.validate_invocation(context)
        if assessing:
            authority = context.scientific_adjudication_context
            if (authority is None or authority.execution_plan != self.verified.execution_plan
                    or self.verified.reveal_authority is None or authority.plumbing_only or authority.fixture_scope_id is not None
                    or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
                    or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
                    or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE):
                raise PermissionError("factorial protected inputs require the actual current genuine reveal context before reads")
        config_type = (ScheduledFactorialCriteriaConfig if freezing else ScheduledFactorialConfirmationSealConfig
            if sealing else ScheduledFactorialConfirmationConfig)
        kinds = (config_type, ScheduledProgramme, ScheduledFactorialSpecification, ScheduledCompactBank,
            *((ScheduledFactorialCriteriaBinding,) if not freezing else ()),
            *((ScheduledFactorialConfirmationInputSeal, ScheduledProgrammeReduction, ScheduledRevisionDataBank) if assessing else ()))
        by_schema = {kind.SCHEMA: kind for kind in kinds}
        records = {}
        for port in context.input_ports:
            kind = by_schema.get(port.payload_schema)
            sealed = kind in (ScheduledProgrammeReduction, ScheduledRevisionDataBank)
            if (kind is None or kind in records or port.media_type != "application/json"
                    or port.kind is not (WorkerInputKind.DEPENDENCY if kind is ScheduledFactorialConfirmationInputSeal else WorkerInputKind.EXTERNAL)
                    or port.outcome_access is not (OutcomeAccess.EVALUATION_SEALED if sealed else OutcomeAccess.OUTCOME_BLIND)
                    or port.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE):
                raise PermissionError("protected factorial changes exact original blind/sealed input contracts")
            cursor = port.cursor()
            try:
                raw = cursor.read()
            finally:
                cursor.close()
            if len(raw) != port.size_bytes:
                raise ValueError("protected factorial changes complete original materialized bytes")
            value = decode_canonical_bytes(raw, kind, maximum_bytes=None)
            if kind is config_type and (port.artifact_id != context.config.artifact_id or value.config_id != context.config.config_id
                    or context.config.config_schema != value.SCHEMA or context.config.content_sha256 != value.fingerprint()):
                raise ValueError("protected factorial substitutes its complete actual external configuration")
            records[kind] = value
        required = {config_type, ScheduledProgramme, ScheduledFactorialSpecification, ScheduledCompactBank}
        if not required <= set(records):
            raise ValueError("protected factorial omits an original complete scientific control")
        config = records[config_type]
        self.verified.validate_context(config, context)
        expected_node = (freeze_node_id(config.specification) if freezing else input_seal_node_id(config.specification)
            if sealing else assess_node_id(config.specification))
        if (context.task_id != expected_node or records[ScheduledProgramme] != config.programme
                or records[ScheduledFactorialSpecification] != config.specification
                or ObjectIdentity.from_record(records[ScheduledCompactBank].bank_id, records[ScheduledCompactBank]) != config.bank):
            raise ValueError("protected factorial substitutes original programme, criteria or bank")
        bank = records[ScheduledCompactBank]
        validate_programme_bank(config.programme, bank)
        declaration = config.qualified_parent if freezing else config.criteria.record.configuration.qualified_parent
        validate_qualified_parent_declaration(bank, declaration)
        if self.verified.qualified_parent != declaration.identity:
            raise PermissionError("protected factorial changes independently authenticated original qualified parent")
        if not freezing:
            required.add(ScheduledFactorialCriteriaBinding)
            if records.get(ScheduledFactorialCriteriaBinding) != config.criteria:
                raise ValueError("protected factorial substitutes its actual pre-acquisition criteria/receipt binding")
            if assessing:
                required.add(ScheduledFactorialConfirmationInputSeal)
                if records.get(ScheduledFactorialConfirmationInputSeal) != confirmation_input_seal(config):
                    raise ValueError("protected factorial substitutes its exact internal confirmation input-design seal")
            if assessing and config.data is not None:
                required.update((ScheduledProgrammeReduction, ScheduledRevisionDataBank))
                reduction, data = records.get(ScheduledProgrammeReduction), records.get(ScheduledRevisionDataBank)
                if (reduction is None or data is None or ObjectIdentity.from_record(reduction.reduction_id, reduction) != config.reduction
                        or data.identity != config.data):
                    raise ValueError("protected factorial substitutes authenticated original paired outcome bytes")
        if set(records) != required:
            raise ValueError("protected factorial adds or removes its exact original scientific input census")
        from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
        outputs = ((context.task_id+".product", (ScheduledFactorialFrozenCriteria if freezing else
            ScheduledFactorialConfirmationInputSeal).SCHEMA),) if not assessing else (
            (context.task_id+".adjudication", ScientificAdjudicationRecord.SCHEMA),
            (context.task_id+".product", ScheduledFactorialConfirmationReadout.SCHEMA))
        if tuple((value.output_id, value.payload_schema) for value in context.output_ports) != outputs:
            raise ValueError("protected factorial changes its complete original output census")
        return config, records

    def execute(self, context):
        from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
        from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
        from empirical_lawhood.kernel.worlds import WorldKind
        from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationRecord
        from empirical_lawhood.runtime.artifacts import ReceiptCheck
        from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
        from .programme_factorial import ASSUMPTION_STATUS, ScheduledFactorialFamilySlot, assess_programme_factorial
        config, records = self._inputs(context)
        if self.role != "assess":
            product = (ScheduledFactorialFrozenCriteria("criteria."+config.specification.specification_id, config, FAMILY_IDS,
                protected_sampling_requirement(config.specification)) if self.role == "freeze" else confirmation_input_seal(config.assessment))
            expected = ((context.task_id+".product", product.SCHEMA),)
            payloads = (TaskOutputPayload(expected[0][0], product.canonical_bytes()),)
            check = ("original-full64-factorial-criteria-freeze" if self.role == "freeze" else
                "original-full64-factorial-confirmation-input-design-seal")
        else:
            authority = context.scientific_adjudication_context
            if (authority is None or authority.plumbing_only or authority.fixture_scope_id is not None
                    or authority.evidence_world_kind is not WorldKind.NUMERICAL_SIMULATOR
                    or authority.outcome_access is not OutcomeAccess.EVALUATION_REVEALED
                    or authority.visibility_ceiling is not VisibilityCeiling.OUTCOME_VISIBLE
                    or authority.information_cutoffs != tuple(sorted((ObjectIdentity.from_record(value.information_cutoff.cutoff_id,
                        value.information_cutoff) for value in config.programme.cases), key=lambda value: value.object_id))):
                raise PermissionError("factorial confirmation lacks the exact genuine full64 revealed scientific context")
            deferred = confirmation_deferred_reasons(config.programme, paired_data=config.data, cases=self.verified.cases, waves=self.verified.waves)
            complete = not deferred
            calculation = (assess_programme_factorial(config.specification, config.programme, records[ScheduledProgrammeReduction],
                records[ScheduledRevisionDataBank], assessment_id="assessment."+config.specification.specification_id) if complete else None)
            slots = calculation.family_slots if calculation is not None else tuple(ScheduledFactorialFamilySlot(name, None, None,
                "UNEVALUABLE", tuple(sorted(deferred))) for name in FAMILY_IDS)
            reasons = tuple(sorted(("SAMPLING_ASSUMPTION_NOT_AUTHENTICATED", *deferred)))
            product = ScheduledFactorialConfirmationReadout("readout."+config.specification.specification_id, config.identity,
                config.programme.identity, config.criteria.identity, config.programme.group_ids, self.verified.cases, self.verified.waves,
                calculation, FAMILY_IDS, slots, ASSUMPTION_STATUS, "UNEVALUABLE", reasons)
            adjudication = ScientificAdjudicationRecord("adjudication."+context.run_id+"."+context.task_id, context.run_id, context.task_id,
                authority.execution_plan, context.input_materialization_ids, tuple(sorted(value.logical_artifact_id for value in context.output_ports)),
                context.dependency_receipt_ids, authority.evidence_world_id, authority.evidence_world_kind, authority.relation,
                authority.independent_unit_id, authority.information_cutoffs, authority.visibility_ceiling, authority.outcome_access,
                AdjudicationEvaluability.UNEVALUABLE, ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE, reasons)
            expected = ((context.task_id+".adjudication", ScientificAdjudicationRecord.SCHEMA), (context.task_id+".product", product.SCHEMA))
            payloads = (TaskOutputPayload(expected[0][0], adjudication.canonical_bytes()), TaskOutputPayload(expected[1][0], product.canonical_bytes()))
            check = "original-full64-conditional-factorial-confirmation"
        if tuple((value.output_id, value.payload_schema) for value in context.output_ports) != expected:
            raise ValueError("protected factorial changes its complete original output census")
        return RunnerResult(payloads, (ReceiptCheck(check, True, ()),))


def operation_declarations():
    from functools import partial
    from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
    from empirical_lawhood.runtime.execution import ParentPreparedTaskRunner
    from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
    from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
    from empirical_lawhood.runtime.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
    from .compact_records import ScheduledCompactBank
    declarations = []
    for role, config_type in (("freeze", ScheduledFactorialCriteriaConfig), ("assess", ScheduledFactorialConfirmationConfig),
            ("seal", ScheduledFactorialConfirmationSealConfig)):
        freezing = role == "freeze"
        assessing = role == "assess"
        inputs = (("bank", ScheduledCompactBank), ("programme", ScheduledProgramme), ("specification", ScheduledFactorialSpecification))
        if not freezing:
            inputs = tuple(sorted((*inputs, ("criteria", ScheduledFactorialCriteriaBinding),
                *(((("input-seal", ScheduledFactorialConfirmationInputSeal), ("data", ScheduledRevisionDataBank),
                    ("reduction", ScheduledProgrammeReduction))) if assessing else ()))))
        product_type = (ScheduledFactorialFrozenCriteria if freezing else ScheduledFactorialConfirmationReadout
            if assessing else ScheduledFactorialConfirmationInputSeal)
        outputs = ((OutputTemplate("product", product_type.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),)
            if not assessing else (OutputTemplate("adjudication", ScientificAdjudicationRecord.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),
                OutputTemplate("product", ScheduledFactorialConfirmationReadout.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json")))
        kinds = (config_type, product_type, *(kind for _, kind in inputs), *((ScientificAdjudicationRecord,) if assessing else ()))
        permissions = (CapabilityPermission.READ_FROZEN_MODELS, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, *((CapabilityPermission.READ_SEALED_OUTCOMES, CapabilityPermission.REVEAL_OUTCOMES) if assessing else ()))
        def prepare(supplier, runner):
            return ParentPreparedTaskRunner(runner.manifest, lambda context: supplier.prepare_factorial_task(context, runner))
        declarations.append(RecursiveOperationDeclaration(capability_key=FREEZE if freezing else ASSESS if assessing else INPUT_SEAL,
            capability_version="1.1.0" if assessing else "1.0.0",
            implementation_id=("original-full64-protected-factorial-assess-with-input-design-seal-v2" if assessing else
                "original-full64-protected-factorial-"+role+"-v1"),
            kind=CapabilityKind.EVALUATOR if assessing else CapabilityKind.EXPERIMENT_DESIGNER, config_record_type=config_type,
            stage=ScientificStage.EVALUATE if assessing else ScientificStage.FREEZE,
            input_ports=tuple(RecursivePortContract(name, kind.SCHEMA, "application/json", None,
                minimum_count=0 if name in ("data", "reduction") else 1) for name, kind in inputs), outputs=outputs,
            permissions=tuple(sorted(permissions)), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=OutcomeAccess.EVALUATOR_REVEAL if assessing else OutcomeAccess.OUTCOME_BLIND,
            visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE if assessing else VisibilityCeiling.PROSPECTIVE,
            resources=ResourceBudget(1, None, 0, None, None, None),
            conformance_check_ids=("actual-original-issued-criteria-and-receipt-before-acquisition",
                "conditional-numbers-do-not-authenticate-assumptions", "full64-576-case-custody-preservation"),
            runner_factory=partial(ScheduledFactorialProtectedWorker, role),
            record_codecs={kind.SCHEMA: kind for kind in kinds}, input_record_types=tuple(sorted((kind for _, kind in inputs), key=lambda kind: (kind.SCHEMA, kind.VERSION))),
            scientific_hooks=RecursiveScientificHooks(scientific_unit_ids=lambda config: config.programme.group_ids,
                scientific_root_validator=scientific_root_validator, adjudication_output_id="adjudication" if assessing else None),
            execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.REVEAL if assessing else BarrierKind.FREEZE,
                runner_preparation_factory=prepare), provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,)))
    return tuple(declarations)


def operation_factories():
    return tuple(value.provider_factory() for value in operation_declarations())


def operation_manifests():
    return tuple(value.manifest() for value in operation_declarations())


@dataclass(frozen=True, slots=True)
class ScheduledFactorialSamplingReadout(CanonicalRecord):
    """Additive premise assessment; original conditional bytes stay unchanged.

    This semantic readout is not an issue, reveal or qualification act. An
    installed protected caller must authenticate the supplied original records
    through its existing source/custody owner before using it for adjudication.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/factorial-sampling-readout"
    VERSION: ClassVar[str] = "2.0.0"
    record_id: str
    calculation: ObjectIdentity
    sampling: MatrixSamplingAdmission
    group_ids: tuple[str, ...]
    family_slots: tuple[tuple[str, str, str], ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_sampling_assessment import E4_FACTORIAL, MatrixSamplingAdmission

        validate_stable_id(self.record_id)
        if (type(self.calculation) is not ObjectIdentity or self.calculation.object_schema != ScheduledFactorialAssessment.SCHEMA
                or type(self.sampling) is not MatrixSamplingAdmission or self.sampling.premise != E4_FACTORIAL
                or len(self.group_ids) not in (32, 64)
                or tuple(name for name, _, _ in self.family_slots) != FAMILY_IDS
                or any(conditional not in ("REJECTED", "NOT_REJECTED", "UNEVALUABLE")
                    or scientific not in ("REJECTED", "NOT_REJECTED", "UNEVALUABLE")
                    or scientific != "UNEVALUABLE" and (self.sampling.disposition != "SUPPORTED" or scientific != conditional)
                    for _, conditional, scientific in self.family_slots)):
            raise ValueError("factorial sampling readout changes complete groups/family or promotes unsupported tests")
        require_sorted_unique_strings(self.group_ids, field_name="factorial sampling whole groups")
        require_sorted_unique_strings(self.reason_codes, field_name="factorial sampling reasons", allow_empty=False)
        self.sampling.__post_init__()


def assess_factorial_sampling(*, request, evidence, programme, specification, calculation):
    """Assess the E4 premise separately for all seven declared contrasts.

    Common-normality applies to whole-group contrasts, including the actual
    preparation-family mixture. Passing normality diagnostics alone is not the
    required scientific warrant. Five other global slots remain unevaluable;
    this function never removes them from the original Holm family.
    """
    from empirical_lawhood.adapters.methods.matrix_sampling_assessment import (
        E4_FACTORIAL, MatrixSamplingRequest, assess_matrix_sampling,
    )
    from .programme_factorial import E4_COMPARISONS

    if (type(programme) is not ScheduledProgramme or type(specification) is not ScheduledFactorialSpecification
            or type(calculation) is not ScheduledFactorialAssessment or type(request) is not MatrixSamplingRequest):
        raise TypeError("factorial sampling requires exact original programme, calculation and sampling request")
    programme.__post_init__()
    specification.__post_init__()
    calculation.__post_init__()
    request.__post_init__()
    scope = request.scope
    if (specification.programme != programme.identity or calculation.programme != programme.identity
            or calculation.specification != specification or scope.premise != E4_FACTORIAL
            or scope.specification != specification.identity or scope.population != programme.identity
            or scope.source != programme.bank or scope.fixed_map != specification.identity
            or scope.unit_ids != programme.group_ids or scope.endpoint_ids != tuple(sorted(E4_COMPARISONS))
            or tuple(row.group_id for row in calculation.groups) != programme.group_ids):
        raise ValueError("factorial sampling substitutes a source, endpoint map, test or independent whole-group scope")
    sampling = assess_matrix_sampling(request, evidence)
    slots = tuple((row.comparison_id, row.conditional_disposition,
        row.conditional_disposition if sampling.disposition == "SUPPORTED" and row.comparison_id in E4_COMPARISONS
        else "UNEVALUABLE") for row in calculation.family_slots)
    reasons = tuple(sorted({*sampling.reason_codes, "COMPLETE_TWELVE_SLOT_FAMILY_RETAINED",
        "THREE_WAY_INTERACTION_DESCRIPTIVE_ONLY", "UNSUPPLIED_CROSS_PHASE_SLOTS_UNEVALUABLE"}))
    return ScheduledFactorialSamplingReadout("sampling." + calculation.assessment_id,
        ObjectIdentity.from_record(calculation.assessment_id, calculation), sampling, programme.group_ids, slots, reasons)
