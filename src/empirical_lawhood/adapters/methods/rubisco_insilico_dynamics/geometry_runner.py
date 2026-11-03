# SPDX-License-Identifier: MPL-2.0
"""Assessed geometry composes the existing preparation worker and transport."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.execution import WorkerInputKind
from empirical_lawhood.runtime.native_subwork import NativeSubworkRoster
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

from . import geometry_operation_bindings as ob
from .durable_runner import DurablePreparationWorker, prepare_native_work as prepare_native_work, validate_current_source_descriptor


def load_inputs(context, manifest):
    ports = tuple(port for port in context.input_ports if port.payload_schema == ob.GeometryReuseConfig.SCHEMA)
    if len(ports) != 1:
        raise ValueError("geometry reuse needs its exact complete immutable configuration")
    port = ports[0]
    config = decode_canonical_bytes(port.read(), ob.GeometryReuseConfig, maximum_bytes=None)
    if (context.task_id != ob.NODE or port.kind is not WorkerInputKind.EXTERNAL
            or port.artifact_id != context.config.artifact_id or config.config_id != context.config.config_id
            or config.fingerprint() != context.config.content_sha256 or context.permissions != manifest.permissions
            or context.resource_budget != ob.BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.dependency_receipts):
        raise ValueError("geometry reuse substitutes actual config/task/access/resources")
    kinds = {(kind.SCHEMA, kind.VERSION): kind for kind in ob.INPUT_RECORD_TYPES}
    records = {}
    for identity in config.operands:
        matched = tuple(row for row in context.input_ports if row.artifact_id == identity.object_id)
        if len(matched) != 1:
            raise ValueError("geometry reuse omits an exact original scientific source/assessment")
        current = matched[0]
        if (current.kind is not WorkerInputKind.EXTERNAL or current.payload_schema != identity.object_schema
                or current.media_type != ob.MEDIA or current.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
                or current.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE):
            raise ValueError("geometry reuse substitutes original input schema/access")
        raw = current.read()
        if len(raw) != current.size_bytes or sha256(raw).hexdigest() != identity.object_fingerprint:
            raise ValueError("geometry reuse changes original complete materialized scientific bytes")
        kind = kinds.get((identity.object_schema, identity.object_version))
        if kind is None:
            raise ValueError("geometry reuse lacks its exact declared original input type/revision")
        records[identity] = decode_canonical_bytes(raw, kind, maximum_bytes=None)
    if (len(context.input_ports) != len(records) + 1 or records[config.plan.identity] != config.plan
            or records[config.plan.source] != config.source
            or any(records[row.identity] != row for row in config.supplies)
            or any(records[supply.independent_integrity] != assessment
                for supply, assessment in zip(config.supplies, config.assessments, strict=True))):
        raise ValueError("geometry reuse substitutes any original plan/source/supplier/assessment record")
    expected = ((ob.NODE + ".census", ob.DurablePreparationCensus.SCHEMA, ArtifactProfile.CANONICAL_JSON, ob.MEDIA),
        (ob.NODE + ".units", ob.DurableUnitStreamChunk.SCHEMA, ArtifactProfile.JSONL_CHUNKS, ob.STREAM_MEDIA))
    if tuple((row.output_id, row.payload_schema, row.profile, row.media_type) for row in context.output_ports) != expected:
        raise ValueError("geometry reuse changes its complete original-custody output contract")
    return config, records


class GeometryReuseWorker(DurablePreparationWorker):
    def __init__(self, operation, manifest=None):
        if operation != "reuse-geometry":
            raise ValueError("unknown geometry reuse operation")
        self.manifest = ob.operation_declarations()[0].manifest() if manifest is None else manifest

    def scientific_inputs(self, context):
        return load_inputs(context, self.manifest)

    @property
    def output_node(self):
        return ob.NODE

    def project_native_scope(self, context, expected_parent):
        from empirical_lawhood.infrastructure.numerical_provenance import capture_numerical_provenance
        from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding
        from .durable_roster import definitions
        from .geometry_recursive_translation import native_effect_slot_ids
        config, records = load_inputs(context, self.manifest)
        if Path(config.plan.workdir).exists():
            raise ValueError("geometry reuse refuses existing uncertain work; use receipt-only recovery")
        if context.prepared_invocation is None:
            observed = capture_numerical_provenance(project_root=config.source_root)
            implementation = RecursiveImplementationBinding(observed.package_sources, observed.code_sources_sha256,
                observed.dependency_lock_sha256, observed.observed_git_head, observed.observed_checkout_clean)
        else:
            implementation = context.prepared_invocation.implementation
        if implementation.observed_git_head != expected_parent.implementation_commit:
            raise ValueError("geometry reuse changes actual anticipated implementation commit")
        validate_current_source_descriptor(config.plan, implementation, config.source_root)
        selected = definitions(config.plan, expected_parent, sources=config.operands,
            input_materialization_ids=context.input_materialization_ids, implementation=implementation, source_root=config.source_root)
        work = PreparedNativeWork(expected_parent, (ob.c.UNIT,), native_effect_slot_ids(config), selected,
            (NativeSubworkRoster("selected.native-subwork", expected_parent, tuple(row.identity for row in selected)),))
        return config, records, work

    def invocation_bytes(self, config, records, definitions, context):
        from .geometry_reuse import _invocation_transport
        return _invocation_transport(config.plan, config.source, records[config.plan.nomination], records[config.plan.inventory],
            records[config.plan.coordinates], definitions, config.source_root, config.supplies, config.assessments,
            implementation=context.prepared_invocation.implementation)

    def inner_runner(self, config, definitions, output_ids, census_output_id):
        from .geometry_reuse import GeometryReuseRunner
        return GeometryReuseRunner(config.plan, config.invocation_path, definitions, config.environment, output_ids, census_output_id)
