# SPDX-License-Identifier: MPL-2.0
"""Explicit historical fit/predict/global-commit/evaluate graph composition."""

from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import SOURCE_SHA256, decode_rr2018, role_slices
from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.status import LifecycleStatus
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
)

from .operation_bindings import BUDGET, MAX_BYTES, historical_development_root, operation_declarations
from .operation_contracts import (
    HistoricalCommitConfigV1, HistoricalEvaluateConfigV1, HistoricalFitConfigV1, HistoricalPredictConfigV1,
)
from .records import HistoricalScienceV1
from .source_binding import HistoricalSourceConfigV1, Rr2018ArticleInputV1

_ROLES = (("training", HistoricalTrainingSliceV1), ("features", HistoricalFeatureSliceV1),
          ("labels", HistoricalLabelSliceV1))


def historical_recursive_draft(science, slices, *, draft_id="draft.rubisco.historical-e1", article_input=None):
    """Freeze exact exposed role inputs; the engine owns execution and custody.

    Historical table exposure predates this software barrier. The barrier
    ensures all selected forecasts exist before evaluation reads its label
    ports; it creates no new biological independence or prospective evidence.
    """
    if not isinstance(science, HistoricalScienceV1) or not isinstance(slices, tuple):
        raise ValueError("historical composition requires immutable typed science and role slices")
    expected = {(role, fold.fold_id) for role, _ in _ROLES for fold in science.folds}
    by_role = {}
    for value in slices:
        role = next((role for role, record_type in _ROLES if type(value) is record_type), None)
        if role is None or value.source != science.source or (role, value.fold_id) not in expected:
            raise ValueError("historical composition substitutes a source or input information role")
        key = (role, value.fold_id)
        if key in by_role:
            raise ValueError("historical composition repeats an input role")
        by_role[key] = value
    if set(by_role) != expected or len({value.slice_id for value in slices}) != len(slices):
        raise ValueError("historical composition loses its complete unique role/fold census")
    for fold in science.folds:
        training = by_role[("training", fold.fold_id)]
        features = by_role[("features", fold.fold_id)]
        labels = by_role[("labels", fold.fold_id)]
        if (tuple(value.sample_id for value in training.features) != fold.training_sample_ids
            or tuple(value.sample_id for value in features.features) != fold.target_sample_ids
            or tuple(value.sample_id for value in labels.endpoints) != fold.target_sample_ids
            or training.features != tuple(s for s in science.substitutions if s.sample_id in fold.training_sample_ids)
            or features.features != tuple(s for s in science.substitutions if s.sample_id in fold.target_sample_ids)):
            raise ValueError("historical composition changes the frozen sample/feature assignment")
    study = historical_development_root(science, study_id=f"study.{draft_id}")
    if article_input is not None and not isinstance(article_input, Rr2018ArticleInputV1):
        raise ValueError("historical source graph needs its typed bounded raw article")
    task_count = 2 * len(science.folds) + 2 + int(article_input is not None)
    budget = ResourceBudget(1, BUDGET.memory_bytes, 0, BUDGET.wall_time_seconds * task_count,
                            BUDGET.source_scan_bytes * task_count, BUDGET.output_bytes * task_count)
    policy = AuthorityPolicy(f"policy.{draft_id}", "owner.local-researcher", "operator.local-development",
        (study.study_id,), frozenset((study.world_kind,)),
        frozenset((AuthorityAction.REPOSITORY_IMPLEMENTATION, AuthorityAction.SIMULATION_EXECUTION)),
        frozenset((SourceAccessClass.NONE,)), ("gate.local-nonactuating-development",), frozenset(),
        budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    root_id = f"design.{draft_id}"
    node = CampaignNode(root_id, CampaignNodeKind.EVIDENCE_SNAPSHOT, CampaignLane.EXPLORATORY,
        ObjectIdentity.from_record(study.study_id, study), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"campaign.{draft_id}", study.question, (study.system.object_id,), (study.world_id,),
        tuple(claim.claim_id for claim in study.claims), budget, ObjectIdentity.from_record(policy.policy_id, policy),
        (DecisionRight(f"decision-right.{draft_id}", AuthorityAction.SIMULATION_EXECUTION,
                       "owner.local-researcher", policy.policy_id, False),),
        (node,), (root_id,), (root_id,), (), LifecycleStatus.ACTIVE)
    registrations = {declaration.config_record_type: declaration.registration() for declaration in operation_declarations()}
    operations, links, externals = [], [], []
    commit_id, evaluate_id = "rubisco.historical.commit", "rubisco.historical.evaluate"
    source_id = "rubisco.historical.source"

    def operation(node_id, operand):
        operations.append(RecursiveOperationSpec.from_config(node_id=node_id,
            selection=registrations[type(operand)].selection, config_id=operand.config_id, config=operand,
            obligation_ids=(f"obligation.{node_id}.complete-roles",), resource_budget=BUDGET))

    if article_input is not None:
        operation(source_id, HistoricalSourceConfigV1(f"config.{source_id}", science))
        raw_id = f"external.{article_input.input_id}"
        if len(article_input.canonical_bytes()) > MAX_BYTES:
            raise ValueError("historical canonical article input exceeds the registered byte bound")
        externals.append(RecursiveExternalInput(raw_id, article_input.input_id, article_input.SCHEMA,
            "application/json", MAX_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
            article_input.fingerprint()))
        links.append(RecursiveInputLink(f"edge.{source_id}.article", source_id, "article",
                                        external_input_id=raw_id, scientific_role="SOURCE"))

    for fold in science.folds:
        fit_id, predict_id = f"rubisco.historical.{fold.fold_id}.fit", f"rubisco.historical.{fold.fold_id}.predict"
        operation(fit_id, HistoricalFitConfigV1(f"config.{fit_id}", science, fold.fold_id))
        operation(predict_id, HistoricalPredictConfigV1(f"config.{predict_id}", science, fold.fold_id))
        links.append(RecursiveInputLink(f"edge.{predict_id}.model", predict_id, "model", fit_id, "model",
                                        scientific_role="MODEL"))
        links.append(RecursiveInputLink(f"edge.{commit_id}.{fold.fold_id}", commit_id,
            f"forecasts.{fold.fold_id}", predict_id, "forecasts"))
        for role, _ in _ROLES:
            value = by_role[(role, fold.fold_id)]
            if len(value.canonical_bytes()) > MAX_BYTES:
                raise ValueError("historical role input exceeds the registered byte bound")
            input_id = f"external.{value.slice_id}"
            consumer = fit_id if role == "training" else predict_id if role == "features" else evaluate_id
            port_id = f"labels.{fold.fold_id}" if role == "labels" else role
            input_role = "OUTCOME" if role == "labels" else "SOURCE"
            if article_input is None:
                externals.append(RecursiveExternalInput(input_id, value.slice_id, value.SCHEMA, "application/json", MAX_BYTES,
                    OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY, value.fingerprint(), input_role))
                links.append(RecursiveInputLink(f"edge.{consumer}.{port_id}", consumer, port_id,
                    external_input_id=input_id, scientific_role=input_role))
            else:
                links.append(RecursiveInputLink(f"edge.{consumer}.{port_id}", consumer, port_id,
                    source_id, f"{role}.{fold.fold_id}", scientific_role=input_role))
    operation(commit_id, HistoricalCommitConfigV1(f"config.{commit_id}", science))
    operation(evaluate_id, HistoricalEvaluateConfigV1(f"config.{evaluate_id}", science))
    links.append(RecursiveInputLink(f"edge.{evaluate_id}.commitment", evaluate_id, "commitment", commit_id,
                                    "commitment", scientific_role="ACTION"))
    ordered = tuple(sorted(operations, key=lambda value: value.node_id))
    return RecursiveStudyDraft(draft_id, study.question, campaign, (), (), (), ordered,
        tuple(sorted(externals, key=lambda value: value.input_id)),
        tuple(sorted(links, key=lambda value: value.edge_id)), tuple(value.node_id for value in ordered),
        development_study=study)


def rr2018_recursive_draft(article_input, *, draft_id="draft.rubisco.historical-e1.source-bound"):
    """Prepare a design from authentic exposed bytes; execution decodes again.

    The design-time source read fixes the audit/feature identities. The source
    operation independently decodes its actual supplied port and must reproduce
    them before any fitted model or forecast can be scheduled.
    """
    from .analysis import rr2018_science

    if not isinstance(article_input, Rr2018ArticleInputV1) or article_input.source_sha256 != SOURCE_SHA256:
        raise ValueError("RR2018 graph requires its authentic bounded native source")
    audit = decode_rr2018(article_input.raw_xml_utf8.encode("utf-8"), expected_sha256=SOURCE_SHA256)
    return historical_recursive_draft(rr2018_science(audit), role_slices(audit), draft_id=draft_id,
                                      article_input=article_input)
