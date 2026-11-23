"""Import original allocations into the continuation without another source or selector call."""

from hashlib import sha256

from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_continuation.discovery import (
    LOCKED_IMPORT_CAPABILITY,
)
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_continuation.provider import (
    FiniteResponseLawPrefixImportProvider,
)
from empirical_lawhood.adapters.simulators.finite_response_law.locked_evaluation import (
    CONTROL_RESULTS,
)
from empirical_lawhood.adapters.simulators.finite_response_law.native_artifact import (
    NATIVE_PAIR_SCHEMA,
)
from empirical_lawhood.adapters.simulators.finite_response_law.provider import (
    native_stage,
)
from empirical_lawhood.adapters.simulators.finite_response_law.source_outputs import (
    FiniteResponseLawAssignedEvaluationTaskResult,
)
from empirical_lawhood.adapters.simulators.response_geometry_prospective.provider import (
    decode_port,
    output_result,
    read_port,
    semantic_contracts,
)
from empirical_lawhood.domains.matrix.finite_response_law.control_records import (
    FiniteResponseLawRootControlLock,
)
from empirical_lawhood.execution.execution import WorkerInputKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.source_qualification import (
    validate_retained_qualification_receipt,
)
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.finite_response_law.contracts import (
    native_invocations,
)
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt


class LockedImportTask:
    manifest = LOCKED_IMPORT_CAPABILITY

    def __init__(self, config, runtime):
        self.config, self.runtime = config, runtime

    def execute(self, context):
        try:
            config = self.config
            artifacts = config.import_inputs[context.task_id]
            external = [
                p for p in context.input_ports if p.kind is WorkerInputKind.EXTERNAL
            ]
            ports = {p.artifact_id: p for p in external}
            key = f"config-artifact.{config.config_id}"
            if (
                len(ports) != len(external)
                or set(ports) != {key, *(a.artifact_id for a in artifacts)}
                or context.config.content_sha256 != config.fingerprint()
                or decode_port(ports[key], type(config), maximum=16 * 1024**2) != config
            ):
                raise ValueError("Retained R24 import changes its issued task inputs")
            dependencies = {r.task_id: r for r in context.dependency_receipts}
            if tuple(sorted(dependencies)) != config.import_dependencies[
                context.task_id
            ] or len(dependencies) != len(context.dependency_receipts):
                raise ValueError(
                    "Retained choice changes its original predecessor tasks"
                )
            consumed = set()
            for task_id, binding in dependencies.items():
                expected = {
                    a.payload_schema: a for a in config.import_inputs[task_id][:-1]
                }
                incoming = [
                    p
                    for p in context.input_ports
                    if p.materialization_id in binding.output_materialization_ids
                ]
                if (
                    len(incoming) != len(expected)
                    or {p.payload_schema for p in incoming} != expected.keys()
                ):
                    raise ValueError(
                        "Retained choice must consume every predecessor publication"
                    )
                for port in incoming:
                    member = expected[port.payload_schema]
                    if (
                        port.size_bytes != member.size_bytes
                        or sha256(read_port(port, member.size_bytes)).hexdigest()
                        != member.sha256
                    ):
                        raise ValueError(
                            "Retained choice consumed different predecessor bytes"
                        )
                    consumed.add(port.materialization_id)
            if {
                p.materialization_id
                for p in context.input_ports
                if p.kind is not WorkerInputKind.EXTERNAL
            } != consumed:
                raise ValueError("Retained import includes an unrelated dependency")
            bodies = {}
            for artifact in artifacts:
                port = ports[artifact.artifact_id]
                raw = read_port(port, artifact.size_bytes)
                if (
                    sha256(raw).hexdigest(),
                    len(raw),
                    port.payload_schema,
                    port.outcome_access,
                    port.visibility_ceiling,
                ) != (
                    artifact.sha256,
                    artifact.size_bytes,
                    artifact.payload_schema,
                    OutcomeAccess.OUTCOME_BLIND,
                    VisibilityCeiling.PROSPECTIVE,
                ):
                    raise ValueError(
                        "Retained R24 task member differs from original custody"
                    )
                bodies[artifact.payload_schema] = raw
            receipt = decode_canonical_bytes(
                bodies.pop(CanonicalTaskReceipt.SCHEMA),
                CanonicalTaskReceipt,
                maximum_bytes=artifacts[-1].size_bytes,
            )
            if (
                receipt.run_id != config.donor_run_id
                or receipt.task_id != context.task_id
                or receipt.receipt_id != artifacts[-1].artifact_id
                or receipt.operational_status.value != "SUCCEEDED"
                or {
                    a.logical_artifact_id: a.content_sha256
                    for a in receipt.output_logical_artifacts
                }
                != {a.artifact_id: a.sha256 for a in artifacts[:-1]}
            ):
                raise ValueError(
                    "Retained import differs from its original successful receipt"
                )
            if NATIVE_PAIR_SCHEMA in bodies:
                prior = next(
                    p for p in config.native_origins if p.segment_id == context.task_id
                )
                validate_retained_qualification_receipt(prior, receipt)
                native = decode_canonical_bytes(
                    bodies[FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA],
                    FiniteResponseLawAssignedEvaluationTaskResult,
                    maximum_bytes=16 * 1024**2,
                )
                expected = next(
                    t
                    for t in native_invocations(config.source)
                    if t.task_id == context.task_id
                )
                if (
                    native.invocation != expected
                    or not native.native_complete
                    or native.native_pair.data_sha256
                    != sha256(bodies[NATIVE_PAIR_SCHEMA]).hexdigest()
                    or native.invocation.task_id != prior.segment_id
                    or native.invocation.root.physical_unit_id
                    != prior.physical_independent_unit_id
                    or native.invocation.source
                    != ObjectIdentity.from_record(config.source.spec_id, config.source)
                    or native_stage(native).canonical_bytes()
                    != bodies[LinkedCampaignStageEnvelope.SCHEMA]
                ):
                    raise ValueError(
                        "Retained preparation changes its assigned source, native bytes or stage"
                    )
            else:
                op = context.task_id.rsplit(".", 1)[-1]
                cls = CONTROL_RESULTS[op]
                record = decode_canonical_bytes(
                    bodies[cls.SCHEMA], cls, maximum_bytes=16 * 1024**2
                )
                root = (
                    record.forecast.root
                    if cls is FiniteResponseLawRootControlLock
                    else record.root
                )
                if (
                    root not in config.source.roots
                    or context.task_id != f"{root.stage_unit}.{op}"
                ):
                    raise ValueError("Retained choice changes its physical root")
                if cls is FiniteResponseLawRootControlLock:
                    forecast, forecast_receipt = config.import_inputs[
                        f"{root.stage_unit}.forecast"
                    ]
                    requests, _ = config.import_inputs[
                        f"{root.stage_unit}.reveal-request"
                    ]
                    if (
                        record.forecast.fingerprint() != forecast.sha256
                        or record.requests.fingerprint() != requests.sha256
                        or record.requests.forecast_receipt_id
                        != forecast_receipt.artifact_id
                    ):
                        raise ValueError(
                            "Retained lock changes the original forecast or independent request"
                        )
                    self.runtime.prepared_store.import_locked_prefixes(record)
            return output_result(
                context,
                bodies,
                ("original-receipt-bound-locked-evaluation", "zero-native-updates"),
            )
        finally:
            for port in context.input_ports:
                port.close()


class LockedImportProvider(FiniteResponseLawPrefixImportProvider):
    def __init__(self, registry, config, resolver, runtime):
        self.registry, self.config, self.resolver, self.runtime = (
            registry,
            config,
            resolver,
            runtime,
        )
        self.manifest = LOCKED_IMPORT_CAPABILITY
        if (
            registry.resolve(
                self.manifest.capability_key, self.manifest.capability_version
            )
            != self.manifest
        ):
            raise ValueError("Locked R24 import has a different registered capability")
        self.registry_sha256, self.capability_count = registry.fingerprint(), 1

    def import_dependencies(self, task_id):
        return self.config.import_dependencies[task_id]

    def import_inputs(self):
        return self.config.import_inputs

    def runners(self, registry, source_records=()):
        if registry != self.registry or source_records:
            raise ValueError("Locked R24 import has another runner registry")
        return (LockedImportTask(self.config, self.runtime),)

    def output_semantic_contracts(self, registry, execution_plan=None):
        if registry != self.registry:
            raise ValueError("Locked R24 import has another semantic registry")
        return semantic_contracts(
            self.manifest,
            (
                FiniteResponseLawAssignedEvaluationTaskResult,
                LinkedCampaignStageEnvelope,
                *CONTROL_RESULTS.values(),
            ),
            NATIVE_PAIR_SCHEMA,
        )
