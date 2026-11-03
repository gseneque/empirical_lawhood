# SPDX-License-Identifier: MPL-2.0
"""Derive a complete exposed E3 wave and its exact external bindings."""

from dataclasses import dataclass, replace

from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
)

from .configured_bindings import ConfiguredMatrixE3OperationConfig, node_id, operation_declarations
from .experiment_methods import MatrixE3MethodInputs, validate_bank, validate_pair


QUESTION = "Do the complete exposed origin-only response-error fit, calibration, freeze and paired evaluation methods preserve their declared whole-root contracts?"
WORLD = "world.matrix-response-experiment.exposed"


def external_id(specification, name, unit_id=None):
    return "external." + specification.object_fingerprint + "." + name + ("." + unit_id if unit_id else "")


def development_root(specification, allocation, unit_ids, *, study_id):
    views = ("fine", "primary")
    claim = ClaimSpec("claim." + study_id, WORLD, specification.object_id, QUESTION,
        "Complete all15 paired finite-dt targets, selected predictor/baselines and full assigned evaluation denominator; source-bound exposed software only.",
        "unit.matrix-response.whole-root", None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Retained/exposed source-bank methods create no fresh units, source eligibility, scientific issue, exchangeability or continuum warrant.",
        ("assumption.matrix-e3.exposed-source-bank",), numerical_view_ids=views)
    return DevelopmentStudySpec(study_id, QUESTION, specification, WORLD, WorldKind.NUMERICAL_SIMULATOR,
        unit_ids, views, (claim,), tuple(sorted((specification, allocation), key=lambda row: row.object_id)))


def expected_connections(config, queries):
    """The declaration validator and lowerer share exact code-owned graph joins."""
    specification = config.specification
    connections = {
        name: (None, None, external_id(specification, name), "SOURCE")
        for name in ("allocation", "specification", "coordinate-census")
    }

    def producer(name, operation, mode="", unit_id=None, role="MODEL"):
        connections[name] = (node_id(specification, operation, mode=mode, unit_id=unit_id), "product", None, role)

    if config.operation == "fit":
        for name in ("features", "outcomes"):
            connections[name] = (None, None, external_id(specification, "train-" + name), "HISTORY")
    elif config.operation == "freeze":
        producer("models", "fit")
        if config.mode == "calibration":
            producer("prior-freeze", "freeze", "model")
            producer("calibration", "calibrate")
    elif config.operation == "forecast":
        producer("models", "fit")
        producer("frozen", "freeze", "model" if config.mode == "calibration" else "calibration")
        if config.mode == "evaluation":
            producer("calibration", "calibrate")
        connections["feature"] = (None, None, external_id(specification, "feature", config.unit_id), "HISTORY")
    elif config.operation == "observe":
        producer("forecast", "forecast", config.mode, config.unit_id)
        connections["outcome"] = (None, None, external_id(specification, "outcome", config.unit_id), "OUTCOME")
    else:
        role = "calibration" if config.operation == "calibrate" else "evaluation"
        if config.operation == "calibrate":
            producer("models", "fit")
        producer("frozen", "freeze", "model" if role == "calibration" else "calibration")
        for unit_id in queries[role]:
            producer("forecasts." + unit_id, "forecast", role, unit_id)
            producer("outcomes." + unit_id, "observe", role, unit_id, role="OUTCOME")
    return connections


@dataclass(frozen=True, slots=True)
class MatrixE3LoweredExperiment:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]


def lower_exposed_matrix_response_error(specification, allocation, method_inputs, *, resources, coordinates):
    """Lower selected immutable banks without fitting, acquisition or custody I/O."""
    if type(allocation) is not UnitAllocation or type(method_inputs) is not MatrixE3MethodInputs:
        raise TypeError("E3 lowering requires the compiled allocation and typed scientific bank handle")
    if method_inputs.campaign is None:
        raise ValueError("E3 lowering requires the actual selected campaign before compiling its draft")
    if specification.evidence_scope != "EXPOSED_CONFORMANCE" or specification.calibration_target_view is None:
        raise ValueError("exposed lowering cannot supply prospective prerequisites or an unselected calibration target")
    feature_banks = {bank.role: bank for bank in method_inputs.features}
    outcome_banks = {bank.role: bank for bank in method_inputs.outcomes}
    if set(feature_banks) != {"train", "calibration", "evaluation"} or set(outcome_banks) != set(feature_banks):
        raise ValueError("E3 lowering requires complete TRAIN, CAL and EVAL feature and paired-outcome banks")
    for role in feature_banks:
        validate_bank(specification, allocation, feature_banks[role])
        validate_bank(specification, allocation, outcome_banks[role])
        for feature, outcome in zip(feature_banks[role].rows, outcome_banks[role].rows, strict=True):
            validate_pair(feature, outcome)
    queries = {role: allocation.unit_ids(role) for role in ("calibration", "evaluation")}
    query_census = tuple((role, len(queries[role])) for role in ("calibration", "evaluation"))
    configs = [ConfiguredMatrixE3OperationConfig("config." + node_id(specification.identity, operation, mode=mode), operation,
        specification.identity, allocation.identity, query_census, resources.budget(operation),
        ObjectIdentity.from_record(coordinates.record_id, coordinates), mode=mode)
        for operation, mode in (("fit", ""), ("freeze", "model"), ("calibrate", ""), ("freeze", "calibration"), ("evaluate", ""))]
    for role, units in queries.items():
        for unit_id in units:
            configs.extend(ConfiguredMatrixE3OperationConfig("config." + node_id(specification.identity, operation, mode=role, unit_id=unit_id),
                operation, specification.identity, allocation.identity, query_census, resources.budget(operation),
        ObjectIdentity.from_record(coordinates.record_id, coordinates), mode=role, unit_id=unit_id)
                for operation in ("forecast", "observe"))
    records = {
        external_id(specification.identity, "specification"): specification,
        external_id(specification.identity, "allocation"): allocation,
        external_id(specification.identity, "coordinate-census"): coordinates,
        external_id(specification.identity, "train-features"): feature_banks["train"],
        external_id(specification.identity, "train-outcomes"): outcome_banks["train"],
    }
    for role in queries:
        records.update({external_id(specification.identity, "feature", feature.unit_id): feature for feature in feature_banks[role].rows})
        records.update({external_id(specification.identity, "outcome", outcome.unit_id): outcome for outcome in outcome_banks[role].rows})
    declarations = {row.capability_key.rsplit(".", 1)[-1]: row for row in operation_declarations()}
    operations, links, roles_by_external = [], [], {}
    for config in configs:
        node = node_id(config.specification, config.operation, mode=config.mode, unit_id=config.unit_id)
        registration = declarations[config.operation].registration()
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=registration.selection,
            config_id=config.config_id, config=config, obligation_ids=("obligation." + node + ".complete-selected-scope",), resource_budget=config.resource_budget))
        for name, (producer, output, external, role) in expected_connections(config, queries).items():
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name,
                producer_node_id=producer, producer_output_id=output, external_input_id=external, scientific_role=role))
            if external is not None and roles_by_external.setdefault(external, role) != role:
                raise ValueError("E3 lowering changes a shared scientific input's role")
    unit_ids = tuple(sorted(unit for units in queries.values() for unit in units))
    study_id = "study.matrix-e3.exposed." + specification.fingerprint()
    root = development_root(specification.identity, allocation.identity, unit_ids, study_id=study_id)
    campaign = replace(method_inputs.campaign, objective=root.question, system_ids=(root.system.object_id,), world_ids=(root.world_id,),
        target_claim_ids=tuple(claim.claim_id for claim in root.claims))
    external = tuple(RecursiveExternalInput(input_id, "input." + input_id, record.SCHEMA, "application/json",
        len(record.canonical_bytes()), OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        record.fingerprint(), roles_by_external[input_id]) for input_id, record in sorted(records.items()))
    draft = RecursiveStudyDraft("draft.matrix-e3.exposed." + specification.fingerprint(), root.question, campaign,
        (), (), (), tuple(sorted(operations, key=lambda row: row.node_id)), external,
        tuple(sorted(links, key=lambda row: row.edge_id)), tuple(sorted(row.node_id for row in operations)), development_study=root)
    return MatrixE3LoweredExperiment(draft, tuple(sorted(records.items())))
