# SPDX-License-Identifier: MPL-2.0
"""Report projections of real registered PURE custody; no native acquisition."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.analytic_material_inquiry import science
from empirical_lawhood.adapters.methods.analytic_material_inquiry.recursive_translation import supply_draft
from empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart import UniformElectronGasAnalyticReferenceConfig
from empirical_lawhood.api import numerical_provenance as provenance_owner
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api import recursive_inquiry as inquiry
from empirical_lawhood.infrastructure.execution import LocalExecutionResourceAdmitter, LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_inquiry import InquirySuccessorIntent, identity
from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
from empirical_lawhood.runtime.recursive_inquiry import InquirySuccessorAdmission
from tests.test_recursive_inquiry import episode as episode
from tests.test_recursive_public_service import _plane
from tests.runtime_platform.test_native_effect_facts import selected as selected

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mode", ("raw-success", "raw-failed", "unknown-sibling"))
def test_public_report_serializes_primary_native_facts_beside_unchanged_history(wave, selected, monkeypatch, mode):
    """Report seam only: genuine literal facts, not native-wave acceptance.

    The PURE public wave supplies authentic ordinary read/report plumbing.
    This explicit owner seam adds a separately labelled literal UNKNOWN row
    and a real inspected native census; it asserts no native lineage for that
    PURE wave and creates no invocation or scientific completion facts.
    """
    from empirical_lawhood.infrastructure import recursive_custody
    from empirical_lawhood.infrastructure.native_parent_finalization import inspect_native_parent_return
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from empirical_lawhood.runtime.execution import TaskBlockReason
    from empirical_lawhood.runtime.native_subwork import invoke_native_subwork
    from tests.runtime_platform.test_native_effect_facts import _snapshot

    store, definitions, _bundle, _context, contract = selected
    entry = store.begin(definitions[0]); store.contact(entry)
    def literal_call():
        if mode == "raw-failed":
            raise ValueError("disclosed literal raw-call error")
        return b"disclosed literal raw return"
    if mode == "raw-failed":
        with pytest.raises(ValueError, match="literal raw-call error"):
            invoke_native_subwork(store, entry, literal_call)
    else:
        invoke_native_subwork(store, entry, literal_call)
    if mode == "unknown-sibling":
        unknown = store.begin(definitions[1]); store.contact(unknown)
    observation = inspect_native_parent_return(store=store, work=contract.native_work)
    parent = observation.work.expected_parent
    recorded = {"task_id": parent.task_id, "attempt_id": parent.attempt_id, "ordinal": 1,
        "operational_status": "BLOCKED", "reason_code": TaskBlockReason.UNKNOWN_COMPLETION.value}
    original_history = canonical_json_bytes(recorded)
    before = _snapshot(store)
    actual = recursive_custody.read_recursive_products
    def products(**arguments):
        retained = actual(**arguments)
        retained["operational_census"] = (recorded,)
        retained["native_observations"] = {parent.attempt_id: observation}
        return retained
    monkeypatch.setattr(recursive_custody, "read_recursive_products", products)
    report, retained, _, _ = execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
        include_products=True, terminal_product_format="compact")
    current, = report["current_native_facts"]
    assert (current["task_id"], current["attempt_id"]) == (parent.task_id, parent.attempt_id)
    for field in ("uncertain_contact_definition_ids", "pending_publication_definition_ids",
            "uncontacted_definition_ids", "failed_return_definition_ids"):
        assert current[field] == tuple(pin.to_document() for pin in getattr(observation, field))
    assert current["native_returns"] == tuple({"definition": row.definition.identity.to_document(),
        "native_return_status": None if row.native_return_status is None else row.native_return_status.value}
        for row in observation.inspections)
    assert report["operational_census"] == (recorded,) and canonical_json_bytes(recorded) == original_history
    assert retained["native_observations"][parent.attempt_id] is observation
    assert report["native_observation_unavailable"] == () and _snapshot(store) == before
    assert report["new_native_contact_count"] == 0 and report["qualification"] == "NOT_ESTABLISHED"
    assert report["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"


@pytest.fixture(scope="module")
def wave(tmp_path_factory, request):
    selected = tmp_path_factory.mktemp("product-report") / "selected"
    plane = _plane(selected)
    source = decode_canonical_bytes((ROOT / "programmes/materials/superconductivity/workflows/electron-gas-response/config.json").read_bytes(),
                                   UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
    draft = supply_draft(source, draft_id="draft.report-projection.pure")
    if getattr(request, 'param', None) is not None:
        draft = replace(draft, operations=tuple(replace(operation, maximum_attempts=request.param)
            for operation in draft.operations))
    origins = RecursiveInputOrigins(tuple(RecursiveInputOrigin(value.input_id, RecursiveInputOriginKind.SOURCE,
        value.expected_content_sha256, value.scientific_role) for value in draft.external_inputs))
    source_path = selected / "selected-source.json"
    source_path.write_bytes(source.canonical_bytes())
    directory = selected / "authored"
    # Snapshot the actual producing commitments once for this software fixture;
    # concurrent source editing is separately tested by source-substitution tests.
    producing_source = author.implementation_binding(ROOT)
    observed = provenance_owner.capture_numerical_provenance(project_root=ROOT)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(author, "implementation_binding", lambda root, **_kwargs: producing_source)
        patch.setattr(execution, "implementation_binding", lambda root, **_kwargs: producing_source)
        patch.setattr(provenance_owner, "capture_numerical_provenance", lambda **kwargs: observed)
        author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=directory,
            input_bindings=((draft.external_inputs[0].input_id, source_path),), origins=origins)
        initial = execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane,
                                               terminal_product_format="references")
        assert initial["status"] == "SUCCEEDED" and initial["new_native_contact_count"] == 0
        def forbidden(*args, **kwargs):
            raise AssertionError("retained PURE operation was executed again")
        executor_execute = LocalProcessExecutor.execute
        patch.setattr(LocalProcessExecutor, "execute", forbidden)
        yield SimpleNamespace(directory=directory, plane=plane, report=initial, origins=origins, source=source,
                              executor_execute=executor_execute)


def test_real_pure_documents_default_and_references_have_identical_authenticated_products(wave):
    options = dict(directory=wave.directory, artifact_writer=wave.plane, include_products=True)
    documents, full, draft, plan = execution.read_recursive_wave(**options)
    explicit = execution.read_recursive_wave(**options, terminal_product_format="documents")
    references, referenced_full, referenced_draft, referenced_plan = execution.read_recursive_wave(
        **options, terminal_product_format="references")
    assert explicit == (documents, full, draft, plan)
    assert (referenced_full, referenced_draft, referenced_plan) == (full, draft, plan)
    assert "terminal_product_format" not in documents
    assert references["terminal_product_format"] == "references"
    assert {k: v for k, v in references.items() if k not in ("terminal_product_format", "terminal_products")} == {
        k: v for k, v in documents.items() if k != "terminal_products"}
    assert references == wave.report
    assert len(full["attempt_receipts"]) == len(plan.tasks) == 1
    assert {row["operational_status"] for row in references["operational_census"]} == {"SUCCEEDED"}
    entries = {(row["task_id"], row["output_id"]): row for row in references["retained_product_index"]}
    assert set(entries) == {(task, output) for task, records in full["records"].items() for output in records}
    assert {task: set(records) for task, records in references["terminal_products"].items()} == {
        task: set(records) for task, records in documents["terminal_products"].items()}
    for task, records in references["terminal_products"].items():
        for output, reference in records.items():
            record = full["records"][task][output]
            receipt = full["receipts"][task]
            assert reference == entries[task, output]
            assert reference["schema"] == record.SCHEMA
            assert reference["sha256"] == record.fingerprint()
            assert reference["producing_receipt"] == identity(receipt, receipt.receipt_id).to_document()
            raw = wave.plane.root.resolve(reference["relative_path"], for_write=False).read_bytes()
            assert len(raw) == reference["size_bytes"] and raw == record.canonical_bytes()
            assert documents["terminal_products"][task][output] == record.to_document()
    assert execution.run_recursive_wave(directory=wave.directory, project_root=ROOT, artifact_writer=wave.plane,
                                       terminal_product_format="references") == references
    assert execution.run_recursive_wave(directory=wave.directory, project_root=ROOT, artifact_writer=wave.plane) == documents


def test_reference_projection_keeps_internal_products_and_only_projects_terminal_outputs(wave, monkeypatch):
    from empirical_lawhood.adapters.methods.rubisco_historical.recursive_translation import historical_recursive_draft
    from tests.test_rubisco_historical_recursive import _inputs

    model, slices = _inputs()
    bindings = []
    root = wave.directory.parent
    for record in slices:
        path = root / (record.slice_id + ".json")
        path.write_bytes(record.canonical_bytes())
        bindings.append(("external." + record.slice_id, path))
    directory = root / "history"
    author.author_recursive_wave(draft=historical_recursive_draft(model, slices), project_root=ROOT,
        artifact_writer=wave.plane, output_dir=directory, input_bindings=tuple(bindings))
    monkeypatch.setattr(LocalProcessExecutor, "execute", wave.executor_execute)
    report = execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=wave.plane,
                                         terminal_product_format="references")
    documents, full, _, plan = execution.read_recursive_wave(directory=directory, artifact_writer=wave.plane,
                                                            include_products=True)
    references, referenced_full, _, _ = execution.read_recursive_wave(directory=directory, artifact_writer=wave.plane,
        include_products=True, terminal_product_format="references")
    assert report == references and referenced_full == full
    assert len(plan.tasks) == len(report["operational_census"]) == len(full["attempt_receipts"]) == 6
    assert report["new_native_contact_count"] == 0 and report["status"] == "SUCCEEDED"
    terminal_ids = {task.task_id for task in plan.tasks} - {
        dependency for task in plan.tasks for dependency in task.dependency_task_ids}
    assert set(report["terminal_products"]) == set(documents["terminal_products"]) == terminal_ids
    assert set(full["records"]) > terminal_ids
    index = {(row["task_id"], row["output_id"]): row for row in report["retained_product_index"]}
    assert set(index) == {(task, output) for task, records in full["records"].items() for output in records}
    for task, records in report["terminal_products"].items():
        for output, reference in records.items():
            assert reference == index[task, output]
            assert documents["terminal_products"][task][output] == full["records"][task][output].to_document()


def test_compact_streams_exact_custody_and_defers_scientific_projection(wave, monkeypatch):
    from empirical_lawhood.infrastructure import recursive_custody
    from empirical_lawhood.api.recursive_operations import operation_catalog

    documents, full, _, _ = execution.read_recursive_wave(
        directory=wave.directory, artifact_writer=wave.plane, include_products=True)

    scientific_kinds = {type(record) for values in full["records"].values() for record in values.values()}
    decode = recursive_custody.decode_canonical_bytes
    def forbid_scientific_product(raw, kind, **kwargs):
        if kind in scientific_kinds:
            raise AssertionError("compact custody decoded a scientific product")
        return decode(raw, kind, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(recursive_custody, "decode_canonical_bytes", forbid_scientific_product)
        compact, products, _, _ = execution.read_recursive_wave(
            directory=wave.directory, artifact_writer=wave.plane, include_products=True,
            terminal_product_format="compact")
    assert compact["retained_product_index"] == wave.report["retained_product_index"]
    assert compact["terminal_products"] == wave.report["terminal_products"]
    assert compact["task_census"] == documents["task_census"]
    assert compact["operational_census"] == documents["operational_census"]
    assert compact["connection_assessments"] == ()
    assert compact["connection_assessment_projection"] == "NOT_DECODED"
    assert compact["typed_product_validation"] == "DEFERRED"
    assert all(not values for values in products["records"].values())
    _, _, codecs = operation_catalog()
    retyped = {}
    for task_id, output_id, record in recursive_custody.iter_recursive_product_records(
            plane=wave.plane, products=products, output_codecs=codecs):
        retyped.setdefault(task_id, {})[output_id] = record
    assert retyped == full["records"]


def test_lazy_authored_members_preserve_exact_eager_inputs(wave):
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads

    eager = author.load_authored_wave(directory=wave.directory, artifact_writer=wave.plane)
    lazy = author.load_authored_wave(directory=wave.directory, artifact_writer=wave.plane, lazy_payloads=True)
    assert lazy[:3] == eager[:3]
    assert isinstance(lazy[3], AuthenticatedRecursivePayloads)
    assert dict(lazy[3]) == eager[3]


def test_compact_execution_streams_external_operands_without_whole_payload_reads(wave, monkeypatch):
    from empirical_lawhood.infrastructure.recursive_custody import AuthenticatedRecursivePayloads

    draft = supply_draft(wave.source, draft_id="draft.report-projection.streamed-input")
    origins = RecursiveInputOrigins(tuple(RecursiveInputOrigin(value.input_id, RecursiveInputOriginKind.SOURCE,
        value.expected_content_sha256, value.scientific_role) for value in draft.external_inputs))
    directory = wave.directory.parent / "streamed-input"
    author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=wave.plane,
        output_dir=directory, input_bindings=((draft.external_inputs[0].input_id,
            wave.directory.parent / "selected-source.json"),), origins=origins)
    original_getitem, original_chunks = AuthenticatedRecursivePayloads.__getitem__, AuthenticatedRecursivePayloads.chunks
    streamed = []

    def forbid_operand_bytes(self, name):
        if name.startswith("external-"):
            pytest.fail("compact execution allocated a whole authored scientific operand")
        return original_getitem(self, name)

    def observed_chunks(self, name, **kwargs):
        streamed.append(name)
        yield from original_chunks(self, name, **kwargs)

    monkeypatch.setattr(AuthenticatedRecursivePayloads, "__getitem__", forbid_operand_bytes)
    monkeypatch.setattr(AuthenticatedRecursivePayloads, "chunks", observed_chunks)
    monkeypatch.setattr(LocalProcessExecutor, "execute", wave.executor_execute)
    report = execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=wave.plane,
        terminal_product_format="compact")
    assert report["status"] == "SUCCEEDED" and report["new_native_contact_count"] == 0
    assert report["typed_product_validation"] == "DEFERRED"
    assert len(streamed) == 2 and sum(name.startswith("external-") for name in streamed) == 1
    assert len(report["task_census"]) == len(report["operational_census"]) == 1


@pytest.mark.parametrize("allow_unexecuted", (False, True))
def test_partial_custody_recovers_completed_receipts_and_keeps_missing_tasks_explicit(wave, allow_unexecuted):
    _, products, draft, _ = execution.read_recursive_wave(
        directory=wave.directory, artifact_writer=wave.plane, include_products=True)
    _, _, _, payloads = author.load_authored_wave(directory=wave.directory, artifact_writer=wave.plane)
    _, _, index = execution._retained_plans(payloads, draft)
    terminal = wave.plane.root.resolve(index.terminal_event_relative_path, for_write=False)
    saved = {}

    def remove(relative):
        path = wave.plane.root.resolve(relative, for_write=False)
        for member in (path, path.with_name(path.name + ".manifest.json")):
            saved[member] = member.read_bytes()
            member.unlink()

    try:
        remove(index.terminal_event_relative_path)
        with pytest.raises(ValueError, match="complete operational terminal"):
            execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
                allow_unexecuted=allow_unexecuted)
        partial = execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
            terminal_product_format="compact", allow_partial=True, allow_unexecuted=allow_unexecuted)
        assert partial["status"] == "PARTIAL" and partial["operational_terminal"] == "ABSENT"
        assert partial["retained_product_index"] == wave.report["retained_product_index"]
        assert len(partial["task_census"]) == partial["task_count"]
        task, receipt = next(iter(products["receipts"].items()))
        candidate = next(row for row in index.task(task).attempts if row.attempt_id == receipt.attempt_id)
        remove(f"runs/{index.run_id}/receipts/{task}/{receipt.attempt_id}.json")
        remove(candidate.event_relative_path)
        unknown = execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
            terminal_product_format="compact", allow_partial=True, allow_unexecuted=allow_unexecuted)
        assert unknown["task_census"] == [{"task_id": task,
            "operational_status": "NO_COMPLETION_RECEIPT", "reason_code": "ENTRY_OR_PROCESS_STATE_NOT_INFERRED"}]
        assert not unknown["retained_product_index"]
        assert wave.plane.root.resolve(wave.report["retained_product_index"][0]["relative_path"],
                                      for_write=False).is_file()
    finally:
        for path, raw in saved.items():
            path.write_bytes(raw)
    assert terminal.is_file()
    assert execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
        terminal_product_format="references") == wave.report


@pytest.mark.parametrize("mode", ["documents", "references", "compact"])
@pytest.mark.parametrize("damage", ["missing-receipt", "tampered-receipt", "tampered-data"])
def test_reference_projection_cannot_bypass_receipt_or_data_authentication(wave, mode, damage):
    _, products, _, _ = execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
                                                       include_products=True)
    task, receipt = next(iter(products["receipts"].items()))
    if damage == "tampered-data":
        relative = wave.report["retained_product_index"][0]["relative_path"]
    else:
        relative = f"runs/{wave.report['run_id']}/receipts/{task}/{receipt.attempt_id}.json"
    path = wave.plane.root.resolve(relative, for_write=False)
    before = path.read_bytes()
    try:
        if damage == "missing-receipt":
            path.unlink()
        else:
            path.write_bytes(b"{}")
        with pytest.raises((ValueError, RuntimeError, OSError)):
            execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
                                          terminal_product_format=mode)
    finally:
        path.write_bytes(before)
    assert execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
                                          terminal_product_format="references") == wave.report


@pytest.mark.parametrize("mode", ["summary", "", None, [], {}])
def test_invalid_report_format_refuses_before_custody_or_execution(monkeypatch, mode):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid format accessed custody or execution")
    monkeypatch.setattr(execution, "load_authored_wave", forbidden)
    monkeypatch.setattr(inquiry, "_read", forbidden)
    with pytest.raises(ValueError, match="terminal_product_format"):
        execution.read_recursive_wave(directory=None, artifact_writer=None, terminal_product_format=mode)
    with pytest.raises(ValueError, match="terminal_product_format"):
        execution.run_recursive_wave(directory=None, project_root=None, artifact_writer=None, terminal_product_format=mode)
    with pytest.raises(ValueError, match="terminal_product_format"):
        inquiry.run_inquiry_successor(directory=None, project_root=None, artifact_writer=None, terminal_product_format=mode)


@pytest.mark.parametrize('workers,explicit_capacity',((1,False),(2,False),(2,True)))
def test_successor_propagates_report_format_after_existing_exact_intent_join(wave, monkeypatch, episode,
                                                                          workers, explicit_capacity):
    # This wiring test substitutes only the persisted decision reader. The wave,
    # configuration, origin record and full runner/read path remain actual custody.
    packet, draft, source, _ = author.load_authored_wave(directory=wave.directory, artifact_writer=wave.plane)
    operation = draft.operations[0]
    key = identity(packet, packet.packet_id)
    intent = InquirySuccessorIntent("intent.report-projection", key, key, key, key, key, "act-a",
        identity(draft, draft.draft_id), operation.config_identity, identity(wave.origins, "inquiry-input-origins"),
        science.scope(wave.source),
        operation.selection.selection_id)
    admission = InquirySuccessorAdmission("decision-fixture", key, identity(intent, intent.intent_id), key)
    from empirical_lawhood.planning.recursive_inquiry import choose_inquiry

    selected = replace(episode["menu"].alternatives[0], successor_draft=intent.draft,
        successor_config=intent.configuration, input_origins=intent.input_origins,
        capability_id=intent.capability_id)
    operands = dict(episode, menu=replace(episode["menu"],
        alternatives=(selected, *episode["menu"].alternatives[1:])))
    decision = choose_inquiry(**operands)
    records = {"intent.json": intent, "implementation.json": source,
        "decision.json": decision, "menu.json": operands["menu"],
        "state.json": operands["state"], "policy.json": operands["policy"],
        "specification.json": operands["specification"]}
    monkeypatch.setattr(inquiry, "_read", lambda *args: admission)
    monkeypatch.setattr(inquiry, "read_inquiry_decision", lambda **kwargs: (packet, records))
    capacity = LocalExecutionResourceAdmitter.detect_capacity() if explicit_capacity else None
    calls = []
    def selected(**kwargs):
        calls.append(kwargs)
        return execution.run_recursive_wave(**kwargs)
    monkeypatch.setattr(inquiry,'run_recursive_wave',selected)
    assert inquiry.run_inquiry_successor(directory=wave.directory, project_root=ROOT, artifact_writer=wave.plane,
        terminal_product_format="references",maximum_parallel_tasks=workers,
        parallel_resource_capacity=capacity) == wave.report
    assert calls == [{'directory':wave.directory,'project_root':ROOT,'artifact_writer':wave.plane,
        'terminal_product_format':'references','maximum_parallel_tasks':workers,
        'parallel_resource_capacity':capacity}]
    assert calls[0]['parallel_resource_capacity'] is capacity
    records["policy.json"] = replace(operands["policy"], max_operations=0)
    with pytest.raises(ValueError, match="finite operation allowance"):
        inquiry.run_inquiry_successor(directory=wave.directory, project_root=ROOT, artifact_writer=wave.plane,
                                      terminal_product_format="references")
    assert len(calls) == 1


@pytest.mark.parametrize("automatic", (False, True))
def test_author_only_partial_read_preserves_pending_census_without_execution_publication(tmp_path, monkeypatch, automatic):
    from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
    plane = _plane(tmp_path / "author-only")
    source = decode_canonical_bytes((ROOT / "programmes/materials/superconductivity/workflows/electron-gas-response/config.json").read_bytes(),
        UniformElectronGasAnalyticReferenceConfig, maximum_bytes=None)
    draft = supply_draft(source, draft_id="draft.report-projection.author-only")
    source_path = Path(plane.root.contract.canonical_path) / "source.json"
    source_path.write_bytes(source.canonical_bytes())
    directory = source_path.parent / "authored"
    authored = author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
        output_dir=directory, input_bindings=((draft.external_inputs[0].input_id, source_path),))
    def forbidden(*args, **kwargs):
        raise AssertionError("author-only inspection entered execution or publication")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(plane, "write", forbidden)
    monkeypatch.setattr(plane, "write_stream", forbidden)
    monkeypatch.setattr(execution, "_provenance", forbidden)
    def census():
        return tuple((path.relative_to(source_path.parent).as_posix(),
            bounded_file_sha256(path, maximum_bytes=path.stat().st_size))
            for path in sorted(source_path.parent.rglob("*")) if path.is_file())
    before = census()
    options = {"allow_unexecuted": True} if automatic else {"terminal_product_format": "compact", "allow_partial": True}
    reads = []
    load = execution.load_authored_wave
    def counted_load(**kwargs):
        reads.append(kwargs["directory"])
        return load(**kwargs)
    monkeypatch.setattr(execution, "load_authored_wave", counted_load)
    report, products, actual, plan = execution.read_recursive_wave(directory=directory, artifact_writer=plane,
        include_products=True, **options)
    assert reads == [directory]
    assert actual == draft and report["status"] == "PARTIAL"
    assert report["assigned_unit_ids"] == draft.development_study.assigned_unit_ids
    assert report["task_count"] == len(plan.tasks) == len(report["task_census"])
    assert {value["operational_status"] for value in report["task_census"]} == {"NO_COMPLETION_RECEIPT"}
    assert {value["reason_code"] for value in report["task_census"]} == {"ENTRY_OR_PROCESS_STATE_NOT_INFERRED"}
    assert report["producing_provenance_sha256"] is report["observed_producing_git_head"] is None
    assert report["qualification"] == "NOT_ESTABLISHED" and report["operational_terminal"] == "ABSENT"
    assert report["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"
    assert products["records"] == products["receipts"] == products["outputs"] == {}
    assert not report["retained_product_index"] and census() == before
    run_path = plane.root.resolve("runs/" + authored["run_id"], for_write=False)
    assert not run_path.exists()
    with pytest.raises(ValueError, match="retained input materialization"):
        execution.read_recursive_wave(directory=directory, artifact_writer=plane)
    # A present execution namespace cannot borrow the author-only projection.
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.symlink_to(run_path.parent / "missing-target", target_is_directory=True)
    with pytest.raises((ValueError, RuntimeError, OSError)):
        execution.read_recursive_wave(directory=directory, artifact_writer=plane,
            **options)
    run_path.unlink()
    run_path.mkdir()
    with pytest.raises(ValueError, match="retained input materialization"):
        execution.read_recursive_wave(directory=directory, artifact_writer=plane,
            **options)


def test_completed_partial_read_still_refuses_missing_retained_input(wave):
    run_path = wave.plane.root.resolve("runs/" + wave.report["run_id"], for_write=False)
    path = run_path / "inputs/input-0000.json"
    sidecar = path.with_name(path.name + ".manifest.json")
    saved = {value: value.read_bytes() for value in (path, sidecar)}
    try:
        for value in saved:
            value.unlink()
        for controls in ({}, {"terminal_product_format": "compact", "allow_partial": True}):
            with pytest.raises(ValueError, match="retained input materialization"):
                execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane, **controls)
    finally:
        for value, raw in saved.items():
            value.write_bytes(raw)


@pytest.mark.parametrize("mode", (None, "references", "compact"))
@pytest.mark.parametrize("opaque", (False, True))
def test_public_read_marks_exact_custody_with_deferred_binary_consumer_join(wave, monkeypatch, mode, opaque):
    """Real public PURE read; only the closed product-state discriminant is supplied.

    The existing wave has canonical outputs. This explicit seam tests report
    propagation of the owner's binary state; it is not binary/native acceptance.
    """
    from empirical_lawhood.infrastructure import recursive_custody
    actual = recursive_custody.read_recursive_products
    calls = []
    state = recursive_custody.RAW_BYTES_CONSUMER_JOIN_DEFERRED
    assert state == "COMPLETE_CANONICAL_RAW_BYTES_CONSUMER_JOIN_DEFERRED"
    def products(**arguments):
        selected = actual(**arguments)
        calls.append(arguments["decode_products"])
        if arguments["decode_products"]:
            assert selected["typed_product_validation"] == "COMPLETE"
            selected["typed_product_validation"] = state if opaque else "COMPLETE"
        else:
            assert selected["typed_product_validation"] == "DEFERRED"
        return selected
    monkeypatch.setattr(recursive_custody, "read_recursive_products", products)
    options = {} if mode is None else {"terminal_product_format": mode}
    report, retained, _, _ = execution.read_recursive_wave(directory=wave.directory, artifact_writer=wave.plane,
        include_products=True, **options)
    assert calls == [mode != "compact"]
    assert report["new_native_contact_count"] == 0 and report["qualification"] == "NOT_ESTABLISHED"
    if opaque and mode != "compact":
        assert retained["typed_product_validation"] == state
        assert report["raw_array_validation"] == "EXACT_CUSTODY_CONSUMER_MANIFEST_JOIN_DEFERRED"
    else:
        assert "raw_array_validation" not in report
    if mode == "compact":
        assert report["typed_product_validation"] == retained["typed_product_validation"] == "DEFERRED"
        assert report["scientific_completion"] == "NOT_ASSESSED_BY_COMPACT_CUSTODY"
