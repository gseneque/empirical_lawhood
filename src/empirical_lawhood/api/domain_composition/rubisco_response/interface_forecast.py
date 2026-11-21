# SPDX-License-Identifier: MPL-2.0
"""Author and read the single-node recursive reconstruction from committed features."""

from hashlib import sha256
import json
import os
from pathlib import Path


def reconstruct(evidence, project, workspace):
    from empirical_lawhood.api.investigations import (
        create_investigation_service,
        create_local_workspace,
    )
    from empirical_lawhood.api.recursive_authoring import author_recursive_wave
    from empirical_lawhood.api.recursive_execution import (
        read_recursive_wave,
        run_recursive_wave,
    )
    from empirical_lawhood.design.campaigns import (
        CampaignLane,
        CampaignNode,
        CampaignNodeKind,
        CampaignSpec,
        DecisionRight,
    )
    from empirical_lawhood.design.recursive_authoring import (
        RecursiveOperationSpec,
        RecursiveStudyDraft,
    )
    from empirical_lawhood.domains.rubisco.rubisco_prediction.interface_forecast.extension import (
        BUDGET,
        FIT,
        KEY,
        InterfaceInput,
    )
    from empirical_lawhood.science.identity.authority import (
        AuthorityAction,
        AuthorityPolicy,
        SourceAccessClass,
    )
    from empirical_lawhood.science.evidence.evidence import (
        ClaimSpec,
        EvidenceCeiling,
        OutcomeAccess,
        VisibilityCeiling,
    )
    from empirical_lawhood.science.identity.provenance import ObjectIdentity
    from empirical_lawhood.science.inquiry.recursive_requirements import (
        DevelopmentStudySpec,
    )
    from empirical_lawhood.science.records.status import LifecycleStatus
    from empirical_lawhood.science.models.worlds import WorldKind

    raw = (evidence / "forecast.json").read_bytes()
    pin = dict(
        line.split()[::-1]
        for line in (evidence / "frozen-inputs.sha256").read_text().splitlines()
    )
    if sha256(raw).hexdigest() != pin["forecast.json"]:
        raise ValueError("Selected forecast was changed")
    source = json.loads(raw)["result"]
    features = {
        group: [
            {
                k: item[k]
                for k in (
                    ("id", "background", "features", "responses")
                    if group == "training"
                    else ("id", "background", "features")
                )
            }
            for item in source[group]
        ]
        for group in ("training", "queries")
    }
    config = InterfaceInput(
        source["design_sha256"],
        json.dumps(features, sort_keys=True, separators=(",", ":")),
    )
    system = ObjectIdentity.from_record("system.paired-ssu-interface-features", config)
    unit, view = "unit.published-ssu-panel", "view.exposed-reconstruction"
    claim = ClaimSpec(
        "claim.paired-ssu-reconstruction",
        "world.interface-numerics",
        "population.supplied-ssu-features",
        "Does the fixed two-output interface fit reconstruct the pre-assessment predictions?",
        "One frozen input panel.",
        unit,
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Numerical reconstruction of the published-fit predictions.",
        ("assumption.fixed-ssu-features",),
        numerical_view_ids=(view,),
    )
    root = DevelopmentStudySpec(
        "study.ssu-interface-reconstruction",
        claim.proposition,
        system,
        claim.world_id,
        WorldKind.ANALYTIC_REFERENCE,
        (unit,),
        (view,),
        (claim,),
        (system,),
    )
    policy = AuthorityPolicy(
        "policy.ssu-interface-reconstruction",
        "owner.local-researcher",
        "operator.local-development",
        (root.study_id,),
        frozenset((root.world_kind,)),
        frozenset(
            (
                AuthorityAction.REPOSITORY_IMPLEMENTATION,
                AuthorityAction.SIMULATION_EXECUTION,
            )
        ),
        frozenset((SourceAccessClass.NONE,)),
        ("gate.local-nonactuating-development",),
        frozenset(),
        BUDGET,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
    )
    node = CampaignNode(
        "design.ssu-interface",
        CampaignNodeKind.EVIDENCE_SNAPSHOT,
        CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(root.study_id, root),
        (),
        LifecycleStatus.ACTIVE,
    )
    campaign = CampaignSpec(
        "campaign.ssu-interface",
        root.question,
        (system.object_id,),
        (root.world_id,),
        (claim.claim_id,),
        BUDGET,
        ObjectIdentity.from_record(policy.policy_id, policy),
        (
            DecisionRight(
                "right.ssu-interface",
                AuthorityAction.SIMULATION_EXECUTION,
                "owner.local-researcher",
                policy.policy_id,
                False,
            ),
        ),
        (node,),
        (node.node_id,),
        (node.node_id,),
        (),
        LifecycleStatus.ACTIVE,
    )
    operation = RecursiveOperationSpec.from_config(
        node_id=KEY,
        selection=FIT.operation.registration().selection,
        config_id="config.paired-ssu-features",
        config=config,
        obligation_ids=("obligation.paired-ssu-complete-forecast",),
        resource_budget=BUDGET,
        maximum_attempts=1,
    )
    draft = RecursiveStudyDraft(
        "draft.ssu-interface-reconstruction",
        root.question,
        campaign,
        (),
        (),
        (),
        (operation,),
        (),
        (),
        (KEY,),
        development_study=root,
    )
    work = create_local_workspace(
        Path(workspace), project_root=Path(project), maximum_parallel_tasks=1
    )
    service = create_investigation_service(
        project_root=Path(project), operator_profile=work.profile_path
    )
    directory = work.artifact_root / "paired-forecast"
    author_recursive_wave(
        draft=draft,
        project_root=project,
        artifact_writer=service.artifact_writer,
        output_dir=directory,
    )
    run_recursive_wave(
        directory=directory,
        project_root=project,
        artifact_writer=service.artifact_writer,
        maximum_parallel_tasks=1,
    )
    report, products, _, _ = read_recursive_wave(
        directory=directory,
        artifact_writer=service.artifact_writer,
        include_products=True,
    )
    (result,) = products["records"][KEY].values()
    expected = {
        (k, m): v
        for k, row in source["predictions"].items()
        for m, v in row.items()
        if m != "donor"
    }
    if len(result.rows) != len(expected) or any(
        [float(a), float(b)] != expected[k, m] for k, m, a, b in result.rows
    ):
        raise ValueError("Recursive worker differs from the pre-assessment forecast")
    return {
        "read": report,
        "workspace": str(workspace),
        "authoring_directory": str(directory),
        "source_prediction_sha256": pin["forecast.json"],
        "input_sha256": config.fingerprint(),
        "output_sha256": result.fingerprint(),
        "paired_results": len(result.rows),
        "affinity": sorted(os.sched_getaffinity(0)),
        "maximum_parallel_tasks": 1,
    }


def measure_interface_transfer(operation: str, *, evidence: Path, archive: Path | None = None,
                               reference: Path | None = None, project_root: Path | None = None, workspace: Path | None = None):
    """Read the selected geometry, fit, blind score or recursive reconstruction using its owning provider."""
    if operation in ("predict", "score") and archive is None:
        raise ValueError("Predict and score require the native source archive")
    if operation == "geometry" and reference is None:
        raise ValueError("Geometry requires the dry structural reference")
    if operation == "geometry":
        from empirical_lawhood.adapters.physical.rubisco_kinetics.interface_geometry import (
            all_profiles,
        )

        return all_profiles(evidence / "sources", reference)
    elif operation == "predict":
        from empirical_lawhood.adapters.physical.rubisco_kinetics.transfer_sources import (
            predict,
        )

        return predict(evidence, archive)
    elif operation == "recursive":
        if project_root is None or workspace is None:
            raise ValueError("recursive requires project_root and workspace")
        return reconstruct(evidence, project_root, workspace)
    if operation == "score":
        from empirical_lawhood.adapters.physical.rubisco_kinetics.transfer_assessment import (
            assess,
        )

        return assess(evidence, archive)
    raise ValueError("Unknown Rubisco transfer operation")
