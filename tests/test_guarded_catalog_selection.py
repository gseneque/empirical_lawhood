# SPDX-License-Identifier: MPL-2.0
"""Explicit external catalog custody; software controls grant no authority."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.facade import EmpiricalLawhoodApi
from empirical_lawhood.infrastructure.artifacts import ExternalRootUnavailable, FilesystemState, GuardedExternalRoot
from empirical_lawhood.infrastructure.guarded_catalog import GuardedCatalogAccess, select_operator_catalog
from empirical_lawhood.runtime.artifacts import ExternalRootContract


@pytest.fixture
def selected(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    contract = ExternalRootContract("software.catalog.scratch", "Bounded software scratch",
        str(root), str(root), "empirical-lawhood/testing/catalog-scratch", 1,
        expected_mount_source="/dev/software-fixture", expected_volume_identity="software-fixture",
        allowed_filesystem_types=("ext4",))
    state = SimpleNamespace(value=FilesystemState(str(root), True, True, 10**9, False,
        "/dev/software-fixture", "software-fixture", "ext4"), inspections=0)

    class Inspector:
        def inspect(self, observed_contract):
            assert observed_contract == contract
            state.inspections += 1
            return state.value

    guard = GuardedExternalRoot(contract, Inspector())
    return GuardedCatalogAccess(guard, "operational/reactor.sqlite3", True), state


def test_selection_and_absent_read_create_no_projection_or_parent(selected):
    access, _ = selected
    assert access.display_locator == "external-scratch:operational/reactor.sqlite3"
    assert not access.database_path.parent.exists()
    with pytest.raises(FileNotFoundError):
        access.read_only_engine()
    assert not access.database_path.parent.exists()


@pytest.mark.parametrize("path", ("../escape.sqlite3", "/absolute.sqlite3", "a//b.sqlite3", "a/../b.sqlite3",
    "target-wal", "target-shm", "target-journal"))
def test_invalid_scalar_locations_refuse(selected, path):
    access, _ = selected
    with pytest.raises(ValueError):
        GuardedCatalogAccess(access.root, path, True)


def test_explicit_scalar_requires_profile_without_probing_or_creating_it():
    assert select_operator_catalog(profile=None, project_root=Path("/unused"), catalog_relative_path=None) is None
    with pytest.raises(ValueError, match="explicit operator"):
        select_operator_catalog(profile=None, project_root=Path("/unused"), catalog_relative_path="catalog.sqlite3")


def test_every_new_connection_rechecks_actual_mount_and_preserves_read_only_bytes(selected):
    access, state = selected
    engine = access.initialize_engine()
    engine.dispose()
    before = access.database_path.read_bytes()
    reader = access.read_only_engine()
    previous = state.inspections
    with reader.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA query_only").scalar_one() == 1
    assert state.inspections > previous
    state.value = replace(state.value, active_mount=False)
    with pytest.raises((PermissionError, RuntimeError)):
        reader.connect()
    reader.dispose()
    assert access.database_path.read_bytes() == before
    assert sorted(path.name for path in access.database_path.parent.iterdir()) == ["reactor.sqlite3"]


@pytest.mark.parametrize("damage", ("inactive", "volume", "source", "capacity", "readonly"))
def test_existing_write_engine_does_not_keep_stale_storage_admission(selected, damage):
    access, state = selected
    engine = access.initialize_engine()
    changed = {
        "inactive": {"active_mount": False}, "volume": {"volume_identity": "changed"},
        "source": {"mount_source": "/dev/changed"}, "capacity": {"free_bytes": 0},
        "readonly": {"writable": False},
    }[damage]
    state.value = replace(state.value, **changed)
    try:
        with pytest.raises((PermissionError, RuntimeError)):
            engine.connect()
    finally:
        engine.dispose()


def test_read_only_profile_cannot_initialize_even_on_writable_mount(selected):
    access, _ = selected
    readonly = replace(access, writable=False)
    with pytest.raises(PermissionError, match="read-only"):
        readonly.initialize_engine()
    assert not access.database_path.parent.exists()


@pytest.mark.parametrize("suffix", ("", "-wal", "-shm", "-journal"))
def test_catalog_and_sqlite_neighbors_refuse_links(selected, tmp_path, suffix):
    access, _ = selected
    access.database_path.parent.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"must remain unchanged")
    access.database_path.with_name(access.database_path.name + suffix).symlink_to(outside)
    with pytest.raises((PermissionError, ExternalRootUnavailable), match="symlink"):
        access.initialize_engine()
    assert outside.read_bytes() == b"must remain unchanged"


def test_facade_reports_selected_absent_catalog_without_creating_it(selected):
    access, _ = selected
    api = EmpiricalLawhoodApi(repo_root=Path(__file__).resolve().parents[1],
        catalog_access=access, external_root=None)
    result = api.check_catalog()
    assert result.succeeded and result.payload.present is False
    assert result.payload.catalog_relative_path == access.display_locator
    assert not access.database_path.parent.exists()


@pytest.mark.parametrize("method", ("register_dataset", "rebuild_dataset_projection", "compact_catalog", "rebuild_catalog"))
def test_fixed_path_maintenance_refuses_before_document_reads_or_writes(selected, method):
    access, _ = selected
    api = EmpiricalLawhoodApi(repo_root=Path(__file__).resolve().parents[1],
        catalog_access=access, external_root=None)
    result = getattr(api, method)(None)
    assert result.reason_codes == ("EXTERNAL_CATALOG_OPERATION_UNSUPPORTED",)
    assert not access.database_path.parent.exists()


def test_sqlite_uri_characters_remain_literal_selected_filename(selected):
    access, _ = selected
    selected_literal = replace(access, relative_path="operational/projection?mode=ro.sqlite3")
    engine = selected_literal.initialize_engine()
    engine.dispose()
    assert selected_literal.database_path.is_file()
    assert not access.database_path.is_file()


def test_trusted_dataset_view_uses_selected_guard_without_deriving_new_trust(selected):
    from empirical_lawhood.infrastructure.dataset_catalog_access import DatasetCatalogReadSessionProvider
    from empirical_lawhood.runtime.datasets import DatasetCatalogSnapshot
    from tests.infrastructure.test_dataset_catalog_access import _projection_anchor

    access, state = selected
    engine = access.initialize_engine()
    engine.dispose()
    snapshot = DatasetCatalogSnapshot((), (), (), (), (), ())
    anchor = _projection_anchor(snapshot)
    provider = DatasetCatalogReadSessionProvider(access.database_path, snapshot, anchor, catalog_access=access)
    assert provider.trusted_snapshot is snapshot and provider.trusted_anchor is anchor
    state.value = replace(state.value, active_mount=False)
    with pytest.raises((PermissionError, RuntimeError)):
        with provider.open():
            pytest.fail("trusted dataset view opened an unavailable selected catalog")


def test_trusted_dataset_owner_refuses_a_different_path(selected):
    from empirical_lawhood.infrastructure.dataset_catalog_access import DatasetCatalogReadSessionProvider
    from empirical_lawhood.runtime.datasets import DatasetCatalogSnapshot
    from tests.infrastructure.test_dataset_catalog_access import _projection_anchor

    access, _ = selected
    snapshot = DatasetCatalogSnapshot((), (), (), (), (), ())
    with pytest.raises(ValueError, match="guarded read-only selection"):
        DatasetCatalogReadSessionProvider(access.database_path.with_name("other.sqlite3"),
            snapshot, _projection_anchor(snapshot), catalog_access=access)


def test_persisted_wal_header_refuses_without_creating_neighbors(selected):
    import sqlite3

    access, _ = selected
    access.database_path.parent.mkdir()
    connection = sqlite3.connect(access.database_path)
    assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
    connection.execute("CREATE TABLE software_control (value INTEGER)")
    connection.commit()
    connection.close()
    before = access.database_path.read_bytes()
    assert before[18:20] == bytes((2, 2))
    assert sorted(path.name for path in access.database_path.parent.iterdir()) == ["reactor.sqlite3"]
    with pytest.raises(PermissionError, match="rollback-journal header"):
        access.read_only_engine()
    assert access.database_path.read_bytes() == before
    assert sorted(path.name for path in access.database_path.parent.iterdir()) == ["reactor.sqlite3"]


@pytest.mark.parametrize("read_only_supplied", (False, True))
def test_selected_service_owner_replaces_foreign_or_omitted_factories(selected, read_only_supplied):
    from empirical_lawhood.api.execution import CampaignExecutionService
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
    from empirical_lawhood.runtime.providers import CampaignRuntimeProviderRegistry

    access, _ = selected

    def foreign_factory():
        pytest.fail("selected catalog called a foreign unguarded factory")

    options = {"read_only_engine_factory": foreign_factory} if read_only_supplied else {}
    service = CampaignExecutionService(repo_root=Path(__file__).resolve().parents[1],
        artifact_plane=ExternalArtifactPlane(access.root), engine_factory=foreign_factory,
        catalog_path=access.database_path, providers=CampaignRuntimeProviderRegistry(()),
        catalog_access=access, enforce_git_identity=False, **options)
    assert service.engine_factory == access.initialize_engine
    assert service.read_only_engine_factory == access.read_only_engine
    writer = service.engine_factory()
    writer.dispose()
    reader = service.read_only_engine_factory()
    with reader.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA query_only").scalar_one() == 1
    reader.dispose()
