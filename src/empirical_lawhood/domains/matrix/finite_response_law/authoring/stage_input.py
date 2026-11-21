"""Scientific authored inputs, independent of retained-file and native access."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.domains.matrix.finite_response_law.authoring.assignment import FiniteResponseLawCohortAssignment, assigned_native_seed_ids
from empirical_lawhood.domains.matrix.finite_response_law.authoring.authoring import build_native_authoring
from empirical_lawhood.domains.matrix.finite_response_law.authoring.exposure import native_seed_ids
from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
from empirical_lawhood.domains.matrix.finite_response_law.science import FiniteResponseLawScienceSpec
from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedCalibrationConfig
from empirical_lawhood.adapters.simulators.finite_response_law.calibration import discovery as calibration_discovery
from empirical_lawhood.adapters.simulators.finite_response_law.calibration import extension as calibration_binding
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_sha256, validate_stable_id
from empirical_lawhood.design.source_qualification import PredecessorBoundSourceQualificationExperiment
from empirical_lawhood.execution.source_qualification import PredecessorBoundSourceQualificationSubstrateBinding


@dataclass(frozen=True, slots=True)
class FiniteResponseLawStageInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input'
    config_id: str
    stage: str
    target_prefix: str
    evidence_role: str

    def __post_init__(self) -> None:
        validate_stable_id(self.config_id, field_name="config_id")
        validate_stable_id(self.target_prefix, field_name="target_prefix")
        if (
            self.stage not in STAGE_BINDINGS
            or not self.config_id.startswith(
                f"empirical-lawhood-finite-response-law-{self.stage}-"
            )
            or not self.target_prefix.startswith(
                f"empirical-lawhood.finite-response-law.{self.stage}."
            )
            or self.evidence_role != "EXPOSED_DEVELOPMENT_NONPROMOTABLE"
        ):
            raise ValueError(
                "FINITE_RESPONSE_LAW_STAGE_INPUT_INVALID: selection or development role"
            )


@dataclass(frozen=True, slots=True)
class FiniteResponseLawPriorCensus(CanonicalRecord):
    """Exact development inspection, without receipt or issue authority."""

    SCHEMA: ClassVar[str] = 'empirical-lawhood/composition/finite-response-law/finite-response-law-prior-census'
    census_id: str
    plan_sha256: str
    source_file_sha256: str
    assignment_sha256: str
    excluded_unit_ids: tuple[str, ...]
    excluded_seed_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.census_id, field_name="census_id")
        for name in ("plan_sha256", "source_file_sha256", "assignment_sha256"):
            validate_sha256(getattr(self, name), field_name=name)
        for name in ("excluded_unit_ids", "excluded_seed_ids"):
            values = getattr(self, name)
            require_sorted_unique_strings(values, field_name=name)
            if not values:
                raise ValueError(
                    "prepared response finite prior census lacks its complete inspected set"
                )
            for value in values:
                validate_stable_id(value, field_name=name)


def _build_assigned_calibration(
    config: FiniteResponseLawStageInput,
    assignment: FiniteResponseLawCohortAssignment,
    plan_sha: str,
    prior_sha: str,
    excluded_units: tuple[str, ...],
    excluded_seeds: tuple[str, ...],
) -> dict[str, object]:
    """Build only the registered development providers, with no native task entry."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY

    manifest = calibration_discovery.SOURCE_CAPABILITY
    source = FiniteResponseLawAssignedCalibrationConfig(
        "calibration",
        FiniteResponseLawScienceSpec(),
        ObjectIdentity.from_record(manifest.capability_key, manifest),
        None,
        (),
        assignment.cohort_namespace,
        assignment.fingerprint(),
        assignment.scientific_seeds,
    )
    if tuple(
        root.physical_unit_id for root in source.roots
    ) != assignment.physical_unit_ids or native_seed_ids(
        source
    ) != assigned_native_seed_ids(assignment):
        raise ValueError("FINITE_RESPONSE_LAW_ASSIGNED_NATIVE_CENSUS_MISMATCH")
    census = FiniteResponseLawPriorCensus(
        f"{config.target_prefix}.prior-census",
        plan_sha,
        prior_sha,
        assignment.fingerprint(),
        excluded_units,
        excluded_seeds,
    )
    bundle = build_native_authoring(
        source=source,
        implementation_sha256=manifest.implementation_sha256,
        exposure=ObjectIdentity.from_record(census.census_id, census),
        exposed_unit_ids=excluded_units,
        exposed_seed_ids=excluded_seeds,
        new_seed_ids=native_seed_ids(source),
    )
    source_records = tuple(
        value
        for value in bundle.payloads
        if type(value)
        in (
            FiniteResponseLawAssignedCalibrationConfig,
            PredecessorBoundSourceQualificationExperiment,
            PredecessorBoundSourceQualificationSubstrateBinding,
        )
    )
    registry = GENERATED_EXTENSION_BUNDLE_AGGREGATE.capability_registry
    factories = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    provider = factories.provider_factory(
        calibration_binding.SOURCE_BINDING.binding_id
    ).build_provider(registry=registry, records=source_records, platform_ports=())
    runners = provider.runners(registry)
    if (
        len(source_records) != 3
        or len(provider.invocations) != 640
        or len(runners) != 1
        or runners[0].manifest != manifest
    ):
        raise ValueError("FINITE_RESPONSE_LAW_ASSIGNED_NATIVE_PROVIDER_MISMATCH")
    for binding, method_manifest in (
        (
            calibration_binding.PROJECTION_BINDING,
            calibration_discovery.PROJECTION_CAPABILITY,
        ),
        (
            calibration_binding.EVALUATION_BINDING,
            calibration_discovery.EVALUATION_CAPABILITY,
        ),
    ):
        method_config = next(
            value
            for value in bundle.payloads
            if value.SCHEMA == method_manifest.config_schema
        )
        method = factories.provider_factory(binding.binding_id).build_provider(
            registry=registry, records=(method_config,), platform_ports=()
        )
        selected = method.runners(registry)
        if len(selected) != 1 or selected[0].manifest != method_manifest:
            raise ValueError("FINITE_RESPONSE_LAW_ASSIGNED_METHOD_PROVIDER_MISMATCH")
    return {
        "status": "FINITE_RESPONSE_LAW_DEVELOPMENT_BINDING_READY",
        "source_contract_compatible": True,
        "provider_built": True,
        "projection_provider_built": True,
        "evaluation_provider_built": True,
        "native_runner_selected": type(runners[0]).__name__,
        "prior_census_sha256": census.fingerprint(),
        "native_source_sha256": source.fingerprint(),
        "native_tasks_planned": len(provider.invocations),
        "future_streams_per_unit": 2,
        "native_task_budget": 640,
        "native_updates_budget": 751104,
    }


STAGE_BINDINGS = {
    "informative-composition": (
        "retained-informative-composition-consumer",
        "RetainedInformativeCompositionConsumer",
        ("AUTHENTICATED_PARENT",),
    ),
    "calibration": (
        "binding.finite-response-law.calibration.source",
        'FiniteResponseLawCalibrationSourceFactory',
        (),
    ),
    "supplemental-development": (
        "binding.finite-response-law.source",
        'FiniteResponseLawSourceFactory',
        ("RETAINED_SOURCE_PORT",),
    ),
    "calibration-method": (
        "binding.finite-response-law.calibration-qualification",
        'FiniteResponseLawCalibrationQualificationFactory',
        ("CANDIDATE_PAYLOAD_PORT", "INPUT_RESOLVER_PORT"),
    ),
    "prospective-evaluation": (
        "binding.finite-response-law.evaluation.source",
        'FiniteResponseLawEvaluationSourceFactory',
        (
            "SOURCE_CONTROL_PORT",
            "CONTROL_RUNTIME_PORT",
            "CANDIDATE_PAYLOAD_PORT",
            "INPUT_RESOLVER_PORT",
            "SEALED_CONTROL_PORT",
            "REVEAL_CONTROL_PORT",
        ),
    ),
    "prospective-continuation": (
        "binding.finite-response-law.evaluation-continuation.source",
        'FiniteResponseLawContinuationSourceFactory',
        ("SOURCE_CONTROL_PORT", "IMPORT_RESOLVER_PORT", "INPUT_RESOLVER_PORT"),
    ),
    "preparation-screening": (
        "binding.finite-response-law.preparation-policy.source",
        'FiniteResponseLawPreparationPolicySourceFactory',
        ("PREPARATION_POLICY_RETAINED_SOURCE_PORT", "PREPARATION_POLICY_EVIDENCE_PORT"),
    ),
}
