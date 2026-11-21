# SPDX-License-Identifier: MPL-2.0
"""Real durable custody of literal test arrays; no molecular backend execution."""
from empirical_lawhood.storage.artifact_sidecars import resolve_artifact_sidecar_bytes

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.disclosed_examples import DisclosedResponseAssumption, disclosed_supply
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_assessment import MolecularPreparationCriteria, assess_molecular_preparation
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_native import MolecularForceProbe, MolecularProbeCensus, capture_force_probe_return, force_probe_request, force_probe_roster, read_force_probe_census, read_force_probe_outcome
from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.execution.native_effects import NativeEffectContact
from empirical_lawhood.execution.native_subwork import NativeSubworkPartialOutput, NativeSubworkState
from tests.rubisco_response_molecular_fixture import chemical_graphs, geometry_files, ligand_bindings, representation
from tests.runtime_platform.test_native_subwork import _plane, _store


@pytest.fixture
def custody(tmp_path):
    source = DisclosedResponseAssumption()
    supplied = disclosed_supply()
    chemistry, graphs = chemical_graphs(supplied.context.chemistry)
    model, topology, coordinates = representation(supplied.case.parent, chemistry, name="molecular.disclosed.force")
    geometry, raw_files = geometry_files(model, topology, coordinates)
    sources = tuple(sorted({model.identity, model.arrays.identity, *model.sources}, key=lambda row: row.object_id))
    probes = tuple(MolecularForceProbe("probe.disclosed." + str(i), model.identity, model.arrays.identity,
        len(model.atoms), source.identity, source.identity, source.identity, sources,
        ("requirement.disclosed.force-method-admission",)) for i in range(3))
    package_sources = (("src/exposed_molecular_probe_fixture.py", "4" * 64),)
    provenance = NumericalProducingProvenance(
        '{"python":"exposed","numpy":"exposed","scipy":"exposed","system":"Linux","machine":"exposed","threadpools":[]}',
        "5" * 64, package_sources, sha256(canonical_json_bytes(package_sources)).hexdigest(), "3" * 40, False)
    requests = tuple(force_probe_request(probe, model, provenance) for probe in probes)
    plane = _plane(tmp_path / "molecular-probe")
    records = ((source.identity, source), *((graph.identity, graph) for graph in graphs),
        (model.identity, model), (model.arrays.identity, model.arrays), (provenance.identity, provenance),
        *((probe.identity, probe) for probe in probes), *((request.identity, request) for request in requests))
    inputs = []
    for identity, value, profile, media in (
            *((identity, record.canonical_bytes(), ArtifactProfile.CANONICAL_JSON, "application/json") for identity, record in records),
            (model.raw_topology, topology, ArtifactProfile.RAW_SOURCE_BYTES, "text/plain"),
            (model.raw_coordinates, coordinates, ArtifactProfile.RAW_SOURCE_BYTES, "text/plain")):
        result = plane.write(ArtifactWriteRequest(identity.object_id, "inputs/" + identity.object_id,
            identity.object_schema, profile, media, "inputs.exposed", "inputs", value,
            VisibilityCeiling.DEVELOPMENT_ONLY, (), OutcomeAccess.DEVELOPMENT_VISIBLE))
        inputs.append(resolve_artifact_sidecar_bytes(plane, plane.root.resolve(result.materialization.relative_path + '.manifest.json', for_write=False).read_bytes()))
    inputs = tuple(sorted(inputs, key=lambda row: row.materialization.materialization_id))
    parent = NativeEffectContact("exposed.molecular", "force.return", "exposed.molecular.force.return.attempt-001",
        ObjectIdentity("plan.exposed", "empirical-lawhood/runtime/development-execution-plan", "1.0.0", "1" * 64),
        ObjectIdentity("force.return", "empirical-lawhood/runtime/execution-task", "1.0.0", "2" * 64),
        provenance.observed_git_head, tuple(row.materialization.materialization_id for row in inputs), ())
    roster, definitions = force_probe_roster(probes, (model,) * 3, provenance,
        parent_contact=parent, input_materialization_ids=parent.input_materialization_ids)
    store = _store(plane, parent, inputs)
    store.parent_contacts.begin(parent)
    store.freeze_roster(roster, definitions=definitions)
    def reader(manifest):
        plane.verify_manifest(manifest)
        return plane.root.resolve(manifest.materialization.relative_path, for_write=False).open("rb")
    criteria = MolecularPreparationCriteria("criteria.disclosed.force", D(100), D("0.01"), source.identity,
        ("requirement.disclosed.force-threshold-support",))
    return SimpleNamespace(model=model, probes=probes, definitions=definitions, roster=roster, provenance=provenance,
        store=store, plane=plane, inputs=inputs, reader=reader, geometry=geometry, raw_files=raw_files, graphs=graphs,
        criteria=criteria, source=source)


def capture(custody, *, gradient, index=0, failed=False):
    entry = custody.store.begin(custody.definitions[index], custody.inputs)
    custody.store.contact(entry)  # Exposed custody marker only; no native function is called.
    returned = capture_force_probe_return(custody.probes[index], custody.model, custody.provenance,
        -1.0, gradient, custody.store, entry)
    custody.store.complete(entry, operational_status=OperationalStatus.FAILED if failed else OperationalStatus.SUCCEEDED,
        cost=InquiryCost(None, None, None), cost_scope="Literal exposed arrays; no measured molecular computation",
        reason_codes=("EXPOSED_CAPTURE_FAILURE",) if failed else ())
    return returned


def report(custody, outcome):
    return assess_molecular_preparation(custody.model, custody.geometry, custody.criteria,
        raw_files=custody.raw_files, assessor_source=custody.source.identity, assessment_id="assessment.disclosed.force",
        ligand_graphs=custody.graphs, ligand_bindings=ligand_bindings(custody.model),
        probe=custody.probes[0], probe_outcome=outcome, reader_for_manifest=custody.reader)


def read(custody, index=0, progress=None):
    return read_force_probe_outcome(custody.probes[index], custody.model, custody.provenance,
        custody.definitions[index], custody.store if progress is None else progress)


def test_actual_complete_retained_force_read_and_assessment_never_reenter(custody, monkeypatch):
    raw = capture(custody, gradient=np.zeros((len(custody.model.atoms), 3)))
    fresh = ExternalNativeSubworkStore(plane=custody.plane, parent_contacts=custody.store.parent_contacts)
    for name in ("begin", "contact", "call_entry", "call_return", "publish_output", "complete"):
        monkeypatch.setattr(fresh, name, lambda *a, **k: pytest.fail("completed reader attempted new effects"))
    outcome = read(custody, progress=fresh)
    assert outcome.returned == raw and outcome.state is NativeSubworkState.COMPLETED
    assert outcome.cost == InquiryCost(None, None, None)
    result = report(custody, outcome)
    assert result.geometry_gate is result.force_gate is A.SATISFIED
    assert result.physical_and_chemical_admission is A.UNEVALUABLE
    assert result.force_integrity.operands[1].retained_values == len(custody.model.atoms) * 3
    assert result.new_native_calls == 0
    with pytest.raises(ValueError, match="exact remaining"):
        replace(result, unresolved_requirement_ids=result.unresolved_requirement_ids[:-1])
    with pytest.raises(ValueError, match="publication|actual completion receipt"):
        wrong = replace(outcome.outputs[0], materialization=replace(outcome.outputs[0].materialization, physical_sha256="b" * 64))
        replace(outcome, outputs=(wrong, *outcome.outputs[1:]))
    with pytest.raises(ValueError, match="drops an available"):
        replace(result, force_integrity=None, force_gate=A.UNEVALUABLE)


@pytest.mark.parametrize("failure", ("nonfinite", "wrong-shape", "large-force", "uncaptured"))
def test_actual_adverse_and_missing_force_returns_stay_in_full_census(custody, failure):
    n = len(custody.model.atoms)
    gradient = np.zeros((n, 3))
    if failure == "nonfinite":
        gradient[-1, 2] = np.nan
    elif failure == "wrong-shape":
        gradient = gradient[:-1]
    elif failure == "large-force":
        gradient[-1, 2] = 0.02
    else:
        gradient = [[0.0, 0.0, 0.0]] * n
    capture(custody, gradient=gradient, failed=failure == "uncaptured")
    outcome = read(custody)
    result = report(custody, outcome)
    assert result.force_gate is (A.UNEVALUABLE if failure == "uncaptured" else A.FALSIFIED)
    assert "requirement.molecular.resolve-force-assessment" in result.unresolved_requirement_ids
    assert result.force_integrity.operands[1].expected_shape == (n, 3)
    assert result.geometry.atom_count == n


def test_complete_frozen_roster_preserves_failed_unknown_and_unentered_calls(custody, monkeypatch):
    entry = custody.store.begin(custody.definitions[0], custody.inputs)
    custody.store.contact(entry)
    custody.store.complete(entry, operational_status=OperationalStatus.FAILED,
        cost=InquiryCost(None, None, None), cost_scope="Exposed known failure; unknown expense",
        reason_codes=("EXPOSED_ERROR",))
    uncertain = custody.store.begin(custody.definitions[1], custody.inputs)
    custody.store.contact(uncertain)
    before = custody.store.inspect(custody.definitions[1])
    for name in ("begin", "contact", "publish_output", "complete"):
        monkeypatch.setattr(custody.store, name, lambda *a, **k: pytest.fail("retained census entered new work"))
    census = read_force_probe_census(custody.probes, (custody.model,) * 3, custody.provenance,
        custody.definitions, custody.store, roster=custody.roster)
    assert tuple(row.state for row in census.outcomes) == (
        NativeSubworkState.COMPLETED, NativeSubworkState.UNKNOWN_COMPLETION, NativeSubworkState.NOT_ENTERED)
    assert census.outcomes[0].completion.operational_status is OperationalStatus.FAILED
    assert all(row.cost == InquiryCost(None, None, None) for row in census.outcomes)
    assert custody.store.inspect(custody.definitions[1]) == before
    assert decode_canonical_bytes(census.canonical_bytes(), MolecularProbeCensus, maximum_bytes=300_000) == census
    with pytest.raises(ValueError, match="frozen selected"):
        replace(census, outcomes=census.outcomes[:-1])
    with pytest.raises(ValueError, match="original selected"):
        read_force_probe_census(custody.probes[:-1], (custody.model,) * 2, custody.provenance,
            custody.definitions[:-1], custody.store, roster=custody.roster)


def test_partial_captured_return_remains_uncertain_and_never_becomes_zero_force(custody):
    entry = custody.store.begin(custody.definitions[0], custody.inputs)
    custody.store.contact(entry)
    original = custody.store.inspect(custody.definitions[0])
    contact = ObjectIdentity.from_record(entry.contact_manifest.logical.logical_artifact_id, original.contact)
    partial = NativeSubworkPartialOutput(custody.definitions[0].identity, contact,
        "raw.gradient", 32, 32, "a" * 64, 7, sha256(b"partial").hexdigest(), ("EXPOSED_TRANSPORT_PREFIX",))
    custody.store.retain_partial_output(entry, partial, (b"partial",))
    outcome = read(custody)
    assert outcome.state is NativeSubworkState.UNKNOWN_COMPLETION and outcome.returned is None
    assert outcome.partial_outputs and outcome.partial_outputs[0].received_size_bytes == 7
    with custody.reader(outcome.partial_output_manifests[0]) as source:
        assert source.read() == b"partial"
    with pytest.raises(ValueError, match="partial-prefix manifest"):
        replace(outcome, partial_output_manifests=())
    result = report(custody, outcome)
    assert result.force_gate is A.UNEVALUABLE
    assert "requirement.molecular.completed-force-custody" in result.unresolved_requirement_ids
