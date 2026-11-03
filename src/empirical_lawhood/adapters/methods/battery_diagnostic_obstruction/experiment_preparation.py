# SPDX-License-Identifier: MPL-2.0
"""Derive one retained-history programme from references and existing custody.

Preparation reads no supplier payload, creates no copy and runs no assessment.
Shared authoring authenticates the portable parent; the registered operation
premise authenticates original source custody at every current boundary.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ContributionRole
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest
from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigin, RecursiveInputOriginKind, RecursiveInputOrigins
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from . import contracts as c, science
from .authenticated_operation import lower_authenticated_obstruction
from .experiment_specification import AUTHENTICATED_NODE, ObstructionExperimentSpecification, ObstructionSourceCustodySelection


INPUT_TYPES = {"custody": ObstructionSourceCustodySelection, "parent": ContributionManifest, "source": c.ObstructionSource}


@dataclass(frozen=True, slots=True)
class ObstructionExperimentInputs:
    source: c.ObstructionSource | None = None
    parent: ContributionManifest | None = None
    custody: ObstructionSourceCustodySelection | None = None
    parent_directory: Path | None = None

    def __post_init__(self):
        for key, kind in INPUT_TYPES.items():
            record = getattr(self, key)
            if record is not None:
                if type(record) is not kind:
                    raise TypeError("obstruction experiment has the wrong closed input type for " + key)
                record.__post_init__()
        if self.parent_directory is not None and (not isinstance(self.parent_directory, Path)
                or not self.parent_directory.is_absolute() or ".." in self.parent_directory.parts):
            raise ValueError("obstruction prior needs an explicitly selected absolute portable contribution directory")


def input_record_types():
    return tuple(sorted(INPUT_TYPES.values(), key=lambda kind: kind.SCHEMA))


def allocation_for(specification, source):
    refs = (specification.identity, specification.parent, c.identity(source))
    view = "view." + c.NAMESPACE + ".complete-adverse-operational-ledger"
    unit = IndependentUnit(c.UNIT, source.source_id, "family.battery-lgm50.exposed-numerical-model", (view,), True)
    return UnitAllocation("allocation.battery-obstruction." + specification.fingerprint(),
        tuple(sorted(refs, key=lambda row: row.object_id)), (unit,), (UnitRoleAssignment(c.UNIT, "retained-history"),))


def bind_obstruction_experiment_inputs(specification, records, *, record_paths=None, files=None):
    if type(specification) is not ObstructionExperimentSpecification:
        raise TypeError("obstruction input binding requires its exact experiment specification")
    specification.__post_init__()
    if not isinstance(records, Mapping) or set(records) - set(INPUT_TYPES) or files:
        raise ValueError("obstruction inputs require only the closed source, parent manifest and operational custody records")
    paths = {} if record_paths is None else record_paths
    if not isinstance(paths, Mapping) or set(paths) - set(records):
        raise ValueError("obstruction input locations add a role outside the exact selected canonical records")
    directory = None
    if "parent" in paths:
        path = paths["parent"]
        if (not isinstance(path, Path) or not path.is_absolute() or path.name != "contribution.json"
                or ".." in path.parts or any(part.is_symlink() for part in (path, *path.parents))):
            raise ValueError("obstruction parent location must be the original exact contribution.json without links or traversal")
        directory = path.parent
    inputs = ObstructionExperimentInputs(**records, parent_directory=directory)
    allocation = None if inputs.source is None else allocation_for(specification, inputs.source)
    return PreparedExperimentInputs({} if allocation is None else {"source": allocation}, inputs)


def _scientific_selection(specification, scientific_inputs, method_inputs):
    if type(specification) is not ObstructionExperimentSpecification:
        raise TypeError("obstruction preparation requires its exact selected specification")
    specification.__post_init__()
    if not isinstance(scientific_inputs, Mapping):
        raise TypeError("obstruction preparation requires its typed source allocation mapping")
    dependencies = []

    def dependency(code, kind, detail, source_key=None):
        dependencies.append(ExperimentDependency("battery.obstruction." + code, kind, detail, source_key))

    if set(scientific_inputs) - {"source"}:
        dependency("unselected-allocation", DependencyKind.EXTERNAL_INPUT, "Only the original retained numerical-family allocation is selected.")
    if method_inputs is None:
        inputs = ObstructionExperimentInputs()
    elif type(method_inputs) is ObstructionExperimentInputs:
        inputs = method_inputs
        inputs.__post_init__()
    else:
        dependency("method-inputs", DependencyKind.EXTERNAL_INPUT, "Supply the exact closed original source, parent and custody selections.")
        inputs = ObstructionExperimentInputs()
    for key in INPUT_TYPES:
        if getattr(inputs, key) is None:
            dependency(key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual selected " + key + " record.", key)
    allocation = None
    if inputs.source is not None:
        if c.identity(inputs.source) != specification.source:
            dependency("source.identity", DependencyKind.SCIENTIFIC_EVIDENCE, "The source differs from its exact selected original bytes.", "source")
        try:
            science.validate_source(inputs.source)
        except ValueError as error:
            dependency("source.primary", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "source")
        allocation = allocation_for(specification, inputs.source)
        if scientific_inputs.get("source") != allocation:
            dependency("source.allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain the original exposed numerical-family unit and nested view.", "source")
    if inputs.parent is not None and ObjectIdentity.from_record(inputs.parent.contribution_id, inputs.parent) != specification.parent:
        dependency("parent.identity", DependencyKind.SCIENTIFIC_EVIDENCE, "The prior contribution differs from its exact selected identity.", "parent")
    if inputs.source is not None and inputs.parent is not None:
        matching = tuple(row for row in inputs.parent.products if row.record == inputs.source.prior_supply
            and row.role is ContributionRole.DESIGN_OPERAND)
        original = tuple(row for row in inputs.source.input_manifests
            if row.logical.payload_schema == inputs.source.prior_supply.object_schema
            and row.logical.content_sha256 == inputs.source.prior_supply.object_fingerprint)
        if (len(matching) != 1 or inputs.parent.scope != science.scope(inputs.source)
                or len(original) != 1 or matching[0].artifact.sha256 != inputs.source.prior_supply.object_fingerprint
                or (matching[0].artifact.artifact_id, matching[0].artifact.size_bytes, matching[0].artifact.media_type) != (
                    original[0].logical.logical_artifact_id, original[0].materialization.size_bytes, original[0].logical.media_type)):
            dependency("parent.product", DependencyKind.SCIENTIFIC_EVIDENCE,
                "The original negative MODEL must be the exact prior product, scope and producing receipt.", "parent")
    if inputs.source is not None and inputs.custody is not None:
        from .experiment_specification import AuthenticatedObstructionConfig
        try:
            AuthenticatedObstructionConfig("config." + AUTHENTICATED_NODE,
                c.ObstructionOperationConfig("config." + c.NAMESPACE + ".assess", inputs.source), inputs.custody)
        except ValueError as error:
            dependency("custody.source", DependencyKind.SCIENTIFIC_EVIDENCE, str(error), "custody")
    if inputs.custody is not None and inputs.custody.selection_id in {
            specification.specification_id, specification.source.object_id, specification.parent.object_id}:
        dependency("custody.alias", DependencyKind.EXTERNAL_INPUT,
            "The operational custody selection cannot alias the specification or original scientific sources.", "custody")
    return inputs, allocation, dependencies


def _draft(specification, inputs):
    return lower_authenticated_obstruction(inputs.source, inputs.parent, inputs.custody,
        draft_id="draft.battery-obstruction-experiment." + specification.fingerprint())


def _origins(draft, source, parent):
    product, = (row for row in parent.products if row.record == source.prior_supply and row.role is ContributionRole.DESIGN_OPERAND)
    return RecursiveInputOrigins(tuple(sorted((
        RecursiveInputOrigin("external." + AUTHENTICATED_NODE + ".obstruction-source", RecursiveInputOriginKind.SOURCE,
            source.fingerprint(), "SOURCE"),
        RecursiveInputOrigin("external." + AUTHENTICATED_NODE + ".prior", RecursiveInputOriginKind.CONTRIBUTION,
            product.artifact.sha256, product.role.value, ObjectIdentity.from_record(parent.contribution_id, parent),
            product.product_id, product.producing_receipt)), key=lambda row: row.input_id)))


def prepare_obstruction_experiment(specification, *, scientific_inputs, execution: ExecutionSelection,
        protocol_bytes=None, method_inputs=None):
    inputs, allocation, dependencies = _scientific_selection(specification, scientific_inputs, method_inputs)
    if type(execution) is not ExecutionSelection:
        raise TypeError("obstruction preparation requires its separate execution selection")
    execution.__post_init__()
    for key, field, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, field) is None:
            dependencies.append(ExperimentDependency("battery.obstruction." + key, kind, "Select the existing " + key + " explicitly."))
    if inputs.parent_directory is None:
        dependencies.append(ExperimentDependency("battery.obstruction.parent.directory", DependencyKind.EXTERNAL_INPUT,
            "Select the actual portable parent's contribution.json; its complete custody is authenticated by shared authoring.", "parent"))
    if protocol_bytes is not None:
        dependencies.append(ExperimentDependency("battery.obstruction.unselected-protocol", DependencyKind.EXTERNAL_INPUT,
            "The original source owns the retained history protocol; replacement protocol bytes are unselected."))
    draft, records, dirs, origins = None, (), (), None
    if not dependencies and allocation is not None:
        draft = _draft(specification, inputs)
        records = (("external." + AUTHENTICATED_NODE + ".obstruction-source", inputs.source),)
        dirs = (inputs.parent_directory,)
        origins = _origins(draft, inputs.source, inputs.parent)
        origins.validate_draft(draft)
    resolved = inputs.source is not None and c.identity(inputs.source) == specification.source
    roles = (("entered-native-operation-records", 1), ("independent-numerical-families", 1),
        ("new-physical-units", 0), ("original-negative-forecasts", 36), ("original-negative-reference-checks", 9),
        ("returned-diagnostic-results", 0), ("returned-trace-rows", 0), ("selected-diagnostic-forecasts", 12))
    census = ExperimentCensus(roles, tuple((key, count if resolved else 0) for key, count in roles),
        (("retained-history-reassessment", 1),), (("retained-history-products", 1),), 0)
    design_records = tuple(sorted((
        (record.source_id if key == "source" else record.contribution_id if key == "parent" else record.selection_id, record)
        for key in INPUT_TYPES if (record := getattr(inputs, key)) is not None)))
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)),
        allocation=allocation, draft=draft, input_records=records, execution=execution, specification_record=specification,
        design_records=design_records, contribution_dirs=dirs, origins=origins)


def validate_obstruction_experiment_instance(*, specification, allocation, draft, source_records):
    if type(source_records) is not tuple or tuple(key for key, _ in source_records) != tuple(sorted({key for key, _ in source_records})):
        raise ValueError("obstruction instance changes its complete original source-record census")
    selected = {}
    for key, record in source_records:
        role, = (name for name, kind in INPUT_TYPES.items() if type(record) is kind)
        expected = record.source_id if role == "source" else record.contribution_id if role == "parent" else record.selection_id
        if role in selected or key != expected:
            raise ValueError("obstruction instance aliases or duplicates an original source or operational record")
        selected[role] = record
    if set(selected) != set(INPUT_TYPES):
        raise ValueError("obstruction instance omits or adds an original source, parent or custody selection")
    resolved = bind_obstruction_experiment_inputs(specification, selected)
    inputs, expected_allocation, dependencies = _scientific_selection(specification, resolved.scientific_inputs, resolved.method_inputs)
    if dependencies or allocation != expected_allocation or draft != _draft(specification, inputs):
        raise ValueError("obstruction instance differs from its exact source/parent/custody/allocation and derived graph")
