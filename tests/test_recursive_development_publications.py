# SPDX-License-Identifier: MPL-2.0
"""Development publication premises are checked before writes and at each read."""

from dataclasses import replace
from pathlib import Path

import pytest

from empirical_lawhood.api.recursive_authoring import author_recursive_wave, load_authored_wave
from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
from empirical_lawhood.runtime.recursive_compiler import RegisteredPublicationRequirement

from tests.test_recursive_public_service import _draft, _plane


ROOT = Path(__file__).resolve().parents[1]


def test_development_boundaries_recheck_registered_premises_before_publication_or_execution(tmp_path, monkeypatch):
    from empirical_lawhood.api import recursive_authoring as owner
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor

    draft = _draft()
    registrations, registry, codecs = owner.operation_catalog()
    selected = {row.selection.selection_id for row in draft.operations
                if row.node_id in draft.selected_operation_ids}
    calls = []
    permitted = [False]

    def authenticate(actual_writer, configs):
        calls.append((actual_writer, tuple(row.node_id for row in configs)))
        if not permitted[0]:
            raise PermissionError("original retained publication refuses replay")

    requirement = RegisteredPublicationRequirement("testing.development.retained-publication", authenticate)
    registrations = tuple(replace(row, publication_requirements=(*row.publication_requirements, requirement))
        if row.selection.selection_id in selected else row for row in registrations)
    monkeypatch.setattr(owner, "operation_catalog", lambda: (registrations, registry, codecs))
    plane = _plane(tmp_path / "selected")
    directory = tmp_path / "selected/authored"
    with pytest.raises(PermissionError, match="retained publication refuses replay"):
        author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=directory)
    assert not directory.exists()
    assert calls == [(plane, tuple(sorted(draft.selected_operation_ids)))]

    permitted[0] = True
    author_recursive_wave(draft=draft, project_root=ROOT, artifact_writer=plane, output_dir=directory)
    load_authored_wave(directory=directory, artifact_writer=plane)
    permitted[0] = False

    def forbidden(*_args, **_kwargs):
        raise AssertionError("refused publication reached a worker")

    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    boundaries = (
        lambda: load_authored_wave(directory=directory, artifact_writer=plane),
        lambda: read_recursive_wave(directory=directory, artifact_writer=plane),
        lambda: run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane),
    )
    for boundary in boundaries:
        before = len(calls)
        with pytest.raises(PermissionError, match="retained publication refuses replay"):
            boundary()
        assert len(calls) == before + 1
