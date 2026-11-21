"""Frozen uniform electron gas transverse receiver screen contracts and strict config decoding.

The records in this module keep source observations, method estimates,
privileged truth and adjudication separate.  They contain no filesystem or
publication behavior.
"""

from __future__ import annotations


from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import ClassVar, Final

from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, require_sorted_unique_strings, validate_decimal, validate_sha256, validate_stable_id


PLAN_ID: Final = "uniform-electron-gas-transverse-receiver-screen"
CAMPAIGN_ID: Final = "uniform-electron-gas-transverse-screen-conformance-closeout"
CONFIG_SCHEMA: Final = 'empirical-lawhood/simulators/uniform-electron-gas-transverse-screen/transverse-receiver-screen-config'
CONFIG_VERSION: Final = "1.0.0"
CAPABILITY_VERSION: Final = "1.0.0"
EXTERNAL_ROOT: Final = "runs/uniform-electron-gas-transverse-receiver-screen"
MAXIMUM_CONFIG_BYTES: Final = 1024 * 1024
MAXIMUM_PANEL_BYTES: Final = 4 * 1024 * 1024

SOURCE_CAPABILITY_KEY: Final = "open-sim.uniform-electron-gas-response-truth-source.transverse-screen"
METHOD_CAPABILITY_KEY: Final = "method.uniform-electron-gas-response-transverse-law.transverse-screen"
ADMISSION_CAPABILITY_KEY: Final = "admission.uniform-electron-gas-response-transverse-screen.transverse-screen"
EVALUATOR_CAPABILITY_KEY: Final = "evaluator.uniform-electron-gas-response-transverse-screen.transverse-screen"
ADJUDICATION_SCHEMA: Final = 'empirical-lawhood/simulators/uniform-electron-gas-transverse-screen/scientific-adjudication'


class EvidenceLane(StrEnum):
    GAUGE_CLOSED_TRANSVERSE = "GAUGE_CLOSED_TRANSVERSE"
    TC_CLOSURE_DIAGNOSTIC = "TC_CLOSURE_DIAGNOSTIC"


class TruthCase(StrEnum):
    MISSING_PRESERVATION = "missing-preservation"
    NONLINEAR = "nonlinear"
    NORMAL = "normal"
    POSITIVE = "positive"
    Q_DRIFT = "q-drift"
    SPURIOUS_NORMAL = "spurious-normal"
    VIEW_DISAGREEMENT = "view-disagreement"
    WARD_FAIL = "ward-fail"
    WRONG_SIGN = "wrong-sign"


class UniformElectronGasMeasurementClass(StrEnum):
    TYPED_TRANSVERSE_PANEL = "MEASUREMENT_TYPED_TRANSVERSE_PANEL"
    CLOSURE_ONLY = "MEASUREMENT_CLOSURE_ONLY"
    PARTIAL_ROLE_LIMITED = "MEASUREMENT_PARTIAL_ROLE_LIMITED"
    SOURCE_IDENTITY_STOP = "MEASUREMENT_SOURCE_IDENTITY_STOP"
    UNEVALUABLE = "MEASUREMENT_UNEVALUABLE"


class UniformElectronGasObservationOrderClass(StrEnum):
    ORDER_OPPORTUNITY_SUPPORTED = "ORDER_RELATION_OPPORTUNITY_SUPPORTED"
    PHENOMENOLOGICAL_CLOSURE_ONLY = "ORDER_RELATION_PHENOMENOLOGICAL_CLOSURE_ONLY"
    NO_ORDER_OPPORTUNITY = "ORDER_RELATION_NO_ORDER_OPPORTUNITY"
    VIEW_OPPOSED = "ORDER_RELATION_VIEW_OPPOSED"
    ORDER_OPERAND_REQUIRED = "ORDER_RELATION_OPERAND_REQUIRED"


class UniformElectronGasResponseClass(StrEnum):
    FINITE_TRANSVERSE_RESPONSE = "RESPONSE_FINITE_TRANSVERSE_RESPONSE"
    RESPONSE_BELOW_FLOOR = "RESPONSE_BELOW_FLOOR"
    WRONG_SIGN = "RESPONSE_WRONG_SIGN"
    CONTROL_FAILED = "RESPONSE_CONTROL_FAILED"
    PARTIAL = "RESPONSE_PARTIAL"
    UNEVALUABLE = "RESPONSE_UNEVALUABLE"
    NOT_ATTEMPTED_PREREQUISITE = "RESPONSE_NOT_ATTEMPTED_PREREQUISITE"


class UniformElectronGasLawQualificationClass(StrEnum):
    TRANSVERSE_LAW_SUPPORTED = "LOCAL_LAW_TRANSVERSE_LAW_SUPPORTED"
    FINITE_Q_ONLY = "LOCAL_LAW_FINITE_Q_ONLY"
    NONLINEAR_BOUNDARY_LIMITED = "LOCAL_LAW_NONLINEAR_BOUNDARY_LIMITED"
    VIEW_LOCAL_ONLY = "LOCAL_LAW_VIEW_LOCAL_ONLY"
    NOT_SUPPORTED = "LOCAL_LAW_NOT_SUPPORTED"
    PARTIAL = "LOCAL_LAW_PARTIAL"
    UNEVALUABLE = "LOCAL_LAW_UNEVALUABLE"
    NOT_ATTEMPTED_PREREQUISITE = "LOCAL_LAW_NOT_ATTEMPTED_PREREQUISITE"


class UniformElectronGasAdmissionClass(StrEnum):
    MODEL_LOCAL_TRANSVERSE_ADMITTED = "ADMISSION_MODEL_LOCAL_TRANSVERSE_ADMITTED"
    BRANCH_LOCAL_ONLY = "ADMISSION_BRANCH_LOCAL_ONLY"
    EMPTY_HOLD = "ADMISSION_EMPTY_HOLD"
    NOT_ENTERED_LOCAL_LAW = "ADMISSION_NOT_ENTERED_LOCAL_LAW"
    PRESERVATION_OPERAND_REQUIRED = "ADMISSION_PRESERVATION_OPERAND_REQUIRED"
    AUTHORITY_REQUIRED = "ADMISSION_AUTHORITY_REQUIRED"
    UNEVALUABLE = "ADMISSION_UNEVALUABLE"
    NOT_ATTEMPTED_PREREQUISITE = "ADMISSION_NOT_ATTEMPTED_PREREQUISITE"


class GateName(StrEnum):
    AUTHORITY = "authority"
    BASELINE_PRESERVATION = "baseline_preservation"
    DYNAMICS = "dynamics"
    EFFORT = "effort"
    OBSERVATION_VALIDITY = "observation_validity"
    PHYSICAL_SINK = "physical_sink"
    REACHABILITY = "reachability"
    TARGET = "target"
    UNCERTAINTY = "uncertainty"



















@dataclass(frozen=True, slots=True)
class UniformElectronGasTransverseScreenConfig:
    """Decoded exact transverse-screen scientific configuration."""

    payload_sha256: str
    campaign_id: str
    freeze_id: str
    frozen_at_utc: str
    r_s: Decimal
    temperature_K: Decimal
    u0: Decimal
    u_values: tuple[Decimal, ...]
    q_over_kf: tuple[Decimal, ...]
    action_direction: tuple[Decimal, Decimal, Decimal]
    q_direction: tuple[Decimal, Decimal, Decimal]
    requested_clock: int
    accepted_clock: int
    applied_clock: int
    receiver_clock: int
    field_ceiling_T: Decimal
    slab_thickness_m: Decimal
    analytic_profile_points: int
    thresholds: tuple[tuple[str, Decimal], ...]
    truth_cases: tuple[TruthCase, ...]
    views: tuple[str, ...]
    positive_penetration_depth_m: Decimal
    deterministic_kernel_relative_error: Decimal
    storage_root: str
    external_root: str
    minimum_free_bytes: int
    resources: tuple[tuple[str, int | bool], ...]
    reference_conformance_gaps: tuple[str, ...]
    out_of_scope_gaps: tuple[str, ...]

    def threshold(self, key: str) -> Decimal:
        try:
            return dict(self.thresholds)[key]
        except KeyError as error:
            raise KeyError(f"unknown frozen threshold {key}") from error

    def resource(self, key: str) -> int | bool:
        try:
            return dict(self.resources)[key]
        except KeyError as error:
            raise KeyError(f"unknown frozen resource {key}") from error








Vector3 = tuple[Decimal, Decimal, Decimal]


def validate_vector(value: Vector3, *, field_name: str) -> None:
    if not isinstance(value, tuple) or len(value) != 3:
        raise ValueError(f"{field_name} must be an exact three-vector")
    for index, coordinate in enumerate(value):
        validate_decimal(coordinate, field_name=f"{field_name}[{index}]")


@dataclass(frozen=True, slots=True)
class ActionCurrentRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/action-current-row'

    row_id: str
    q_over_kf: Decimal
    u: Decimal
    requested_A_T: Vector3
    accepted_A_T: Vector3
    applied_A_T: Vector3
    realized_A_T: Vector3
    current_density: Vector3
    current_error_bound_A_m2: Decimal
    requested_clock: int
    accepted_clock: int
    applied_clock: int
    receiver_clock: int
    accepted: bool
    valid: bool
    reason_code: str | None = None

    def __post_init__(self) -> None:
        validate_stable_id(self.row_id, field_name="row_id")
        validate_decimal(self.q_over_kf, field_name="q_over_kf", minimum=Decimal("0"))
        if self.q_over_kf == 0:
            raise ValueError("finite-q action rows require q_over_kf > 0")
        validate_decimal(self.u, field_name="u")
        for name in (
            "requested_A_T",
            "accepted_A_T",
            "applied_A_T",
            "realized_A_T",
            "current_density",
        ):
            validate_vector(getattr(self, name), field_name=name)
        validate_decimal(
            self.current_error_bound_A_m2,
            field_name="current_error_bound_A_m2",
            minimum=Decimal("0"),
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (
                self.requested_clock,
                self.accepted_clock,
                self.applied_clock,
                self.receiver_clock,
            )
        ):
            raise ValueError("action/receiver clocks must be exact integers")
        if self.reason_code is not None:
            validate_stable_id(self.reason_code, field_name="reason_code")
        if self.valid and (not self.accepted or self.reason_code is not None):
            raise ValueError("a valid row must be accepted without a reason code")
        if not self.valid and self.reason_code is None:
            raise ValueError("an invalid row requires a reason code")


@dataclass(frozen=True, slots=True)
class GaugeControlRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/gauge-control-row'

    control_id: str
    q_over_kf: Decimal
    diamagnetic_normal: Decimal
    paramagnetic_normal: Decimal
    ward_residual: Decimal
    wrong_polarization_current_A_m2: Decimal
    converged: bool
    limit_order_supported: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.control_id, field_name="control_id")
        validate_decimal(self.q_over_kf, field_name="q_over_kf", minimum=Decimal("0"))
        for name in (
            "diamagnetic_normal",
            "paramagnetic_normal",
            "ward_residual",
            "wrong_polarization_current_A_m2",
        ):
            validate_decimal(getattr(self, name), field_name=name)
        if self.ward_residual < 0:
            raise ValueError("ward_residual must be nonnegative")


@dataclass(frozen=True, slots=True)
class TransversePanel(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/transverse-panel'

    panel_id: str
    source_id: str
    branch_id: str
    view_id: str
    evidence_lane: EvidenceLane
    evidence_world: str
    independent_unit_id: str
    deterministic: bool
    r_s: Decimal
    temperature_K: Decimal
    q_direction: Vector3
    action_direction: Vector3
    rows: tuple[ActionCurrentRow, ...]
    controls: tuple[GaugeControlRow, ...]
    order_zero: Decimal | None
    order_at_max_action: Decimal | None
    baseline_preserved: bool | None
    source_semantics_valid: bool

    def __post_init__(self) -> None:
        for name in (
            "panel_id",
            "source_id",
            "branch_id",
            "view_id",
            "evidence_world",
            "independent_unit_id",
        ):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.evidence_lane is not EvidenceLane.GAUGE_CLOSED_TRANSVERSE:
            raise ValueError("a transverse panel must use the gauge-closed lane")
        validate_decimal(self.r_s, field_name="r_s", minimum=Decimal("0"))
        validate_decimal(self.temperature_K, field_name="temperature_K", minimum=Decimal("0"))
        validate_vector(self.q_direction, field_name="q_direction")
        validate_vector(self.action_direction, field_name="action_direction")
        require_sorted_unique_ids(self.rows, attribute="row_id", field_name="rows")
        require_sorted_unique_ids(self.controls, attribute="control_id", field_name="controls")
        if not self.rows or not self.controls:
            raise ValueError("a transverse panel requires action rows and gauge controls")
        for name in ("order_zero", "order_at_max_action"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name, minimum=Decimal("0"))


@dataclass(frozen=True, slots=True)
class BranchInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/branch-input'

    input_id: str
    case_id: str
    panels: tuple[TransversePanel, ...]
    authority_valid: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.input_id, field_name="input_id")
        validate_stable_id(self.case_id, field_name="case_id")
        require_sorted_unique_ids(self.panels, attribute="panel_id", field_name="panels")
        if not self.panels:
            raise ValueError("branch input requires at least one panel")
        branch_ids = {panel.branch_id for panel in self.panels}
        view_ids = {panel.view_id for panel in self.panels}
        if len(branch_ids) != 1 or len(view_ids) != len(self.panels):
            raise ValueError("branch panels must share one branch and have unique views")


@dataclass(frozen=True, slots=True)
class ClosureDiagnosticInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/closure-diagnostic-input'

    input_id: str
    source_id: str
    branch_id: str
    r_s: Decimal
    temperature_K: Decimal
    supplied_tc_K: Decimal
    stiffness_closure: str

    def __post_init__(self) -> None:
        for name in ("input_id", "source_id", "branch_id", "stiffness_closure"):
            validate_stable_id(getattr(self, name), field_name=name)
        for name in ("r_s", "temperature_K", "supplied_tc_K"):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal("0"))


@dataclass(frozen=True, slots=True)
class FiniteQEstimate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/finite-q-estimate'

    estimate_id: str
    q_over_kf: Decimal
    kernel_half: Decimal
    kernel_full: Decimal
    kernel_error_bound: Decimal
    offset_current_A_m2: Decimal
    even_remainder_half_A_m2: Decimal
    even_remainder_full_A_m2: Decimal
    locality_relative: Decimal
    locality_pass: bool
    even_remainder_pass: bool
    zero_offset_pass: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.estimate_id, field_name="estimate_id")
        for name in (
            "q_over_kf",
            "kernel_half",
            "kernel_full",
            "kernel_error_bound",
            "offset_current_A_m2",
            "even_remainder_half_A_m2",
            "even_remainder_full_A_m2",
            "locality_relative",
        ):
            validate_decimal(getattr(self, name), field_name=name)
        if self.kernel_error_bound < 0 or self.locality_relative < 0:
            raise ValueError("estimate error/locality must be nonnegative")


@dataclass(frozen=True, slots=True)
class ViewLawResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/view-law-result'

    result_id: str
    panel_id: str
    view_id: str
    measurement_class: UniformElectronGasMeasurementClass
    observation_order_class: UniformElectronGasObservationOrderClass
    response_class: UniformElectronGasResponseClass
    law_qualification_class: UniformElectronGasLawQualificationClass
    finite_q: tuple[FiniteQEstimate, ...]
    kernel0: Decimal | None
    kernel0_error_bound: Decimal | None
    kernel0_lower_bound: Decimal | None
    c2: Decimal | None
    q_intercept_stability_relative: Decimal | None
    normal_cancellation_max_relative: Decimal
    ward_residual_max: Decimal
    maximum_field_T: Decimal
    order_preservation_fraction: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("result_id", "panel_id", "view_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        require_sorted_unique_ids(self.finite_q, attribute="estimate_id", field_name="finite_q")
        for name in (
            "kernel0",
            "kernel0_error_bound",
            "kernel0_lower_bound",
            "c2",
            "q_intercept_stability_relative",
            "order_preservation_fraction",
        ):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        for name in (
            "normal_cancellation_max_relative",
            "ward_residual_max",
            "maximum_field_T",
        ):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal("0"))
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")


@dataclass(frozen=True, slots=True)
class BranchLawResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/branch-law-result'

    result_id: str
    input_id: str
    case_id: str
    measurement_class: UniformElectronGasMeasurementClass
    observation_order_class: UniformElectronGasObservationOrderClass
    response_class: UniformElectronGasResponseClass
    law_qualification_class: UniformElectronGasLawQualificationClass
    view_results: tuple[ViewLawResult, ...]
    robust_kernel0_lower_bound: Decimal | None
    view_k0_agreement_relative: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("result_id", "input_id", "case_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        require_sorted_unique_ids(
            self.view_results, attribute="result_id", field_name="view_results"
        )
        for name in ("robust_kernel0_lower_bound", "view_k0_agreement_relative"):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")


@dataclass(frozen=True, slots=True)
class AdmissionGateResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/admission-gate-result'

    gate: GateName
    passed: bool
    margin: Decimal | None
    reason_code: str

    def __post_init__(self) -> None:
        if self.margin is not None:
            validate_decimal(self.margin, field_name="margin")
        validate_stable_id(self.reason_code, field_name="reason_code")


@dataclass(frozen=True, slots=True)
class ViewScreenResult(CanonicalRecord):
    """One numerical view's complete, noncompensating receiver admission decision."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/view-screen-result'

    result_id: str
    panel_id: str
    view_id: str
    admission_class: UniformElectronGasAdmissionClass
    gates: tuple[AdmissionGateResult, ...]
    kernel0_lower_bound: Decimal | None
    penetration_depth_upper_m: Decimal | None
    shielding_score_lower: Decimal | None
    hold: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("result_id", "panel_id", "view_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        if tuple(gate.gate.value for gate in self.gates) != tuple(gate.value for gate in GateName):
            raise ValueError("view result must contain all nine sorted admission gates")
        for name in (
            "kernel0_lower_bound",
            "penetration_depth_upper_m",
            "shielding_score_lower",
        ):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        admitted = self.admission_class is UniformElectronGasAdmissionClass.MODEL_LOCAL_TRANSVERSE_ADMITTED
        if admitted == self.hold:
            raise ValueError("view admission and hold must be exact complements")
        if admitted != all(gate.passed for gate in self.gates):
            raise ValueError("view admission must equal the nine-gate intersection")


@dataclass(frozen=True, slots=True)
class BranchScreenResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/branch-screen-result'

    result_id: str
    input_id: str
    case_id: str
    evidence_lane: EvidenceLane
    measurement_class: UniformElectronGasMeasurementClass
    observation_order_class: UniformElectronGasObservationOrderClass
    response_class: UniformElectronGasResponseClass
    law_qualification_class: UniformElectronGasLawQualificationClass
    admission_class: UniformElectronGasAdmissionClass
    view_results: tuple[ViewLawResult, ...]
    view_screens: tuple[ViewScreenResult, ...]
    gates: tuple[AdmissionGateResult, ...]
    robust_kernel0_lower_bound: Decimal | None
    penetration_depth_upper_m: Decimal | None
    shielding_score_lower: Decimal | None
    hold: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("result_id", "input_id", "case_id"):
            validate_stable_id(getattr(self, name), field_name=name)
        require_sorted_unique_ids(
            self.view_results, attribute="result_id", field_name="view_results"
        )
        require_sorted_unique_ids(
            self.view_screens, attribute="result_id", field_name="view_screens"
        )
        if tuple(gate.gate.value for gate in self.gates) != tuple(gate.value for gate in GateName):
            raise ValueError("branch result must contain all nine sorted admission gates")
        if self.evidence_lane is EvidenceLane.GAUGE_CLOSED_TRANSVERSE:
            if tuple(value.view_id for value in self.view_results) != tuple(
                value.view_id for value in self.view_screens
            ):
                raise ValueError("branch law and admission views differ")
        elif self.view_screens:
            raise ValueError("closure-only results cannot carry transverse view screens")
        for name in (
            "robust_kernel0_lower_bound",
            "penetration_depth_upper_m",
            "shielding_score_lower",
        ):
            value = getattr(self, name)
            if value is not None:
                validate_decimal(value, field_name=name)
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")
        if self.admission_class is UniformElectronGasAdmissionClass.MODEL_LOCAL_TRANSVERSE_ADMITTED and self.hold:
            raise ValueError("an admitted result cannot command hold")
        if self.admission_class is not UniformElectronGasAdmissionClass.MODEL_LOCAL_TRANSVERSE_ADMITTED and not self.hold:
            raise ValueError("every non-admitted result must command hold")
        if (self.admission_class is UniformElectronGasAdmissionClass.MODEL_LOCAL_TRANSVERSE_ADMITTED) != all(
            gate.passed for gate in self.gates
        ):
            raise ValueError("branch admission must equal the nine-gate intersection")


@dataclass(frozen=True, slots=True)
class TruthOracle(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/truth-oracle'

    oracle_id: str
    case_id: str
    truth_family: TruthCase
    expected_response_class: UniformElectronGasResponseClass
    expected_law_qualification_class: UniformElectronGasLawQualificationClass
    expected_admission_class: UniformElectronGasAdmissionClass
    true_penetration_depth_m: Decimal | None
    decisive_reason_code: str

    def __post_init__(self) -> None:
        for name in ("oracle_id", "case_id", "decisive_reason_code"):
            validate_stable_id(getattr(self, name), field_name=name)
        if self.true_penetration_depth_m is not None:
            validate_decimal(
                self.true_penetration_depth_m,
                field_name="true_penetration_depth_m",
                minimum=Decimal("0"),
            )


@dataclass(frozen=True, slots=True)
class TruthKnownCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/truth-known-case'

    case_id: str
    method_input: BranchInput
    privileged_oracle: TruthOracle

    def __post_init__(self) -> None:
        validate_stable_id(self.case_id, field_name="case_id")
        if (
            self.method_input.case_id != self.case_id
            or self.privileged_oracle.case_id != self.case_id
        ):
            raise ValueError("truth-known case input/oracle identity differs")


@dataclass(frozen=True, slots=True)
class CaseConformance(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/case-conformance'

    case_id: str
    result: BranchScreenResult
    oracle: TruthOracle
    passed: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.case_id, field_name="case_id")
        if self.result.case_id != self.case_id or self.oracle.case_id != self.case_id:
            raise ValueError("conformance case identities differ")
        require_sorted_unique_strings(self.reason_codes, field_name="reason_codes")


@dataclass(frozen=True, slots=True)
class MethodConformanceResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/method-conformance-result'

    result_id: str
    config_sha256: str
    cases: tuple[CaseConformance, ...]
    closure_nonpromotion_pass: bool
    passed: bool
    status: str

    def __post_init__(self) -> None:
        validate_stable_id(self.result_id, field_name="result_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        require_sorted_unique_ids(self.cases, attribute="case_id", field_name="cases")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("status must be a nonempty string")
        if self.passed != (
            self.closure_nonpromotion_pass and all(case.passed for case in self.cases)
        ):
            raise ValueError("method conformance verdict differs from case evidence")


@dataclass(frozen=True, slots=True)
class SourceStopResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/source-stop-result'

    result_id: str
    config_sha256: str
    source_dispositions: tuple[tuple[str, str], ...]
    task_dispositions: tuple[tuple[str, str], ...]
    target_contact_count: int
    status: str

    def __post_init__(self) -> None:
        validate_stable_id(self.result_id, field_name="result_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        if tuple(sorted(dict(self.source_dispositions))) != tuple(
            key for key, _value in self.source_dispositions
        ):
            raise ValueError("source dispositions must have sorted unique keys")
        if tuple(sorted(dict(self.task_dispositions))) != tuple(
            key for key, _value in self.task_dispositions
        ):
            raise ValueError("task dispositions must have sorted unique keys")
        if self.target_contact_count != 0:
            raise ValueError("transverse-screen source stop must contact zero target panels")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("status must be a nonempty string")


@dataclass(frozen=True, slots=True)
class TruthInputBatch(CanonicalRecord):
    """Truth-blind method inputs; privileged family labels are prohibited."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/truth-input-batch'

    batch_id: str
    config_sha256: str
    inputs: tuple[BranchInput, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.batch_id, field_name="batch_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        require_sorted_unique_ids(self.inputs, attribute="case_id", field_name="inputs")
        if not self.inputs:
            raise ValueError("truth input batch cannot be empty")


@dataclass(frozen=True, slots=True)
class TruthOracleBatch(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/truth-oracle-batch'

    batch_id: str
    config_sha256: str
    oracles: tuple[TruthOracle, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.batch_id, field_name="batch_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        require_sorted_unique_ids(self.oracles, attribute="case_id", field_name="oracles")
        if not self.oracles:
            raise ValueError("truth oracle batch cannot be empty")


@dataclass(frozen=True, slots=True)
class TruthLawBatch(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/truth-law-batch'

    batch_id: str
    config_sha256: str
    laws: tuple[BranchLawResult, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.batch_id, field_name="batch_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        require_sorted_unique_ids(self.laws, attribute="case_id", field_name="laws")
        if not self.laws:
            raise ValueError("truth law batch cannot be empty")


@dataclass(frozen=True, slots=True)
class TruthScreenBatch(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/uniform-electron-gas-response/truth-screen-batch'

    batch_id: str
    config_sha256: str
    screens: tuple[BranchScreenResult, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.batch_id, field_name="batch_id")
        validate_sha256(self.config_sha256, field_name="config_sha256")
        require_sorted_unique_ids(self.screens, attribute="case_id", field_name="screens")
        if not self.screens:
            raise ValueError("truth screen batch cannot be empty")


__all__ = [
    "ADMISSION_CAPABILITY_KEY",
    "ADJUDICATION_SCHEMA",
    "ActionCurrentRow",
    "AdmissionGateResult",
    "BranchInput",
    "BranchLawResult",
    "BranchScreenResult",
    "CAMPAIGN_ID",
    "CAPABILITY_VERSION",
    "CONFIG_SCHEMA",
    "CaseConformance",
    "ClosureDiagnosticInput",
    "EVALUATOR_CAPABILITY_KEY",
    "EvidenceLane",
    "EXTERNAL_ROOT",
    "FiniteQEstimate",
    "GateName",
    "GaugeControlRow",
    "MAXIMUM_PANEL_BYTES",
    "METHOD_CAPABILITY_KEY",
    "MethodConformanceResult",
    'UniformElectronGasMeasurementClass',
    'UniformElectronGasObservationOrderClass',
    'UniformElectronGasResponseClass',
    'UniformElectronGasLawQualificationClass',
    'UniformElectronGasAdmissionClass',
    "PLAN_ID",
    "SOURCE_CAPABILITY_KEY",
    "SourceStopResult",
    "UniformElectronGasTransverseScreenConfig",
    "TransversePanel",
    "TruthCase",
    "TruthInputBatch",
    "TruthKnownCase",
    "TruthLawBatch",
    "TruthOracle",
    "TruthOracleBatch",
    "TruthScreenBatch",
    "Vector3",
    "ViewLawResult",
    "ViewScreenResult",
]
