# SPDX-License-Identifier: MPL-2.0
"""Preserved W1 identities and early refusal of inconsistent declarations."""

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.executable_binding import (
    EXECUTABLE_BINDING_CONTRIBUTION, EXECUTABLE_BINDING_FACTORIES,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.extension_bundle import (
    EXTENSION_BUNDLE_CONTRIBUTION,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.operation_bindings import (
    KineticJoinConfig, operation_declarations, operation_manifests, operation_registrations,
    scientific_operand_sha256s, scientific_root_validator, scientific_unit_ids,
)
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.recursive_translation import scientific_work
from empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.numerical_runtime import (
    KINETIC_PROVENANCE_REQUIREMENT, validate_kinetic_producing_provenance,
)
from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import (
    MATRIX_PROVENANCE_REQUIREMENT, validate_matrix_producing_provenance,
    validate_matrix_runtime_observation_json,
)
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.serialization import canonical_json_bytes


def test_declaration_migration_preserves_original_installed_descriptors():
    """These hashes are the selected descriptors captured before migration."""
    original = {"rubisco-kinetic-join.assay", "rubisco-kinetic-join.assess"}
    assert {row.capability_key: row.fingerprint() for row in operation_manifests() if row.capability_key in original} == {
        "rubisco-kinetic-join.assay": "4942fd9a283bffde5a0aa7d64a8ba2c2c6064db02e901e07c7929c65fe857b79",
        "rubisco-kinetic-join.assess": "2d4009b41d6617d2684010bfb234ae49ef93d253dadd072d63f59ea573e2bc62",
    }
    assert {row.binding.capability_key: row.binding.fingerprint() for row in EXECUTABLE_BINDING_FACTORIES
        if row.binding.capability_key in original} == {
        "rubisco-kinetic-join.assay": "b23c89cc1e31b3c0796d673bfaefe5aeedc2cb4f9e6299dc539987904fe3a838",
        "rubisco-kinetic-join.assess": "bca0c1a14c61d4cff7444de5833ceb4360c3b1df3117f653f46ff99076720cea",
    }
    assert {row.capability_key for row in EXECUTABLE_BINDING_CONTRIBUTION.bindings} == {
        *original, "rubisco-kinetic-join.gas-contrast"}
    assert {row.capability_key for row in EXTENSION_BUNDLE_CONTRIBUTION.capability_manifests} == {
        *original, "rubisco-kinetic-join.gas-contrast"}


def test_all_w1_projections_keep_the_declared_domain_validators_and_work():
    declarations = operation_declarations()
    assert tuple(row.registration() for row in declarations) == operation_registrations()
    assert tuple(row.manifest() for row in declarations) == operation_manifests()
    for declaration in declarations:
        if declaration.config_record_type is not KineticJoinConfig:
            continue
        assert declaration.config_record_type is KineticJoinConfig
        assert declaration.scientific_hooks.scientific_operand_sha256s is scientific_operand_sha256s
        assert declaration.scientific_hooks.scientific_unit_ids is scientific_unit_ids
        assert declaration.scientific_hooks.scientific_root_validator is scientific_root_validator
        assert declaration.inquiry_hooks.inquiry_work_projector is scientific_work
        assert declaration.provenance_requirements == (KINETIC_PROVENANCE_REQUIREMENT,)
        assert declaration.registration().provenance_requirements == (KINETIC_PROVENANCE_REQUIREMENT,)
        assert not declaration.registration().native_effect
    assert declarations[-1].provenance_requirements == ()


@pytest.mark.parametrize("change", ["missing-codec", "wrong-codec", "duplicate-output", "invalid-validator"])
def test_inconsistent_domain_declaration_refuses_without_constructing_runner(change):
    def forbidden():
        raise AssertionError("inconsistent declaration constructed a scientific runner")

    declaration = replace(operation_declarations()[0], runner_factory=forbidden)
    with pytest.raises((TypeError, ValueError)):
        if change in {"missing-codec", "wrong-codec"}:
            codecs = dict(declaration.record_codecs)
            schema = declaration.outputs[0].payload_schema
            if change == "missing-codec":
                del codecs[schema]
            else:
                codecs[schema] = KineticJoinConfig
            replace(declaration, record_codecs=codecs)
        elif change == "duplicate-output":
            replace(declaration, outputs=declaration.outputs * 2)
        else:
            replace(declaration, scientific_hooks=replace(declaration.scientific_hooks,
                scientific_root_validator="caller-selected-validator"))


def _profile_provenance(**change):
    """Disclosed profile predicate fixtures, with no producing-custody claim."""
    observation = {"python": "3.11.14", "numpy": "2.4.6", "scipy": "1.17.1",
        "system": "linux", "machine": "x86_64", "threadpools": ({"num_threads": 1},)}
    observation.update(change)
    sources = (("exposed-profile-fixture.py", sha256(b"exposed software fixture").hexdigest()),)
    return NumericalProducingProvenance(canonical_json_bytes(observation).decode(), "a" * 64,
        sources, sha256(canonical_json_bytes(sources)).hexdigest(), "b" * 40, False)


@pytest.mark.parametrize("validator", (validate_matrix_producing_provenance,
    validate_kinetic_producing_provenance))
@pytest.mark.parametrize("field,value", (("python", "3.11.99"), ("numpy", "0.0.0"),
    ("scipy", "0.0.0"), ("system", "darwin"), ("machine", "arm64")))
def test_domain_profile_requires_the_selected_versions_and_host(validator, field, value):
    assert validator(_profile_provenance()) is None
    with pytest.raises(ValueError, match="selected numerical profile"):
        validator(_profile_provenance(**{field: value}))


@pytest.mark.parametrize("validator", (validate_matrix_producing_provenance,
    validate_kinetic_producing_provenance))
@pytest.mark.parametrize("threadpools", (({"num_threads": 2},), ({"num_threads": True},),
    ({},), (None,), ("omitted",), "omitted"))
def test_domain_profile_preserves_the_single_thread_requirement(validator, threadpools):
    with pytest.raises(ValueError, match="single-thread bootstrap"):
        validator(_profile_provenance(threadpools=threadpools))


def test_matrix_profile_keeps_historical_observation_and_empty_pool_semantics():
    from empirical_lawhood.api.matrix_native_custody import MatrixNativeRuntimeObservation

    for provenance in (_profile_provenance(), _profile_provenance(threadpools=())):
        assert validate_matrix_runtime_observation_json(provenance.runtime_observation_json) is None
        assert MatrixNativeRuntimeObservation(provenance.runtime_observation_json).observation_json == (
            provenance.runtime_observation_json)
        assert validate_kinetic_producing_provenance(provenance) is None
    assert MATRIX_PROVENANCE_REQUIREMENT.validate_observation is validate_matrix_producing_provenance
    noncanonical = replace(_profile_provenance(), runtime_observation_json=json.dumps(
        json.loads(_profile_provenance().runtime_observation_json)))
    for validator in (validate_matrix_producing_provenance, validate_kinetic_producing_provenance):
        with pytest.raises(ValueError, match="exact canonical JSON"):
            validator(noncanonical)
        with pytest.raises(ValueError, match="producing provenance"):
            validator(object())


def test_shared_registered_dispatch_applies_kinetic_profile_to_recorded_provenance(monkeypatch):
    from empirical_lawhood.api.numerical_provenance import validate_registered_provenance
    from tests.test_rubisco_kinetic_join import operands

    draft = operands()[3]
    # Retained evidence is assessed without consulting the reader's host.
    monkeypatch.setattr("platform.python_version", lambda: "reader-profile-is-distinct")
    assert validate_registered_provenance(provenance=_profile_provenance(), draft=draft,
        registrations=operation_registrations()) is None
    with pytest.raises(ValueError, match="kinetic join.*selected numerical profile"):
        validate_registered_provenance(provenance=_profile_provenance(numpy="0.0.0"), draft=draft,
            registrations=operation_registrations())
