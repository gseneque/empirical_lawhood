# SPDX-License-Identifier: MPL-2.0
"""E2 retained-reader controls on disclosed sources, never qualification evidence."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest
from threadpoolctl import threadpool_limits

from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_acquisition as owner
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_bindings as bindings
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_records as r
from empirical_lawhood.adapters.methods.matrix_factor_response import native_utility_science as science
from empirical_lawhood.api import matrix_native_utility_read as reader
from empirical_lawhood.api.experiment_preparation import author_prepared_experiment
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.recursive_authoring import load_authored_wave
from empirical_lawhood.api.recursive_execution import _retained_plans, read_recursive_wave
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from tests.test_matrix_native_utility import copied_preparation, utility_case

ROOT = Path(__file__).parents[1]


class _Unreadable:
    def __getattribute__(self, name):
        raise AssertionError("deferred E2 read touched scientific custody: " + name)

    def __getitem__(self, key):
        raise AssertionError("deferred E2 read opened scientific payload: " + str(key))


def test_native_e2_root_read_refuses_a_foreign_source_index_before_opening_products(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex

    case = utility_case(tmp_path)
    manifest = case.request.source_manifest
    foreign = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification,
        provenances=(replace(manifest.provenances[0], observed_git_head="f" * 40),))
    original = case.request.canonical_bytes()
    def forbidden(*_args, **_kwargs):
        pytest.fail("foreign E2 source index opened a scientific product")
    monkeypatch.setattr(reader, "_record", forbidden)
    with pytest.raises(ValueError, match="shared scientific parents"):
        reader._root(case.specification, case.request, case.acquisition, case.specification.root_ids[0],
            {}, None, {}, "run.unread-foreign-source", source_index=foreign)
    assert case.request.canonical_bytes() == original


@pytest.mark.parametrize("partial,status,typed_validation", ((True, "SUCCEEDED", None),
    (True, "PARTIAL", None), (False, "REFUSED", None), (False, "SUCCEEDED", "DEFERRED")))
def test_partial_or_refused_native_e2_cannot_open_products_or_promote_unknowns(tmp_path, partial, status, typed_validation):
    case = utility_case(tmp_path)
    poison = _Unreadable()
    result = reader.read_development_result(directory=poison, artifact_writer=poison,
        specification=case.specification, instance=poison, payloads=poison,
        report={"status": status, "typed_product_validation": typed_validation},
        products=poison, draft=poison, plan=poison, allow_partial=partial)
    assert result["scientific_completion"] == "NOT_ESTABLISHED"
    assert result["state"] == "NATIVE_UTILITY_ASSESSMENT_DEFERRED"
    assert result["qualification"] == result["sampling_warrant"] == "NOT_ESTABLISHED"
    counts = result["denominators"]["native-utility"]
    assert counts["assigned_units"] == len(case.specification.root_ids)
    assert counts["usable_units"] is counts["successes"] is counts["adverse_units"] is None
    if typed_validation == "DEFERRED":
        assert result["reason_codes"] == ("COMPACT_CUSTODY_SCIENTIFIC_ASSESSMENT_DEFERRED",)


def test_native_e2_read_joins_exact_authored_request_and_complete_graph_without_compilation(tmp_path, monkeypatch):
    case = utility_case(tmp_path)
    preparation = copied_preparation(case, tmp_path / "copied")
    directory = Path(case.plane.root.contract.canonical_path) / "utility-authored"
    author_prepared_experiment(preparation=preparation, project_root=ROOT, artifact_writer=case.plane, output_dir=directory)
    _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=case.plane, lazy_payloads=True)
    _, plan, _ = _retained_plans(payloads, draft)
    raw = payloads["experiment-instance.json"]
    instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
    monkeypatch.setattr(owner, "lower", lambda *a, **kw: pytest.fail("retained E2 read compiled a new graph"))
    monkeypatch.setattr(bindings, "operation_declarations", lambda: pytest.fail("retained E2 read rediscovered operations"))
    assert reader._request(case.specification, instance, payloads) == case.request
    configs, tasks = reader._graph(case.specification, case.request, draft, plan)
    assert len(configs) == len(tasks) == 10
    with pytest.raises(PermissionError, match="graph/root/source census"):
        reader._graph(case.specification, case.request, replace(draft, links=draft.links[:-1]), plan)
    with pytest.raises(PermissionError, match="operation/configuration/resource"):
        first, *rest = draft.operations
        reader._graph(case.specification, case.request,
            replace(draft, operations=(replace(first, config_id="config.foreign"), *rest)), plan)
    name = "experiment-source-" + sha256(case.request.record_id.encode()).hexdigest() + ".json"
    with pytest.raises(PermissionError, match="original canonical request"):
        reader._request(case.specification, instance, {name: replace(case.request, record_id="request.foreign").canonical_bytes()})


@pytest.mark.native
def test_actual_public_native_e2_strict_read_replays_received_scores_and_recovery_without_contact(tmp_path, monkeypatch):
    from empirical_lawhood.runtime import recursive_compiler
    from tests.test_matrix_native_training_public_lifecycle import _actual_case
    with threadpool_limits(limits=1):
        case = utility_case(tmp_path, original=_actual_case(tmp_path, monkeypatch))
        preparation = copied_preparation(case, tmp_path / "utility-copied")
        directory = Path(case.plane.root.contract.canonical_path) / "native-e2-authored"
        author_prepared_experiment(preparation=preparation, project_root=ROOT, artifact_writer=case.plane, output_dir=directory)
        import empirical_lawhood.api.recursive_authoring as authoring_owner
        import empirical_lawhood.api.recursive_execution as execution_owner
        loads = []
        authenticated_load = authoring_owner.load_authored_wave
        def observed_load(**kwargs):
            loads.append(kwargs["directory"])
            return authenticated_load(**kwargs)
        monkeypatch.setattr(authoring_owner, "load_authored_wave", observed_load)
        monkeypatch.setattr(execution_owner, "load_authored_wave", observed_load)
        service = ExperimentProgrammeService(ROOT, case.plane, SimpleNamespace(maximum_parallel_tasks=4))
        run = service.run(directory=directory, maximum_parallel_tasks=4)
        assert run["status"] == "SUCCEEDED" and run["new_native_contact_count"] == 2
        # Entry authenticates once; the final read authenticates the new receipts
        # in a separate lifetime. Programme selection must not preload the packet.
        assert loads == [directory, directory]
        monkeypatch.setattr(bindings, "execute_parameter_native_work", lambda *a, **kw: pytest.fail("read acquired prefix"))
        monkeypatch.setattr(bindings, "execute_paired_response_native_work", lambda *a, **kw: pytest.fail("read acquired responses"))
        monkeypatch.setattr(science, "physical", lambda *a, **kw: pytest.fail("read recomputed physical eigensolve/forecast"))
        monkeypatch.setattr(recursive_compiler, "compile_recursive_wave", lambda *a, **kw: pytest.fail("read recompiled the graph"))
        monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *a, **kw: pytest.fail("read/recovery entered executor"))
        calls = {"score": 0, "summary": 0}
        assess_score, summarize = science.assess_score, science.summarize
        def assess(*args, **kwargs):
            calls["score"] += 1
            return assess_score(*args, **kwargs)
        def summary(*args, **kwargs):
            calls["summary"] += 1
            return summarize(*args, **kwargs)
        monkeypatch.setattr(science, "assess_score", assess)
        monkeypatch.setattr(science, "summarize", summary)
        public = service.read(directory=directory)
        result = public["scientific_result"]
        assert calls == {"score": 1, "summary": 1}
        assert result["scientific_completion"] == "COMPLETE_NATIVE_UTILITY_ASSESSMENT"
        assert result["scientific_status"] == "UNEVALUABLE"
        assert result["qualification"] == result["sampling_warrant"] == "NOT_ESTABLISHED"
        assert result["denominators"]["native-utility"]["assigned_units"] == 1
        assert result["terminal"]["value"]["object_schema"] == r.NativeUtilitySummary.SCHEMA
        assert len(result["outcomes"]) == 1
        assert set(result["outcomes"][0]["outcome"]["value"]) == {
            "object_id", "object_schema", "object_version", "object_fingerprint"}
        retained, products, draft, plan = read_recursive_wave(directory=directory, artifact_writer=case.plane, include_products=True)
        _, _, _, payloads = load_authored_wave(directory=directory, artifact_writer=case.plane, lazy_payloads=True)
        raw = payloads["experiment-instance.json"]
        instance = decode_canonical_bytes(raw, ExperimentInstanceBinding, maximum_bytes=len(raw))
        task = owner.task_id(case.specification.root_ids[0], "response-score")
        output = task + ".product"
        actual = products["records"][task][output]
        changed = dict(products)
        changed["records"] = {**products["records"], task: {**products["records"][task],
            output: replace(actual, unit_id="unit.foreign")}}
        with pytest.raises(PermissionError, match="canonical product bytes"):
            reader.read_development_result(directory=directory, artifact_writer=case.plane,
                specification=case.specification, instance=instance, payloads=payloads,
                report=retained, products=changed, draft=draft, plan=plan)
        prefix_task = owner.task_id(case.specification.root_ids[0], "prefix")
        prefix = products["records"][prefix_task][prefix_task + ".product"]
        forged_arrays = replace(prefix.arrays, array_artifact=replace(prefix.arrays.array_artifact, sha256="b" * 64))
        with pytest.raises(PermissionError, match="consumer.s actual receipted array descriptor"):
            reader._array(products, {value.task_id: value for value in plan.tasks}, prefix_task, forged_arrays)
        compact = service.read(directory=directory, allow_partial=True)
        assert compact["scientific_result"]["scientific_completion"] == "NOT_ESTABLISHED"
        before = len(loads)
        recovered = service.recover(directory=directory, maximum_parallel_tasks=4)
        assert loads[before:] == [directory, directory]
        assert recovered["status"] == "SUCCEEDED" and recovered["new_native_contact_count"] == 0
        assert recovered["scientific_result"]["scientific_completion"] == "COMPLETE_NATIVE_UTILITY_ASSESSMENT"
        marker = directory / "inquiry-admission.json"
        marker.write_bytes(b"{}")
        before = len(loads)
        try:
            with pytest.raises(ValueError, match="initial programme refuses an inquiry successor"):
                service.run(directory=directory, maximum_parallel_tasks=4)
            assert loads[before:] == [directory]
        finally:
            marker.unlink()
