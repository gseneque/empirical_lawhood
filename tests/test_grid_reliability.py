# SPDX-License-Identifier: MPL-2.0
"""Literal exposed software controls; no simulator, source or qualification."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
from hashlib import sha256
import struct

import pytest

from empirical_lawhood.adapters.simulators.grid2op_response.contracts import (
    Grid2OpChronicBinding, Grid2OpNativeStep, Grid2OpSourceBinding,
)
from empirical_lawhood.adapters.simulators.grid2op_response.independent_reliability import independently_check_grid_reliability
from empirical_lawhood.adapters.simulators.grid2op_response.reliability import (
    assess_grid_reliability_panel, assess_grid_saved_episode,
)
from empirical_lawhood.adapters.simulators.grid2op_response.reliability_contracts import (
    GridDeliveredEnergyReceiver, GridEpisodeRole, GridEpisodeTermination,
    GridOperatingEpisodeContext, GridReliabilityDisposition, GridReliabilityRequirement,
    GridSavedOperatingEpisode, GridServiceInterval,
)
from empirical_lawhood.adapters.simulators.grid2op_response.reliability_dataset import (
    DATASET_MEMBERS, EVENT_MEMBERS, VALUE_MEMBERS, GridServiceDatasetSelection, assess_grid_service_dataset,
)
from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader
from empirical_lawhood.kernel.datasets import ArrayDatasetManifest, ArrayDatasetMember
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity


def ref(name):
    return ObjectIdentity(name, "empirical-lawhood/tests/grid-literal-original-source", "1.0.0", sha256(name.encode()).hexdigest())


def operands():
    chronics = tuple(Grid2OpChronicBinding("chronic.literal." + str(index), "literal-" + str(index),
        str(index) * 64, "2026-01-01T00:00:00Z", 300, 3, "a" * 64, True) for index in (1, 2))
    source = Grid2OpSourceBinding("source.grid.literal", "1.12.5", "a" * 64, "literal-exposed-grid",
        "LightSimBackend", "0.13.1", "b" * 64, "c" * 64, "literal.rules", "d" * 64,
        "literal.actions", "literal.observations", "e" * 64, "literal.chronics", chronics, True, False, False)
    source_id = ObjectIdentity.from_record(source.binding_id, source)
    receiver = GridDeliveredEnergyReceiver("receiver.grid.literal", source_id, ref("source.literal.energy-receiver"),
        ref("source.literal.terminal-semantics"), "Literal paired demanded and delivered load energy; no native measurement.")
    criterion = GridReliabilityRequirement("requirement.grid.literal", source_id, ref("source.literal.consequential-criterion"),
        receiver.identity, D("0.25"), D("1"), 0, True)
    return source, receiver, criterion


def episode(source, receiver, *, unit=0, branch="branch.hold", termination=GridEpisodeTermination.COMPLETED,
        role=GridEpisodeRole.DEVELOPMENT, deliveries=("0.95", "1", "1")):
    chronic = source.chronic_bindings[unit]
    context = GridOperatingEpisodeContext("episode." + chronic.chronic_id + "." + branch, chronic.chronic_id,
        ObjectIdentity.from_record(source.binding_id, source), ObjectIdentity.from_record(chronic.chronic_id, chronic),
        receiver.identity, branch, ref("contingency.literal.unchanged"), role, ref("source.literal.original-chronology"),
        1, None if termination is GridEpisodeTermination.NOT_ENTERED else 2, termination,
        () if termination is GridEpisodeTermination.COMPLETED else ("LITERAL_ORIGINAL_STOP",))
    rows = []
    for ordinal, delivered in enumerate(deliveries, 1):
        terminal = ordinal == len(deliveries) and termination in (
            GridEpisodeTermination.COMPLETED, GridEpisodeTermination.PREMATURE_TERMINAL, GridEpisodeTermination.BACKEND_DIVERGENCE)
        error = terminal and termination is GridEpisodeTermination.BACKEND_DIVERGENCE
        step = Grid2OpNativeStep("step." + chronic.chronic_id + "." + branch + "." + str(ordinal), branch, ordinal,
            ordinal, "2026-01-01T00:" + str(ordinal * 5).zfill(2) + ":00Z", "HOLD", "HOLD", "HOLD", "HOLD",
            False, False, True, "topology.literal", "f" * 64, 1, 0, D("0.8"), terminal, error,
            not error, ("GRID2OP_BACKEND_EXCEPTION",) if error else ())
        rows.append(GridServiceInterval(step, 300, D(1), D(delivered), D("0.125"), D("0.01"), D("0.001"), True, False, False))
    return GridSavedOperatingEpisode(context, tuple(rows))


def test_complete_energy_arithmetic_is_exact_under_low_decimal_precision():
    source, receiver, criterion = operands()
    original = episode(source, receiver, deliveries=("0.12345678901234567890123456789", "1", "1"))
    with localcontext() as context:
        context.prec = 2
        result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
        assert independently_check_grid_reliability(source=source, receiver=receiver, requirement=criterion,
            episode=original, report=result)
    assert result.demanded_energy_mwh == D(3)
    assert result.delivered_energy_mwh == D("2.12345678901234567890123456789")
    assert result.unserved_energy_mwh == D("0.87654321098765432109876543211")
    assert result.redispatch_magnitude_mwh == D("0.375") and result.curtailed_energy_mwh == D("0.03")
    assert result.runtime_seconds == D("0.003") and result.disposition is GridReliabilityDisposition.FAILED
    assert decode_canonical_bytes(original.canonical_bytes(), GridSavedOperatingEpisode, maximum_bytes=None) == original


def test_expected_final_terminal_is_distinct_from_premature_failure():
    source, receiver, criterion = operands()
    complete = episode(source, receiver)
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=complete)
    assert result.disposition is GridReliabilityDisposition.SATISFIED and result.observed_intervals == 3
    assert complete.intervals[-1].native_step.done
    early = episode(source, receiver, termination=GridEpisodeTermination.PREMATURE_TERMINAL, deliveries=("1",))
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=early)
    assert result.disposition is GridReliabilityDisposition.FAILED and result.observed_intervals == 1 and result.expected_intervals == 3
    assert "GRID_SURVIVAL_REQUIREMENT_FAILED" in result.reason_codes
    assert independently_check_grid_reliability(source=source, receiver=receiver, requirement=criterion, episode=early, report=result)


@pytest.mark.parametrize("event", ("illegal", "ambiguous", "unrealized", "forecasts", "refusal", "fallback"))
def test_actual_adverse_events_are_retained_and_fallback_service_is_measured(event):
    source, receiver, criterion = operands()
    original = episode(source, receiver)
    first = original.intervals[0]
    fields = {}
    if event in ("illegal", "ambiguous"):
        first = replace(first, native_step=replace(first.native_step, requested_action_code="disconnect-line-000",
            action_illegal=event == "illegal", action_ambiguous=event == "ambiguous"))
    elif event == "unrealized":
        first = replace(first, native_step=replace(first.native_step, realization_observed=False, realized_action_code=None))
    else:
        fields[{"forecasts": "forecast_available", "refusal": "supplier_refused", "fallback": "fallback_used"}[event]] = event != "forecasts"
    original = replace(original, intervals=(replace(first, **fields), *original.intervals[1:]))
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
    assert result.disposition is GridReliabilityDisposition.SATISFIED
    field = {"illegal": "illegal_action_intervals", "ambiguous": "ambiguous_action_intervals",
        "unrealized": "unrealized_action_intervals", "forecasts": "unavailable_forecast_intervals",
        "refusal": "supplier_refusal_intervals", "fallback": "fallback_intervals"}[event]
    assert getattr(result, field) == 1 and result.unserved_energy_mwh == D("0.05")
    assert independently_check_grid_reliability(source=source, receiver=receiver, requirement=criterion, episode=original, report=result)


def test_full_whole_chronic_denominator_keeps_missing_branches_and_all_failures():
    source, receiver, criterion = operands()
    episodes = (episode(source, receiver, branch="branch.hold"), episode(source, receiver, branch="branch.disconnect"),
        episode(source, receiver, unit=1, branch="branch.hold", termination=GridEpisodeTermination.PREMATURE_TERMINAL,
            deliveries=("0.9",)))
    result = assess_grid_reliability_panel(panel_id="panel.grid.literal", source=source, receiver=receiver, requirement=criterion,
        role=GridEpisodeRole.DEVELOPMENT, planned_unit_ids=tuple(row.chronic_id for row in source.chronic_bindings),
        branch_ids=("branch.disconnect", "branch.hold"), episodes=episodes)
    assert result.independent_unit_count == 2 and len(result.branches) == 4 and result.satisfied_unit_count == 1
    assert result.unit_dispositions == (("chronic.literal.1", GridReliabilityDisposition.SATISFIED),
        ("chronic.literal.2", GridReliabilityDisposition.FAILED))
    missing = result.branches[2]
    assert missing.episode is None and missing.expected_intervals == 3 and missing.disposition is GridReliabilityDisposition.UNEVALUABLE


@pytest.mark.parametrize("damage", ("duplicate", "new-unit", "role", "gap", "timestamp", "fresh-label", "late-selection"))
def test_no_duplicate_reset_branch_relabelled_unit_or_chronology_escape(damage):
    source, receiver, criterion = operands()
    original = episode(source, receiver)
    with pytest.raises(ValueError):
        if damage in ("duplicate", "role"):
            episodes = (original, original) if damage == "duplicate" else (replace(original,
                context=replace(original.context, role=GridEpisodeRole.REUSE)),)
            assess_grid_reliability_panel(panel_id="panel.grid.literal", source=source, receiver=receiver, requirement=criterion,
                role=GridEpisodeRole.DEVELOPMENT, planned_unit_ids=("chronic.literal.1",), branch_ids=("branch.hold",), episodes=episodes)
        elif damage == "new-unit":
            replace(original.context, unit_id="chronic.literal.new-seed")
        elif damage == "fresh-label":
            replace(original.context, evidence_scope="FRESH")
        elif damage == "late-selection":
            replace(original.context, selection_sequence=2)
        else:
            middle = original.intervals[1]
            step = replace(middle.native_step, horizon_step=3) if damage == "gap" else replace(middle.native_step, timestamp_utc="2026-01-01T00:11:00Z")
            original = replace(original, intervals=(original.intervals[0], replace(middle, native_step=step), original.intervals[2]))
            assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)


def test_missing_energy_cannot_be_replaced_by_reward_rho_or_topology_and_backend_is_unevaluable():
    source, receiver, criterion = operands()
    original = episode(source, receiver)
    original = replace(original, intervals=tuple(replace(row, demanded_energy_mwh=None, delivered_energy_mwh=None) for row in original.intervals))
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
    assert result.disposition is GridReliabilityDisposition.UNEVALUABLE and result.unserved_energy_mwh is None
    backend = episode(source, receiver, termination=GridEpisodeTermination.BACKEND_DIVERGENCE, deliveries=("1",))
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=backend)
    assert result.disposition is GridReliabilityDisposition.UNEVALUABLE


def test_observed_energy_failure_survives_a_later_missing_receiver():
    source, receiver, criterion = operands()
    original = episode(source, receiver, deliveries=("0.5", "1", "1"))
    original = replace(original, intervals=(*original.intervals[:2],
        replace(original.intervals[-1], demanded_energy_mwh=None, delivered_energy_mwh=None)))
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
    assert result.unserved_energy_mwh is None and result.unserved_energy_lower_bound_mwh == D("0.5")
    assert result.disposition is GridReliabilityDisposition.FAILED
    assert independently_check_grid_reliability(source=source, receiver=receiver, requirement=criterion,
        episode=original, report=result)


@pytest.mark.parametrize("termination", (GridEpisodeTermination.REFUSED, GridEpisodeTermination.MISSING_OBSERVATION,
    GridEpisodeTermination.NOT_ENTERED))
def test_explicit_unentered_or_refused_whole_unit_never_creates_empty_success(termination):
    source, receiver, criterion = operands()
    original = episode(source, receiver, termination=termination, deliveries=())
    original = replace(original, context=replace(original.context, first_observation_sequence=None))
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
    assert result.observed_intervals == 0 and result.expected_intervals == 3
    assert result.disposition is GridReliabilityDisposition.UNEVALUABLE and result.unserved_energy_mwh is None
    assert result.termination is termination and "LITERAL_ORIGINAL_STOP" in result.reason_codes


def test_identical_chronic_bytes_cannot_become_independent_by_another_label():
    source, receiver, criterion = operands()
    repeated = replace(source.chronic_bindings[1], content_sha256=source.chronic_bindings[0].content_sha256)
    source = replace(source, chronic_bindings=(source.chronic_bindings[0], repeated))
    source_id = ObjectIdentity.from_record(source.binding_id, source)
    receiver = replace(receiver, source_binding=source_id)
    criterion = replace(criterion, source_binding=source_id, receiver=receiver.identity)
    with pytest.raises(ValueError, match="identical original chronic bytes"):
        assess_grid_reliability_panel(panel_id="panel.grid.literal", source=source, receiver=receiver, requirement=criterion,
            role=GridEpisodeRole.DEVELOPMENT, planned_unit_ids=tuple(row.chronic_id for row in source.chronic_bindings),
            branch_ids=("branch.hold",), episodes=())


@pytest.mark.parametrize("damage", ("energy", "denominator", "event", "status"))
def test_independent_falsifier_detects_altered_report_without_calling_the_producer(damage, monkeypatch):
    source, receiver, criterion = operands()
    original = episode(source, receiver)
    result = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
    from empirical_lawhood.adapters.simulators.grid2op_response import reliability
    monkeypatch.setattr(reliability, "assess_grid_saved_episode", lambda **_: pytest.fail("implementation oracle called"))
    field, value = {"energy": ("delivered_energy_mwh", D(3)), "denominator": ("expected_intervals", 4),
        "event": ("fallback_intervals", 1), "status": ("disposition", GridReliabilityDisposition.FAILED)}[damage]
    with pytest.raises(ValueError, match="independent grid check"):
        independently_check_grid_reliability(source=source, receiver=receiver, requirement=criterion,
            episode=original, report=replace(result, **{field: value}))


class LiteralBytes:
    def __init__(self, members):
        self.members = members

    def open_member(self, name):
        raw = self.members[name]
        return (raw[start:start + 7] for start in range(0, len(raw), 7))


def dataset(original, receiver):
    raw = {}
    fields = {"demanded-energy-mwh": (1000, 1000, 1000), "delivered-energy-mwh": (950, 1000, 1000),
        "redispatch-magnitude-mwh": (125, 125, 125), "curtailed-energy-mwh": (10, 10, 10), "runtime-seconds": (1, 1, 1)}
    for name in VALUE_MEMBERS:
        raw[name] = struct.pack("<qqq", *fields[name])
        raw[name + ".valid"] = bytes((1, 1, 1))
    for name in EVENT_MEMBERS:
        raw[name] = bytes((1, 1, 1) if name == "forecast-available" else (0, 0, 0))
    refs = tuple(sorted((original.context.identity, original.context.source_binding, receiver.identity), key=lambda row: row.object_id))
    manifest = ArrayDatasetManifest("dataset.grid.literal", tuple(ArrayDatasetMember(name,
        "<i8" if name in VALUE_MEMBERS else "|u1", (3,), sha256(raw[name]).hexdigest()) for name in DATASET_MEMBERS), refs)
    selection = GridServiceDatasetSelection(original.context, manifest.identity, tuple(row.native_step for row in original.intervals), D(".001"), D(".001"))
    return raw, manifest, selection


def test_named_array_and_canonical_energy_use_the_same_complete_consumer_with_bounded_reads(monkeypatch):
    source, receiver, criterion = operands()
    original = episode(source, receiver)
    raw, manifest, selection = dataset(original, receiver)
    reader = ArrayDatasetReader(manifest, LiteralBytes(raw), maximum_chunk_bytes=16, maximum_slice_bytes=8)
    slices = []
    method = ArrayDatasetReader.read_array_slice
    def bounded(self, name, start, stop):
        slices.append(stop - start)
        return method(self, name, start, stop)
    monkeypatch.setattr(ArrayDatasetReader, "read_array_slice", bounded)
    result = assess_grid_service_dataset(reader, selection, source=source, receiver=receiver, requirement=criterion, block_rows=2000)
    expected = assess_grid_saved_episode(source=source, receiver=receiver, requirement=criterion, episode=original)
    assert result == expected and slices and max(slices) == 1


@pytest.mark.parametrize("damage", ("changed-bytes", "missing-member", "source-reference", "mask"))
def test_dataset_refuses_changed_values_omitted_members_detached_source_and_invalid_masks(damage):
    source, receiver, criterion = operands()
    original = episode(source, receiver)
    raw, manifest, selection = dataset(original, receiver)
    if damage == "changed-bytes":
        raw["delivered-energy-mwh"] = bytes(24)
    elif damage == "missing-member":
        manifest = replace(manifest, members=manifest.members[:-1])
        selection = replace(selection, dataset=manifest.identity)
    elif damage == "source-reference":
        manifest = replace(manifest, scientific_references=(receiver.identity,))
        selection = replace(selection, dataset=manifest.identity)
    else:
        raw["forecast-available"] = bytes((2, 1, 1))
        manifest = replace(manifest, members=tuple(replace(row, sha256=sha256(raw[row.name]).hexdigest()) for row in manifest.members))
        selection = replace(selection, dataset=manifest.identity)
    reader = ArrayDatasetReader(manifest, LiteralBytes(raw), maximum_chunk_bytes=16, maximum_slice_bytes=8)
    with pytest.raises(ValueError):
        assess_grid_service_dataset(reader, selection, source=source, receiver=receiver, requirement=criterion, block_rows=1)
