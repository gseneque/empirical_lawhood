"""Public finite-stage selections with exact precontact parent refusals."""
from empirical_lawhood.domains.matrix.finite_response_law.authoring.stage_input import FiniteResponseLawStageInput as _science_FiniteResponseLawStageInput, _build_assigned_calibration

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.matrix.finite_response_law.authoring.assignment import FiniteResponseLawCohortAssignment, assigned_native_seed_ids
from empirical_lawhood.domains.matrix.finite_response_law.authoring.exposure import native_seed_collisions
from empirical_lawhood.adapters.composition.finite_response_law.native_input import _census
from empirical_lawhood.adapters.composition.prepared_response.native_authoring import _read_external, _read_plan
from empirical_lawhood.domains.matrix.finite_response_law.science import FiniteResponseLawScienceSpec
from empirical_lawhood.science.identity.provenance import ObjectIdentity

from empirical_lawhood.domains.matrix.finite_response_law.authoring.stage_input import STAGE_BINDINGS as _science_STAGE_BINDINGS








def check_finite_stage_input(
    config: _science_FiniteResponseLawStageInput,
    *,
    source_root: Path | None,
    plan: Path | None,
    prior_exposure: Path | None,
    assignment: FiniteResponseLawCohortAssignment | None,
    parent_manifest: Path | None,
    custody: Path | None,
    reveal_record: Path | None,
    analysis_record: Path | None,
    authority_store=None,
    authoring_input: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Select the real factory and stop at the first missing safe input gate."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY

    if source_root is None:
        raise ValueError("FINITE_RESPONSE_LAW_SOURCE_ROOT_REQUIRED")
    if plan is None:
        raise ValueError("FINITE_RESPONSE_LAW_PLAN_REQUIRED")
    if prior_exposure is None:
        raise ValueError("FINITE_RESPONSE_LAW_PRIOR_EXPOSURE_REQUIRED")
    plan_sha = sha256(_read_plan(plan)).hexdigest()
    if plan_sha != FiniteResponseLawScienceSpec().plan_sha256:
        raise ValueError("FINITE_RESPONSE_LAW_PLAN_MISMATCH: plan differs from frozen science")
    prior_raw, _ = _read_external(source_root, prior_exposure, 128 * 1024**2)
    excluded_units, excluded_seeds = _census(prior_raw)
    binding_id, factory_name, ports = _science_STAGE_BINDINGS[config.stage]
    factory = (
        None
        if config.stage == "informative-composition"
        else EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY.factory(binding_id)
    )
    if factory is not None and type(factory).__name__ != factory_name:
        raise ValueError("FINITE_RESPONSE_LAW_REGISTERED_BINDING_MISMATCH")
    report: dict[str, object] = {
        "config_id": config.config_id,
        "stage": config.stage,
        "target_prefix": config.target_prefix,
        "evidence_role": config.evidence_role,
        "binding_id": binding_id,
        "binding_selected": factory_name,
        "missing_port_keys": list(ports),
        "provider_built": False,
        "native_plan_sha256": plan_sha,
        "prior_exposure_sha256": sha256(prior_raw).hexdigest(),
        "prior_custody_authenticated": False,
        "parent_custody_authenticated": False,
        "target_reveal_authorized": False,
        "target_analysis_authorized": False,
        "independent_units": 0,
        "nested_views_per_unit": 2,
        "native_tasks_planned": 0,
        "native_tasks_executed": 0,
        "analysis_tasks_executed": 0,
        "campaign_candidate_compiled": False,
        "campaign_issued": False,
    }
    assigned_stage = (
        "prospective-evaluation" if config.stage in ("prospective-evaluation", "prospective-continuation") else "calibration"
    )
    if config.stage in ("calibration", "prospective-evaluation", "prospective-continuation"):
        if assignment is None:
            raise ValueError("FINITE_RESPONSE_LAW_ASSIGNMENT_REQUIRED")
        if (
            assignment.stage != assigned_stage
            or assignment.science_plan_sha256 != plan_sha
        ):
            raise ValueError("FINITE_RESPONSE_LAW_ASSIGNMENT_MISMATCH: stage or frozen plan")
        units = assignment.physical_unit_ids
        seeds = assigned_native_seed_ids(assignment)
        unit_collisions = set(units) & set(excluded_units)
        seed_collisions = (
            set(seeds) & set(excluded_seeds)
            if config.stage == "prospective-continuation"
            else native_seed_collisions(seeds, excluded_seeds)
        )
        if config.stage == "prospective-continuation":
            if unit_collisions != set(units) or seed_collisions != set(seeds):
                raise ValueError(
                    "FINITE_RESPONSE_LAW_RETAINED_ROSTER_REQUIRED: original independent evaluation units and streams"
                )
        elif unit_collisions or seed_collisions:
            raise ValueError(
                "FINITE_RESPONSE_LAW_EXPOSED_ASSIGNED_ROSTER: "
                f"{len(unit_collisions)} units, {len(seed_collisions)} streams"
            )
        report.update(
            assignment_sha256=assignment.fingerprint(),
            cohort_namespace=assignment.cohort_namespace,
            independent_units=len(units),
        )
        report[
            "streams_reused"
            if config.stage == "prospective-continuation"
            else "streams_reserved"
        ] = len(seeds)
        if config.stage == "calibration":
            report.update(
                _build_assigned_calibration(
                    config,
                    assignment,
                    plan_sha,
                    sha256(prior_raw).hexdigest(),
                    excluded_units,
                    excluded_seeds,
                )
            )
            return report
    if parent_manifest is None:
        raise ValueError("FINITE_RESPONSE_LAW_PARENT_MANIFEST_REQUIRED")
    if custody is None:
        raise ValueError("FINITE_RESPONSE_LAW_TARGET_CUSTODY_REQUIRED")
    if reveal_record is None:
        raise ValueError("FINITE_RESPONSE_LAW_TARGET_REVEAL_REQUIRED")
    if analysis_record is None:
        raise ValueError("FINITE_RESPONSE_LAW_TARGET_ANALYSIS_REQUIRED")
    if authority_store is None:
        raise ValueError("FINITE_RESPONSE_LAW_TARGET_CUSTODY_STORE_REQUIRED")
    from empirical_lawhood.adapters.composition.response_parent_reader import read_authenticated_parent
    from empirical_lawhood.adapters.composition.prepared_response.native_authoring import _implementation_digest
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes

    from empirical_lawhood.domains.matrix.finite_response_law.authoring.consumer_input import FiniteResponseLawAuthoringInput, build_consumer_authoring, validate_parent_join
    from empirical_lawhood.adapters.composition.finite_response_law.consumer_ports import consumer_ports

    route = {
        "supplemental-development": "finite-response-law-supplemental-development",
        "informative-composition": "finite-response-law-informative-composition",
        "calibration-method": "finite-response-law-calibration-method",
        "prospective-evaluation": "finite-response-law-prospective-parent",
        "prospective-continuation": "finite-response-law-prospective-parent",
        "preparation-screening": "finite-response-law-preparation-screening",
    }[config.stage]
    primary = read_authenticated_parent(
        route=route,
        source_root=source_root,
        parent_manifest=parent_manifest,
        custody=custody,
        reveal_record=reveal_record,
        analysis_record=analysis_record,
        authority_store=authority_store,
    )
    if config.stage == "informative-composition":
        from empirical_lawhood.domains.matrix.finite_response_law.authoring.informative_composition_input import check_informative_composition_parent

        report.update(check_informative_composition_parent(primary, expected_plan_sha256=plan_sha))
        return report
    if authoring_input is None:
        raise ValueError("FINITE_RESPONSE_LAW_CONSUMER_INPUT_REQUIRED")
    if repo_root is None:
        raise ValueError("FINITE_RESPONSE_LAW_PROJECT_ROOT_REQUIRED")
    raw, _ = _read_external(source_root, authoring_input, 64 * 1024**2)
    packet = decode_canonical_bytes(
        raw, FiniteResponseLawAuthoringInput, maximum_bytes=64 * 1024**2
    )
    if packet.stage != config.stage or packet.source.science.plan_sha256 != plan_sha:
        raise ValueError("FINITE_RESPONSE_LAW_CONSUMER_SELECTION_MISMATCH")
    if assignment is not None and (
        getattr(packet.source, "cohort_namespace", None) != assignment.cohort_namespace
        or getattr(packet.source, "assignment_sha256", None) != assignment.fingerprint()
        or getattr(packet.source, "scientific_seeds", None) != assignment.scientific_seeds
        or tuple(root.physical_unit_id for root in packet.source.roots)
        != assignment.physical_unit_ids
    ):
        raise ValueError("FINITE_RESPONSE_LAW_CONSUMER_ASSIGNMENT_MISMATCH")
    parents = [primary]
    manifests = [parent_manifest]
    for additional in packet.additional_parents:
        parents.append(
            read_authenticated_parent(
                route=route,
                source_root=Path(additional.source_root),
                parent_manifest=Path(additional.parent_manifest),
                custody=Path(additional.custody),
                reveal_record=Path(additional.reveal_record),
                analysis_record=Path(additional.analysis_record),
                authority_store=authority_store,
            )
        )
        manifests.append(Path(additional.parent_manifest))
    validate_parent_join(packet, tuple(parents))
    exposure = ObjectIdentity.from_record(
        f"{config.target_prefix}.consumer-input", packet
    )
    bundle = build_consumer_authoring(
        packet,
        implementation_sha256=_implementation_digest(repo_root),
        exposure=exposure,
        current_units=excluded_units,
        current_seeds=excluded_seeds,
    )
    plane = getattr(authority_store, "plane", None)
    if plane is None:
        raise ValueError("FINITE_RESPONSE_LAW_TARGET_ARTIFACT_PLANE_REQUIRED")
    available = consumer_ports(
        packet=packet, bundle=bundle, plane=plane, manifests=tuple(manifests)
    )
    owners = inspect_consumer_providers(bundle, available)
    if packet.completion is not None:
        from empirical_lawhood.domains.matrix.finite_response_law.completion.extension import ASSIGNED_BINDING

        binding_id = ASSIGNED_BINDING.binding_id
    selected = next((row for row in owners if row["binding_id"] == binding_id), None)
    if selected is None:
        raise ValueError("FINITE_RESPONSE_LAW_SELECTED_STAGE_PROVIDER_MISSING")
    report.update(
        status="FINITE_RESPONSE_LAW_DEVELOPMENT_BINDING_READY",
        binding_id=selected["binding_id"],
        binding_selected=selected["factory"],
        provider_built=True,
        missing_port_keys=[],
        parent_custody_authenticated=True,
        target_reveal_authorized=True,
        target_analysis_authorized=True,
        primary_parent_sha256=primary.grant.parent.physical_sha256,
        parent_custody_sha256s=[parent.custody.fingerprint() for parent in parents],
        authoring_input_sha256=packet.fingerprint(),
        native_source_sha256=packet.source.fingerprint(),
        independent_units=len(packet.source.roots),
        native_tasks_planned=selected["native_tasks_planned"],
        selected_providers=owners,
        prospective_issue_eligible=False,
        nonacquiring_completion=packet.completion is not None,
        protocol_steps_planned=len(
            bundle.standard_context.base.templates[0].protocol.steps
        ),
    )
    return report


def inspect_consumer_providers(bundle, platform_ports) -> list[dict[str, object]]:
    """Resolve every retained owner selected by the builder's actual graph."""
    from empirical_lawhood.adapters.composition.generated_executable_bindings import EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    from dataclasses import asdict

    registry = bundle.standard_context.base.registry
    factories = EXECUTABLE_CAPABILITY_PROVIDER_FACTORY_REGISTRY
    capabilities = {
        step.capability_key
        for step in bundle.standard_context.base.templates[0].protocol.steps
    }
    owners = []
    for capability in sorted(capabilities):
        matching = [
            binding
            for binding in factories.aggregate.bindings
            if binding.capability_key == capability
        ]
        if len(matching) != 1:
            raise ValueError("FINITE_RESPONSE_LAW_STAGE_CAPABILITY_BINDING_AMBIGUOUS")
        binding = matching[0]
        factory = factories.provider_factory(binding.binding_id)
        schemas = {value.record_schema for value in binding.accepted_config_types}
        records = tuple(value for value in bundle.payloads if value.SCHEMA in schemas)
        ports = tuple(
            port
            for port in platform_ports
            if port.port_key in binding.required_platform_port_keys
        )
        provider = factory.build_provider(
            registry=registry, records=records, platform_ports=ports
        )
        runners = provider.runners(registry)
        if len(runners) != 1 or runners[0].manifest.capability_key != capability:
            raise ValueError("FINITE_RESPONSE_LAW_STAGE_RUNNER_MISMATCH")
        semantics = provider.output_semantic_contracts(registry)
        if {contract.payload_schema for contract in semantics} != set(
            runners[0].manifest.output_schema_ids
        ):
            raise ValueError("FINITE_RESPONSE_LAW_STAGE_OUTPUT_CONTRACT_MISMATCH")
        owners.append(
            {
                "binding_id": binding.binding_id,
                "factory": type(factory).__name__,
                "runner": type(runners[0]).__name__,
                "output_schema_ids": list(runners[0].manifest.output_schema_ids),
                "output_semantic_contracts": [asdict(contract) for contract in semantics],
                "provider_built": True,
                "native_tasks_planned": len(getattr(provider, "invocations", ())),
            }
        )
    return owners


__all__ = ['check_finite_stage_input']
