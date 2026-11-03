# SPDX-License-Identifier: MPL-2.0
"""Pure revision reserve joins; disclosed fixtures create no custody authority."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.api import matrix_selected_revision_runtime as runtime
from tests.test_matrix_selected_protected import transfer, unpublished  # noqa: F401


def _programme(base, **changes):
    selected = SimpleNamespace(phase="E6_TRANSFER", sources=base.sources,
        reservation=base.sources.closure.reservation, expected_groups=base.point_design.expected_groups,
        source_arms=base.sources.source_arms)
    for name, value in changes.items():
        setattr(selected, name, value)
    return selected


def test_revision_transfer_accepts_the_authenticated_original_reserve(transfer):  # noqa: F811
    original = MatrixSelectedPublicPackage.from_package(transfer.point_design.package)
    runtime._require_original_transfer_reserve(original, _programme(transfer))


def test_revision_transfer_refuses_a_separately_published_late_reserve(transfer):  # noqa: F811
    original = MatrixSelectedPublicPackage.from_package(transfer.point_design.package)
    closure = transfer.sources.closure
    allocation = replace(closure.reservation.allocation, allocation_id="allocation.audit.late-unrelated")
    reservation = old.ScheduledReservation("reservation.audit.late-unrelated", allocation,
        unpublished(allocation, "publication.audit.late-allocation"))
    selection = replace(closure.specification.selection, selection_id="selection.audit.late-unrelated",
        reservation=old.identity(reservation))
    specification = old.ScheduledSpecification("specification.audit.late-unrelated", selection,
        unpublished(selection, "publication.audit.late-selection"))
    source_index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=closure.provenances)
    descriptors = tuple(source_index.reference(source_id="source.audit." + row.root.root_id,
        root_id=row.root.root_id, provenance=closure.provenances[0].identity) for row in allocation.roots)
    closure = replace(closure, record_id="closure.audit.late-unrelated", reservation=reservation,
        specification=specification, descriptors=descriptors)
    sources = replace(transfer.sources, record_id="sources.audit.late-unrelated", closure=closure)
    with pytest.raises(PermissionError, match="pre-fit reservation or allocation"):
        runtime._require_original_transfer_reserve(original,
            _programme(transfer, sources=sources, reservation=reservation, source_arms=sources.source_arms))


@pytest.mark.parametrize("duplicate", (False, True), ids=("missing", "duplicate"))
def test_revision_transfer_requires_each_original_reserved_group_once(transfer, duplicate):  # noqa: F811
    original = MatrixSelectedPublicPackage.from_package(transfer.point_design.package)
    rows = transfer.sources.source_arms()
    changed = (*rows, rows[0]) if duplicate else rows[:-1]
    with pytest.raises(PermissionError, match="complete original pre-fit reserve"):
        runtime._require_original_transfer_reserve(original, _programme(transfer, source_arms=lambda: changed))


def test_revision_transfer_refuses_changed_original_partition_size(transfer):  # noqa: F811
    original = MatrixSelectedPublicPackage.from_package(transfer.point_design.package)
    with pytest.raises(PermissionError, match="nearby and shifted whole-group partitions"):
        runtime._require_original_transfer_reserve(original,
            _programme(transfer, expected_groups=transfer.point_design.expected_groups + 1))


@pytest.mark.parametrize("phase", ("E5_OPPORTUNITY", "E5_CONFIRMATION"))
def test_revision_e5_does_not_consume_the_reserved_e6_partition(phase):
    runtime._require_original_transfer_reserve(object(), SimpleNamespace(phase=phase))


@pytest.mark.parametrize("include", (False, True), ids=("seal-only", "seal-and-allocation"))
def test_revision_entry_carries_the_same_once_authenticated_allocation(monkeypatch, include):
    from empirical_lawhood.api import matrix_prepared_original_commitments
    used, allocation, seal, access = ("group.used",), object(), object(), object()
    calls = []

    def originals(writer, programme, evidence, codecs, *, include_original_allocation, current_access):
        assert include_original_allocation is True and current_access is access
        calls.append("originals")
        return used, allocation

    monkeypatch.setattr(runtime, "revision_original_operands", originals)
    def commitments(**kwargs):
        assert kwargs["current_access"] is access
        calls.append("commitments")
    def source(*args, current_access):
        assert current_access is access
        calls.append("source")
    monkeypatch.setattr(matrix_prepared_original_commitments, "authenticate_prepared_original_commitments", commitments)
    monkeypatch.setattr(runtime, "authenticate_revision_source_custody", source)
    monkeypatch.setattr(runtime, "entry_seal", lambda programme: seal)
    result = runtime.authenticate_revision_entry(None, SimpleNamespace(excluded_group_ids=used), None, {},
        source_scan_bytes=128 * 1024**2, include_original_allocation=include, current_access=access)
    assert result == ((seal, allocation) if include else seal)
    assert calls == ["commitments", "originals", "source"]


@pytest.mark.parametrize("entrypoint", (runtime.revision_original_operands, runtime.authenticate_revision_entry))
def test_revision_allocation_selection_refuses_nonboolean_before_authentication(entrypoint):
    with pytest.raises(TypeError, match="must be a boolean"):
        keywords = {"source_scan_bytes": 128 * 1024**2} if entrypoint is runtime.authenticate_revision_entry else {}
        entrypoint(None, None, None, {}, include_original_allocation=1, **keywords)
