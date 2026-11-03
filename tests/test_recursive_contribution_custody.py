"""Exposed synthetic software custody fixtures, never native qualification evidence.

The fixture task runner publishes precomputed typed products to exercise the real
authoring, scheduler, receipt, parent, export and relocated-reader owners. It
performs no PyBaMM acquisition; scientific acceptance requires the separate
actual public two-wave numerical execution.
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from empirical_lawhood.adapters.methods.battery_recursive_construction import science
from empirical_lawhood.adapters.methods.battery_recursive_construction.contracts import (
    BatteryOperation, BatteryOperationConfig, BatteryProcedureContribution,
)
from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import (
    QUESTION_A, QUESTION_B, battery_wave_a_draft, battery_wave_b_draft, describe_contributions, next_wave_builder,
)
from empirical_lawhood.api import numerical_provenance as provenance_owner
from empirical_lawhood.api import recursive_authoring as author
from empirical_lawhood.api import recursive_execution as execution
from empirical_lawhood.api.recursive_contributions import (
    authenticate_recursive_contribution, contribution_input_bindings, export_recursive_contribution,
    inspect_recursive_contribution,
)
from empirical_lawhood.api.recursive_operations import operation_catalog
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.infrastructure import execution as execution_infrastructure
from empirical_lawhood.infrastructure import development_native_custody as native_custody
from empirical_lawhood.infrastructure import recursive_custody, task_receipts
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerRegistry, RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.recursive_handoff import PortableRecursiveContribution, RecursiveImplementationBinding
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from tests.test_battery_recursive_construction import _checkpoint, _trace
from tests.test_recursive_public_service import _plane

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_LABEL = "EXPOSED SYNTHETIC SOFTWARE CUSTODY FIXTURE; no native execution, physical validation or qualification."


@dataclass(frozen=True)
class SyntheticProductRunner:
    manifest: object
    products: tuple[tuple[str, object], ...]

    def execute(self, context):
        record = dict(self.products)[context.task_id]
        return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, record.canonical_bytes()),),
                            (ReceiptCheck("exposed-synthetic-custody-fixture", True, ()),))


class SyntheticProductExecutor(execution_infrastructure.DirectTaskExecutor):
    """Validate prepared PURE fixture contracts; claim no process enforcement."""

    def __init__(self, *, scratch_root=None):
        self.scratch_root = scratch_root

    def execute(self, runner, context, *, timeout_seconds, native_subwork=None,
                prepared_contract=None, provenance_requirements=(), native_entry=None,
                native_work_preparer=None):
        from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract

        if (native_subwork is not None or provenance_requirements or native_entry is not None
                or native_work_preparer is not None):
            raise AssertionError("synthetic product fixture refuses native work or provenance hooks")
        if prepared_contract is not None:
            if type(prepared_contract) is not PreparedInvocationContract:
                raise TypeError("synthetic product fixture requires an exact prepared invocation")
            prepared_contract.require_complete()
            prepared_contract.validate_context(context)
            if (prepared_contract.native_effect or prepared_contract.native_work is not None
                    or prepared_contract.manifest != runner.manifest):
                raise AssertionError("synthetic product fixture changes its prepared PURE runner")
            context = replace(context, prepared_invocation=prepared_contract)
        return super().execute(runner, context, timeout_seconds=timeout_seconds)


def _products(draft, manifest=None, procedure=None):
    """Produce explicitly synthetic operands by the selected fixed scientific ports."""
    values, checkpoints, traces, assessments, admissions = {}, {}, {}, {}, {}
    operations = {op.node_id: op for op in draft.operations}
    dependencies = {node: {link.producer_node_id for link in draft.links if link.consumer_node_id == node and link.producer_node_id is not None}
                    for node in operations}
    while len(values) < len(operations):
        ready = sorted(node for node, parents in dependencies.items() if node not in values and parents <= values.keys())
        assert ready
        for node in ready:
            config = decode_canonical_bytes(operations[node].config_payload.encode(), BatteryOperationConfig, maximum_bytes=4*1024**2)
            role, history, word = config.operation, config.history, config.future_word
            if role is BatteryOperation.CHECKPOINT:
                record = replace(_checkpoint(config.wave, history), checkpoint_id=f"{config.config_id}.checkpoint")
                checkpoints[history] = record
            elif role is BatteryOperation.PROJECT:
                record = science.project_checkpoint(checkpoints[history])
            elif role in {BatteryOperation.REFERENCE, BatteryOperation.FULL, BatteryOperation.SOC, BatteryOperation.TIGHTER}:
                record = replace(_trace(checkpoints[history], role.value, word), trace_id=f"{config.config_id}.trace")
                traces[history, word, role.value] = record
            elif role is BatteryOperation.ASSESS:
                soc = traces.get((history, word, "SOC"))
                record = science.assess_restart(config, checkpoints[history], traces[history, word, "REFERENCE"], traces[history, word, "FULL"], soc)
                assessments[history, word] = record
            elif role is BatteryOperation.PROCEDURE:
                record = science.construct_procedure(config, tuple(checkpoints.values()), tuple(assessments.values()))
                record = replace(record, finding=FIXTURE_LABEL, scope=replace(record.scope, coordinate_meaning=FIXTURE_LABEL))
            elif role in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}:
                record = science.admit_procedure(config, manifest, procedure, science.project_checkpoint(checkpoints[history]))
                admissions[record.consumer_id] = record
            elif role is BatteryOperation.VOLTAGE:
                record = science.assess_voltage(config, admissions["C1"], admissions["C2"], tuple(traces.values()), tuple(assessments.values()))
            else:
                raise AssertionError("unassigned fixture operation")
            values[node] = record
    return values


def _freeze_test_producer(monkeypatch):
    observed = provenance_owner.capture_numerical_provenance(project_root=ROOT)
    source = RecursiveImplementationBinding(observed.package_sources, observed.code_sources_sha256,
                observed.dependency_lock_sha256, observed.observed_git_head, observed.observed_checkout_clean)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **_kwargs: source)
    monkeypatch.setattr(execution, "implementation_binding", lambda root, **_kwargs: source)
    monkeypatch.setattr(provenance_owner, "capture_numerical_provenance", lambda **kwargs: observed)
    # This synthetic conformance harness deliberately uses direct publication;
    # the public native route separately exercises the process executor.
    monkeypatch.setattr(execution_infrastructure, "LocalProcessExecutor", SyntheticProductExecutor)


def _publish_fixture_wave(monkeypatch, plane, directory, draft, *, manifest=None, procedure=None, parent=None):
    products = _products(draft, manifest, procedure)
    _, registry, _ = operation_catalog()
    manifests = {m.registry_id: m for m in registry.capabilities}
    runners = tuple(SyntheticProductRunner(manifests[selection], tuple(sorted(products.items())))
                    for selection in sorted({op.selection.selection_id for op in draft.operations}))
    monkeypatch.setattr(execution, "operation_runners", lambda **kwargs: RunnerRegistry(runners, registry_sha256=registry.fingerprint()))
    authored = author.author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane,
                                            output_dir=directory, contribution_dir=parent)
    report = execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane)
    assert report["status"] == "SUCCEEDED" and authored["native_contact"] == "none"
    return report


@pytest.fixture
def portable_a(tmp_path, monkeypatch):
    _freeze_test_producer(monkeypatch)
    producer = _plane(tmp_path / "producer-selected")
    directory = tmp_path / "producer-selected/authored-a"
    report = _publish_fixture_wave(monkeypatch, producer, directory, battery_wave_a_draft())
    exported = tmp_path / "producer-selected/exported-a"
    transport_report = export_recursive_contribution(directory=directory, output_dir=exported, project_root=ROOT, artifact_writer=producer)
    consumer = _plane(tmp_path / "new-consumer-selected")
    imported = tmp_path / "new-consumer-selected/imported-a"
    shutil.copytree(exported, imported)
    return producer, directory, report, exported, consumer, imported, transport_report


def _raw_snapshot(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes() for p in directory.rglob("*") if p.is_file() and not p.name.endswith(".lock")}


def _read_transport(directory):
    return decode_canonical_bytes((directory / "transport.json").read_bytes(), PortableRecursiveContribution, maximum_bytes=16*1024**2)


def _members_with_schema(directory, schema):
    """Select scientific records, rather than publication controls in their scope."""
    return [directory / "custody" / member.relative_path for member in _read_transport(directory).members
            if member.relative_path.endswith(".json") and
            json.loads((directory / "custody" / member.relative_path).read_bytes()).get("schema") == schema]


def _refresh_outer_census(directory):
    """An editable transport checksum is never sufficient completion custody."""
    transport = _read_transport(directory)
    from empirical_lawhood.api.recursive_contributions import _custody_members
    members = _custody_members(directory / "custody", (transport.authoring_relative_path,
                              transport.run_relative_path, *transport.parent_closure_relative_paths))
    (directory / "transport.json").write_bytes(replace(transport, members=members).canonical_bytes())


def test_relocated_exact_closure_authenticates_without_native_or_producer_root(portable_a, monkeypatch):
    producer, _, report, exported, consumer, imported, transport_report = portable_a
    expected = _raw_snapshot(imported)
    def no_contact(*args, **kwargs):
        pytest.fail("portable reader attempted native acquisition or producing checkout inspection")
    monkeypatch.setattr(science, "capture_checkpoint", no_contact)
    monkeypatch.setattr(science, "continue_checkpoint", no_contact)
    monkeypatch.setattr(execution, "implementation_binding", no_contact)
    # Remove the original producer entirely: the consumer has a complete copy.
    shutil.rmtree(Path(producer.root.contract.canonical_path))
    result = inspect_recursive_contribution(directory=imported, artifact_writer=consumer)
    assert result["status"] == "AUTHENTICATED" and result["producing_run_id"] == report["run_id"]
    assert result["scientific_authority"] == "NONE" and result["qualification"] == "NOT_ESTABLISHED"
    assert transport_report["custody_member_count"] > 50
    assert _raw_snapshot(imported) == expected
    assert exported != imported


def test_parent_product_role_scope_receipts_and_exact_external_binding_are_retained(portable_a):
    _, _, _, _, consumer, imported, _ = portable_a
    _, _, manifest, _, products, _ = authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    procedure = next(record for values in products["records"].values() for record in values.values() if isinstance(record, BatteryProcedureContribution))
    assert manifest.scope == procedure.scope and FIXTURE_LABEL in manifest.finding
    assert procedure.assessed_future_words == ("hold",)
    assert procedure.remaining_obligations == ("changed-future-fidelity", "new-instance-supply")
    assert all(p.evidence_ceiling is EvidenceCeiling.NON_PROMOTABLE and p.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE and
               p.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY for p in manifest.products)
    assert {p.producing_receipt.object_fingerprint for p in manifest.products} <= {r.fingerprint() for r in products["receipts"].values()}
    draft = battery_wave_b_draft(manifest, procedure)
    bindings = dict(contribution_input_bindings(directory=imported, draft=draft, artifact_writer=consumer))
    assert set(bindings) == {"battery.parent.manifest", "battery.parent.procedure"}
    assert bindings["battery.parent.procedure"].read_bytes() == procedure.canonical_bytes()
    assert bindings["battery.parent.manifest"].read_bytes() == manifest.canonical_bytes()
    assert all(str(path).startswith(str(imported)) for path in bindings.values())


def test_registered_contribution_callbacks_follow_actual_products_under_a_cloned_authored_label(tmp_path, monkeypatch):
    _freeze_test_producer(monkeypatch)
    plane = _plane(tmp_path / "selected-cloned-study")
    directory = Path(plane.root.contract.canonical_path) / "authored"
    draft = replace(battery_wave_a_draft(), draft_id="researcher.exposed-procedure-study")
    _publish_fixture_wave(monkeypatch, plane, directory, draft)
    exported = directory.parent / "exported"
    export_recursive_contribution(directory=directory, output_dir=exported, project_root=ROOT, artifact_writer=plane)
    _, _, manifest, _, products, _ = authenticate_recursive_contribution(directory=exported, artifact_writer=plane)
    assert manifest.contribution_id == "contribution.researcher.exposed-procedure-study"
    assert manifest.scientific_question == QUESTION_A and FIXTURE_LABEL in manifest.finding
    next_wave = decode_canonical_bytes((exported / "next-wave.json").read_bytes(), RecursiveStudyDraft, maximum_bytes=16*1024**2)
    assert next_wave.question == QUESTION_B and next_wave.draft_id == "battery.wave-b"
    assert next_wave.contribution_parents == (manifest,)
    assert next_wave_builder(draft, manifest, products) == next_wave
    assert next(value for value in next_wave.external_inputs if value.input_id == "battery.parent.manifest").expected_content_sha256 == manifest.fingerprint()
    for operation in next_wave.operations:
        config = decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig, maximum_bytes=4*1024**2)
        if config.contribution_sha256 is not None:
            assert config.contribution_sha256 == manifest.fingerprint()


def test_contribution_projection_refuses_missing_ambiguous_or_out_of_scope_actual_terminals(portable_a):
    _, _, _, _, consumer, imported, _ = portable_a
    _, _, manifest, _, products, view = authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    transport = _read_transport(imported)
    _, draft, _, _ = author.load_authored_wave(directory=imported / "custody" / transport.authoring_relative_path, artifact_writer=view)
    terminal_task, terminal_output, procedure = next((task, output, record) for task, values in products["records"].items()
        for output, record in values.items() if isinstance(record, BatteryProcedureContribution))
    def changed_records():
        return {task: dict(values) for task, values in products["records"].items()}
    absent = changed_records()
    del absent[terminal_task][terminal_output]
    ambiguous = changed_records()
    ambiguous[terminal_task]["unassigned-duplicate"] = procedure
    outside = changed_records()
    outside[terminal_task][terminal_output] = replace(procedure, scope=replace(procedure.scope, valid_until=Decimal(900)))
    missing_assessment = changed_records()
    assessed_task = next(task for task, values in missing_assessment.items() if any(record.SCHEMA.endswith("restart-assessment") for record in values.values()))
    missing_assessment[assessed_task] = {}
    for records, message in ((absent, "unique declared terminal"), (ambiguous, "unique declared terminal"),
                             (outside, "declared scientific source"), (missing_assessment, "actual assessment census")):
        with pytest.raises(ValueError, match=message):
            describe_contributions(draft, dict(products, records=records))
    with pytest.raises(ValueError, match="exact authenticated contribution"):
        next_wave_builder(draft, replace(manifest, finding="Forged parent scientific content"), products)


@pytest.mark.parametrize("tamper", ["output", "receipt", "extra-file", "missing-receipt"])
def test_tampered_or_incomplete_custody_refuses_even_if_display_status_says_success(portable_a, tamper):
    _, _, _, _, consumer, imported, _ = portable_a
    custody = imported / "custody"
    transport = _read_transport(imported)
    if tamper == "extra-file":
        (custody / transport.authoring_relative_path / "extra-unassigned.json").write_bytes(b"{}\n")
    else:
        candidates = _members_with_schema(imported, "empirical-lawhood/runtime/canonical-task-receipt")
        assert candidates
        path = candidates[0]
        if tamper == "missing-receipt":
            path.unlink()
        elif tamper == "receipt":
            before = path.read_bytes()
            after = before.replace(b'SUCCEEDED', b'FAILED', 1)
            assert after != before
            path.write_bytes(after)
        else:
            outputs = [custody / m.relative_path for m in transport.members if "/outputs/" in m.relative_path and m.relative_path.endswith(".json") and not m.relative_path.endswith(".manifest.json")]
            assert outputs
            outputs[0].write_bytes(b'{}\n')
    with pytest.raises((ValueError, RuntimeError, OSError)):
        inspect_recursive_contribution(directory=imported, artifact_writer=consumer)


def test_recipe_and_transport_digest_do_not_qualify_forged_scope(portable_a):
    _, _, _, _, consumer, imported, _ = portable_a
    original = decode_canonical_bytes((imported / "contribution.json").read_bytes(), ContributionManifest, maximum_bytes=16*1024**2)
    forged = replace(original, scope=replace(original.scope, valid_until=Decimal(900)))
    (imported / "contribution.json").write_bytes(forged.canonical_bytes())
    transport = replace(_read_transport(imported), contribution=ObjectIdentity.from_record(forged.contribution_id, forged))
    (imported / "transport.json").write_bytes(transport.canonical_bytes())
    with pytest.raises(ValueError, match="actual producing receipts"):
        inspect_recursive_contribution(directory=imported, artifact_writer=consumer)


def test_complete_receipt_is_required_after_recomputing_the_editable_transport_census(portable_a):
    _, _, _, _, consumer, imported, _ = portable_a
    receipt = _members_with_schema(imported, "empirical-lawhood/runtime/canonical-task-receipt")[0]
    receipt.unlink()
    _refresh_outer_census(imported)
    with pytest.raises((ValueError, RuntimeError, OSError), match="receipt|artifact|publication|material|batch"):
        inspect_recursive_contribution(directory=imported, artifact_writer=consumer)


def test_retained_input_contract_checks_exact_lineage_role_profile_and_size_before_payload(portable_a, monkeypatch):
    producer, directory, _, _, _, _, _ = portable_a
    _, draft, _, payloads = author.load_authored_wave(directory=directory, artifact_writer=producer)
    _, plan, _ = execution._retained_plans(payloads, draft)
    relative = f"runs/{plan.source_plan.object_id}/inputs/input-0000.json.manifest.json"
    raw = producer.root.resolve(relative, for_write=False).read_bytes()
    original_decoder = task_receipts.decode_artifact_manifest
    original = original_decoder(raw)
    logical = original.logical
    profile = ArtifactProfile.RAW_SOURCE_BYTES
    mutations = (
        replace(logical, media_type="application/octet-stream"),
        replace(logical, profile=profile, generic_validation=replace(logical.generic_validation, profile=profile)),
        replace(logical, visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE),
        replace(logical, visibility_ceiling=VisibilityCeiling.PRIVILEGED_TRUTH, outcome_access=OutcomeAccess.PRIVILEGED_TRUTH),
        replace(logical, lineage_parents=(), parent_visibility_ceilings=()),
        replace(logical, lineage_parents=(replace(logical.lineage_parents[0], identity=replace(
                logical.lineage_parents[0].identity, object_fingerprint="f"*64)),)),
    )
    changed = tuple(ArtifactManifest(value, original.materialization) for value in mutations) + (
        ArtifactManifest(logical, replace(original.materialization, size_bytes=original.materialization.size_bytes + 1)),)
    def forbidden(*args, **kwargs):
        pytest.fail("invalid retained metadata reached payload acquisition")
    monkeypatch.setattr(native_custody, "read_development_native_payload", forbidden)
    for candidate in changed:
        monkeypatch.setattr(task_receipts, "decode_artifact_manifest",
            lambda payload, *, maximum_bytes=None, candidate=candidate, **kwargs: candidate
            if sha256(payload).digest() == sha256(raw).digest()
            else original_decoder(payload, maximum_bytes=maximum_bytes, **kwargs))
        with pytest.raises(ValueError, match="frozen scientific identity"):
            execution._external_inputs(plane=producer, plan=plan, draft=draft, payloads=payloads, read_only=True)


def test_inner_reader_refuses_consistent_terminal_hash_with_changed_schema_input_census_or_lineage(portable_a, monkeypatch):
    _, _, _, _, consumer, imported, _ = portable_a
    _, transport, _, _, products, plane = authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    directory = imported / "custody" / transport.authoring_relative_path
    _, draft, _, payloads = author.load_authored_wave(directory=directory, artifact_writer=plane)
    _, plan, index = execution._retained_plans(payloads, draft)
    inputs = execution._external_inputs(plane=plane, plan=plan, draft=draft, payloads=payloads, read_only=True)
    first = plan.topological_task_ids()[0]
    original = products["receipts"][first]
    logical = original.output_logical_artifacts[0]
    schema = "empirical-lawhood/testing/changed-output-schema"
    variants = (
        replace(original, input_materialization_ids=()),
        replace(original, output_logical_artifacts=(replace(logical, payload_schema=schema,
                generic_validation=replace(logical.generic_validation, payload_schema=schema)),)),
        replace(original, output_logical_artifacts=(replace(logical, lineage_parents=(), parent_visibility_ceilings=()),)),
        replace(original, output_logical_artifacts=(replace(logical, visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE),)),
    )
    _, _, codecs = operation_catalog()
    original_recovery = recursive_custody.ExternalRunRecoveryStore
    for changed in variants:
        terminal = replace(products["terminal"], attempts=tuple(
            replace(row, receipt_sha256=changed.fingerprint()) if row.task_id == first else row
            for row in products["terminal"].attempts))
        class ReceiptView:
            def __init__(self, plane):
                self.plane = plane
            def read(self, run, task, attempt):
                return changed if task == first else products["receipts"][task]
        class RecoveryView:
            _validate_receipt_static = staticmethod(recursive_custody.ExternalRunRecoveryStore._validate_receipt_static)
            def __init__(self, plane):
                pass
            def read_terminal(self, index):
                return terminal
            def read_index(self, path, *, expected_schema):
                return original_recovery(plane).read_index(path, expected_schema=expected_schema)
            def read_event(self, index, path):
                return original_recovery(plane).read_event(index, path)
        with monkeypatch.context() as context:
            context.setattr(recursive_custody, "ExternalTaskReceiptStore", ReceiptView)
            context.setattr(recursive_custody, "ExternalRunRecoveryStore", RecoveryView)
            with pytest.raises((ValueError, RuntimeError), match="input materialization census|recovery index|input lineage|scientific role|receipt or recovery event"):
                recursive_custody.read_recursive_products(plane=plane, plan=plan, index=index,
                                                         external_inputs=inputs, output_codecs=codecs)


def test_changed_parent_bytes_or_access_are_refused_before_any_new_effect(portable_a):
    _, _, _, _, consumer, imported, _ = portable_a
    _, _, manifest, _, products, _ = authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    procedure = next(record for values in products["records"].values() for record in values.values() if isinstance(record, BatteryProcedureContribution))
    draft = battery_wave_b_draft(manifest, procedure)
    changed = replace(draft, contribution_parents=(replace(manifest, finding="Changed source finding"),))
    with pytest.raises(ValueError, match="exact authenticated contribution"):
        contribution_input_bindings(directory=imported, draft=changed, artifact_writer=consumer)
    external = next(value for value in draft.external_inputs if value.input_id == "battery.parent.procedure")
    blind = replace(external, visibility_ceiling=VisibilityCeiling.PROSPECTIVE, outcome_access=OutcomeAccess.OUTCOME_BLIND)
    with pytest.raises(ValueError, match="role, bytes or access"):
        from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
        registrations, registry, codecs = operation_catalog()
        compile_recursive_wave(draft=replace(draft, external_inputs=tuple(blind if i.input_id == blind.input_id else i for i in draft.external_inputs)),
            registrations=registrations, registry=registry, implementation_commit="a"*40, output_codecs=codecs)


def test_provenance_keeps_original_runtime_bytes_and_refuses_changed_runtime_or_source_before_effects(portable_a, monkeypatch):
    producer, directory, report, _, _, _, _ = portable_a
    original = execution._provenance(plane=producer, run_id=report["run_id"])
    runtime = json.loads(original.runtime_observation_json)
    assert len(runtime["threadpools"]) >= 2
    before = _raw_snapshot(Path(producer.root.contract.canonical_path))
    reordered_runtime = dict(runtime, threadpools=list(reversed(runtime["threadpools"])))
    reordered = replace(original, runtime_observation_json=canonical_json_bytes(provenance_owner.immutable_json(reordered_runtime)).decode())
    assert reordered.runtime_observation_json != original.runtime_observation_json
    assert execution._provenance(plane=producer, run_id=report["run_id"], observed=reordered) == original
    def no_effect(*args, **kwargs):
        pytest.fail("changed source/runtime reached the task executor")
    monkeypatch.setattr(execution_infrastructure, "LocalProcessExecutor", no_effect)
    changed_runtime = dict(runtime, threadpools=[dict(row, num_threads=row["num_threads"] + 1)
                                              for row in runtime["threadpools"]])
    changed = replace(original, runtime_observation_json=canonical_json_bytes(provenance_owner.immutable_json(changed_runtime)).decode())
    monkeypatch.setattr(provenance_owner, "capture_numerical_provenance", lambda **kwargs: changed)
    with pytest.raises(ValueError, match="numerical_runtime|single-thread"):
        execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=producer)
    for field in ("dependency_lock_sha256", "observed_git_head"):
        _, _, source, _ = author.load_authored_wave(directory=directory, artifact_writer=producer)
        candidate = replace(source, **{field: "f" * (40 if field == "observed_git_head" else 64)})
        monkeypatch.setattr(execution, "implementation_binding", lambda root, candidate=candidate, **_kwargs: candidate)
        with pytest.raises(ValueError, match="source or lock changed"):
            execution.run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=producer)
    assert _raw_snapshot(Path(producer.root.contract.canonical_path)) == before


def test_later_product_export_preserves_transitive_parent_closure_after_relocation(portable_a, monkeypatch, tmp_path):
    producer, _, _, _, consumer, imported, _ = portable_a
    _, _, manifest, _, products, _ = authenticate_recursive_contribution(directory=imported, artifact_writer=consumer)
    procedure = next(record for values in products["records"].values() for record in values.values() if isinstance(record, BatteryProcedureContribution))
    draft = battery_wave_b_draft(manifest, procedure)
    directory = Path(consumer.root.contract.canonical_path) / "authored-b"
    report = _publish_fixture_wave(monkeypatch, consumer, directory, draft, manifest=manifest, procedure=procedure, parent=imported)
    exported = Path(consumer.root.contract.canonical_path) / "exported-b"
    export_recursive_contribution(directory=directory, output_dir=exported, project_root=ROOT, artifact_writer=consumer)
    newest = _plane(tmp_path / "third-selected")
    copied = Path(newest.root.contract.canonical_path) / "imported-b"
    shutil.copytree(exported, copied)
    original_bytes = _raw_snapshot(copied)
    shutil.rmtree(Path(producer.root.contract.canonical_path))
    shutil.rmtree(Path(consumer.root.contract.canonical_path))
    result = inspect_recursive_contribution(directory=copied, artifact_writer=newest)
    assert result["producing_run_id"] == report["run_id"]
    assert _raw_snapshot(copied) == original_bytes
    transport = _read_transport(copied)
    assert transport.parent_closure_relative_paths == ("imported-a",)
    assert any("imported-a/custody/" in member.relative_path for member in transport.members)
    assert result["contribution"]["value"]["predecessors"][0]["value"]["object_fingerprint"] == manifest.fingerprint()
