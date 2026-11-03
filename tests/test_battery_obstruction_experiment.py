# SPDX-License-Identifier: MPL-2.0
"""Exposed metadata and custody adversaries; no supplier load or native entry."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction import (
    authenticated_operation as operation, contracts as c, experiment_preparation as owner,
    experiment_specification as records, recursive_translation as translation, science, source_custody,
)
from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt, ExternalRootContract
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, ExperimentProtocolDeclaration
from empirical_lawhood.runtime.operator_profile import OperatorStorageProfile
from empirical_lawhood.runtime.recursive_compiler import RecursiveScientificRootContext, compile_recursive_wave
from tests.battery_obstruction_fixtures import load_retained_obstruction_source


@pytest.fixture
def selected(tmp_path):
    source = load_retained_obstruction_source()
    supplied = next(row for row in source.input_manifests if row.logical.payload_schema == source.prior_supply.object_schema)
    receipt = ObjectIdentity("receipt.exposed-original-negative", CanonicalTaskReceipt.SCHEMA, CanonicalTaskReceipt.VERSION, "1" * 64)
    product = ContributionProduct("product.exposed-original-negative", source.prior_supply,
        ArtifactIdentity(supplied.logical.logical_artifact_id, "scientific-product", source.prior_supply.object_schema,
            source.prior_supply.object_fingerprint, "application/json", supplied.materialization.size_bytes), receipt,
        ContributionRole.DESIGN_OPERAND, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY)
    parent = ContributionManifest("contribution.exposed-original-negative", "Exposed metadata-only conformance", "No custody or authority asserted.",
        science.scope(source), (product,), (receipt,), ())
    storage = ExternalRootContract("storage.exposed-original-obstruction", "Unpublished original custody for refusal controls",
        str(tmp_path / "original"), "/", OperatorStorageProfile.SCHEMA, 0)
    cost = source.invocation_cost_raw_utf8.encode()
    custody = records.ObstructionSourceCustodySelection("selection.exposed-obstruction-custody", storage, c.identity(source),
        c.CustodyMember("programme-report.json", 1, source.invocation_report_sha256),
        c.CustodyMember("invocation-cost.json", len(cost), sha256(cost).hexdigest()))
    specification = records.ObstructionExperimentSpecification("experiment.exposed-obstruction", c.identity(source),
        ObjectIdentity.from_record(parent.contribution_id, parent))
    paths = {"parent": tmp_path / "parent" / "contribution.json"}
    inputs = owner.bind_obstruction_experiment_inputs(specification,
        {"source": source, "parent": parent, "custody": custody}, record_paths=MappingProxyType(paths))
    execution = ExecutionSelection(workers=1, environment_id="locked.main", output_root=str(tmp_path / "output"),
        source_snapshot=ObjectIdentity("recursive-member.implementation", "empirical-lawhood/runtime/recursive-implementation-binding", "1.0.0", "2" * 64))
    return SimpleNamespace(source=source, parent=parent, custody=custody, specification=specification, inputs=inputs,
        execution=execution, paths=paths)


def prepare(selected, **changes):
    return owner.prepare_obstruction_experiment(selected.specification, scientific_inputs=selected.inputs.scientific_inputs,
        execution=selected.execution, method_inputs=selected.inputs.method_inputs, **changes)


def test_high_level_projection_keeps_source_parent_roles_and_unknown_complete_denominators(selected, monkeypatch):
    monkeypatch.setattr(science, "assess", lambda *args: pytest.fail("preparation executed the scientific assessor"))
    prepared = prepare(selected)
    assert prepared.executable
    assert len(prepared.input_records) == len(prepared.contribution_dirs) == 1 and not prepared.input_files
    assert prepared.input_records[0][1] is selected.source
    assert {row.kind.value for row in prepared.origins.inputs} == {"SOURCE", "CONTRIBUTION"}
    assert len(prepared.draft.external_inputs) == 2
    assert len(prepared.allocation.units) == 1 and prepared.allocation.units[0].exposed
    counts = dict(prepared.census.role_counts)
    assert (counts["original-negative-forecasts"], counts["original-negative-reference-checks"],
        counts["selected-diagnostic-forecasts"], counts["entered-native-operation-records"], counts["returned-diagnostic-results"]) == (36, 9, 12, 1, 0)
    assert prepared.census.native_effect_count == counts["new-physical-units"] == 0
    assert len(prepared.design_records) == 3
    assert len(prepared.draft.canonical_bytes()) < 400000
    assert len(prepared.specification_record.canonical_bytes()) < 1500
    owner.validate_obstruction_experiment_instance(specification=selected.specification, allocation=prepared.allocation,
        draft=prepared.draft, source_records=prepared.design_records)


def test_new_declaration_compiles_complete_source_parent_graph_without_native_effect(selected):
    prepared = prepare(selected)
    declaration = operation.operation_declaration()
    compiled = compile_recursive_wave(draft=prepared.draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry("registry.exposed-obstruction", (declaration.manifest(),)),
        implementation_commit="3" * 40, output_codecs=declaration.record_codecs)
    task, = compiled.execution_plan.tasks
    assert len(tuple(row for row in task.scientific_inputs if row.consumer_input_id != "config")) == 2
    configuration, = (row for row in task.scientific_inputs if row.consumer_input_id == "config")
    assert configuration.payload_schema == declaration.config_record_type.SCHEMA and len(task.outputs) == 1
    assert declaration.registration().native_effect is False
    assert declaration.registration().publication_requirements == (operation.ORIGINAL_CUSTODY_REQUIREMENT,)
    assert declaration.provider_factory().registration == declaration.registration()


@pytest.mark.parametrize("damage", ("requirement", "falsifier", "connection", "role", "external", "claim"))
def test_real_compiler_refuses_changed_registered_scientific_graph(selected, damage):
    draft = prepare(selected).draft
    if damage in ("requirement", "falsifier"):
        field = "condition" if damage == "requirement" else "falsifier"
        draft = replace(draft, requirements=(replace(draft.requirements[0], **{field: "Unselected scientific meaning"}),))
    elif damage == "connection":
        draft = replace(draft, connections=(replace(draft.connections[0], supplier_product_id="product.unselected-original"),))
    elif damage == "role":
        draft = replace(draft, links=(replace(draft.links[0], scientific_role="HISTORY"), *draft.links[1:]))
    elif damage == "external":
        draft = replace(draft, external_inputs=(replace(draft.external_inputs[0], expected_content_sha256="f" * 64), *draft.external_inputs[1:]))
    else:
        root = replace(draft.development_study, claims=(replace(draft.development_study.claims[0], proposition="Unselected scientific finding"),))
        draft = replace(draft, development_study=root)
    declaration = operation.operation_declaration()
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
            registry=CapabilityRegistry("registry.exposed-obstruction", (declaration.manifest(),)),
            implementation_commit="3" * 40, output_codecs=declaration.record_codecs)


@pytest.mark.parametrize("coordinate", ("payload_schema", "media_type", "logical_artifact_id", "outcome_access", "visibility_ceiling", "maximum_size_bytes"))
def test_real_compiler_rejects_each_changed_exact_external_coordinate(selected, coordinate):
    prepared = prepare(selected)
    original = prepared.draft.external_inputs[0]
    value = {"payload_schema": "empirical-lawhood/testing/unselected-source", "media_type": "application/octet-stream",
        "logical_artifact_id": "artifact.unselected-original-source", "outcome_access": OutcomeAccess.PRIVILEGED_TRUTH,
        "visibility_ceiling": VisibilityCeiling.OUTCOME_VISIBLE, "maximum_size_bytes": original.maximum_size_bytes + 1}[coordinate]
    draft = replace(prepared.draft, external_inputs=(replace(original, **{coordinate: value}), *prepared.draft.external_inputs[1:]))
    declaration = operation.operation_declaration()
    with pytest.raises(ValueError):
        compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
            registry=CapabilityRegistry("registry.exposed-obstruction", (declaration.manifest(),)),
            implementation_commit="3" * 40, output_codecs=declaration.record_codecs)


def test_new_validator_refuses_missing_external_contract_roster_in_a_manual_context(selected):
    prepared = prepare(selected)
    declaration = operation.operation_declaration()
    draft = prepared.draft
    compiled = compile_recursive_wave(draft=draft, registrations=(declaration.registration(),),
        registry=CapabilityRegistry("registry.exposed-obstruction", (declaration.manifest(),)),
        implementation_commit="3" * 40, output_codecs=declaration.record_codecs)
    from empirical_lawhood.runtime.plans import ScientificStage
    context = RecursiveScientificRootContext(draft.development_study, records.AUTHENTICATED_NODE, ScientificStage.FALSIFY,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, (c.UNIT,), (c.UNIT,), False,
        draft.requirements, draft.connections, (), (), compiled.config_inputs, draft.links)
    config, = (row.record for row in compiled.config_inputs)
    with pytest.raises(ValueError, match="exact external"):
        operation.scientific_root_validator(config, context)
    operation.scientific_root_validator(config, replace(context, external_inputs=draft.external_inputs))


def test_existing_strict_caller_delegates_without_changing_original_projection(selected, monkeypatch):
    calls = []
    prior = object()
    monkeypatch.setattr(science, "assess", lambda source, supplied: calls.append((source, supplied)))
    old = translation.obstruction_draft(selected.source, prior, parent=selected.parent)
    metadata = translation.obstruction_draft_from_parent(selected.source, parent=selected.parent)
    assert calls == [(selected.source, prior)]
    assert old.canonical_bytes() == metadata.canonical_bytes()
    assert old.selected_operation_ids == ("battery-diagnostic-obstruction.assess",)


@pytest.mark.parametrize("damage", ("parent", "source", "role", "receipt", "allocation", "custody", "missing-record", "extra-record"))
def test_instance_reconstruction_refuses_source_parent_custody_and_derived_graph_substitution(selected, damage):
    prepared = prepare(selected)
    specification, allocation, draft, sources = selected.specification, prepared.allocation, prepared.draft, prepared.design_records
    if damage in ("parent", "source"):
        specification = replace(specification, **{damage: replace(getattr(specification, damage), object_fingerprint="f" * 64)})
    elif damage == "role":
        link = draft.links[0]
        draft = replace(draft, links=(replace(link, scientific_role="HISTORY"), *draft.links[1:]))
    elif damage == "receipt":
        changed = replace(selected.parent, products=(replace(selected.parent.products[0],
            producing_receipt=replace(selected.parent.products[0].producing_receipt, object_fingerprint="f" * 64)),))
        sources = tuple((key, changed if value is selected.parent else value) for key, value in sources)
    elif damage == "allocation":
        allocation = replace(allocation, units=(replace(allocation.units[0], exposed=False),))
    elif damage == "custody":
        changed = replace(selected.custody, storage=replace(selected.custody.storage, canonical_path="/tmp/unselected-original"))
        sources = tuple((key, changed if value is selected.custody else value) for key, value in sources)
    elif damage == "missing-record":
        sources = sources[:-1]
    else:
        sources = tuple(sorted((*sources, ("unselected.extra", selected.source))))
    with pytest.raises(ValueError):
        owner.validate_obstruction_experiment_instance(specification=specification, allocation=allocation, draft=draft, source_records=sources)


@pytest.mark.parametrize("damage", ("parent-name", "relative-path", "symlink"))
def test_parent_location_never_becomes_an_arbitrary_directory_or_aliased_manifest(selected, tmp_path, damage):
    path = selected.paths["parent"]
    if damage == "parent-name":
        path = path.with_name("invented-parent.json")
    elif damage == "relative-path":
        path = Path("parent/contribution.json")
    else:
        link = tmp_path / "linked-parent"
        link.symlink_to(tmp_path / "parent", target_is_directory=True)
        path = link / "contribution.json"
    with pytest.raises(ValueError, match="contribution.json"):
        owner.bind_obstruction_experiment_inputs(selected.specification,
            {"source": selected.source, "parent": selected.parent, "custody": selected.custody}, record_paths={"parent": path})


def test_public_loader_and_preparer_use_same_closed_selection_and_location_seam(selected, tmp_path, monkeypatch):
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated
    declaration = ExperimentProtocolDeclaration(records.PROTOCOL_ID, records.ObstructionExperimentSpecification,
        owner.prepare_obstruction_experiment, "battery-obstruction-experiment", maximum_config_bytes=4 * 1024 * 1024,
        input_record_types=owner.input_record_types(), bind_inputs=owner.bind_obstruction_experiment_inputs,
        validate_instance=owner.validate_obstruction_experiment_instance, bind_input_locations=True)
    monkeypatch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
    chosen = {"source": selected.source, "parent": selected.parent, "custody": selected.custody}
    bindings = []
    for role, record in sorted(chosen.items()):
        member = tmp_path / ("parent/contribution.json" if role == "parent" else role + ".json")
        member.parent.mkdir(parents=True, exist_ok=True)
        member.write_bytes(record.canonical_bytes())
        identity = c.identity(record) if role == "source" else (selected.specification.parent if role == "parent" else record.identity)
        bindings.append(ExperimentInputBinding(role, identity, member.relative_to(tmp_path).as_posix(), len(record.canonical_bytes())))
    selection = ExperimentInputSelection("inputs.exposed-obstruction", records.PROTOCOL_ID, tuple(bindings))
    path = tmp_path / "selection.json"
    path.write_bytes(selection.canonical_bytes())
    resolved = load_experiment_inputs(selected.specification, path)
    assert resolved.method_inputs.parent_directory == tmp_path / "parent"
    prepared = prepare_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        execution=selected.execution, method_inputs=resolved.method_inputs)
    assert prepared.draft == prepare(selected).draft


def test_missing_inputs_and_execution_explain_every_known_role_without_native_execution(selected):
    prepared = owner.prepare_obstruction_experiment(selected.specification, scientific_inputs={}, execution=ExecutionSelection())
    assert not prepared.executable and prepared.draft is None
    assert {row.code.rsplit("battery.obstruction.", 1)[-1] for row in prepared.dependencies} == {
        "source.missing", "parent.missing", "custody.missing", "environment", "source-snapshot", "output-root", "parent.directory"}
    assert dict(prepared.census.role_counts)["original-negative-forecasts"] == 36


def test_original_scientific_and_new_wrapper_bytes_roundtrip_separately(selected):
    original = c.ObstructionOperationConfig("config.battery-diagnostic-obstruction.assess", selected.source)
    config = records.AuthenticatedObstructionConfig("config." + records.AUTHENTICATED_NODE, original, selected.custody)
    raw = original.canonical_bytes()
    assert decode_canonical_bytes(raw, c.ObstructionOperationConfig, maximum_bytes=len(raw)).canonical_bytes() == raw
    assert decode_canonical_bytes(config.canonical_bytes(), type(config), maximum_bytes=None) == config
    assert config.source is original.source and config.operands == original.operands


def test_registered_custody_callback_rechecks_each_boundary_without_cached_verdict(selected, monkeypatch):
    config = records.AuthenticatedObstructionConfig("config." + records.AUTHENTICATED_NODE,
        c.ObstructionOperationConfig("config.battery-diagnostic-obstruction.assess", selected.source), selected.custody)
    calls = []
    monkeypatch.setattr(source_custody, "authenticate_source_custody", lambda record: calls.append(record))
    rows = (SimpleNamespace(record=config), SimpleNamespace(record=config))
    source_custody.authenticate_registered_source_custody(None, rows)
    source_custody.authenticate_registered_source_custody(None, rows)
    assert calls == [config, config]


@pytest.mark.parametrize("damage", ("storage-root", "publication"))
def test_authenticated_boundary_refuses_reselected_typed_input_before_original_io(selected, monkeypatch, damage):
    original = selected.source.input_manifests[0]
    changed = (replace(original, publication=None) if damage == "publication" else
        replace(original, publication=None, materialization=replace(original.materialization,
            storage_root_id="storage.unselected-rebound-original")))
    source = replace(selected.source, input_manifests=(changed, *selected.source.input_manifests[1:]))
    custody = replace(selected.custody, source=c.identity(source))
    config = records.AuthenticatedObstructionConfig("config." + records.AUTHENTICATED_NODE,
        c.ObstructionOperationConfig("config.battery-diagnostic-obstruction.assess", source), custody)
    monkeypatch.setattr(source_custody, "GuardedExternalRoot",
        lambda *args: pytest.fail("altered typed sidecar reached original custody I/O"))
    with pytest.raises(ValueError, match="original sidecar bytes"):
        source_custody.authenticate_registered_source_custody(None, (SimpleNamespace(record=config),))


@pytest.mark.parametrize("damage", (None, "omitted-member", "boolean-size", "cost", "new-receipt", "new-result", "new-result-manifest", "extra-contact"))
def test_custody_predicate_checks_complete_census_and_current_unknown_before_acceptance(selected, tmp_path, monkeypatch, damage):
    """I/O boundary simulation only; fake files establish no authentic custody."""
    primary = science.validate_source(selected.source)
    contact = next(row.relative_path for row in selected.source.records if row.role == "contact")
    contact_path = tmp_path / contact
    contact_path.parent.mkdir(parents=True)
    contact_path.write_bytes(b"EXPOSED I/O routing fixture, not a scientific contact")
    verified, roots = [], []

    class BoundaryRoot:
        def __init__(self, storage):
            roots.append(storage)

        def verify(self, *, for_write):
            assert for_write is False

        def resolve(self, relative, *, for_write):
            assert for_write is False
            return tmp_path / relative

    monkeypatch.setattr(source_custody, "GuardedExternalRoot", BoundaryRoot)
    monkeypatch.setattr(source_custody, "_verify_member", lambda root, member: verified.append(member))
    report = {"custody_members": {row.relative_path: {"bytes": row.size_bytes, "sha256": row.sha256}
        for row in selected.source.complete_custody}}
    if damage == "omitted-member":
        report["custody_members"].pop(next(iter(report["custody_members"])))
    elif damage == "boolean-size":
        member = next(row for row in selected.source.complete_custody if row.size_bytes == 0)
        report["custody_members"][member.relative_path]["bytes"] = False
    elif damage in ("new-receipt", "new-result", "new-result-manifest"):
        relative = (primary["index"].tasks[0].attempts[0].receipt_relative_path if damage == "new-receipt"
            else primary["plan"].tasks[0].outputs[0].relative_path)
        if damage == "new-result-manifest":
            relative += ".manifest.json"
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"Changed current completion state")
    elif damage == "extra-contact":
        (contact_path.parent / "unselected-native-contact.json").write_bytes(b"Changed current native census")
    monkeypatch.setattr(source_custody, "_read_member", lambda root, member: json.dumps(report).encode()
        if member is selected.custody.report else (b"Changed complete invocation cost" if damage == "cost"
            else selected.source.invocation_cost_raw_utf8.encode()))
    config = records.AuthenticatedObstructionConfig("config." + records.AUTHENTICATED_NODE,
        c.ObstructionOperationConfig("config.battery-diagnostic-obstruction.assess", selected.source), selected.custody)
    if damage is None:
        source_custody.authenticate_source_custody(config)
    else:
        with pytest.raises(ValueError, match="census|completion state|cost bytes"):
            source_custody.authenticate_source_custody(config)
    assert roots == [selected.custody.storage]
    assert verified == list(selected.source.complete_custody) and len(verified) == 475


@pytest.mark.parametrize("damage", ("digest", "size", "link"))
def test_exact_original_member_reader_refuses_changed_physical_bytes(tmp_path, damage):
    raw = b"original bounded custody bytes\n"
    member = c.CustodyMember("original.json", len(raw), sha256(raw).hexdigest())
    path = tmp_path / member.relative_path
    path.write_bytes(raw)
    if damage == "digest":
        path.write_bytes(raw.replace(b"bounded", b"changed"))
    elif damage == "size":
        path.write_bytes(raw + b"unexpected")
    else:
        actual = tmp_path / "other.json"
        path.rename(actual)
        path.symlink_to(actual)
    root = SimpleNamespace(resolve=lambda relative, for_write: tmp_path / relative)
    with pytest.raises((ValueError, RuntimeError, OSError)):
        source_custody._read_member(root, member)
