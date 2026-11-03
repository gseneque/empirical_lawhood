# SPDX-License-Identifier: MPL-2.0
"""Local ordinary graph operations for complete source20 numerical consumers.

Shared preparation owns manifests and authenticated port construction. These
workers independently assess the scientific operands received through existing
IPC ports. They neither acquire native work nor admit a model. A completed
negative/unevaluable procedure is a valid ordinary output.
"""

from empirical_lawhood.runtime.recursive_provider import RecursiveOperationDeclaration,RecursiveScientificHooks

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.recursive_authoring import RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import contracts
from . import durable_roster
from . import forecast_state_census as census
from . import forecast_state_control as state
from . import forecast_state_orchestration as orchestration
from . import forecast_step_control as step
from . import lossless_evidence_stream as stream
from . import segmented_contracts
from . import segmented_evidence
from . import segmented_qualification as qualification

NAMESPACE = "battery-forecast-state"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
ACCESS = OutcomeAccess.DEVELOPMENT_VISIBLE
VISIBILITY = VisibilityCeiling.DEVELOPMENT_ONLY


def input_types(operation):
    common = (("control", state.ForecastStateControl), ("selected-roster", durable_roster.FrozenForecastRoster))
    if operation == "pair":
        return tuple(sorted((*common, *((side + "-" + name, record)
            for side in ("left", "right") for name, record in (
                ("evidence", segmented_evidence.SegmentedNativeEvidence),
                ("assignment", step.ForecastStepEvidence),
                ("summary", qualification.SegmentedTraceSummary),
                ("segments", stream.LosslessEvidenceLine))))))
    if operation == "census":
        return tuple(sorted((*common, ("receiver", qualification.SegmentedFidelityQualification),
            *(("pair." + f"{index:03d}", state.ForecastStateStream) for index in range(96)))))
    raise ValueError("forecast state operation must be pair or complete census")


def media_for(name):
    return "application/x-ndjson" if name.endswith("-segments") else "application/json"


@dataclass(frozen=True, slots=True)
class ForecastStateOperationConfig(CanonicalRecord):
    """Task transport is explicit; original scientific identities stay distinct."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/battery-segmented/forecast-state-operation-config"
    config_id: str
    operation: str
    control: ObjectIdentity
    selected_roster: ObjectIdentity
    configurations: tuple[ObjectIdentity, ...]
    input_artifacts: tuple[tuple[str, str], ...]

    def __post_init__(self):
        validate_stable_id(self.config_id)
        for identity, schema in ((self.control, state.ForecastStateControl.SCHEMA),
                (self.selected_roster, durable_roster.FrozenForecastRoster.SCHEMA)):
            if type(identity) is not ObjectIdentity or identity.object_schema != schema:
                raise ValueError("forecast state operation substitutes selected scientific controls")
            identity.__post_init__()
        expected = tuple(name for name, _ in input_types(self.operation))
        if (type(self.input_artifacts) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.input_artifacts)
                or tuple(row[0] for row in self.input_artifacts) != expected
                or len({row[1] for row in self.input_artifacts}) != len(expected)):
            raise ValueError("forecast state operation changes its complete named input transport census")
        for name, artifact in self.input_artifacts:
            validate_stable_id(name)
            validate_stable_id(artifact)
        if (type(self.configurations) is not tuple or len(self.configurations) != (2 if self.operation == "pair" else 0)
                or any(type(row) is not ObjectIdentity or row.object_schema != segmented_contracts.SegmentedNativeConfig.SCHEMA
                    for row in self.configurations)
                or len(set(self.configurations)) != len(self.configurations)):
            raise ValueError("forecast state operation changes its distinct original configuration census")
        for row in self.configurations:
            row.__post_init__()

    @property
    def scientific_operands(self):
        return (self.control, self.selected_roster, *self.configurations)


def operation_declaration(operation):
    """Local cold projection; the caller still owns the actual temporary port."""
    from functools import partial
    from .controlled_operation_bindings import LOSSLESS_STORAGE_CODECS
    output = state.ForecastStateStream if operation == 'pair' else census.ForecastStateCensus
    output_name = 'assessment' if operation == 'pair' else 'census'
    ports = input_types(operation) if operation == 'pair' else (('control', state.ForecastStateControl), ('pair', state.ForecastStateStream), ('receiver', qualification.SegmentedFidelityQualification), ('selected-roster', durable_roster.FrozenForecastRoster))
    codecs = {record.SCHEMA: record for _, record in input_types(operation)}
    codecs.update({ForecastStateOperationConfig.SCHEMA: ForecastStateOperationConfig, output.SCHEMA: output})
    runner = partial(ForecastStateRunner, operation)
    return RecursiveOperationDeclaration(
        capability_key=NAMESPACE + '.' + operation, capability_version='1.0.0',
        implementation_id='complete-original-state-derivative-consumer-v1.' + operation, kind=CapabilityKind.ANALYSIS,
        config_record_type=ForecastStateOperationConfig, stage=ScientificStage.QUALIFY,
        input_ports=tuple((RecursivePortContract(name, record.SCHEMA, media_for(name), None, minimum_count=96 if name == 'pair' else 1, maximum_count=96 if name == 'pair' else 1) for name, record in ports)),
        outputs=(OutputTemplate(output_name, output.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=ACCESS, visibility_ceiling=VISIBILITY,
        resources=BUDGET,
        conformance_check_ids=('actual-original-array-and-assignment-joins', 'complete-adverse-denominator', 'local-pure-consumer-no-model-admission'),
        runner_factory=runner, record_codecs=codecs, storage_codecs=LOSSLESS_STORAGE_CODECS,
        scientific_hooks=RecursiveScientificHooks(
            scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in config.scientific_operands})),
            scientific_unit_ids=lambda config: (contracts.UNIT,),
        ),
    )


def operation_manifest(operation):
    return operation_declaration(operation).manifest()


def operation_registration(operation):
    return operation_declaration(operation).registration()


def graph_fragment(config, *, node_id, references, dependencies=(), run_plan_id=None):
    """Connect the ordinary consumer to existing producers or retained outputs.

    ``dependencies`` contains named ``(producer_node_id, output_id)`` pairs.
    Remaining references are exact authenticated external ObjectIdentities;
    transport aliases come from the configuration, not scientific record IDs.
    The caller retains source/campaign/lineage ownership and composes this
    fragment into the existing compiler. No public registration is installed.
    """
    config.__post_init__()
    dependency_map = dict(dependencies)
    if len(dependency_map) != len(dependencies) or set(dependency_map) & set(references):
        raise ValueError("forecast consumer repeats an input source")
    expected = dict(input_types(config.operation))
    if set(dependency_map) | set(references) != set(expected):
        raise ValueError("forecast consumer graph omits or invents an input")
    registered = operation_registration(config.operation)
    operation = RecursiveOperationSpec.from_config(node_id=node_id, selection=registered.selection,
        config_id=config.config_id, config=config, obligation_ids=("obligation." + node_id + ".complete-original-consumer",),
        resource_budget=BUDGET, maximum_attempts=1)
    artifacts = dict(config.input_artifacts)
    external, links = [], []
    for name, record in input_types(config.operation):
        role = "SOURCE" if name in {"control", "selected-roster"} else "OUTCOME"
        if name in dependency_map:
            producer, output = dependency_map[name]
            if run_plan_id is None:
                raise ValueError("forecast dependent inputs require the selected compiler run identity")
            validate_stable_id(run_plan_id)
            if artifacts[name] != "artifact." + run_plan_id + "." + producer + "." + output:
                raise ValueError("forecast dependent input substitutes compiler-owned output transport")
            links.append(RecursiveInputLink("edge." + node_id + "." + name, node_id, name,
                producer_node_id=producer, producer_output_id=output, scientific_role=role))
        else:
            identity = references[name]
            if type(identity) is not ObjectIdentity or identity.object_schema != record.SCHEMA:
                raise ValueError("forecast consumer external reference changes its declared type")
            identifier = "external." + node_id + "." + name
            external.append(RecursiveExternalInput(identifier, artifacts[name], record.SCHEMA, media_for(name),
                None, ACCESS, VISIBILITY, identity.object_fingerprint, role))
            links.append(RecursiveInputLink("edge." + node_id + "." + name, node_id, name,
                external_input_id=identifier, scientific_role=role))
    return operation, tuple(external), tuple(links)


class ForecastStateRunner:
    """Independent numerical meanings over ordinary authenticated worker ports."""

    def __init__(self, operation, *, temporary_file):
        self.operation, self.temporary_file = operation, temporary_file
        self.manifest = operation_manifest(operation)

    def execute(self, context):
        try:
            return self._execute(context)
        finally:
            for port in context.input_ports:
                port.close()

    def _execute(self, context):
        configs = tuple(port for port in context.input_ports if port.artifact_id == context.config.artifact_id)
        if len(configs) != 1 or configs[0].payload_schema != ForecastStateOperationConfig.SCHEMA:
            raise ValueError("forecast consumer requires its exact immutable operation configuration")
        config = decode_canonical_bytes(configs[0].read(), ForecastStateOperationConfig, maximum_bytes=None)
        if (config.operation != self.operation or config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
                or context.permissions != self.manifest.permissions or context.resource_budget != BUDGET
                or context.outcome_access is not ACCESS):
            raise ValueError("forecast consumer substitutes task/config/access/resource ownership")
        name = "assessment" if self.operation == "pair" else "census"
        output_type = state.ForecastStateStream if self.operation == "pair" else census.ForecastStateCensus
        expected_output = context.task_id + "." + name
        if (len(context.output_ports) != 1 or context.output_ports[0].output_id != expected_output
                or context.output_ports[0].payload_schema != output_type.SCHEMA
                or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON
                or context.output_ports[0].media_type != "application/json"):
            raise ValueError("forecast consumer changes its complete scientific output contract")
        stock = {port.artifact_id: port for port in context.input_ports}
        if len(stock) != len(context.input_ports) or set(stock) != {context.config.artifact_id, *(artifact for _, artifact in config.input_artifacts)}:
            raise ValueError("forecast consumer changes its complete authenticated port census")
        ports = {name: stock[artifact] for name, artifact in config.input_artifacts}
        types = dict(input_types(self.operation))
        for name, port in ports.items():
            if (port.payload_schema != types[name].SCHEMA or port.media_type != media_for(name)
                    or port.outcome_access is not ACCESS or port.visibility_ceiling is not VISIBILITY):
                raise ValueError("forecast consumer changes selected typed port/access")

        def decode(name):
            raw = ports[name].read()
            if len(raw) != ports[name].size_bytes:
                raise ValueError("forecast consumer input changes its complete byte census")
            return decode_canonical_bytes(raw, types[name], maximum_bytes=None)

        control, selected = decode("control"), decode("selected-roster")
        if control.identity != config.control or step.identity(selected, "roster_id") != config.selected_roster:
            raise ValueError("forecast consumer substitutes selected source/control records")
        if self.operation == "pair":
            observed = tuple(orchestration.ForecastObservation(decode(side + "-evidence"),
                decode(side + "-assignment"), decode(side + "-summary")) for side in ("left", "right"))
            if tuple(row.configuration for row in observed) != config.configurations:
                raise ValueError("forecast consumer substitutes original native configurations")
            result = orchestration.assess_pair(control, selected, *observed,
                ports["left-segments"], ports["right-segments"], temporary_file=self.temporary_file)
        else:
            receiver = decode("receiver")
            # Decode/reduce one complete product at a time. Full per-pair arrays
            # and interval products do not accumulate across all96 inputs.
            result = orchestration.join_complete_pairs(control, selected, receiver,
                (decode("pair." + f"{index:03d}") for index in range(96)))
        return RunnerResult((TaskOutputPayload(expected_output, result.canonical_bytes()),),
            (ReceiptCheck("complete-original-state-and-adverse-census", True, ()),))
