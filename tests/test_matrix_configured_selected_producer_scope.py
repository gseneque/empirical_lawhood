# SPDX-License-Identifier: MPL-2.0
"""Configured original producer predicates only; no issue/native authority."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from empirical_lawhood.api import matrix_selected_producer_scope as owner
from tests.test_matrix_selected_producer_scope import case_for
from tests.test_matrix_configured_selected_package import configured_package
from tests.test_matrix_e3_original_publications import case as original_case  # noqa: F401


@pytest.fixture(scope="module")
def selected(original_case):  # noqa: F811
    frozen, native_case = configured_package(original_case, return_context=True)
    return SimpleNamespace(frozen=frozen, training_coordinates=native_case.inputs.training_coordinates)


@pytest.mark.parametrize("phase", ("fit", "model-freeze", "calibrate", "calibration-freeze"))
def test_configured_original_scope_uses_exact_installed_native_bank_family(selected, phase, monkeypatch):
    case = case_for(phase, frozen=selected.frozen, training_coordinates=selected.training_coordinates)
    reads = []
    def read_config(*args):
        reads.append(args)
        return case.config
    monkeypatch.setattr(owner, "_read_config", read_config)
    owner.validate_selected_original_producer(**case.arguments)
    assert len(reads) == 1
    assert case.declaration.capability_key.startswith("matrix-e3-configured-protected.")
    if phase == "fit":
        assert case.declaration.capability_key.endswith(".native-fit")


@pytest.mark.parametrize("phase", ("fit", "model-freeze", "calibrate", "calibration-freeze"))
def test_configured_original_scope_refuses_legacy_owner_before_input_read(selected, phase, monkeypatch):
    case = case_for(phase, frozen=selected.frozen, training_coordinates=selected.training_coordinates)
    task = replace(case.task, capability=replace(case.task.capability, capability_key="matrix-e3-protected." + phase))
    case.arguments["execution_plan"].tasks = (task,)
    monkeypatch.setattr(owner, "_read_config", lambda *_: pytest.fail("foreign edition reached original science"))
    with pytest.raises(PermissionError, match="exact installed"):
        owner.validate_selected_original_producer(**case.arguments)


def test_native_bank_model_pins_refuse_configured_legacy_bank_fit_owner(selected, monkeypatch):
    case = case_for("fit", frozen=selected.frozen, training_coordinates=selected.training_coordinates)
    task = replace(case.task, capability=replace(case.task.capability, capability_key="matrix-e3-configured-protected.fit"))
    case.arguments["execution_plan"].tasks = (task,)
    monkeypatch.setattr(owner, "_read_config", lambda *_: pytest.fail("wrong TRAIN edition reached original science"))
    with pytest.raises(PermissionError, match="exact installed"):
        owner.validate_selected_original_producer(**case.arguments)


def test_configured_public_projection_reconstructs_exact_full_family(selected):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.api.matrix_selected_runtime import reconstruct_selected_package
    from tests.test_matrix_selected_package import package as legacy_package

    public = ConfiguredMatrixSelectedPublicPackage.from_package(selected.frozen)
    restored = reconstruct_selected_package(public, selected.frozen.calibration)
    assert type(restored) is type(selected.frozen) and restored == selected.frozen
    assert restored.canonical_bytes() == selected.frozen.canonical_bytes()
    with pytest.raises((TypeError, ValueError)):
        reconstruct_selected_package(public, legacy_package().calibration)
