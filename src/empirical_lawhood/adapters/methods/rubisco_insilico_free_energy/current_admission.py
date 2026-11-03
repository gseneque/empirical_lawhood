# SPDX-License-Identifier: MPL-2.0
"""Pure present-use validation, separate from producer and native assessment."""

from decimal import Decimal
from hashlib import sha256

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import validate_stable_id
from . import contracts as c, admission_records as r


def reduce_reported_dispositions(dispositions):
    if not dispositions or any(type(value) is not A for value in dispositions):
        raise ValueError("reported sampling dispositions require a nonempty typed census")
    return next(value for value in r.REPORTED_PRECEDENCE if value in dispositions)


def validate_complete_window_census(selection, traces):
    if type(selection) is not c.FreeEnergySelection:
        raise ValueError("sampling requires exact FreeEnergySelection")
    if any(type(getattr(selection, name)) is not tuple for name in ("models", "windows", "original_assets_roster", "chemical_states")):
        raise ValueError("sampling requires exact selected roster tuples")
    if type(selection.engine) is not c.EngineBinding or any(type(model) is not c.ReactiveModel
            or type(model.alternative) is not c.ChemicalAlternative for model in selection.models):
        raise ValueError("sampling substitutes exact selected engine/model/state types")
    if any(type(window) is not c.UmbrellaWindow for window in selection.windows):
        raise ValueError("sampling substitutes exact selected window types")
    try:
        selection.__post_init__()
    except (TypeError, AttributeError) as error:
        raise ValueError("malformed current sampling selection") from error
    for value in (selection.actual_mechanism, selection.actual_preparation,
                  selection.standard_state_correction, selection.independent_refinement, *selection.original_assets_roster):
        r.identity(value, "selected scientific source/control")
    for model in selection.models:
        for value in (model.original_assets, model.preparation_assessment, model.complement,
                      model.transformation, *model.alternative.source_members):
            r.identity(value, "selected model/source/control")
    if type(traces) is not tuple or any(type(trace) is not c.WindowTrace for trace in traces):
        raise ValueError("sampling requires an exact tuple of WindowTrace records")
    for trace in traces:
        validate_stable_id(trace.trace_id)
        if type(trace.window) is not c.UmbrellaWindow:
            raise ValueError("sampling requires exact trace window types")
        trace.window.__post_init__()
    rows = {trace.window.window_id: trace for trace in traces}
    if len(rows) != len(traces) or rows.keys() != {window.window_id for window in selection.windows}:
        raise ValueError("complete attempted window census omitted/duplicated/substituted")
    if len({trace.trace_id for trace in traces}) != len(traces):
        raise ValueError("sampling duplicates exact trace identities")
    ordered = tuple(rows[window.window_id] for window in selection.windows)
    selected_identity = c.identity(selection)
    for trace, window in zip(ordered, selection.windows, strict=True):
        r.identity(trace.selection, "trace selection")
        if trace.selection != selected_identity or trace.window != window:
            raise ValueError("sampling changes exact selected source/window/initialization")
        if type(trace.disposition) is not A:
            raise ValueError("reported sampling disposition must be typed")
        if type(trace.reason_codes) is not tuple or any(type(code) is not str or not code for code in trace.reason_codes):
            raise ValueError("reported sampling reasons must be explicit strings")
        if trace.disposition is not A.SATISFIED and not trace.reason_codes:
            raise ValueError("adverse sampling requires its actual reason")
        for value in (trace.cpu_seconds, trace.wall_seconds):
            r.expense(value)
        if type(trace.raw_files) is not tuple:
            raise ValueError("raw reference census must be an exact unique tuple")
        for raw in trace.raw_files:
            r.identity(raw, "reported raw reference")
        if len(set(trace.raw_files)) != len(trace.raw_files):
            raise ValueError("raw reference census must be an exact unique tuple")
        if type(trace.observations) is not tuple:
            raise ValueError("sampling observations must retain the exact tuple")
        expected_count = window.sampling_steps // window.sample_interval
        for observation in trace.observations:
            if type(observation) is not tuple or len(observation) != 3:
                raise ValueError("malformed production observation")
            ordinal, energy, cv = observation
            if (type(ordinal) is not int or ordinal < window.sample_interval
                    or ordinal > window.sampling_steps or ordinal % window.sample_interval):
                raise ValueError("sampling observation ordinal is outside selected production schedule")
            if (type(energy) is not Decimal or not energy.is_finite() or type(cv) is not tuple
                    or len(cv) != len(window.centers) or any(type(value) is not Decimal or not value.is_finite() for value in cv)):
                raise ValueError("sample requires full finite Decimal energy/CV observation")
        try:
            trace.__post_init__()
        except (TypeError, AttributeError) as error:
            raise ValueError("malformed current window trace") from error
        if trace.disposition is A.SATISFIED and (not expected_count or len(trace.observations) != expected_count
                or any(row[0] != (index + 1) * window.sample_interval for index, row in enumerate(trace.observations))):
            raise ValueError("successful sampling omits full production observation denominator")
        if trace.disposition is A.NOT_ATTEMPTED and (
                trace.attempted_energy_calls or trace.completed_energy_calls or trace.observations or trace.raw_files):
            raise ValueError("NOT_ATTEMPTED sampling contains reported actual work")
    return ordered


def admit_window_census(selection, traces, *, report_id, assessor_source, independent_sampling_contact=None):
    """Report exact producer-record consistency, leaving independent science open.

    A supplied contact reference can only record unresolved assessment contact;
    neither a reference nor producer re-execution grants independent acceptance.
    Actual native-call totals and authentication remain unknown in this PURE route.
    """
    ordered = validate_complete_window_census(selection, traces)
    r.identity(assessor_source, "assessor source")
    if independent_sampling_contact is not None:
        r.identity(independent_sampling_contact, "reported independent sampling contact")
    selected_identity = c.identity(selection)
    admitted = tuple(r.WindowAdmission(
        "window-admission." + sha256(trace.fingerprint().encode()).hexdigest()[:24],
        selected_identity, ObjectIdentity.from_record(trace.window.window_id, trace.window), c.identity(trace), trace.disposition,
        trace.window.sampling_steps // trace.window.sample_interval, len(trace.observations),
        trace.window.sampling_steps // trace.window.sample_interval - len(trace.observations),
        trace.attempted_energy_calls, trace.completed_energy_calls, trace.cpu_seconds, trace.wall_seconds,
        trace.raw_files, tuple(sorted(set(trace.reason_codes))),
    ) for trace in ordered)
    contact = independent_sampling_contact is not None
    return r.WindowCensusAdmission(
        report_id, selected_identity, tuple(ObjectIdentity.from_record(window.window_id, window) for window in selection.windows), admitted,
        assessor_source, r.METHOD_CONTRACT,
        tuple((state, sum(trace.disposition is state for trace in ordered)) for state in A),
        reduce_reported_dispositions(tuple(trace.disposition for trace in ordered)),
        independent_sampling_contact, A.UNEVALUABLE if contact else A.NOT_ATTEMPTED, None,
        ("INDEPENDENT_SAMPLING_CONTACT_WITHOUT_AUTHENTICATED_ASSESSMENT",) if contact
        else ("INDEPENDENT_SAMPLING_ASSESSMENT_NOT_ENTERED",),
    )


def validate_census_admission(report, selection, traces, *, assessor_source):
    """Check an admission against actual immutable inputs and selected assessor."""
    if type(report) is not r.WindowCensusAdmission:
        raise ValueError("current admission must be an exact WindowCensusAdmission")
    report.__post_init__()
    expected = admit_window_census(selection, traces, report_id=report.report_id,
                                  assessor_source=assessor_source,
                                  independent_sampling_contact=report.independent_sampling_contact)
    if report != expected:
        raise ValueError("admission changes actual trace/window/source/control/cost joins")
    return report
