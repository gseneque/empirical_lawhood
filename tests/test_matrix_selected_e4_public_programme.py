# SPDX-License-Identifier: MPL-2.0
"""HELD full E4 public worker acceptance over the retained selected64 E3 run.

Opt in only after source integration, focused controls and a committed source
freeze. This is exposed software conformance with new test-only source/issue
authority. Original E3 is read, never run or recovered by this test. No fixture
source qualification or conditional statistic is a real scientific warrant.
"""

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.experiment_preparation import load_experiment_inputs
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import load_prepared_prospective_experiment
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
from tests.matrix_selected_e4_public_fixture import (
    ROOT, DISCLOSURE, authenticate_originals, authored_plan, development_inputs, execution_selection,
    held_selection, method_products, protected_plan, retained_census, revision_inputs,
    selected_populations, selected_settings_census, write_selection, _source_admissions,
)
from tests.matrix_workflow_measurements import WorkflowMeasurements, matrix_observation_callbacks
from tests.test_matrix_e3_public_programme import _ObservedProcessExecutor, _execution
from tests.runtime_platform.test_recursive_prospective_workflow import _issue_public_handoff
from tests.runtime_platform.test_study_issue import _issue_api_fixture


def retain(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


class _NoProcess:
    def __init__(self, context, refuse):
        self.context, self.refuse = context, refuse

    def Process(self, *_args, **_kwargs):
        return self.refuse("Process")

    def __getattr__(self, name):
        return getattr(self.context, name)


class NeverExecute(LocalProcessExecutor):
    """Preserve real platform metadata; every attempted child is a test failure."""
    def __init__(self, root):
        super().__init__(scratch_root=root)
        self.calls = []
        self._context = _NoProcess(self._context, self.refuse)

    def refuse(self, name):
        self.calls.append(name)
        raise AssertionError("completed public E4 read/recovery attempted worker entry: " + name)

    def execute(self, *_args, **_kwargs):
        return self.refuse("execute")

    def execute_deadline_free(self, *_args, **_kwargs):
        return self.refuse("execute_deadline_free")

    def execute_deadline_free_until(self, *_args, **_kwargs):
        return self.refuse("execute_deadline_free_until")

    def _admit_worker(self, *_args, **_kwargs):
        return self.refuse("Ready")


class IssuedProgrammeService(ExperimentProgrammeService):
    """Public service with explicitly selected test authority composition.

    This does not register another provider or bypass an entry/worker gate.
    A fresh base service calls the original context loader for each exact
    component, injecting only that component's test approval/API composition.
    It establishes SDK lifecycle acceptance, not default CLI trust deployment.
    """
    def select_controls(self, controls):
        self.controls = dict(controls)

    def _prospective_context(self, directory, **kwargs):
        control = self.controls[Path(directory).resolve(strict=True)]
        scoped = ExperimentProgrammeService(self.project_root, self.artifact_writer, self.storage_profile,
            prospective_api_factory=lambda **_options: control.api)
        return scoped._prospective_context(directory, **kwargs)


def observed_development(monkeypatch, writer, output, operation, *args, **kwargs):
    import empirical_lawhood.infrastructure.execution as execution
    observers = []
    def create(*, scratch_root):
        observer = _ObservedProcessExecutor(scratch_root, output / ("worker-ready-" + str(len(observers))))
        observers.append(observer)
        return observer
    with monkeypatch.context() as patch:
        patch.setattr(execution, "LocalProcessExecutor", create)
        result = operation(*args, **kwargs)
    return result, tuple(observers)


def observer_proof(observer, expected_tasks):
    expected_tasks = set(expected_tasks)
    assert set(observer.contracts) == set(observer.ready) == expected_tasks
    assert {task for task, _, _ in observer.completed} == expected_tasks
    assert len(observer.completed) == len(expected_tasks)
    assert all(pid != os.getpid() for _, _, pid in observer.completed)
    assert all(row.ready for row in observer.ready.values())
    assert all(observer.ready[task].invocation == contract.identity for task, contract in observer.contracts.items())
    return {"assigned_tasks": len(expected_tasks), "child_completions": tuple(observer.completed),
        "source_entries": tuple(observer.source_entries.values()),
        "prepared": {key: value.identity.to_document() for key, value in observer.contracts.items()},
        "ready": {key: value.proof() for key, value in observer.ready.items()},
        "ready_bytes": sum(value.size_bytes for value in observer.ready.values()),
        "qualification": "NOT_ESTABLISHED", "scope": DISCLOSURE}


def authoring_size_checkpoint(*, directory, writer):
    """Size the authenticated authored header and actual files; no second compile.

    The public author/loader owns content/identity validation. This operational
    checkpoint reads only the small packet header and stats its named members.
    It creates no reusable custody verdict or arbitrary generic plan-size gate.
    """
    from empirical_lawhood.api.recursive_authoring import MAX_DRAFT_BYTES, MAX_PACKET_BYTES
    from empirical_lawhood.infrastructure.bounded_io import MAX_RUNTIME_PLAN_JSON_BYTES
    from empirical_lawhood.infrastructure.development_native_custody import read_development_native_payload
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
    from empirical_lawhood.planning.recursive_authoring import MAX_RECURSIVE_CONFIG_BYTES

    directory = Path(directory)
    root = Path(writer.root.contract.canonical_path)
    relative = (directory / "authored-wave.json").relative_to(root).as_posix()
    manifest = writer.read_manifest(relative)
    raw = read_development_native_payload(writer, manifest, maximum_bytes=manifest.materialization.size_bytes)
    packet = decode_canonical_bytes(raw, AuthoredRecursiveWave, maximum_bytes=len(raw))
    rows = []
    for member in packet.members:
        path = writer.root.resolve((directory / member.filename).relative_to(root).as_posix(), for_write=False)
        size = path.stat().st_size
        assert size == member.size_bytes
        sidecar = path.with_name(path.name + ".manifest.json")
        rows.append({"filename": member.filename, "payload_bytes": size, "sidecar_bytes": sidecar.stat().st_size,
            "schema": member.identity.object_schema, "sha256_from_authenticated_header": member.identity.object_fingerprint})
    return {"scope": "ACTUAL_AUTHORED_HEADER_AND_FILE_SIZES_NOT_EXTRA_SCIENTIFIC_AUTHORITY",
        "member_count": len(rows), "member_payload_bytes": sum(row["payload_bytes"] for row in rows),
        "member_sidecar_bytes": sum(row["sidecar_bytes"] for row in rows), "packet_header_bytes": len(raw),
        "packet_header_sha256": sha256(raw).hexdigest(), "members": rows,
        "largest_config_bytes": max(row["payload_bytes"] for row in rows if row["filename"].startswith("config-")),
        "owner_bounds": {"development_draft": MAX_DRAFT_BYTES, "development_packet": MAX_PACKET_BYTES,
            "recursive_configuration": MAX_RECURSIVE_CONFIG_BYTES, "generic_runtime_plan": MAX_RUNTIME_PLAN_JSON_BYTES},
        "bound_applicability": "DEVELOPMENT_USES_ITS_ACTUAL_EXACT_MEMBER_OWNER_NOT_AN_INVENTED_GENERIC_PLAN_LIMIT",
        "native_contact": "NONE_AT_THIS_CHECKPOINT", "qualification": "NOT_ESTABLISHED"}


def issue_component(*, originals, profile, directory, output, namespace, selected, monkeypatch):
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    loaded = load_prepared_prospective_experiment(directory=directory, project_root=ROOT,
        storage_profile=profile, artifact_writer=originals.writer)
    output.mkdir(parents=True, exist_ok=False)
    scaffold_directory = output / "new-disclosed-test-authority"
    scaffold_directory.mkdir()
    handoff = loaded.handoff
    scaffold_api, paths, _, custody = _issue_api_fixture(scaffold_directory,
        standard_fixture=lambda: (handoff.authoring.base, handoff.context.resolve_standard(handoff.authoring.base).context))
    parts = (handoff, EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY, GENERATED_EXTENSION_BUNDLE_AGGREGATE,
        originals.writer, b"", scaffold_api, paths, custody)
    issued = _issue_public_handoff(output, monkeypatch, handoff_parts=parts, namespace=namespace,
        compiled_candidate=loaded.candidate)
    control = _execution(originals, handoff, issued, output, maximum_parallel_tasks=selected.workers)
    assert control.service.maximum_parallel_tasks == selected.workers
    assert control.package.execution_resource_envelope_spec.maximum_parallel_tasks == selected.workers
    retain(output / "issued-package-size.json", {"scope": DISCLOSURE,
        "package_path": str(control.package_path), "package_bytes": control.package_path.stat().st_size,
        "assigned_tasks": len(control.package.execution_resource_envelope_spec.task_cells),
        "selected_workers": selected.workers, "qualification": "NOT_ESTABLISHED",
        "native_contact": "NONE_AT_THIS_COMPONENT_CHECKPOINT"})
    return control


def component_request(plan, component_id, control, writer):
    from empirical_lawhood.api.selected_e4_programme_service import SelectedE4ComponentRequest
    relative = control.package_path.relative_to(writer.root.contract.canonical_path).as_posix()
    return SelectedE4ComponentRequest(component_id, control.package.run_plan_id, relative, control.reveal.authority_id,
        None, ())


def wave_locator(plan, wave, control):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    actual = control.service._load_status_execution_plan(control.package.run_plan_id)
    return native.SelectedE4WaveLocator(wave.wave_id, control.package.run_plan_id,
        ObjectIdentity.from_record(control.package.package_id, control.package),
        ObjectIdentity.from_record(control.package.issued_study.issue_id, control.package.issued_study),
        ObjectIdentity.from_record(control.package.execution_authority.authority_id, control.package.execution_authority),
        ObjectIdentity.from_record(control.reveal.authority_id, control.reveal),
        ObjectIdentity.from_record(actual.execution_plan_id, actual))


def _wave_observation_records(draft, records, observations):
    """Reuse freshly authenticated observations for exact produced-input admission."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4WaveObservation
    by_id={value.identity.object_id:value for value in observations}
    if len(by_id)!=len(observations):
        raise PermissionError("selected E4 observation admissions duplicate an actual wave")
    additions=[]
    used=set()
    for external in draft.external_inputs:
        if external.payload_schema!=SelectedE4WaveObservation.SCHEMA:
            continue
        value=by_id.get(external.logical_artifact_id)
        if (value is None or (value.SCHEMA,value.fingerprint(),len(value.canonical_bytes()),"application/json")!=
                (external.payload_schema,external.expected_content_sha256,external.maximum_size_bytes,external.media_type)):
            raise PermissionError("selected E4 observation admission substitutes actual authenticated bytes")
        additions.append((external.input_id,value));used.add(value.identity.object_id)
    if used!=set(by_id) or len({key for key,_ in (*records,*additions)})!=len(records)+len(additions):
        raise PermissionError("selected E4 observation admissions change the complete unique external-input census")
    return tuple(sorted((*records,*additions)))


def collection_selection(originals, plan, directory, controls):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as public
    from empirical_lawhood.api.selected_e4_native_read import read_selected_e4_programme
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from tests.matrix_selected_original_public_fixture import actual_publication
    locators = tuple(wave_locator(plan, wave, controls[wave.wave_id]) for wave in plan.declaration.programme.waves)
    observations, state = read_selected_e4_programme(writer=originals.writer, declaration=plan.declaration,
        locators=locators, codecs=operation_catalog()[2])
    assert len(observations) == len(plan.declaration.programme.waves)
    assert sum(len(value.cases) for value in observations) == len(plan.declaration.programme.cases)
    evidence = native.SelectedE4PhaseCollectionEvidence("wave-evidence." + plan.plan_id, plan.declaration.identity,
        tuple(native.SelectedE4WaveInput(locator, observation.identity, len(observation.canonical_bytes()))
            for locator, observation in zip(locators, observations, strict=True)))
    artifacts = tuple(ArtifactIdentity(value.identity.object_id, "actual-selected-e4-wave-observation", value.SCHEMA,
        value.fingerprint(), "application/json", len(value.canonical_bytes())) for value in observations)
    provisional = public.SelectedE4PhaseCollectionSelection("collection." + plan.plan_id, evidence, artifacts, (), ())
    stored = actual_publication(originals.writer, originals.writer.read_manifest(
        (directory / "native-declaration.json").relative_to(originals.writer.root.contract.canonical_path).as_posix()))
    inputs = public.ResolvedSelectedE4ComponentInputs(plan,public.ASSESSMENT_COMPONENT_ID,stored,provisional)
    specification = public.component_specification(plan, public.ASSESSMENT_COMPONENT_ID)
    draft, records, arrays = public.component_source_operands(specification, inputs)
    records = _wave_observation_records(draft, records, observations)
    configs, qualifications = _source_admissions(draft, records, arrays, root=draft.prospective_draft,
        prefix=plan.plan_id + ".assessment",
        observation_operator=plan.evidence.source.pipeline.pipeline_config.profile.observation_operator)
    # Existing plan sources retain their original qualifications; only causal
    # produced inputs and new collector/tail configs are admitted here.
    existing = {value.source_id for value in plan.preparation.source_configs}
    selected_configs = tuple(sorted((value for value in configs if value.source_id not in existing), key=lambda value: value.source_id))
    original_qualifications = {value.fingerprint() for value in plan.preparation.qualifications}
    selected_qualifications = tuple(sorted((value for value in qualifications if value.fingerprint() not in original_qualifications), key=lambda value: value.receipt_id))
    return replace(provisional, qualifications=selected_qualifications, source_configs=selected_configs), state


def assessment_products(report):
    science = report["assessment"]["scientific_result"]
    if science["scientific_completion"] != "COMPLETE_ASSIGNED_ASSESSMENT":
        raise AssertionError(science)
    from empirical_lawhood.api.recursive_operations import operation_catalog
    codecs = operation_catalog()[2]
    return tuple(decode_canonical_record(document, codecs[document["schema"]]) for _, document in science["products"])


def original_calibration_product(control, result, writer):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
    plan = control.service._load_status_execution_plan(control.package.run_plan_id)
    task, = (value for value in plan.tasks if value.capability.capability_key == "matrix-selected-e4.revision-calibrate")
    root = Path(writer.root.contract.canonical_path)
    rows = []
    for path in (root / "runs" / control.package.run_plan_id / "receipts").glob("*/*.json"):
        if path.name.endswith(".manifest.json"):
            continue
        receipt = decode_canonical_bytes(path.read_bytes(), CanonicalTaskReceipt, maximum_bytes=1024**2)
        if receipt.task_id == task.task_id and any(value.payload_schema == result.SCHEMA and value.content_sha256 == result.fingerprint()
                for value in receipt.output_logical_artifacts):
            rows.append(receipt)
    receipt, = rows
    logical, = (value for value in receipt.output_logical_artifacts
        if value.payload_schema == result.SCHEMA and value.content_sha256 == result.fingerprint())
    binding = RecursivePriorExecutionBinding("binding." + result.record_id,
        ObjectIdentity.from_record(control.package.issued_study.issue_id, control.package.issued_study),
        ObjectIdentity.from_record(control.package.execution_authority.authority_id, control.package.execution_authority),
        ObjectIdentity.from_record(control.package.package_id, control.package),
        ObjectIdentity.from_record(plan.execution_plan_id, plan), control.package.run_plan_id, task.task_id,
        ObjectIdentity.from_record(receipt.receipt_id, receipt), logical.logical_artifact_id, result.identity, ())
    return MatrixSelectedOriginalProduct(binding, ObjectIdentity.from_record(control.reveal.authority_id, control.reveal))


def execute_phase(originals, populations, selected, products, *, label, predecessor, directory, output,
        monkeypatch, measurements, public_calibration=None, calibration_product=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as public
    from empirical_lawhood.api.selected_e4_programme_service import SelectedE4ProgrammeRequest
    plan, expected_publication = protected_plan(originals, populations, selected, label=label,
        products=products, predecessor=predecessor, directory=directory,
        public_calibration=public_calibration, calibration_product=calibration_product)
    profile = replace(originals.profile, maximum_parallel_tasks=selected.workers)
    service = IssuedProgrammeService(ROOT, originals.writer, profile)
    service.select_controls({})
    path = write_selection(output / "inputs", protocol_id=public.PROGRAMME_PROTOCOL_ID, records={"plan": plan}, fields={"plan": "plan_id"})
    bound = load_experiment_inputs(plan.specification, path)
    preparation = measurements.call(label + ".prepare", service.prepare, plan.specification,
        scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=execution_selection(originals, selected))
    assert preparation.executable, service.explain(preparation)
    authored = measurements.call(label + ".author-all-waves", service.author, preparation=preparation, output_dir=directory)
    assert len(authored["components"]) == len(plan.declaration.programme.waves)
    from tests.matrix_selected_original_public_fixture import actual_publication
    actual = actual_publication(originals.writer, originals.writer.read_manifest(
        (directory / "native-declaration.json").relative_to(originals.writer.root.contract.canonical_path).as_posix()))
    assert actual == expected_publication
    controls, requests, directory_controls = {}, [], {}
    for wave in plan.declaration.programme.waves:
        component = directory / "components" / wave.wave_id
        namespace = selected.namespace + "." + label.lower() + "." + sha256(wave.wave_id.encode()).hexdigest()[:16]
        control = measurements.call(label + ".issue." + wave.wave_id, issue_component,
            originals=originals, profile=profile, directory=component, output=output / "authority" / wave.wave_id,
            namespace=namespace, selected=selected, monkeypatch=monkeypatch)
        controls[wave.wave_id] = control
        directory_controls[component.resolve(strict=True)] = control
        requests.append(component_request(plan, wave.wave_id, control, originals.writer))
    service.select_controls(directory_controls)
    request_path = output / "programme-request.json"
    request = SelectedE4ProgrammeRequest("request." + plan.plan_id, plan.identity, tuple(sorted(requests, key=lambda value: value.component_id)), None)
    request_path.write_bytes(request.canonical_bytes())
    preview = measurements.call(label + ".preview", service.run, directory=directory,
        maximum_parallel_tasks=selected.workers, programme_request_path=request_path, confirmed=False)
    assert preview["state"] == "CONFIRMATION_REQUIRED"
    assert all(not value.executor.contracts for value in controls.values())
    run = measurements.call(label + ".native-all-waves", service.run, directory=directory,
        maximum_parallel_tasks=selected.workers, programme_request_path=request_path, confirmed=True)
    assert run["state"] == "AWAITING_PRODUCED_INPUT_ADMISSIONS_AND_ASSESSMENT_AUTHORITY", run
    collection, census = measurements.call(label + ".authenticated-wave-collection", collection_selection,
        originals, plan, directory, controls)
    assert census["assigned_group_count"] == (selected.calibration_groups if label == "CAL" else selected.confirmation_groups)
    assert census["assigned_case_count"] == len(plan.declaration.programme.cases)
    # The unissued assessment remains absent until its actual public authoring
    # has produced the component that can receive independent issue/reveal acts.
    request = replace(request, collection=collection)
    request_path.write_bytes(request.canonical_bytes())
    counts = {key: len(value.executor.completed) for key, value in controls.items()}
    assessment_author = measurements.call(label + ".author-causal-assessment", service.run, directory=directory,
        maximum_parallel_tasks=selected.workers, programme_request_path=request_path, confirmed=True)
    assert assessment_author["state"] == "ASSESSMENT_AUTHORITY_REQUIRED", assessment_author
    assert counts == {key: len(value.executor.completed) for key, value in controls.items()}
    component = directory / "components" / public.ASSESSMENT_COMPONENT_ID
    assessment = measurements.call(label + ".issue-assessment", issue_component, originals=originals, profile=profile,
        directory=component, output=output / "authority" / public.ASSESSMENT_COMPONENT_ID,
        namespace=selected.namespace + "." + label.lower() + ".assessment", selected=selected, monkeypatch=monkeypatch)
    directory_controls[component.resolve(strict=True)] = assessment
    controls[public.ASSESSMENT_COMPONENT_ID] = assessment
    service.select_controls(directory_controls)
    actual_request = component_request(plan, public.ASSESSMENT_COMPONENT_ID, assessment, originals.writer)
    request = replace(request, components=tuple(sorted((*requests, actual_request), key=lambda value: value.component_id)))
    request_path.write_bytes(request.canonical_bytes())
    complete = measurements.call(label + ".actual-assessment", service.run, directory=directory,
        maximum_parallel_tasks=selected.workers, programme_request_path=request_path, confirmed=True)
    assert complete["state"] == "ASSESSMENT_RETAINED" and complete["assessment"]["status"] == "SUCCEEDED", complete
    proofs = {}
    for component_id, control in controls.items():
        plan_actual = control.service._load_status_execution_plan(control.package.run_plan_id)
        proofs[component_id] = observer_proof(control.executor, (task.task_id for task in plan_actual.tasks))
        assert all(task.capability.requested_resources.memory_bytes == selected.memory_bytes_per_task for task in plan_actual.tasks)
        assert all(task.capability.requested_resources.wall_time_seconds is None for task in plan_actual.tasks)
    run_ids = tuple(value.package.run_plan_id for value in controls.values())
    before = retained_census(originals.writer, run_ids)
    never = []
    for control in controls.values():
        blocked = NeverExecute(originals.writer.root)
        never.append(blocked)
        control.service.executor = blocked
    read = measurements.call(label + ".public-complete-read", service.read, directory=directory, programme_request_path=request_path)
    recovered = measurements.call(label + ".completed-recovery", service.recover, directory=directory,
        maximum_parallel_tasks=selected.workers, programme_request_path=request_path, confirmed=True)
    assert recovered["state"] == "ASSESSMENT_RETAINED", recovered
    assert not any(value.calls for value in never)
    assert retained_census(originals.writer, run_ids) == before
    provenance = read["original_comparator_training"]
    assert provenance["model_set"] == ObjectIdentity.from_record(originals.package.models.record_id, originals.package.models).to_document()
    assert provenance["feature_bank"] == originals.package.models.training_features.to_document()
    assert provenance["outcome_bank"] == originals.package.models.training_outcomes.to_document()
    assert provenance["units"] == list(originals.package.allocation.unit_ids("train"))
    assert read["assessment"]["scientific_result"]["original_comparator_training"] == provenance
    typed = assessment_products(read)
    retain(output / "phase-public-proof.json", {"scope": DISCLOSURE,
        "default_provider_registry": True, "default_cli_authority_composition": "NOT_TESTED",
        "public_sdk_lifecycle": "ACTUAL_WORKERS_READ_ZERO_ENTRY_COMPLETED_RECOVERY",
        "programme": plan.identity.to_document(), "assigned_groups": len(plan.declaration.programme.group_ids),
        "assigned_cases": len(plan.declaration.programme.cases), "waves": len(plan.declaration.programme.waves),
        "proofs": proofs, "scientific_qualification": "NOT_ESTABLISHED",
        "read": read, "recover": recovered, "primary_census": before})
    return SimpleNamespace(plan=plan, controls=controls, products=typed, read=read, recover=recovered)


@pytest.mark.held
def test_selected_e4_public_native_dev_revision_cal_conf_read_completed_recovery(tmp_path, monkeypatch):
    selection_path = os.environ.get("EL_E4_PUBLIC_SELECTION")
    if selection_path is None:
        pytest.skip("held actual native E4 requires an explicit retained EL_E4_PUBLIC_SELECTION")
    selected = held_selection(selection_path)
    settings_before = selected_settings_census(selected)
    assert tmp_path.resolve().is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    measurements = WorkflowMeasurements(tmp_path / "workflow-phase-measurements.json", monkeypatch,
        selection=selected.record_id, callbacks=matrix_observation_callbacks())
    originals = measurements.call("original-e3-current-custody", authenticate_originals, selected)
    assert originals.package.calibration.radius is None, "actual selected64 E3 infinite calibration must stay infinite"
    original_run = originals.issued_package.run_plan_id
    original_before = measurements.call("original-e3-primary-census-before", retained_census, originals.writer, (original_run,))
    root = Path(originals.writer.root.contract.canonical_path)
    output = originals.writer.root.resolve(selected.output_relative_path, for_write=True)
    assert not output.exists()
    output.mkdir(parents=True)
    profile = replace(originals.profile, maximum_parallel_tasks=selected.workers)
    service = ExperimentProgrammeService(ROOT, originals.writer, profile)
    populations = measurements.call("declared-populations-and-original-source-joins", selected_populations, originals, selected)
    assert tuple(len(populations.programmes[label].cases) for label in ("DEV", "CAL", "CONF")) == (288, 576, 576)
    from tests.matrix_selected_source_predecessor import selected_e4_source_predecessor
    # These structural source predecessors depend only on the full frozen
    # banks/source metadata, never on DEV outcomes or fitted revision models.
    # Execute the existing eight-producer route now and retain its actual
    # custody for later phase entry, before committing hours of DEV acquisition.
    source_predecessors = {
        label: selected_e4_source_predecessor(project_root=ROOT, originals=originals,
            programme=populations.programmes[label], bank=populations.banks[label], selected=selected,
            directory=output / (label.lower() + "-source-predecessor"),
            monkeypatch=monkeypatch, measurements=measurements)
        for label in ("CAL", "CONF")
    }
    dev_spec, dev_sources = development_inputs(originals, populations, selected, output / "dev-inputs")
    dev_bound = measurements.call("DEV.public-load-inputs", load_experiment_inputs, dev_spec, dev_sources)
    preparation = measurements.call("DEV.public-prepare", service.prepare, dev_spec,
        scientific_inputs=dev_bound.scientific_inputs, method_inputs=dev_bound.method_inputs,
        execution=execution_selection(originals, selected))
    assert preparation.executable, service.explain(preparation)
    acquisition_directory = output / "development-acquisition"
    measurements.call("DEV.public-author", service.author, preparation=preparation, output_dir=acquisition_directory)
    run, dev_draft, plan = authored_plan(acquisition_directory, originals.writer)
    assert len(plan.tasks) == 3458 and len(dev_draft.development_study.assigned_unit_ids) == 32
    sizes = measurements.call("DEV.actual-authored-size-checkpoint", authoring_size_checkpoint,
        directory=acquisition_directory, writer=originals.writer)
    retain(output / "development-authored-size-proof.json", sizes)
    acquisition, observers = measurements.call("DEV.actual-native-acquisition", observed_development,
        monkeypatch, originals.writer, output / "dev-worker-observation", service.run,
        directory=acquisition_directory, maximum_parallel_tasks=selected.workers)
    assert acquisition["status"] == "SUCCEEDED", acquisition
    assert selected_settings_census(selected) == settings_before
    assert len(observers) == 1
    dev_proof = observer_proof(observers[0], (task.task_id for task in plan.tasks))
    before = retained_census(originals.writer, (run.run_plan_id,))
    from empirical_lawhood.api.matrix_selected_e3_e4_read import read_selected_e3_e4_development
    dev_read = measurements.call("DEV.actual-receipt-scientific-read", read_selected_e3_e4_development,
        directory=acquisition_directory, artifact_writer=originals.writer, allow_partial=False)
    assert dev_read["assigned_groups"] == 32 and dev_read["assigned_cases"] == 288
    assert dev_read["original_comparator_training"]["model_set"] == ObjectIdentity.from_record(
        originals.package.models.record_id, originals.package.models).to_document()
    assert dev_read["original_comparator_training"]["feature_bank"] == originals.package.models.training_features.to_document()
    dev_public = measurements.call("DEV.public-complete-read", service.read, directory=acquisition_directory)
    assert len(dev_public["assigned_unit_ids"]) == 32
    wrapper_spec, wrapper_sources = revision_inputs(originals, populations, selected,
        output / "revision-inputs", acquisition_directory)
    wrapper_bound = measurements.call("revision.public-load-inputs", load_experiment_inputs, wrapper_spec, wrapper_sources)
    wrapper_preparation = measurements.call("revision.public-prepare", service.prepare, wrapper_spec,
        scientific_inputs=wrapper_bound.scientific_inputs, method_inputs=wrapper_bound.method_inputs,
        execution=execution_selection(originals, selected))
    assert wrapper_preparation.executable, service.explain(wrapper_preparation)
    wrapper_directory = output / "revision-from-acquisition"
    authored = measurements.call("revision.public-owned-acquisition-export-and-author", service.author,
        preparation=wrapper_preparation, output_dir=wrapper_directory)
    assert authored["status"] == "AUTHORED"
    assert retained_census(originals.writer, (run.run_plan_id,)) == before
    fit, revision_observers = measurements.call("revision.actual-fit-and-freeze", observed_development,
        monkeypatch, originals.writer, output / "revision-worker-observation", service.run,
        directory=wrapper_directory, maximum_parallel_tasks=selected.workers)
    assert fit["status"] == "SUCCEEDED", fit
    child_directory = wrapper_directory / "revision-component"
    products = measurements.call("revision.actual-original-producers", method_products, child_directory, originals.writer)
    assert products.nomination.specification.programme == populations.programmes["DEV"].identity
    assert products.frozen.programme == populations.programmes["DEV"].identity
    revision_proof = observer_proof(revision_observers[0], (task.task_id for task in products.plan.tasks))
    import empirical_lawhood.infrastructure.execution as execution
    never = []
    def no_entry(*, scratch_root):
        value = NeverExecute(scratch_root)
        never.append(value)
        return value
    primary = retained_census(originals.writer, (run.run_plan_id, products.run_id))
    with monkeypatch.context() as patch:
        patch.setattr(execution, "LocalProcessExecutor", no_entry)
        revision_read = measurements.call("revision.public-read", service.read, directory=wrapper_directory)
        recovery = measurements.call("revision.public-completed-recovery", service.recover, directory=wrapper_directory,
            maximum_parallel_tasks=selected.workers)
        dev_recovery = measurements.call("DEV.public-completed-recovery", service.recover, directory=acquisition_directory,
            maximum_parallel_tasks=selected.workers)
    assert recovery["status"] == dev_recovery["status"] == "SUCCEEDED"
    assert not any(value.calls for value in never)
    assert retained_census(originals.writer, (run.run_plan_id, products.run_id)) == primary
    assert revision_read["assigned_groups"] == 32
    retain(output / "development-and-revision-public-proof.json", {"scope": DISCLOSURE, "workers": selected.workers,
        "numerical_threads": selected.numerical_threads, "qualification": "NOT_ESTABLISHED",
        "DEV": dev_proof, "revision": revision_proof, "read": revision_read, "recover": recovery,
        "actual_nomination": products.nomination.identity.to_document(), "actual_freeze": products.frozen.identity.to_document()})
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as public_records
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as scientific
    public_calibration = calibration_product = None
    if products.nomination.trigger_disposition == "TRIGGERED":
        predecessor = source_predecessors["CAL"]
        cal = execute_phase(originals, populations, selected, products, label="CAL", predecessor=predecessor,
            directory=output / "calibration-programme", output=output / "calibration-control", monkeypatch=monkeypatch, measurements=measurements)
        actual_calibration, = (value for value in cal.products if type(value) is scientific.SelectedE4Calibration)
        assert len(actual_calibration.group_ids) == 64
        public_calibration = public_records.SelectedE4PublicCalibration.from_calibration(actual_calibration,
            record_id="public-calibration." + selected.namespace)
        calibration_product = original_calibration_product(cal.controls["assessment"], actual_calibration, originals.writer)
    else:
        retain(output / "calibration-unentered.json", {"scope": DISCLOSURE,
            "state": "UNENTERED_REVISION_" + products.nomination.trigger_disposition,
            "assigned_groups": populations.programmes["CAL"].group_ids,
            "assigned_cases": tuple(value.root_id for value in populations.programmes["CAL"].cases),
            "actual_nomination": products.nomination.identity.to_document(), "new_native_contact_count": 0,
            "scientific_qualification": "NOT_ESTABLISHED", "public_calibration_record": None})
    predecessor = source_predecessors["CONF"]
    conf = execute_phase(originals, populations, selected, products, label="CONF", predecessor=predecessor,
        directory=output / "confirmation-programme", output=output / "confirmation-control", monkeypatch=monkeypatch,
        measurements=measurements, public_calibration=public_calibration, calibration_product=calibration_product)
    confirmation, = (value for value in conf.products if type(value) is scientific.SelectedE4Confirmation)
    nomination, = (value for value in conf.products if type(value) is scientific.SelectedE4DownstreamNomination)
    assert len(confirmation.groups) == 64 and len(confirmation.family_slots) == 12
    assert nomination.confirmation_product == confirmation
    assert selected_settings_census(selected) == settings_before
    assert all(value.original_covered is None for value in confirmation.groups)
    assert retained_census(originals.writer, (original_run,)) == original_before
    assert root == Path(originals.writer.root.contract.canonical_path)
    retain(output / "full-public-e4-proof.json", {"scope": DISCLOSURE,
        "qualification": "NOT_ESTABLISHED", "original_E3_reexecuted": False,
        "original_E3_primary_custody_unchanged": True, "original_E3_calibration_radius": None,
        "workers": selected.workers, "numerical_threads": selected.numerical_threads,
        "populations": {"DEV": 32, "CAL": 64, "CONF": 64}, "paired_targets_per_case": 30,
        "conditional_family_slots": 12, "downstream_nomination": nomination.to_document(),
        "default_cli_authority_composition": "NOT_TESTED",
        "source_qualification_composition": "EXPLICIT_NEW_TEST_ONLY_SDK_ACTS",
        "scientific_settings_census_before_native_and_after_all_phases": settings_before})
    measurements.finish()
