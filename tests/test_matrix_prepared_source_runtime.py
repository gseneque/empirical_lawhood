# SPDX-License-Identifier: MPL-2.0
"""Real public/custody refusal controls; no prepared/native qualification claim."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import matrix_prepared_source_runtime as owner
from empirical_lawhood.api.recursive_authoring import author_recursive_wave
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_recursive_public_service import _draft, _plane

ROOT = Path(__file__).resolve().parents[1]


def test_actual_author_only_development_cannot_supply_control_custody_or_publish_inputs(tmp_path, monkeypatch):
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    plane = _plane(tmp_path / "control")
    directory = tmp_path / "control" / "authored"
    author_recursive_wave(draft=_draft(), project_root=ROOT, artifact_writer=plane, output_dir=directory)
    before = {path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    def forbidden(*args, **kwargs):
        raise AssertionError("instrument control read attempted execution")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    monkeypatch.setattr(LocalProcessExecutor, "execute_deadline_free", forbidden)
    with pytest.raises(ValueError, match="retained input materialization"):
        owner._complete_development(plane, directory, validate_authored=lambda **roots: None)
    assert {path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize("phase", ("E5_CONFIRMATION", "E6_TRANSFER"))
def test_prepared_gate_requires_actual_current_issued_method_before_control_reads(actual_issued_current_task_controls, monkeypatch, phase):  # noqa: F811
    from empirical_lawhood.adapters.methods import matrix_prepared_source_bindings as bindings
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as records
    from empirical_lawhood.api.current_task_custody import current_issued_task_control_scope
    from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
    from empirical_lawhood.runtime.executable_bindings import ExecutablePlatformPort
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationInputPort
    f = actual_issued_current_task_controls
    supplier = owner.MatrixPreparedSourceRuntimeInputSupplier(SimpleNamespace(
        resolve_input=lambda spec: pytest.fail("foreign task read scientific control inputs")), custody=f.custody)
    f.control.service.executable_platform_ports = (ExecutablePlatformPort("prepared-source.control", RecursiveOperationInputPort(supplier)),)
    gate = bindings.MatrixPreparedSourceGateWorker(records.GATES[0], phase)
    context = replace(f.context, permissions=gate.manifest.permissions)
    loads = []
    original = ExternalStudyOperationAuthorityStore.load
    def current(self, authority_id):
        loads.append(authority_id)
        return original(self, authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, "load", current)
    monkeypatch.setattr(owner, "authenticate_prepared_source_certificate", lambda **kwargs:
        pytest.fail("foreign issued task reached certificate reconstruction"))
    with current_issued_task_control_scope(f.control.api):
        with pytest.raises(PermissionError, match="actual current installed task/config/access"):
            supplier.prepare_matrix_prepared_source_gate(context, gate)
    assert f.control.package.execution_authority.authority_id in loads
    assert f.custody._control_reader is None


def test_current_conf_exposure_requires_immutable_baseline_and_actual_sequence_union(tmp_path):
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    from tests.test_matrix_factor_confirmation_eligibility import publish
    case = fresh_training_metadata_case(tmp_path)
    original = case.request.future_manifest.audit
    baseline = original.census
    extra_seed = next(value for value in range(1, 100) if value not in baseline.effective_seed_exclusions)
    extra_group = "group.actual.disclosed.e4-control"
    coordinate = case.request.train_manifest.reservation.allocation.coordinates[0]
    from empirical_lawhood.adapters.methods.matrix_factor_response.exposure import (
        MANDATORY_EFFECTIVE_SEEDS, MatrixScheduledPhysicalExclusion,
    )
    current_census = replace(baseline,
        effective_seed_exclusions=tuple(sorted((*baseline.effective_seed_exclusions, extra_seed))),
        scheduled_physical_exclusions=tuple(sorted({*baseline.scheduled_physical_exclusions,
            MatrixScheduledPhysicalExclusion.from_coordinate(coordinate)},key=lambda value:value.fingerprint())),
        exposed_independent_groups=tuple(sorted((*baseline.exposed_independent_groups, extra_group))))

    def published_audit(census, coordinates=(coordinate,)):
        records = (census, *coordinates)
        publications = tuple(sorted((publish(case.plane, value, "current.conf." + value.fingerprint())
            for value in records), key=lambda value: value.logical.logical_artifact_id))
        return replace(original, audit_id="audit.actual.current-conf." + census.fingerprint(), census=census,
            prior_scheduled_coordinates=coordinates, prior_corpus=publications)

    current = published_audit(current_census)
    parameters = dict(effective_seeds=(extra_seed,), group_ids=(extra_group,), coordinates=(coordinate,))
    owner._require_current_exposure_subset(original, current, **parameters)
    # Every negative retains a real, exact publication for its changed census;
    # a committed marker alone cannot replace the complete source exposure join.
    for damaged in (original,
            published_audit(replace(current_census, effective_seed_exclusions=baseline.effective_seed_exclusions)),
            published_audit(replace(current_census, exposed_independent_groups=baseline.exposed_independent_groups)),
            published_audit(current_census, ())):
        with pytest.raises(PermissionError):
            owner._require_current_exposure_subset(original, damaged, **parameters)
    original_extras = set(baseline.effective_seed_exclusions) - MANDATORY_EFFECTIVE_SEEDS
    assert original_extras
    without_original = replace(current_census, effective_seed_exclusions=tuple(value
        for value in current_census.effective_seed_exclusions if value not in original_extras))
    with pytest.raises(PermissionError, match="original exposure"):
        owner._require_current_exposure_subset(original, published_audit(without_original), **parameters)


def test_prepared_current_support_uses_actual_bytes_before_certificate_publication(tmp_path):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    from tests.test_matrix_native_training_acquisition import fresh_training_metadata_case
    case = fresh_training_metadata_case(tmp_path)
    for artifact, custody in case.request.exposure_support:
        _authenticate_artifact(case.plane, artifact, custody)
    artifact, custody = case.request.exposure_support[0]
    path = case.plane.root.resolve(custody.materialization.relative_path, for_write=False)
    path.write_bytes(b"x" * artifact.size_bytes)
    from empirical_lawhood.infrastructure.artifact_stream_primitives import ArtifactPlaneError
    with pytest.raises((PermissionError, ValueError, ArtifactPlaneError)):
        _authenticate_artifact(case.plane, artifact, custody)
