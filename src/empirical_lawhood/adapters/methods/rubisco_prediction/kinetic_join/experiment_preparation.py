# SPDX-License-Identifier: MPL-2.0
"""Prepare conditional W1 through existing declarations; execute no science."""

from collections.abc import Mapping
from dataclasses import replace

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
)

from .experiment_inputs import (
    INPUT_TYPES, KineticExperimentInputs, bind_kinetic_experiment_inputs, source_allocation,
)
from .experiment_specification import RubiscoKineticExperimentSpecification
from .operation_bindings import BUDGET, NAMESPACE
from .recursive_translation import kinetic_join_draft


def _scientific_selection(specification, scientific_inputs, method_inputs):
    """Resolve immutable scientific meaning without observing execution settings."""
    if type(specification) is not RubiscoKineticExperimentSpecification:
        raise TypeError("kinetic preparation requires its exact specification")
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("kinetic preparation requires its source allocation mapping")
    specification.__post_init__()
    dependencies = []

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency("rubisco.kinetic." + code, kind, detail, source_key))

    if set(scientific_inputs) - {"supply"}:
        dependency("unknown-allocation", DependencyKind.EXTERNAL_INPUT,
            "Only the source-bound analytical supply allocation is accepted.")
    if method_inputs is None:
        inputs = KineticExperimentInputs()
    elif type(method_inputs) is KineticExperimentInputs:
        inputs = method_inputs
        inputs.__post_init__()
    else:
        dependency("method-inputs", DependencyKind.EXTERNAL_INPUT,
            "Supply the typed closed campaign/material/supply/source-query/comparison handle.")
        inputs = KineticExperimentInputs()
    for key in INPUT_TYPES:
        record = getattr(inputs, key)
        if record is None:
            dependency(key + ".missing", DependencyKind.EXTERNAL_INPUT,
                "Supply the actual original " + key + " record; a selection supplies no source bytes.", key)
            continue
        identity = specification.source_query if key == "query" else getattr(specification, key)
        original_id = (identity.object_id if key == "query" else getattr(record,
            {"campaign": "campaign_id", "material": "assumption_id", "supply": "supply_id",
             "comparison": "comparison_id"}[key]))
        if ObjectIdentity.from_record(original_id, record) != identity:
            dependency(key + ".identity", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The original " + key + " differs from its exact selected source identity.", key)
    supply = inputs.supply
    allocation = None
    if supply is not None:
        actual_allocation = source_allocation(supply)
        supplied_allocation = scientific_inputs.get("supply")
        if supplied_allocation != actual_allocation:
            dependency("supply.allocation", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The analytical allocation differs from the complete actual supply; no member is an independent biological unit.", "supply")
        if (supply.context != specification.context or supply.expected_member_ids != specification.expected_member_ids
                or supply.evidence_role != "DISCLOSED_SYNTHETIC" or supply.independent_biological_units != 0):
            dependency("supply.compatibility", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Retain the exact disclosed context, complete supplied/partial/adverse member roster and zero biological units.", "supply")
        if inputs.material is not None:
            original_material = ObjectIdentity.from_record(inputs.material.assumption_id, inputs.material)
            if (supply.context.material != original_material or supply.context.assay_conditions != original_material
                    or any(member.source_parents != (original_material,) for member in supply.members)
                    or inputs.comparison is not None and inputs.comparison.reference_sources != (original_material,)):
                dependency("material.compatibility", DependencyKind.SCIENTIFIC_EVIDENCE,
                    "Every original member and both material/assay conditions must retain their disclosed source witness.", "material")
        if inputs.comparison is not None and inputs.comparison.candidate_context != ObjectIdentity.from_record(
                supply.context.context_id, supply.context):
            dependency("comparison.compatibility", DependencyKind.SCIENTIFIC_EVIDENCE,
                "Conditional references must describe the exact supplied material/assay context.", "comparison")
        if inputs.campaign is not None and (inputs.campaign.budget != BUDGET
                or NAMESPACE + ".design" not in inputs.campaign.system_ids
                or "world." + NAMESPACE not in inputs.campaign.world_ids
                or "claim." + NAMESPACE not in inputs.campaign.target_claim_ids):
            dependency("campaign.compatibility", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The selected original campaign does not contain this exact conditional material/world/claim and resource scope.", "campaign")
        source_dependencies = tuple(row for row in dependencies if row.source_key is not None)
        if not source_dependencies and all(getattr(inputs, key) is not None for key in INPUT_TYPES):
            sources = (*actual_allocation.sources, specification.identity, specification.campaign,
                specification.material, specification.source_query, specification.comparison)
            if len({source.object_id for source in sources}) != len(sources):
                dependency("source-alias", DependencyKind.SCIENTIFIC_EVIDENCE,
                    "Selected original source identities alias one another.")
            else:
                allocation = replace(actual_allocation, allocation_id="allocation.rubisco-kinetic-experiment." + specification.fingerprint(),
                    sources=tuple(sorted(sources, key=lambda row: row.object_id)))
    return inputs, allocation, dependencies


def _lower_exposed(specification, inputs):
    """Use the original declaration-owned lowering and exact scientific guards."""
    derived = kinetic_join_draft(inputs.supply, specification.query, inputs.comparison,
        relative_tolerance=specification.numerical_relative_tolerance,
        draft_id="draft.rubisco-kinetic-experiment." + specification.fingerprint())
    draft = replace(derived, campaign=inputs.campaign)
    records = {"supply": inputs.supply, "query": specification.query, "comparison": inputs.comparison}
    return draft, tuple(sorted((f"external.{NAMESPACE}.{key}", record) for key, record in records.items()))


def prepare_kinetic_experiment(specification, *, scientific_inputs: Mapping[str, UnitAllocation],
        execution: ExecutionSelection, protocol_bytes=None, method_inputs=None) -> ExperimentPreparation:
    """Freeze a proposed gas action over the complete original supplied roster."""
    inputs, allocation, dependencies = _scientific_selection(specification, scientific_inputs, method_inputs)
    if type(execution) is not ExecutionSelection:
        raise TypeError("kinetic preparation requires its separate typed execution selection")
    execution.__post_init__()

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency("rubisco.kinetic." + code, kind, detail, source_key))

    for name, kind, detail in (("environment", DependencyKind.ENVIRONMENT,
            "Select the existing locked kinetic profile; execution observes the actual worker and dispatches its numerical requirement."),
            ("source-snapshot", DependencyKind.ENVIRONMENT, "Select the producing implementation snapshot before execution."),
            ("output-root", DependencyKind.STORAGE, "Select explicit guarded custody before execution.")):
        if getattr(execution, name.replace("-", "_") if name != "environment" else "environment_id") is None:
            dependency(name, kind, detail)
    if protocol_bytes is not None:
        dependency("unselected-protocol", DependencyKind.EXTERNAL_INPUT,
            "This protocol is owned by the installed assay/assessment declarations; no extra protocol-file selection is declared.")
    if specification.evidence_scope == "PROSPECTIVE_REQUIRED":
        dependency("actual-domain-evidence", DependencyKind.SCIENTIFIC_EVIDENCE,
            "Actual independently assessed preparation, native molecular/chemical evidence, joint kinetic supply and biological calibration remain required; disclosed constants supply none of them.")
        dependency("issue-execution-reveal", DependencyKind.AUTHORITY,
            "Prospective work requires actual source, owner trust, approval, issue and separately scoped execution/reveal authority.")
        dependency("prospective-operation-lowering", DependencyKind.SOFTWARE,
            "This installed route lowers exposed conditional assay/assessment only; biological predictor and protected prospective stage composition remain unimplemented here.")
    draft, input_records = None, ()
    if not dependencies and allocation is not None:
        draft, input_records = _lower_exposed(specification, inputs)
    supply = inputs.supply
    members = () if supply is None else supply.members
    supplied = sum(member.constants is not None for member in members)
    partial = sum(member.constants is None and member.outcome == "AVAILABLE" for member in members)
    rejected = sum(member.outcome == "FALSIFIED" for member in members)
    census = ExperimentCensus((("analytical", 1), ("biological", 0), ("supported-members", len(specification.expected_member_ids))),
        (("analytical", int(supply is not None)), ("biological", 0), ("supported-members", len(members))),
        (("assay", 1), ("assess", 1)),
        tuple(sorted((("assessment-products", 1), ("assay-products", 1), ("member-assessments", len(specification.expected_member_ids)),
         ("partial-members", partial), ("rejected-members", rejected), ("supplied-solver-calls", supplied)))), 0)
    design_records = () if allocation is None else tuple(sorted(
        (getattr(specification, key).object_id if key != "query" else specification.source_query.object_id,
         getattr(inputs, key)) for key in INPUT_TYPES))
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=draft, input_records=input_records, execution=execution,
        design_records=design_records)


def validate_kinetic_experiment_instance(*, specification, allocation, draft, source_records) -> None:
    """Recompute the scientific association from authenticated original records.

    This predicate observes no environment, source checkout, custody destination
    or authority. It shares preparation's exact source checks and old lowering.
    """
    if type(specification) is not RubiscoKineticExperimentSpecification:
        raise TypeError("kinetic instance requires its exact specification")
    specification.__post_init__()
    if specification.evidence_scope != "EXPOSED_CONFORMANCE":
        raise ValueError("kinetic instance requires the exposed conditional evidence scope")
    if (type(source_records) is not tuple
            or tuple(key for key, _ in source_records) != tuple(sorted({key for key, _ in source_records}))):
        raise ValueError("kinetic instance changes its original source-record census")
    sources = dict(source_records)
    references = {key: specification.source_query if key == "query" else getattr(specification, key)
        for key in INPUT_TYPES}
    if set(sources) != {identity.object_id for identity in references.values()}:
        raise ValueError("kinetic instance omits or adds an original source record")
    resolved = bind_kinetic_experiment_inputs(specification,
        {key: sources[identity.object_id] for key, identity in references.items()})
    inputs, expected_allocation, dependencies = _scientific_selection(specification,
        resolved.scientific_inputs, resolved.method_inputs)
    if dependencies or expected_allocation is None:
        raise ValueError("kinetic instance changes its original scientific sources: "
            + "; ".join(row.code for row in sorted(dependencies, key=lambda row: row.code)))
    expected_draft, _ = _lower_exposed(specification, inputs)
    if allocation != expected_allocation or draft != expected_draft:
        raise ValueError("kinetic instance differs from its exact derived specification/allocation/action/draft")
