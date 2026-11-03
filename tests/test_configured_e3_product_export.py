# SPDX-License-Identifier: MPL-2.0
"""Export conformance with disclosed read/grant/source seams, never authority.

Typed E3 products, actual original publications and receipts, frozen joins,
public projection, lineage and atomic publication use the production owners.
The full protected reader is an explicit seam tested by its separate controls.
"""

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_exports import ConfiguredProtectedE3ProductExportSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
from empirical_lawhood.adapters.methods.matrix_factor_response.extension_bundle import EXPERIMENT_PROTOCOL_DECLARATIONS
from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import product_export as owner
from empirical_lawhood.api.domain_composition.matrix_configured_protected_response import scientific_read
from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment
from empirical_lawhood.infrastructure.artifacts import ArtifactIdentityConflict
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, CanonicalTaskReceipt
from tests.test_matrix_configured_selected_package import configured_package
from tests.test_matrix_e3_original_publications import case as original_case  # noqa: F401


def _literal(identifier, schema, **fields):
    return SimpleNamespace(SCHEMA=schema, VERSION="1.0.0",
        fingerprint=lambda: sha256(identifier.encode()).hexdigest(), **fields)


@pytest.fixture(scope="module")
def products(original_case):  # noqa: F811
    full = configured_package(original_case)
    plane = original_case.plane
    run = "run.disclosed-configured-export"
    receipts, tasks = {}, []
    for name, operation, mode in owner._PRODUCTS:
        record = getattr(full, name.replace("-", "_"))
        task_id = statistical_task_id(full.specification.identity, full.allocation.identity, operation, mode=mode)
        access = OutcomeAccess.DEVELOPMENT_VISIBLE if name in ("models", "model-freeze") else OutcomeAccess.EVALUATION_SEALED
        publication = plane.write(ArtifactWriteRequest("literal.export." + name,
            "export-originals/" + name + ".json", record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
            "application/json", "literal.export", "export-originals", record.canonical_bytes(),
            VisibilityCeiling.DEVELOPMENT_ONLY, (), access))
        receipts[task_id] = CanonicalTaskReceipt("receipt.export." + name, run, task_id, "attempt.export." + name,
            "c" * 40, (), (publication.materialization,), (publication.logical,), (), OperationalStatus.SUCCEEDED, ())
        tasks.append(SimpleNamespace(task_id=task_id, outputs=(SimpleNamespace(output_id=task_id + ".product",
            logical_artifact_id=publication.logical.logical_artifact_id, payload_schema=record.SCHEMA),)))
    issue = _literal("issue.export", "empirical-lawhood/runtime/issued-executable-study-manifest", issue_id="issue.export")
    execution = _literal("authority.export.execution", "empirical-lawhood/planning/study-operation-authority",
        authority_id="authority.export.execution")
    package = _literal("package.export", "empirical-lawhood/api/experiment-package", package_id="package.export",
        run_plan_id=run, issued_study=issue, execution_authority=execution)
    plan = _literal("plan.export", "empirical-lawhood/runtime/execution-plan", execution_plan_id="plan.export", tasks=tuple(tasks))
    reveal = ObjectIdentity("authority.export.reveal", execution.SCHEMA, "1.0.0", "d" * 64)
    report = {"scientific_status": "UNEVALUABLE", "qualification": "NOT_ESTABLISHED",
        "operational_status": "BLOCKED", "unresolved_native_tasks": ["task.original-unknown"],
        "typed_product_validation": "COMPLETE", "scientific_completion": "RETAINED_ADJUDICATION"}
    return SimpleNamespace(full=full, plane=plane, package=package, plan=plan, receipts=receipts, reveal=reveal, report=report)


@pytest.fixture
def export_case(products, monkeypatch, tmp_path):
    suffix = sha256(tmp_path.name.encode()).hexdigest()[:12]
    selection = ConfiguredProtectedE3ProductExportSelection("export." + suffix, products.package.run_plan_id,
        owner._identity(products.package, "package_id"), products.reveal.object_id,
        "frozen." + suffix, "exports/" + suffix)
    path = tmp_path / "selection.json"
    path.write_bytes(selection.canonical_bytes())
    calls = []
    read = SimpleNamespace(package=products.package, execution_plan=products.plan,
        specification=products.full.specification, allocation=products.full.allocation,
        prefit=products.full.prefit, models=products.full.models, model_freeze=products.full.model_freeze,
        calibration=products.full.calibration, calibrated_freeze=products.full.calibrated_freeze,
        receipts=dict(products.receipts), reveal_authority=products.reveal, report=dict(products.report),
        require_current=lambda: calls.append("current"))

    @contextmanager
    def actual_read(**arguments):
        calls.append("full-read")
        assert arguments["expected_package"] is products.package
        assert arguments["reveal_authority_id"] == products.reveal.object_id
        yield read
        calls.append("closed")

    monkeypatch.setattr(scientific_read, "read_protected_e3_original_products", actual_read)
    monkeypatch.setattr(owner, "_current_control", lambda **_: products.package)
    arguments = dict(directory=tmp_path, selected=object(), project_root=tmp_path,
        artifact_writer=products.plane, selection_path=path)
    return SimpleNamespace(selection=selection, path=path, arguments=arguments, read=read,
        calls=calls, products=products)


def test_public_prospective_export_dispatches_retained_owner_without_runtime_composition(export_case, monkeypatch):
    from empirical_lawhood.api import experiment_preparation, recursive_authoring

    selected = RetainedProspectiveExperiment(None,
        SimpleNamespace(specification=export_case.read.specification.identity), None, None, None, None, {})
    monkeypatch.setattr(ExperimentProgrammeService, "_composite_programme", lambda *_, **__: None)
    monkeypatch.setattr(ExperimentProgrammeService, "_is_prospective", lambda *_, **__: True)
    monkeypatch.setattr(experiment_preparation, "experiment_protocols", lambda: EXPERIMENT_PROTOCOL_DECLARATIONS)
    monkeypatch.setattr(recursive_authoring, "load_authored_wave", lambda **_: pytest.fail("development loader entered"))
    service = ExperimentProgrammeService(export_case.arguments["project_root"], export_case.products.plane,
        prospective_experiment_loader=lambda **_: selected,
        prospective_api_factory=lambda **_: pytest.fail("runtime composition entered"))
    report = service.export_products(directory=export_case.arguments["directory"], selection_path=export_case.path)
    assert export_case.calls == ["full-read", "current", "closed"]
    assert report["scientific_result"] == export_case.products.report
    json.dumps(report)
    public = decode_canonical_bytes(Path(report["paths"]["package"]).read_bytes(),
        ConfiguredMatrixSelectedPublicPackage, maximum_bytes=None)
    assert public.models == export_case.products.full.models
    assert public.calibration == owner._identity(export_case.products.full.calibration)
    assert public.selection_unit_ids == export_case.products.full.selection_unit_ids
    assert b'"scores"' not in public.canonical_bytes()
    manifests = tuple(decode_artifact_manifest(Path(path + ".manifest.json").read_bytes())
        for path in report["paths"].values())
    assert len(manifests) == 5
    # An exposed TRAIN member makes the whole export exposed; sealed CAL members
    # cannot turn any part of this synthetic development package into fresh data.
    assert {manifest.logical.outcome_access for manifest in manifests} == {OutcomeAccess.DEVELOPMENT_VISIBLE}
    assert all(manifest.logical.lineage_parents == manifests[0].logical.lineage_parents for manifest in manifests)
    for name, operation, mode in owner._PRODUCTS:
        locator = decode_canonical_bytes(Path(report["paths"][name]).read_bytes(),
            MatrixSelectedOriginalProduct, maximum_bytes=None)
        task = statistical_task_id(public.specification.identity, public.allocation.identity, operation, mode=mode)
        assert locator.prior_execution.receipt == owner._identity(export_case.products.receipts[task], "receipt_id")
        assert locator.prior_execution.record == owner._identity(getattr(export_case.products.full, name.replace("-", "_")))
        assert locator.reveal_authority == export_case.products.reveal
    before = {path: Path(path).read_bytes() for path in report["paths"].values()}
    again = service.export_products(directory=export_case.arguments["directory"], selection_path=export_case.path)
    assert again["public_package"] == report["public_package"]
    assert before == {path: Path(path).read_bytes() for path in again["paths"].values()}
    assert export_case.calls.count("full-read") == export_case.calls.count("current") == 2


@pytest.mark.parametrize("damage", ("package", "model", "prefit", "missing-receipt", "wrong-receipt", "output", "grant"))
def test_export_refuses_changed_originals_or_current_grant_before_publication(export_case, damage):
    value = export_case
    fit = statistical_task_id(value.read.specification.identity, value.read.allocation.identity, "fit")
    if damage == "package":
        value.path.write_bytes(replace(value.selection,
            original_package=replace(value.selection.original_package, object_fingerprint="f" * 64)).canonical_bytes())
    elif damage == "model":
        value.read.models = replace(value.read.models, record_id="models.foreign")
    elif damage == "prefit":
        value.read.prefit = replace(value.read.prefit, record_id="prefit.foreign")
    elif damage == "missing-receipt":
        value.read.receipts.pop(fit)
    elif damage == "wrong-receipt":
        value.read.receipts[fit] = replace(value.read.receipts[fit], run_id="run.foreign")
    elif damage == "output":
        receipt = value.read.receipts[fit]
        value.read.receipts[fit] = replace(receipt, output_logical_artifacts=(),
            output_materializations=())
    else:
        def denied():
            raise PermissionError("current export grant revoked")
        value.read.require_current = denied
    with pytest.raises((ValueError, PermissionError)):
        owner.export_configured_protected_e3_products(**value.arguments)
    assert not value.products.plane.root.resolve(value.selection.output_relative_path, for_write=False).exists()


def test_export_preserves_foreign_target_and_never_publishes_partial_batch(export_case):
    target = export_case.products.plane.root.resolve(export_case.selection.output_relative_path + "/models.locator.json",
        for_write=True)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"retained foreign bytes")
    with pytest.raises(ArtifactIdentityConflict, match="immutable artifact identity already exists"):
        owner.export_configured_protected_e3_products(**export_case.arguments)
    assert target.read_bytes() == b"retained foreign bytes"
    assert not (target.parent / "package.json").exists()


def test_registered_canonical_selection_refuses_traversal_and_foreign_package():
    declaration = next(value for value in EXPERIMENT_PROTOCOL_DECLARATIONS
        if value.protocol_id == "matrix.response-error.configured-protected-v2")
    configuration = next(value for value in declaration.configuration_inputs
        if value.consumer_id == "matrix-configured-protected-product-export")
    path = Path(__file__).resolve().parents[1] / configuration.example_paths[0]
    raw = path.read_bytes()
    selection = decode_canonical_bytes(raw, configuration.record_type, maximum_bytes=configuration.maximum_config_bytes)
    assert selection.canonical_bytes() == raw
    assert ConfiguredProtectedE3ProductExportSelection in declaration.input_record_types
    for relative in ("../escape", "/absolute", ".", "exports/../escape"):
        with pytest.raises(ValueError):
            replace(selection, output_relative_path=relative)
    with pytest.raises(TypeError):
        replace(selection, original_package=replace(selection.original_package, object_schema="empirical-lawhood/testing/foreign"))
