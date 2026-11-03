# SPDX-License-Identifier: MPL-2.0
"""Programme operational selection over actual APIs and guarded SQLite.

The retained packet is the existing exposed synthetic prospective fixture,
including its documented source-inspector and loader seams. These controls
exercise default API/catalog composition and actual CLI refusal, not genuine
authority, native execution or complete profile-plane lifecycle acceptance.
"""

from contextlib import nullcontext
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api import prospective_experiment as owner
from empirical_lawhood.cli.app import app
from empirical_lawhood.runtime.operator_profile import OperatorStorageAccessMode, OperatorStorageProfile
from tests.test_prospective_experiment import selected as prospective_selection  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
CATALOG = "operational/programme.sqlite3"


@pytest.fixture
def operator(tmp_path):
    mount = Path(os.environ.get("EL_TEST_EXTERNAL_MOUNT", "/dev/shm")).resolve(strict=True)
    if not mount.is_mount() or mount == Path("/"):
        raise ValueError("programme catalog control requires an actual selected external mount")
    if tmp_path.is_relative_to(mount):
        storage = tmp_path / "programme-operator"
        storage.mkdir()
        selected = nullcontext(str(storage))
    else:
        if "EL_TEST_EXTERNAL_MOUNT" in os.environ:
            raise ValueError("select pytest basetemp beneath EL_TEST_EXTERNAL_MOUNT")
        selected = TemporaryDirectory(prefix="empirical-lawhood-programme-", dir=mount)
    with selected as value:
        storage = Path(value)
        (storage / "artifacts").mkdir()
        (storage / "scratch").mkdir()
        yield OperatorStorageProfile("synthetic.programme.storage", "external-filesystem", "1.0.0",
            str(storage), str(mount), "artifacts", "scratch", OperatorStorageAccessMode.READ_WRITE,
            None, None, ("ext4", "tmpfs"), "strict-mount-contained-no-symlink", 1, (), 1, False)


def _loader(selection):
    prepared = owner.load_prepared_prospective_experiment
    retained = owner.load_retained_prospective_experiment

    def load(**arguments):
        # Keep the existing synthetic packet's original source-inspector seam
        # explicit. The API itself uses sole ROOT and its real origin owner;
        # this component control does not assert a scientific source join.
        arguments = dict(arguments, project_root=selection.root / "checkout")
        if "reveal_authority_id" in arguments:
            return prepared(**arguments, composition=selection.composition,
                candidate_catalog=selection.candidate_catalog)
        return retained(**arguments)
    return load


def _service(selection, profile, **options):
    return ExperimentProgrammeService(ROOT, selection.plane, profile,
        prospective_experiment_loader=_loader(selection), **options)


def _source_catalog_census(project):
    directory = project / ".empirical-lawhood"
    return (directory.exists(), {path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*") if path.is_file()})


def _cli_fixture(monkeypatch, selection, profile):
    from empirical_lawhood.cli import integrations
    load = _loader(selection)
    monkeypatch.setattr(owner, "load_prepared_prospective_experiment", load)
    monkeypatch.setattr(owner, "load_retained_prospective_experiment", load)
    monkeypatch.setattr(integrations, "_storage", lambda *, read_only=False: (ROOT, profile, selection.plane))


def _cli_arguments(selection, profile, lifecycle):
    # The missing package/run is deliberate: no approval or original publication
    # is invented to turn this operational route control into lifecycle evidence.
    if lifecycle == "run":
        return ["--plan", str(Path(profile.external_root_locator) / "absent-package.json")]
    return ["--run", "run.synthetic.absent"]


@pytest.mark.parametrize("lifecycle", ("run", "read", "recover"))
def test_default_programme_api_uses_selected_catalog_for_real_rw_and_ro_connections(
        prospective_selection, operator, lifecycle):  # noqa: F811
    selection = prospective_selection
    service = _service(selection, operator, catalog_relative_path=CATALOG)
    project = ROOT
    before = _source_catalog_census(project)
    # This composition control selects the same deliberately missing run as
    # its public CLI fixture; it does not recover or fabricate completed work.
    recovery_options = {"recovery_run_id": "run.synthetic.absent"} if lifecycle == "recover" else {}
    _, api = service._prospective_context(selection.directory, lifecycle=lifecycle, **recovery_options)
    actual = api._execution_service
    access = actual.catalog_access
    assert actual.catalog_path == Path(operator.external_root_locator) / "scratch" / CATALOG
    assert access is not None and access.database_path == actual.catalog_path
    assert actual.engine_factory == access.initialize_engine
    assert actual.read_only_engine_factory == access.read_only_engine
    report = api.check_catalog()
    assert report.succeeded and report.payload.present is False
    assert not actual.catalog_path.parent.exists()
    engine = actual.engine_factory()
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE software_programme_probe (value INTEGER NOT NULL)")
            connection.exec_driver_sql("INSERT INTO software_programme_probe VALUES (434)")
    finally:
        engine.dispose()
    retained_bytes = actual.catalog_path.read_bytes()
    reader = actual.read_only_engine_factory()
    try:
        with reader.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA query_only").scalar_one() == 1
            assert connection.exec_driver_sql("SELECT value FROM software_programme_probe").scalar_one() == 434
    finally:
        reader.dispose()
    assert actual.catalog_path.read_bytes() == retained_bytes
    assert api.check_catalog().payload.catalog_relative_path == "external-scratch:" + CATALOG
    assert _source_catalog_census(project) == before


def test_optional_catalog_preserves_legacy_default_and_factory_signature(prospective_selection, operator, monkeypatch):  # noqa: F811
    from empirical_lawhood.api import composition

    seen = []
    real = composition.create_api

    def compose(**arguments):
        seen.append(arguments)
        return real(**arguments)

    monkeypatch.setattr(composition, "create_api", compose)
    selection = prospective_selection
    from empirical_lawhood.runtime.operational_configuration import ArtifactVerificationMode
    selection.plane.artifact_verification = ArtifactVerificationMode.STRICT
    _, api = _service(selection, operator)._prospective_context(selection.directory, lifecycle="read")
    assert "catalog_relative_path" not in seen[-1]
    assert api._execution_service.catalog_access is None
    assert api._execution_service.artifact_plane.artifact_verification is ArtifactVerificationMode.STRICT
    assert api._execution_service.catalog_path == ROOT / ".empirical-lawhood/experiment_catalog.sqlite3"
    calls = []
    sentinel = object()
    service = ExperimentProgrammeService(selection.root / "checkout", selection.plane, SimpleNamespace(maximum_parallel_tasks=1),
        _loader(selection), lambda **arguments: calls.append(arguments) or sentinel)
    assert service._prospective_context(selection.directory, lifecycle="read")[1] is sentinel
    assert set(calls[-1]) == {"handoff", "project_root", "storage_profile", "maximum_parallel_tasks"}
    assert calls[-1]["maximum_parallel_tasks"] == 1


def test_catalog_and_custom_factory_refuse_before_loading_or_callback():
    def forbidden(**_arguments):
        pytest.fail("conflicting selected catalog entered an injected owner")

    with pytest.raises(ValueError, match="catalog_relative_path.*prospective_api_factory"):
        ExperimentProgrammeService(Path("/unused"), object(), object(), forbidden, forbidden,
            catalog_relative_path=CATALOG)


@pytest.mark.parametrize("lifecycle", ("run", "read", "recover"))
def test_real_cli_programme_refuses_selected_catalog_sidecar_before_root_writes(
        prospective_selection, operator, monkeypatch, lifecycle):  # noqa: F811
    selection = prospective_selection
    _cli_fixture(monkeypatch, selection, operator)
    before = _source_catalog_census(ROOT)
    result = CliRunner().invoke(app, ["--catalog-relative-path", "forbidden-wal",
        "campaign", "experiment-" + lifecycle, "--authoring-dir", str(selection.directory),
        *_cli_arguments(selection, operator, lifecycle)])
    assert result.exit_code == 2, result.output
    assert "catalog target cannot select a SQLite sidecar" in result.output
    assert _source_catalog_census(ROOT) == before
    assert list((Path(operator.external_root_locator) / "scratch").iterdir()) == []
