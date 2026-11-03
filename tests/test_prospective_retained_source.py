# SPDX-License-Identifier: MPL-2.0
"""Original custody reads and recovery loading across current source changes.

The original public fixture uses disclosed software data and synthetic authority.
These controls perform no worker execution or native scientific acquisition.
"""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import prospective_experiment as experiment
from empirical_lawhood.api import recursive_prospective_authoring as recursive
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.results import ApiResult, CampaignStatusRequest, OperationStatus, RunCampaignRequest
from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactIdentityConflict
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.prospective_experiment import ALLOCATION_FILENAME, SPECIFICATION_FILENAME
from tests.test_prospective_experiment import _load, selected  # noqa: F401


def _read(case):
    return experiment.load_retained_prospective_experiment(directory=case.directory,
        project_root=case.root / "checkout", storage_profile=object(), artifact_writer=case.plane)


def _unavailable_checkout(*_args, **_kwargs):
    raise PermissionError("current checkout is dirty, changed or unavailable")


def _block_current_source(monkeypatch):
    for module in (recursive, experiment):
        monkeypatch.setattr(module, "capture_target_closure", _unavailable_checkout)
        monkeypatch.setattr(module, "GitStudySourceClosureInspector",
            lambda *_args: SimpleNamespace(observe=_unavailable_checkout))


def test_retained_read_authenticates_originals_without_current_source_or_operations(selected, monkeypatch):  # noqa: F811
    original = _load(selected)
    original_bytes = {path.relative_to(selected.directory).as_posix(): path.read_bytes()
        for path in selected.directory.rglob("*") if path.is_file()}
    _block_current_source(monkeypatch)
    monkeypatch.setattr(recursive, "_compile", lambda *_args, **_kwargs:
        pytest.fail("retained read recompiled current operation declarations"))
    from empirical_lawhood.api import experiment_preparation, recursive_operations
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    monkeypatch.setattr(recursive_operations, "operation_catalog", lambda:
        pytest.fail("retained read inspected changed current operation declarations"))
    # Static code-owned protocol metadata selects the closed original-access
    # bootstrap. It creates no provider, execution or selected-source admission.
    static_lookups = []
    protocols = experiment_preparation.experiment_protocols
    def selected_protocols():
        declarations = protocols()
        static_lookups.append(tuple((row.specification_type.SCHEMA, row.specification_type.VERSION)
            for row in declarations))
        return declarations
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", selected_protocols)
    monkeypatch.setattr(recursive, "RecursiveCandidateContextProvider", lambda *_args, **_kwargs:
        pytest.fail("retained read constructed a current context provider"))
    monkeypatch.setattr(recursive, "CandidateSourceResolutionService", lambda *_args, **_kwargs:
        pytest.fail("retained read constructed current source resolution"))
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *_args, **_kwargs:
        pytest.fail("retained read executed a runtime task"))
    retained = _read(selected)
    assert static_lookups == [((selected.preparation.specification.object_schema,
        selected.preparation.specification.object_version),)]
    assert retained.association == original.association
    assert retained.instance == original.instance
    assert retained.candidate == original.candidate
    assert retained.projection == original.handoff.projection
    assert retained.draft == original.handoff.compilation.draft
    assert ObjectIdentity.from_record("recursive-member.implementation", retained.implementation) == selected.preparation.execution.source_snapshot
    assert retained.payloads[SPECIFICATION_FILENAME] == selected.preparation.specification_record.canonical_bytes()
    assert retained.payloads[ALLOCATION_FILENAME] == selected.preparation.allocation.canonical_bytes()
    with pytest.raises(TypeError):
        retained.payloads[SPECIFICATION_FILENAME] = b"substitution"
    assert {path.relative_to(selected.directory).as_posix(): path.read_bytes()
        for path in selected.directory.rglob("*") if path.is_file()} == original_bytes



def test_retained_reader_decodes_roots_once_but_authenticates_all_members_on_each_read(selected, monkeypatch):  # noqa: F811
    original = _read(selected)
    packet = recursive.decode_canonical_bytes((selected.directory / "prospective/authored-wave.json").read_bytes(),
        recursive.AuthoredRecursiveWave, maximum_bytes=None)
    members = {row.filename: row for row in packet.members}
    decoder_kind, _ = recursive._prospective_member_codec(members["decoder.json"])
    decoder = recursive.decode_canonical_bytes((selected.directory / "prospective/decoder.json").read_bytes(),
        decoder_kind, maximum_bytes=None)
    original_bytes = {row.filename: (selected.directory / "prospective" / row.filename).read_bytes()
        for row in packet.members}
    decoded, authenticated = Counter(), Counter()
    actual_decode = recursive.decode_canonical_bytes
    actual_verify = selected.plane.verify_manifest

    def decode(raw, kind, **arguments):
        decoded[kind.SCHEMA, sha256(raw).hexdigest()] += 1
        return actual_decode(raw, kind, **arguments)

    def verify(manifest):
        authenticated[manifest.materialization.relative_path] += 1
        return actual_verify(manifest)

    monkeypatch.setattr(recursive, "decode_canonical_bytes", decode)
    monkeypatch.setattr(selected.plane, "verify_manifest", verify)
    for _ in range(2):
        decoded.clear()
        authenticated.clear()
        retained = _read(selected)
        assert retained == original
        # Standalone draft/implementation duplicates are authenticated against
        # the reconstructed roots rather than decoded into discarded trees.
        for name in ("recursive-prospective.json", "decoder.json", "source-closure.json"):
            kind, _ = recursive._prospective_member_codec(members[name], decoder_registration=decoder)
            assert decoded[kind.SCHEMA, sha256(original_bytes[name]).hexdigest()] == 1
        draft_schema = members["draft.json"].identity.object_schema
        assert decoded[draft_schema, sha256(original_bytes["draft.json"]).hexdigest()] == 0
        implementation_schema = members["implementation.json"].identity.object_schema
        assert decoded[implementation_schema, sha256(original_bytes["implementation.json"]).hexdigest()] == 1
        # The report already contains the strict typed candidate and authoring;
        # the reconstructed spec contains the resources. Their separate files
        # must still authenticate, without allocating another decoded tree.
        for name in ("candidate.json", "authoring.json", "resources.json"):
            kind, _ = recursive._prospective_member_codec(members[name], decoder_registration=decoder)
            assert decoded[kind.SCHEMA, sha256(original_bytes[name]).hexdigest()] == 0
        kind, _ = recursive._prospective_member_codec(members["candidate-report.json"], decoder_registration=decoder)
        assert decoded[kind.SCHEMA, sha256(original_bytes["candidate-report.json"]).hexdigest()] == 1
        for name in members:
            relative = (selected.directory / "prospective" / name).relative_to(
                Path(selected.plane.root.contract.canonical_path)).as_posix()
            assert authenticated[relative] >= 1
    assert {name: (selected.directory / "prospective" / name).read_bytes() for name in members} == original_bytes

def test_fresh_handoff_stays_strict_while_recovery_load_preserves_original_source(selected, monkeypatch):  # noqa: F811
    original = _load(selected)
    _block_current_source(monkeypatch)
    with pytest.raises(PermissionError, match="current checkout"):
        _load(selected)
    recovered = _load(selected, require_current_source=False)
    assert (recovered.association, recovered.instance, recovered.candidate, recovered.specification,
        recovered.allocation, recovered.design_records) == (original.association, original.instance,
        original.candidate, original.specification, original.allocation, original.design_records)
    assert recovered.handoff.authoring == original.handoff.authoring
    assert recovered.handoff.projection == original.handoff.projection
    assert recovered.handoff.resources == original.handoff.resources
    assert recovered.association.candidate == ObjectIdentity.from_record(original.candidate.candidate_id, original.candidate)


def test_changed_current_commit_does_not_replace_retained_source_pin(selected, monkeypatch):  # noqa: F811
    original = _read(selected)
    changed = replace(original.implementation, implementation_commit="b" * 40, source_tree_sha256="c" * 64)
    monkeypatch.setattr(recursive, "GitStudySourceClosureInspector",
        lambda *_args: SimpleNamespace(observe=lambda _expected: changed))
    with pytest.raises(ValueError, match="selected source checkout"):
        _load(selected)
    recovered = _load(selected, require_current_source=False)
    retained = _read(selected)
    assert retained.implementation == original.implementation
    assert recovered.candidate == original.candidate == retained.candidate
    assert retained.implementation != changed


def test_recovery_current_manifest_drift_refuses_without_rewriting_candidate(selected, monkeypatch):  # noqa: F811
    candidate_path = selected.directory / "prospective/candidate.json"
    before = candidate_path.read_bytes()
    registrations, registry, codecs = selected.composition
    manifest = registry.capabilities[0]
    changed = replace(registry, capabilities=tuple(replace(row, implementation_sha256="f" * 64)
        if row == manifest else row for row in registry.capabilities))
    _block_current_source(monkeypatch)
    with pytest.raises(ValueError, match="implementation differs from the locked registry"):
        experiment.load_prepared_prospective_experiment(directory=selected.directory,
            project_root=selected.root / "checkout", storage_profile=object(), artifact_writer=selected.plane,
            composition=(registrations, changed, codecs), candidate_catalog=selected.candidate_catalog,
            require_current_source=False)
    assert candidate_path.read_bytes() == before
    assert _read(selected).candidate.canonical_bytes() == before


def test_public_read_reaches_status_with_original_candidate_after_source_changes(selected, monkeypatch):  # noqa: F811
    retained = _read(selected)
    calls = []
    scientific_calls = []
    _block_current_source(monkeypatch)
    monkeypatch.setattr(recursive, "_compile", lambda *_args, **_kwargs:
        pytest.fail("public read recompiled changed current operation declarations"))

    def scientific_read(**arguments):
        # This synthetic orchestration fixture has no installed scientific
        # specification reader. Observe that boundary without weakening the
        # production reader's exact-revision admission or fabricating a result.
        scientific_calls.append(arguments)
        return None

    monkeypatch.setattr(
        "empirical_lawhood.api.experiment_scientific_read.read_prepared_experiment_science", scientific_read)

    def status(request, *, expected_candidate):
        calls.append((request, expected_candidate))
        return ApiResult("campaign.status", OperationStatus.SUCCEEDED)

    def factory(**arguments):
        assert arguments["handoff"] is None
        return SimpleNamespace(campaign_status=status)

    service = ExperimentProgrammeService(selected.root / "checkout", selected.plane, SimpleNamespace(maximum_parallel_tasks=1),
        prospective_api_factory=factory)
    request = CampaignStatusRequest("run.synthetic-retained", include_attempt_history=True)
    report = service.read(directory=selected.directory, request=request)
    assert calls == [(request, retained.association.candidate)]
    assert report["status"] == "SUCCEEDED"
    assert report["programme"]["assigned_tasks"] == len(retained.projection.tasks)
    assert report["programme"]["candidate"] == retained.association.candidate.to_document()
    assert report["scientific_result"] is None
    assert len(scientific_calls) == 1
    assert scientific_calls[0]["selected"].association == retained.association
    assert {key: value for key, value in scientific_calls[0].items() if key != "selected"} == {
        "artifact_writer": selected.plane, "run_id": request.run_id,
        "reveal_authority_id": None, "allow_partial": False, "assess_incomplete": False}




def test_public_fresh_run_and_author_still_require_original_selected_source(selected, monkeypatch):  # noqa: F811
    _block_current_source(monkeypatch)

    def loader(**arguments):
        assert arguments.get("require_current_source", True) is True
        return experiment.load_prepared_prospective_experiment(**arguments, composition=selected.composition,
            candidate_catalog=selected.candidate_catalog)

    service = ExperimentProgrammeService(selected.root / "checkout", selected.plane, SimpleNamespace(maximum_parallel_tasks=1), loader,
        lambda **_arguments: pytest.fail("fresh run reached campaign handler after source refusal"))
    with pytest.raises(PermissionError, match="current checkout"):
        service.run(directory=selected.directory, request=RunCampaignRequest(Path("/unused/issued.json"), confirmed=True))
    destination = selected.directory.parent / "refused-current-source"
    with pytest.raises(PermissionError, match="current checkout"):
        experiment.author_prepared_prospective_experiment(preparation=selected.preparation,
            prospective_spec=selected.prospective_spec, source_configs=(selected.config,),
            project_root=selected.root / "checkout", artifact_writer=selected.plane, output_dir=destination,
            composition=selected.composition, api_factory=selected.api_factory, candidate_catalog=selected.candidate_catalog)
    assert not destination.exists()


@pytest.mark.parametrize("member", ("prospective/source-closure.json", "prospective/candidate.json",
    "prospective/authoring.json", "prospective/resources.json", "prospective/candidate-report.json",
    "prospective/draft.json", "prospective/implementation.json", "prospective/recursive-prospective.json",
    "prospective/decoder.json", "experiment/experiment-specification.json"))
def test_retained_read_still_refuses_changed_primary_bytes(selected, monkeypatch, member):  # noqa: F811
    _block_current_source(monkeypatch)
    path = selected.directory / member
    original = path.read_bytes()
    try:
        path.write_bytes(original + b" ")
        with pytest.raises((ValueError, OSError, ArtifactIdentityConflict)):
            _read(selected)
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("member", ("draft.json", "implementation.json", "recursive-prospective.json", "decoder.json", "source-closure.json"))
@pytest.mark.parametrize("suffix", ("", ".manifest.json"))
def test_retained_read_refuses_omitted_already_decoded_members(selected, member, suffix):  # noqa: F811
    _read(selected)
    path = selected.directory / "prospective" / (member + suffix)
    original = path.read_bytes()
    try:
        path.unlink()
        with pytest.raises((ValueError, OSError, ArtifactIdentityConflict)):
            _read(selected)
    finally:
        path.write_bytes(original)


@pytest.mark.parametrize("require_current_source", (None, 0, 1, "retained"))
@pytest.mark.parametrize("owner", (experiment, recursive))
def test_source_mode_requires_explicit_boolean_before_custody(owner, require_current_source):
    arguments = dict(directory="/unused", storage_profile=object(), artifact_writer=object(),
        require_current_source=require_current_source)
    if owner is experiment:
        arguments["project_root"] = "/unused"
        load = owner.load_prepared_prospective_experiment
    else:
        arguments["root"] = "/unused"
        load = owner.load_recursive_prospective_handoff
    with pytest.raises(TypeError, match="explicit boolean"):
        load(**arguments)
