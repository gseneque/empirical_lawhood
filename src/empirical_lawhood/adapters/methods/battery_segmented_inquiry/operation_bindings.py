# SPDX-License-Identifier: MPL-2.0
"""One native forecast or two-trace comparison per ordinary scheduled task.

The scientific roster is unchanged. Equal physical recipe conditions have
explicit DERIVED reuse products rather than repeated native effect slots.
Historical UNKNOWN completion remains retained. Changed actual preparation
and short-step operands grant neither replay nor scientific entry authority.
"""

from functools import partial
from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from empirical_lawhood.adapters.methods.battery_segmented_inquiry.storage_codecs import SEGMENT_STORAGE_CODECS

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_qualification as pq, durable_roster as dr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_contracts as sc, segmented_roster as sr, segmented_evidence as se
from empirical_lawhood.adapters.methods.battery_refined_inquiry.source_derived_preparation import SourceRootPreparation, SourceRootAssessment
from .evidence_stream import SegmentStreamChunk, MEDIA as STREAM_MEDIA
from empirical_lawhood.adapters.methods.battery_refined_inquiry.operation_bindings import SourcePolicyAdmission, history_type
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

NAMESPACE = "battery-segmented-inquiry"
QUESTION = "Do complete source-bound, independently assessed preparations and numerical comparisons supply a dependable conditional charging description?"
OPERATIONS = ("assess", "compare", "forecast", "qualify", "reuse", "validate")
MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
FORECAST_OUTPUTS = (("evidence", se.SegmentedNativeEvidence), ("segments", SegmentStreamChunk))


@dataclass(frozen=True, slots=True)
class SegmentedOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented-inquiry/operation-config"
    config_id: str
    operation: str
    index: int | None
    source: c.RefinedSource
    policy: c.NumericalPolicy
    roster: ObjectIdentity
    uncertain_work: ObjectIdentity
    producing_provenance: ObjectIdentity
    preparation_protocols: tuple[ObjectIdentity, ...]
    history_artifact_id: str
    method: sc.SegmentedMethodProtocol
    supplies: tuple[tuple[SourceRootPreparation, SourceRootAssessment], ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        validate_stable_id(self.history_artifact_id)
        if self.operation not in OPERATIONS or self.config_id != "config." + node_id(self.operation, self.index):
            raise ValueError("durable operation changes its exact task identity")
        if self.source.policy != c.identity(self.policy) or not self.policy.tolerance_probe:
            raise ValueError("durable operation changes its selected complete54 source/policy")
        if self.source.diagnostic.object_schema != "empirical-lawhood/battery-diagnostic-obstruction/assessment":
            raise ValueError("durable successor requires explicit authentic unknown-completion history")
        expected = roster_for(self)
        if self.roster != ObjectIdentity.from_record(expected.roster_id, expected):
            raise ValueError("durable operation changes its actual complete frozen roster")
        if (self.uncertain_work.object_schema != dr.UnknownDiagnosticWork.SCHEMA
                or self.producing_provenance.object_schema != NumericalProducingProvenance.SCHEMA
                or len(self.preparation_protocols) != len(sr.distinct_forecast_groups(expected))
                or any(row.object_schema != pc.PreparationProtocol.SCHEMA for row in self.preparation_protocols)
                or len(set(row.object_id for row in self.preparation_protocols)) != len(self.preparation_protocols)):
            raise ValueError("durable operation omits its authentic history/provenance/protocol operands")
        if self.operation in {"validate", "qualify"}:
            if self.index is not None:
                raise ValueError("aggregate operation has no forecast/pair ordinal")
        elif type(self.index) is not int or not 0 <= self.index < (36 if self.operation == "compare" else 54):
            raise ValueError("durable operation changes its scientific ordinal")
        elif self.operation != "compare":
            representative = representative_index(expected, self.index)
            if (self.operation == "reuse") != (representative != self.index):
                raise ValueError("durable operation disguises an equal-condition reuse as native contact")

    @property
    def operands(self):
        roster = roster_for(self)
        return tuple(sorted((c.identity(self.source), c.identity(self.policy),
            ObjectIdentity.from_record("selection." + self.policy.policy_id, self.policy.selection),
            self.source.diagnostic, self.roster, self.uncertain_work, self.producing_provenance,
            *self.preparation_protocols, ObjectIdentity.from_record(self.method.method_id, self.method),
            *(ObjectIdentity.from_record(row.preparation_id, row) for row, _ in self.supplies),
            *(ObjectIdentity.from_record(row.assessment_id, row) for _, row in self.supplies), *(c.identity(native) for native in roster.configurations)), key=lambda row: row.object_id))


def node_id(operation, index=None):
    return NAMESPACE + "." + operation + ("." + f"{index:03d}" if index is not None else "")


@lru_cache(maxsize=8)
def _roster(source, policy, uncertain_work, method, supplies):
    if (type(method) is not sc.SegmentedMethodProtocol or len(supplies) != 2
            or tuple(row.parameter_source for row, _ in supplies) != ("Chen2020", "ORegan2022")):
        raise ValueError("segmented operation omits its two exact stock suppliers or prospective method")
    original = dr.freeze_forecast_roster(source, policy)
    configs = []
    for native in original.configurations:
        preparation, assessment = supplies[0 if native.model_view == "chen-spme" else 1]
        configs.append(sc.SegmentedNativeConfig("config.segmented." + str(method.maximum_segment_horizon_s) + "." + native.config_id.removeprefix("config."),
            native, preparation, assessment, method))
    names = {row.native.config_id: row.config_id for row in configs}
    return sr.SegmentedQualificationRoster("roster.segmented." + str(method.maximum_segment_horizon_s), original,
        uncertain_work, method, tuple(configs), tuple((names[left.object_id], names[right.object_id]) for left, right in original.comparison_config_pairs))


def roster_for(config):
    return _roster(config.source, config.policy, config.uncertain_work, config.method, config.supplies)


def supplies_for(roster):
    by_stock = {row.preparation.parameter_source: (row.preparation, row.preparation_assessment) for row in roster.configurations}
    return tuple(by_stock[name] for name in ("Chen2020", "ORegan2022"))


def forecast_primitive(config):
    # Labels/IDs alone never distinguish physical work. These changed actual
    # source-assigned binary64 values and short-step operands do distinguish it.
    return canonical_json_bytes({"native_primitive_sha256": sha256(dr.forecast_primitive(config.native)).hexdigest(),
        "parameter_source": config.preparation.parameter_source,
        "assigned_negative_concentration": dict(config.preparation.binary64_operands)["assigned_negative_concentration"],
        "assigned_positive_concentration": dict(config.preparation.binary64_operands)["assigned_positive_concentration"],
        "maximum_segment_horizon_binary64": float(config.method.maximum_segment_horizon_s).hex(),
        "preparation_method": config.method.preparation_method, "continuation_method": config.method.continuation_method,
        "output_method": config.method.output_method})


def representative_index(roster, index):
    primitive = forecast_primitive(roster.configurations[index])
    return next(i for i, row in enumerate(roster.configurations) if forecast_primitive(row) == primitive)


def summary_node(roster, index):
    return node_id("assess" if representative_index(roster, index) == index else "reuse", index)


def common_inputs(config):
    return (("history", history_type(config.source.diagnostic)), ("policy", c.NumericalPolicy),
        ("producing-provenance", NumericalProducingProvenance), ("roster", sr.SegmentedQualificationRoster),
        ("selection", c.NumericalSelection), ("source", c.RefinedSource), ("uncertain-work", dr.UnknownDiagnosticWork),
        ("method", sc.SegmentedMethodProtocol), ("preparation-chen", SourceRootPreparation),
        ("preparation-oregan", SourceRootPreparation), ("source-assessment-chen", SourceRootAssessment),
        ("source-assessment-oregan", SourceRootAssessment))


def operation_inputs(operation):
    if operation == "validate":
        return ()
    if operation == "forecast":
        return (("admission", SourcePolicyAdmission), ("entry", sr.ProspectiveMethodDisposition),
            ("native-config", sc.SegmentedNativeConfig), ("selected-protocol", pc.PreparationProtocol))
    if operation == "assess":
        return FORECAST_OUTPUTS
    if operation == "reuse":
        return (("summary", pq.SegmentedTraceSummary),)
    if operation == "compare":
        return (("left-summary", pq.SegmentedTraceSummary), ("left-evidence", se.SegmentedNativeEvidence),
            ("right-summary", pq.SegmentedTraceSummary), ("right-evidence", se.SegmentedNativeEvidence))
    return tuple(("summary-" + f"{i:03d}", pq.SegmentedTraceSummary) for i in range(54)) + tuple(
        ("comparison-" + f"{i:03d}", pq.SegmentedComparison) for i in range(36))


def operation_outputs(operation):
    if operation == "validate":
        return (("admission", SourcePolicyAdmission),) + tuple(("entry-" + f"{i:03d}", sr.ProspectiveMethodDisposition) for i in range(54))
    if operation == "forecast":
        return FORECAST_OUTPUTS
    if operation == "assess":
        return (("summary", pq.SegmentedTraceSummary),)
    if operation == "reuse":
        return (("reuse", pq.SegmentedConditionReuse), ("summary", pq.SegmentedTraceSummary))
    if operation == "compare":
        return (("comparison", pq.SegmentedComparison),)
    return (("qualification", pq.SegmentedQualification),)


def media_for(name):
    return STREAM_MEDIA if name == "segments" else MEDIA


def operation_stage(operation):
    return ScientificStage.ACQUIRE if operation == "forecast" else ScientificStage.ADMISSION if operation == "validate" else ScientificStage.QUALIFY


def development_root(config, *, study_id):
    scope = c.scope(config.source)
    claim = ClaimSpec("claim." + NAMESPACE, scope.world_id, "population.battery-thermal-inquiry.exposed-lgm50", QUESTION,
        "Complete54 selected conditional forecasts and36 comparisons, including six explicit equal-condition aliases;48 distinct native charging requests.",
        c.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "One existing numerical family; zero fresh physical units. Preparation, precision, later use and physical qualification are separate achievements.",
        ("assumption.exposed-lgm50-model-family",), numerical_view_ids=("view.battery-segmented-inquiry.complete-family",))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope.system_id, config.source),
        scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (c.UNIT,), ("view.battery-segmented-inquiry.complete-family",), (claim,), config.operands)


def native_effect_slot_ids(config):
    if config.operation != "forecast":
        return ()
    native = roster_for(config).configurations[config.index]
    return ("native.battery-charging." + sha256(forecast_primitive(native)).hexdigest(),)


def scientific_root_validator(config, context):
    if (context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != node_id(config.operation, config.index) or context.stage is not operation_stage(config.operation)
            or context.unit_ids != (c.UNIT,) or context.selected_unit_ids != (c.UNIT,)
            or context.complete_unit_census != (config.operation == "forecast")):
        raise ValueError("durable operation changes its exact scientific root/stage/unit census")
    from .recursive_translation import validate_graph
    validate_graph(context, config)


def operation_declarations():
    from .recursive_translation import scientific_work
    from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import DiagnosticResult
    from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
    from .runner import prepare_native_work
    from empirical_lawhood.adapters.methods.battery_refined_inquiry.prepared_native import native_worker_environment
    registrations = []
    for operation in OPERATIONS:
        inputs = operation_inputs(operation) + (('policy', c.NumericalPolicy), ('selection', c.NumericalSelection), ('source', c.RefinedSource), ('roster', sr.SegmentedQualificationRoster), ('uncertain-work', dr.UnknownDiagnosticWork), ('producing-provenance', NumericalProducingProvenance), ('history', ObstructionAssessment), ('method', sc.SegmentedMethodProtocol), ('preparation-chen', SourceRootPreparation), ('preparation-oregan', SourceRootPreparation), ('source-assessment-chen', SourceRootAssessment), ('source-assessment-oregan', SourceRootAssessment))
        registrations.append(RecursiveOperationDeclaration(
            capability_key=NAMESPACE + '.' + operation, capability_version='1.0.0',
            implementation_id='source-derived-segmented-original-full-custody-v1.' + operation,
            kind=CapabilityKind.SIMULATOR if operation == 'forecast' else CapabilityKind.ANALYSIS,
            config_record_type=SegmentedOperationConfig, stage=operation_stage(operation),
            input_ports=tuple((RecursivePortContract(name, record.SCHEMA, media_for(name), None) for name, record in sorted(inputs))),
            outputs=tuple((OutputTemplate(name, record.SCHEMA, ArtifactProfile.JSONL_CHUNKS if name == 'segments' else ArtifactProfile.CANONICAL_JSON, media_for(name), '.jsonl' if name == 'segments' else '.json') for name, record in operation_outputs(operation))),
            permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
            conformance_check_ids=tuple(sorted(('source-bound-complete54-census', 'actual-receipt-independent-raw-full-state-stream', 'changed-actual-method-old-unknown-retained-no-replay', 'compact-pair-reduction'))),
            runner_factory=partial(SegmentedRunner, operation), record_codecs=output_codecs(),
            scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in config.operands})),
                scientific_unit_ids=lambda config: (c.UNIT,),
                native_effect_slot_ids=native_effect_slot_ids if operation == 'forecast' else None,
                scientific_root_validator=scientific_root_validator,
            ),
            execution_properties=RecursiveExecutionProperties(
                native_effect=operation == 'forecast', complete_unit_census=operation == 'forecast',
                native_work_preparer=prepare_native_work if operation == 'forecast' else None,
                worker_environment_selector=native_worker_environment if operation == 'forecast' else None,
            ),
            inquiry_hooks=RecursiveInquiryHooks(
                inquiry_work_projector=scientific_work,
            ),
            storage_codecs=SEGMENT_STORAGE_CODECS, additional_input_schema_ids=(DiagnosticResult.SCHEMA,),
        ))
    return tuple(registrations)

def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
    records = {record for operation in OPERATIONS for _, record in (*operation_inputs(operation), *operation_outputs(operation))}
    records.update((SegmentedOperationConfig, ObstructionAssessment, c.RefinedSource, c.NumericalPolicy, c.NumericalSelection,
        sr.SegmentedQualificationRoster, dr.UnknownDiagnosticWork, NumericalProducingProvenance,
        sc.SegmentedMethodProtocol, SourceRootPreparation, SourceRootAssessment))
    return {record.SCHEMA: record for record in records}



from .runner import SegmentedRunner as SegmentedRunner  # noqa: E402
