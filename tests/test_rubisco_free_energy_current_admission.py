# SPDX-License-Identifier: MPL-2.0
"""Independent adverse oracles and frozen v1 records; no native chemistry."""

from dataclasses import fields, replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import (
    admission_records as records, contracts as c, current_admission as admission, science,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "tests/fixtures/rubisco_insilico_free_energy/legacy-admission-v1.json"
FROZEN_SHA256 = "1592a6a5765ab4abdcc1d999009c2c8c186d9e38e408f390a59ea489b4b1b651"
ASSESSOR = ObjectIdentity("source.exposed-assessor", "empirical-lawhood/test/assessor", "1.0.0", "b" * 64)
CONTACT = ObjectIdentity("contact.exposed-assessor", "empirical-lawhood/test/contact", "1.0.0", "c" * 64)


@pytest.fixture
def case():
    document = json.loads(FROZEN.read_bytes())
    selected = decode_canonical_bytes(document["records"]["selection"]["canonical_text"].encode(), c.FreeEnergySelection, maximum_bytes=None)
    trace = decode_canonical_bytes(document["records"]["satisfied"]["canonical_text"].encode(), c.WindowTrace, maximum_bytes=None)
    return selected, tuple(replace(trace, trace_id="trace." + window.window_id, window=window) for window in selected.windows)


def reported(trace, state):
    if state is A.SATISFIED:
        return trace
    return replace(trace, disposition=state, reason_codes=("EXPOSED_" + state.value,), observations=(),
                   attempted_energy_calls=0 if state is A.NOT_ATTEMPTED else 9,
                   completed_energy_calls=0, cpu_seconds=None, wall_seconds=None, raw_files=())


def report(selection, traces, **kwargs):
    return admission.admit_window_census(selection, traces, report_id="admission.exposed", assessor_source=ASSESSOR, **kwargs)


def malformed(value, **changes):
    """Present a malformed in-memory legacy value without changing its owner."""
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


@pytest.mark.parametrize("state", tuple(A))
def test_uniform_dispositions_keep_all_counts_and_unknown_actual_calls(case, state):
    selection, positive = case
    traces = tuple(reported(trace, state) for trace in positive)
    result = report(selection, traces)
    assert result.reported_preliminary_disposition is state
    assert result.disposition_counts == tuple((item, 6 if item is state else 0) for item in A)
    assert len(result.selected_windows) == len(result.windows) == 6
    assert sum(row.retained_sample_count + row.missing_selected_sample_count for row in result.windows) == 18
    assert result.independent_sampling_disposition is A.NOT_ATTEMPTED
    assert result.biological_target_disposition is A.UNEVALUABLE
    assert result.fresh_physical_units == 0 and result.qualification == "NOT_PERFORMED"
    for row, original in zip(result.windows, traces, strict=True):
        assert row.legacy_trace == c.identity(original) and row.raw_files == original.raw_files
        assert row.reported_attempted_energy_calls == original.attempted_energy_calls
        assert row.reported_completed_energy_calls == original.completed_energy_calls
        assert row.actual_attempted_energy_calls is None and row.actual_completed_energy_calls is None
        assert row.native_call_coverage_assessment_disposition is A.NOT_ATTEMPTED
        assert row.raw_custody_assessment_disposition is A.NOT_ATTEMPTED
        assert row.reported_cpu_seconds == original.cpu_seconds


# Literal independently authored table in enum order; not derived from the
# implementation's precedence or reducer.
ORACLE = (
    (A.SATISFIED, A.FALSIFIED, A.REFUSED, A.UNEVALUABLE, A.UNSUPPORTED, A.NOT_ATTEMPTED),
    (A.FALSIFIED, A.FALSIFIED, A.REFUSED, A.UNEVALUABLE, A.FALSIFIED, A.FALSIFIED),
    (A.REFUSED, A.REFUSED, A.REFUSED, A.UNEVALUABLE, A.REFUSED, A.REFUSED),
    (A.UNEVALUABLE, A.UNEVALUABLE, A.UNEVALUABLE, A.UNEVALUABLE, A.UNEVALUABLE, A.UNEVALUABLE),
    (A.UNSUPPORTED, A.FALSIFIED, A.REFUSED, A.UNEVALUABLE, A.UNSUPPORTED, A.UNSUPPORTED),
    (A.NOT_ATTEMPTED, A.FALSIFIED, A.REFUSED, A.UNEVALUABLE, A.UNSUPPORTED, A.NOT_ATTEMPTED),
)
PAIRS = tuple((left, right, ORACLE[i][j]) for i, left in enumerate(A) for j, right in enumerate(A))


@pytest.mark.parametrize("left,right,expected", PAIRS, ids=[left.value + "-" + right.value for left, right, _ in PAIRS])
def test_all_36_mixed_pairs_use_literal_oracle_with_complete_window_census(case, left, right, expected):
    selection, positive = case
    traces = (reported(positive[0], left), reported(positive[1], right), *positive[2:])
    result = report(selection, traces)
    assert result.reported_preliminary_disposition is expected
    assert science.preliminary_sampling_disposition(selection, traces) is expected
    assert sum(total for _, total in result.disposition_counts) == 6
    assert result.canonical_bytes() == report(selection, tuple(reversed(traces))).canonical_bytes()


def test_all_six_outcomes_survive_a_single_report(case):
    selection, positive = case
    result = report(selection, tuple(reported(trace, state) for trace, state in zip(positive, A, strict=True)))
    assert result.disposition_counts == tuple((state, 1) for state in A)
    assert result.reported_preliminary_disposition is A.UNEVALUABLE
    assert tuple(row.reported_disposition for row in result.windows) == tuple(A)


@pytest.mark.parametrize("value", ("SATISFIED", "UNKNOWN", None, True, 0))
def test_unknown_or_untyped_disposition_refuses(case, value):
    selection, traces = case
    with pytest.raises(ValueError, match="typed"):
        report(selection, (malformed(traces[0], disposition=value), *traces[1:]))
    with pytest.raises(ValueError, match="typed census"):
        admission.reduce_reported_dispositions((value,))


@pytest.mark.parametrize("bad", (None, SimpleNamespace(window=None), "trace"))
def test_wrong_trace_types_refuse_before_attribute_lookup(case, bad):
    selection, traces = case
    with pytest.raises(ValueError, match="WindowTrace"):
        report(selection, (bad, *traces[1:]))
    with pytest.raises(ValueError, match="FreeEnergySelection"):
        report(bad, traces)


@pytest.mark.parametrize("raw", ({"untyped": "output"}, "raw", None))
def test_malformed_raw_references_refuse_before_hash_or_attribute_lookup(case, raw):
    selection, traces = case
    with pytest.raises(ValueError, match="ObjectIdentity"):
        report(selection, (malformed(traces[0], raw_files=(raw,)), *traces[1:]))


@pytest.mark.parametrize("changes", (
    {"attempted_energy_calls": 1}, {"attempted_energy_calls": 1, "completed_energy_calls": 1},
    {"observations": ((2, D(0), (D(1),)),)}, {"raw_files": (CONTACT,)},
))
def test_not_attempted_with_any_reported_work_refuses(case, changes):
    selection, positive = case
    trace = reported(positive[0], A.NOT_ATTEMPTED)
    with pytest.raises(ValueError, match="NOT_ATTEMPTED"):
        report(selection, (malformed(trace, **changes), *positive[1:]))


@pytest.mark.parametrize("ordinals", ((True,), (-2,), (0,), (1,), (8,), (2, 2), (4, 2)))
def test_partial_adverse_observations_require_exact_production_schedule(case, ordinals):
    selection, positive = case
    trace = malformed(reported(positive[0], A.FALSIFIED), observations=tuple((step, D(0), (D(1),)) for step in ordinals))
    with pytest.raises(ValueError, match="ordinal"):
        report(selection, (trace, *positive[1:]))


@pytest.mark.parametrize("changes", (
    {"observations": ()}, {"observations": ((2, D(0), (D(1),)),)},
    {"attempted_energy_calls": 0, "completed_energy_calls": 0},
    {"completed_energy_calls": 8}, {"raw_files": ()},
))
def test_positive_window_cannot_hide_partial_empty_or_incomplete_calls(case, changes):
    selection, traces = case
    with pytest.raises(ValueError, match="successful"):
        report(selection, (malformed(traces[0], **changes), *traces[1:]))


@pytest.mark.parametrize("attempted,completed", ((True, 0), (9, False), (-1, 0), (1, 2), (None, 0)))
def test_reported_call_totals_remain_strict_known_v1_integers(case, attempted, completed):
    selection, positive = case
    trace = malformed(reported(positive[0], A.UNEVALUABLE), attempted_energy_calls=attempted, completed_energy_calls=completed)
    with pytest.raises(ValueError, match="ledger"):
        report(selection, (trace, *positive[1:]))


def test_honest_partial_adverse_samples_and_unknown_costs_remain_retained(case):
    selection, positive = case
    trace = replace(reported(positive[0], A.FALSIFIED), observations=positive[0].observations[1:2], completed_energy_calls=2)
    result = report(selection, (trace, *positive[1:]))
    assert result.reported_preliminary_disposition is A.FALSIFIED
    assert result.windows[0].retained_sample_count == 1 and result.windows[0].missing_selected_sample_count == 2
    assert result.windows[0].reported_cpu_seconds is None
    assert science.retained_expense((trace, *positive[1:])) == {"cpu_seconds": None, "wall_seconds": None}


def test_empty_selected_observation_schedule_cannot_admit_positive(case):
    selection, positive = case
    selected = replace(selection, windows=tuple(replace(window, sample_interval=10) for window in selection.windows))
    traces = tuple(replace(trace, selection=c.identity(selected), window=window) for trace, window in zip(positive, selected.windows, strict=True))
    with pytest.raises(ValueError, match="schedule|denominator"):
        report(selected, traces)
    adverse = tuple(reported(trace, A.NOT_ATTEMPTED) for trace in traces)
    assert report(selected, adverse).reported_preliminary_disposition is A.NOT_ATTEMPTED


@pytest.mark.parametrize("kind", ("missing", "extra", "duplicate"))
def test_selected_window_roster_cannot_be_thinned(case, kind):
    selection, traces = case
    original = selection.canonical_bytes()
    if kind == "missing":
        changed = traces[1:]
    elif kind == "duplicate":
        changed = (*traces, replace(traces[0], trace_id="trace.extra"))
    else:
        changed = (*traces, replace(traces[0], trace_id="trace.foreign", window=replace(traces[0].window, window_id="window.foreign")))
    with pytest.raises(ValueError, match="complete attempted"):
        report(selection, changed)
    assert selection.canonical_bytes() == original and len(selection.windows) == 6


@pytest.mark.parametrize("field,value", (
    ("temperature_kelvin", D(301)), ("standard_state_definition", "OTHER_STANDARD_STATE"),
    ("independent_refinement", CONTACT), ("standard_state_correction", CONTACT),
    ("actual_mechanism", CONTACT), ("actual_preparation", CONTACT),
    ("minimum_effective_samples", D(3)), ("minimum_adjacent_overlap", D(".2")),
    ("maximum_block_disagreement_kcal", D(2)), ("maximum_refinement_disagreement_kcal", D(2)),
))
def test_changed_scientific_conditions_and_controls_cannot_reuse_old_trace_joins(case, field, value):
    selection, traces = case
    with pytest.raises(ValueError, match="exact selected"):
        report(replace(selection, **{field: value}), traces)


@pytest.mark.parametrize("field,value", (("centers", (D(2),)), ("random_seed", 11), ("force_constants", (D(4),)), ("cv_atom_ids", (("h2", "h1"),))))
def test_window_atoms_restraints_and_seed_cannot_reuse_old_trace(case, field, value):
    selection, traces = case
    selected = replace(selection, windows=(replace(selection.windows[0], **{field: value}), *selection.windows[1:]))
    with pytest.raises(ValueError, match="exact selected"):
        report(selected, traces)


def test_report_joins_legacy_raw_sources_costs_and_assessor_exactly(case):
    selection, traces = case
    result = report(selection, traces)
    assert admission.validate_census_admission(result, selection, traces, assessor_source=ASSESSOR) == result
    for changed in (replace(traces[0], raw_files=(CONTACT,)), replace(traces[0], cpu_seconds=D(2))):
        with pytest.raises(ValueError, match="actual trace"):
            admission.validate_census_admission(result, selection, (changed, *traces[1:]), assessor_source=ASSESSOR)
    with pytest.raises(ValueError, match="actual trace"):
        admission.validate_census_admission(result, selection, traces, assessor_source=CONTACT)


@pytest.mark.parametrize("changes", (
    {"disposition_counts": ((A.SATISFIED, 5),)}, {"selected_windows": ()},
    {"reported_preliminary_disposition": A.FALSIFIED}, {"fresh_physical_units": 1},
    {"independent_sampling_disposition": A.SATISFIED, "independent_sampling_assessment": CONTACT},
))
def test_additive_report_refuses_count_qualification_and_unbound_assessment_forgery(case, changes):
    selection, traces = case
    with pytest.raises(ValueError):
        replace(report(selection, traces), **changes)


def test_unresolved_assessor_contact_is_uncertain_and_never_a_positive_independent_assessment(case):
    selection, traces = case
    result = report(selection, traces, independent_sampling_contact=CONTACT)
    assert result.reported_preliminary_disposition is A.SATISFIED
    assert result.independent_sampling_disposition is A.UNEVALUABLE
    assert result.independent_sampling_assessment is None and result.biological_target_disposition is A.UNEVALUABLE
    for row in result.windows:
        with pytest.raises(ValueError, match="pure record consistency"):
            replace(row, actual_attempted_energy_calls=0)
        with pytest.raises(ValueError, match="pure record consistency"):
            replace(row, native_call_coverage_assessment_disposition=A.SATISFIED)


def test_frozen_legacy_bytes_versions_and_decimal_values_remain_exact(case):
    payload = FROZEN.read_bytes()
    assert sha256(payload).hexdigest() == FROZEN_SHA256
    fixture = json.loads(payload)
    contract_pin = next(row for row in fixture["source_before"] if row["path"].endswith("/contracts.py"))
    assert sha256((ROOT / contract_pin["path"]).read_bytes()).hexdigest() == contract_pin["sha256"]
    for name, row in fixture["records"].items():
        original = row["canonical_text"].encode()
        assert sha256(original).hexdigest() == row["sha256"]
        value = decode_canonical_bytes(original, c.FreeEnergySelection if name == "selection" else c.WindowTrace, maximum_bytes=None)
        assert value.VERSION == "1.0.0" and value.canonical_bytes() == original
    selection, traces = case
    original = tuple(trace.canonical_bytes() for trace in traces)
    result = report(selection, traces)
    assert tuple(trace.canonical_bytes() for trace in traces) == original
    assert decode_canonical_bytes(result.canonical_bytes(), records.WindowCensusAdmission, maximum_bytes=None) == result
    legacy = decode_canonical_bytes(fixture["records"]["legacy_not_attempted_with_actual_work"]["canonical_text"].encode(), c.WindowTrace, maximum_bytes=None)
    with pytest.raises(ValueError, match="NOT_ATTEMPTED"):
        report(selection, (legacy, *traces[1:]))
    assert legacy.canonical_bytes().decode() == fixture["records"]["legacy_not_attempted_with_actual_work"]["canonical_text"]


def test_nested_parallel_supplied_expense_sums_are_not_unique_native_or_elapsed_costs():
    parent = SimpleNamespace(cpu_seconds=D(7), wall_seconds=D(9))
    other = SimpleNamespace(cpu_seconds=D(3), wall_seconds=D(4))
    assert science.retained_expense((parent, other)) == {"cpu_seconds": D(10), "wall_seconds": D(13)}
    assert science.retained_expense((parent, SimpleNamespace(cpu_seconds=None, wall_seconds=None))) == {"cpu_seconds": None, "wall_seconds": None}
