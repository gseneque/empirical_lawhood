# SPDX-License-Identifier: MPL-2.0
"""Closed role-bound projection of the original controlled forecast operands.

The editable wrapper selects existing records. Its request digest and scientific
graph are derived from those records; neither is an admission or replay grant.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar, Mapping

from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
from empirical_lawhood.adapters.methods.battery_observation_inquiry.contracts import ObservationReadout
from empirical_lawhood.adapters.methods.battery_observation_inquiry.precision_assessment import PrecisionReassessment
from empirical_lawhood.adapters.methods.battery_refined_inquiry.operation_bindings import SourcePolicyAdmission
from empirical_lawhood.adapters.methods.battery_refined_inquiry.source_derived_preparation import SourceRootPreparation, SourceRootAssessment
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import operation_bindings as original
from empirical_lawhood.adapters.methods.battery_segmented_inquiry import recursive_translation as translation
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import require_forecast_records
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole, DevelopmentStudySpec, ScientificConnectionSpec, ScientificRequirementSpec
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_sha256
from . import contracts as c, durable_roster as dr, forecast_step_control as control
from . import preparation_contracts as pc, segmented_contracts as sc, segmented_native as native, segmented_roster as sr
from .representable_clock import RepresentableClockAssessment
from . import controlled_retained_work as retained


CAPABILITY_KEY = original.NAMESPACE + ".controlled-forecast"
ROLE_TYPES = {
    "admission": SourcePolicyAdmission,
    "baseline-request": native.SegmentRequest,
    "comparison-budget": control.ForecastComparisonBudget,
    "control": control.ForecastStepPolicy,
    "entry": sr.ProspectiveMethodDisposition,
    "forecast-config": original.SegmentedOperationConfig,
    "history": ObstructionAssessment,
    "history-contribution": ContributionManifest,
    "method": sc.SegmentedMethodProtocol,
    "native-config": sc.SegmentedNativeConfig,
    "original-negative": ObservationReadout,
    "original-roster": dr.FrozenForecastRoster,
    "policy": c.NumericalPolicy,
    "precision": PrecisionReassessment,
    "preparation-chen": SourceRootPreparation,
    "preparation-oregan": SourceRootPreparation,
    "producing-provenance": NumericalProducingProvenance,
    "representable-clock-0": RepresentableClockAssessment,
    "representable-clock-1": RepresentableClockAssessment,
    "roster": sr.SegmentedQualificationRoster,
    "selected-protocol": pc.PreparationProtocol,
    "selected-roster": dr.FrozenForecastRoster,
    "selection": c.NumericalSelection,
    "source": c.RefinedSource,
    "source-assessment-chen": SourceRootAssessment,
    "source-assessment-oregan": SourceRootAssessment,
    "uncertain-work": dr.UnknownDiagnosticWork,
}
ORIGINAL_ROLE_TYPES = dict(ROLE_TYPES)
ROLE_TYPES.update({
    "retained-root-selection": retained.RetainedForecastRootSelection,
    "retained-condition": retained.RetainedForecastWorkCondition,
    "retained-contact": retained.NativeEffectContact,
    "retained-event": retained.TaskRecoveryEvent,
    "retained-plan": retained.DevelopmentExecutionPlan,
    "retained-task": retained.ExecutionTask,
    "retained-config": original.SegmentedOperationConfig,
    "retained-step-evidence": control.ActualForecastStepAssignment,
})
_IDENTITY_FIELDS = {
    "admission": "admission_id", "baseline-request": "request_id", "comparison-budget": "budget_id",
    "control": "policy_id", "entry": "disposition_id", "forecast-config": "config_id",
    "history": "product_id", "history-contribution": "contribution_id", "method": "method_id",
    "native-config": "config_id", "original-negative": "readout_id", "original-roster": "roster_id",
    "policy": "policy_id", "precision": "assessment_id", "preparation-chen": "preparation_id",
    "preparation-oregan": "preparation_id", "representable-clock-0": "assessment_id",
    "representable-clock-1": "assessment_id", "roster": "roster_id", "selected-protocol": "protocol_id",
    "selected-roster": "roster_id", "source": "source_id", "source-assessment-chen": "assessment_id",
    "source-assessment-oregan": "assessment_id", "uncertain-work": "record_id", "retained-root-selection": "selection_id",
    "retained-condition": "condition_id", "retained-contact": None, "retained-event": "event_id",
    "retained-plan": "execution_plan_id", "retained-task": "task_id", "retained-config": "config_id",
    "retained-step-evidence": "assignment_id",
}


def record_identity(role, record):
    """Role, rather than object ID or schema, selects each original record."""
    if role not in ROLE_TYPES or type(record) is not ROLE_TYPES[role]:
        raise ValueError("controlled forecast substitutes a closed typed scientific role")
    record.__post_init__()
    if role == "retained-contact":
        return ObjectIdentity.from_record("native-contact." + record.run_id + "." + record.task_id, record)
    if role == "producing-provenance":
        return record.identity
    if role == "selection":
        return ObjectIdentity.from_record("selection." + record.policy_id, record)
    return ObjectIdentity.from_record(getattr(record, _IDENTITY_FIELDS[role]), record)


def request_sha256(native_config, selected_control):
    """Only the original physical recipe and actual selected step define work."""
    if type(native_config) is not sc.SegmentedNativeConfig or type(selected_control) is not control.ForecastStepPolicy:
        raise ValueError("controlled request requires its original native recipe and exact step policy")
    native_config.__post_init__()
    selected_control.__post_init__()
    return sha256(canonical_json_bytes({"original_forecast_primitive": original.forecast_primitive(native_config).decode(),
        "maximum_internal_step_s": selected_control.maximum_internal_step_s})).hexdigest()


def node_id(index):
    if type(index) is not int or not 0 <= index < 54:
        raise ValueError("controlled forecast requires an original complete-roster ordinal")
    return CAPABILITY_KEY + "." + f"{index:03d}"


@dataclass(frozen=True, slots=True)
class HistoricalControlledForecastConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/controlled-forecast-config"
    VERSION: ClassVar[str] = "1.0.0"
    ROLE_TYPES: ClassVar[dict] = ORIGINAL_ROLE_TYPES
    config_id: str
    index: int
    role_bindings: tuple[tuple[str, ObjectIdentity], ...]
    native_request_sha256: str
    development_root: DevelopmentStudySpec
    history_requirement: ScientificRequirementSpec
    history_connection: ScientificConnectionSpec

    def __post_init__(self):
        if (self.config_id != "config." + node_id(self.index) or type(self.role_bindings) is not tuple
                or tuple(role for role, _ in self.role_bindings) != tuple(sorted(self.ROLE_TYPES))):
            raise ValueError("controlled forecast changes its complete role/config census")
        for role, ref in self.role_bindings:
            kind = self.ROLE_TYPES[role]
            if type(ref) is not ObjectIdentity or (ref.object_schema, ref.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("controlled forecast changes an original role schema/revision")
        validate_sha256(self.native_request_sha256)
        if (type(self.development_root) is not DevelopmentStudySpec
                or type(self.history_requirement) is not ScientificRequirementSpec
                or type(self.history_connection) is not ScientificConnectionSpec):
            raise ValueError("controlled forecast needs its derived original scientific graph")
        for record in (self.development_root, self.history_requirement, self.history_connection):
            record.__post_init__()
        refs = dict(self.role_bindings)
        node, requirement, connection = node_id(self.index), self.history_requirement, self.history_connection
        if (self.development_root.question != original.QUESTION or self.development_root.assigned_unit_ids != (c.UNIT,)
                or requirement.requirement_id != "requirement." + node + ".actual-unknown-history"
                or requirement.consumer_operation_id != node or requirement.assessment_operation_id != node
                or requirement.condition_role is not ConditionRole.EVIDENTIAL
                or requirement.permitted_roles != (ContributionRole.RETAINED_ANALYSIS_INPUT,)
                or connection.connection_id != "connection." + node + ".actual-unknown-history"
                or connection.requirement_id != requirement.requirement_id or connection.assessment_operation_id != node
                or connection.consumer_input_id != "history" or connection.external_input_id != "external." + node + ".history"
                or connection.supplier_operation_id is not None or connection.supplier_output_id is not None
                or connection.supplier_contribution != refs["history-contribution"]
                or connection.claim_id != "claim." + original.NAMESPACE
                or connection.evidence_role is not ContributionRole.RETAINED_ANALYSIS_INPUT):
            raise ValueError("controlled forecast substitutes its original adverse-history condition/connection")
        root_refs = set(self.development_root.scientific_operands)
        required_refs = {ref for role, ref in self.role_bindings if not (
            (role == "original-roster" and ref.object_id == refs["selected-roster"].object_id and ref != refs["selected-roster"])
            or (role == "retained-config" and ref.object_id == refs["forecast-config"].object_id and ref != refs["forecast-config"]))}
        if not required_refs.issubset(root_refs):
            raise ValueError("controlled forecast omits an exact role operand from its scientific root")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)

    @property
    def operands(self):
        return self.development_root.scientific_operands


@dataclass(frozen=True, slots=True)
class ControlledForecastConfig(HistoricalControlledForecastConfig):
    """Current contract adds actual unfinished-parent custody;1.0 stays readable."""
    VERSION: ClassVar[str] = "1.1.0"
    ROLE_TYPES: ClassVar[dict] = ROLE_TYPES
    retained_root_selection: retained.RetainedForecastRootSelection
    retained_work_condition: retained.RetainedForecastWorkCondition

    def __post_init__(self):
        super(ControlledForecastConfig, self).__post_init__()
        if (type(self.retained_root_selection) is not retained.RetainedForecastRootSelection
                or self.retained_root_selection.identity != dict(self.role_bindings)["retained-root-selection"]):
            raise ValueError("controlled forecast substitutes its selected original operational custody root")
        self.retained_root_selection.__post_init__()
        refs = dict(self.role_bindings)
        if (type(self.retained_work_condition) is not retained.RetainedForecastWorkCondition
                or self.retained_work_condition.identity != refs["retained-condition"]
                or self.retained_work_condition.selected_root != self.retained_root_selection.identity):
            raise ValueError("controlled forecast substitutes its exact derived original unfinished-work condition")
        for role, ref in self.retained_root_selection.records:
            if role in {"assignment-receipt", "assignment-definition"}:
                continue
            name = "retained-step-evidence" if role == "assignment" else "retained-" + role
            if refs[name] != ref:
                raise ValueError("controlled forecast selected root substitutes an original primary role binding")
        require_permitted_config(self)


def require_permitted_config(config):
    retained.require_permitted_work(config.retained_work_condition,
        retained.work_from_request(config.native_request_sha256, config.history_requirement.scope), config.identity)


def retained_port_records(records):
    return {role: records["retained-" + name] for role, name in (
        ("contact", "contact"), ("event", "event"), ("plan", "plan"), ("task", "task"),
        ("config", "config"), ("assignment", "step-evidence"))}


def require_retained_inputs(records, *, successor_config):
    selected = records["retained-root-selection"]
    condition = records["retained-condition"]
    derived = retained.derive_condition(selected, retained_port_records(records))
    if derived != condition:
        raise ValueError("controlled forecast substitutes its derived exact original UNKNOWN work condition")
    retained.require_no_uncertain_replay(condition, records["native-config"], records["control"], successor_config)


def control_operands(records):
    return (records["control"], records["original-roster"], records["selected-roster"], records["precision"],
        (records["representable-clock-0"], records["representable-clock-1"]), records["original-negative"], records["baseline-request"])


def require_scientific_inputs(records):
    """Validate actual scientific witnesses without claiming their publication."""
    if set(records) != set(ORIGINAL_ROLE_TYPES) - {"history-contribution"}:
        raise ValueError("controlled forecast omits or adds an original scientific witness role")
    for role, record in records.items():
        record_identity(role, record)
    base, selected_control = records["forecast-config"], records["control"]
    require_forecast_records(base, records)
    control.require_retained_evidence(*control_operands(records))
    control.require_config(selected_control, records["selected-roster"], records["native-config"])
    if (records["roster"].original_selection != records["selected-roster"]
            or records["comparison-budget"] != selected_control.comparison_budget):
        raise ValueError("controlled forecast substitutes the selected complete roster or comparison budget")


def build_config(records: Mapping[str, CanonicalRecord], *, study_id):
    """Recompute all original gates from complete actual records; execute nothing."""
    if set(records) != set(ROLE_TYPES):
        raise ValueError("controlled forecast omits or adds an original scientific role")
    bindings = tuple((role, record_identity(role, records[role])) for role in sorted(ROLE_TYPES))
    base, selected_control = records["forecast-config"], records["control"]
    require_scientific_inputs({role: value for role, value in records.items() if role in ORIGINAL_ROLE_TYPES and role != "history-contribution"})
    parent = records["history-contribution"]
    products = tuple(row for row in parent.products if row.record == base.source.diagnostic
        and row.role is ContributionRole.RETAINED_ANALYSIS_INPUT)
    if len(products) != 1:
        raise ValueError("controlled forecast loses its exact original adverse-history contribution")
    root = original.development_root(base, study_id=study_id)
    # Both roster roles remain exact config/port bindings. A repeated scientific
    # label cannot represent two different operands in the existing flat root.
    values = {row.object_id: row for row in root.scientific_operands}
    bindings_by_role = dict(bindings)
    for role, ref in bindings:
        if ((role == "original-roster" and ref.object_id == records["control"].selected_roster.object_id
                and ref != records["control"].selected_roster) or (role == "retained-config"
                and ref.object_id == bindings_by_role["forecast-config"].object_id and ref != bindings_by_role["forecast-config"])):
            continue
        if values.setdefault(ref.object_id, ref) != ref:
            raise ValueError("controlled scientific root collides outside its explicit original-roster alias")
    root = replace(root, scientific_operands=tuple(values[key] for key in sorted(values)))
    requirement, connection = translation.requirement_pair(base, parent, products[0])
    node = node_id(base.index)
    requirement = replace(requirement, requirement_id="requirement." + node + ".actual-unknown-history",
        consumer_operation_id=node, assessment_operation_id=node)
    connection = replace(connection, connection_id="connection." + node + ".actual-unknown-history",
        requirement_id=requirement.requirement_id, assessment_operation_id=node, external_input_id="external." + node + ".history")
    require_retained_inputs(records, successor_config=record_identity("forecast-config", base))
    return ControlledForecastConfig("config." + node, base.index, bindings,
        request_sha256(records["native-config"], selected_control), root, requirement, connection, records["retained-root-selection"], records["retained-condition"])


def require_config_records(config, records):
    if type(config) is not ControlledForecastConfig or build_config(records, study_id=config.development_root.study_id) != config:
        raise ValueError("controlled forecast config/root/request differs from its complete original role-bound records")


def native_effect_slot_ids(config):
    return ("native.battery-charging." + config.native_request_sha256,)


def authenticate_prior_retained_work(plane, config_inputs):
    """Authenticate old primary evidence before publication and each retained read."""
    del plane  # The original explicitly selected guarded root owns this custody.
    for row in config_inputs:
        config = row.record
        if type(config) is not ControlledForecastConfig:
            raise ValueError("controlled forecast publication substitutes its current exact configuration")
        condition, originals = retained.authenticate_primary(config.retained_root_selection)
        refs = dict(config.role_bindings)
        if condition.identity != refs["retained-condition"] or condition != config.retained_work_condition:
            raise ValueError("controlled forecast publication substitutes its exact derived UNKNOWN condition")
        for role, record in originals.items():
            if role in {"assignment-receipt", "assignment-definition"}:
                continue
            name = "retained-step-evidence" if role == "assignment" else "retained-" + role
            if record_identity(name, record) != refs[name]:
                raise ValueError("controlled forecast publication substitutes an original primary input role")
        native = original.roster_for(originals["config"]).configurations[originals["config"].index]
        # Unknown old work cannot be cleared by an unrelated wrapper/config ID.
        retained.require_no_uncertain_replay(condition, native, originals["assignment"].control, config.identity)
