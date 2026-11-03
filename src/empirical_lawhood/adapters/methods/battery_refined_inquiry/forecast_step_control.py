# SPDX-License-Identifier: MPL-2.0
"""Prospective complete-roster accuracy operands over existing native custody.

This owner changes only the explicitly selected internal step, with native
tolerances carried by the existing NumericalPolicy. Comparison weights are a
separate scientific operand. Neither a declaration nor actual assignment admits
a model, clears prior UNKNOWN work, or qualifies a full forecast.
"""

from contextlib import contextmanager
from dataclasses import dataclass, replace
from decimal import Decimal
import json
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkOutput
from . import contracts as c, durable_roster as dr, prepared_native as passive
from . import segmented_contracts as sc, segmented_native as native
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import NativeSegmentedRunner

D = Decimal
SCOPE = "PROSPECTIVE_FULL54_NUMERICAL_HYPOTHESIS;NO_QUALIFICATION_OR_ENTRY_AUTHORITY"
ASSIGNMENT_KIND = "ACTUAL_SOLVER_CONSTRUCTOR_AND_COMPLETE_RETURNED_OPTIONS;NOT_CONVERGENCE"


def identity(record, field):
    return ObjectIdentity.from_record(getattr(record, field), record)


def _primitive(value):
    return canonical_json_bytes(passive._freeze(value)).decode()


def _bits(value):
    return {"binary64": float(value).hex()}


def prospective_selection(original, *, policy_id, source_id, roster_id):
    """Keep every scientific slot and mesh/band; commit the stated tolerance ladder."""
    if type(original) is not dr.FrozenForecastRoster:
        raise ValueError("prospective selection needs its complete original frozen roster")
    original.__post_init__()
    if policy_id == original.policy.policy_id or source_id == original.source.source_id:
        raise ValueError("prospective numerical selection requires distinct committed source and policy identities")
    views = tuple(replace(row, rtol=D("1e-11") if row.view_id == "dfn-tolerance" else D("1e-9"),
        atol=D("1e-12") if row.view_id == "dfn-tolerance" else D("1e-10")) for row in original.policy.views)
    selection = replace(original.policy.selection, policy_id=policy_id, views=views)
    policy = replace(original.policy, policy_id=policy_id, views=views, protocol_sha256=selection.fingerprint())
    source = replace(original.source, source_id=source_id, policy=c.identity(policy), protocol_sha256=selection.fingerprint())
    return replace(dr.freeze_forecast_roster(source, policy), roster_id=roster_id)


@dataclass(frozen=True, slots=True)
class ForecastComparisonBudget(CanonicalRecord):
    """Explicit fixed weights; these are not the selected native solver weights."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-comparison-budget"
    budget_id: str
    selected_roster: ObjectIdentity
    rtol: Decimal = D("1e-7")
    atol: Decimal = D("1e-8")
    derivative_time_scale_s: Decimal = D(1)
    interpretation: str = "COMPONENTWISE_CONVERGENCE;NO_SOLVER_ERROR_ENCLOSURE_OR_PHYSICAL_ACCURACY"

    def __post_init__(self):
        validate_stable_id(self.budget_id)
        if (type(self.selected_roster) is not ObjectIdentity or self.selected_roster.object_schema != dr.FrozenForecastRoster.SCHEMA
                or any(type(getattr(self, name)) is not D for name in ("rtol", "atol", "derivative_time_scale_s"))
                or (self.rtol, self.atol, self.derivative_time_scale_s) != (D("1e-7"), D("1e-8"), D(1))
                or self.interpretation != "COMPONENTWISE_CONVERGENCE;NO_SOLVER_ERROR_ENCLOSURE_OR_PHYSICAL_ACCURACY"):
            raise ValueError("forecast comparison budget changes fixed scientific weights or claim")


@dataclass(frozen=True, slots=True)
class ForecastStepPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-step-policy"
    policy_id: str
    original_roster: ObjectIdentity
    selected_roster: ObjectIdentity
    selected_numerical_policy: ObjectIdentity
    comparison_budget: ForecastComparisonBudget
    retained_precision_assessment: ObjectIdentity
    retained_clock_assessments: tuple[ObjectIdentity, ObjectIdentity]
    baseline_native_request: ObjectIdentity
    baseline_solver_json: str
    maximum_internal_step_s: Decimal = D(1)
    scientific_horizon_s: Decimal = D(180000)
    selected_forecast_slots: int = 54
    selected_reference_pairs: int = 36
    scope: str = SCOPE
    qualification: str = "UNASSESSED;ALL_NATIVE_AND_INDEPENDENT_CONTROLS_REQUIRED"
    historical_completion: str = "UNCHANGED;OLD_UNKNOWN_RETAINED;NO_REPLAY_CLEARANCE"
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        self.comparison_budget.__post_init__()
        solver = json.loads(self.baseline_solver_json)
        if (any(type(row) is not ObjectIdentity or row.object_schema != dr.FrozenForecastRoster.SCHEMA
                    for row in (self.original_roster, self.selected_roster))
                or self.original_roster == self.selected_roster
                or type(self.selected_numerical_policy) is not ObjectIdentity
                or self.selected_numerical_policy.object_schema != c.NumericalPolicy.SCHEMA
                or type(self.comparison_budget) is not ForecastComparisonBudget
                or self.comparison_budget.selected_roster != self.selected_roster
                or type(self.retained_precision_assessment) is not ObjectIdentity
                or self.retained_precision_assessment.object_schema != "empirical-lawhood/battery-observation-inquiry/completed-precision-reassessment"
                or type(self.retained_clock_assessments) is not tuple or len(self.retained_clock_assessments) != 2
                or len(set(self.retained_clock_assessments)) != 2
                or any(type(row) is not ObjectIdentity or row.object_schema != "empirical-lawhood/battery-segmented/representable-clock-assessment"
                       for row in self.retained_clock_assessments)
                or type(self.baseline_native_request) is not ObjectIdentity
                or self.baseline_native_request.object_schema != native.SegmentRequest.SCHEMA
                or solver.get("type") != "IDAKLUSolver" or solver.get("rtol") != _bits(D("1e-7"))
                or solver.get("atol") != _bits(D("1e-8")) or solver.get("options", {}).get("dt_max") != _bits(0)
                or type(self.maximum_internal_step_s) is not D or self.maximum_internal_step_s != 1
                or type(self.scientific_horizon_s) is not D or self.scientific_horizon_s != 180000
                or type(self.selected_forecast_slots) is not int or self.selected_forecast_slots != 54
                or type(self.selected_reference_pairs) is not int or self.selected_reference_pairs != 36
                or self.scope != SCOPE or self.qualification != "UNASSESSED;ALL_NATIVE_AND_INDEPENDENT_CONTROLS_REQUIRED"
                or self.historical_completion != "UNCHANGED;OLD_UNKNOWN_RETAINED;NO_REPLAY_CLEARANCE"
                or type(self.fresh_physical_units) is not int or self.fresh_physical_units != 0):
            raise ValueError("forecast step policy changes complete operands, retained evidence or unqualified scope")

    @property
    def identity(self):
        return identity(self, "policy_id")

    @property
    def sources(self):
        # The existing full-roster convention can reuse its stable label while
        # canonical source/policy/content changes. Original exact identity stays
        # in this policy and in its authenticated input materialization; avoid
        # two different fingerprints under one flattened source label.
        original = () if self.original_roster.object_id == self.selected_roster.object_id else (self.original_roster,)
        return (self.identity, *original, self.selected_roster, self.selected_numerical_policy,
            identity(self.comparison_budget, "budget_id"), self.retained_precision_assessment,
            *self.retained_clock_assessments, self.baseline_native_request)


def require_policy(control, original, selected, *, baseline_request=None):
    if type(control) is not ForecastStepPolicy or type(original) is not dr.FrozenForecastRoster or type(selected) is not dr.FrozenForecastRoster:
        raise ValueError("full forecast accuracy requires actual typed original and prospective rosters")
    for record in (control, original, selected):
        record.__post_init__()
    expected = prospective_selection(original, policy_id=selected.policy.policy_id,
        source_id=selected.source.source_id, roster_id=selected.roster_id)
    if (control.original_roster != identity(original, "roster_id") or control.selected_roster != identity(selected, "roster_id")
            or control.selected_numerical_policy != c.identity(selected.policy) or selected != expected):
        raise ValueError("prospective numerical policy changes original slot order, mesh, band, source, preparation or tolerance ladder")
    if baseline_request is not None:
        if (type(baseline_request) is not native.SegmentRequest or baseline_request.identity != control.baseline_native_request
                or baseline_request.ordinal != 1 or baseline_request.kind != "charging"
                or _primitive(json.loads(baseline_request.primitive_json)["solver"]) != control.baseline_solver_json):
            raise ValueError("forecast policy substitutes its complete original baseline request/options")


def require_config(control, selected, config):
    if (type(config) is not sc.SegmentedNativeConfig or config.native not in selected.configurations
            or control.selected_roster != identity(selected, "roster_id")
            or config.method.maximum_model_clock_s != control.scientific_horizon_s):
        raise ValueError("forecast accuracy config is not an exact complete-roster scientific operand")
    config.__post_init__()


def require_retained_evidence(control, original, selected, precision, clocks, negative, baseline_request):
    """Join actual complete local evidence without calling it full qualification."""
    from empirical_lawhood.adapters.methods.battery_observation_inquiry import contracts as observation
    from empirical_lawhood.adapters.methods.battery_observation_inquiry.precision_assessment import PrecisionReassessment
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
    from .representable_clock import RepresentableClockAssessment
    from . import segmented_science as science
    require_policy(control, original, selected, baseline_request=baseline_request)
    if (type(precision) is not PrecisionReassessment or type(clocks) is not tuple or len(clocks) != 2
            or any(type(row) is not RepresentableClockAssessment for row in clocks)
            or type(negative) is not observation.ObservationReadout):
        raise ValueError("full forecast policy requires actual complete retained local scientific operands")
    for record in (precision, *clocks, negative):
        record.__post_init__()
    readout = precision.reassessed_readout.original_readout
    if (identity(precision, "assessment_id") != control.retained_precision_assessment
            or tuple(identity(row, "assessment_id") for row in clocks) != control.retained_clock_assessments
            or tuple(row.original_pair for row in clocks) != readout.pairs
            or readout.observation.original_selection != original or negative.observation.original_selection != original
            or any(row.disposition is not A.SATISFIED for row in (*readout.methods, *clocks))
            or any(not pair.intervals or any(interval.disposition is not A.SATISFIED
                or not interval.checked_rhs_components or not interval.checked_derivative_components for interval in pair.intervals)
                   for pair in readout.pairs)
            or negative.disposition is not A.FALSIFIED
            or any(row.disposition is not A.FALSIFIED for row in negative.pairs)
            or baseline_request.identity != negative.methods[0].window.result.evidence.trace.segments[0].request):
        raise ValueError("retained scientific evidence substitutes local precision, boundaries, original negative or denominators")
    science.authenticate_payloads(negative.methods[0].window.result.evidence.native_receipt, (baseline_request,))


@dataclass(frozen=True, slots=True)
class ActualForecastStepAssignment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/actual-forecast-step-assignment"
    assignment_id: str
    control: ForecastStepPolicy
    native_configuration: ObjectIdentity
    numerical_view: c.NumericalView
    baseline_constructor_json: str
    actual_constructor_json: str
    actual_solver_json: str
    assignment_kind: str = ASSIGNMENT_KIND

    def __post_init__(self):
        validate_stable_id(self.assignment_id)
        self.control.__post_init__()
        self.numerical_view.__post_init__()
        base, selected, actual = (json.loads(value) for value in (
            self.baseline_constructor_json, self.actual_constructor_json, self.actual_solver_json))
        expected = dict(base, options=dict(base["options"], dt_max=_bits(self.control.maximum_internal_step_s)))
        expected_actual = json.loads(self.control.baseline_solver_json)
        expected_actual.update(rtol=_bits(self.numerical_view.rtol), atol=_bits(self.numerical_view.atol))
        expected_actual["options"]["dt_max"] = _bits(self.control.maximum_internal_step_s)
        if (type(self.native_configuration) is not ObjectIdentity or self.native_configuration.object_schema != sc.SegmentedNativeConfig.SCHEMA
                or type(self.numerical_view) is not c.NumericalView
                or (self.numerical_view.rtol, self.numerical_view.atol) != (
                    (D("1e-11"), D("1e-12")) if self.numerical_view.view_id == "dfn-tolerance" else (D("1e-9"), D("1e-10")))
                or base["options"].get("dt_max") != _bits(0) or selected != expected or actual != expected_actual
                or base.get("rtol") != _bits(self.numerical_view.rtol) or base.get("atol") != _bits(self.numerical_view.atol)
                or any(actual.get(key) != value for key, value in selected.items() if key != "options")
                or any(actual["options"].get(key) != value for key, value in selected["options"].items())
                or self.assignment_kind != ASSIGNMENT_KIND):
            raise ValueError("actual forecast assignment changes undeclared options or hides selected native precision")


class _BackendView:
    def __init__(self, backend, control, config):
        self.backend, self.control, self.config, self.calls, self.assignment = backend, control, config, 0, None

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def IDAKLUSolver(self, **kwargs):
        if (self.calls or kwargs.get("options", {}).get("dt_max") != 0.0
                or kwargs.get("rtol") != float(self.config.rtol) or kwargs.get("atol") != float(self.config.atol)):
            raise ValueError("forecast wrapper lacks single unchanged explicit-precision constructor")
        self.calls += 1
        selected = dict(kwargs, options=dict(kwargs["options"], dt_max=float(self.control.maximum_internal_step_s)))
        solver = self.backend.IDAKLUSolver(**selected)
        self.assignment = _primitive(kwargs), _primitive(selected), _primitive(solver.to_config())
        return solver


class _ControlledProgress:
    def __init__(self, original, control):
        self.original, self.control, self.main, self.added_bytes = original, control, None, 0
        self.definition = None
        self._preparation_records = {}

    def __getattr__(self, name):
        return getattr(self.original, name)

    def begin(self, definition, inputs=None):
        entry = self.original.begin(definition, inputs)
        if definition.operation_id == "battery.segmented-native.forecast":
            if self.main is not None:
                raise ValueError("full forecast policy entered multiple main contacts")
            self.main = entry
        return entry

    def contact(self, entry):
        self.original.contact(entry)
        if entry is self.main:
            self.publish_extra("forecast-step-policy", self.control)

    def publish_extra(self, name, record):
        if self.main is None:
            raise ValueError("actual forecast assignment has no original entered main custody")
        self.added_bytes += passive._publish(self.original, self.main, name, record).materialization.size_bytes
        self._preparation_records[name] = record

    def preparation_records(self):
        """Only records actually observed and published by the native builder."""
        if set(self._preparation_records) != {"forecast-step-policy", "forecast-step-assignment"}:
            raise ValueError("actual preparation checkpoint lacks its solver assignment")
        return tuple(sorted(self._preparation_records.items()))

    def complete(self, entry, **kwargs):
        if entry is self.main:
            kwargs["cost"] = replace(kwargs["cost"], retained_bytes=kwargs["cost"].retained_bytes + D(self.added_bytes))
            kwargs["cost_scope"] = kwargs.get("cost_scope", "") + "; added policy/assignment bytes counted once; pre-timer policy CPU/wall covered by whole entry"
        return self.original.complete(entry, **kwargs)


@contextmanager
def native_step_scope(control, original, selected, progress=None, *, additional_materialization_ids=()):
    """Use unchanged scientific native implementation, source checks and recovery."""
    require_policy(control, original, selected)
    original_definition, original_runtime = native.build_forecast_definition, native.build_runtime
    selected_progress = None if progress is None else _ControlledProgress(progress, control)

    def definition(config, *args):
        base = original_definition(config, *args)
        result = controlled_forecast_definition(control, original, selected, config, base,
            additional_materialization_ids=additional_materialization_ids)
        if selected_progress is not None:
            if selected_progress.definition is not None and selected_progress.definition != result:
                raise ValueError("controlled forecast substitutes its frozen actual definition")
            selected_progress.definition = result
        return result

    def runtime(config, protocol, backend):
        require_config(control, selected, config)
        if selected_progress is None:
            raise ValueError("full forecast controlled runtime requires original actual custody")
        view = _BackendView(backend, control, config.native)
        result = original_runtime(config, protocol, view)
        if view.calls != 1 or view.assignment is None or _primitive(result[1].to_config()) != view.assignment[2]:
            raise ValueError("full forecast runtime lacks exact actual constructor/returned assignment")
        witness = ActualForecastStepAssignment("assignment." + control.policy_id + "." + config.config_id,
            control, identity(config, "config_id"), config.native.numerical_view, *view.assignment)
        selected_progress.publish_extra("forecast-step-assignment", witness)
        return result

    native.build_forecast_definition, native.build_runtime = definition, runtime
    try:
        yield selected_progress
    finally:
        native.build_forecast_definition, native.build_runtime = original_definition, original_runtime


def controlled_forecast_definition(control, original, selected, config, base, *, additional_materialization_ids=()):
    """The original controlled definition, shared by preparation and execution."""
    require_policy(control, original, selected)
    require_config(control, selected, config)
    sources = {row.object_id: row for row in (*base.sources, *control.sources)}
    if len(sources) != len(base.sources) + len(control.sources):
        raise ValueError("forecast policy collides with an original native source identity")
    return replace(base, subwork_id="controlled." + control.policy_id + "." + base.subwork_id,
        sources=tuple(sorted(sources.values(), key=lambda row: row.object_id)),
        input_materialization_ids=tuple(sorted(set((*base.input_materialization_ids, *additional_materialization_ids)))),
        outputs=tuple(sorted((*base.outputs,
            NativeSubworkOutput("forecast-step-policy", ForecastStepPolicy.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"),
            NativeSubworkOutput("forecast-step-assignment", ActualForecastStepAssignment.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")), key=lambda row: row.output_id)))


def require_assignment(control, selected, assignment, config, definition, receipt):
    """Independent consumers authenticate original native outputs before use."""
    from . import segmented_science as science
    require_config(control, selected, config)
    if type(assignment) is not ActualForecastStepAssignment:
        raise ValueError("full forecast consumer requires its actual typed assignment")
    assignment.__post_init__()
    if (assignment.control != control or assignment.native_configuration != identity(config, "config_id")
            or assignment.numerical_view != config.native.numerical_view or not set(control.sources).issubset(definition.sources)
            or definition.configuration != identity(config, "config_id")):
        raise ValueError("full forecast assignment substitutes configuration, control or actual definition sources")
    science.authenticate_payloads(receipt, (control, assignment))


@dataclass(frozen=True, slots=True)
class ForecastStepEvidence(CanonicalRecord):
    """Ordinary dependency exposing exact completed native assignment custody."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-step-evidence"
    evidence_id: str
    control: ForecastStepPolicy
    assignment: ActualForecastStepAssignment | None
    original_native_definition: NativeSubworkDefinition
    original_native_completion: NativeSubworkCompletion
    original_native_receipt: CanonicalTaskReceipt
    scope: str = "ACTUAL_ASSIGNMENT_OR_KNOWN_FAILURE_BEFORE_ASSIGNMENT;ZERO_SOLVE_TRACE_REQUIRED_BY_CONSUMER;NO_CONVERGENCE_OR_ADMISSION_CLAIM"

    def __post_init__(self):
        from . import segmented_science as science
        validate_stable_id(self.evidence_id)
        if (type(self.control) is not ForecastStepPolicy
                or self.assignment is not None and type(self.assignment) is not ActualForecastStepAssignment
                or type(self.original_native_definition) is not NativeSubworkDefinition
                or type(self.original_native_completion) is not NativeSubworkCompletion
                or type(self.original_native_receipt) is not CanonicalTaskReceipt
                or not set(self.control.sources).issubset(self.original_native_definition.sources)
                or self.original_native_completion.definition != self.original_native_definition.identity
                or not set(self.original_native_definition.input_materialization_ids).issubset(self.original_native_receipt.input_materialization_ids)
                or self.scope != "ACTUAL_ASSIGNMENT_OR_KNOWN_FAILURE_BEFORE_ASSIGNMENT;ZERO_SOLVE_TRACE_REQUIRED_BY_CONSUMER;NO_CONVERGENCE_OR_ADMISSION_CLAIM"):
            raise ValueError("forecast step evidence loses actual definition, assignment, policy or receipt")
        science.authenticate_payloads(self.original_native_receipt, (self.control, self.original_native_completion))
        assignment_outputs = tuple(row for row in self.original_native_receipt.output_logical_artifacts
            if row.payload_schema == ActualForecastStepAssignment.SCHEMA)
        if self.assignment is None:
            if (assignment_outputs or "forecast-step-assignment" not in self.original_native_completion.omitted_output_ids
                    or self.original_native_completion.operational_status is not OperationalStatus.FAILED
                    or self.original_native_receipt.operational_status is not OperationalStatus.FAILED):
                raise ValueError("absent forecast assignment requires authentic known native failure and omission")
        else:
            if (self.assignment.control != self.control
                    or self.assignment.native_configuration != self.original_native_definition.configuration
                    or len(assignment_outputs) != 1
                    or "forecast-step-assignment" not in self.original_native_completion.output_ids):
                raise ValueError("forecast step evidence substitutes or hides actual numerical assignment")
            self.assignment.__post_init__()
            science.authenticate_payloads(self.original_native_receipt, (self.assignment,))


class _ConsumerView:
    def __init__(self, original, inputs, outputs):
        self.original, self.input_ports, self.output_ports = original, inputs, outputs

    def __getattr__(self, name):
        return getattr(self.original, name)


def controlled_context(context, control, original, selected, precision, clocks, negative, baseline_request):
    """Authenticate every extra real input and ordinary output before old loading."""
    require_retained_evidence(control, original, selected, precision, clocks, negative, baseline_request)
    records = ((control, control.identity), (original, identity(original, "roster_id")),
        (precision, identity(precision, "assessment_id")), *((row, identity(row, "assessment_id")) for row in clocks),
        (negative, identity(negative, "readout_id")), (baseline_request, baseline_request.identity))
    selected_ports = []
    for record, operand in records:
        found = tuple(port for port in context.input_ports if port.artifact_id == operand.object_id)
        if len(found) != 1:
            raise ValueError("forecast step worker omits its complete actual additional scientific input")
        port = found[0]
        if (port.kind is not WorkerInputKind.EXTERNAL or port.payload_schema != record.SCHEMA
                or port.media_type != "application/json" or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError("forecast step worker substitutes additional input type or access")
        raw = port.read()
        if len(raw) != port.size_bytes or decode_canonical_bytes(raw, type(record), maximum_bytes=None) != record:
            raise ValueError("forecast step worker changes retained input canonical operands")
        selected_ports.append(port)
    if len(context.output_ports) != 3:
        raise ValueError("forecast step worker omits its actual ordinary assignment output")
    selected_outputs = tuple(port for port in context.output_ports if port.payload_schema == ForecastStepEvidence.SCHEMA)
    if len(selected_outputs) != 1:
        raise ValueError("forecast step worker omits its unique actual ordinary assignment output")
    output = selected_outputs[0]
    if (output.output_id != context.task_id + ".forecast-step-evidence" or output.payload_schema != ForecastStepEvidence.SCHEMA
            or output.profile is not ArtifactProfile.CANONICAL_JSON or output.media_type != "application/json"):
        raise ValueError("forecast step worker changes prefixed ordinary assignment output/profile")
    return _ConsumerView(context, tuple(port for port in context.input_ports if port not in selected_ports),
        tuple(port for port in context.output_ports if port is not output)), output, tuple(port.materialization_id for port in selected_ports)


class ControlledSegmentedRunner(NativeSegmentedRunner):
    """Local forecast composition; the original compiler/scheduler/custody own effects."""
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, control, original, selected, precision, clocks, negative, baseline_request):
        super().__init__("forecast")
        self.operands = control, original, selected, precision, clocks, negative, baseline_request

    def forecast_operands(self, context):
        from empirical_lawhood.adapters.methods.battery_segmented_inquiry.runner import _load
        view, _, _ = controlled_context(context, *self.operands)
        # The view selects scientific ports only. The complete original typed
        # context and its prepared anchor still enter every shared boundary.
        return _load(context, self.operation, self.manifest,
            scientific_input_ports=view.input_ports, scientific_output_ports=view.output_ports)

    def control_operands(self, context):
        return self.operands

    def forecast_definition(self, config, decoded, expected_parent, materializations):
        base = super().forecast_definition(config, decoded, expected_parent, materializations)
        return controlled_forecast_definition(*self.operands[:3], decoded["native-config"], base,
            additional_materialization_ids=materializations)

    def forecast_output_ports(self, context):
        return tuple(port for port in context.output_ports if port.payload_schema != ForecastStepEvidence.SCHEMA)

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
        control, original, selected = self.control_operands(context)[:3]
        try:
            all_materializations = context.input_materialization_ids
            with native_step_scope(control, original, selected, native_subwork, additional_materialization_ids=all_materializations) as native_progress:
                checks = super().execute_streaming_with_native_subwork(context, native_progress, emitter, progress)
                definition = native_progress.definition
                if definition is None:
                    raise ValueError("controlled full forecast returned without its actual frozen definition")
                inspection = native_subwork.inspect(definition)
                assignment = stream.completed_record(native_subwork, definition, inspection,
                    "forecast-step-assignment", ActualForecastStepAssignment, optional=True)
                evidence = ForecastStepEvidence("evidence.step." + definition.configuration.object_id,
                    control, assignment, definition, inspection.completion, inspection.receipt)
                output, = (port for port in context.output_ports if port.payload_schema == ForecastStepEvidence.SCHEMA)
                stream.emit_record(emitter, output.output_id, evidence)
                return (*checks, ReceiptCheck("forecast-step-actual-assignment-or-authentic-failure-and-policy-custody", True, ()))
        finally:
            for port in context.input_ports:
                port.close()


@contextmanager
def request_step_scope(assignments):
    """Check every original request's complete actual solver options and policy."""
    from empirical_lawhood.adapters.methods.battery_segmented_inquiry import evidence_stream as stream
    if (type(assignments) is not tuple or not assignments or any(type(row) is not ActualForecastStepAssignment for row in assignments)
            or len({row.native_configuration for row in assignments}) != len(assignments)):
        raise ValueError("full forecast request consumer loses actual assignment denominator")
    for assignment in assignments:
        assignment.__post_init__()
    stock = {row.native_configuration: row for row in assignments}
    original = stream.read_frames

    def frames(port):
        for frame in original(port):
            if type(frame) is stream.SegmentEvidenceFrame:
                assignment = stock.get(frame.request.configuration)
                if (assignment is None or json.loads(frame.request.primitive_json)["solver"] != json.loads(assignment.actual_solver_json)
                        or not set(assignment.control.sources).issubset(frame.definition.sources)):
                    raise ValueError("full forecast actual request changes explicit policy or complete solver options")
            yield frame

    stream.read_frames = frames
    try:
        yield
    finally:
        stream.read_frames = original
