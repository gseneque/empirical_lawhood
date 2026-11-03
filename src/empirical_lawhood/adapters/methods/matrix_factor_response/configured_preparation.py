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

from empirical_lawhood.kernel.experimental_design import UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
)

from .configured_specification import ConfiguredMatrixResponseErrorSpecification as MatrixResponseErrorSpecification, ConfiguredE3Protocol, ConfiguredE3Resources, ConfiguredE3CoordinateCensus
from .configured_inputs import ConfiguredE3MethodInputs
from .configured_census import feature_counts


def _protocol_errors(specification, raw):
    """Scientific operands occur once in typed V2 records, never in prose."""
    if raw is None:
        return ()
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    try:
        protocol = decode_canonical_bytes(raw, ConfiguredE3Protocol, maximum_bytes=len(raw))
        return () if protocol == specification.protocol else ("typed protocol differs from its scientific selection",)
    except (TypeError, ValueError):
        return ("typed protocol is malformed or outside the installed contract",)


def validate_matrix_response_instance(*, specification, allocation, draft, source_records) -> None:
    """Join an exposed sidecar to its exact selected scientific operation graph.

    Matrix operands are declared external inputs, so no sidecar-only source
    record supplies scientific eligibility or authority. The existing pure
    compiler configuration/root checks retain their owning phase validators.
    """
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec, RecursiveStudyDraft
    from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input, validate_recursive_scientific_roots
    from .configured_bindings import PHASES, node_id, operation_declarations
    from .configured_lowering import development_root, expected_connections, external_id

    if (type(specification) is not MatrixResponseErrorSpecification or type(allocation) is not UnitAllocation
            or type(draft) is not RecursiveStudyDraft):
        raise TypeError("Matrix instance requires its exact specification, allocation and derived draft types")
    specification.__post_init__()
    allocation.__post_init__()
    draft.__post_init__()
    records = dict(source_records)
    if (set(records) != {"coordinate-census", "resources"}
            or type(records["coordinate-census"]) is not ConfiguredE3CoordinateCensus
            or type(records["resources"]) is not ConfiguredE3Resources):
        raise ValueError("configured cold instance drops its declared coordinate/resource selections")
    records["coordinate-census"].validate(specification, allocation, ())
    resources = records["resources"]
    resources.__post_init__()
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
        if (config.resource_budget != resources.budget(config.operation)
                or config.coordinate_census != ObjectIdentity.from_record(records["coordinate-census"].record_id, records["coordinate-census"])):
            raise ValueError("configured cold instance changes selected operation budgets")
        if (config.specification != specification.identity or config.allocation != allocation.identity
                or config.query_census != query_census):
            raise ValueError("Matrix sidecar and operation configuration name different scientific operands")
        expected_operation = RecursiveOperationSpec.from_config(node_id=operation.node_id, selection=registration.selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + operation.node_id + ".complete-selected-scope",),
            resource_budget=config.resource_budget)
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
        external_id(specification.identity, "allocation"): allocation,
        external_id(specification.identity, "coordinate-census"): records["coordinate-census"]}
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
    selected = method_inputs if type(method_inputs) is ConfiguredE3MethodInputs else None
    resources = None if selected is None else selected.resources
    coordinates = None if selected is None else selected.coordinates
    method_inputs = None if selected is None else selected.banks
    dependencies = []

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency(code, kind, detail, source_key))

    if type(resources) is not ConfiguredE3Resources:
        dependency("matrix.e3.resources", DependencyKind.EXTERNAL_INPUT, "Supply explicit finite budgets for all six operations.", "resources")
    else:
        resources.__post_init__()
    if type(coordinates) is not ConfiguredE3CoordinateCensus:
        dependency("matrix.e3.coordinate-census", DependencyKind.EXTERNAL_INPUT, "Supply complete declared exposed unit/source/coordinate metadata.", "coordinate-census")
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
            if coordinates is not None:
                try:
                    coordinates.validate(specification, allocation, method_inputs.features)
                except (TypeError, ValueError) as error:
                    dependency("matrix.e3.coordinates.invalid", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "coordinate-census")
            if not dependencies:
                from .configured_lowering import lower_exposed_matrix_response_error
                lowered = lower_exposed_matrix_response_error(specification, allocation, method_inputs, resources=resources, coordinates=coordinates)
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
            *feature_counts(specification.methods),
            ("calibration-rank", specification.calibration_rank), ("calibration-unit-scores", counts["calibration"]),
            ("evaluation-unit-decisions", counts["evaluation"]), ("fitted-models", len(specification.methods)),
            ("minimum-primary-successes", specification.minimum_successes),
            ("point-forecast-endpoints", query_count * specification.measurement.point_endpoint_count * len(specification.methods)),
            ("response-view-endpoints", (counts["train"] + query_count) * specification.measurement.endpoint_count * len(specification.measurement.numerical_views)),
        ))), 0)
    return ExperimentPreparation(specification.identity, census,
        tuple(sorted(dependencies, key=lambda row: row.code)), allocation=allocation, draft=draft,
        input_records=input_records, design_records=tuple(sorted((name, value) for name, value in
            (("coordinate-census", coordinates), ("resources", resources)) if value is not None)))
