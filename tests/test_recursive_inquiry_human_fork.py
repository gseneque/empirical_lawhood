# SPDX-License-Identifier: MPL-2.0
"""Exposed source/intent substitution refusals; no authority or worker entry."""

from pathlib import Path
from types import SimpleNamespace as N
import pytest
from empirical_lawhood.api import (
    recursive_inquiry as service,
    recursive_contributions as contributions,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recursive_inquiry import (
    InquiryStateSources,
    InquiryWaveSource,
)
from empirical_lawhood.kernel.recursive_inquiry import identity


class Record:
    SCHEMA = "empirical-lawhood/testing/human-fork-record"
    VERSION = "1.0.0"

    def __init__(self, key):
        self.draft_id = self.packet_id = key

    def fingerprint(self):
        return ("a" if self.draft_id == "new" else "b") * 64


@pytest.fixture
def fork(tmp_path, monkeypatch):
    root = tmp_path / "root"
    supplier = root / "supplier"
    supplier.mkdir(parents=True)
    packet = Record("packet")
    old = Record("old")
    draft = Record("new")
    parent = object()
    draft.contribution_parents = (parent,)
    old.contribution_parents = (parent,)
    calls = []
    origins = N(validate_draft=lambda d: calls.append(("origins", d)))
    plane = N(root=N(contract=N(canonical_path=str(root))))
    records = {
        "decision.json": N(human_directed=True),
        "sources.json": InquiryStateSources(
            (InquiryWaveSource("supplier", identity(packet, "packet"), True),)
        ),
    }
    monkeypatch.setattr(
        service, "load_authored_wave", lambda **kw: (packet, old, None, None)
    )
    monkeypatch.setattr(
        service,
        "read_recursive_wave",
        lambda **kw: ({"status": "SUCCEEDED"}, {}, old, None),
    )
    monkeypatch.setattr(contributions, "_described", lambda d, p: parent)

    def authenticated(**kw):
        if kw["draft"].contribution_parents != (parent,):
            raise ValueError(
                "human inquiry fork changes its actual receipt-backed supplier parent"
            )
        return ((None, None, parent, None, None, None),)

    monkeypatch.setattr(contributions, "authenticate_recursive_parents", authenticated)
    return N(
        root=root,
        supplier=supplier,
        packet=packet,
        old=old,
        draft=draft,
        parent=parent,
        origins=origins,
        plane=plane,
        records=records,
        calls=calls,
    )


def validate(fork, **changes):
    params = dict(
        draft=fork.draft,
        records=fork.records,
        supplier_directory=fork.supplier,
        contribution_dir=fork.root / "portable",
        origins=fork.origins,
        artifact_writer=fork.plane,
    )
    params.update(changes)
    return service._validate_human_fork(**params)


def test_human_fork_retains_actual_supplier_and_one_exact_portable_parent(fork):
    assert validate(fork) is fork.draft and fork.calls == [("origins", fork.draft)]


def test_automatic_or_missing_actual_source_cannot_author_human_fork(fork):
    bad = dict(fork.records)
    bad["decision.json"] = N(human_directed=False)
    with pytest.raises(ValueError, match="explicit persisted human-directed"):
        validate(fork, records=bad)
    for waves in (
        (),
        (InquiryWaveSource("supplier", identity(fork.packet, "packet"), False),),
        (InquiryWaveSource("other", identity(fork.packet, "packet"), True),),
        (
            InquiryWaveSource(
                "supplier",
                ObjectIdentity("foreign", Record.SCHEMA, "1.0.0", "c" * 64),
                True,
            ),
        ),
    ):
        bad = dict(fork.records)
        bad["sources.json"] = InquiryStateSources(waves)
        with pytest.raises(ValueError, match="absent from"):
            validate(fork, records=bad)


def test_same_draft_wrong_parent_and_uncompleted_supplier_refuse(fork, monkeypatch):
    with pytest.raises(ValueError, match="distinct new"):
        validate(fork, draft=fork.old)
    fork.draft.contribution_parents = (object(),)
    with pytest.raises(ValueError, match="actual receipt-backed"):
        validate(fork)
    fork.draft.contribution_parents = (fork.parent,)
    monkeypatch.setattr(
        contributions,
        "authenticate_recursive_parents",
        lambda **kw: ((None, None, object(), None, None, None),),
    )
    with pytest.raises(ValueError, match="actual receipt-backed"):
        validate(fork)
    monkeypatch.setattr(
        service,
        "read_recursive_wave",
        lambda **kw: ({"status": "BLOCKED"}, {}, fork.old, None),
    )
    with pytest.raises(ValueError, match="completed supplier"):
        validate(fork)


def test_human_fork_does_not_accept_source_only_initial_or_unselected_supplier(
    fork, monkeypatch
):
    records = {"intent.json": N(), **fork.records,
        "decision.json": N(human_directed=True, selected_alternative_id="act"),
        "menu.json": N(alternatives=(N(alternative_id="act", reuse_completion=None),))}
    monkeypatch.setattr(
        service,
        "read_inquiry_decision",
        lambda **kw: (fork.packet, records),
    )
    for supplier, initial in ((None, None), (fork.supplier, N())):
        with pytest.raises(ValueError, match="forbids an initial draft"):
            service.author_inquiry_successor(
                decision_directory=fork.root / "decision",
                origins=fork.origins,
                project_root=Path("."),
                artifact_writer=fork.plane,
                output_dir=fork.root / "unentered",
                supplier_directory=supplier,
                initial_draft=initial,
                human_fork_draft=fork.draft,
            )
    assert not (fork.root / "unentered").exists()


def test_human_fork_intent_keeps_exact_draft_config_origins_and_capability(fork):
    config = ObjectIdentity("config.new", Record.SCHEMA, "1.0.0", "c" * 64)
    origins = Record("origins")
    fork.draft.operations = (
        N(
            node_id="new",
            config_identity=config,
            selection=N(selection_id="capability.new"),
        ),
    )
    fork.draft.selected_operation_ids = ("new",)
    exact = dict(
        draft=identity(fork.draft, "new"),
        configuration=config,
        input_origins=identity(origins, "inquiry-input-origins"),
        capability_id="capability.new",
    )
    service._validate_intent_draft(N(**exact), fork.draft, origins)
    for field, replacement in (
        ("draft", identity(fork.old, "old")),
        (
            "configuration",
            ObjectIdentity("config.other", Record.SCHEMA, "1.0.0", "d" * 64),
        ),
        ("input_origins", identity(fork.draft, "inquiry-input-origins")),
        ("capability_id", "capability.other"),
    ):
        altered = {**exact, field: replacement}
        with pytest.raises(ValueError, match="substitutes its registered"):
            service._validate_intent_draft(N(**altered), fork.draft, origins)


def test_human_fork_additional_authentic_parent_keeps_designated_supplier(
    fork, monkeypatch
):
    additional = object()
    fork.draft.contribution_parents = (fork.parent, additional)
    directories = (fork.root / "portable-supplier", fork.root / "portable-history")

    def authenticated(**kw):
        assert kw["directories"] == directories and kw["directory"] is None
        return tuple(
            (None, None, value, None, None, None)
            for value in kw["draft"].contribution_parents
        )

    monkeypatch.setattr(contributions, "authenticate_recursive_parents", authenticated)
    assert (
        validate(fork, contribution_dir=None, contribution_dirs=directories)
        is fork.draft
    )
    fork.draft.contribution_parents = (additional,)
    with pytest.raises(ValueError, match="actual receipt-backed supplier"):
        validate(fork, contribution_dir=None, contribution_dirs=directories)
