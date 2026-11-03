# SPDX-License-Identifier: MPL-2.0
"""Complete per-forecast operands and conservative cross-protocol contact joins.

Task/source namespaces do not clear uncertainty about the same underlying
charging or SOH request. This adapter projection is additional scientific
information for shared policy; it grants no issue, execution or retry authority.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from functools import lru_cache
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticNativeConfig, DiagnosticSource
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic import science as diagnostic_science
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource, CONTROL_RULE, TARGET_CHARGE
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, require_sorted_unique_strings, validate_sha256, validate_stable_id
from . import contracts as c, science

D = Decimal


def _physical_decimal(value):
    # The native code passes binary64 operands. Decimal spelling is retained
    # in the immutable original config; it does not distinguish equal requests.
    return float(value).hex()


def _mesh(native):
    if type(native) is c.NativeConfig:
        return native.numerical_view.electrode_points, native.numerical_view.particle_points
    if type(native) is DiagnosticNativeConfig:
        return native.electrode_points, native.particle_points
    raise ValueError("primitive work projection requires an exact supported native config")


@lru_cache(maxsize=256)
def forecast_primitive(native):
    """Charging operands independent of task IDs and downstream report schema."""
    native.__post_init__()
    nx, nr = _mesh(native)
    return canonical_json_bytes({
        "source": BatteryInquirySource(),
        "initial_soc_binary64": _physical_decimal(D("0.30")),
        "initial_temperature_binary64": _physical_decimal(native.initial_temperature_k),
        "chamber_temperature_binary64": _physical_decimal(native.chamber_temperature_k),
        "model_view": native.model_view,
        "electrode_points": nx,
        "particle_points": nr,
        "localization_epsilon_binary64": _physical_decimal(native.localization_epsilon_k),
        "rtol_binary64": _physical_decimal(native.rtol),
        "atol_binary64": _physical_decimal(native.atol),
        "control_rule": CONTROL_RULE,
        "target_charge": TARGET_CHARGE,
        "initial_clock": D(0),
        "initial_discharge_capacity": D(0),
    })


@lru_cache(maxsize=256)
def initializer_primitive(native):
    """Conservative exact selected preparation match, separate from charging.

    Mesh and main-solve tolerances do not change the default SOH initializer.
    Retaining initial/chamber operands makes this an at-least overlap detector;
    absence of this match is not proof that every initializer operand differs.
    """
    native.__post_init__()
    _mesh(native)
    return canonical_json_bytes({
        "source": BatteryInquirySource(),
        "parameter_source": "Chen2020" if native.model_view == "chen-spme" else "ORegan2022",
        "requested_soc_binary64": _physical_decimal(D(".30")),
        "initial_temperature_binary64": _physical_decimal(native.initial_temperature_k),
        "chamber_temperature_binary64": _physical_decimal(native.chamber_temperature_k),
        "reference_temperature_binary64": _physical_decimal(D("298.15")),
        "voltage_endpoints": (D("2.5"), D("4.2")),
        "known_value": "cyclable lithium capacity",
        "direction": "NONE",
    })


@dataclass(frozen=True, slots=True)
class UnknownDiagnosticWork(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-durable-inquiry/unknown-diagnostic-work"
    record_id: str
    original_contact: ObjectIdentity
    original_producing_source: ObjectIdentity
    configurations: tuple[DiagnosticNativeConfig, ...]
    forecast_count: int | None = None
    initializer_count: int | None = None
    charging_segment_count: int | None = None
    disposition: str = "UNKNOWN_COMPLETION"

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.original_contact.object_schema != "empirical-lawhood/runtime/native-effect-contact"
                or self.original_producing_source.object_schema != "empirical-lawhood/kernel/numerical-producing-provenance"):
            raise ValueError("unknown diagnostic work requires its original actual contact and producing source")
        if self.disposition != "UNKNOWN_COMPLETION" or any(value is not None for value in (self.forecast_count, self.initializer_count, self.charging_segment_count)):
            raise ValueError("unknown diagnostic work cannot invent completed subwork counts")
        source = DiagnosticSource()
        prior = ObjectIdentity("product.battery-thermal-inquiry.supply", "empirical-lawhood/battery-thermal-inquiry/supply", "1.1.0", source.prior_supply_sha256)
        if self.configurations != diagnostic_science.configurations(source, prior):
            raise ValueError("unknown diagnostic work omits, relabels or changes the original twelve operands")


@dataclass(frozen=True, slots=True)
class FrozenForecastRoster(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-durable-inquiry/forecast-roster"
    roster_id: str
    source: c.RefinedSource
    policy: c.NumericalPolicy
    configurations: tuple[c.NativeConfig, ...]
    comparison_config_pairs: tuple[tuple[ObjectIdentity, ObjectIdentity], ...]
    scientific_unit_id: str = c.UNIT
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.roster_id)
        if not self.policy.tolerance_probe or self.configurations != science.configurations(self.source, self.policy):
            raise ValueError("durable roster requires exactly the unchanged selected fifty-four native operands")
        rows = {(native.initial_temperature_k, native.recipe, native.component_view): native for native in self.configurations}
        expected = tuple((c.identity(rows[t, r, left]), c.identity(rows[t, r, right]))
            for t, r in self.policy.development_preparations for left, right in self.policy.comparison_pairs)
        if len(self.configurations) != 54 or len(expected) != 36 or self.comparison_config_pairs != expected:
            raise ValueError("durable roster changes its complete 54/36 forecast/comparison denominator")
        if self.scientific_unit_id != c.UNIT or self.fresh_physical_units != 0:
            raise ValueError("nested numerical forecasts do not create fresh physical units")


@dataclass(frozen=True, slots=True)
class ForecastEntryDisposition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-durable-inquiry/entry-disposition"
    disposition_id: str
    roster: ObjectIdentity
    configuration: ObjectIdentity
    uncertain_work: ObjectIdentity
    forecast_primitive_sha256: str
    initializer_primitive_sha256: str
    matching_uncertain_forecast_ids: tuple[str, ...]
    matching_uncertain_initializer_ids: tuple[str, ...]
    state: str
    scientific_authority: str = "NONE"

    def __post_init__(self):
        validate_stable_id(self.disposition_id)
        validate_sha256(self.forecast_primitive_sha256)
        validate_sha256(self.initializer_primitive_sha256)
        if (self.roster.object_schema != FrozenForecastRoster.SCHEMA or self.configuration.object_schema != c.NativeConfig.SCHEMA
                or self.uncertain_work.object_schema != UnknownDiagnosticWork.SCHEMA):
            raise ValueError("primitive entry disposition substitutes its typed operands")
        for name in ("matching_uncertain_forecast_ids", "matching_uncertain_initializer_ids"):
            require_sorted_unique_strings(getattr(self, name), field_name=name)
        overlaps = bool(self.matching_uncertain_forecast_ids or self.matching_uncertain_initializer_ids)
        expected = "HOLD_UNCERTAIN_PRIOR_PRIMITIVE" if overlaps else "NO_EXACT_OVERLAP_FOUND;NOT_ENTRY_AUTHORITY"
        if self.state != expected or self.scientific_authority != "NONE":
            raise ValueError("primitive overlap disposition cannot clear uncertainty or grant entry authority")


@lru_cache(maxsize=8)
def freeze_forecast_roster(source, policy):
    configurations = science.configurations(source, policy)
    rows = {(native.initial_temperature_k, native.recipe, native.component_view): native for native in configurations}
    pairs = tuple((c.identity(rows[t, r, left]), c.identity(rows[t, r, right]))
        for t, r in policy.development_preparations for left, right in policy.comparison_pairs)
    return FrozenForecastRoster("roster.battery-durable-inquiry.qualification", source, policy, configurations, pairs)


def entry_dispositions(roster, uncertain):
    if type(roster) is not FrozenForecastRoster or type(uncertain) is not UnknownDiagnosticWork:
        raise ValueError("entry reconciliation requires its actual frozen roster and uncertain work")
    roster.__post_init__()
    uncertain.__post_init__()
    old_forecasts = tuple((native.config_id, forecast_primitive(native)) for native in uncertain.configurations)
    old_initializers = tuple((native.config_id, initializer_primitive(native)) for native in uncertain.configurations)
    rows = []
    for native in roster.configurations:
        forecast, initializer = forecast_primitive(native), initializer_primitive(native)
        forecasts = tuple(sorted(name for name, value in old_forecasts if value == forecast))
        initializers = tuple(sorted(name for name, value in old_initializers if value == initializer))
        rows.append(ForecastEntryDisposition("entry." + native.config_id,
            ObjectIdentity.from_record(roster.roster_id, roster), c.identity(native),
            ObjectIdentity.from_record(uncertain.record_id, uncertain), sha256(forecast).hexdigest(), sha256(initializer).hexdigest(),
            forecasts, initializers, "HOLD_UNCERTAIN_PRIOR_PRIMITIVE" if forecasts or initializers else "NO_EXACT_OVERLAP_FOUND;NOT_ENTRY_AUTHORITY"))
    return tuple(rows)


def require_no_uncertain_primitive(disposition):
    if type(disposition) is not ForecastEntryDisposition:
        raise ValueError("native entry requires its actual source-bound primitive disposition")
    disposition.__post_init__()
    if disposition.state == "HOLD_UNCERTAIN_PRIOR_PRIMITIVE":
        raise ValueError("same forecast or initializer has unknown historical completion; automatic replay refuses")
    return disposition


@dataclass(frozen=True, slots=True)
class ExactConditionReuse(CanonicalRecord):
    """A second selected label shares the original observation; no relabelling.

    This is a DERIVED conditional forecast operand, never a new native result,
    independent observation, qualification or physical unit. Original canonical
    trace, preparation and producing receipts remain unchanged.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-durable-inquiry/exact-condition-reuse"
    reuse_id: str
    requested_configuration: c.NativeConfig
    observed_configuration: c.NativeConfig
    original_trace: ObjectIdentity
    original_summary: ObjectIdentity
    primitive_sha256: str
    kind: str = "DERIVED_FROM_AUTHENTICATED_SAME_CONDITION"
    native_provider_attempts: int = 0
    fresh_physical_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.reuse_id)
        validate_sha256(self.primitive_sha256)
        left, right = self.requested_configuration, self.observed_configuration
        if (type(left) is not c.NativeConfig or type(right) is not c.NativeConfig or left == right
                or left.source != right.source or left.policy != right.policy or left.phase != right.phase
                or forecast_primitive(left) != forecast_primitive(right)
                or self.primitive_sha256 != sha256(forecast_primitive(right)).hexdigest()):
            raise ValueError("conditional reuse changes an actual selected native operand")
        if (self.original_trace.object_schema != c.Trace.SCHEMA
                or self.original_trace.object_id != "trace." + right.config_id
                or self.original_summary.object_schema != "empirical-lawhood/battery-preparation/trace-summary"):
            raise ValueError("conditional reuse loses the original authenticated observation")
        if (self.kind != "DERIVED_FROM_AUTHENTICATED_SAME_CONDITION"
                or self.native_provider_attempts != 0 or self.fresh_physical_units != 0):
            raise ValueError("conditional reuse cannot create native contact or fresh evidence")


def distinct_forecast_groups(roster):
    """All 54 labels remain; first canonical config owns each distinct contact."""
    if type(roster) is not FrozenForecastRoster:
        raise ValueError("distinct forecast projection requires its exact frozen roster")
    roster.__post_init__()
    groups = {}
    for native in roster.configurations:
        groups.setdefault(forecast_primitive(native), []).append(native)
    return tuple(tuple(rows) for rows in groups.values())
