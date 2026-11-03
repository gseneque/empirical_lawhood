# SPDX-License-Identifier: MPL-2.0
"""Exact current TRAIN/E2 native definitions; no I/O, allocation or execution."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as sr
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput


def native_work_definition(config, source, records, expected_parent, input_materialization_ids):
    """Direct typed-family delegation preserves each original canonical definition."""
    from . import native_training_bindings as train, native_training_records as training
    from . import native_utility_bindings as utility, native_utility_records as evaluation
    if type(config) in (train.NativeTrainingOperationConfig, train._BoundConfiguration):
        r = training
    elif type(config) in (utility.NativeUtilityOperationConfig, utility._BoundConfiguration):
        r = evaluation
    else:
        raise TypeError("native acquisition definition requires its exact TRAIN or E2 configuration")
    if (type(config) is train._BoundConfiguration and type(config.wire) is not train.NativeTrainingOperationConfig
            or type(config) is utility._BoundConfiguration and type(config.wire) is not utility.NativeUtilityOperationConfig):
        raise TypeError("native acquisition definition cannot bind a foreign family configuration")
    if config.operation not in ("prefix", "responses"):
        raise ValueError("native acquisition definition requires an actual native phase")
    if (config.source != source.reference
            or input_materialization_ids != expected_parent.input_materialization_ids
            or expected_parent.implementation_commit != source.provenance.observed_git_head
            or config.operation == "responses" and type(config) not in (train._BoundConfiguration, utility._BoundConfiguration)):
        raise ValueError("native acquisition definition changes actual compact source, parent inputs/code or bound response protocol")
    acquisition = records["acquisition"]
    seal_kind = training.NativeTrainingAcquisitionSeal if r is training else evaluation.NativeUtilityAcquisitionSeal
    if (type(acquisition) is not seal_kind
            or (acquisition.specification, acquisition.request) != (config.specification, config.request)):
        raise ValueError("native acquisition definition changes the exact actual request/specification seal")
    if config.operation == "prefix":
        sources = (*r.native_source_pins(source), acquisition.identity)
        streams = tuple(source.root.stream_identity(value) for value in source.root.streams)
        outputs = (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),
            NativeSubworkOutput("checkpoint", sr.ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"))
    else:
        history, causal, physical = (records[name] for name in ("history", "causal", "physical"))
        if (records["checkpoint"] != history.checkpoint or causal.source != sr.identity(source)
                or causal.history != r.identity(history) or physical.source != sr.identity(source)
                or physical.causal_prefix != r.identity(causal)
                or physical.protocol != ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol)):
            raise ValueError("native acquisition future changes actual cutoff/physical acquisition lineage")
        # PURE work describes exact operands. The actual worker validates and
        # materializes these arrays once, before Ready; parent projections
        # never decode or transport an additional copy of native arrays.
        sources = (*r.native_source_pins(source),
            r.identity(history), sr.identity(history.checkpoint), r.identity(causal), acquisition.identity,
            r.identity(physical), config.specification)
        streams = (*tuple(source.root.stream_identity(value) for value in source.root.streams),
            *(panel.stream_identity(value) for panel in config.panels if panel.role == "INDEPENDENT_FUTURE" for value in panel.streams))
        outputs = (NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz"),)
    return NativeSubworkDefinition(config.operation + "." + source.root_id,
        r.NAMESPACE + (".paired-prefix.v1" if config.operation == "prefix" else ".paired-responses.v1"), expected_parent,
        r.identity(config), tuple(sorted(sources, key=lambda value: value.object_id)), source.provenance.code_sources_sha256,
        source.provenance.dependency_lock_sha256, input_materialization_ids,
        tuple(sorted(streams, key=lambda value: value.object_id)), outputs)
