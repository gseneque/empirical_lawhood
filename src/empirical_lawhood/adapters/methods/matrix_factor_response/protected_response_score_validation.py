# SPDX-License-Identifier: MPL-2.0
"""One complete current-response control census for the exact E3 facades."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore, branch_census, has_response_measurements


def validate_current_score(score, native_config, responses, *, source, protocol, panels,
        causal_identity, error_identity, physical_identity, response_identity):
    if type(score) is not ScheduledResponseScore:
        raise TypeError("protected E3 response requires exact current or original record types")
    score.__post_init__()
    if (score.source != native_config.source.identity or score.causal_prefix != causal_identity
            or score.error_forecast != error_identity or score.physical_forecast != physical_identity
            or score.responses != response_identity or score.criterion != protocol.criterion
            or (score.root_id, score.independent_group_id, score.role) !=
                (source.root_id, protocol.public_source.root.independent_group_id, protocol.public_source.root.role.value)):
        raise ValueError("protected E3 target projection substitutes actual current score/source/forecast/response evidence")
    if responses.disposition == "COMPLETED":
        expected = {"control.scheduled." + source.root_id + "." + branch:
            (1 if view == "PRIMARY" else 2) * protocol.horizon_steps[-1]
            for branch, view, *_ in branch_census(protocol, panels)}
        if (score.disposition not in ("FINITE", "PARTIAL", "NATIVE_CROSSCHECK_FAILED")
                or len(score.controls) != len(expected) or {control.control_id for control in score.controls} != set(expected)
                or any(control.denominator_steps != expected[control.control_id]
                    or control.denominator_real_coordinates != 192
                    or control.tolerance != protocol.native_reference_tolerance for control in score.controls)):
            raise ValueError("protected E3 current score changes actual full192 paired native controls or completed/negative status")
    elif (score.disposition != responses.disposition or score.numerical_pass or score.controls
            or has_response_measurements(score)):
        raise ValueError("protected E3 current score invents finite received outcomes after original nonuse")

