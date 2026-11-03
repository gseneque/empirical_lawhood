# SPDX-License-Identifier: MPL-2.0
"""Actual public E1 allocation before D; exposed software inputs only."""
from dataclasses import fields, replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_records import E1CompactCriterionChoices
from empirical_lawhood.adapters.methods.matrix_researcher_programme import e1_allocation as domain
from empirical_lawhood.api import matrix_programme_e1_allocation as owner
from empirical_lawhood.api.experiment_preparation import derive_experiment_inputs, load_experiment_inputs
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_programme_allocations import MATERIALS, NAMESPACE, census as census  # noqa: F401

ROOT = Path(__file__).parents[1]


def public_e1_case(tmp_path, census, *, design=None, writer=None):
    """Use mathematics only; never prebind through the private C source plan."""
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.api.recursive_operations import operation_storage_codecs
    from tests.runtime_platform.test_native_subwork import _plane
    from tests.test_matrix_programme_scientific_design import build_scientific_design

    design = build_scientific_design() if design is None else design
    writer = _plane(tmp_path / "custody", binary_codecs=operation_storage_codecs()) if writer is None else writer
    copied = Path(writer.root.contract.canonical_path) / "copied-public-e1"
    copied.mkdir()
    criterion_choices = E1CompactCriterionChoices(**{
        field.name: getattr(design.e1_criterion, field.name) for field in fields(E1CompactCriterionChoices)})
    assert not hasattr(criterion_choices, "allocation")
    budget = ResourceBudget(1, owner._process_rss_bytes() + 1024**3, 0, 60, 128 * 1024**2, 128 * 1024**2)
    request = domain.MatrixProgrammeE1AllocationRequest("request.disclosed.public-e1-allocation", NAMESPACE,
        census.identity, MATERIALS[0], design.e1_coordinates, design.e1_factor_rule, criterion_choices, budget)
    implementation = implementation_binding(ROOT)
    execution = ExecutionSelection(4, "environment.disclosed.public-e1",
        ObjectIdentity.from_record("recursive-member.implementation", implementation), writer.root.contract.canonical_path)
    case = SimpleNamespace(design=design, census=census, writer=writer, copied=copied, request=request,
        specification_path=copied / "specification.json", selector_path=copied / "sources.json",
        directory=Path(writer.root.contract.canonical_path) / "public-e1-allocation", execution=execution)
    write_copied(case)
    return case


def write_copied(case):
    case.specification = domain.MatrixProgrammeE1AllocationSpecification(
        "assembly.disclosed.public-e1-allocation", case.request.identity)
    bindings = []
    for key, record in sorted({"request": case.request, "exposure-census": case.census}.items()):
        raw = record.canonical_bytes()
        (case.copied / (key + ".json")).write_bytes(raw)
        bindings.append(ExperimentInputBinding(key, record.identity, key + ".json", len(raw)))
    case.specification_path.write_bytes(case.specification.canonical_bytes())
    case.selector = ExperimentFileInputSelection("sources.disclosed.public-e1-allocation", domain.PROTOCOL_ID,
        tuple(bindings), ())
    case.selector_path.write_bytes(case.selector.canonical_bytes())


def derive(case):
    return derive_experiment_inputs(specification_path=case.specification_path, source_selection_path=case.selector_path,
        project_root=ROOT, artifact_writer=case.writer, metadata_directory=case.directory,
        output_selection_path=case.directory / "inputs/sources.json", execution=case.execution)


@pytest.fixture
def e1_case(tmp_path, census):  # noqa: F811
    return public_e1_case(tmp_path, census)


def inventory(root):
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()}


def test_public_allocation_binds_actual_criterion_without_D_or_private_compiler(e1_case, monkeypatch):
    from collections import Counter
    from empirical_lawhood.api.configuration import validate_configuration
    from tests.test_matrix_programme_allocations import _forbid_acquisition

    case = e1_case
    _forbid_acquisition(monkeypatch)
    monkeypatch.setattr("empirical_lawhood.api.matrix_programme_allocations._source_plan",
        lambda **_: pytest.fail("prospective E1 must not require a prebound D/private whole-programme plan"))
    assert validate_configuration(case.specification_path, consumer="matrix-programme-e1-allocation")["status"] == "VALIDATED"
    before_inputs = load_experiment_inputs(case.specification, case.selector_path).method_inputs
    assert before_inputs.allocation is None and before_inputs.criterion is None
    assert not hasattr(before_inputs.request, "scientific_design")
    result = derive(case)
    actual = load_experiment_inputs(case.specification, result.source_selection_path).method_inputs
    assert actual.request == case.request and actual.census == case.census
    assert actual.allocation.coordinates == case.design.e1_coordinates
    actual.criterion.validate_allocation(actual.allocation, case.design.e1_factor_rule)
    assert actual.criterion == replace(case.design.e1_criterion, allocation=domain.identity(actual.allocation))
    by_coordinate = {domain.coordinate_identity(value): value.family_id for value in case.design.e1_coordinates}
    assert Counter(by_coordinate[row.coordinate] for row in actual.allocation.roots) == {
        value.family_id: value.requested_roots for value in case.request.criterion_choices.family_requirements}
    assert result.preparation.draft is None and result.preparation.census.native_effect_count == 0
    assert {value.code for value in result.preparation.dependencies} == {"programme-e1-allocation.use-criterion"}
    requirement = result.requirements_publication.materialization.relative_path
    body = json.loads(case.writer.root.resolve(requirement, for_write=False).read_bytes())["value"]
    assert body["native_contact"] == body["scientific_authority"] == "NONE"
    assert body["qualification"] == "NOT_ESTABLISHED"
    assert body["allocation"] == actual.criterion.allocation.to_document()
    assert body["criterion"] == actual.criterion.identity.to_document()
    before = inventory(Path(case.writer.root.contract.canonical_path))
    assert derive(case) == result
    assert inventory(Path(case.writer.root.contract.canonical_path)) == before


@pytest.mark.parametrize("field", ("source_scan_bytes", "memory_bytes", "output_bytes"))
def test_public_e1_resource_refusal_precedes_allocation_and_publication(e1_case, monkeypatch, field):
    case = e1_case
    case.request = replace(case.request, metadata_budget=replace(case.request.metadata_budget, **{field: 1}))
    write_copied(case)
    monkeypatch.setattr(domain, "e1_allocation", lambda **_: pytest.fail("resource refusal constructed roots"))
    root = Path(case.writer.root.contract.canonical_path)
    before = inventory(root)
    with pytest.raises(ValueError, match="memory|source|output-byte"):
        derive(case)
    assert inventory(root) == before and not case.directory.exists()


@pytest.mark.parametrize("damage", ("census", "risk-window", "exposed-group", "exposed-stream"))
def test_public_e1_invalid_originals_refuse_before_publication(e1_case, damage):
    case = e1_case
    if damage == "census":
        case.request = replace(case.request, exposure_census=replace(case.census.identity, object_fingerprint="a" * 64))
    elif damage == "risk-window":
        case.request = replace(case.request, criterion_choices=replace(case.request.criterion_choices,
            occurrence_end_tick=case.request.factor_rule.lattice[-1] + 1,
            survival_origin_end_tick=case.request.factor_rule.lattice[-1] + 1))
    else:
        group = "group." + case.request.namespace + ".e1.0.000"
        if damage == "exposed-group":
            case.census = replace(case.census, exposed_independent_groups=tuple(sorted({
                *case.census.exposed_independent_groups, group})))
        else:
            seed = domain.ordinary_streams(case.request.root_seed_material_sha256, group)[0].effective_seed
            case.census = replace(case.census, effective_seed_exclusions=tuple(sorted({
                *case.census.effective_seed_exclusions, seed})))
        case.request = replace(case.request, exposure_census=case.census.identity)
    write_copied(case)
    root = Path(case.writer.root.contract.canonical_path)
    before = inventory(root)
    with pytest.raises((ValueError, PermissionError), match="census|risk|duration|exposed|collide"):
        derive(case)
    assert inventory(root) == before and not case.directory.exists()


@pytest.mark.parametrize("moment", ("before-final-guard", "during-publication"))
@pytest.mark.parametrize("operand", ("request", "sources"))
def test_public_e1_original_byte_guard_survives_dependent_publication(e1_case, monkeypatch, moment, operand):
    case = e1_case
    original = case.copied / (operand + ".json")
    raw = original.read_bytes()
    def mutate():
        original.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    if moment == "before-final-guard":
        size_check = owner._metadata_record_size
        def checked(*args, **kwargs):
            result = size_check(*args, **kwargs)
            mutate()
            return result
        monkeypatch.setattr(owner, "_metadata_record_size", checked)
    else:
        publish = case.writer.write_batch
        def changed(requests):
            result = publish(requests)
            mutate()
            return result
        monkeypatch.setattr(case.writer, "write_batch", changed)
    with pytest.raises(ValueError, match="copied input changed"):
        derive(case)
    if moment == "before-final-guard":
        assert not case.directory.exists()


def test_cold_e1_output_binding_refuses_substituted_stream_with_consistently_rebound_criterion(e1_case):
    case = e1_case
    result = derive(case)
    actual = load_experiment_inputs(case.specification, result.source_selection_path).method_inputs
    first, *rest = actual.allocation.roots
    stream, *other = first.streams
    changed = replace(actual.allocation, roots=(replace(first, streams=(
        replace(stream, digest_sha256="e" * 64), *other)), *rest))
    criterion = case.request.criterion_choices.bind_allocation(changed, case.request.factor_rule)
    with pytest.raises(ValueError, match="assigned stream"):
        domain.bind_inputs(case.specification, {"request": case.request, "exposure-census": case.census,
            "allocation": changed, "criterion": criterion})
