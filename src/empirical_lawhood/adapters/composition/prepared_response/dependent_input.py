"""Target dependent-refinement/fresh-response-calibration selection; historical parent paths cannot authorize an import."""
from empirical_lawhood.domains.matrix.prepared_response.authoring.dependent_input import PreparedResponseDependentAuthoring as _science_PreparedResponseDependentAuthoring, PreparedResponseDependentInput as _science_PreparedResponseDependentInput

import re
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.composition.response_parent_custody import ResponseParentTargetAuthorityStore
from empirical_lawhood.adapters.composition.response_parent_reader import read_authenticated_parent
from empirical_lawhood.domains.matrix.prepared_response.development_selection import PreparedResponseDevelopmentNominalLibrary
from empirical_lawhood.domains.matrix.prepared_response.qualification import PreparedResponseSourceQualificationEvaluation
from empirical_lawhood.science.records.decoding import decode_canonical_bytes







def check_dependent_input(
    config: _science_PreparedResponseDependentInput,
    *,
    source_root: Path | None,
    parent_manifest: Path | None,
    custody: Path | None,
    reveal_record: Path | None,
    analysis_record: Path | None,
    authority_store: ResponseParentTargetAuthorityStore | None = None,
    authoring_input: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Authenticate first, then select the retained qualified-parent builder."""

    parent = read_authenticated_parent(
        route=config.route,
        source_root=source_root,
        parent_manifest=parent_manifest,
        custody=custody,
        reveal_record=reveal_record,
        analysis_record=analysis_record,
        authority_store=authority_store,
    )
    parent_type = (
        PreparedResponseSourceQualificationEvaluation if config.route == "dependent-refinement" else PreparedResponseDevelopmentNominalLibrary
    )
    # Historical schemas are never relabelled as new target receipts. Their
    # custody witness remains usable for explicit historical analysis routes.
    if parent.grant.parent.source_schema != parent_type.SCHEMA:
        raise ValueError("PREPARED_RESPONSE_DEPENDENT_TARGET_TYPED_PARENT_REQUIRED")
    decoded = decode_canonical_bytes(parent.raw, parent_type, maximum_bytes=8 * 1024**2)
    if config.route == "dependent-refinement":
        roots = set()
        for observation in decoded.observations:
            match = re.match(r"^(.+?\.r[0-9]{3})\.", observation.object_id)
            if (
                match is None
                or observation.object_fingerprint not in parent.custody.artifact_sha256s
            ):
                raise ValueError("DEPENDENT_REFINEMENT_OBSERVATION_CUSTODY_INCOMPLETE")
            roots.add(match.group(1))
    else:
        roots = {
            root.root_id for root in decoded.config.fit.projection.native_spec.roots
        }
        if any(
            fit.object_fingerprint not in parent.custody.artifact_sha256s
            for fit in decoded.fits
        ):
            raise ValueError("FRESH_RESPONSE_CALIBRATION_FIT_CUSTODY_INCOMPLETE")
    if tuple(sorted(roots)) != parent.custody.original_root_ids:
        raise ValueError("PREPARED_RESPONSE_DEPENDENT_PARENT_ROOT_CUSTODY_MISMATCH")
    if config.route == "dependent-refinement" and decoded.selected_charter is None:
        raise ValueError("DEPENDENT_REFINEMENT_NO_COMMON_QUALIFIED_CHARTER")
    if config.route == "fresh-response-calibration" and (
        decoded.disposition != "NOMINATED_FOR_FRESH_CALIBRATION"
        or decoded.policy_library is None
    ):
        raise ValueError("FRESH_RESPONSE_CALIBRATION_NO_QUALIFIED_DEPENDENT_REFINEMENT_LIBRARY")
    if authoring_input is None:
        raise ValueError("PREPARED_RESPONSE_DEPENDENT_AUTHORING_INPUT_REQUIRED")
    if repo_root is None:
        raise ValueError("PREPARED_RESPONSE_DEPENDENT_PROJECT_ROOT_REQUIRED")
    from empirical_lawhood.adapters.composition.prepared_response.native_authoring import _implementation_digest, _read_external

    assert source_root is not None
    authoring_bytes, _ = _read_external(source_root, authoring_input, 64 * 1024**2)
    inputs = decode_canonical_bytes(
        authoring_bytes,
        _science_PreparedResponseDependentAuthoring,
        maximum_bytes=64 * 1024**2,
    )
    source = inputs.exposure.source_config
    if (
        source.stage != ("development" if config.route == "dependent-refinement" else "calibration")
        or source.seed_sha256 != config.source_seed_sha256
        or source.dependency_lock_sha256
        != sha256((repo_root / "uv.lock").read_bytes()).hexdigest()
        or any(
            not any(
                unit == root or unit.startswith(root + ".seed.")
                for unit in inputs.exposure.excluded_unit_ids
            )
            for root in parent.custody.original_root_ids
        )
    ):
        raise ValueError("PREPARED_RESPONSE_DEPENDENT_SOURCE_SELECTION_MISMATCH")
    if config.route == "dependent-refinement":
        from empirical_lawhood.domains.matrix.prepared_response.authoring.development_design import build_prepared_response_development_authoring

        bundle = build_prepared_response_development_authoring(
            design_packet_sha256=sha256(inputs.design_text.encode()).hexdigest(),
            implementation_sha256=_implementation_digest(repo_root),
            exposure=inputs.exposure,
            source_qualification=decoded,
            candidate_costs=inputs.candidate_costs,
        )
    else:
        from empirical_lawhood.domains.matrix.prepared_response.authoring.calibration_design import build_prepared_response_calibration_authoring

        bundle = build_prepared_response_calibration_authoring(
            design_packet_sha256=sha256(inputs.design_text.encode()).hexdigest(),
            implementation_sha256=_implementation_digest(repo_root),
            exposure=inputs.exposure,
            development_library=decoded,
        )
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from empirical_lawhood.execution.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.adapters.simulators.prepared_response.extension import CALIBRATION_SOURCE_BINDING, DEVELOPMENT_SOURCE_BINDING

    binding = DEVELOPMENT_SOURCE_BINDING if config.route == "dependent-refinement" else CALIBRATION_SOURCE_BINDING
    factory = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.provider_factory(
        binding.binding_id
    )
    records = tuple(
        record
        for record in bundle.payloads
        if record.SCHEMA in binding.accepted_record_schema_ids
    )
    registry = GENERATED_EXTENSION_BUNDLE_AGGREGATE.capability_registry
    provider = factory.build_provider(
        registry=registry, records=records, platform_ports=()
    )
    runners = provider.runners(registry)
    if (
        len(runners) != 1
        or runners[0].manifest.capability_key != binding.capability_key
    ):
        raise ValueError("PREPARED_RESPONSE_DEPENDENT_RUNNER_MISMATCH")
    return {
        "status": "PREPARED_RESPONSE_DEPENDENT_DEVELOPMENT_BINDING_READY",
        "route": config.route,
        "evidence_role": config.evidence_role,
        "parent_sha256": parent.grant.parent.physical_sha256,
        "parent_custody_sha256": parent.custody.fingerprint(),
        "parent_custody_authenticated": True,
        "target_reveal_authorized": True,
        "target_analysis_authorized": True,
        "binding_selected": binding.binding_id,
        "factory": type(factory).__name__,
        "provider_built": True,
        "runner_selected": type(runners[0]).__name__,
        "independent_units": len(source.roots),
        "nested_views_per_unit": 2,
        "authoring_sha256": bundle.authoring.fingerprint(),
        "prior_census_sha256": inputs.exposure.fingerprint(),
        "native_tasks_executed": 0,
        "analysis_tasks_executed": 0,
        "campaign_issued": False,
        "prospective_issue_eligible": False,
    }


__all__ = ['check_dependent_input']
