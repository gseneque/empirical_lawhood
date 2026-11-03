# SPDX-License-Identifier: MPL-2.0
"""Cold scientific declarations and plans preserve causal stage barriers."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

import pytest

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef, CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import (
    BarrierKind, OutputTemplate, ProtocolStepTemplate, ScientificStage,
    validate_scientific_stage_barrier,
)
from empirical_lawhood.runtime.recursive_compiler import RegisteredPublicationRequirement
from empirical_lawhood.runtime.recursive_provider import (
    RecursiveExecutionProperties, RecursiveInquiryHooks, RecursiveOperationDeclaration,
    RecursiveScientificHooks,
)


@dataclass(frozen=True, slots=True)
class BarrierConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/stage-barrier-config"
    config_id: str


BUDGET = ResourceBudget(1, 4096, 0, 1, 4096, 4096)
VALID_PAIRS = (
    (ScientificStage.FREEZE, BarrierKind.FREEZE),
    (ScientificStage.EVALUATE, BarrierKind.REVEAL),
    (ScientificStage.REVEAL, BarrierKind.REVEAL),
)
INVALID_PAIRS = tuple((stage, barrier) for stage, required in VALID_PAIRS
                      for barrier in BarrierKind if barrier is not required)


def _forbidden(*_args, **_kwargs):
    raise AssertionError("cold declaration or plan invoked scientific/native work")


def _declaration(stage=ScientificStage.TRANSFORM, barrier=BarrierKind.NONE):
    return RecursiveOperationDeclaration(
        capability_key="testing.stage-barrier", capability_version="1.0.0", implementation_id="testing.stage-barrier.v1",
        kind=({ScientificStage.PREPARE: CapabilityKind.SOURCE,
               ScientificStage.REPORT: CapabilityKind.REPORTER,
               ScientificStage.EVALUATE: CapabilityKind.EVALUATOR,
               ScientificStage.REVEAL: CapabilityKind.EVALUATOR}.get(stage, CapabilityKind.TRANSFORM)),
        config_record_type=BarrierConfig, stage=stage, input_ports=(),
        outputs=(OutputTemplate("result", BarrierConfig.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                                "application/json", ".json"),),
        permissions=(CapabilityPermission.READ_SEALED_OUTCOMES, CapabilityPermission.REVEAL_OUTCOMES)
            if stage in (ScientificStage.EVALUATE, ScientificStage.REVEAL) else (),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.EVALUATOR_REVEAL if stage in (ScientificStage.EVALUATE, ScientificStage.REVEAL)
            else OutcomeAccess.OUTCOME_BLIND,
        visibility_ceiling=VisibilityCeiling.OUTCOME_VISIBLE if stage in (ScientificStage.EVALUATE, ScientificStage.REVEAL)
            else VisibilityCeiling.PROSPECTIVE,
        resources=BUDGET, conformance_check_ids=("check.stage-barrier",), runner_factory=_forbidden,
        record_codecs={BarrierConfig.SCHEMA: BarrierConfig},
        scientific_hooks=RecursiveScientificHooks(scientific_root_validator=_forbidden),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_work_projector=_forbidden),
        execution_properties=RecursiveExecutionProperties(barrier=barrier,
            runner_preparation_factory=_forbidden),
        publication_requirements=(RegisteredPublicationRequirement("publication.stage-barrier", _forbidden),),
    )


def _step(stage, barrier):
    config = BarrierConfig("config.stage-barrier")
    return ProtocolStepTemplate(
        "step.stage-barrier", stage, "testing.stage-barrier", "1.0.0",
        CapabilityConfigRef(config.config_id, config.SCHEMA, sha256(config.SCHEMA.encode()).hexdigest(),
                            config.fingerprint(), "artifact.stage-barrier-config"),
        (), (OutputTemplate("result", BarrierConfig.SCHEMA, ArtifactProfile.CANONICAL_JSON,
                            "application/json", ".json"),),
        (), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, BUDGET, (), barrier, 1,
        ("obligation.stage-barrier",),
    )


def test_declaration_preserves_explicit_manifest_identity_without_running_hooks():
    declaration = _declaration()
    default = declaration.manifest()
    assert default.runtime_id == declaration.capability_key
    assert default.implementation_sha256 == sha256(
        (declaration.capability_key + '.' + declaration.implementation_id).encode()).hexdigest()
    digest = sha256(b'original-current-manifest-preimage').hexdigest()
    selected = replace(declaration, runtime_id='cpython-current-native', implementation_sha256=digest)
    manifest, factory = selected.manifest(), selected.provider_factory()
    assert manifest == replace(default, runtime_id='cpython-current-native', implementation_sha256=digest)
    assert factory.manifest == manifest
    assert factory.registration.selection.implementation_sha256 == digest
    assert factory.binding.capability_implementation_sha256 == digest


@pytest.mark.parametrize('changes', (
    {'runtime_id': ''}, {'runtime_id': 'contains whitespace'},
    {'implementation_sha256': 'f' * 63}, {'implementation_sha256': 'g' * 64},
))
def test_declaration_rejects_malformed_explicit_manifest_identity(changes):
    with pytest.raises(ValueError, match='runtime_id|implementation_sha256'):
        replace(_declaration(), **changes)


def test_extra_manifest_schema_preserves_advertisement_without_inventing_a_port():
    declaration = _declaration()
    schema = 'empirical-lawhood/testing/declared-input-metadata'
    selected = replace(declaration, additional_input_schema_ids=(schema,))
    assert selected.manifest().input_schema_ids == tuple(sorted((BarrierConfig.SCHEMA, schema)))
    assert selected.registration().input_ports == declaration.registration().input_ports == ()
    with pytest.raises(ValueError, match='schema'):
        replace(declaration, additional_input_schema_ids=('not-a-schema',))


@pytest.mark.parametrize("stage,barrier", INVALID_PAIRS)
def test_invalid_freeze_evaluate_reveal_barriers_refuse_at_cold_declaration(stage, barrier):
    with pytest.raises(ValueError, match="requires a freeze barrier|require a reveal barrier"):
        _declaration(stage, barrier)


@pytest.mark.parametrize("stage,barrier", INVALID_PAIRS)
def test_same_invalid_pairs_refuse_in_the_shared_guard_and_lowered_plan(stage, barrier):
    with pytest.raises(ValueError, match="requires a freeze barrier|require a reveal barrier"):
        validate_scientific_stage_barrier(stage, barrier)
    with pytest.raises(ValueError, match="requires a freeze barrier|require a reveal barrier"):
        _step(stage, barrier)


@pytest.mark.parametrize("stage,barrier", VALID_PAIRS)
def test_valid_stage_barriers_project_without_calling_runner_or_domain_hooks(stage, barrier):
    declaration = _declaration(stage, barrier)
    registration = declaration.registration()
    factory = declaration.provider_factory()
    step = _step(stage, barrier)
    assert registration.stage is stage
    assert registration.barrier is barrier
    assert factory.registration == registration
    assert factory.runner_factory is _forbidden
    assert factory.runner_preparation_factory is _forbidden
    assert declaration.scientific_hooks.scientific_root_validator is _forbidden
    assert declaration.publication_requirements[0].validate is _forbidden
    assert step.stage is stage and step.barrier is barrier


@pytest.mark.parametrize("stage,barrier", (
    ("FREEZE", BarrierKind.FREEZE), (ScientificStage.FREEZE, "FREEZE"),
    (None, BarrierKind.NONE), (ScientificStage.TRANSFORM, None),
))
def test_string_or_untyped_stage_barrier_cannot_bypass_the_declaration_contract(stage, barrier):
    with pytest.raises(TypeError, match="exact typed contracts"):
        _declaration(stage, barrier)
    with pytest.raises(TypeError, match="exact typed contracts"):
        _step(stage, barrier)


def test_editing_a_valid_declaration_cannot_drop_its_freeze_or_reveal_barrier():
    declaration = _declaration(ScientificStage.FREEZE, BarrierKind.FREEZE)
    with pytest.raises(ValueError, match="requires a freeze barrier"):
        replace(declaration, execution_properties=replace(declaration.execution_properties, barrier=BarrierKind.NONE))
    with pytest.raises(ValueError, match="require a reveal barrier"):
        replace(declaration, stage=ScientificStage.EVALUATE)


@pytest.mark.parametrize("stage", (ScientificStage.PREPARE, ScientificStage.TRANSFORM, ScientificStage.REPORT))
def test_non_sensitive_stages_retain_the_existing_none_barrier_contract(stage):
    declaration = _declaration(stage, BarrierKind.NONE)
    assert declaration.registration().barrier is BarrierKind.NONE
    assert _step(stage, BarrierKind.NONE).barrier is BarrierKind.NONE


def test_installed_recursive_operations_agree_with_lifecycle_and_both_compilers():
    from empirical_lawhood.adapters.composition.generated_executable_bindings import _EXECUTABLE_FACTORIES
    from empirical_lawhood.runtime.candidate_compiler import _ALLOWED_STAGE_KINDS
    from empirical_lawhood.runtime.compiler import _validate_stage_capability
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.recursive_provider import RecursiveOperationProviderFactory
    from empirical_lawhood.runtime.stage_contracts import stage_kind_allowed

    factories = tuple(value for value in _EXECUTABLE_FACTORIES
                      if isinstance(value, RecursiveOperationProviderFactory))
    assert factories
    for factory in factories:
        registration, manifest = factory.registration, factory.manifest
        lifecycle, = registration.supported_lifecycles
        assert stage_kind_allowed(registration.stage, manifest.kind, lifecycle=lifecycle), manifest.registry_id
        if lifecycle is PlanLane.DEVELOPMENT:
            assert registration.visibility_ceiling is VisibilityCeiling.DEVELOPMENT_ONLY
            assert registration.outcome_access is OutcomeAccess.DEVELOPMENT_VISIBLE
            continue
        # The actual candidate predicate and runtime access validator must accept
        # every installed prospective registration without constructing a runner.
        assert manifest.kind in _ALLOWED_STAGE_KINDS[registration.stage], manifest.registry_id
        step = ProtocolStepTemplate('step.registry-stage-control', registration.stage,
            manifest.capability_key, manifest.capability_version,
            CapabilityConfigRef('config.registry-stage-control', manifest.config_schema,
                manifest.config_schema_sha256, 'a'*64, 'artifact.registry-stage-control'),
            (), registration.outputs, registration.required_permissions, registration.outcome_access,
            registration.visibility_ceiling, registration.resource_ceiling, (), registration.barrier,
            1, ('obligation.registry-stage-control',))
        _validate_stage_capability(step, manifest.kind)


def test_development_kind_exceptions_never_become_prospective_support():
    from empirical_lawhood.runtime.compiler import ProtocolCompilationError, _validate_stage_capability
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.stage_contracts import stage_kind_allowed

    assert stage_kind_allowed(ScientificStage.PREPARE, CapabilityKind.ANALYSIS, lifecycle=PlanLane.DEVELOPMENT)
    assert not stage_kind_allowed(ScientificStage.PREPARE, CapabilityKind.ANALYSIS)
    with pytest.raises(ProtocolCompilationError, match='forbidden'):
        _validate_stage_capability(_step(ScientificStage.PREPARE, BarrierKind.NONE), CapabilityKind.ANALYSIS)
    with pytest.raises(ValueError, match='stage/lifecycle'):
        replace(_declaration(), stage=ScientificStage.PREPARE, kind=CapabilityKind.ANALYSIS)




def test_development_provenance_does_not_relabel_blind_sealed_or_revealed_access():
    from empirical_lawhood.runtime.plans import PlanLane
    from empirical_lawhood.runtime.stage_contracts import operation_lifecycle, stage_kind_allowed

    assert operation_lifecycle(outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY) is PlanLane.DEVELOPMENT
    for access in (OutcomeAccess.OUTCOME_BLIND, OutcomeAccess.EVALUATION_SEALED,
            OutcomeAccess.EVALUATOR_REVEAL, OutcomeAccess.EVALUATION_REVEALED):
        lifecycle = operation_lifecycle(outcome_access=access, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        assert lifecycle is PlanLane.PROSPECTIVE
        # A provenance ceiling never grants the development stage exception.
        assert not stage_kind_allowed(ScientificStage.PREPARE, CapabilityKind.ANALYSIS, lifecycle=lifecycle)
        assert stage_kind_allowed(ScientificStage.EVALUATE, CapabilityKind.EVALUATOR, lifecycle=lifecycle)
    with pytest.raises(TypeError, match="typed access"):
        operation_lifecycle(outcome_access=OutcomeAccess.OUTCOME_BLIND.value,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
