# SPDX-License-Identifier: MPL-2.0
"""Registered RC phases: native effects, isolated choices and later assessment."""

from decimal import Decimal

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from . import science
from .contracts import (ARM_IDS, VARIANT_IDS, RCChainDecision, RCChainCaseResult,
    RCChainUnitResult, fixed_decimal_context)
from .operation_contracts import (
    ARM_SLOTS, RCSourceEvidence, RCObserverExport, RCObservationVariant, RCObservationSet,
    RCAdmission, RCAdmissionSet, RCCommittedDecision, RCCommitmentSet, RCNativeArmEvidence,
    RCNativeDeliverySet, RCMeasurementAssessment, RCMeasurementAssessmentSet,
    RCSupportAssessment, RCSupportAssessmentSet, RCJoinedAssessment, RCJoinedAssessmentSet,
)

D = Decimal
MAX_OPERATION_BYTES = 16 * 1024**2


def _same_unit(config, *products):
    sha = (config.scientific_config.fingerprint() if hasattr(config, "scientific_config")
           else config.scientific_config_sha256)
    for product in products:
        unit_id, fingerprint = ((product.expectation.unit_id, product.expectation.config_sha256)
                               if hasattr(product, "expectation") else (product.unit_id, product.config_sha256))
        if (unit_id, fingerprint) != (config.unit_id, sha):
            raise ValueError("RC phase substitutes its frozen scientific configuration or unit")


def _execute_native_views(config, unit, model):
    """Preserve completed raw views when a later declared numerical view fails."""
    from empirical_lawhood.adapters.simulators.rc_ladder_response.campaign import VIEWS, check_native_views, run_native_view
    study = science._study(config, unit, model)
    panels = []
    try:
        for view in VIEWS:
            panels.append(run_native_view(study, view))
        check = check_native_views(study, tuple(panels))
    except (ArithmeticError, RuntimeError):
        return tuple(panels), None, ("NUMERICAL_EXECUTION_FAILED",)
    return tuple(panels), check, ()


@fixed_decimal_context
def acquire_source(config):
    frozen = config.scientific_config
    science.prove_chain(frozen)
    unit = science._unit(frozen, config.unit_id)
    model = science._source(frozen, unit)
    expectation = science._expectation(frozen, unit, model)
    panels, check, failure = _execute_native_views(frozen, unit, model)
    if failure:
        return (RCSourceEvidence(unit.unit_id, frozen.fingerprint(), model, panels, None, failure),
                RCObserverExport(expectation, None, failure))
    failure = () if check.converged else ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",)
    sample = None if failure else next(panel for panel in panels if panel.view_id == "matrix-exponential").node_voltages_volts[0][0]
    # Independent scalar truth is assessed only after the commitment receipt.
    return (RCSourceEvidence(unit.unit_id, frozen.fingerprint(), model, panels, check, failure),
            RCObserverExport(expectation, sample, failure))


def construct_observations(config, exported):
    _same_unit(config, exported)
    reports = tuple(RCObservationVariant(variant, None if exported.source_failure_reason_codes
        else science._observation(config.protocol, exported.expectation, exported.observed_sample_volts, variant))
        for variant in VARIANT_IDS)
    return RCObservationSet(exported.expectation, reports, exported.source_failure_reason_codes)


def _admission(protocol, expectation, report):
    if (expectation.receiver_id, expectation.quantity_id, expectation.voltage_unit,
        expectation.sample_seconds, expectation.decision_seconds, expectation.maximum_radius_volts) != (
            protocol.receiver_id, protocol.quantity_id, protocol.voltage_unit, protocol.sample_seconds,
            protocol.decision_seconds, protocol.maximum_observation_radius_volts):
        raise ValueError("RC admission changes the frozen consumer requirement")
    if report is None:
        return "UNEVALUABLE", ("MISSING_OBSERVATION",)
    reasons = []
    for field, code in (("unit_id", "UNIT_BINDING_MISMATCH"), ("config_sha256", "CONFIGURATION_BINDING_MISMATCH"),
        ("model_sha256", "MODEL_BINDING_MISMATCH"), ("source_sha256", "SOURCE_BINDING_MISMATCH"),
        ("source_binding_sha256", "DECLARED_SOURCE_BINDING_MISMATCH"), ("receiver_id", "WRONG_RECEIVER"),
        ("quantity_id", "WRONG_QUANTITY"), ("voltage_unit", "WRONG_UNITS"), ("sample_seconds", "WRONG_SAMPLE_CLOCK")):
        if getattr(report, field) != getattr(expectation, field):
            reasons.append(code)
    if report.sample_seconds > report.available_seconds:
        reasons.append("OBSERVATION_PRECEDES_SAMPLE")
    if report.available_seconds > expectation.decision_seconds:
        reasons.append("LATE_OBSERVATION")
    if report.radius_volts > expectation.maximum_radius_volts:
        reasons.append("UNCERTAINTY_EXCEEDS_CONSUMER_LIMIT")
    return ("REFUSED" if reasons else "ADMITTED"), tuple(sorted(reasons))


def admit_observations(config, reports):
    _same_unit(config, reports)
    admissions = []
    for report in reports.reports:
        state, reasons = _admission(config.protocol, reports.expectation, report.observation)
        if reports.source_failure_reason_codes:
            state, reasons = "UNEVALUABLE", reports.source_failure_reason_codes
        elif report.variant_id == "physical-stop":
            state, reasons = "UNSUPPORTED", ("PHYSICAL_SENSOR_AND_METROLOGY_UNSUPPORTED",)
        admissions.append(RCAdmission(report.variant_id, state, reasons))
    return RCAdmissionSet(config.unit_id, config.scientific_config_sha256, reports.fingerprint(), tuple(admissions))


def commit_preparations(config, reports, admissions):
    _same_unit(config, reports, admissions)
    expected_admissions = admit_observations(config, reports)
    if admissions != expected_admissions:
        raise ValueError("RC commitment consumes a substituted causal admission")
    decisions = []
    for report in reports.reports:
        if reports.source_failure_reason_codes:
            decision = RCChainDecision(None, "UNEVALUABLE", None, None, None, None, None, reports.source_failure_reason_codes)
        else:
            decision = science.decide_preparation(config.protocol, reports.expectation, report.observation)
            if report.variant_id == "physical-stop":
                decision = RCChainDecision(None, "UNSUPPORTED", None, None, None, None, None,
                    ("PHYSICAL_SENSOR_AND_METROLOGY_UNSUPPORTED",))
        decisions.append(RCCommittedDecision(report.variant_id, decision))
    return RCCommitmentSet(config.unit_id, config.scientific_config_sha256, reports.fingerprint(),
                           admissions.fingerprint(), tuple(decisions))


@fixed_decimal_context
def deliver_phases(config, commitments):
    """A finite native batch consumes choices; it does not choose or adjudicate."""
    _same_unit(config, commitments)
    frozen = config.scientific_config
    unit = science._unit(frozen, config.unit_id)
    decisions = {item.variant_id: item.decision for item in commitments.decisions}
    arms = []
    for variant, arm in ARM_SLOTS:
        decision = decisions[variant]
        if decision.disposition != "ADMITTED":
            arms.append(RCNativeArmEvidence(variant, arm, None, (), None, ()))
            continue
        duration, left, right = science._arm_operands(frozen.protocol, decision, arm)
        model = science._model(frozen, unit, model_id=f"{frozen.config_id}.{unit.unit_id}.{variant}.{arm}",
            duration=duration, prep_left=left, prep_right=right)
        panels, check, failure = _execute_native_views(frozen, unit, model)
        arms.append(RCNativeArmEvidence(variant, arm, model, panels, check, failure))
    return RCNativeDeliverySet(unit.unit_id, frozen.fingerprint(), commitments.fingerprint(), tuple(arms))


def assess_measurement(config, source, reports, commitments):
    _same_unit(config, source, reports, commitments)
    frozen = config.scientific_config
    unit = science._unit(frozen, config.unit_id)
    if commitments.observation_set_sha256 != reports.fingerprint():
        raise ValueError("RC measurement replaces the committed observation set")
    if source.failure_reason_codes:
        results = tuple(RCMeasurementAssessment(variant, "UNEVALUABLE", source.failure_reason_codes) for variant in VARIANT_IDS)
    else:
        science._verify_panels(frozen, unit, source.measurement_source, source.native_panels)
        results = tuple(RCMeasurementAssessment(report.variant_id, *science._measurement_state(frozen.protocol,
            unit, report.observation, commitment.decision, report.variant_id))
            for report, commitment in zip(reports.reports, commitments.decisions, strict=True))
    return RCMeasurementAssessmentSet(unit.unit_id, frozen.fingerprint(), commitments.fingerprint(), results)


@fixed_decimal_context
def assess_support(config, measurements, commitments, native):
    _same_unit(config, measurements, commitments, native)
    if measurements.commitment_sha256 != commitments.fingerprint() or native.commitment_sha256 != commitments.fingerprint():
        raise ValueError("RC support changes the prior action commitment")
    frozen, unit = config.scientific_config, science._unit(config.scientific_config, config.unit_id)
    p = frozen.protocol
    decisions = {item.variant_id: item.decision for item in commitments.decisions}
    ms = {item.variant_id: item for item in measurements.assessments}
    assessments = []
    for item in native.arms:
        decision, m = decisions[item.variant_id], ms[item.variant_id]
        if item.native_model is None or item.failure_reason_codes:
            failed = bool(item.failure_reason_codes)
            d = (RCChainDecision(decision.observation_sha256, "UNEVALUABLE", None,
                decision.sample_lower_volts, decision.sample_upper_volts, None, None, item.failure_reason_codes) if failed else decision)
            deadline = p.conflict_deadline_seconds if item.variant_id == "resource-conflict" else p.completion_deadline_seconds
            result = science._unexecuted_arm(p, d, "UNEVALUABLE" if failed else m.state, deadline, item.arm_id)
            assessments.append(RCSupportAssessment(item.variant_id, item.arm_id, None, None, None, None,
                result.preparation_state, result.reason_codes))
            continue
        science._verify_panels(frozen, unit, item.native_model, item.native_panels,
                              allow_analytic_defect=not item.numerical_check.converged)
        duration, left, right = science._arm_operands(p, decision, item.arm_id)
        at_decision = science._interval(p, decision.sample_lower_volts, decision.sample_upper_volts,
                                       p.decision_seconds - p.sample_seconds)
        lower, upper = science._interval(p, *at_decision, duration, left, right)
        prospective = science._supported(p, lower, upper, guarded=True)
        exact = next(panel for panel in item.native_panels if panel.view_id == "matrix-exponential")
        state = exact.node_voltages_volts[exact.times_seconds.index(p.decision_seconds + duration)][0]
        actual = science._supported(p, state, state, guarded=False)
        reasons = []
        if m.state != "PASSED": reasons.append("MEASUREMENT_REQUIREMENT_NOT_SUPPLIED")
        if not prospective: reasons.append("PROSPECTIVE_SUPPORT_NOT_CERTIFIED")
        if not actual: reasons.append("ACTUAL_RESPONSE_CUTOFF_OUTSIDE_SUPPORT")
        if not item.numerical_check.converged: reasons.append("NUMERICAL_CONFORMANCE_FAILED")
        outcome = ("UNEVALUABLE" if not item.numerical_check.converged else
                   "FAILED" if m.state != "PASSED" or not actual else "REFUSED" if not prospective else "PASSED")
        assessments.append(RCSupportAssessment(item.variant_id, item.arm_id, lower, upper, prospective, actual,
                                              outcome, tuple(sorted(reasons))))
    return RCSupportAssessmentSet(unit.unit_id, frozen.fingerprint(), commitments.fingerprint(), tuple(assessments))


@fixed_decimal_context
def assess_joined(config, measurements, commitments, native, support):
    _same_unit(config, measurements, commitments, native, support)
    if support != assess_support(config, measurements, commitments, native):
        raise ValueError("RC joined use consumes a substituted support assessment")
    frozen, unit = config.scientific_config, science._unit(config.scientific_config, config.unit_id)
    p = frozen.protocol
    decisions = {item.variant_id: item.decision for item in commitments.decisions}
    ms = {item.variant_id: item for item in measurements.assessments}
    assessments = []
    for item in native.arms:
        decision, m = decisions[item.variant_id], ms[item.variant_id]
        if item.native_model is None or item.failure_reason_codes:
            failed = bool(item.failure_reason_codes)
            d = (RCChainDecision(decision.observation_sha256, "UNEVALUABLE", None,
                decision.sample_lower_volts, decision.sample_upper_volts, None, None, item.failure_reason_codes) if failed else decision)
            deadline = p.conflict_deadline_seconds if item.variant_id == "resource-conflict" else p.completion_deadline_seconds
            result = science._unexecuted_arm(p, d, "UNEVALUABLE" if failed else m.state, deadline, item.arm_id)
        else:
            result = science._reduce_arm(frozen, unit, item.variant_id, decision, m.state, item.arm_id,
                                        item.native_model, item.native_panels, item.numerical_check)
        assessments.append(RCJoinedAssessment(item.variant_id, item.arm_id, result))
    return RCJoinedAssessmentSet(unit.unit_id, frozen.fingerprint(), commitments.fingerprint(), tuple(assessments))


def reduce_unit(config, source, reports, commitments, measurements, support, joined):
    _same_unit(config, source, reports, commitments, measurements, support, joined)
    if (commitments.observation_set_sha256 != reports.fingerprint() or any(
        value.commitment_sha256 != commitments.fingerprint() for value in (measurements, support, joined))):
        raise ValueError("RC final projection substitutes its prior frozen commitments")
    frozen = config.scientific_config
    if source.failure_reason_codes:
        # Original records have a closed complete-two-view failure contract.
        # The phase source retains partial raw panels independently.
        legacy_panels = source.native_panels if source.failure_reason_codes == ("NUMERICAL_SOURCE_CONFORMANCE_FAILED",) else ()
        result = science.failed_unit_result(frozen, config.unit_id, source.failure_reason_codes[0], source_panels=legacy_panels)
    else:
        cases = []
        ms = {item.variant_id: item for item in measurements.assessments}
        js = {(item.variant_id, item.arm_id): item.result for item in joined.assessments}
        for report, commitment in zip(reports.reports, commitments.decisions, strict=True):
            m = ms[report.variant_id]
            cases.append(RCChainCaseResult(report.variant_id, reports.expectation, report.observation, commitment.decision,
                m.state, m.reason_codes, tuple(js[(report.variant_id, arm)]
                    for arm in (ARM_IDS if report.variant_id == "adequate" else ("selected",)))))
        result = RCChainUnitResult(config.unit_id, frozen.fingerprint(), source.measurement_source, source.native_panels, tuple(cases))
    science.verify_unit_result(frozen, result)
    return result


def summarize_units(config, units):
    return science.summarize_chain(config.scientific_config, tuple(sorted(units, key=lambda value: value.unit_id)))


class RCPhaseRunner:
    """A statically registered operation reads only its frozen typed ports."""

    def __init__(self, *, manifest, config_type, input_types, operation, output_types):
        self.manifest, self.config_type = manifest, config_type
        self.input_types, self.operation, self.output_types = input_types, operation, output_types

    def execute(self, context):
        if context.config.config_schema != self.config_type.SCHEMA:
            raise ValueError("RC operation changes its registered configuration schema")
        allowed = {self.config_type.SCHEMA: self.config_type, **{record.SCHEMA: record for record in self.input_types}}
        decoded = {}
        for port in context.input_ports:
            if port.payload_schema not in allowed:
                raise ValueError("RC operation receives an undeclared input or oracle port")
            value = decode_canonical_bytes(port.read(), allowed[port.payload_schema], maximum_bytes=MAX_OPERATION_BYTES)
            decoded.setdefault(port.payload_schema, []).append(value)
        configs = decoded.pop(self.config_type.SCHEMA, ())
        if len(configs) != 1 or configs[0].fingerprint() != context.config.content_sha256 or configs[0].config_id != context.config.config_id:
            raise ValueError("RC operation lacks its exact immutable configuration input")
        inputs = []
        for record in self.input_types:
            values = decoded.get(record.SCHEMA, ())
            if self.operation is summarize_units:
                inputs.append(tuple(values))
            elif len(values) != 1:
                raise ValueError("RC operation changes its declared input cardinality")
            else:
                inputs.append(values[0])
        product = self.operation(configs[0], *inputs)
        products = product if isinstance(product, tuple) else (product,)
        if tuple(type(value) for value in products) != self.output_types:
            raise ValueError("RC operation changes its typed output census")
        output_by_schema = {value.SCHEMA: value for value in products}
        if tuple(sorted(output_by_schema)) != tuple(sorted(port.payload_schema for port in context.output_ports)):
            raise ValueError("RC operation output ports differ from its registered product census")
        outputs = tuple(TaskOutputPayload(port.output_id, output_by_schema[port.payload_schema].canonical_bytes())
                        for port in context.output_ports)
        return RunnerResult(outputs, (ReceiptCheck("valid-complete-rc-phase-product", True, ()),))
