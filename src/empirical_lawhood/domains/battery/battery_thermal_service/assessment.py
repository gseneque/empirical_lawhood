# SPDX-License-Identifier: MPL-2.0
'Independent thermal-service assessment over an original complete trace. Uses realized current and preserves absent whole-time certification.'

from dataclasses import replace
from decimal import Decimal
from empirical_lawhood.domains.battery.battery_thermal_service.contracts import BatteryThermalAssessment, EVENTS


def assess(config, trace):
    """Integrate the realized current; never infer delivery from a request."""
    if config.operation != "assess":
        raise ValueError("thermal assessment requires its separately selected operation")
    if trace.config != replace(config, operation="acquire"):
        # Config identities belong to their operation, so compare the scientific
        # fields separately when the authored nodes use distinct labels.
        expected = replace(config, operation="acquire", config_id=trace.config.config_id)
        if trace.config != expected:
            raise ValueError("thermal assessment substitutes its producing scientific operands")
    reasons = []
    realized = capacity = discrepancy = None
    envelope = guarded = False
    if not trace.times_s:
        reasons.append("native-receivers-absent")
    else:
        realized = -sum(((a + b) * (t1 - t0) / Decimal(7200)
                         for t0, t1, a, b in zip(trace.times_s, trace.times_s[1:], trace.current_a, trace.current_a[1:])), Decimal(0))
        capacity = -(trace.discharge_capacity_ah[-1] - trace.discharge_capacity_ah[0])
        discrepancy = abs(realized - capacity)
        # This is a declared numerical receiver agreement, not physical uncertainty.
        if discrepancy > Decimal("1e-8"):
            reasons.append("current-capacity-disagreement")
        if realized < Decimal("0.36375"):
            reasons.append("useful-charge-not-delivered")
        envelope = (all(Decimal("2.5") <= v <= Decimal("4.2") for v in trace.voltage_v)
                    and all(Decimal("273.15") <= t <= Decimal("318.15") for t in trace.volume_mean_temperature_k)
                    and all(abs(i) <= Decimal("1.455") for i in trace.current_a))
        if not envelope:
            reasons.append("sampled-service-envelope-violation")
        if trace.accepted_current_a != config.current_a or trace.applied_current_a != config.current_a or any(i != config.current_a for i in trace.current_a):
            reasons.append("native-current-delivery-differs")
        guarded = (trace.event_names == EVENTS and len(trace.processed_event_expressions) == len(EVENTS)
                   and all(trace.processed_event_expressions) and trace.disposition == "COMPLETE")
    if trace.disposition != "COMPLETE":
        reasons.append("full-service-horizon-not-realized")
    if reasons:
        disposition = "UNEVALUABLE" if not trace.times_s else "SERVICE_FAIL"
    else:
        disposition = "UNEVALUABLE"
        reasons.append("whole-time-certificate-absent")
    return BatteryThermalAssessment(config.fingerprint(), trace.fingerprint(), disposition,
                                    tuple(sorted(reasons)), realized, capacity, discrepancy, envelope, guarded)
