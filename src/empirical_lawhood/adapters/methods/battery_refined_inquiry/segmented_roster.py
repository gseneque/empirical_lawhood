# SPDX-License-Identifier: MPL-2.0
"""Complete selected census and substantive prospective-method disposition.

Changed source-derived preparation and segment durations are actual numerical
operands. Historical UNKNOWN work is retained unchanged. This disposition is
neither a recovery clearance nor scientific issue/execution authority.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from . import contracts as c
from . import durable_roster as dr
from . import segmented_contracts as sc
from .source_derived_preparation import require_assessed_source_roots

D = Decimal


def identity(record, name):
    return ObjectIdentity.from_record(getattr(record, name), record)


@dataclass(frozen=True, slots=True)
class SegmentedQualificationRoster(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/qualification-roster"
    roster_id: str
    original_selection: dr.FrozenForecastRoster
    uncertain_work: ObjectIdentity
    method: sc.SegmentedMethodProtocol
    configurations: tuple[sc.SegmentedNativeConfig, ...]
    comparison_config_pairs: tuple[tuple[str, str], ...]
    scientific_unit_id: str = c.UNIT
    fresh_physical_units: int = 0
    historical_completion: str = "NOT_ASSESSED;OLD_UNKNOWN_RETAINED"

    def __post_init__(self):
        validate_stable_id(self.roster_id)
        if type(self.original_selection) is not dr.FrozenForecastRoster or type(self.method) is not sc.SegmentedMethodProtocol:
            raise ValueError("segmented roster substitutes its complete original selection or prospective method")
        self.original_selection.__post_init__()
        self.method.__post_init__()
        if self.uncertain_work.object_schema != dr.UnknownDiagnosticWork.SCHEMA:
            raise ValueError("segmented roster loses the actual uncertain-work source")
        if (len(self.configurations) != 54 or any(type(row) is not sc.SegmentedNativeConfig for row in self.configurations)
                or tuple(row.native for row in self.configurations) != self.original_selection.configurations
                or any(row.method != self.method for row in self.configurations)
                or len({row.config_id for row in self.configurations}) != 54):
            raise ValueError("segmented roster omits, reorders or relabels its full fifty-four selected slots")
        names = {row.native.config_id: row.config_id for row in self.configurations}
        if (self.comparison_config_pairs != tuple((names[left.object_id], names[right.object_id]) for left, right in self.original_selection.comparison_config_pairs)
                or len(self.comparison_config_pairs) != 36):
            raise ValueError("segmented roster changes its complete thirty-six selected comparisons")
        if self.scientific_unit_id != c.UNIT or self.fresh_physical_units != 0 or self.historical_completion != "NOT_ASSESSED;OLD_UNKNOWN_RETAINED":
            raise ValueError("segmented roster cannot grant fresh units or old completion")


def freeze_segmented_roster(original, unknown, method, supplies):
    """Use exact assessed stock suppliers; retain every selected comparison slot."""
    if type(unknown) is not dr.UnknownDiagnosticWork:
        raise ValueError("segmented roster requires actual typed unknown completion")
    unknown.__post_init__()
    if set(supplies) != {"Chen2020", "ORegan2022"}:
        raise ValueError("segmented roster requires both complete parameter-stock suppliers")
    for preparation, assessment in supplies.values():
        require_assessed_source_roots(preparation, assessment)
    configs = []
    for native in original.configurations:
        stock = "Chen2020" if native.model_view == "chen-spme" else "ORegan2022"
        preparation, assessment = supplies[stock]
        configs.append(sc.SegmentedNativeConfig("config.segmented." + str(method.maximum_segment_horizon_s) + "." + native.config_id.removeprefix("config."),
            native, preparation, assessment, method))
    names = {row.native.config_id: row.config_id for row in configs}
    return SegmentedQualificationRoster("roster.segmented." + str(method.maximum_segment_horizon_s), original,
        identity(unknown, "record_id"), method, tuple(configs), tuple((names[left.object_id], names[right.object_id]) for left, right in original.comparison_config_pairs))


@dataclass(frozen=True, slots=True)
class ProspectiveMethodDisposition(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/prospective-method-disposition"
    disposition_id: str
    roster: ObjectIdentity
    configuration: ObjectIdentity
    original_entry: dr.ForecastEntryDisposition
    source_preparation: ObjectIdentity
    source_assessment: ObjectIdentity
    method: ObjectIdentity
    prospective_duration_binary64: str
    changed_preparation: str = "ASSESSED_SOURCE_ROOT_OPERANDS_ASSIGNED_DIRECTLY;NO_DEFAULT_NATIVE_ESOH_CONTACT"
    changed_continuation: str = "PROSPECTIVE_SHORT_STEP_REQUESTS;FULL_OUTPUT_DURABLE_BETWEEN_CALLS;GLOBAL_CLOCK_AND_FULL_STATE_RETAINED"
    prior_uncertainty: str = "UNCHANGED;OLD_COUNTS_UNKNOWN;NO_REPLAY_OR_COMPLETION_CLEARANCE"
    scientific_authority: str = "NONE"
    fidelity: str = "UNQUALIFIED;INDEPENDENT_CONTROLS_REQUIRED"

    def __post_init__(self):
        validate_stable_id(self.disposition_id)
        if (self.roster.object_schema != SegmentedQualificationRoster.SCHEMA or self.configuration.object_schema != sc.SegmentedNativeConfig.SCHEMA
                or type(self.original_entry) is not dr.ForecastEntryDisposition
                or self.source_preparation.object_schema != "empirical-lawhood/battery-preparation/source-derived-electrodes"
                or self.source_assessment.object_schema != "empirical-lawhood/battery-preparation/source-root-assessment"
                or self.method.object_schema != sc.SegmentedMethodProtocol.SCHEMA
                or self.prospective_duration_binary64 not in tuple(float(value).hex() for value in (60, 30, 15))
                or self.changed_preparation != "ASSESSED_SOURCE_ROOT_OPERANDS_ASSIGNED_DIRECTLY;NO_DEFAULT_NATIVE_ESOH_CONTACT"
                or self.changed_continuation != "PROSPECTIVE_SHORT_STEP_REQUESTS;FULL_OUTPUT_DURABLE_BETWEEN_CALLS;GLOBAL_CLOCK_AND_FULL_STATE_RETAINED"
                or self.prior_uncertainty != "UNCHANGED;OLD_COUNTS_UNKNOWN;NO_REPLAY_OR_COMPLETION_CLEARANCE"
                or self.scientific_authority != "NONE" or self.fidelity != "UNQUALIFIED;INDEPENDENT_CONTROLS_REQUIRED"):
            raise ValueError("prospective method disposition cannot clear unknown completion or grant scientific entry")
        self.original_entry.__post_init__()


def method_dispositions(roster, unknown):
    """Explain changed actual operands, while keeping every old HOLD exact."""
    if type(roster) is not SegmentedQualificationRoster or roster.uncertain_work != identity(unknown, "record_id"):
        raise ValueError("prospective method changes its authentic selected uncertain-work join")
    roster.__post_init__()
    old = dr.entry_dispositions(roster.original_selection, unknown)
    rows = []
    for config, prior in zip(roster.configurations, old, strict=True):
        require_assessed_source_roots(config.preparation, config.preparation_assessment)
        rows.append(ProspectiveMethodDisposition("disposition.segmented." + config.config_id, identity(roster, "roster_id"),
            identity(config, "config_id"), prior, identity(config.preparation, "preparation_id"),
            identity(config.preparation_assessment, "assessment_id"), identity(config.method, "method_id"),
            float(config.method.maximum_segment_horizon_s).hex()))
    return tuple(rows)


def distinct_forecast_groups(roster):
    """Exact equal-condition aliases stay explicit at each prospective method."""
    groups = {}
    for index, config in enumerate(roster.configurations):
        key = (dr.forecast_primitive(config.native), config.method.fingerprint(), config.preparation.fingerprint(), config.preparation_assessment.fingerprint())
        groups.setdefault(key, []).append(index)
    return tuple(tuple(group) for group in groups.values())

