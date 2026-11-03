# SPDX-License-Identifier: MPL-2.0
"""Exposed matrix architecture conformance; no fresh scientific qualification."""

from dataclasses import replace
from pathlib import Path
import os
import shutil

import pytest

from empirical_lawhood.adapters.methods.matrix_prospective import science
from empirical_lawhood.adapters.methods.matrix_prospective.example import example_source
from empirical_lawhood.adapters.methods.matrix_prospective.records import (
    BRANCHES, MatrixProgrammeRole, identity,
)
from empirical_lawhood.adapters.methods.matrix_prospective.recursive_translation import prospective_draft
from empirical_lawhood.api import matrix_numerical_provenance as provenance_owner
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.runtime.native_subwork import NativeSubworkState
from tests.test_recursive_public_service import _plane as _standard_plane

def _plane(root):
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    from empirical_lawhood.infrastructure.artifact_validation import ArtifactProfileValidatorRegistry

    plane = _standard_plane(root)
    plane.validators = ArtifactProfileValidatorRegistry(binary_codecs=MATRIX_STORAGE_CODECS)
    return plane


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def selected_source(monkeypatch):
    # Exposed conformance may run beside an editor. The release gate separately
    # binds the settled source. The native store still checks exact supplied
    # operand/code/lock identities; this fixture creates no qualification.
    observed = provenance_owner.capture_matrix_provenance(project_root=ROOT)
    source_binding = author.implementation_binding(ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **_kwargs: source_binding)
    monkeypatch.setattr(execution, "implementation_binding", lambda root, **_kwargs: source_binding)
    monkeypatch.setattr(provenance_owner, "capture_matrix_provenance", lambda **kwargs: observed)
    return example_source(), observed


def prepare(tmp_path, selected_source):
    source, provenance = selected_source
    plane = _plane(tmp_path / "selected")
    root = Path(plane.root.contract.canonical_path)
    source_path, provenance_path = root / "source.json", root / "provenance.json"
    source_path.write_bytes(source.canonical_bytes())
    provenance_path.write_bytes(provenance.canonical_bytes())
    bindings = [("external.matrix.provenance", provenance_path), ("external.matrix.source", source_path)]
    for branch in BRANCHES:
        path = root / (branch + "-stream.json")
        path.write_bytes(science.branch_contract(source, branch).stream.canonical_bytes())
        bindings.append(("external.matrix." + branch + "-stream", path))
    draft = prospective_draft(source, provenance)
    return plane, draft, tuple(bindings), root / "authored"


def contact_store(plane, plan):
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    return ExternalNativeEffectContactStore(plane=plane,
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan),
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)


def relocate_and_remove_producer(tmp_path, plane):
    original = Path(plane.root.contract.canonical_path)
    members = {p.relative_to(original): p.read_bytes() for p in original.rglob("*") if p.is_file()}
    relocated = _plane(tmp_path / "relocated")
    destination = Path(relocated.root.contract.canonical_path)
    shutil.copytree(original, destination, dirs_exist_ok=True)
    assert all((destination / name).read_bytes() == raw for name, raw in members.items())
    # The producing root is this test's disposable fixture, not historical data.
    shutil.rmtree(original)
    return relocated, members


def retain_selected_fixture(plane, name):
    selected = os.environ.get("EL_MATRIX_ACCEPTANCE_RETAIN")
    if selected:
        target = Path(selected) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plane.root.contract.canonical_path, target)


def test_installed_origin_commitment_branches_independent_negative_and_portable_recovery(
        tmp_path, monkeypatch, selected_source):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixIndependentAssessment

    plane, draft, bindings, directory = prepare(tmp_path, selected_source)
    authored = author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=bindings)
    assert authored["native_contact"] == "none" and authored["task_count"] == 4
    report = execution.run_recursive_wave(directory=directory, project_root=ROOT,
        artifact_writer=plane, terminal_product_format="compact")
    assert report["status"] == "SUCCEEDED", report
    assert report["new_native_contact_count"] == 2
    assert report["task_count"] == 4 and len(report["retained_product_index"]) == 7
    documents, products, _, plan = execution.read_recursive_wave(directory=directory,
        artifact_writer=plane, include_products=True)
    assessment = next(iter(products["records"]["matrix-prospective.assess"].values()))
    assert type(assessment) is MatrixIndependentAssessment
    assert tuple(row.branch_id for row in assessment.branches) == BRANCHES
    assert all(row.native_disposition is AssessmentDisposition.SATISFIED for row in assessment.branches)
    assert all(row.forecast_disposition is AssessmentDisposition.FALSIFIED for row in assessment.branches)
    assert all(row.native_reference_error < selected_source[0].protocol.native_reference_tolerance
               for row in assessment.branches)
    assert documents["qualification"] == "NOT_ESTABLISHED"

    contacts = contact_store(plane, plan)
    future_contact = contacts.read(report["run_id"], "matrix-prospective.futures")
    assert future_contact is not None
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts)
    definitions = tuple(store.iter_roster_definitions(future_contact))
    assert len(definitions) == 2
    assert tuple(store.inspect(d).state for d in definitions) == (NativeSubworkState.COMPLETED,) * 2
    for definition in definitions:
        retained = store.recover(definition)
        assert retained.completion.consumed_streams == definition.streams
        assert retained.completion.peak_rss_bytes > 0
        assert retained.completion.cost.cpu_seconds >= 0
        assert len(retained.outputs) == 1

    completions = tuple(store.recover(d).completion for d in definitions)
    relocated, members = relocate_and_remove_producer(tmp_path, plane)
    relocated_directory = Path(relocated.root.contract.canonical_path) / "authored"
    def forbidden(*args, **kwargs):
        raise AssertionError("completed matrix science was re-entered during recovery")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", forbidden)
    expected = {**report, "native_contact": "none", "new_native_contact_count": 0}
    assert execution.read_recursive_wave(directory=relocated_directory, artifact_writer=relocated,
        terminal_product_format="compact") == expected
    assert execution.run_recursive_wave(directory=relocated_directory, project_root=ROOT,
        artifact_writer=relocated, terminal_product_format="compact") == expected
    recovered_store = ExternalNativeSubworkStore(plane=relocated,
        parent_contacts=contact_store(relocated, plan))
    assert tuple(recovered_store.recover(d).completion for d in definitions) == completions
    root = Path(relocated.root.contract.canonical_path)
    assert all((root / name).read_bytes() == raw for name, raw in members.items())
    retain_selected_fixture(relocated, "complete")


def test_terminal_persistence_failure_recovers_all_native_receipts_after_relocation(
        tmp_path, monkeypatch, selected_source):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.infrastructure.recovery import ExternalRunRecoveryStore
    plane, draft, bindings, directory = prepare(tmp_path, selected_source)
    author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=bindings)
    original = ExternalRunRecoveryStore.record_terminal
    def interrupted(*args, **kwargs):
        raise OSError("exposed interruption before terminal persistence")
    monkeypatch.setattr(ExternalRunRecoveryStore, "record_terminal", interrupted)
    with pytest.raises(OSError, match="before terminal persistence"):
        execution.run_recursive_wave(directory=directory, project_root=ROOT,
            artifact_writer=plane, terminal_product_format="compact")
    partial = execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        terminal_product_format="compact", allow_partial=True)
    assert partial["status"] == "PARTIAL" and partial["task_count"] == 4
    assert len(partial["retained_product_index"]) == 7
    relocated, members = relocate_and_remove_producer(tmp_path, plane)
    monkeypatch.setattr(ExternalRunRecoveryStore, "record_terminal", original)
    def forbidden(*args, **kwargs):
        raise AssertionError("terminal repair re-entered a completed matrix task")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", forbidden)
    report = execution.run_recursive_wave(directory=Path(relocated.root.contract.canonical_path) / "authored",
        project_root=ROOT, artifact_writer=relocated, terminal_product_format="compact")
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    root = Path(relocated.root.contract.canonical_path)
    assert all((root / name).read_bytes() == raw for name, raw in members.items())
    retain_selected_fixture(relocated, "terminal-recovery")


def test_first_branch_receipt_and_unentered_second_branch_survive_failed_parent_without_replay(
        tmp_path, monkeypatch, selected_source):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.infrastructure.native_subwork import ExternalNativeSubworkStore
    plane, draft, bindings, directory = prepare(tmp_path, selected_source)
    author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=bindings)
    original = ExternalNativeSubworkStore.complete
    def interrupted(store, entry, **kwargs):
        result = original(store, entry, **kwargs)
        if entry.definition.subwork_id.endswith(".future-1"):
            raise OSError("exposed interruption after completed first branch receipt")
        return result
    monkeypatch.setattr(ExternalNativeSubworkStore, "complete", interrupted)
    with pytest.raises((ValueError, RuntimeError, OSError)):
        execution.run_recursive_wave(directory=directory, project_root=ROOT,
            artifact_writer=plane, terminal_product_format="compact")
    partial, _, _, plan = execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        terminal_product_format="compact", allow_partial=True, include_products=True)
    assert partial["status"] == "PARTIAL" and partial["task_count"] == 4
    contacts = contact_store(plane, plan)
    future = contacts.read(partial["run_id"], "matrix-prospective.futures")
    store = ExternalNativeSubworkStore(plane=plane, parent_contacts=contacts)
    definitions = tuple(store.iter_roster_definitions(future))
    assert len(definitions) == 2
    assert tuple(store.inspect(d).state for d in definitions) == (
        NativeSubworkState.COMPLETED, NativeSubworkState.NOT_ENTERED)
    first = store.recover(definitions[0])
    assert first.completion.consumed_streams == definitions[0].streams
    assert len(first.outputs) == 1
    relocated, members = relocate_and_remove_producer(tmp_path, plane)
    reader = ExternalNativeSubworkStore(plane=relocated, parent_contacts=contact_store(relocated, plan))
    assert reader.recover(definitions[0]).completion == first.completion
    assert reader.inspect(definitions[1]).state is NativeSubworkState.NOT_ENTERED
    monkeypatch.setattr(ExternalNativeSubworkStore, "complete", original)
    def forbidden(*args, **kwargs):
        raise AssertionError("uncertain parent caused completed or unentered branch replay")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", forbidden)
    with pytest.raises((ValueError, RuntimeError)):
        execution.run_recursive_wave(directory=Path(relocated.root.contract.canonical_path) / "authored",
            project_root=ROOT, artifact_writer=relocated, terminal_product_format="compact")
    root = Path(relocated.root.contract.canonical_path)
    assert all((root / name).read_bytes() == raw for name, raw in members.items())
    retain_selected_fixture(relocated, "partial-branch")


@pytest.mark.parametrize("defect", ("future-leak", "role", "commitment", "model", "root"))
def test_invalid_causal_wave_refuses_before_publication_or_native_entry(tmp_path, selected_source, defect):
    plane, draft, bindings, directory = prepare(tmp_path, selected_source)
    if defect in {"future-leak", "role", "commitment"}:
        edge = next(link for link in draft.links if link.consumer_node_id == "matrix-prospective.forecast")
        if defect == "role":
            edge = replace(edge, scientific_role="OUTCOME")
        elif defect == "future-leak":
            edge = replace(edge, producer_node_id="matrix-prospective.futures")
        else:
            edge = replace(edge, producer_output_id="missing")
        draft = replace(draft, links=tuple(edge if link.edge_id == edge.edge_id else link for link in draft.links))
    elif defect == "model":
        root = replace(draft.development_study, system=replace(draft.development_study.system,
                                                             object_fingerprint="f" * 64))
        draft = replace(draft, development_study=root)
    else:
        draft = replace(draft, development_study=replace(draft.development_study,
                                                       assigned_unit_ids=("independent.unrelated",)))
    with pytest.raises((ValueError, RuntimeError)):
        author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
            output_dir=directory, input_bindings=bindings)
    assert not directory.exists()
    assert not (Path(plane.root.contract.canonical_path) / "runs").exists()


def test_future_seed_changes_do_not_change_prefix_only_prediction_values():
    source = example_source()
    native_root = source.allocation.streams.roots[0]
    seeds = tuple(replace(seed, seed=seed.seed + 901) if seed.purpose_id in BRANCHES else seed
                  for seed in native_root.scientific_seeds)
    streams = replace(source.allocation.streams, roots=(replace(native_root, scientific_seeds=seeds),))
    changed = replace(source, protocol=replace(source.protocol, allocation=streams.identity),
                      allocation=replace(source.allocation, streams=streams))
    # Metadata correctly retains the changed allocation/source identity. Only
    # the prediction values are invariant; canonical identities are not reused.
    forecasts = []
    for selected in (source, changed):
        arrays = science.prefix(selected)
        _, origin = science.origin_record(selected, arrays, artifact_id="array.exposed.prefix")
        raw, record = science.forecast(origin, arrays, artifact_id="array.exposed.forecast")
        record.validate_origin(origin)
        forecasts.append((raw, record))
    # NPZ bytes contain only the complete numerical arrays and are deterministic.
    assert forecasts[0][0] == forecasts[1][0]
    assert identity(forecasts[0][1]) != identity(forecasts[1][1])


@pytest.mark.parametrize("defect", ("role", "calibration", "calibration-phase", "calibration-coordinate",
                                  "calibration-clock", "preparation", "rng", "horizon-package"))
def test_protocol_refuses_role_scope_and_numerical_substitution(defect):
    protocol = example_source().protocol
    with pytest.raises(ValueError):
        if defect == "role":
            replace(protocol, root=replace(protocol.root, role=MatrixProgrammeRole.CONFIRMATION))
        elif defect == "calibration":
            replace(protocol, calibration_scope=replace(protocol.calibration_scope,
                                                       root_ids=protocol.preparation_scope.root_ids))
        elif defect.startswith("calibration-"):
            from decimal import Decimal
            from empirical_lawhood.kernel.time import CausalPhase
            cutoff = protocol.calibration_scope.information_cutoff
            changes = {"calibration-phase": {"phase": CausalPhase.POST_OUTCOME},
                       "calibration-coordinate": {"coordinate": Decimal(100)},
                       "calibration-clock": {"clock_id": protocol.root.clock_id}}[defect]
            replace(protocol, calibration_scope=replace(protocol.calibration_scope,
                                                       information_cutoff=replace(cutoff, **changes)))
        elif defect == "preparation":
            replace(protocol, preparation_scope=replace(protocol.preparation_scope,
                                                        numerical_view=replace(protocol.preparation_scope.numerical_view,
                                                                               object_fingerprint="e" * 64)))
        elif defect == "rng":
            replace(protocol, view=replace(protocol.view, rng_algorithm="unsupported"))
        else:
            replace(protocol, horizon_steps=10**9)


def test_independent_assessment_detects_native_error_and_withholds_forecast_admission(monkeypatch):
    source = example_source()
    prefix = science.prefix(source)
    _, origin = science.origin_record(source, prefix, artifact_id="array.prefix")
    raw, forecast = science.forecast(origin, prefix, artifact_id="array.forecast")
    del raw
    predicted = {branch: prefix["positions"][-1] + float(source.protocol.view.timestep *
                 source.protocol.horizon_steps) * prefix["momenta"][-1] for branch in BRANCHES}
    branches = {b: science.native_branch(source, origin, prefix, science.branch_contract(source, b)) for b in BRANCHES}
    branches[BRANCHES[0]]["positions"][-1, 0, 0, 0, 0] += 0.01
    _, native = science.futures(source, origin, forecast, branches, artifact_id="array.future")
    arrays = {f"{b}.{name}": value for b in BRANCHES for name, value in branches[b].items()}
    def forbidden(*args, **kwargs):
        raise AssertionError("the independent assessor invoked the native producer")
    monkeypatch.setattr(science, "native_branch", forbidden)
    assessment = science.assess(source, origin, forecast, native, prefix, predicted, arrays)
    assert assessment.branches[0].native_disposition is AssessmentDisposition.FALSIFIED
    assert assessment.branches[0].forecast_disposition is AssessmentDisposition.UNEVALUABLE
    assert len(assessment.branches) == len(BRANCHES)


@pytest.mark.parametrize("damage", ("exact", "late-member"))
def test_scoped_reader_preserves_real_prospective_assessment_and_complete_refusal(tmp_path, monkeypatch, damage):
    from contextlib import ExitStack
    from hashlib import sha256
    import json
    import tracemalloc
    from empirical_lawhood.adapters.methods.matrix_prospective.operation_bindings import _consume_array
    from empirical_lawhood.infrastructure import matrix_array_io
    from tests.test_matrix_dataset_readers import real_port

    original = example_source()
    protocol = replace(original.protocol, horizon_steps=128,
        calibration_scope=replace(original.protocol.calibration_scope, horizon_steps=128),
        preparation_scope=replace(original.protocol.preparation_scope, horizon_steps=128))
    source = replace(original, protocol=protocol)
    prefix = science.prefix(source)
    prefix_raw, origin = science.origin_record(source, prefix, artifact_id="array.reader.prefix")
    forecast_raw, forecast = science.forecast(origin, prefix, artifact_id="array.reader.forecast")
    predicted = matrix_array_io.decode_matrix_arrays(forecast_raw, forecast.arrays)
    branches = {branch: science.native_branch(source, origin, prefix, science.branch_contract(source, branch)) for branch in BRANCHES}
    future_raw, native = science.futures(source, origin, forecast, branches, artifact_id="array.reader.future")
    future = {f"{branch}.{name}": value for branch in BRANCHES for name, value in branches[branch].items()}
    expected = science.assess(source, origin, forecast, native, prefix, predicted, future)
    selected = native.arrays
    if damage == "late-member":
        selected = replace(selected, members=(*selected.members[:-1], replace(selected.members[-1], sha256="b" * 64)))
    monkeypatch.setattr(matrix_array_io, "decode_matrix_arrays", lambda *a, **k: pytest.fail("reader decoded a complete population"))
    with ExitStack() as stack:
        ports = {}
        for saved, raw in ((origin.arrays, prefix_raw), (forecast.arrays, forecast_raw), (selected, future_raw)):
            port = real_port(saved.array_artifact, raw)
            stack.callback(port.close)
            ports[port.artifact_id] = port
        tracemalloc.start()
        try:
            with ExitStack() as readers:
                past = readers.enter_context(_consume_array(ports, origin.arrays, origin.arrays.producers, protocol))
                prediction = readers.enter_context(_consume_array(ports, forecast.arrays, forecast.arrays.producers, protocol))
                if damage == "late-member":
                    with pytest.raises(ValueError, match="hash"):
                        readers.enter_context(_consume_array(ports, selected, selected.producers, protocol))
                    return
                values = readers.enter_context(_consume_array(ports, selected, selected.producers, protocol))
                assert not isinstance(values, dict)
                actual = science.assess(source, origin, forecast, native, past, prediction, values)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert actual.canonical_bytes() == expected.canonical_bytes()
        assert len(actual.branches) == len(BRANCHES)
        assert all(port.bytes_read == 0 for port in ports.values())
        report = {"standing": "EXPOSED_SOFTWARE_CONFORMANCE_NONPROMOTABLE",
            "horizon_steps": protocol.horizon_steps, "complete_branches": len(BRANCHES),
            "future_value_bytes": sum(member.size_bytes for member in native.arrays.members),
            "assessment_sha256": sha256(actual.canonical_bytes()).hexdigest(),
            "traced_peak_bytes": peak,
            "memory_scope": "reader admission, complete unchanged scientific assessment and final seals; excludes fixture preparation, kernel FD cache and untracked RSS",
            "source": identity(source).object_fingerprint,
            "original_artifact_sha256": [saved.array_artifact.sha256 for saved in (origin.arrays, forecast.arrays, native.arrays)]}
        (tmp_path / "prospective-dataset-assessment.json").write_text(json.dumps(report, indent=2) + "\n")
