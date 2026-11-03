# SPDX-License-Identifier: MPL-2.0
"""Cold companion custody over exposed synthetic source/authority fixtures only.

The existing generic prospective fixture uses truth-known software science and
synthetic authority scaffolding. No genuine signer, native task, scientific
execution, qualification or protected real source is used by these tests.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.api import prospective_experiment as owner
from empirical_lawhood.api import recursive_prospective_authoring as prospective
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import (
    ExecutionSelection, ExperimentCensus, ExperimentInstanceBinding, ExperimentPreparation,
    ExperimentProtocolDeclaration, PreparedExperimentFile, PreparedExperimentInputs,
)
from empirical_lawhood.runtime.prospective_experiment import (
    ASSOCIATION_FILENAME, ProspectiveExperimentAssociation, source_filename,
)
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig
from tests.runtime_platform.test_recursive_compiler import Config
from tests.runtime_platform.test_recursive_prospective_workflow import FixtureCanonicalSource, _authored_handoff_fixture, _registrations


@dataclass(frozen=True, slots=True)
class FixtureSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/prospective-experiment-specification"
    specification_id: str
    question: str
    scalar: int
    source_config: ObjectIdentity

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def _allocation(draft, config):
    source = ObjectIdentity.from_record(config.config_id, config)
    rows = sorted((*((unit, "development") for unit in draft.prospective_draft.development_unit_ids),
        *((unit, "evaluation") for unit in draft.prospective_draft.evaluation_unit_ids)))
    return UnitAllocation("allocation.synthetic-prospective-experiment", (source,),
        tuple(IndependentUnit(unit, source.object_id, "family.synthetic-fixture", (), role == "development") for unit, role in rows),
        tuple(UnitRoleAssignment(unit, role) for unit, role in rows))


def _validate_instance(*, specification, allocation, draft, source_records):
    """Independently derive the explicit synthetic selection's design joins."""
    if (type(specification) is not FixtureSpecification or len(source_records) != 1
            or type(source_records[0][1]) is not SourceMaterializationConfig):
        raise ValueError("synthetic experiment loses its original source-config census")
    key, config = source_records[0]
    if (key != config.config_id or specification.source_config != ObjectIdentity.from_record(key, config)
            or specification.question != draft.question or allocation != _allocation(draft, config)
            or {row.source_config_sha256 for row in draft.prospective_draft.source_materializations} != {config.fingerprint()}
            or any(decode_canonical_bytes(row.config_payload.encode(), Config, maximum_bytes=None).scalar != specification.scalar
                for row in draft.operations)):
        raise ValueError("synthetic experiment instance differs from its original scientific selection")


@pytest.fixture(scope="module")
def selected(tmp_path_factory, request):
    root = tmp_path_factory.mktemp("prospective-experiment-custody")
    patch = pytest.MonkeyPatch()
    try:
        parts = _authored_handoff_fixture(root, patch, worker_memory_bytes=getattr(request, "param", None))
        handoff, factories, discovery, plane, raw, *_ = parts
        spec = decode_canonical_bytes((handoff.directory / "recursive-prospective.json").read_bytes(),
            RecursiveProspectiveAuthoringSpec, maximum_bytes=None)
        digest = spec.draft.prospective_draft.source_materializations[0].source_config_sha256
        config = decode_canonical_bytes(plane.root.resolve("candidate-inputs/sha256/" + digest[:2] + "/" + digest,
            for_write=False).read_bytes(), SourceMaterializationConfig, maximum_bytes=None)
        specification = FixtureSpecification("specification.synthetic-prospective-experiment", spec.draft.question, 3,
            ObjectIdentity.from_record(config.config_id, config))
        allocation = _allocation(spec.draft, config)
        external, = spec.draft.external_inputs
        path = root / "original-synthetic-source.json"
        path.write_bytes(raw)
        selected_file = PreparedExperimentFile(ArtifactIdentity(external.logical_artifact_id, "source", external.payload_schema,
            sha256(raw).hexdigest(), external.media_type, len(raw)), "1.0.0", path, len(raw))
        closure = prospective.capture_target_closure(root / "checkout", spec.spec_id + ".source-closure").closure
        execution = ExecutionSelection(workers=1, environment_id="synthetic-locked-test", source_snapshot=ObjectIdentity.from_record(
            "recursive-member.implementation", closure), output_root=plane.root.contract.canonical_path)
        preparation = ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0), (),
            allocation=allocation, draft=spec.draft, execution=execution, specification_record=specification,
            design_records=((config.config_id, config),), input_files=((external.input_id, selected_file),))
        declaration = ExperimentProtocolDeclaration("synthetic.prospective-experiment", FixtureSpecification,
            lambda *_args, **_kwargs: preparation, "synthetic-prospective-experiment",
            input_record_types=(SourceMaterializationConfig,), bind_inputs=lambda *_args: PreparedExperimentInputs({}),
            validate_instance=_validate_instance, input_file_record_types=(FixtureCanonicalSource,))
        from empirical_lawhood.adapters.composition import generated_extension_bundles as generated
        patch.setattr(generated, "EXPERIMENT_PROTOCOL_DECLARATIONS", (declaration,))
        patch.setattr(owner, "capture_target_closure", prospective.capture_target_closure)
        patch.setattr(owner, "GitStudySourceClosureInspector", prospective.GitStudySourceClosureInspector)
        composition = (_registrations(handoff.compilation), handoff.compilation.registry, handoff.compilation.output_codecs)
        from empirical_lawhood.api import recursive_operations
        patch.setattr(recursive_operations, "operation_catalog", lambda: composition)

        def api_factory(*, repo_root, candidate_context_provider, candidate_capability_catalog):
            from empirical_lawhood.api.facade import EmpiricalLawhoodApi
            from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY
            return EmpiricalLawhoodApi(repo_root=repo_root, external_root=None, candidate_context_provider=candidate_context_provider,
                candidate_capability_catalog=candidate_capability_catalog, extension_bundle_aggregate=discovery,
                executable_binding_aggregate=factories.aggregate, executable_factory_registry=factories,
                study_extension_codec_registry=EXECUTABLE_CANONICAL_RECORD_CODEC_REGISTRY)

        destination = Path(plane.root.contract.canonical_path) / "experiment-programme"
        report = owner.author_prepared_prospective_experiment(preparation=preparation, prospective_spec=spec,
            source_configs=(config,), project_root=root / "checkout", artifact_writer=plane, output_dir=destination,
            composition=composition, api_factory=api_factory, candidate_catalog=discovery.candidate_capability_catalog)
        yield SimpleNamespace(root=root, plane=plane, directory=destination, preparation=preparation, prospective_spec=spec,
            config=config, original=handoff, report=report, composition=composition, api_factory=api_factory,
            candidate_catalog=discovery.candidate_capability_catalog, original_parts=parts)
    finally:
        patch.undo()


def _load(selected, **arguments):
    return owner.load_prepared_prospective_experiment(directory=selected.directory, project_root=selected.root / "checkout",
        storage_profile=object(), artifact_writer=selected.plane, composition=selected.composition,
        candidate_catalog=selected.candidate_catalog, **arguments)


def test_actual_prospective_owner_and_closed_companion_preserve_original_bytes(selected):
    loaded = _load(selected)
    old = decode_canonical_bytes((selected.original.directory / "authored-wave.json").read_bytes(), AuthoredRecursiveWave, maximum_bytes=None)
    new = decode_canonical_bytes((selected.directory / "prospective/authored-wave.json").read_bytes(), AuthoredRecursiveWave, maximum_bytes=None)
    assert len(old.members) == len(new.members) == 14
    assert old.canonical_bytes() == new.canonical_bytes()
    for member in old.members:
        assert (selected.original.directory / member.filename).read_bytes() == (selected.directory / "prospective" / member.filename).read_bytes()
    assert loaded.specification == selected.preparation.specification_record
    assert loaded.allocation == selected.preparation.allocation
    assert loaded.design_records == selected.preparation.design_records
    assert loaded.association.candidate == ObjectIdentity.from_record(loaded.candidate.candidate_id, loaded.candidate)
    assert loaded.instance.specification == selected.preparation.specification
    assert selected.report["scientific_authority"] == "NONE" and selected.report["native_contact"] == "none"
    assert len(loaded.association.members) == 4


def test_selected_owning_loader_is_called_first_on_every_cold_load(selected):
    calls = []

    def loader(**arguments):
        calls.append(arguments["directory"])
        return prospective.load_recursive_prospective_handoff(**arguments)

    assert _load(selected, handoff_loader=loader).association == _load(selected, handoff_loader=loader).association
    assert calls == [selected.directory / "prospective"] * 2


@pytest.mark.parametrize("damage", ("missing", "extra", "duplicate", "namespace-alias", "development-snapshot", "snapshot-role", "other-draft"))
def test_author_refuses_incomplete_or_aliased_selection_before_publication(selected, monkeypatch, damage):
    preparation, spec, configs = selected.preparation, selected.prospective_spec, (selected.config,)
    if damage == "missing":
        configs = ()
    elif damage == "extra":
        configs = (*configs, replace(selected.config, config_id="config.unselected-extra"))
    elif damage == "duplicate":
        configs = configs * 2
    elif damage == "namespace-alias":
        external, = spec.draft.external_inputs
        changed = replace(external, logical_artifact_id=selected.config.fingerprint())
        draft = replace(spec.draft, external_inputs=(changed,))
        files = tuple((key, replace(value, identity=replace(value.identity, artifact_id=changed.logical_artifact_id)))
            for key, value in preparation.input_files)
        preparation = replace(preparation, draft=draft, input_files=files)
        spec = replace(spec, draft=draft, external_operands=tuple(replace(row,
            logical_artifact_id=changed.logical_artifact_id) for row in spec.external_operands))
    elif damage in ("development-snapshot", "snapshot-role"):
        snapshot = replace(preparation.execution.source_snapshot, **({"object_schema": "empirical-lawhood/runtime/recursive-implementation-binding"}
            if damage == "development-snapshot" else {"object_id": "unrelated.source-role"}))
        preparation = replace(preparation, execution=replace(preparation.execution, source_snapshot=snapshot))
    else:
        spec = replace(spec, draft=replace(spec.draft, question="Unselected scientific question"))
    monkeypatch.setattr(selected.plane, "write", lambda *_args: pytest.fail("refused author reached publication"))
    with pytest.raises((ValueError, TypeError)):
        owner.author_prepared_prospective_experiment(preparation=preparation, prospective_spec=spec, source_configs=configs,
            project_root=selected.root / "checkout", artifact_writer=selected.plane,
            output_dir=Path(selected.plane.root.contract.canonical_path) / ("refused-" + damage),
            composition=selected.composition, api_factory=selected.api_factory, candidate_catalog=selected.candidate_catalog)


@pytest.mark.parametrize("failure", ("association-publication", "source-change"))
def test_interrupted_publication_never_commits_an_experiment_association(selected, monkeypatch, failure):
    destination = Path(selected.plane.root.contract.canonical_path) / failure
    observed = []
    if failure == "association-publication":
        original_write = selected.plane.write

        def write(request):
            observed.append(request.payload_schema)
            if request.payload_schema == ProspectiveExperimentAssociation.SCHEMA:
                raise OSError("exposed simulated association publication failure")
            return original_write(request)

        monkeypatch.setattr(selected.plane, "write", write)
    else:
        monkeypatch.setattr(prospective, "GitStudySourceClosureInspector", lambda *_args:
            SimpleNamespace(observe=lambda closure: replace(closure, source_tree_sha256="f"*64)))
    with pytest.raises((ValueError, OSError), match="association publication failure|producing source changed|selected producing source"):
        owner.author_prepared_prospective_experiment(preparation=selected.preparation, prospective_spec=selected.prospective_spec,
            source_configs=(selected.config,), project_root=selected.root / "checkout", artifact_writer=selected.plane,
            output_dir=destination, composition=selected.composition, api_factory=selected.api_factory,
            candidate_catalog=selected.candidate_catalog)
    assert (destination / "prospective/authored-wave.json").is_file() == (failure == "association-publication")
    assert not (destination / "experiment" / ASSOCIATION_FILENAME).exists()
    assert not (destination / "experiment" / (ASSOCIATION_FILENAME + ".manifest.json")).exists()
    if observed:
        assert observed[-1] == ProspectiveExperimentAssociation.SCHEMA
        assert set(observed[-5:-1]) == {FixtureSpecification.SCHEMA, UnitAllocation.SCHEMA,
            ExperimentInstanceBinding.SCHEMA, SourceMaterializationConfig.SCHEMA}


@pytest.mark.parametrize("damage", (None, "specification", "allocation", "source", "source-revision", "member-revision", "draft", "projection", "outer-candidate", "instance-role", "implementation-role", "missing-member", "extra-file"))
def test_cold_loader_refuses_consistently_republished_changed_design(selected, tmp_path, damage):
    from tests.test_recursive_public_service import _plane

    plane = _plane(tmp_path / "changed-custody")
    companion = Path(plane.root.contract.canonical_path) / "selected/experiment"
    companion.mkdir(parents=True)
    original = decode_canonical_bytes((selected.directory / "experiment" / ASSOCIATION_FILENAME).read_bytes(),
        ProspectiveExperimentAssociation, maximum_bytes=None)
    payloads = {row.filename: (selected.directory / "experiment" / row.filename).read_bytes() for row in original.members}
    instance = decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)
    identities = {row.filename: row.identity for row in original.members}
    association = original
    if damage == "specification":
        record = replace(selected.preparation.specification_record, scalar=4)
        payloads["experiment-specification.json"] = record.canonical_bytes()
        instance = replace(instance, specification=record.identity)
        identities["experiment-specification.json"] = record.identity
    elif damage == "allocation":
        record = replace(selected.preparation.allocation,
            units=tuple(replace(row, exposed=not row.exposed) for row in selected.preparation.allocation.units))
        payloads["experiment-allocation.json"] = record.canonical_bytes()
        instance = replace(instance, allocation=record.identity)
        identities["experiment-allocation.json"] = record.identity
    elif damage == "source":
        record = replace(selected.config, expected_size_bytes=selected.config.expected_size_bytes - 1)
        reference = ObjectIdentity.from_record(record.config_id, record)
        payloads[source_filename(reference)] = record.canonical_bytes()
        instance = replace(instance, sources=(reference,))
        identities[source_filename(reference)] = reference
    elif damage == "source-revision":
        reference = replace(instance.sources[0], object_version="9.0.0")
        instance = replace(instance, sources=(reference,))
        identities[source_filename(reference)] = reference
    elif damage == "member-revision":
        reference = replace(instance.sources[0], object_version="9.0.0")
        identities[source_filename(reference)] = reference
    elif damage == "projection":
        instance = replace(instance, scientific_projection=replace(instance.scientific_projection, object_fingerprint="f" * 64))
    elif damage == "outer-candidate":
        association = replace(association, candidate=replace(association.candidate, object_id="candidate.unrelated-outer"))
    elif damage == "missing-member":
        name = source_filename(instance.sources[0])
        payloads.pop(name)
        identities.pop(name)
    payloads["experiment-instance.json"] = instance.canonical_bytes()
    instance_role = "instance.unrelated-original-design-role" if damage == "instance-role" else original.instance.object_id
    identities["experiment-instance.json"] = ObjectIdentity.from_record(instance_role, instance)
    members = tuple(RecursiveWaveMember(name, identities[name], len(raw)) for name, raw in sorted(payloads.items()))
    association = replace(association, instance=identities["experiment-instance.json"], members=members)
    packet = decode_canonical_bytes((selected.directory / "prospective/authored-wave.json").read_bytes(),
        AuthoredRecursiveWave, maximum_bytes=None)
    prospective_payloads = {row.filename: (selected.directory / "prospective" / row.filename).read_bytes() for row in packet.members}
    if damage == "draft":
        changed = replace(selected.prospective_spec.draft, question="Consistently republished unselected scientific draft")
        prospective_payloads["draft.json"] = changed.canonical_bytes()
        members = tuple(replace(row, identity=ObjectIdentity.from_record(changed.draft_id, changed),
            size_bytes=len(changed.canonical_bytes())) if row.filename == "draft.json" else row for row in packet.members)
        packet = replace(packet, draft=ObjectIdentity.from_record(changed.draft_id, changed), members=members)
    elif damage == "implementation-role":
        reference = replace(packet.implementation, object_id="implementation.unrelated-source-role")
        packet = replace(packet, implementation=reference, members=tuple(replace(row, identity=reference)
            if row.filename == "implementation.json" else row for row in packet.members))
    association = replace(association, prospective_wave=ObjectIdentity.from_record(packet.packet_id, packet))
    for name, raw in (*sorted(payloads.items()), (ASSOCIATION_FILENAME, association.canonical_bytes())):
        plane.write(ArtifactWriteRequest(association.association_id + "." + name.removesuffix(".json"), "selected/experiment/" + name,
            json.loads(raw)["schema"], ArtifactProfile.CANONICAL_JSON, "application/json", association.association_id,
            "selected/experiment", raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        plane.verify_manifest(decode_artifact_manifest((companion / (name + ".manifest.json")).read_bytes(), maximum_bytes=None))
    if damage == "extra-file":
        (companion / "unselected.json").write_bytes(b"{}\n")
    # Re-publish all original14 control records and the original packet through
    # real custody, then invoke the actual owning cold loader. No guard is
    # mocked and the old package stays byte-for-byte untouched.
    prospective_dir = companion.parent / "prospective"
    prospective_dir.mkdir()
    for name in (*(row.filename for row in packet.members), "authored-wave.json"):
        raw = packet.canonical_bytes() if name == "authored-wave.json" else prospective_payloads[name]
        plane.write(ArtifactWriteRequest(packet.packet_id + "." + name.removesuffix(".json"), "selected/prospective/" + name,
            json.loads(raw)["schema"], ArtifactProfile.CANONICAL_JSON, "application/json", packet.packet_id,
            "selected/prospective", raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    # Exact-source handoffs also retain these two operational provenance records
    # beside the unchanged fourteen-member packet. Republish the original typed
    # bytes through real custody so mutations reach their own scientific guards.
    assert len(packet.members) == 14
    closure = decode_canonical_bytes(prospective_payloads["source-closure.json"],
        prospective.ImplementationSourceClosure, maximum_bytes=prospective.MAXIMUM_SPEC_BYTES)
    relative = "selected/prospective/provenance"
    for name, kind in zip(prospective.SOURCE_PROVENANCE_MEMBERS,
            (prospective.SelectedSourceManifest, prospective.ProspectiveSourceObservation), strict=True):
        raw = (selected.directory / "prospective/provenance" / name).read_bytes()
        record = decode_canonical_bytes(raw, kind, maximum_bytes=prospective.MAXIMUM_SPEC_BYTES)
        assert record.canonical_bytes() == raw
        plane.write(ArtifactWriteRequest(closure.source_closure_id + ".provenance." + name.removesuffix(".json"),
            relative + "/" + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            closure.source_closure_id + ".provenance", relative, raw,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
    arguments = dict(directory=companion.parent, project_root=selected.root / "checkout", storage_profile=object(),
        artifact_writer=plane, composition=selected.composition, candidate_catalog=selected.candidate_catalog)
    if damage is None:
        assert owner.load_prepared_prospective_experiment(**arguments).association == original
    else:
        reasons = {"specification": "prospective bootstrap substitutes its original instance association", "allocation": "synthetic experiment instance",
            "source": "original source|synthetic experiment instance", "source-revision": "codec/revision",
            "member-revision": "substitutes its exact original", "projection": "design/scientific projection",
            "draft": "scientific or producing implementation root",
            "instance-role": "prospective bootstrap substitutes its original instance association", "implementation-role": "source-closure role or identity",
            "outer-candidate": "another wave or outer candidate", "missing-member": "omits or adds an original source",
            "extra-file": "closed complete file census"}
        error = PermissionError if damage in ("specification", "instance-role") else (ValueError, TypeError, KeyError)
        with pytest.raises(error, match=reasons[damage]):
            owner.load_prepared_prospective_experiment(**arguments)
