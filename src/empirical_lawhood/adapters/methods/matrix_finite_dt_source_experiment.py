# SPDX-License-Identifier: MPL-2.0
"""Copied explicit inputs for the genuine finite-dt Matrix source qualification.

This is one finite composition of installed owners. The researcher supplies its
actual source profile, prior TRAIN locator, scientific root and operational
selections; preparation never invents authority or changes scientific inputs.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_bindings as b
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_pipeline import (
    MatrixFiniteDtPendingSourceRows, MatrixFiniteDtSourceValidationRule, MatrixFiniteDtSourceVerification, metadata_records_for, validate_source_rows)
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineConfig, MatrixSourceQualificationConfig
from empirical_lawhood.adapters.methods.matrix_source_bindings import source_declarations
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledReservation, identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank, SelectedE4PhaseProgramme
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.candidate_compiler import _required_obligation_ids
from empirical_lawhood.runtime.experiment_preparation import (DependencyKind, ExecutionSelection, ExperimentCensus,
    ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs)
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

PROTOCOL_ID = "matrix.source.finite-dt-instrument-qualification"


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceQualificationSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-qualification-specification"
    specification_id: str
    selection: ObjectIdentity
    maximum_parallel_tasks: int

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        r._exact(self.selection, MatrixFiniteDtSourceQualificationSelection)
        if type(self.maximum_parallel_tasks) is not int or self.maximum_parallel_tasks < 1:
            raise ValueError("finite-dt source qualification needs an explicit positive worker count")

    @property
    def identity(self):
        return r.pin(self, "specification_id")


@dataclass(frozen=True, slots=True)
class MatrixFiniteDtSourceQualificationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-source/finite-dt-qualification-selection"
    record_id: str
    scope: r.MatrixFiniteDtSourceScope
    programme: SelectedE4PhaseProgramme
    bank: SelectedE4PhaseBank
    original_future_reservation: ScheduledReservation
    certificate: r.MatrixFiniteDtInstrumentCertificate
    rows: MatrixFiniteDtPendingSourceRows
    rule: MatrixFiniteDtSourceValidationRule
    source_publication: ArtifactWriteResult
    output_publication: ArtifactWriteResult
    verification: MatrixFiniteDtSourceVerification
    verification_publication: ArtifactWriteResult
    pipeline: MatrixSourcePipelineConfig
    authoring: RecursiveProspectiveAuthoringSpec
    source_configs: tuple[SourceMaterializationConfig, ...]
    exposure_support: tuple[tuple[ArtifactIdentity, ArtifactWriteResult | ExperimentFileInputBinding], ...]
    metadata_publications: tuple[tuple[ObjectIdentity, ArtifactWriteResult], ...]
    terminal_budgets: tuple[tuple[str, ResourceBudget], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.scope, r.MatrixFiniteDtSourceScope), (self.programme, SelectedE4PhaseProgramme),
                (self.bank, SelectedE4PhaseBank), (self.original_future_reservation, ScheduledReservation),
                (self.certificate, r.MatrixFiniteDtInstrumentCertificate), (self.rows, MatrixFiniteDtPendingSourceRows),
                (self.rule, MatrixFiniteDtSourceValidationRule), (self.source_publication, ArtifactWriteResult),
                (self.output_publication, ArtifactWriteResult), (self.verification, MatrixFiniteDtSourceVerification),
                (self.verification_publication, ArtifactWriteResult), (self.pipeline, MatrixSourcePipelineConfig),
                (self.authoring, RecursiveProspectiveAuthoringSpec)):
            if type(value) is not kind:
                raise TypeError("finite-dt source qualification substitutes an exact scientific or original custody owner")
            value.__post_init__()
        if (type(self.source_configs) is not tuple or any(type(value) is not SourceMaterializationConfig for value in self.source_configs)):
            raise TypeError("finite-dt source requires exact immutable materialization access controls")
        if (tuple(value.fingerprint() for value in self.source_configs) !=
                tuple(sorted({value.fingerprint() for value in self.source_configs}))
                or len({value.source_id for value in self.source_configs}) != len(self.source_configs)):
            raise ValueError("finite-dt source requires unique access controls in the owning SHA order")
        if (any(type(value) is not SourceMaterializationConfig for value in self.source_configs)
                or tuple(name for name, _ in self.terminal_budgets) != ("adjudicate", "pipeline", "qualification")
                or any(type(value) is not ResourceBudget or not b.BUDGET.contains(value) for _, value in self.terminal_budgets)
                or self.scope.pipeline_receipt != self.pipeline.assess()
                or self.scope.profile != self.pipeline.profile
                or self.scope.certificate != self.certificate.identity
                or self.scope.programme != self.programme.identity or self.scope.bank != self.bank.identity
                or self.scope.original_future_reservation != identity(self.original_future_reservation)
                or self.scope.publication != self.verification.identity or self.scope.recovery != self.verification.identity):
            raise ValueError("finite-dt source selection changes genuine source premises, replay or explicit resources")
        validate_source_rows(self.programme, self.bank, self.rows, self.rule)
        if tuple(value.object_id for value, _ in self.metadata_publications) != tuple(sorted({value.object_id for value, _ in self.metadata_publications})):
            raise ValueError("finite-dt source metadata publications repeat or reorder exact original objects")
        if tuple(reference for reference, _ in self.metadata_publications) != tuple(reference for reference, _ in metadata_records(self)):
            raise ValueError("finite-dt source omits an exact otherwise-nested metadata publication")
        for reference, publication in self.metadata_publications:
            if (type(reference) is not ObjectIdentity or type(publication) is not ArtifactWriteResult
                    or (publication.logical.payload_schema, publication.logical.content_sha256) !=
                        (reference.object_schema, reference.object_fingerprint)
                    or publication.logical.outcome_access is not r.BLIND or publication.logical.visibility_ceiling is not r.PROSPECTIVE):
                raise ValueError("finite-dt source metadata loses exact original canonical publication custody")
        required = {artifact for artifact, _ in current_exposure_support(self.bank.audit)}
        if (tuple(value.artifact_id for value, _ in self.exposure_support) !=
                tuple(sorted({value.artifact_id for value, _ in self.exposure_support}))
                or {value for value, _ in self.exposure_support} != required):
            raise ValueError("finite-dt source omits the exact current exposure census publication")
        for artifact, custody in self.exposure_support:
            if type(artifact) is not ArtifactIdentity or type(custody) not in (ArtifactWriteResult, ExperimentFileInputBinding):
                raise TypeError("finite-dt source exposure support requires actual published or FILE custody")
            artifact.__post_init__()
            custody.__post_init__()
            if type(custody) is ExperimentFileInputBinding:
                if custody.identity != artifact:
                    raise ValueError("finite-dt source exposure FILE changes original supporting bytes")
            elif (custody.logical.logical_artifact_id, custody.logical.payload_schema, custody.logical.media_type,
                    custody.logical.content_sha256, custody.materialization.physical_sha256, custody.materialization.size_bytes) != (
                    artifact.artifact_id, artifact.payload_schema, artifact.media_type, artifact.sha256, artifact.sha256, artifact.size_bytes):
                raise ValueError("finite-dt source exposure publication changes original supporting bytes")

    @property
    def identity(self):
        return r.pin(self)



def selection_types():
    return (MatrixFiniteDtSourceQualificationSelection,)


def specification_types():
    return (MatrixFiniteDtSourceQualificationSpecification,)


def metadata_records(selection):
    """Exact expected metadata records; this pure enumeration grants no custody."""
    return metadata_records_for(selection.scope, selection.pipeline)


def operands(selection):
    values = {"scope": selection.scope, "programme": selection.programme, "bank": selection.bank,
        "reservation": selection.bank.reservation, "original-reservation": selection.original_future_reservation,
        "assay": selection.bank.response_selection, "numerical": selection.bank.specification.selection.numerical_design,
        "cutoff": selection.scope.cutoff, "certificate": selection.certificate}
    return values


def node_id(scope, phase):
    return r.NAMESPACE + "." + scope.record_id + "." + phase


def operand_access_from_authoring(*, operands, authoring):
    """Replay actual retained input labels without inferring access from bodies."""
    result = {}
    for name, value in operands.items():
        selected = tuple(row for row in authoring.draft.external_inputs
            if (row.payload_schema, row.expected_content_sha256, row.maximum_size_bytes) ==
                (value.SCHEMA, value.fingerprint(), len(value.canonical_bytes())))
        if len(selected) != 1:
            raise ValueError("source preparation changes its exact retained operand access census")
        result[name] = selected[0].outcome_access, selected[0].visibility_ceiling
    return result


def compose_source_draft(*, scope, scientific_operands, pipeline, root, campaign, draft_id, terminal_budgets, operand_access):
    """Pure finite graph; source/certificate byte authentication is an API duty."""
    scope.__post_init__()
    if set(scientific_operands) != set(b.input_kinds()) or scientific_operands["scope"] != scope:
        raise ValueError("finite-dt source changes its exact complete scientific operands")
    if (not isinstance(operand_access, Mapping) or set(operand_access) != set(scientific_operands)
            or any(type(value) is not tuple or len(value) != 2
                or type(value[0]) is not OutcomeAccess or type(value[1]) is not VisibilityCeiling
                for value in operand_access.values())
            or any(operand_access[name][0] is OutcomeAccess.OUTCOME_BLIND for name in ("bank", "programme"))):
        raise ValueError("finite-dt model-bearing operands require their actual inherited access labels")
    budgets = dict(terminal_budgets)
    if set(budgets) != {"pipeline", "qualification", "adjudicate"}:
        raise ValueError("finite-dt source omits an explicit replay or closeout budget")
    gates = {}
    configs, externals, records, links = {}, {}, {}, []
    for config in r.gate_configs(scope):
        node = node_id(scope, config.gate_kind.value.lower())
        configs[node] = config
        gates[config.gate_kind] = r.validate_gate_operands(config, scope, scientific_operands)
    gate_evidence = tuple(sorted(gates.values(), key=lambda value: value.evidence_id))
    specification = r.qualification_specification(scope)
    from empirical_lawhood.runtime.capabilities import CapabilityRegistry
    registry = CapabilityRegistry("registry." + scope.record_id,
        tuple(sorted((b.gate_declaration(kind).manifest() for kind in r.GATES), key=lambda value: value.registry_id)))
    qualification = MatrixSourceQualificationConfig("config.qualification." + scope.record_id,
        specification, scope.pipeline_receipt, registry, gate_evidence)
    result = qualification.assess()
    configs[node_id(scope, "pipeline")] = pipeline
    configs[node_id(scope, "qualification")] = qualification
    products = tuple(sorted((r.pin(scope.pipeline_receipt, "receipt_id"), r.pin(result, "result_id"),
        *(r.pin(value, "evidence_id") for value in gate_evidence)), key=lambda value: value.object_id))
    configs[node_id(scope, "adjudicate")] = b.MatrixFiniteDtSourceCloseoutConfig("config.adjudicate." + scope.record_id,
        products, scope.group_ids, budgets["adjudicate"])
    for name, value in sorted(scientific_operands.items()):
        reference = scope.identity if name == "scope" else (r.pin(value, "cutoff_id") if name == "cutoff" else
            value.identity if name in ("programme", "bank", "assay", "certificate") else identity(value))
        key = "external." + reference.object_id
        external = RecursiveExternalInput(key, reference.object_id, value.SCHEMA, "application/json", len(value.canonical_bytes()),
            *operand_access[name], value.fingerprint(), "QUALIFICATION")
        if externals.setdefault(key, external) != external or records.setdefault(key, value) != value:
            raise ValueError("finite-dt source aliases different scientific inputs")
        for kind in r.GATES:
            node = node_id(scope, kind.value.lower())
            links.append(RecursiveInputLink("edge." + node + "." + name, node, name,
                external_input_id=key, scientific_role="QUALIFICATION"))
    for kind in r.GATES:
        node = node_id(scope, kind.value.lower())
        links.append(RecursiveInputLink("edge." + node + ".closeout", node_id(scope, "adjudicate"),
            kind.value.lower(), producer_node_id=node, producer_output_id="product", scientific_role="QUALIFICATION"))
    for phase in ("pipeline", "qualification"):
        links.append(RecursiveInputLink("edge." + phase + ".closeout", node_id(scope, "adjudicate"), phase,
            producer_node_id=node_id(scope, phase), producer_output_id="product", scientific_role="QUALIFICATION"))
    declarations = {node_id(scope, kind.value.lower()): b.gate_declaration(kind) for kind in r.GATES}
    declarations.update({node_id(scope, "pipeline"): source_declarations()[0],
        node_id(scope, "qualification"): source_declarations()[1], node_id(scope, "adjudicate"): b.closeout_declaration()})
    required = set(_required_obligation_ids(root.experiment))
    owners = {value: node_id(scope, "qualification") for value in required}
    owners.update({value.cutoff_id: node_id(scope, "causal_cutoff") for value in root.experiment.information_cutoffs})
    for value in (root.experiment.reveal_barrier.barrier_id, *(root.experiment.experiment_id + "." + suffix
            for suffix in ("admission", "authority", "required-outputs", "seal-reveal-separation"))):
        owners[value] = node_id(scope, "adjudicate")
    operations = []
    for node, config in sorted(configs.items()):
        phase = node.rsplit(".", 1)[-1]
        budget = config.resource_budget if type(config) is r.MatrixFiniteDtGateConfig else budgets[phase]
        operations.append(RecursiveOperationSpec.from_config(node_id=node, selection=declarations[node].registration().selection,
            config_id=config.config_id, config=config,
            obligation_ids=tuple(sorted({"obligation." + node} | {key for key, owner in owners.items() if owner == node})),
            resource_budget=budget))
    draft = RecursiveStudyDraft(draft_id, root.question, campaign, (), (), (), tuple(operations),
        tuple(externals[key] for key in sorted(externals)), tuple(sorted(links, key=lambda value: value.edge_id)),
        tuple(sorted(configs)), prospective_draft=root)
    return draft, tuple(sorted(records.items())), qualification, result


def lower(selection):
    root = selection.authoring.draft.prospective_draft
    if root is None:
        raise ValueError("finite-dt source requires its actual prospective numerical scientific root")
    selected = operands(selection)
    return compose_source_draft(scope=selection.scope, scientific_operands=selected, pipeline=selection.pipeline,
        root=root, campaign=selection.authoring.draft.campaign, draft_id=selection.authoring.draft.draft_id,
        terminal_budgets=selection.terminal_budgets,
        operand_access=operand_access_from_authoring(operands=selected, authoring=selection.authoring))


def source_allocation(selection):
    from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
    coordinates = {coordinate_identity(value): value for value in selection.bank.reservation.allocation.coordinates}
    units = []
    for group in selection.scope.group_ids:
        cases = tuple(value for value in selection.programme.cases if value.independent_group_id == group)
        views = tuple(sorted({view.view_id for case in cases for view in
            (coordinates[case.coordinate].primary_view, coordinates[case.coordinate].fine_view)}))
        units.append(IndependentUnit(group, selection.scope.bank.object_id, cases[0].family_id, views, False))
    return UnitAllocation("allocation." + selection.scope.record_id,
        tuple(sorted((selection.scope.bank, selection.certificate.identity), key=lambda value: value.object_id)),
        tuple(units), tuple(UnitRoleAssignment(group, "source") for group in selection.scope.group_ids))


def input_record_types():
    return selection_types()


def bind_inputs(specification, records, **kwargs):
    if (not isinstance(records, Mapping) or set(records) != {"selection"}
            or type(records["selection"]) not in selection_types()):
        raise ValueError("finite-dt qualification requires its one complete explicit source selection")
    selected = records["selection"]
    selected.__post_init__()
    return PreparedExperimentInputs({"source": source_allocation(selected)}, selected)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if (type(specification) not in specification_types() or type(execution) is not ExecutionSelection):
        raise TypeError("finite-dt qualification requires its exact public specification and operational selection")
    specification.__post_init__()
    execution.__post_init__()
    if method_inputs is None:
        return ExperimentPreparation(specification.identity,
            ExperimentCensus((), (), (("closeout", 1), ("independent-source-gates", len(r.GATES)),
                ("original-owner-replays", 2)), (("source-premise-products", len(r.GATES) + 3),), 0),
            (ExperimentDependency("matrix.finite-dt.source-selection", DependencyKind.EXTERNAL_INPUT,
                "Select the complete receipt-backed native TRAIN instrument certificate and explicit future-source inputs.",
                source_key="selection"),), execution=execution, specification_record=specification)
    if type(method_inputs) not in selection_types():
        raise TypeError("finite-dt qualification requires its exact original source selection")
    method_inputs.__post_init__()
    selected = method_inputs
    if (specification.selection != selected.identity or execution.workers != specification.maximum_parallel_tasks
            or scientific_inputs != {"source": source_allocation(selected)} or protocol_bytes is not None):
        raise ValueError("finite-dt qualification changes selected scientific inputs, workers or protocol")
    draft, records, _, _ = lower(selected)
    if draft != selected.authoring.draft:
        raise ValueError("finite-dt qualification changes complete declared source/gate/closeout graph")
    missing = []
    for name, field, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, field) is None:
            missing.append(ExperimentDependency("matrix.finite-dt." + name, kind, "Select actual " + name + " before authoring."))
    count = len(selected.scope.group_ids)
    census = ExperimentCensus((("source-groups", count),), (("source-groups", count),),
        (("closeout", 1), ("independent-source-gates", len(r.GATES)), ("original-owner-replays", 2)), (("source-premise-products", len(r.GATES) + 3),), 0)
    return ExperimentPreparation(specification.identity, census, tuple(sorted(missing, key=lambda value: value.code)),
        allocation=source_allocation(selected), draft=draft, input_records=records, execution=execution,
        specification_record=specification, design_records=((selected.record_id, selected),),
        prospective_spec=selected.authoring, source_configs=selected.source_configs,
        assessment_limitations=(ExperimentDependency("matrix.finite-dt.no-global-qualification", DependencyKind.SCIENTIFIC_EVIDENCE,
            "Finite-dt instrument source premise only; future numerical outcomes, continuum, sampling and transport remain unestablished."),))


def validate_instance(*, specification, allocation, draft, source_records):
    rows = tuple(value for _, value in source_records if type(value) in selection_types())
    if len(rows) != 1 or len(source_records) != 1:
        raise ValueError("finite-dt qualification changes its exact original public source selection")
    selected, = rows
    if (specification.selection != selected.identity or allocation != source_allocation(selected)
            or draft != selected.authoring.draft or draft != lower(selected)[0]):
        raise ValueError("finite-dt qualification changes its original complete source/graph/allocation")
