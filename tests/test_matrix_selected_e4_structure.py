# SPDX-License-Identifier: MPL-2.0
"""Ordinary structure composition using explicitly exposed original input seams.

The PURE compiler/workers/receipt reader are real. The original native census
is deliberately unentered fixture data; this is no native lifecycle, source
qualification, reveal, freshness or installed release acceptance proof.
"""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_structure import structural_measurement
from empirical_lawhood.api import selected_e4_structure as ordinary
from empirical_lawhood.api import matrix_full_factor_custody as custody
from empirical_lawhood.api import matrix_full_factor_authoring as author
from empirical_lawhood.api import matrix_full_factor_runtime as runtime
from empirical_lawhood.api import matrix_full_factor_read as reader
from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
from empirical_lawhood.runtime.operational_configuration import scientific_reconstruction_operation
from tests.matrix_e4_structure_support import disclosed_structure, publish_secondary
from tests.test_matrix_e4_full_factor_public import ROOT, _real_plane, _development_access_seam, selected  # noqa: F401
from tests.test_matrix_e4_full_factor_values import scopes  # noqa: F401
from tests.test_matrix_selected_e4_bank_recipe import literal_recipe_source_inputs  # noqa: F401


@pytest.mark.parametrize("change", ("factor", "numerical", "secondary"))
def test_ordinary_structural_binding_refuses_changed_original_mathematics(selected, change):  # noqa: F811
    choices, _ = disclosed_structure(selected.bank, budget=dict(selected.resources.phase_budgets)["measure"])
    if change == "factor":
        choices = replace(choices, factor_rule=replace(choices.factor_rule,
            primary_dt=choices.factor_rule.primary_dt * 2))
    elif change == "numerical":
        choices = replace(choices, numerical_design=replace(choices.numerical_design,
            scalar_tolerance=choices.numerical_design.scalar_tolerance + Decimal(".000001")))
    else:
        criterion = replace(choices.secondary_target.mathematical_protocol, protocol_id="criterion.disclosed.changed")
        choices = replace(choices, secondary_target=replace(choices.secondary_target, mathematical_protocol=criterion))
    with pytest.raises(ValueError, match="mathematics|numerical"):
        structural_measurement(programme=selected.programme, bank=selected.bank, choices=choices)


def _files(directory):
    return {path.relative_to(directory).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()}


@scientific_reconstruction_operation('full')
def test_ordinary_dev_produces_reads_and_reuses_structure_without_operator_closeout(selected, tmp_path, monkeypatch):  # noqa: F811
    root = tmp_path / "ordinary-e4-structure-disclosed"
    assert root.is_relative_to(Path("/media/chevre/EL/empirical-lawhood"))
    plane = _real_plane(root)
    directory = root / "ordinary-phase"
    directory.mkdir()
    choices, resources = disclosed_structure(selected.bank, budget=dict(selected.resources.phase_budgets)["measure"])
    target, secondary = publish_secondary(plane, selected.bank, root / "early-secondary")
    scopes_seen = []
    access=_development_access_seam(monkeypatch,selected,plane)
    def original(**kwargs):
        reference = kwargs.get("reference")
        record_id = kwargs.get("record_id", selected.scope.record_id) if reference is None else reference.scope.object_id
        scope = replace(selected.scope, record_id=record_id)
        scopes_seen.append(scope)
        if kwargs.get("_consume_original_access") is not None:
            kwargs["_consume_original_access"](access,selected.evidence)
        if kwargs.get("_consume_programme_result") is not None:
            kwargs["_consume_programme_result"](observations=(), report={
                "state": "DISCLOSED_UNENTERED_ORIGINAL_FIXTURE", "new_native_contact_count": 0})
        if kwargs.get("_consume_functional") is not None:
            from tests.matrix_e4_structure_support import unentered_dense_functional_rows as dense_e4_functional_rows
            for case in scope.original_cases:
                kwargs["_consume_functional"](dense_e4_functional_rows(selected.bank, case, None, dense_score=None, target=target, secondary=secondary))
        return scope, ()
    monkeypatch.setattr(custody, "derive_original_full_factor_scope", original)
    monkeypatch.setattr(author, "authenticate_original_full_factor_scope", lambda **kwargs: ())
    monkeypatch.setattr(runtime, "authenticate_original_full_factor_reference", original)
    monkeypatch.setattr(reader, "authenticate_original_full_factor_reference", original)
    kwargs = dict(directory=directory, artifact_writer=plane, programme=selected.programme, bank=selected.bank,
        choices=choices, secondary_readout=secondary, resources=resources)
    result = ordinary.produce_selected_e4_structure(**kwargs, project_root=ROOT, maximum_parallel_tasks=4,
        campaign=selected.campaign, development_directory=directory)
    assert result["scientific_completion"] == "COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS"
    assert result["assigned_cases"] == len(selected.programme.cases)
    assert result["assigned_groups"] == len(selected.programme.group_ids)
    assert result["scientific_qualification"] == "NOT_ESTABLISHED"
    assert result["new_native_contact_count"] == 0
    assert result["secondary_structural_functional_readout"]["criterion_origin"] == choices.secondary_target.identity.to_document()
    assert all(value["value"]["disposition"] == "HISTORY_UNAVAILABLE" for value in result["assessments"])
    monkeypatch.setattr(LocalProcessExecutor, "execute", lambda *args, **values: pytest.fail("completed ordinary structure reentered executor"))
    before = _files(root)
    reopened = ordinary.read_selected_e4_structure(**kwargs, campaign=selected.campaign, original=selected.scope.development)
    assert reopened == result and _files(root) == before
    def no_reconstruction(*_args, **_kwargs):
        pytest.fail("retained ordinary structure reconstructed a secondary selection or derived request")
    monkeypatch.setattr("empirical_lawhood.api.matrix_full_factor_secondary.publish_e4_secondary_target", no_reconstruction)
    monkeypatch.setattr("empirical_lawhood.api.matrix_full_factor_derivation._derive_observed_input_selection", no_reconstruction)
    repeated = ordinary.produce_selected_e4_structure(**kwargs, project_root=ROOT, maximum_parallel_tasks=4,
        campaign=selected.campaign, development_directory=directory)
    assert repeated == result and scopes_seen and repeated["new_native_contact_count"] == 0
    after_reuse = _files(root)
    # This actual ordinary service uses SQLite :memory:. There are no on-disk
    # projection DB/WAL/SHM paths to exempt; no catalog-prefix exclusion is used.
    sqlite_projection_paths = frozenset()
    assert {path: digest for path, digest in before.items() if path not in sqlite_projection_paths} == {
        path: digest for path, digest in after_reuse.items() if path not in sqlite_projection_paths}
    changed = replace(choices, secondary_target=replace(choices.secondary_target,
        record_id=choices.secondary_target.record_id + ".changed"))
    with pytest.raises(PermissionError, match="actual pre-future target"):
        ordinary.read_selected_e4_structure(**{**kwargs, "choices": changed}, campaign=selected.campaign, original=selected.scope.development)
    with pytest.raises(PermissionError, match="actual pre-future target"):
        ordinary.produce_selected_e4_structure(**{**kwargs, "choices": changed}, project_root=ROOT,
            maximum_parallel_tasks=4, campaign=selected.campaign, development_directory=directory)
    assert _files(root) == after_reuse

    def substituted_original(**options):
        scope, files = original(**options)
        acquisition = replace(scope.development,
            entry_receipt=replace(scope.development.entry_receipt, object_fingerprint="f" * 64))
        return replace(scope, development=acquisition), files

    with monkeypatch.context() as changed_original:
        changed_original.setattr(custody, "derive_original_full_factor_scope", substituted_original)
        with pytest.raises(PermissionError, match="original custody|choices|reservations"):
            ordinary.produce_selected_e4_structure(**kwargs, project_root=ROOT, maximum_parallel_tasks=4,
                campaign=selected.campaign, development_directory=directory)
    assert _files(root) == after_reuse

    target = plane.root.resolve(secondary.publication.materialization.relative_path, for_write=False)
    original_target = target.read_bytes()
    changed_target = original_target.replace(b'"decimal":"0.01"', b'"decimal":"0.02"')
    assert changed_target != original_target and len(changed_target) == len(original_target)
    try:
        target.write_bytes(changed_target)
        with pytest.raises((PermissionError, ValueError, RuntimeError)):
            ordinary.produce_selected_e4_structure(**kwargs, project_root=ROOT, maximum_parallel_tasks=4,
                campaign=selected.campaign, development_directory=directory)
    finally:
        target.write_bytes(original_target)
    assert _files(root) == after_reuse


def test_protected_structure_reuses_complete_inputs_after_preauthor_interruption_with_new_access(
        scopes,literal_recipe_source_inputs,tmp_path,monkeypatch):  # noqa: F811
    """Actual derived/authoring custody; original grants/run are disclosed seams.

    Stored-grant tests own current permission evidence. This control proves
    original metadata reuse and public authoring, with no worker or scientific
    completion claim from its final routing-only report seam.
    """
    from empirical_lawhood.api import experiment_programme,selected_e4_access
    from tests import test_matrix_e4_full_factor_exposed_public as protected
    protected_values=protected._selected(scopes,literal_recipe_source_inputs,monkeypatch)
    actual_author_guard=protected.author.validate_authoring_read_access
    protected._original_seams(monkeypatch,protected_values)
    monkeypatch.setattr(custody,'derive_original_full_factor_scope',protected.derive.derive_original_full_factor_scope)
    plane=protected._real_plane(tmp_path/'protected-custody')
    # The ordinary phase and all derived/authoring paths share the selected root.
    directory=Path(plane.root.contract.canonical_path)/'phase'
    directory.mkdir()
    choices,resources=disclosed_structure(protected_values.bank,budget=dict(protected_values.resources.phase_budgets)['measure'])
    target,secondary=publish_secondary(plane,protected_values.bank,Path(plane.root.contract.canonical_path)/'early-secondary')
    protected_values.secondary_target,protected_values.secondary_readout=target,secondary
    original_author=experiment_programme.ExperimentProgrammeService.author
    interrupted=[]
    class BeforeAuthor(RuntimeError):pass
    def stop_once(self,**kwargs):
        interrupted.append(kwargs)
        raise BeforeAuthor('complete inputs before child author')
    monkeypatch.setattr(experiment_programme.ExperimentProgrammeService,'author',stop_once)
    kwargs=dict(directory=directory,artifact_writer=plane,project_root=ROOT,maximum_parallel_tasks=4,
        programme=protected_values.programme,bank=protected_values.bank,choices=choices,secondary_readout=secondary,resources=resources,
        campaign=protected_values.campaign,declaration=protected_values.scope.declaration)
    with pytest.raises(BeforeAuthor,match='before child author'):
        ordinary.produce_selected_e4_structure(**kwargs,waves=protected_values.scope.waves)
    assert len(interrupted)==1 and not (directory/'structure/analysis').exists()
    before=_files(Path(plane.root.contract.canonical_path))
    request_path=directory/'structure/inputs/records/request.json'
    original_request=request_path.read_bytes()
    prepared=interrupted[0]['preparation']
    records=dict(prepared.design_records)
    foreign_reference=replace(records['reference'],waves=tuple(replace(value,
        reveal_authority=replace(value.reveal_authority,object_id=value.reveal_authority.object_id+'.foreign'))
        for value in records['reference'].waves))
    forged=replace(prepared,design_records=tuple((name,foreign_reference if name=='reference' else value)
        for name,value in prepared.design_records))
    def no_foreign_grant(**_values):
        pytest.fail('foreign blind scope ancestry reached current grant selection')
    monkeypatch.setattr(selected_e4_access,'require_current_e4_access',no_foreign_grant)
    with pytest.raises(PermissionError,match='blind original scope'):
        actual_author_guard(preparation=forged,artifact_writer=plane,
            read_access=selected_e4_access.SelectedE4CurrentAccess(protected_values.scope.waves))
    assert _files(Path(plane.root.contract.canonical_path))==before
    replacements=tuple(replace(value,reveal_authority=replace(value.reveal_authority,
        object_id=value.reveal_authority.object_id+'.replacement')) for value in protected_values.scope.waves)
    current=selected_e4_access.SelectedE4CurrentAccess(replacements)
    current.require_originals(protected_values.scope.waves)
    accesses=[]
    def permit(**values):
        assert values['current_access']==current
        current.require_originals(values['originals'])
        accesses.append(values['originals'])
    def forbidden(*_args,**_kwargs):
        pytest.fail('preauthor retry reconstructed an original scope, secondary or request')
    monkeypatch.setattr(custody,'derive_original_full_factor_scope',forbidden)
    monkeypatch.setattr("empirical_lawhood.api.matrix_full_factor_secondary.publish_e4_secondary_target",forbidden)
    monkeypatch.setattr('empirical_lawhood.api.matrix_full_factor_derivation._derive_observed_input_selection',forbidden)
    monkeypatch.setattr(experiment_programme.ExperimentProgrammeService,'author',original_author)
    # Re-enable the actual owner guard, now using the explicit current-access
    # seam above. The original request's reveal fields remain byte-exact.
    from empirical_lawhood.api import matrix_full_factor_authoring as full_author
    monkeypatch.setattr(full_author,'validate_authoring_read_access',actual_author_guard)
    def denied(**values):
        assert values['current_access']==current
        raise PermissionError('current original reveal refused before FILE access')
    monkeypatch.setattr(selected_e4_access,'require_current_e4_access',denied)
    with pytest.raises(PermissionError,match='before FILE access'):
        ordinary.produce_selected_e4_structure(**kwargs,waves=replacements)
    assert _files(Path(plane.root.contract.canonical_path))==before
    monkeypatch.setattr(selected_e4_access,'require_current_e4_access',permit)
    result={'scientific_completion':'COMPLETE_ORIGINAL_FULL_FACTOR_CENSUS','new_native_contact_count':0}
    def run(self,**values):
        assert values['read_access']==current
        assert (values['directory']/'authored-wave.json').is_file()
        return {'status':'SUCCEEDED','scientific_result':result}
    monkeypatch.setattr(experiment_programme.ExperimentProgrammeService,'run',run)
    assert ordinary.produce_selected_e4_structure(**kwargs,waves=replacements)==result
    after=_files(Path(plane.root.contract.canonical_path))
    assert all(after[name]==digest for name,digest in before.items())
    assert request_path.read_bytes()==original_request and accesses
