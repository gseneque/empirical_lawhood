# SPDX-License-Identifier: MPL-2.0
"""Public specification edits over exact exposed Rubisco source records."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.disclosed_examples import DisclosedAssumption
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.experiment_inputs import (
    bind_kinetic_experiment_inputs,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.experiment_preparation import (
    prepare_kinetic_experiment, validate_kinetic_experiment_instance,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.experiment_specification import (
    PROTOCOL_ID, RubiscoKineticExperimentSpecification, kinetic_experiment_specification,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.operation_bindings import (
    KineticJoinConfig, UNIT,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply import JointKineticSupply, KineticTargetComparison
from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.api.experiment_preparation import (
    author_prepared_experiment, experiment_preparation_report, experiment_protocols,
    load_experiment_inputs, load_experiment_specification, prepare_experiment,
)
from empirical_lawhood.api.configuration import validate_configuration
from empirical_lawhood.api.recursive_authoring import implementation_binding, load_authored_wave
from empirical_lawhood.api.recursive_operations import operation_catalog
from empirical_lawhood.cli.app import app
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "programmes/biology/photosynthesis/workflows/rubisco-kinetic-join"


def _records():
    records = {key: decode_canonical_bytes((EXAMPLE / filename).read_bytes(), kind, maximum_bytes=None)
        for key, filename, kind in (("material", "assumptions.json", DisclosedAssumption),
            ("supply", "supply.json", JointKineticSupply), ("query", "query.json", AssayQuery),
            ("comparison", "comparison.json", KineticTargetComparison))}
    records["campaign"] = decode_canonical_bytes((EXAMPLE / "draft.json").read_bytes(),
        RecursiveStudyDraft, maximum_bytes=None).campaign
    return records


def _specification(records=None):
    records = _records() if records is None else records
    return kinetic_experiment_specification(specification_id="specification.rubisco-kinetic-experiment.exposed",
        campaign=records["campaign"], material=records["material"], supply=records["supply"],
        source_query=records["query"], comparison=records["comparison"])


def _execution(directory):
    source = implementation_binding(ROOT)
    return ExecutionSelection(workers=1, environment_id="rubisco-prediction",
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", source),
        output_root=str(directory))


def _sources(directory, specification, records):
    directory.mkdir()
    bindings = []
    for key, record in sorted(records.items()):
        path = directory / (key + ".json")
        path.write_bytes(record.canonical_bytes())
        identity = specification.source_query if key == "query" else getattr(specification, key)
        bindings.append(ExperimentInputBinding(key, identity, path.name, len(record.canonical_bytes())))
    selection = ExperimentInputSelection("selection.rubisco-kinetic-experiment.original-sources",
        PROTOCOL_ID, tuple(bindings))
    path = directory / "sources.json"
    path.write_bytes(selection.canonical_bytes())
    return path


def _prepare(specification, records, execution):
    resolved = bind_kinetic_experiment_inputs(specification, records)
    return prepare_kinetic_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=execution)


def test_specification_gas_edit_reuses_the_same_public_source_selection_and_operation_route(tmp_path):
    records = _records()
    original = {key: record.canonical_bytes() for key, record in records.items()}
    first = _specification(records)
    second = replace(first, query=replace(first.query, co2_um=Decimal("20")))
    source_path = _sources(tmp_path / "original-inputs", first, records)
    selection_bytes = source_path.read_bytes()
    preparations = []
    for specification in (first, second):
        path = tmp_path / (specification.fingerprint() + ".json")
        path.write_bytes(specification.canonical_bytes())
        assert load_experiment_specification(path) == specification
        validation = validate_configuration(path, consumer="rubisco-kinetic-experiment")
        assert validation["consumer_byte_ready"] and not validation["authority_granted"]
        resolved = load_experiment_inputs(specification, source_path)
        preparation = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
            method_inputs=resolved.method_inputs, execution=_execution(tmp_path / "unentered-output"))
        assert preparation.executable and preparation.dependencies == ()
        assert preparation.draft.campaign == records["campaign"]
        assert preparation.allocation.unit_ids() == (UNIT,)
        assert dict(preparation.census.role_counts) == {"analytical": 1, "biological": 0, "supported-members": 3}
        assert dict(preparation.census.output_counts)["supplied-solver-calls"] == 1
        assert dict(preparation.census.output_counts)["partial-members"] == 1
        assert dict(preparation.census.output_counts)["rejected-members"] == 1
        assert preparation.census.native_effect_count == 0
        assert {row.node_id for row in preparation.draft.operations} == {
            "rubisco-kinetic-join.assay", "rubisco-kinetic-join.assess"}
        selected = dict(preparation.input_records)
        assert selected["external.rubisco-kinetic-join.supply"].canonical_bytes() == original["supply"]
        assert selected["external.rubisco-kinetic-join.comparison"].canonical_bytes() == original["comparison"]
        assert selected["external.rubisco-kinetic-join.query"] == specification.query
        assert specification.source_query in preparation.allocation.sources
        assert {identity: record.canonical_bytes() for identity, record in preparation.design_records} == {
            (specification.source_query if key == "query" else getattr(specification, key)).object_id: original[key]
            for key in records}
        registrations, registry, codecs = operation_catalog()
        compiled = compile_recursive_wave(draft=preparation.draft, registrations=registrations,
            registry=registry, implementation_commit=implementation_binding(ROOT).observed_git_head,
            output_codecs=codecs)
        assert len(compiled.execution_plan.tasks) == 2
        config = decode_canonical_bytes(preparation.draft.operations[0].config_payload.encode(),
            KineticJoinConfig, maximum_bytes=None)
        assert config.science.query.object_fingerprint == specification.query.fingerprint()
        report = experiment_preparation_report(preparation)
        assert report["scientific_execution_performed"] is False
        assert report["qualification"] == "NOT_ESTABLISHED" and report["scientific_authority"] == "NONE"
        preparations.append(preparation)
    assert preparations[0].allocation.identity != preparations[1].allocation.identity
    assert preparations[0].draft.fingerprint() != preparations[1].draft.fingerprint()
    assert source_path.read_bytes() == selection_bytes
    assert {key: record.canonical_bytes() for key, record in records.items()} == original
    assert not (tmp_path / "unentered-output").exists()


def test_missing_preparation_reports_all_original_inputs_and_execution_selections(tmp_path):
    specification = _specification()
    preparation = prepare_experiment(specification)
    expected = {"rubisco.kinetic." + key + ".missing": DependencyKind.EXTERNAL_INPUT
        for key in ("campaign", "material", "supply", "query", "comparison")}
    expected.update({"rubisco.kinetic.environment": DependencyKind.ENVIRONMENT,
        "rubisco.kinetic.source-snapshot": DependencyKind.ENVIRONMENT,
        "rubisco.kinetic.output-root": DependencyKind.STORAGE,
        "experiment.workers": DependencyKind.ENVIRONMENT})
    assert {row.code: row.kind for row in preparation.dependencies} == expected
    assert dict(preparation.census.role_counts)["supported-members"] == 3
    assert dict(preparation.census.resolved_role_counts)["supported-members"] == 0
    assert preparation.allocation is None and preparation.draft is None
    path = tmp_path / "specification.json"
    path.write_bytes(specification.canonical_bytes())
    result = CliRunner().invoke(app, ["campaign", "experiment-explain", "--input", str(path)])
    assert result.exit_code == 0, result.stdout + result.stderr


@pytest.mark.parametrize("missing", ("campaign", "material", "query", "comparison"))
def test_partial_input_binding_keeps_the_complete_supply_denominator(missing, tmp_path):
    records = _records()
    specification = _specification(records)
    del records[missing]
    preparation = _prepare(specification, records, _execution(tmp_path))
    assert [row.code for row in preparation.dependencies] == ["rubisco.kinetic." + missing + ".missing"]
    assert dict(preparation.census.resolved_role_counts)["supported-members"] == 3
    assert dict(preparation.census.output_counts)["partial-members"] == 1
    assert dict(preparation.census.output_counts)["rejected-members"] == 1
    assert not preparation.executable and preparation.draft is None


@pytest.mark.parametrize("change", ("source", "roster", "allocation", "campaign"))
def test_unsupported_source_census_and_campaign_changes_refuse_before_execution(change, tmp_path):
    records = _records()
    specification = _specification(records)
    if change == "source":
        records["material"] = replace(records["material"], description="A changed disclosed material source")
    elif change == "roster":
        source = records["supply"]
        records["supply"] = replace(source, expected_member_ids=source.expected_member_ids[:-1], members=source.members[:-1])
    elif change == "campaign":
        records["campaign"] = replace(records["campaign"], system_ids=("material.unrelated",))
    resolved = bind_kinetic_experiment_inputs(specification, records)
    allocations = dict(resolved.scientific_inputs)
    if change == "allocation":
        allocations.clear()
    preparation = prepare_experiment(specification, scientific_inputs=allocations,
        method_inputs=resolved.method_inputs, execution=_execution(tmp_path))
    assert not preparation.executable and preparation.draft is None
    assert any(row.kind is DependencyKind.SCIENTIFIC_EVIDENCE for row in preparation.dependencies)
    if change == "roster":
        assert dict(preparation.census.resolved_role_counts)["supported-members"] == 2
        assert dict(preparation.census.role_counts)["supported-members"] == 3


def test_input_codec_roster_is_closed_and_public_bytes_are_authenticated(tmp_path):
    records = _records()
    specification = _specification(records)
    declaration, = (row for row in experiment_protocols() if row.protocol_id == PROTOCOL_ID)
    assert declaration.specification_type is RubiscoKineticExperimentSpecification
    with pytest.raises(ValueError, match="unknown keys"):
        bind_kinetic_experiment_inputs(specification, {**records, "native-runner": records["query"]})
    with pytest.raises(TypeError, match="wrong closed record type"):
        bind_kinetic_experiment_inputs(specification, {**records, "supply": records["query"]})
    path = _sources(tmp_path / "sources", specification, records)
    payload = (path.parent / "supply.json").read_bytes()
    (path.parent / "supply.json").write_bytes(payload[:-1] + b" ")
    with pytest.raises(ValueError, match="selected bytes"):
        load_experiment_inputs(specification, path)


def test_prospective_selection_preserves_explicit_science_authority_and_software_dependencies(tmp_path):
    records = _records()
    specification = replace(_specification(records), evidence_scope="PROSPECTIVE_REQUIRED")
    preparation = _prepare(specification, records, _execution(tmp_path))
    assert {row.kind for row in preparation.dependencies} == {
        DependencyKind.SCIENTIFIC_EVIDENCE, DependencyKind.AUTHORITY, DependencyKind.SOFTWARE}
    assert preparation.allocation.unit_ids() == (UNIT,)
    assert not preparation.executable and preparation.draft is None
    assert dict(preparation.census.role_counts)["biological"] == 0


def test_specification_cannot_drop_a_rejected_original_member_from_the_denominator(tmp_path):
    records = _records()
    specification = _specification(records)
    shortened = replace(specification, expected_member_ids=specification.expected_member_ids[:-1])
    preparation = _prepare(shortened, records, _execution(tmp_path))
    assert not preparation.executable and preparation.draft is None
    assert dict(preparation.census.role_counts)["supported-members"] == 2
    assert dict(preparation.census.resolved_role_counts)["supported-members"] == 3
    assert dict(preparation.census.output_counts)["rejected-members"] == 1
    assert "rubisco.kinetic.supply.compatibility" in {row.code for row in preparation.dependencies}


@pytest.mark.parametrize("change", ("biological", "context", "revision", "query-alias", "question"))
def test_unsupported_specification_changes_refuse_cold(change):
    specification = _specification()
    with pytest.raises(ValueError):
        if change == "biological":
            replace(specification, independent_biological_units=1)
        elif change == "context":
            replace(specification, context=replace(specification.context, temperature_k=Decimal("300")))
        elif change == "revision":
            replace(specification, supply=replace(specification.supply, object_version="9.0.0"))
        elif change == "query-alias":
            replace(specification, source_query=replace(specification.source_query, object_id="query.relabelled-as-fresh"))
        else:
            replace(specification, question="A biological mutant prediction or challenge qualification claim")


@pytest.mark.parametrize("change", ("draft-action", "allocation-role", "source-query", "missing-source", "extra-source"))
def test_instance_validator_refuses_design_decoupling_and_original_source_census_changes(change, tmp_path):
    records = _records()
    specification = _specification(records)
    preparation = _prepare(specification, records, _execution(tmp_path))
    assert validate_kinetic_experiment_instance(specification=specification, allocation=preparation.allocation,
        draft=preparation.draft, source_records=preparation.design_records) is None
    allocation, draft, sources = preparation.allocation, preparation.draft, dict(preparation.design_records)
    if change == "draft-action":
        revised = replace(specification, query=replace(specification.query, co2_um=Decimal("20")))
        draft = _prepare(revised, records, preparation.execution).draft
    elif change == "allocation-role":
        allocation = replace(allocation, roles=(replace(allocation.roles[0], role="biological"),))
    elif change == "source-query":
        sources[specification.source_query.object_id] = replace(records["query"], co2_um=Decimal("20"))
    elif change == "missing-source":
        del sources[specification.material.object_id]
    else:
        sources["source.unselected"] = records["query"]
    with pytest.raises(ValueError, match="kinetic instance"):
        validate_kinetic_experiment_instance(specification=specification, allocation=allocation, draft=draft,
            source_records=tuple(sorted(sources.items())))


def test_public_authoring_rejects_a_draft_decoupled_from_the_selected_specification(tmp_path):
    from tests.test_rubisco_gas_contrast import _real_plane

    records = _records()
    specification = _specification(records)
    selected_root = tmp_path / "decoupling-refusal-custody"
    plane = _real_plane(selected_root)
    resolved = bind_kinetic_experiment_inputs(specification, records)
    execution = _execution(selected_root)
    original = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=execution)
    revised = prepare_experiment(replace(specification, query=replace(specification.query, co2_um=Decimal("20"))),
        scientific_inputs=resolved.scientific_inputs, method_inputs=resolved.method_inputs, execution=execution)
    forged = replace(original, draft=revised.draft, input_records=revised.input_records)
    wave = selected_root / "refused-wave"
    with pytest.raises(ValueError, match="exact derived specification"):
        author_prepared_experiment(preparation=forged, project_root=ROOT, artifact_writer=plane, output_dir=wave)
    assert not wave.exists() or not tuple(wave.iterdir())


def test_public_prepared_experiment_authors_both_gas_queries_without_manual_graph_or_bindings(tmp_path):
    from tests.test_rubisco_gas_contrast import _real_plane

    records = _records()
    first = _specification(records)
    selected_root = tmp_path / "actual-authoring-custody"
    plane = _real_plane(selected_root)
    source_path = _sources(tmp_path / "source-inputs", first, records)
    original_digest = sha256(source_path.read_bytes()).hexdigest()
    for index, query in enumerate((first.query, replace(first.query, co2_um=Decimal("20")))):
        specification = replace(first, query=query)
        resolved = load_experiment_inputs(specification, source_path)
        preparation = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
            method_inputs=resolved.method_inputs, execution=_execution(selected_root))
        wave = selected_root / ("prepared-wave-" + str(index))
        report = author_prepared_experiment(preparation=preparation, project_root=ROOT,
            artifact_writer=plane, output_dir=wave)
        assert report["native_contact"] == "none" and report["status"] == "AUTHORED"
        assert report["specification"] == specification.identity.to_document()
        draft = decode_canonical_bytes((wave / "draft.json").read_bytes(), RecursiveStudyDraft, maximum_bytes=None)
        assert draft == preparation.draft
        assert draft.campaign == records["campaign"]
        packet, retained_draft, _, payloads = load_authored_wave(directory=wave, artifact_writer=plane)
        assert retained_draft == draft
        assert {member.filename for member in packet.members} >= {
            "experiment-specification.json", "experiment-allocation.json", "experiment-instance.json"}
        assert payloads["experiment-specification.json"] == specification.canonical_bytes()
        assert payloads["experiment-allocation.json"] == preparation.allocation.canonical_bytes()
        instance = decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)
        assert instance.specification == specification.identity and instance.allocation == preparation.allocation.identity
        assert instance.sources == tuple(ObjectIdentity.from_record(key, record) for key, record in preparation.design_records)
        for key, record in preparation.design_records:
            name = "experiment-source-" + sha256(key.encode()).hexdigest() + ".json"
            assert payloads[name] == record.canonical_bytes()
        assert not (wave / "completion.json").exists()
    assert sha256(source_path.read_bytes()).hexdigest() == original_digest
