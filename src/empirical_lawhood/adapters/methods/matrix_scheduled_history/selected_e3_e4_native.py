# SPDX-License-Identifier: MPL-2.0
"""Exact selected E4 DEV native scopes through original segment/pulse owners."""

from dataclasses import replace

import numpy as np

from empirical_lawhood.adapters.simulators.six_matrix_response import parameter_history_segments as segments
from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkOutput, NativeSubworkRoster
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork

from . import science
from .parameter_native import execute_parameter_native_work
from .response_bindings import execute_paired_response_native_work
from .response_forecast import array_product as response_array_product
from .response_records import branch_census
from .records import identity, ScheduledCheckpoint, ScheduledNativeEvidence
from .selected_native_source import bind_selected_native_source
from .selected_e3_e4_bindings import native_contract, local_node
from .selected_e3_e4_records import DEV, EXPOSED, SelectedE3E4Arrays, SelectedE3E4PrefixHistory, SelectedE3E4FullHistory, SelectedE3E4Responses


def phase_config(config, phase):
    return replace(config, phase=phase, config_id="config." + local_node(config.source.root_id, phase))


def initial_native_work(context, config, records, arrays, expected_parent):
    source, phase = bind_selected_native_source(config.source, records["provenance"]), config.phase
    if ((expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id, expected_parent.input_materialization_ids,
            expected_parent.dependency_receipt_ids, expected_parent.implementation_commit) !=
            (context.run_id, context.task_id, context.attempt_id, context.input_materialization_ids,
                context.dependency_receipt_ids, source.provenance.observed_git_head)):
        raise ValueError("selected E4 native preparation changes actual current DEV parent")
    prepared = context.prepared_invocation
    if prepared is not None:
        implementation = prepared.implementation
        if (prepared.expected_parent_contact != expected_parent or (source.provenance.package_sources,
                source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256, source.provenance.observed_git_head) !=
                (implementation.package_sources, implementation.code_sources_sha256, implementation.dependency_lock_sha256,
                    implementation.observed_git_head)):
            raise ValueError("selected E4 native source differs from actual selected source/lock/parent implementation")
    configuration, parent_task, operation, shared = native_contract(config, source)
    if parent_task != context.task_id:
        raise ValueError("selected E4 native phase differs from the actual current task")
    sources = list(shared)
    outputs = [NativeSubworkOutput("arrays", MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz")]
    streams = tuple(source.root.stream_identity(value) for value in source.root.streams)
    if phase == "prefix":
        segments.validate_segment_entry(source.coordinate, source.root.streams, 0, source.policy.cutoff_tick)
        outputs.append(NativeSubworkOutput("checkpoint", ScheduledCheckpoint.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json"))
    else:
        history, causal, account, mechanical = (records[name] for name in ("prefix", "causal", "account", "mechanical"))
        history.validate_source(source, config=phase_config(config, "prefix"))
        if (history.native.definition.parent_contact.run_id != context.run_id or causal.history != identity(history)
                or causal.source != identity(source) or account.source != identity(source) or account.prefix != identity(causal)
                or mechanical.source != identity(source) or mechanical.causal_prefix != identity(causal)):
            raise ValueError("selected E4 future changes actual original prefix/forecast-before-future chain")
        sources.extend((identity(history), identity(history.checkpoint), identity(causal), account.identity, identity(mechanical)))
        if phase == "continue":
            if records.get("checkpoint") != history.checkpoint:
                raise ValueError("selected E4 continuation changes actual four-generator checkpoint input")
        else:
            streams += tuple(panel.stream_identity(value) for panel in config.panels if panel.role == "INDEPENDENT_FUTURE"
                for value in panel.streams)
    # The complete potential child stays frozen even when scientific nonuse
    # prevents entering it. Execution checks that disposition before BEGIN.
    definition = NativeSubworkDefinition(phase + "." + source.root_id, operation, expected_parent, configuration,
        tuple(sorted(sources, key=lambda value: value.object_id)), source.provenance.code_sources_sha256,
        source.provenance.dependency_lock_sha256, context.input_materialization_ids,
        tuple(sorted(streams, key=lambda value: value.object_id)), tuple(outputs))
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, (source.root.root.independent_group_id,),
        (phase + "." + source.root_id,), (definition,), (roster,))


def execute_native(context, config, records, arrays, native_subwork, *, artifact_id, progress=None, prepared_arrays=None):
    source, phase = bind_selected_native_source(config.source, records["provenance"]), config.phase
    work = initial_native_work(context, config, records, arrays, native_subwork.parent_contact)
    if phase == "prefix":
        returned = execute_parameter_native_work(source, work, native_subwork,
            prefix_only=True, start=0, stop=source.policy.cutoff_tick, progress=progress)
        raw, _, checkpoint, definition, completed = returned
        product_arrays = returned.rebind_prefix(source, record_type=SelectedE3E4Arrays, artifact_id=artifact_id,
            artifact_role="selected-e4-exposed-prefix", access=DEV, visibility=EXPOSED)
        product = SelectedE3E4PrefixHistory("prefix." + source.root_id, identity(source), product_arrays, checkpoint,
            ScheduledNativeEvidence(definition, completed.completion, completed.receipt))
        product.validate_source(source, config=config)
        return raw, product
    history, causal, account, mechanical = (records[name] for name in ("prefix", "causal", "account", "mechanical"))
    prefix = (science.consume_prefix(source, history.arrays, arrays["prefix-arrays"])
        if prepared_arrays is None else prepared_arrays[0])
    if phase == "continue":
        terminal = {view + "_" + component: prefix[view + "_" + component][-1]
            for view in ("primary", "fine") for component in ("positions", "momenta")}
        segments.validate_segment_entry(source.coordinate, source.root.streams, source.policy.cutoff_tick,
            source.coordinate.total_ticks, terminal=terminal, generator_states=history.checkpoint.generators)
        returned = execute_parameter_native_work(source, work, native_subwork, prefix_only=False,
            start=source.policy.cutoff_tick, stop=source.coordinate.total_ticks, history=history,
            prefix_raw=arrays["prefix-arrays"], terminal=terminal, progress=progress,
            prefix_values=prefix, artifact_id=artifact_id)
        raw, _, _, definition, completed = returned
        operand = returned.array_product
        product = SelectedE3E4FullHistory("full." + source.root_id, identity(source), identity(history), identity(history.checkpoint),
            account.identity, operand, ScheduledNativeEvidence(definition, completed.completion, completed.receipt),
            source.coordinate.total_ticks, 2 * source.coordinate.total_ticks, identity(mechanical))
        product.validate_source(source, history, causal, account, mechanical, config=config, prefix_config=phase_config(config, "prefix"))
        return raw, product
    frozen = (decode_matrix_arrays(arrays["mechanical-arrays"], mechanical.arrays)
        if prepared_arrays is None else prepared_arrays[1])
    native = ()
    if causal.disposition != "AVAILABLE" or mechanical.disposition != "AVAILABLE":
        values = {"unentered_branches": np.arange(48, dtype="<i8")}
        disposition = ("NO_ORIGIN" if causal.disposition == "NO_ORIGIN" else "INSTRUMENT_UNRESOLVED"
            if mechanical.disposition == "INSTRUMENT_UNRESOLVED" else "UNEVALUABLE")
        raw = None
    else:
        raw, values, definition, completed = execute_paired_response_native_work(source, work, native_subwork,
            protocol=config.protocol, panels=config.panels, history=history, prefix=prefix, frozen=frozen,
            selection=config.response_selection, progress=progress)
        native = (ScheduledNativeEvidence(definition, completed.completion, completed.receipt),)
        disposition = "COMPLETED"
    raw, operand = response_array_product(config.protocol, values, role="RESPONSES", artifact_id=artifact_id,
        producers=(identity(source), config.response_selection, identity(mechanical), account.identity), access=DEV, visibility=EXPOSED,
        **({"raw": raw} if native else {}))
    product = SelectedE3E4Responses("responses." + source.root_id, identity(source), identity(causal), identity(mechanical),
        account.identity, ObjectIdentity.from_record(config.protocol.protocol_id, config.protocol),
        operand, tuple(value[0] for value in branch_census(config.protocol, config.panels)), native, disposition,
        () if native else ("complete48-pulse-slots-not-entered-" + disposition.lower(),))
    product.validate_source(source, history, causal, mechanical, account, config=config, prefix_config=phase_config(config, "prefix"))
    return raw, product
