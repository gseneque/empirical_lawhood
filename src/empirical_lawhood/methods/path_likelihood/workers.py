# SPDX-License-Identifier: MPL-2.0
"""Workers for two independently registered, causally frozen path experiments."""

from dataclasses import replace
from functools import partial
from hashlib import sha256
from time import process_time, perf_counter

from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import BarrierKind, OutputTemplate
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import (
    RecursiveExecutionProperties,
    RecursiveOperationDeclaration,
    RecursiveScientificHooks,
)
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import (
    AssessmentDisposition,
    AssessmentPhase,
    RequirementSupplyAssessment,
)
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from . import arrays, protocol
from .records import (
    PathOperation,
    PathProduct,
    numerical_json,
    operations,
    required_parents,
)


def units(config):
    if config.acquires:
        return (config.unit_id,)
    return tuple(
        sorted(
            f"batch.{i:019d}.{min(config.first + config.count - i, config.design.batch_size):07d}"
            for i in range(
                config.first, config.first + config.count, config.design.batch_size
            )
        )
    )


def prepare_root(context, *, spec_type):
    configs = tuple(v.record for v in context.config_inputs)
    spec = spec_type(configs[0].design)
    expected = operations(spec)
    if sorted(configs, key=lambda c: c.node_id) != list(expected):
        raise ValueError("path experiment changes a block or freeze boundary")
    root, requirements, connections, links = protocol.graph(spec, expected)
    if (root, requirements, connections, links, ()) != (
        context.root,
        context.requirements,
        context.connections,
        context.links,
        context.external_inputs,
    ):
        raise ValueError("path experiment changed its causal graph")
    return {c.node_id: c for c in expected}


def validate_root(config, context):
    if (
        context.scientific_preparation.get(context.node_id) != config
        or context.unit_ids != units(config)
        or context.stage != protocol.STAGES[config.phase]
        or context.outcome_access != protocol.ACCESS
        or context.visibility_ceiling != protocol.VISIBILITY
    ):
        raise ValueError("path stage changes its scientific scope or unit census")


def operands(config):
    return (config.specification.object_fingerprint,)


def assess_supply(record, requirement, connection):
    if type(record) is not PathProduct:
        return ()
    pins = tuple(
        p
        for p in record.parents
        if p.object_id == connection.supplier_operation_id + ".product"
    )
    if len(pins) != 1 or record.config.node_id != connection.assessment_operation_id:
        raise ValueError("path supply lacks the original measured parent")
    return (
        RequirementSupplyAssessment(
            "assessment." + connection.connection_id,
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            AssessmentPhase.INSTANCE,
            AssessmentDisposition.SATISFIED,
            record.config.node_id,
            tuple(sorted((*pins, record.identity), key=lambda p: p.object_id)),
            (),
        ),
    )


class PathRunner:
    def __init__(self, spec_type, acquire, evaluate, manifest):
        self.spec_type, self.acquire, self.evaluate, self.manifest = (
            spec_type,
            acquire,
            evaluate,
            manifest,
        )

    def execute(self, context):
        from threadpoolctl import threadpool_limits

        started, wall = process_time(), perf_counter()
        try:
            configs, parents, files = [], [], {}
            for port in context.input_ports:
                if (port.payload_schema, port.media_type) == (
                    arrays.SCHEMA,
                    arrays.MEDIA,
                ):
                    if port.artifact_id in files:
                        raise ValueError("duplicate path array")
                    files[port.artifact_id] = port
                    continue
                kind = {
                    PathOperation.SCHEMA: PathOperation,
                    PathProduct.SCHEMA: PathProduct,
                }[port.payload_schema]
                if port.media_type != "application/json":
                    raise ValueError("unexpected path record media")
                (configs if kind is PathOperation else parents).append(
                    port.decode_canonical_record(kind, maximum_bytes=port.size_bytes)
                )
            (config,) = configs
            spec = self.spec_type(config.design)
            if (
                config.node_id != context.task_id
                or config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
                or context.permissions != protocol.PERMISSIONS
                or context.resource_budget != protocol.BUDGET
                or self.manifest.capability_key != spec.FAMILY + "." + config.phase
            ):
                raise ValueError("path worker changed its registered operation")
            parents.sort(key=lambda p: p.config.node_id)
            if tuple(p.config for p in parents) != required_parents(
                config, operations(spec)
            ):
                raise ValueError(
                    "path worker changed a cohort, frozen rule or original parent"
                )
            batch_parents = sorted(
                (p for p in parents if p.arrays is not None),
                key=lambda p: p.config.first,
            )
            if set(files) != {p.arrays.artifact_id for p in batch_parents}:
                raise ValueError("path worker lacks an original binary companion")
            batches = []
            for parent in batch_parents:
                pin = parent.arrays
                raw = files[pin.artifact_id].read()
                if (len(raw), sha256(raw).hexdigest()) != (pin.size_bytes, pin.sha256):
                    raise ValueError("retained path bytes differ")
                measurement = parent.measurement
                decoded = arrays.decode(raw, measurement["array_manifest"])
                if decoded["root"].tolist() != list(
                    range(
                        parent.config.first, parent.config.first + parent.config.count
                    )
                ):
                    raise ValueError(
                        "incorrect independent root census in retained path arrays"
                    )
                batches.append((measurement, decoded))
            frozen = next(
                (p.measurement for p in parents if p.config.phase == "freeze"), None
            )
            pins = tuple(p.identity for p in parents)
            out = {port.output_id: port for port in context.output_ports}
            product_id, array_id = (
                config.node_id + ".product",
                config.node_id + ".arrays",
            )
            if set(out) != (
                {product_id, array_id} if config.acquires else {product_id}
            ):
                raise ValueError("unexpected path output ports")
            emissions, pin = [], None
            with threadpool_limits(limits=1):
                if config.acquires:
                    settings = dict(
                        spec.design.parameters,
                        retained_root=(
                            spec.design.first_root
                            if config.phase == "develop"
                            else spec.design.first_root + spec.design.development_roots
                        ),
                    )
                    if spec.ISSUED_FORECAST:
                        settings["first_root"] = spec.design.first_root
                        inputs = {
                            p.config.phase: values
                            for p, (_, values) in zip(
                                batch_parents, batches, strict=True
                            )
                        }
                        result, samples = self.acquire(
                            config.phase,
                            settings,
                            config.first,
                            config.count,
                            inputs,
                            frozen,
                        )
                    else:
                        result, samples = self.acquire(
                            settings, config.first, config.count, frozen
                        )
                    raw, manifest = arrays.encode(samples)
                    pin = ArtifactIdentity(
                        out[array_id].logical_artifact_id,
                        "path-array-container",
                        arrays.SCHEMA,
                        sha256(raw).hexdigest(),
                        arrays.MEDIA,
                        len(raw),
                    )
                    emissions.append(TaskOutputPayload(array_id, raw))
                    result["array_manifest"] = manifest
                else:
                    result = self.evaluate(spec.design.parameters, batches, frozen)
            result["execution_seconds"] = {
                "cpu": process_time() - started,
                "wall": perf_counter() - wall,
            }
            record = PathProduct(config, pins, numerical_json(result), pin)
            emissions.append(TaskOutputPayload(product_id, record.canonical_bytes()))
            return RunnerResult(
                tuple(emissions),
                (ReceiptCheck("path-ensemble.original-census", True, ()),),
            )
        finally:
            for port in context.input_ports:
                port.close()


def operation_declarations(spec_type, acquire, evaluate):
    ns = spec_type.FAMILY
    decls = []
    phases = ("assess", "develop", "evaluate", "freeze")
    if spec_type.ISSUED_FORECAST:
        phases += ("observe", "predict", "prefix")
    for phase in phases:
        native = phase in ("develop", "evaluate", "observe", "predict", "prefix")
        ports = []
        if phase != "develop":
            ports.append(
                RecursivePortContract(
                    "parents", PathProduct.SCHEMA, "application/json", None, 1, None
                )
            )
        if not native or (
            spec_type.ISSUED_FORECAST and phase in ("observe", "predict", "evaluate")
        ):
            ports.append(
                RecursivePortContract(
                    "arrays", arrays.SCHEMA, arrays.MEDIA, arrays.LIMIT, 1, None
                )
            )
        outputs = (
            OutputTemplate(
                "product",
                PathProduct.SCHEMA,
                ArtifactProfile.CANONICAL_JSON,
                "application/json",
                ".json",
            ),
        )
        if native:
            outputs = (
                OutputTemplate(
                    "arrays",
                    arrays.SCHEMA,
                    ArtifactProfile.RAW_SOURCE_BYTES,
                    arrays.MEDIA,
                    ".bin",
                ),
            ) + outputs
        row = RecursiveOperationDeclaration(
            capability_key=ns + "." + phase,
            capability_version="1.0.0",
            implementation_id=ns + "." + phase + ".v1",
            kind=CapabilityKind.SIMULATOR
            if phase in ("develop", "prefix", "evaluate")
            else CapabilityKind.ANALYSIS,
            config_record_type=PathOperation,
            stage=protocol.STAGES[phase],
            input_ports=tuple(sorted(ports, key=lambda p: p.port_id)),
            outputs=outputs,
            permissions=protocol.PERMISSIONS,
            evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=protocol.ACCESS,
            visibility_ceiling=protocol.VISIBILITY,
            resources=protocol.BUDGET,
            conformance_check_ids=(
                "path-ensemble.original-batch",
                "path-ensemble.pre-evaluation-freeze",
            ),
            runner_factory=PathRunner,
            record_codecs={
                v.SCHEMA: v for v in (PathOperation, PathProduct, spec_type)
            },
            storage_codecs=(arrays.CODEC,),
            execution_properties=RecursiveExecutionProperties(
                deterministic=False,
                barrier=BarrierKind.FREEZE if phase == "predict" else BarrierKind.NONE,
            ),
            scientific_hooks=RecursiveScientificHooks(
                scientific_unit_ids=units,
                scientific_operand_sha256s=operands,
                scientific_root_preparer=partial(prepare_root, spec_type=spec_type),
                scientific_root_validator=validate_root,
                assessment_projector=assess_supply,
            ),
        )
        decls.append(
            replace(
                row,
                runner_factory=partial(
                    PathRunner, spec_type, acquire, evaluate, row.manifest()
                ),
            )
        )
    return tuple(decls)
