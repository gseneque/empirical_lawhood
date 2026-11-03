# SPDX-License-Identifier: MPL-2.0
"""Cold ordinary operations for a complete prospective observation episode."""

from functools import partial
from empirical_lawhood.runtime.recursive_provider import (RecursiveOperationDeclaration,RecursiveExecutionProperties,RecursiveInquiryHooks,RecursiveScientificHooks)

from empirical_lawhood.adapters.methods.battery_segmented_inquiry.storage_codecs import OBSERVATION_STORAGE_CODECS

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.battery_refined_inquiry import contracts as c, durable_roster as dr
from empirical_lawhood.adapters.methods.battery_refined_inquiry import preparation_contracts as pc, segmented_contracts as sc
from empirical_lawhood.adapters.methods.battery_refined_inquiry import segmented_observation_contracts as oc
from empirical_lawhood.adapters.methods.battery_refined_inquiry.operation_bindings import history_type
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity import FullStateControlProtocol
from empirical_lawhood.adapters.methods.battery_refined_inquiry.segmented_fidelity_stream import FullStateStreamAssessment
from empirical_lawhood.adapters.methods.battery_refined_inquiry.source_derived_preparation import SourceRootPreparation, SourceRootAssessment
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.evidence_stream import SegmentStreamChunk, MEDIA as STREAM_MEDIA
from empirical_lawhood.adapters.methods.battery_segmented_inquiry.operation_bindings import forecast_primitive
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ExternalRootContract, is_canonical_json_media_type
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
from .contracts import ObservedWindow, ObservationMethodAssessment, ObservationReadout, identity

NAMESPACE = "battery-observation-inquiry"
QUESTION = "Do three genuinely changed source-derived initial-window methods supply authentic preparation, numerical discrepancy and measured resource operands for the next charging inquiry?"
OPERATIONS = ("assess", "observe", "pair", "summarize")
BUDGET = ResourceBudget(1, None, 0, None, None, None)


class RawSource:
    SCHEMA = oc.RAW_SOURCE_SCHEMA


def node_id(operation, index=None):
    return NAMESPACE + "." + operation + ("." + f"{index:03d}" if index is not None else "")


@dataclass(frozen=True, slots=True)
class ObservationOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-observation-inquiry/operation-config"
    config_id: str
    operation: str
    index: int | None
    observation: oc.PreparationObservationProtocol
    protocols: tuple[pc.PreparationProtocol, ...]
    declarations: tuple[oc.ObservationEntryDeclaration, ...]
    storage: ExternalRootContract
    provenance: NumericalProducingProvenance
    control: FullStateControlProtocol
    history_artifact_id: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        validate_stable_id(self.history_artifact_id)
        if (self.operation not in OPERATIONS or self.config_id != "config." + node_id(self.operation, self.index)
                or (self.operation == "summarize" and self.index is not None)
                or (self.operation != "summarize" and (type(self.index) is not int
                    or not 0 <= self.index < (2 if self.operation == "pair" else 3)))):
            raise ValueError("observation operation changes its complete task/ordinal identity")
        if (type(self.observation) is not oc.PreparationObservationProtocol or type(self.storage) is not ExternalRootContract
                or type(self.provenance) is not NumericalProducingProvenance or type(self.control) is not FullStateControlProtocol
                or type(self.protocols) is not tuple or len(self.protocols) != 3
                or type(self.declarations) is not tuple or len(self.declarations) != 3):
            raise ValueError("observation operation omits original typed scientific/environment/storage operands")
        for row in (self.observation, self.storage, self.provenance, self.control):
            row.__post_init__()
        for i, (config, protocol, declaration) in enumerate(zip(self.observation.configurations, self.protocols, self.declarations, strict=True)):
            if (type(protocol) is not pc.PreparationProtocol or type(declaration) is not oc.ObservationEntryDeclaration
                    or protocol.configuration != identity(config, "config_id") or protocol.source != c.identity(config.source)
                    or protocol.producing_provenance != self.provenance.identity
                    or declaration.observation != identity(self.observation, "observation_id")
                    or declaration.configured_method_index != i or declaration.producing_provenance != self.provenance
                    or declaration.resources.declared_storage_root != identity(self.storage, "storage_root_id")):
                raise ValueError("observation operation changes actual method/protocol/provenance/root joins")
            protocol.__post_init__()
            declaration.__post_init__()
        if (len({row.protocol_id for row in self.protocols}) != 3 or len({row.declaration_id for row in self.declarations}) != 3
                or any((row.resources, row.abi_import_report) != (self.declarations[0].resources, self.declarations[0].abi_import_report)
                       for row in self.declarations)):
            raise ValueError("observation operation changes declared complete initial resource/ABI census")

    @property
    def source(self):
        return self.observation.original_selection.source

    @property
    def operands(self):
        rows = (identity(self.observation, "observation_id"), c.identity(self.source),
            identity(self.observation.original_selection, "roster_id"), identity(self.observation.uncertain_work, "record_id"),
            self.source.diagnostic, self.provenance.identity, identity(self.storage, "storage_root_id"),
            identity(self.control, "control_id"), *(identity(row, "protocol_id") for row in self.protocols),
            *(identity(row, "declaration_id") for row in self.declarations),
            *(identity(row, "config_id") for row in self.observation.configurations),
            *(identity(row.method, "method_id") for row in self.observation.configurations),
            identity(self.observation.configurations[0].preparation, "preparation_id"),
            identity(self.observation.configurations[0].preparation_assessment, "assessment_id"),
            identity(self.declarations[0].resources, "snapshot_id"), self.declarations[0].resources.evidence,
            self.declarations[0].abi_import_report)
        return tuple(sorted(set(rows), key=lambda row: row.object_id))


def require_selected_storage(config, selected_storage_contract):
    """Outer composition must pass its actual artifact_writer.root.contract.

    Path-free workers cannot independently discover the custody root. This
    explicit join is an entry prerequisite, not a new effect/permission issuer.
    """
    config.__post_init__()
    if type(selected_storage_contract) is not ExternalRootContract or selected_storage_contract != config.storage:
        raise ValueError("observation operational custody changes the actually selected measured storage root")


def primitive(config, index):
    selected = config.observation.configurations[index]
    return canonical_json_bytes({"source_method": sha256(forecast_primitive(selected)).hexdigest(),
        "minimum_observation_clock_s": config.observation.minimum_observation_clock_s,
        "stopping_semantics": config.observation.stopping_semantics})


def common_inputs(config):
    return (("history", history_type(config.source.diagnostic)), ("observation", oc.PreparationObservationProtocol),
        ("provenance", NumericalProducingProvenance), ("storage", ExternalRootContract), ("source", c.RefinedSource))


def operation_inputs(operation):
    if operation == "observe":
        return (("native-config", sc.SegmentedNativeConfig), ("protocol", pc.PreparationProtocol),
            ("entry", oc.ObservationEntryDeclaration), ("abi-import-report", RawSource), ("resource-source", RawSource),
            ("resources", oc.ObservationResourceSnapshot), ("original-roster", dr.FrozenForecastRoster),
            ("uncertain-work", dr.UnknownDiagnosticWork), ("method", sc.SegmentedMethodProtocol),
            ("preparation", SourceRootPreparation), ("source-assessment", SourceRootAssessment))
    if operation == "assess":
        return (("window", ObservedWindow), ("segments", SegmentStreamChunk))
    if operation == "pair":
        return (("left-window", ObservedWindow), ("left-segments", SegmentStreamChunk),
            ("right-window", ObservedWindow), ("right-segments", SegmentStreamChunk), ("control", FullStateControlProtocol))
    return tuple(("method-" + str(i), ObservationMethodAssessment) for i in range(3)) + tuple(
        ("pair-" + str(i), FullStateStreamAssessment) for i in range(2))


def operation_outputs(operation):
    if operation == "observe":
        return (("segments", SegmentStreamChunk), ("window", ObservedWindow))
    if operation == "assess":
        return (("assessment", ObservationMethodAssessment),)
    if operation == "pair":
        return (("comparison", FullStateStreamAssessment),)
    return (("readout", ObservationReadout),)


def media_for(name):
    return STREAM_MEDIA if name.endswith("segments") else "text/plain" if name in {"abi-import-report", "resource-source"} else "application/json"


def stage(operation):
    return ScientificStage.ACQUIRE if operation == "observe" else ScientificStage.QUALIFY


def development_root(config, *, study_id):
    scope = c.scope(config.source)
    claim = ClaimSpec("claim." + NAMESPACE, scope.world_id, "population.battery-thermal-inquiry.exposed-lgm50", QUESTION,
        "One declared original condition; complete60/30/15 windows and both60-30/30-15 pairs; zero fresh physical units.",
        c.UNIT, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
        "Preparation, discrepancy and observed resource operands only; no full forecast, supplier or physical qualification.",
        ("assumption.exposed-lgm50-model-family",), numerical_view_ids=("view.battery-observation-inquiry.initial-window",))
    return DevelopmentStudySpec(study_id, QUESTION, ObjectIdentity.from_record(scope.system_id, config.source),
        scope.world_id, WorldKind.NUMERICAL_SIMULATOR, (c.UNIT,), ("view.battery-observation-inquiry.initial-window",), (claim,), config.operands)


def scientific_root_validator(config, context):
    if (context.root != development_root(config, study_id=context.root.study_id)
            or context.node_id != node_id(config.operation, config.index) or context.stage is not stage(config.operation)
            or context.unit_ids != (c.UNIT,) or context.selected_unit_ids != (c.UNIT,)
            or context.complete_unit_census != (config.operation == "observe")):
        raise ValueError("observation operation changes scientific scope/stage/units")
    from .recursive_translation import validate_graph
    validate_graph(context, config)


def native_effect_slot_ids(config):
    return ("native.battery-initial-window." + sha256(primitive(config, config.index)).hexdigest(),) if config.operation == "observe" else ()


def operation_declarations():
    from .recursive_translation import scientific_work
    from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import ObstructionAssessment
    common = (('history', ObstructionAssessment), ('observation', oc.PreparationObservationProtocol), ('provenance', NumericalProducingProvenance), ('storage', ExternalRootContract), ('source', c.RefinedSource))
    return tuple((RecursiveOperationDeclaration(
        capability_key=NAMESPACE + '.' + operation, capability_version='1.0.0',
        implementation_id='declared-initial-window-original-custody-v1.' + operation,
        kind=CapabilityKind.SIMULATOR if operation == 'observe' else CapabilityKind.ANALYSIS,
        config_record_type=ObservationOperationConfig, stage=stage(operation),
        input_ports=tuple((RecursivePortContract(name, record.SCHEMA, media_for(name), None) for name, record in sorted((*common, *operation_inputs(operation))))),
        outputs=tuple((OutputTemplate(name, record.SCHEMA, ArtifactProfile.JSONL_CHUNKS if name == 'segments' else ArtifactProfile.CANONICAL_JSON, media_for(name), '.jsonl' if name == 'segments' else '.json') for name, record in operation_outputs(operation))),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=('complete-three-method-two-pair-outcome-denominator', 'distinct-preparation-window-no-full-supplier', 'original-raw-state-receipt-independent-stream'),
        runner_factory=partial(ObservationRunner, operation), record_codecs=output_codecs(),
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda config: tuple(sorted({operand.object_fingerprint for operand in config.operands})),
            scientific_unit_ids=lambda config: (c.UNIT,),
            native_effect_slot_ids=native_effect_slot_ids if operation == 'observe' else None,
            scientific_root_validator=scientific_root_validator,
        ),
        execution_properties=RecursiveExecutionProperties(
            native_effect=operation == 'observe', complete_unit_census=operation == 'observe',
        ),
        inquiry_hooks=RecursiveInquiryHooks(
            inquiry_work_projector=scientific_work,
        ),
        storage_codecs=OBSERVATION_STORAGE_CODECS,
        input_record_types=tuple(sorted({record for name, record in (*common, *operation_inputs(operation))
            if is_canonical_json_media_type(media_for(name)) and issubclass(record, CanonicalRecord)},
            key=lambda record: (record.SCHEMA, record.VERSION))),
    ) for operation in OPERATIONS))

def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {record.SCHEMA: record for operation in OPERATIONS for _, record in operation_outputs(operation)}


from .runner import ObservationRunner as ObservationRunner  # noqa: E402
