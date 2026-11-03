# SPDX-License-Identifier: MPL-2.0
"""Pure preparation of parameterized Matrix response-error selections.

The supplying API authenticates original source custody before passing resolved
allocations. Checks here establish design consistency, not the truth of source
qualification or an exposure audit. Preparation never loads training arrays.
"""

from collections.abc import Mapping
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json

from empirical_lawhood.kernel.experimental_design import UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
)

from .experiment_specification import MatrixResponseErrorSpecification


def _unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("selected prediction protocol contains a duplicate key")
        result[name] = value
    return result


def _protocol_errors(specification, raw):
    """Bind the reviewable candidate's exact bytes and its selected mathematics."""
    if type(raw) is not bytes:
        return ("prediction protocol bytes were not supplied",)
    if sha256(raw).hexdigest() != specification.protocol_sha256:
        return ("prediction protocol bytes differ from their selected SHA256",)
    try:
        document = json.loads(raw, object_pairs_hook=_unique_object,
            parse_float=lambda _: (_ for _ in ()).throw(ValueError("binary fractional protocol number")),
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite protocol number")))
        target = document["target"]
        protocol = target["original_mathematical_protocol"]["value"]
        prediction = document["prediction"]
        criterion = document["primary_criterion"]
        numerical = document["numerical"]
        calibration = document["calibration"]
        m, a = specification.measurement, specification.assessment
        fixed_prediction = {
            "candidate_features": "CONTEXT10 + SPECTRAL3 installed fixed feature mask",
            "strong_conventional_baseline": "ALL_ORIGIN21 fixed ridge, with the same available pre-cutoff observation channels.",
            "opportunity_baseline": "TRAIN-only per-endpoint median of raw normalized error (even-n median arithmetic midpoint), fit after genuine reservation; transform with log1p only for uniform forecast representation.",
            "label_transform": "log1p(E), all15 outputs",
            "algorithm": "TRAIN-only means/scales; constant columns scale1/mask; intercept unpenalized; ridge lambda1 fixed; no hyperparameter/model search. Clip log predictions at0 then per-description cumulative max on the unchanged horizon lattice; compare expm1 predictions in original normalized units.",
            "causal_delivery": "Feature/model/calibration only to forecaster; future raw arrays and labels only to evaluator; exact source, frame, clock and cutoff joins; forecast seal before continuation.",
            "paired_view_forecast": "ONE immutable forecast from the original PRIMARY causal frame, compared with BOTH view labels; no view-specific refit or future-feature access.",
        }
        fixed_criterion = {
            "root_loss": "Absolute FACTOR E128 forecast error in original actuator-normalized units.",
            "success": "One whole assigned CONF root succeeds only if usable/qualified, and its candidate absolute forecast loss improves by STRICTLY MORE than0.0002 versus EACH fixed baseline at BOTH PRIMARY and FINE views. Ties, refusal, no-origin, missing, numerical failure and UNKNOWN count as nonsuccess, with original labels preserved.",
            "null": "Probability of this whole-root success is at most1/2 under the genuinely assessed fixed-map IID sampling contract.",
            "formal_family": "Preserve12 planned programme comparison slots; this one E3 claim uses conservative0.05/12. No redistribution of unused slots.",
        }
        checks = (
            (target["primary"] == [m.primary_description, m.primary_horizon], "primary target"),
            (target["secondary_factor_horizons"] == list(m.horizons[:-1]), "secondary horizons"),
            (protocol["horizon_steps"] == list(m.horizons), "complete horizon scope"),
            (protocol["primary_timestep"] == {"decimal": str(m.primary_timestep)}, "primary clock"),
            (protocol["panel_roles"] == list(m.panel_roles), "future panels"),
            (protocol["estimand"] == m.estimand and protocol["metric"] == m.metric
                and protocol["aggregation"] == m.aggregation, "response quantity"),
            (tuple(row["value"]["role"] for row in protocol["action_scales"]) == m.actions
                and all(row["value"]["amplitude"] == {"decimal": str(m.action_amplitude)}
                    and row["value"]["force_norm"] == {"decimal": "1"}
                    and row["value"]["pulse_steps"] == m.pulse_ticks for row in protocol["action_scales"]), "action menu"),
            (prediction["candidate_method"] == "SPECTRAL"
                and prediction["feature_window_ticks"] == m.feature_window_ticks
                and prediction["feature_cadence_ticks"] == m.feature_cadence_ticks, "causal predictor"),
            (criterion["meaningful_paired_improvement"] == str(a.improvement_margin)
                and criterion["alpha_rational"] == str(a.alpha), "exact primary criterion"),
            (numerical["primary_dt"] == str(m.primary_timestep)
                and numerical["fine_dt"] == str(m.fine_timestep)
                and numerical["observed_target_primary_fine_difference_gate"] == str(m.target_discrepancy_tolerance), "paired numerical screen"),
            (calibration["alpha"] == str(specification.calibration_alpha), "calibration confidence"),
        )
        return (tuple("prediction protocol changes " + name for passed, name in checks if not passed)
            + tuple("prediction protocol changes prediction." + name for name, value in fixed_prediction.items()
                if prediction[name] != value)
            + tuple("prediction protocol changes primary_criterion." + name for name, value in fixed_criterion.items()
                if criterion[name] != value))
    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
        return ("prediction protocol is malformed or lacks the complete selected scientific operands",)


def validate_matrix_response_instance(*, specification, allocation, draft, source_records) -> None:
    """Join an exposed sidecar to its exact selected scientific operation graph.

    Matrix operands are declared external inputs, so no sidecar-only source
    record supplies scientific eligibility or authority. The existing pure
    compiler configuration/root checks retain their owning phase validators.
    """
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec, RecursiveStudyDraft
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, validate_recursive_scientific_roots
    from .experiment_bindings import BUDGET, PHASES, node_id, operation_declarations
    from .experiment_lowering import development_root, expected_connections, external_id

    if (type(specification) is not MatrixResponseErrorSpecification or type(allocation) is not UnitAllocation
            or type(draft) is not RecursiveStudyDraft):
        raise TypeError("Matrix instance requires its exact specification, allocation and derived draft types")
    specification.__post_init__()
    allocation.__post_init__()
    draft.__post_init__()
    if specification.evidence_scope == "PROSPECTIVE_REQUIRED":
        from .protected_preparation import validate_protected_e3_experiment_instance

        return validate_protected_e3_experiment_instance(specification=specification, allocation=allocation,
            draft=draft, source_records=source_records)
    expected_roles = tuple(sorted((selection.role.lower(), selection.expected_units) for selection in specification.populations))
    if (specification.evidence_scope != "EXPOSED_CONFORMANCE" or specification.calibration_target_view is None
            or allocation.role_counts != expected_roles
            or any(not unit.exposed or not {"fine", "primary"}.issubset(unit.numerical_view_ids) for unit in allocation.units)):
        raise ValueError("Matrix instance changes selected population counts, nested views or exposed lifecycle")
    for selection in specification.populations:
        selected_ids = allocation.unit_ids(selection.role.lower())
        if (selection.unit_ids is not None and selected_ids != selection.unit_ids
                or selection.family_id is not None and any(allocation.unit(unit_id).family_id != selection.family_id for unit_id in selected_ids)):
            raise ValueError("Matrix instance changes its selected original units or preparation family")
    queries = {role: allocation.unit_ids(role) for role in ("calibration", "evaluation")}
    units = tuple(sorted(unit for selected in queries.values() for unit in selected))
    root = development_root(specification.identity, allocation.identity, units,
        study_id="study.matrix-e3.exposed." + specification.fingerprint())
    if (draft.draft_id != "draft.matrix-e3.exposed." + specification.fingerprint()
            or draft.development_study != root or draft.question != root.question
            or draft.prospective_draft is not None or draft.requirements or draft.connections or draft.suppliers
            or draft.unresolved_decisions or draft.contribution_parents
            or draft.campaign.objective != root.question or draft.campaign.system_ids != (root.system.object_id,)
            or draft.campaign.world_ids != (root.world_id,)
            or draft.campaign.target_claim_ids != tuple(claim.claim_id for claim in root.claims)):
        raise ValueError("Matrix sidecar differs from its selected source-bound scientific root or claims")
    expected_nodes = {node_id(specification.identity, operation, mode=mode)
        for operation, mode in (("fit", ""), ("freeze", "model"), ("calibrate", ""), ("freeze", "calibration"), ("evaluate", ""))}
    expected_nodes.update(node_id(specification.identity, operation, mode=role, unit_id=unit_id)
        for role, selected in queries.items() for unit_id in selected for operation in ("forecast", "observe"))
    if (set(operation.node_id for operation in draft.operations) != expected_nodes
            or draft.selected_operation_ids != tuple(sorted(expected_nodes))):
        raise ValueError("Matrix instance drops, adds or substitutes its complete derived operation census")
    declarations = {declaration.registration().selection.selection_id: declaration.registration()
        for declaration in operation_declarations()}
    registrations, configs, externals = {}, [], {}
    query_census = tuple((role, len(selected)) for role, selected in queries.items())
    for operation in draft.operations:
        registration = declarations.get(operation.selection.selection_id)
        if registration is None or operation.selection != registration.selection:
            raise ValueError("Matrix instance substitutes an operation's selected method implementation")
        row = decode_recursive_config_input(operation, registration)
        config = row.record
        if (config.specification != specification.identity or config.allocation != allocation.identity
                or config.query_census != query_census):
            raise ValueError("Matrix sidecar and operation configuration name different scientific operands")
        expected_operation = RecursiveOperationSpec.from_config(node_id=operation.node_id, selection=registration.selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + operation.node_id + ".complete-selected-scope",),
            resource_budget=BUDGET)
        if operation != expected_operation:
            raise ValueError("Matrix instance changes its derived operation obligations or execution contract")
        registrations[operation.node_id] = registration
        configs.append(row)
        phase = next(phase for phase in PHASES if phase[0] == config.operation)
        schemas = {name: kind.SCHEMA for name, kind in phase[1]}
        for name, (_, _, external, role) in expected_connections(config, queries).items():
            if external is not None:
                value = (schemas[name.split(".", 1)[0]], role)
                if externals.setdefault(external, value) != value:
                    raise ValueError("Matrix instance changes one external operand's scientific role")
    if {value.input_id for value in draft.external_inputs} != set(externals):
        raise ValueError("Matrix instance omits or adds declared scientific external inputs")
    exact_records = {external_id(specification.identity, "specification"): specification,
        external_id(specification.identity, "allocation"): allocation}
    for value in draft.external_inputs:
        schema, role = externals[value.input_id]
        if (value.payload_schema != schema or value.scientific_role != role or value.media_type != "application/json"
                or value.logical_artifact_id != "input." + value.input_id or value.parent_substitution
                or value.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or value.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or type(value.maximum_size_bytes) is not int or value.maximum_size_bytes < 1):
            raise ValueError("Matrix instance changes its exact external operand schema, access or binding")
        exact = exact_records.get(value.input_id)
        if exact is not None and (value.expected_content_sha256 != exact.fingerprint()
                or value.maximum_size_bytes != len(exact.canonical_bytes())):
            raise ValueError("Matrix instance substitutes its declared exact specification or allocation bytes")
    if any(link.edge_id != "edge." + link.consumer_node_id + "." + link.consumer_input_id for link in draft.links):
        raise ValueError("Matrix instance substitutes its code-derived scientific binding identities")
    validate_recursive_scientific_roots(root=root, config_inputs=tuple(configs), registrations_for_node=registrations,
        requirements=draft.requirements, connections=draft.connections, links=draft.links,
        qualifications=(), known_design_inputs=(), external_inputs=draft.external_inputs)


def prepare_matrix_response_error(
    specification: MatrixResponseErrorSpecification,
    *,
    scientific_inputs: Mapping[str, UnitAllocation],
    execution: ExecutionSelection,
    protocol_bytes: bytes | None = None,
    method_inputs=None,
) -> ExperimentPreparation:
    """Resolve whole units, report all known dependencies, and freeze allocation.

    ``scientific_inputs`` must come from the API's authenticated source boundary.
    Constructor validity and a matching hash supply no source eligibility. This
    source-bank method route is exposed conformance, not fresh acquisition or
    protected scientific execution. No training or numerical science runs here.
    """
    if type(specification) is not MatrixResponseErrorSpecification:
        raise TypeError("Matrix preparation needs its typed experiment specification")
    if not isinstance(scientific_inputs, Mapping) or type(execution) is not ExecutionSelection:
        raise TypeError("Matrix preparation separates resolved scientific inputs from execution selection")
    specification.__post_init__()
    execution.__post_init__()
    if specification.evidence_scope == "PROSPECTIVE_REQUIRED":
        from .protected_preparation import prepare_protected_e3

        return prepare_protected_e3(specification, execution=execution, protocol_bytes=protocol_bytes,
            method_inputs=method_inputs, scientific_inputs=scientific_inputs)
    dependencies = []

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency(code, kind, detail, source_key))

    for index, reason in enumerate(_protocol_errors(specification, protocol_bytes)):
        dependency("matrix.e3.protocol." + str(index), DependencyKind.EXTERNAL_INPUT, reason, "prediction-protocol")
    if specification.calibration_target_view is None:
        dependency("matrix.e3.calibration-target-view", DependencyKind.SCIENTIFIC_EVIDENCE,
            "Select PRIMARY-only or MAX_PAIRED_VIEWS calibration targets explicitly before calibration outcomes; the candidate does not select this scientific quantity.")
    if execution.environment_id is None:
        dependency("matrix.e3.environment", DependencyKind.ENVIRONMENT, "Select the existing route environment; preparation does not synchronize it.")
    if execution.source_snapshot is None:
        dependency("matrix.e3.source-snapshot", DependencyKind.ENVIRONMENT, "Select the producing implementation snapshot before execution.")
    if execution.output_root is None:
        dependency("matrix.e3.output-root", DependencyKind.STORAGE, "Select an explicit custody/output destination before execution.")

    selected_units, selected_roles, source_references, input_identities = [], [], {}, []
    resolved_counts = []
    allocation_errors = False
    seen_units = {}
    for selection in specification.populations:
        role = selection.role.lower()
        supplied = scientific_inputs.get(selection.source_key)
        if supplied is None:
            dependency(selection.selection_id + ".missing", DependencyKind.EXTERNAL_INPUT,
                "Supply the actual authenticated " + role + " source allocation; a requested count assigns no units.", selection.source_key)
            resolved_counts.append((role, 0))
            allocation_errors = True
            continue
        if type(supplied) is not UnitAllocation:
            dependency(selection.selection_id + ".invalid", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The selected input is not a typed immutable unit allocation.", selection.source_key)
            resolved_counts.append((role, 0))
            allocation_errors = True
            continue
        try:
            supplied.__post_init__()
        except (ValueError, TypeError, AttributeError) as error:
            dependency(selection.selection_id + ".invalid", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The supplied complete allocation is invalid: " + str(error), selection.source_key)
            resolved_counts.append((role, 0))
            allocation_errors = True
            continue
        units = tuple(unit for unit in supplied.units if selection.family_id is None or unit.family_id == selection.family_id)
        if selection.unit_ids is not None:
            requested_ids = set(selection.unit_ids)
            available = {unit.unit_id for unit in units}
            missing_ids = requested_ids - available
            if missing_ids:
                dependency(selection.selection_id + ".unit-selection", DependencyKind.SCIENTIFIC_EVIDENCE,
                    "Explicit original unit IDs lack membership in the selected source/family: " + ", ".join(sorted(missing_ids)), selection.source_key)
                allocation_errors = True
            units = tuple(unit for unit in units if unit.unit_id in requested_ids)
        resolved_counts.append((role, len(units)))
        if len(units) != selection.expected_units:
            dependency(selection.selection_id + ".census", DependencyKind.SCIENTIFIC_EVIDENCE,
                f"Selected {len(units)} actual whole units; the specification declares {selection.expected_units}. No units are dropped or invented.", selection.source_key)
            allocation_errors = True
        original_roles = {row.unit_id: row.role for row in supplied.roles}
        invalid_roles = tuple(unit.unit_id for unit in units if original_roles[unit.unit_id] != role
            and not (unit.exposed and (role == "train" or specification.evidence_scope == "EXPOSED_CONFORMANCE")
                and original_roles[unit.unit_id] == "development"))
        if invalid_roles:
            dependency(selection.selection_id + ".roles", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Selected units have incompatible original roles: " + ", ".join(invalid_roles), selection.source_key)
            allocation_errors = True
        invalid_exposure = tuple(unit.unit_id for unit in units if
            (specification.evidence_scope == "EXPOSED_CONFORMANCE" and not unit.exposed)
            or (specification.evidence_scope == "PROSPECTIVE_REQUIRED" and role != "train" and unit.exposed))
        if invalid_exposure:
            dependency(selection.selection_id + ".exposure", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The selected evidence scope cannot consume these exposed/unverified units: " + ", ".join(invalid_exposure), selection.source_key)
            allocation_errors = True
        missing_views = tuple(unit.unit_id for unit in units if not {"primary", "fine"}.issubset(unit.numerical_view_ids))
        if missing_views:
            dependency(selection.selection_id + ".numerical-views", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Both selected numerical views are required; missing support for: " + ", ".join(missing_views), selection.source_key)
            allocation_errors = True
        for unit in units:
            if unit.unit_id in seen_units:
                dependency(selection.selection_id + ".overlap." + unit.unit_id, DependencyKind.SCIENTIFIC_EVIDENCE,
                    "Whole unit is also selected for " + seen_units[unit.unit_id] + "; another role or label creates no independence.", selection.source_key)
                allocation_errors = True
            seen_units[unit.unit_id] = role
            selected_units.append(unit)
            selected_roles.append(UnitRoleAssignment(unit.unit_id, role))
        for reference in supplied.sources:
            if reference.object_id in source_references and source_references[reference.object_id] != reference:
                dependency(selection.selection_id + ".source-alias", DependencyKind.SCIENTIFIC_EVIDENCE,
                    "One source ID refers to differing immutable source bytes.", selection.source_key)
                allocation_errors = True
            source_references[reference.object_id] = reference
        input_identities.append(supplied.identity)

    evaluation_count = specification.population("EVALUATION").expected_units
    if specification.minimum_successes > evaluation_count:
        dependency("matrix.e3.evaluation-resolution", DependencyKind.SCIENTIFIC_EVIDENCE,
            "The complete declared evaluation census cannot reach the selected exact alpha even if every root succeeds; revise the design before outcomes.")

    allocation = None
    if not allocation_errors:
        input_digest = sha256(canonical_json_bytes((specification.identity, tuple(input_identities)))).hexdigest()
        allocation = UnitAllocation("allocation.matrix.e3." + input_digest,
            tuple(sorted(source_references.values(), key=lambda reference: reference.object_id)),
            tuple(sorted(selected_units, key=lambda unit: unit.unit_id)),
            tuple(sorted(selected_roles, key=lambda row: row.unit_id)))

    draft, input_records = None, ()
    if method_inputs is None:
        dependency("matrix.e3.campaign", DependencyKind.EXTERNAL_INPUT,
            "Supply the actual selected campaign; complete banks alone select no execution campaign.", "campaign")
        for role in ("train", "calibration", "evaluation"):
            for kind in ("features", "outcomes"):
                dependency("matrix.e3." + role + "-" + kind, DependencyKind.EXTERNAL_INPUT,
                    "Supply the complete authenticated exposed " + role + " " + kind + " bank, preserving original causal and paired numerical records.", role + "-" + kind)
    else:
        from .experiment_methods import MatrixE3MethodInputs, project_source_bank, validate_bank, validate_pair
        if type(method_inputs) is not MatrixE3MethodInputs:
            dependency("matrix.e3.method-inputs", DependencyKind.EXTERNAL_INPUT,
                "Method inputs must be the typed source-bank handle with its selected campaign.")
        else:
            if method_inputs.campaign is None:
                dependency("matrix.e3.campaign", DependencyKind.EXTERNAL_INPUT,
                    "Supply the actual selected campaign; retained banks and their complete census remain available for preflight.", "campaign")
        if type(method_inputs) is MatrixE3MethodInputs and allocation is not None:
            for role in ("train", "calibration", "evaluation"):
                original_features = next((bank for bank in method_inputs.features if bank.role == role), None)
                original_outcomes = next((bank for bank in method_inputs.outcomes if bank.role == role), None)
                if original_features is not None and original_outcomes is not None:
                    for index, (feature, outcome) in enumerate(zip(original_features.rows, original_outcomes.rows)):
                        try:
                            validate_pair(feature, outcome)
                        except ValueError as error:
                            dependency("matrix.e3." + role + ".original-pair." + str(index), DependencyKind.SCIENTIFIC_EVIDENCE, str(error), role)
            projected = {"features": [], "outcomes": []}
            for kind, banks in (("features", method_inputs.features), ("outcomes", method_inputs.outcomes)):
                by_role = {bank.role: bank for bank in banks}
                for role in ("train", "calibration", "evaluation"):
                    if role not in by_role:
                        dependency("matrix.e3." + role + "-" + kind, DependencyKind.EXTERNAL_INPUT,
                            "Supply the actual complete " + role + " " + kind + " bank.", role + "-" + kind)
                    else:
                        try:
                            source_key = specification.population(role.upper()).source_key
                            bank = project_source_bank(specification, allocation, scientific_inputs[source_key], by_role[role])
                            validate_bank(specification, allocation, bank)
                            projected[kind].append(bank)
                        except (ValueError, TypeError) as error:
                            dependency("matrix.e3." + role + "-" + kind + ".invalid", DependencyKind.SCIENTIFIC_EVIDENCE,
                                "Invalid complete source bank: " + str(error), role + "-" + kind)
            method_inputs = replace(method_inputs, features=tuple(projected["features"]), outcomes=tuple(projected["outcomes"]))
            features_by_role = {bank.role: bank for bank in method_inputs.features}
            outcomes_by_role = {bank.role: bank for bank in method_inputs.outcomes}
            for role in sorted(set(features_by_role) & set(outcomes_by_role)):
                for index, (feature, outcome) in enumerate(zip(features_by_role[role].rows, outcomes_by_role[role].rows)):
                    try:
                        validate_pair(feature, outcome)
                    except ValueError as error:
                        dependency("matrix.e3." + role + ".pair." + str(index), DependencyKind.SCIENTIFIC_EVIDENCE, str(error), role)
            if not dependencies:
                from .experiment_lowering import lower_exposed_matrix_response_error
                lowered = lower_exposed_matrix_response_error(specification, allocation, method_inputs)
                draft, input_records = lowered.draft, lowered.input_records
    counts = {selection.role.lower(): selection.expected_units for selection in specification.populations}
    query_count = counts["calibration"] + counts["evaluation"]
    operation_counts = (("calibrate", 1), ("evaluate", 1), ("fit", len(specification.methods)), ("forecast-seal", query_count))
    if specification.evidence_scope == "EXPOSED_CONFORMANCE":
        operation_counts = (("calibrate", 1), ("evaluate", 1), ("fit", 1), ("forecast", query_count),
            ("freeze", 2), ("observe", query_count))
    if draft is not None:
        operation_counts = tuple(sorted(Counter(operation.selection.capability_key.rsplit(".", 1)[-1]
            for operation in draft.operations).items()))
    census = ExperimentCensus(tuple(sorted(counts.items())), tuple(sorted(resolved_counts)), operation_counts,
        tuple(sorted((
            ("all-origin-features", next(method.feature_count for method in specification.methods if method.method_key == "ALL_ORIGIN_RIDGE")),
            ("calibration-rank", specification.calibration_rank), ("calibration-unit-scores", counts["calibration"]),
            ("evaluation-unit-decisions", counts["evaluation"]), ("fitted-models", len(specification.methods)),
            ("minimum-primary-successes", specification.minimum_successes),
            ("point-forecast-endpoints", query_count * specification.measurement.endpoint_count * len(specification.methods)),
            ("response-view-endpoints", (counts["train"] + query_count) * specification.measurement.endpoint_count * len(specification.measurement.numerical_views)),
            ("spectral-features", next(method.feature_count for method in specification.methods if method.method_key == "SPECTRAL_RIDGE")),
        ))), 0)
    return ExperimentPreparation(specification.identity, census,
        tuple(sorted(dependencies, key=lambda row: row.code)), allocation=allocation, draft=draft,
        input_records=input_records)
