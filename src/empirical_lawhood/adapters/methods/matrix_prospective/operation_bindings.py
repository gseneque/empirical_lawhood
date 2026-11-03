# SPDX-License-Identifier: MPL-2.0
"""Installed causal example on existing compiler, worker, custody and scheduler."""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties, RecursiveInquiryHooks,
)

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS

from dataclasses import dataclass
from contextlib import ExitStack, contextmanager
from decimal import Decimal
from hashlib import sha256
import resource
import time
from typing import ClassVar

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixPurposeSeed
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_inquiry import InquiryCost
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster, invoke_native_subwork
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from . import science
from .records import (
    BRANCHES, MatrixCausalForecast, MatrixCausalOrigin, MatrixIndependentAssessment,
    MatrixNativeFutures, MatrixProspectiveSource, MatrixPublicProtocol, identity,
)

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT


NAMESPACE = "matrix-prospective"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
MEDIA = "application/json"
WORLD = "world.matrix-prospective.exposed"
QUESTION = "Does a prefix-only committed inertial description pass its declared native response precision?"
PHASES = (
    ("origin", (("provenance", NumericalProducingProvenance), ("source", MatrixProspectiveSource)),
     MatrixCausalOrigin, ScientificStage.ACQUIRE),
    ("forecast", (("origin", MatrixCausalOrigin), ("origin-arrays", None)),
     MatrixCausalForecast, ScientificStage.FREEZE),
    ("futures", (("forecast", MatrixCausalForecast),
        ("future-1-stream", MatrixPurposeSeed), ("future-2-stream", MatrixPurposeSeed), ("origin", MatrixCausalOrigin),
        ("origin-arrays", None), ("provenance", NumericalProducingProvenance), ("source", MatrixProspectiveSource)),
     MatrixNativeFutures, ScientificStage.ACQUIRE),
    ("assess", (("forecast", MatrixCausalForecast), ("forecast-arrays", None),
        ("futures", MatrixNativeFutures), ("futures-arrays", None), ("origin", MatrixCausalOrigin),
        ("origin-arrays", None), ("source", MatrixProspectiveSource)),
     MatrixIndependentAssessment, ScientificStage.FALSIFY),
)


@dataclass(frozen=True, slots=True)
class MatrixOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-prospective/operation-config"
    config_id: str
    operation: str
    protocol: MatrixPublicProtocol
    native_source: ObjectIdentity | None
    provenance: ObjectIdentity | None

    def __post_init__(self):
        validate_stable_id(self.config_id)
        if self.operation not in {p[0] for p in PHASES} or self.config_id != f"config.{NAMESPACE}.{self.operation}":
            raise ValueError("matrix selected operation/configuration substitution")
        if self.operation == "forecast":
            if self.native_source is not None or self.provenance is not None:
                raise ValueError("matrix predictor cannot receive native source or producing future operands")
        elif self.native_source is None or self.native_source.object_schema != MatrixProspectiveSource.SCHEMA:
            raise ValueError("matrix selected native/assessment operation requires its exact source")
        if self.operation in {"origin", "futures"}:
            if self.provenance is None or self.provenance.object_schema != NumericalProducingProvenance.SCHEMA:
                raise ValueError("matrix native entry requires actual producing code/lock provenance")
        elif self.provenance is not None:
            raise ValueError("matrix pure operation has no native producing input")


def scientific_operand_sha256s(config):
    return tuple(sorted({config.protocol.fingerprint(), *(x.object_fingerprint
        for x in (config.native_source, config.provenance) if x is not None)}))


def scientific_unit_ids(config):
    return (config.protocol.root.independent_group_id,)


def native_effect_slot_ids(config):
    prefix = config.protocol.root.root_id
    return ((prefix + ".prefix",) if config.operation == "origin" else
            tuple(prefix + "." + branch for branch in BRANCHES))


def development_root(protocol, *, study_id, scientific_operands=()):
    unit = protocol.root.independent_group_id
    claim = ClaimSpec("claim.matrix-prospective.exposed", WORLD, "population.matrix-prospective.exposed",
        QUESTION, "One exposed root with two nested native branches and an independent numerical assay.",
        unit, None, EvidenceCeiling.NON_PROMOTABLE, OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "No fresh confirmation, lifetime calibration, factor utility or preparation benefit.",
        ("assumption.matrix-prospective.exposed",), numerical_view_ids=(protocol.view.view_id,))
    operands = tuple(sorted(set((identity(protocol), *scientific_operands)), key=lambda item: item.object_id))
    return DevelopmentStudySpec(study_id, QUESTION, identity(protocol), WORLD, WorldKind.NUMERICAL_SIMULATOR,
        (unit,), (protocol.view.view_id,), (claim,), operands)


def scientific_root_validator(config, context):
    configs = tuple(i.record for i in context.config_inputs)
    if (len(configs) != len(PHASES) or any(type(c) is not MatrixOperationConfig for c in configs)
            or {c.operation for c in configs} != {p[0] for p in PHASES}
            or any(c.protocol != config.protocol for c in configs)):
        raise ValueError("matrix route needs its complete installed origin/forecast/future/assess census")
    sources = {c.native_source for c in configs if c.native_source is not None}
    provenances = {c.provenance for c in configs if c.provenance is not None}
    if len(sources) != 1 or len(provenances) != 1:
        raise ValueError("matrix native and assessment operations require the same exact source/provenance")
    if type(context.root) is not DevelopmentStudySpec or context.root != development_root(
            config.protocol, study_id=context.root.study_id, scientific_operands=(*sources, *provenances)):
        raise ValueError("matrix operation changes exact root, model, coordinate, role or exposure")
    phase = next(p for p in PHASES if p[0] == config.operation)
    native = config.operation in {"origin", "futures"}
    if (context.node_id != f"{NAMESPACE}.{config.operation}" or context.stage is not phase[3]
            or context.unit_ids != scientific_unit_ids(config)
            or context.selected_unit_ids != scientific_unit_ids(config)
            or context.complete_unit_census != native
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("matrix stage, full root denominator or access boundary differs")
    incoming = tuple(link for link in context.links if link.consumer_node_id == context.node_id)
    if {link.consumer_input_id for link in incoming} != {name for name, _ in phase[1]} or len(incoming) != len(phase[1]):
        raise ValueError("matrix operation changes its exact predictor/native/assessor input census")
    external = {"source", "provenance", *(b + "-stream" for b in BRANCHES)}
    for link in incoming:
        if link.consumer_input_id in external:
            if link.external_input_id is None or link.scientific_role != "SOURCE":
                raise ValueError("matrix operation changes its exact external source role")
        else:
            owner = link.consumer_input_id.removesuffix("-arrays")
            output = "arrays" if link.consumer_input_id.endswith("-arrays") else "product"
            expected_role = "MODEL" if owner == "forecast" else "OUTCOME" if owner == "futures" else "HISTORY"
            if (link.producer_node_id != f"{NAMESPACE}.{owner}" or link.producer_output_id != output
                    or link.external_input_id is not None or link.scientific_role != expected_role):
                raise ValueError("matrix causal commitment/array/role dependency differs")


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def output_codecs():
    return {t.SCHEMA: t for t in (MatrixOperationConfig, MatrixProspectiveSource, NumericalProducingProvenance, MatrixPurposeSeed,
        MatrixCausalOrigin, MatrixCausalForecast, MatrixNativeFutures, MatrixIndependentAssessment)}


def _decode_inputs(context, role):
    phase = next(p for p in PHASES if p[0] == role)
    expected = {MatrixOperationConfig.SCHEMA: MatrixOperationConfig,
                **{t.SCHEMA: t for _, t in phase[1] if t}}
    records, arrays, streams = {}, {}, []
    for port in context.input_ports:
        if port.payload_schema == MATRIX_ARRAY_SCHEMA:
            arrays[port.artifact_id] = port
        elif port.payload_schema == MatrixPurposeSeed.SCHEMA and port.payload_schema in expected:
            streams.append(decode_canonical_bytes(port.read(), MatrixPurposeSeed, maximum_bytes=None))
        elif port.payload_schema in expected and port.payload_schema not in records:
            records[port.payload_schema] = decode_canonical_bytes(port.read(), expected[port.payload_schema], maximum_bytes=None)
        else:
            raise ValueError("matrix worker received an undeclared or duplicate operand")
    if streams:
        records[MatrixPurposeSeed.SCHEMA] = tuple(sorted(streams, key=lambda stream: stream.purpose_id))
    if (set(records) != set(expected) or len(arrays) != sum(t is None for _, t in phase[1])
            or len(streams) != sum(t is MatrixPurposeSeed for _, t in phase[1])):
        raise ValueError("matrix worker omits its complete typed/raw input census")
    config = records[MatrixOperationConfig.SCHEMA]
    selected = next(m for m in operation_manifests() if m.capability_key == f"{NAMESPACE}.{role}")
    if (config.operation != role or config.fingerprint() != context.config.content_sha256
            or context.task_id != f"{NAMESPACE}.{role}" or context.resource_budget != BUDGET
            or context.permissions != selected.permissions or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
        raise ValueError("matrix worker changes exact selected configuration/resources/access")
    if MatrixProspectiveSource.SCHEMA in records:
        source = records[MatrixProspectiveSource.SCHEMA]
        if source.protocol != config.protocol or identity(source) != config.native_source:
            raise ValueError("matrix worker source/model/coordinate identity substitution")
        if streams and records[MatrixPurposeSeed.SCHEMA] != tuple(science.branch_contract(source, b).stream for b in BRANCHES):
            raise ValueError("matrix future stream ports differ from the exact selected source allocation")
    if NumericalProducingProvenance.SCHEMA in records and records[NumericalProducingProvenance.SCHEMA].identity != config.provenance:
        raise ValueError("matrix worker changes actual producing provenance")
    return config, records, arrays


@contextmanager
def _consume_array(port_map, saved, expected_producers, protocol):
    """Hold exact complete source verification through the scientific consumer."""
    from empirical_lawhood.adapters.methods.matrix_dataset_readers import bridge_saved_arrays
    from empirical_lawhood.infrastructure.matrix_array_io import validate_matrix_worker_array_input

    protocol.__post_init__()
    port = port_map[saved.array_artifact.artifact_id]
    validate_matrix_worker_array_input(port, manifest=saved, allocation=protocol.allocation,
        expected_producers=tuple(sorted(expected_producers, key=lambda value:value.object_id)))
    dataset = bridge_saved_arrays(saved, port, maximum_chunk_bytes=65536,
        maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES,
        scientific_references=tuple(sorted((identity(protocol),
            ObjectIdentity.from_record(protocol.root.root_id, protocol.root)), key=lambda value:value.object_id)))
    try:
        with dataset.reader.verified_session(block_size_bytes=65536) as reader:
            yield dataset.array_mapping(reader)
    finally:
        dataset.close()


def _outputs(context, product, raw=None):
    by_name = {p.output_id.rsplit(".", 1)[-1]: p for p in context.output_ports}
    expected = {"product"} if raw is None else {"arrays", "product"}
    if set(by_name) != expected or by_name["product"].payload_schema != product.SCHEMA:
        raise ValueError("matrix worker changes its full scientific output census")
    values = [TaskOutputPayload(by_name["product"].output_id, product.canonical_bytes())]
    if raw is not None:
        if (product.arrays.array_artifact.artifact_id != by_name["arrays"].logical_artifact_id
                or sha256(raw).hexdigest() != product.arrays.array_artifact.sha256):
            raise ValueError("matrix manifest differs from exact published raw array")
        values.append(TaskOutputPayload(by_name["arrays"].output_id, raw))
    return RunnerResult(tuple(sorted(values, key=lambda v: v.output_id)),
        (ReceiptCheck("matrix-causal-full-census", True, ()),))


def _future_records(config, records):
    """One original future source/origin/forecast and allocated prefix join."""
    source = records[MatrixProspectiveSource.SCHEMA]
    origin, forecast = records[MatrixCausalOrigin.SCHEMA], records[MatrixCausalForecast.SCHEMA]
    forecast.validate_origin(origin)
    if origin.protocol != config.protocol or origin.source != identity(source):
        raise ValueError("matrix native branch changes its committed initial source")
    prefix = next(stream for stream in source.allocation.streams.roots[0].scientific_seeds if stream.purpose_id == "prefix")
    if origin.prefix_stream != prefix:
        raise ValueError("matrix native branch changes its original allocated prefix stream")
    return source, origin, forecast, records[NumericalProducingProvenance.SCHEMA]


def _validate_prefix(origin, past):
    import numpy as np

    expected = (origin.protocol.prefix_steps + 1, 2, 3, 4, 4)
    if set(past) != {"momenta", "positions"}:
        raise ValueError("matrix native prefix changes complete original state census")
    for name in ("momenta", "positions"):
        value = past[name]
        if value.shape != expected or value.dtype.str != "<c16" or not np.isfinite(value).all():
            raise ValueError("matrix native prefix changes complete original shape/precision/finite state")


def _future_definitions(context, config, source, origin, forecast, provenance, parent_contact):
    return tuple(NativeSubworkDefinition("subwork." + source.protocol.root.root_id + "." + branch,
        "matrix-native-branch." + branch, parent_contact, identity(config),
        tuple(sorted((identity(source), identity(origin), identity(forecast), provenance.identity), key=lambda value: value.object_id)),
        provenance.code_sources_sha256, provenance.dependency_lock_sha256,
        tuple(sorted(port.materialization_id for port in context.input_ports)),
        (ObjectIdentity.from_record("stream." + source.protocol.root.root_id + "." + branch,
            science.branch_contract(source, branch).stream),),
        (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),))
        for branch in BRANCHES)


def prepare_native_work(*, runner, context, expected_parent):
    """Original top-level prefix or original two-child future, without RNG."""
    from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

    if (type(runner) is not MatrixRunner or runner.role != "origin") and (
            type(runner) is not MatrixFutureRunner or runner.role != "futures"):
        raise ValueError("matrix preparation requires its installed original native phase")
    config, records, ports = _decode_inputs(context, runner.role)
    if runner.role == "origin":
        return PreparedNativeWork(expected_parent, scientific_unit_ids(config), native_effect_slot_ids(config))
    source, origin, forecast, provenance = _future_records(config, records)
    with _consume_array(ports, origin.arrays, (origin.source, identity(origin.protocol)), origin.protocol) as past:
        _validate_prefix(origin, past)
    definitions = _future_definitions(context, config, source, origin, forecast, provenance, expected_parent)
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, tuple(row.identity for row in definitions))
    return PreparedNativeWork(expected_parent, scientific_unit_ids(config), native_effect_slot_ids(config), definitions, (roster,))


class MatrixRunner:
    def __init__(self, role):
        self.role = role
        self.manifest = next(m for m in operation_manifests() if m.capability_key == f"{NAMESPACE}.{role}")

    def execute(self, context):
        try:
            with ExitStack() as stack:
                config, records, ports = _decode_inputs(context, self.role)
                output = next((p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ), None)
                artifact_id = None if output is None else output.logical_artifact_id
                if self.role == "origin":
                    source = records[MatrixProspectiveSource.SCHEMA]
                    raw, product = science.origin_record(source, science.prefix(source), artifact_id=artifact_id)
                else:
                    origin = records[MatrixCausalOrigin.SCHEMA]
                    if origin.protocol != config.protocol:
                        raise ValueError("matrix worker substitutes the committed origin protocol")
                    past = stack.enter_context(_consume_array(ports, origin.arrays, (origin.source, identity(origin.protocol)), origin.protocol))
                    if self.role == "forecast":
                        raw, product = science.forecast(origin, past, artifact_id=artifact_id)
                    elif self.role == "assess":
                        forecast = records[MatrixCausalForecast.SCHEMA]
                        native = records[MatrixNativeFutures.SCHEMA]
                        predicted = stack.enter_context(_consume_array(ports, forecast.arrays,
                            (identity(origin), identity(origin.protocol.calibration_scope), identity(origin.protocol.preparation_scope)), origin.protocol))
                        future = stack.enter_context(_consume_array(ports, native.arrays,
                            (identity(origin), identity(forecast), identity(records[MatrixProspectiveSource.SCHEMA])), origin.protocol))
                        raw, product = None, science.assess(records[MatrixProspectiveSource.SCHEMA], origin,
                            forecast, native, past, predicted, future)
                    else:
                        raise ValueError("matrix futures require the live native progress port")
                return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()


class MatrixFutureRunner(MatrixRunner):
    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            with ExitStack() as stack:
                config, records, ports = _decode_inputs(context, "futures")
                source, origin, forecast, provenance = _future_records(config, records)
                past = stack.enter_context(_consume_array(ports, origin.arrays, (origin.source, identity(origin.protocol)), origin.protocol))
                _validate_prefix(origin, past)
                contact = native_subwork.parent_contact
                definitions = _future_definitions(context, config, source, origin, forecast, provenance, contact)
                native_subwork.freeze_roster(NativeSubworkRoster("selected.native-subwork", contact,
                    tuple(d.identity for d in definitions)), definitions=definitions)
                branch_arrays = {}
                for branch, definition in zip(BRANCHES, definitions, strict=True):
                    # A known completion is reusable custody. Never reacquire it if
                    # this creator encounters a retained or uncertain slot.
                    if native_subwork.recover(definition) is not None:
                        raise ValueError("completed matrix branch is retained; use receipt recovery, not native replay")
                    entry = native_subwork.begin(definition)
                    native_subwork.contact(entry)
                    cpu, wall = time.process_time(), time.monotonic()
                    try:
                        values = invoke_native_subwork(native_subwork, entry, science.native_branch,
                            source, origin, past, science.branch_contract(source, branch))
                    except (MemoryError, ArithmeticError, ValueError) as error:
                        native_subwork.complete(entry, operational_status=OperationalStatus.FAILED,
                            cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), None),
                            cost_scope="matrix native branch, nested inside complete task window",
                            unknown_streams=definition.streams, reason_codes=("matrix-native-branch-failure",))
                        raise RuntimeError("matrix native branch returned an unresolved failure") from error
                    raw, _ = science.array_product(values, allocation=config.protocol.allocation,
                        producers=(identity(source), identity(forecast)), artifact_id="array.subwork." + definition.subwork_id,
                        operand_id="operand.subwork." + definition.subwork_id)
                    native_subwork.publish_output(entry, "arrays", (raw,), maximum_bytes=len(raw),
                        maximum_chunk_bytes=len(raw), expected_size_bytes=len(raw),
                        expected_physical_sha256=sha256(raw).hexdigest())
                    native_subwork.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
                        cost=InquiryCost(Decimal(str(time.process_time() - cpu)), Decimal(str(time.monotonic() - wall)), Decimal(len(raw))),
                        cost_scope="matrix native branch, nested inside complete task window", consumed_streams=definition.streams,
                        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
                    branch_arrays[branch] = values
                output = next(p for p in context.output_ports if p.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
                raw, product = science.futures(source, origin, forecast, branch_arrays, artifact_id=output.logical_artifact_id)
                return _outputs(context, product, raw)
        finally:
            for port in context.input_ports:
                port.close()


def _operation_declaration(role, inputs, output, stage):
    return RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + role,
        capability_version="1.0.0",
        implementation_id=f'{NAMESPACE}.exposed-causal-{role}-v1',
        kind=CapabilityKind.SIMULATOR if role in {'origin', 'futures'} else CapabilityKind.ANALYSIS,
        config_record_type=MatrixOperationConfig,
        stage=stage,
        input_ports=tuple((RecursivePortContract(name, t.SCHEMA if t else MATRIX_ARRAY_SCHEMA, MEDIA if t else 'application/x-npz', None if t else MAXIMUM_MATRIX_ARRAY_BYTES) for name, t in inputs)),
        outputs=tuple(sorted((OutputTemplate('product', output.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, '.json'), *(() if role == 'assess' else (OutputTemplate('arrays', MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, 'application/x-npz', '.npz'),))), key=lambda o: o.output_id)),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_DEVELOPMENT))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('complete-selected-census', 'exact-causal-ports', 'independent-potential-assay'))),
        runner_factory=lambda: MatrixFutureRunner(role) if role == "futures" else MatrixRunner(role),
        record_codecs={**output_codecs(), **{kind.SCHEMA: kind for _, kind in inputs if kind is not None}},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=scientific_operand_sha256s, scientific_unit_ids=scientific_unit_ids, native_effect_slot_ids=native_effect_slot_ids if role in {'origin', 'futures'} else None, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE if role == 'forecast' else BarrierKind.NONE, native_effect=role in {'origin', 'futures'}, complete_unit_census=role in {'origin', 'futures'}, native_work_preparer=prepare_native_work if role in {'origin', 'futures'} else None),
        inquiry_hooks=RecursiveInquiryHooks(inquiry_record_identity=identity),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
        storage_codecs=MATRIX_STORAGE_CODECS,
    )


def operation_declarations():
    return tuple(_operation_declaration(*phase) for phase in PHASES)
