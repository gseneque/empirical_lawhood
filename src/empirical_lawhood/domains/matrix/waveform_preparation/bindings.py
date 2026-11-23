# SPDX-License-Identifier: MPL-2.0
"""Registered waveform operations with original parent and numerical-array custody."""

from dataclasses import replace
from functools import lru_cache, partial
from types import MappingProxyType
from hashlib import sha256

from empirical_lawhood.domains.matrix.classical_series.arrays import (
    decode_acquisition,
    encode_acquisition,
    iter_encoded_bytes,
)
from empirical_lawhood.domains.matrix.finite_response_law.original_f import (
    OriginalFiniteResponseLaw,
)
from empirical_lawhood.domains.matrix.matrix_storage_codecs import (
    MATRIX_FRAMED_CODEC,
    MATRIX_FRAMED_ARRAY_SCHEMA,
)
from empirical_lawhood.domains.matrix.preparation_applicability.dynamics import (
    acquire_prefix,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_evaluation import (
    WaveformCohort,
    assess_cohort,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_population import (
    WaveformPrefix,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_trial import (
    WaveformForecast,
    WaveformLowerSeal,
    WaveformMeasurement,
    WaveformPanel,
    WaveformParents,
    acquire_panel,
    acquire_parents,
    assess_panel,
    seal_lower,
    seal_prefix,
)
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import (
    RecursiveExecutionProperties,
    RecursiveOperationDeclaration,
    RecursiveScientificHooks,
)
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import (
    AssessmentDisposition,
    AssessmentPhase,
    RequirementSupplyAssessment,
)
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import (
    canonical_json_document_bytes,
)
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.storage.artifact_stream_primitives import STREAM_CHUNK_BYTES

from . import design
from .records import (
    LOWER_USERS,
    NAMESPACE,
    NATIVE,
    PHASES,
    PREDECESSORS,
    WaveformOperation,
    WaveformProduct,
    WaveformSpecification,
)

PHASE_TYPES = dict(
    zip(
        PHASES,
        (
            WaveformPrefix,
            WaveformForecast,
            WaveformParents,
            WaveformLowerSeal,
            WaveformPanel,
            WaveformMeasurement,
            WaveformCohort,
        ),
        strict=True,
    )
)
FLOAT_FIELDS = frozenset(
    (
        "frame_base64",
        "trace_base64",
        "positions_base64",
        "momenta_base64",
        "transfer_base64",
        "history_positions_base64",
        "history_momenta_base64",
    )
)
CHECK = "waveform.original-predecessors-and-assigned-waveforms"


def units(config):
    return config.unit_ids


def operands(config):
    return tuple(
        sorted(
            (
                config.specification.object_fingerprint,
                config.design.lower.object_fingerprint,
                config.design.exposure.object_fingerprint,
            )
        )
    )


def prepare_root(context):
    selected = tuple(row.record for row in context.config_inputs)
    if not selected or any(type(c) is not WaveformOperation for c in selected):
        raise ValueError(
            "Waveform graph requires its original operation configurations"
        )
    spec = selected[0].design
    configs = design.configurations(spec)
    root = design.scientific_root(spec)
    if (
        root != context.root
        or tuple(sorted(selected, key=lambda c: c.node_id)) != configs
        or design.graph(spec, configs, root)
        != (
            context.requirements,
            context.connections,
            context.links,
            context.external_inputs,
        )
    ):
        raise ValueError(
            "Waveform graph omits an assigned root, causal cutoff or coupled operand"
        )
    return MappingProxyType({c.node_id: c for c in configs})


def validate_root(config, context):
    if (
        context.scientific_preparation.get(context.node_id) != config
        or context.node_id != config.node_id
        or context.unit_ids != config.unit_ids
        or not set(context.unit_ids) <= set(context.selected_unit_ids)
        or context.stage != design.STAGES[config.phase]
        or context.outcome_access != design.ACCESS
        or context.visibility_ceiling != design.VISIBILITY
    ):
        raise ValueError("Waveform operation changed its scientific scope")


def assess_supply(record, requirement, connection):
    if type(record) is not WaveformProduct:
        return ()
    parents = tuple(
        p
        for p in record.dependencies
        if p.object_id == connection.supplier_operation_id + ".product"
    )
    if len(parents) != 1 or connection.assessment_operation_id != record.config.node_id:
        raise ValueError("Waveform supply does not belong to its consuming operation")
    return (
        RequirementSupplyAssessment(
            "assessment." + connection.connection_id,
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            AssessmentPhase.INSTANCE,
            AssessmentDisposition.SATISFIED,
            record.config.node_id,
            tuple(sorted((parents[0], record.identity), key=lambda p: p.object_id)),
            (),
        ),
    )


def read_operand(product, binary=None):
    expected = PHASE_TYPES[product.config.phase]
    document = (
        decode_acquisition(product, binary) if binary is not None else product.payload
    )
    raw = canonical_json_document_bytes(document)
    if sha256(raw).hexdigest() != product.operand_sha256:
        raise ValueError(
            "Reconstructed waveform operand differs from its measured canonical bytes"
        )
    return decode_canonical_bytes(raw, expected, maximum_bytes=len(raw))


def calculate(config, sources, parents, binary, *, array_artifact_id=None):
    if sorted((p.config.node_id for p in parents)) != sorted(
        p.node_id for p in config.suppliers()
    ):
        raise ValueError("Waveform worker substituted a sibling or omitted an input")
    for p in parents:
        if p.config.design != config.design or (p.config.phase in NATIVE) != (
            p.array_artifact is not None
        ):
            raise ValueError("Waveform native companion or original design is missing")
    expected = {
        p.array_artifact.artifact_id for p in parents if p.array_artifact is not None
    }
    if set(binary) != expected:
        raise ValueError(
            "Waveform worker requires the exact original binary companions"
        )
    data = [
        (
            p.config.phase,
            read_operand(
                p,
                binary.get(p.array_artifact.artifact_id) if p.array_artifact else None,
            ),
        )
        for p in parents
    ]
    phase, spec = config.phase, config.design
    required_sources = ({"lower"} if phase in LOWER_USERS else set()) | (
        {"development"}
        if phase in ("forecast", "cohort") and spec.development
        else set()
    )
    if set(sources) != required_sources or any(
        v.identity != getattr(spec, k) for k, v in sources.items()
    ):
        raise ValueError(
            "Waveform worker substituted the original F or development fit"
        )
    if phase == "cohort":
        result = assess_cohort(
            spec.role,
            spec.master_seed,
            spec.bootstrap_seed,
            [v for _, v in data],
            development=sources.get("development"),
        )
    else:
        values = dict(data)
        if phase == "prefix":
            draw = spec.draw(config.index)
            result = acquire_prefix(
                draw.allocation, spec.producing_code_sha256, waveform=draw
            )
        elif phase == "forecast":
            parent = sources.get("development")
            result = seal_prefix(
                values["prefix"], sources["lower"], parent.fitted if parent else None
            )
        elif phase == "parents":
            result = acquire_parents(values["prefix"], values["forecast"])
        elif phase == "lower":
            result = seal_lower(
                values["prefix"],
                values["forecast"],
                values["parents"],
                sources["lower"],
            )
        elif phase == "assay":
            result = acquire_panel(values["prefix"], values["parents"], values["lower"])
        else:
            result = assess_panel(
                values["prefix"],
                values["forecast"],
                values["lower"],
                values["assay"],
                sources["lower"],
            )
    product = WaveformProduct.from_operand(config, parents, result)
    if phase in NATIVE:
        return encode_acquisition(
            product,
            artifact_id=array_artifact_id or config.node_id + ".arrays",
            allow_empty=True,
            base64_float_fields=FLOAT_FIELDS,
        )
    return product, None


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def _outputs(self, context):
        configs, parents, binary, sources = [], [], {}, {}
        for port in context.input_ports:
            if (
                port.payload_schema == MATRIX_FRAMED_ARRAY_SCHEMA
                and port.media_type == "application/octet-stream"
            ):
                if port.artifact_id in binary:
                    raise ValueError("Duplicate waveform binary input")
                binary[port.artifact_id] = port
                continue
            kinds = {
                t.SCHEMA: t
                for t in (
                    WaveformOperation,
                    WaveformProduct,
                    OriginalFiniteResponseLaw,
                    WaveformCohort,
                )
            }
            kind = kinds.get(port.payload_schema)
            if not kind or port.media_type != "application/json":
                raise ValueError("Unexpected waveform worker input")
            record = port.decode_canonical_record(kind, maximum_bytes=port.size_bytes)
            if kind is WaveformOperation:
                configs.append(record)
            elif kind is WaveformProduct:
                parents.append(record)
            else:
                key = "lower" if kind is OriginalFiniteResponseLaw else "development"
                if key in sources:
                    raise ValueError("Duplicate waveform scientific input")
                sources[key] = record
        (config,) = configs
        if (
            context.task_id != config.node_id
            or config.config_id != context.config.config_id
            or context.config.content_sha256 != config.fingerprint()
            or context.permissions != design.PERMISSIONS
            or context.resource_budget != design.BUDGET
            or context.outcome_access != design.ACCESS
            or self.manifest.capability_key != NAMESPACE + "." + config.phase
        ):
            raise ValueError(
                "Waveform task and authored scientific configuration differ"
            )
        outputs = {p.output_id: p for p in context.output_ports}
        array_id = config.node_id + ".arrays"
        product_id = config.node_id + ".product"
        expected_outputs = (
            {product_id, array_id} if config.phase in NATIVE else {product_id}
        )
        if set(outputs) != expected_outputs or len(outputs) != len(
            context.output_ports
        ):
            raise ValueError("Waveform output ports differ from the declared operation")
        for name, port in outputs.items():
            if port.logical_artifact_id != f"artifact.{context.run_id}.{name}":
                raise ValueError("Waveform output belongs to another run")
        product, chunks = calculate(
            config,
            sources,
            parents,
            binary,
            array_artifact_id=outputs[array_id].logical_artifact_id
            if config.phase in NATIVE
            else None,
        )
        if chunks is not None:
            yield config.node_id + ".arrays", iter_encoded_bytes(product, chunks)
        yield product.record_id, (product.canonical_bytes(),)

    def execute(self, context):
        try:
            return RunnerResult(
                tuple(
                    TaskOutputPayload(key, b"".join(parts))
                    for key, parts in self._outputs(context)
                ),
                (ReceiptCheck(CHECK, True, ()),),
            )
        finally:
            for port in context.input_ports:
                port.close()

    def execute_streaming(self, context, emitter, progress=None):
        try:
            for key, parts in self._outputs(context):
                for part in parts:
                    for start in range(0, len(part), STREAM_CHUNK_BYTES):
                        emitter.write(key, part[start : start + STREAM_CHUNK_BYTES])
            return (ReceiptCheck(CHECK, True, ()),)
        finally:
            for port in context.input_ports:
                port.close()


@lru_cache(maxsize=1)
def declarations():
    result = []
    codecs = {
        t.SCHEMA: t
        for t in (
            WaveformSpecification,
            WaveformOperation,
            WaveformProduct,
            OriginalFiniteResponseLaw,
            WaveformCohort,
        )
    }
    for phase in PHASES:
        ports = []
        if PREDECESSORS[phase]:
            ports.append(
                RecursivePortContract(
                    "parents", WaveformProduct.SCHEMA, "application/json", None, 1, None
                )
            )
        if any(p in NATIVE for p in PREDECESSORS[phase]):
            ports.append(
                RecursivePortContract(
                    "arrays",
                    MATRIX_FRAMED_ARRAY_SCHEMA,
                    "application/octet-stream",
                    None,
                    1,
                    None,
                )
            )
        if phase in LOWER_USERS:
            ports.append(
                RecursivePortContract(
                    "lower", OriginalFiniteResponseLaw.SCHEMA, "application/json", None
                )
            )
        if phase in ("forecast", "cohort"):
            ports.append(
                RecursivePortContract(
                    "development", WaveformCohort.SCHEMA, "application/json", None, 0, 1
                )
            )
        outputs = (
            (
                OutputTemplate(
                    "arrays",
                    MATRIX_FRAMED_ARRAY_SCHEMA,
                    ArtifactProfile.RAW_SOURCE_BYTES,
                    "application/octet-stream",
                    ".bin",
                ),
            )
            if phase in NATIVE
            else ()
        )
        outputs += (
            OutputTemplate(
                "product",
                WaveformProduct.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,
                "application/json",
                ".json",
            ),
        )
        decl = RecursiveOperationDeclaration(
            capability_key=NAMESPACE + "." + phase,
            capability_version="1.0.0",
            implementation_id=NAMESPACE + "." + phase + ".v1",
            kind=CapabilityKind.SIMULATOR
            if phase in NATIVE
            else CapabilityKind.ANALYSIS,
            config_record_type=WaveformOperation,
            stage=design.STAGES[phase],
            input_ports=tuple(sorted(ports, key=lambda r: r.port_id)),
            outputs=outputs,
            permissions=design.PERMISSIONS,
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=design.ACCESS,
            visibility_ceiling=design.VISIBILITY,
            resources=design.BUDGET,
            conformance_check_ids=(CHECK,),
            runner_factory=Runner,
            record_codecs=codecs,
            storage_codecs=(MATRIX_FRAMED_CODEC,),
            execution_properties=RecursiveExecutionProperties(deterministic=False),
            scientific_hooks=RecursiveScientificHooks(
                assessment_projector=assess_supply,
                scientific_operand_sha256s=operands,
                scientific_unit_ids=units,
                scientific_root_preparer=prepare_root,
                scientific_root_validator=validate_root,
            ),
        )
        result.append(
            replace(decl, runner_factory=partial(Runner, manifest=decl.manifest()))
        )
    return tuple(result)
