# SPDX-License-Identifier: MPL-2.0
"""Retained selected E5/E6 science, under current issued and original custody.

The native functional assay, raw point comparison and downstream uncertainty
are distinct products. This reader executes no provider or native operation.
"""
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_prepared_choices as scientific_choices
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as declarative
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_protected_bindings as original
from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_bindings as revision
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_e6_transport_config import (
    ENTRY_TRANSPORT_KEY, MatrixSelectedTransportRootConfig, MatrixSelectedTransportPointConfig,
    MatrixSelectedTransportFutureConfig, MatrixSelectedTransportScoreConfig,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import (
    MatrixE6TransportDecision, MatrixE6EmpiricalTransportAssessment, MatrixE6TransportManifest,
)
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import assess_e6_transport
from empirical_lawhood.adapters.methods.matrix_experimental_programme.functional_case_reduction import native_functional_case
from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_secondary_readout import prepared_secondary_projection
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_protected_results import assess_selected_programme, entry_seal
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_results import assess_revision_programme, revision_transfer_regimes
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import entry_seal as revision_entry_seal
from .current_result_custody import CurrentResultPlanReader, retained_output_artifact_plane
from .matrix_selected_runtime import _authenticate_entry, _current_source_qualifications, _published_input
from empirical_lawhood.api.matrix_selected_revision_runtime import authenticate_revision_entry
from .recursive_qualified_parents import (
    MAX_PARENT_BYTES, _actual_package, _output_payload,
    _replay_parent_authority, _verify_receipt_closure,
)
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.kernel.status import AdmissionStatus, ScientificStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.adjudication import AdjudicationEvaluability, ScientificAdjudicationRecord
from empirical_lawhood.runtime.prospective_experiment import ALLOCATION_FILENAME, SPECIFICATION_FILENAME, source_filename


def _pin(value, field="record_id"):
    return ObjectIdentity.from_record(getattr(value, field), value)


def _decode(raw, kind):
    value = decode_canonical_bytes(raw, kind, maximum_bytes=MAX_PARENT_BYTES)
    if value.canonical_bytes() != raw:
        raise PermissionError("SELECTED_SCIENCE_EXACT_CANONICAL_BYTES_REQUIRED")
    return value


def _design(selected):
    kinds = (scientific_choices.SelectedPreparedProtectedSpecification,)
    kinds = tuple(kind for kind in kinds if (kind.SCHEMA, kind.VERSION) ==
        (selected.instance.specification.object_schema, selected.instance.specification.object_version))
    if len(kinds) != 1:
        raise PermissionError("SELECTED_SCIENCE_EXACT_SPECIFICATION_REVISION_REQUIRED")
    specification = _decode(selected.payloads[SPECIFICATION_FILENAME], kinds[0])
    allocation = _decode(selected.payloads[ALLOCATION_FILENAME], UnitAllocation)
    if (specification.identity, allocation.identity) != (selected.instance.specification, selected.instance.allocation):
        raise PermissionError("SELECTED_SCIENCE_EXACT_ORIGINAL_DESIGN_REQUIRED")
    return specification, allocation


def _configuration(writer, run_id, task, kinds, *, custody=None):
    kinds = tuple(kind for kind in kinds if kind.SCHEMA == task.capability.config.config_schema)
    specs = tuple(spec for spec in task.external_inputs if spec.logical_artifact_id == task.capability.config.artifact_id)
    if len(kinds) != 1 or len(specs) != 1:
        raise PermissionError("SELECTED_SCIENCE_EXACT_ROOT_CONFIGURATION_REQUIRED")
    return _published_input(writer, run_id, specs[0], kinds[0],custody=custody)


def _entry(writer, run_id, plan,*,custody=None):
    original_keys = (original.ENTRY_ORIGINAL_COMMITMENTS_KEY, ENTRY_TRANSPORT_KEY)
    revision_keys = (revision.capability_key("entry", "PROTECTED", "2.0.0"),)
    entries = tuple(task for task in plan.tasks if task.capability.capability_key in (*original_keys, *revision_keys))
    if len(entries) != 1:
        raise PermissionError("SELECTED_SCIENCE_UNIQUE_ACTUAL_ENTRY_REQUIRED")
    task, = entries
    is_revision = task.capability.capability_key in revision_keys
    kinds = ((revision.MatrixRevisionRootConfigV2,) if is_revision else
        (original.MatrixSelectedProtectedRootConfigV3, MatrixSelectedTransportRootConfig))
    config = _configuration(writer, run_id, task, kinds,custody=custody)
    if config.phase != "entry":
        raise PermissionError("SELECTED_SCIENCE_EXACT_ENTRY_PHASE_REQUIRED")
    return task, config, is_revision


def _validate_design(selected, specification, allocation, entry, is_revision):
    programme = entry.programme
    if type(specification) is not scientific_choices.SelectedPreparedProtectedSpecification:
        raise PermissionError("SELECTED_SCIENCE_CURRENT_DECLARATIVE_SPECIFICATION_REQUIRED")
    expected_revision = specification.account == "REVISION"
    if is_revision != expected_revision or programme.phase != specification.phase:
        raise PermissionError("SELECTED_SCIENCE_EXACT_SELECTED_ACCOUNT_AND_PHASE_REQUIRED")
    kinds = declarative.derived_selection_types()
    refs = tuple((ref, kind) for ref in selected.instance.sources for kind in kinds
        if (ref.object_schema, ref.object_version) == (kind.SCHEMA, kind.VERSION))
    if len(refs) != 1:
        raise PermissionError("SELECTED_SCIENCE_EXACT_DERIVED_SELECTION_REQUIRED")
    ref, kind = refs[0]
    selection = _decode(selected.payloads[source_filename(ref)], kind)
    if selection.identity != ref or declarative.validate_selection(specification, selection) != programme:
        raise PermissionError("SELECTED_SCIENCE_EXACT_DERIVED_PROGRAMME_REQUIRED")
    if _pin(selection.evidence) != entry.entry_evidence:
        raise PermissionError("SELECTED_SCIENCE_EXACT_DERIVED_ENTRY_EVIDENCE_REQUIRED")
    if type(selection) is declarative.SelectedPreparedDerivedSelectionV5:
        if (type(entry) is not MatrixSelectedTransportRootConfig or
                (selection.request.transport_policy, selection.transport_calibration) != (entry.transport_policy, entry.transport_calibration)):
            raise PermissionError("SELECTED_SCIENCE_EXACT_PRETRAIN_TRANSPORT_POLICY_REQUIRED")
    elif type(entry) is MatrixSelectedTransportRootConfig:
        raise PermissionError("SELECTED_SCIENCE_POLICY_BEARING_DERIVED_SELECTION_REQUIRED")
    expected_allocation = declarative.allocation(programme)
    if allocation != expected_allocation:
        raise PermissionError("SELECTED_SCIENCE_COMPLETE_ORIGINAL_ALLOCATION_REQUIRED")


def _entry_evidence(writer, run_id, task, entry, is_revision,*,custody=None):
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import MatrixSelectedEntryEvidenceV3, MatrixRevisionEntryEvidenceV2
    kinds = (MatrixRevisionEntryEvidenceV2,) if is_revision else (MatrixSelectedEntryEvidenceV3,)
    kinds = tuple(kind for kind in kinds if (kind.SCHEMA, kind.VERSION) ==
        (entry.entry_evidence.object_schema, entry.entry_evidence.object_version))
    specs = tuple(spec for spec in task.external_inputs if spec.logical_artifact_id != task.capability.config.artifact_id)
    if len(kinds) != 1 or len(specs) != 1 or specs[0].expected_size_bytes != entry.entry_evidence_size_bytes:
        raise PermissionError("SELECTED_SCIENCE_EXACT_ENTRY_EVIDENCE_CENSUS_REQUIRED")
    evidence = _published_input(writer, run_id, specs[0], kinds[0],custody=custody)
    if _pin(evidence) != entry.entry_evidence:
        raise PermissionError("SELECTED_SCIENCE_EXACT_CURRENT_SOURCE_EVIDENCE_REQUIRED")
    return evidence


def _original_source_operands(writer, entry, evidence, is_revision, codecs, *, source_scan_bytes,current_access=None):
    """Authenticate exact current commitment-bearing source operands."""
    if is_revision:
        return authenticate_revision_entry(writer, entry.programme, evidence, codecs,
            source_scan_bytes=source_scan_bytes, include_original_allocation=True,current_access=current_access)[1]
    _authenticate_entry(writer, entry.programme, evidence, codecs,
        source_scan_bytes=source_scan_bytes, transport_policy=getattr(entry, "transport_policy", None),
        transport_calibration=getattr(entry, "transport_calibration", None),current_access=current_access)
    return None


def _science_edges(task):
    """Authenticate the frozen CONFIG edge before returning all science edges."""
    from empirical_lawhood.runtime.input_access import validated_task_scientific_input_edges
    return validated_task_scientific_input_edges(task)


def _product_bytes(writer, receipts, task, output, schema, maximum, *, original_input_access=None):
    outputs = tuple(row for row in task.outputs if row.output_id == task.task_id + "." + output)
    receipt = receipts[task.task_id]
    if len(outputs) != 1 or outputs[0].payload_schema != schema:
        raise PermissionError("SELECTED_SCIENCE_EXACT_TYPED_OUTPUT_REQUIRED")
    rows = tuple(row for row in receipt.output_logical_artifacts if row.logical_artifact_id == outputs[0].logical_artifact_id)
    if len(rows) != 1 or rows[0].payload_schema != schema:
        raise PermissionError("SELECTED_SCIENCE_EXACT_RECEIPTED_OUTPUT_REQUIRED")
    logical, = rows
    if original_input_access is None:
        raw = _output_payload(writer, receipt, logical, maximum)
    else:
        from .selected_prepared_access import guarded_output_payload
        raw=guarded_output_payload(writer,receipt,logical,maximum,original_input_access)
    custody = {"receipt": _pin(receipt, "receipt_id").to_document(), "logical_artifact": logical.to_document(),
        "materialization": next(row for row in receipt.output_materializations if row.logical_artifact_id == logical.logical_artifact_id).to_document()}
    return raw, logical, custody


def _product(writer, receipts, task, output, kind, *, original_input_access=None):
    raw, logical, custody = _product_bytes(writer, receipts, task, output, kind.SCHEMA, MAX_PARENT_BYTES,
        original_input_access=original_input_access)
    value = _decode(raw, kind)
    if value.fingerprint() != logical.content_sha256:
        raise PermissionError("SELECTED_SCIENCE_EXACT_TYPED_OUTPUT_BYTES_REQUIRED")
    return value, custody


def _consumed_producer(tasks, terminal, name, *, producer=None, output="product"):
    edges = tuple(edge for edge in terminal.scientific_inputs if edge.consumer_input_id == name)
    if len(edges) != 1 or edges[0].producer_task_id not in tasks:
        raise PermissionError("SELECTED_SCIENCE_EXACT_CONSUMED_PRODUCT_REQUIRED")
    edge, = edges
    task = tasks[edge.producer_task_id]
    if ((producer is not None and task.task_id != producer)
            or edge.producer_output_id != task.task_id + "." + output):
        raise PermissionError("SELECTED_SCIENCE_EXACT_CONSUMED_PRODUCER_REQUIRED")
    selected = tuple(row for row in task.outputs if row.output_id == edge.producer_output_id)
    if len(selected) != 1 or edge.operational_logical_artifact_id != selected[0].logical_artifact_id:
        raise PermissionError("SELECTED_SCIENCE_EXACT_CONSUMED_LOGICAL_ARTIFACT_REQUIRED")
    return task


def _consumed(writer, receipts, tasks, terminal, name, kind, *, producer=None, output="product", product_cache=None, original_input_access=None):
    task = _consumed_producer(tasks, terminal, name, producer=producer, output=output)
    key = task.task_id, output, kind
    if product_cache is not None and key in product_cache:
        return product_cache[key]
    value = _product(writer, receipts, task, output, kind,original_input_access=original_input_access)[0]
    if product_cache is not None:
        product_cache[key] = value
    return value


def _consumed_array(writer, receipts, tasks, terminal, name, operand, *, original_input_access=None):
    """Open only the exact array archive actually consumed from its producer."""
    from hashlib import sha256
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES
    task = _consumed_producer(tasks, terminal, name, output="arrays")
    artifact = operand.array_artifact
    raw, logical, _ = _product_bytes(writer, receipts, task, "arrays", MATRIX_ARRAY_SCHEMA,
        min(artifact.size_bytes, MAXIMUM_MATRIX_ARRAY_BYTES), original_input_access=original_input_access)
    if ((logical.logical_artifact_id, logical.content_sha256, logical.media_type, len(raw), sha256(raw).hexdigest()) !=
            (artifact.artifact_id, artifact.sha256, artifact.media_type, artifact.size_bytes, artifact.sha256)):
        raise PermissionError("SELECTED_SCIENCE_EXACT_CONSUMED_ARRAY_BYTES_REQUIRED")
    return raw


def _external_array(writer, run_id, task, name, artifact, *, original_input_access=None):
    """Read a frozen external array under the existing provider-copy boundary."""
    from hashlib import sha256
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    from .current_task_custody import _require_provider_input_manifest

    edges = tuple(edge for edge in _science_edges(task) if edge.consumer_input_id == name)
    if len(edges) != 1 or edges[0].producer_task_id is not None:
        raise PermissionError("SELECTED_SCIENCE_EXACT_EXTERNAL_ARRAY_EDGE_REQUIRED")
    specs = tuple(spec for spec in task.external_inputs if spec.logical_artifact_id == edges[0].operational_logical_artifact_id)
    if len(specs) != 1 or specs[0].expected_content_sha256 != artifact.sha256:
        raise PermissionError("SELECTED_SCIENCE_EXACT_EXTERNAL_ARRAY_INPUT_REQUIRED")
    spec, = specs
    relative, _, _ = provider_input_location(writer, run_id, spec.logical_artifact_id)
    manifest = writer.read_manifest(relative)
    _require_provider_input_manifest(writer, run_id, spec, manifest, authenticated_size_bytes=artifact.size_bytes)
    if (manifest.logical.payload_schema, manifest.logical.media_type) != (artifact.payload_schema, artifact.media_type):
        raise PermissionError("SELECTED_SCIENCE_EXACT_EXTERNAL_ARRAY_TYPE_REQUIRED")
    def before_member(member):
        if (member.logical, member.materialization) != (manifest.logical, manifest.materialization):
            raise PermissionError("SELECTED_SCIENCE_SINGLE_FROZEN_EXTERNAL_ARRAY_REQUIRED")
        if original_input_access is not None:
            original_input_access.require_member(member)
    writer.verify_manifest(manifest, before_member=before_member)
    if original_input_access is not None:
        original_input_access.require_current()
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=artifact.size_bytes)
    if len(raw) != artifact.size_bytes or sha256(raw).hexdigest() != artifact.sha256:
        raise PermissionError("SELECTED_SCIENCE_EXACT_EXTERNAL_ARRAY_BYTES_REQUIRED")
    if original_input_access is not None:
        original_input_access.require_current()
    return raw


def _replay_matched_revision_case(writer, run_id, programme, source, observation, tasks, receipts, *,
        original_input_access=None, control_custody=None, allow_missing_future=False):
    """Cold reproof of actual feature, pre-future points and full native score."""
    from functools import partial
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_revision_future as future
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_forecast import forecast_public
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource, matched_causal_feature
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix, MatrixPreparedFactorWitness
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationHistory
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_point import forecast_revision_prepared
    from empirical_lawhood.infrastructure.matrix_array_io import DecodedMatrixArrayInput

    consumed = partial(_consumed, original_input_access=original_input_access)
    array = partial(_consumed_array, original_input_access=original_input_access)
    external = partial(_external_array, original_input_access=original_input_access)
    configuration = partial(_configuration, custody=control_custody)
    point, mechanical, readout = observation
    lane = revision.lane_of(programme)
    selected = {}
    for phase, kind in (("point", revision.MatrixRevisionPreparedConfig), ("response-score", future.MatrixRevisionFutureConfig),
            ("responses", future.MatrixRevisionFutureConfigV2)):
        task = tasks.get(future.node_id(source, phase))
        if task is None or (task.capability.capability_key, task.capability.capability_version) != (
                revision.capability_key(phase, lane, revision.phase_version(phase)), revision.phase_version(phase)):
            raise PermissionError("MATCHED_PREPARED_EXACT_ORIGINAL_PRODUCER_REQUIRED")
        config = configuration(writer, run_id, task, (kind,))
        if config.phase != phase or config.programme != programme.identity:
            raise PermissionError("MATCHED_PREPARED_EXACT_ORIGINAL_CONFIG_REQUIRED")
        selected[phase] = task, config
    point_task, point_config = selected['point']
    score_task, score_config = selected['response-score']
    response_task, response_config = selected['responses']
    public, protocol, package = MatrixPreparedPublicSource.from_source(source), programme.protocol(source), programme.selected_package
    if (point_config.public_source != public or point_config.selected_package != package.identity
            or any(config.source != source or config.protocol != protocol or config.selected_package != package
                for config in (score_config, response_config))):
        raise PermissionError("MATCHED_PREPARED_EXACT_SOURCE_MODEL_AND_PROTOCOL_REQUIRED")
    causal = consumed(writer, receipts, tasks, point_task, 'causal', MatrixPreparedCausalPrefix)
    witness = consumed(writer, receipts, tasks, point_task, 'witness', MatrixPreparedFactorWitness)
    if consumed(writer, receipts, tasks, point_task, 'mechanical', type(mechanical)) != mechanical:
        raise PermissionError("MATCHED_PREPARED_POINT_MUST_CONSUME_ACTUAL_MECHANICAL_CHART")
    causal_raw = array(writer, receipts, tasks, point_task, 'causal-arrays', causal.arrays)
    diagnostic_raw = array(writer, receipts, tasks, point_task, 'diagnostic-arrays', witness.arrays)
    frozen_raw = array(writer, receipts, tasks, point_task, 'mechanical-arrays', mechanical.arrays)
    # The score must consume the same actual archives, not merely records with
    # similar numerical values. Complete plan/receipt joins precede expansion.
    for name in ('causal-arrays', 'diagnostic-arrays', 'mechanical-arrays'):
        if _consumed_producer(tasks, point_task, name, output='arrays') != _consumed_producer(tasks, score_task, name, output='arrays'):
            raise PermissionError("MATCHED_PREPARED_SCORE_CHANGES_ORIGINAL_CAUSAL_ARCHIVES")
    mechanical_task = _consumed_producer(tasks, point_task, 'mechanical')
    templates = external(writer, run_id, mechanical_task, 'templates', protocol.templates.array_artifact)
    frozen = DecodedMatrixArrayInput(frozen_raw, mechanical.arrays)
    _, checked = forecast_public(public, protocol, causal, causal_raw, templates,
        artifact_id=mechanical.arrays.array_artifact.artifact_id, retained_input=frozen, raw=frozen_raw)
    if checked != mechanical:
        raise PermissionError("MATCHED_PREPARED_INDEPENDENT_MECHANICAL_REPROOF_FAILED")
    if point.feature is None:
        raise PermissionError("MATCHED_PREPARED_ORIGINAL_CAUSAL_FEATURE_REQUIRED")
    feature = matched_causal_feature(public, protocol, causal, witness, mechanical, causal_raw, diagnostic_raw, frozen_raw,
        record_id=point.feature.record_id, curve_primary=package.models.relation_fit.selection.is_curve_primary)
    expected = forecast_revision_prepared(package.models, public, causal, nomination=package.nomination,
        original_calibration=package.original_calibration, record_id=point.record_id, feature=feature,
        calibration=package.frozen_calibration, reference_package=package.reference_package)
    if expected != point:
        raise PermissionError("MATCHED_PREPARED_INDEPENDENT_CAUSAL_POINT_REPROOF_FAILED")
    if readout is None:
        if not allow_missing_future or score_task.task_id in receipts:
            raise PermissionError('MATCHED_PREPARED_READOUT_CANNOT_BE_DROPPED')
        return None
    for consumer in (score_task, response_task):
        if (consumed(writer, receipts, tasks, consumer, 'point', type(point), producer=point_task.task_id) != point
                or consumed(writer, receipts, tasks, consumer, 'mechanical', type(mechanical)) != mechanical
                or consumed(writer, receipts, tasks, consumer, 'causal', MatrixPreparedCausalPrefix) != causal):
            raise PermissionError("MATCHED_PREPARED_FUTURE_MUST_CONSUME_ORIGINAL_SEALED_FORECAST")
    if consumed(writer, receipts, tasks, score_task, 'witness', MatrixPreparedFactorWitness) != witness:
        raise PermissionError("MATCHED_PREPARED_SCORE_CHANGES_ORIGINAL_FEATURE_WITNESS")
    history = consumed(writer, receipts, tasks, score_task, 'history', MatrixPreparationHistory)
    if consumed(writer, receipts, tasks, response_task, 'history', MatrixPreparationHistory) != history:
        raise PermissionError("MATCHED_PREPARED_RESPONSE_CHANGES_ORIGINAL_HANDOFF_HISTORY")
    response = consumed(writer, receipts, tasks, score_task, 'responses', future.MatrixRevisionFutureHistory, producer=response_task.task_id)
    future.validate_future_history(response_config, history, causal, point, mechanical, response)
    initial = external(writer, run_id, score_task, 'initial-state', source.initial.array_artifact)
    preparation_raw = array(writer, receipts, tasks, score_task, 'history-arrays', history.arrays)
    response_raw = array(writer, receipts, tasks, score_task, 'response-arrays', response.arrays)
    checked = future.assess_future(score_config, history, causal, point, mechanical, response, initial,
        preparation_raw, frozen_raw, response_raw, record_id=readout.record_id, frozen_input=frozen)
    if checked != readout:
        raise PermissionError("MATCHED_PREPARED_INDEPENDENT_NATIVE_SCORE_REPROOF_FAILED")
    if package.models.relation_fit.selection.is_curve_primary:
        from .matrix_mechanism_read import bound_mechanism
        from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
        return bound_mechanism(protocol=protocol, source=source.identity, causal_record=causal,
            physical_record=mechanical, response_record=response, causal_arrays=decode_matrix_arrays(causal_raw, causal.arrays),
            frozen_arrays=frozen.for_operand(frozen_raw, mechanical.arrays),
            response_arrays=decode_matrix_arrays(response_raw, response.arrays), panels=score_config.panels,
            numerical_status='SATISFIED' if readout.numerical_pass else 'UNEVALUABLE', feature=feature, score=readout,
            subject_id=source.source_id, group_id=source.root.root.independent_group_id, retain_instrument=True)
    return None


def _transport_products(writer, package, plan, tasks, receipts, entry, source,*,original_input_access=None,control_custody=None):
    from functools import partial as bind
    product=bind(_product,original_input_access=original_input_access) if original_input_access is not None else _product
    consumed=bind(_consumed,original_input_access=original_input_access) if original_input_access is not None else _consumed
    configuration=bind(_configuration,custody=control_custody) if control_custody is not None else _configuration
    """Follow the actual pre-future decision through response and score custody."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_future as future
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_records import MatrixPreparationHistory
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_prefix import MatrixPreparedCausalPrefix
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.prepared_point import MatrixPreparedPublicSource
    expected = (entry.transport_policy, entry.transport_calibration)
    ids = {phase: original.NAMESPACE + "." + source.source_id + "." + phase
        for phase in ("point", "mechanical", "response-score", "responses")}
    point_task, mechanical_task, score_task, response_task = (tasks[ids[phase]]
        for phase in ("point", "mechanical", "response-score", "responses"))
    point = decision = mechanical = readout = None
    cache = {}
    if point_task.task_id in receipts:
        point_config = configuration(writer, package.run_plan_id, point_task, (MatrixSelectedTransportPointConfig,))
        if ((point_config.transport_policy, point_config.transport_calibration) != expected
                or point_config.programme != entry.programme.identity
                or point_config.public_source != MatrixPreparedPublicSource.from_source(source)
                or point_task.capability.capability_key != original.capability_key("point", "2.0.0")):
            raise PermissionError("E6_ACTUAL_CAUSAL_POINT_CONFIGURATION_REQUIRED")
        point = product(writer, receipts, point_task, "product", original.FINAL_KINDS["points"])[0]
        decision = product(writer, receipts, point_task, "decision", MatrixE6TransportDecision)[0]
        cache[(point_task.task_id, "product", type(point))] = point
        cache[(point_task.task_id, "decision", type(decision))] = decision
    if mechanical_task.task_id in receipts:
        mechanical_config = configuration(writer, package.run_plan_id, mechanical_task, (original.MatrixSelectedPreparedConfig,))
        mechanical = product(writer, receipts, mechanical_task, "product", original.FINAL_KINDS["mechanicals"])[0]
        cache[(mechanical_task.task_id, "product", type(mechanical))] = mechanical
        causal = consumed(writer, receipts, tasks, mechanical_task, "causal", MatrixPreparedCausalPrefix, product_cache=cache)
        protocol = entry.programme.protocol(source)
        if (mechanical_config.phase != "mechanical" or mechanical_config.programme != entry.programme.identity
                or mechanical_config.public_source != MatrixPreparedPublicSource.from_source(source)
                or mechanical.source != source.identity or causal.source != source.identity
                or mechanical.causal != _pin(causal) or mechanical.arrays.preparation != causal.preparation
                or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or mechanical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
                or point is not None and point.feature.prefix != _pin(causal)):
            raise PermissionError("E6_ACTUAL_PARTIAL_MECHANICAL_ANCESTRY_REQUIRED")
    if response_task.task_id in receipts:
        response_config = configuration(writer, package.run_plan_id, response_task, (MatrixSelectedTransportFutureConfig,))
        if ((response_config.transport_policy, response_config.transport_calibration) != expected
                or response_config.programme != entry.programme.identity
                or response_config.source != source
                or response_task.capability.capability_key != original.capability_key("responses", "3.0.0")):
            raise PermissionError("E6_ACTUAL_DECISION_CONSUMING_RESPONSE_REQUIRED")
        if consumed(writer, receipts, tasks, response_task, "decision", MatrixE6TransportDecision,
                producer=point_task.task_id, output="decision", product_cache=cache) != decision:
            raise PermissionError("E6_EXACT_PRE_FUTURE_DECISION_RECEIPT_REQUIRED")
        response = product(writer, receipts, response_task, "product", future.MatrixSelectedFutureHistory)[0]
        cache[(response_task.task_id, "product", type(response))] = response
        history = consumed(writer, receipts, tasks, response_task, "history", MatrixPreparationHistory, product_cache=cache)
        causal = consumed(writer, receipts, tasks, response_task, "causal", MatrixPreparedCausalPrefix, product_cache=cache)
        future.validate_future_history(response_config, history, causal, point, mechanical, response)
        if response.native:
            from .recursive_qualified_parents import _prior_native_subwork
            from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorNativeBinding
            native, = response.native
            definition, completion, nested_receipt = native.definition, native.completion, native.receipt
            parent, receipt = definition.parent_contact, receipts[response_task.task_id]
            if (parent.run_id != package.run_plan_id or parent.task_id != response_task.task_id
                    or parent.attempt_id != receipt.attempt_id or parent.implementation_commit != receipt.implementation_commit
                    or parent.input_materialization_ids != receipt.input_materialization_ids
                    or parent.dependency_receipt_ids != tuple(sorted(receipts[key].receipt_id for key in response_task.dependency_task_ids))):
                raise PermissionError("E6_ACTUAL_NATIVE_PARENT_RECEIPT_REQUIRED")
            request = RecursivePriorNativeBinding(response_task.task_id, definition.identity,
                ObjectIdentity.from_record("completion." + definition.subwork_id, completion), _pin(nested_receipt, "receipt_id"))
            _prior_native_subwork(writer, SimpleNamespace(native_subwork=(request,),
                execution_plan=_pin(plan, "execution_plan_id"), run_id=package.run_plan_id), plan, receipts, task_index=tasks)
    if score_task.task_id in receipts:
        score_config = configuration(writer, package.run_plan_id, score_task, (MatrixSelectedTransportScoreConfig,))
        if ((score_config.transport_policy, score_config.transport_calibration) != expected
                or score_config.programme != entry.programme.identity
                or score_config.source != source
                or score_task.capability.capability_key != original.capability_key("response-score", "2.0.0")
                or response_task.task_id not in receipts or response_config != future.response_config_for(score_config)):
            raise PermissionError("E6_ACTUAL_DECISION_CONSUMING_SCORE_REQUIRED")
        if (consumed(writer, receipts, tasks, score_task, "decision", MatrixE6TransportDecision,
                producer=point_task.task_id, output="decision", product_cache=cache) != decision
                or consumed(writer, receipts, tasks, score_task, "responses", future.MatrixSelectedFutureHistory,
                    producer=response_task.task_id, product_cache=cache) != response):
            raise PermissionError("E6_SCORE_EXACT_ORIGINAL_DECISION_AND_RESPONSE_REQUIRED")
        readout = product(writer, receipts, score_task, "product", original.FINAL_KINDS["readouts"])[0]
    return (point, mechanical, readout), decision


def _transport_predicted_lifetimes(policy, cases, observations):
    """Display authenticated frozen points on their finite retained lattice.

    The caller already validated every actual point against ORIGINAL_E3. This
    projection changes no canonical record, primary result or qualification.
    A missing value before a later observed predicted failure prevents a
    complete first-failure or right-censoring statement.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import METHODS
    from empirical_lawhood.adapters.methods.matrix_factor_response.e3_numerical_methods import original_units

    rows = []
    descriptions = tuple(dict.fromkeys(description for description, _ in policy.endpoint_order))
    for case in cases:
        observation = observations.get(case.case_id)
        point = None if observation is None else observation[0]
        menu = None if point is None else dict(point.log_points)
        for description in descriptions:
            selected = tuple((index, horizon) for index, (name, horizon) in enumerate(policy.endpoint_order)
                if name == description)
            horizons = tuple(horizon for _, horizon in selected)
            for method in METHODS:
                missing = failure = None
                if menu is None:
                    status = "MISSING_POINT"
                else:
                    missing = next((horizon for index, horizon in selected if menu[method][index] is None), None)
                    failure = next((horizon for index, horizon in selected if menu[method][index] is not None
                        and original_units(menu[method][index]) > policy.criterion.normalized_error_maximum), None)
                    status = ("FORECAST_NONUSE" if missing is not None and (failure is None or missing < failure)
                        else "PREDICTED_FAILURE" if failure is not None else "RIGHT_CENSORED")
                rows.append({"case_id": case.case_id, "description": description, "method": method,
                    "status": status, "horizon_ticks": list(horizons), "first_missing_horizon": missing,
                    "first_observed_predicted_failure_horizon": failure,
                    "right_censored_through_horizon": horizons[-1] if status == "RIGHT_CENSORED" else None})
    return {"scope": "DECLARED_FINITE_HORIZON_LATTICE",
        "standing": "DESCRIPTIVE_FROZEN_POINTS_WITHOUT_CONTINUOUS_LIFETIME_OR_QUALIFICATION", "rows": rows}


def _transport_science(writer, package, plan, receipts, entry_task, entry, *, partial,original_input_access=None,control_custody=None):
    from functools import partial as bind
    product=bind(_product,original_input_access=original_input_access) if original_input_access is not None else _product
    consumed=bind(_consumed,original_input_access=original_input_access) if original_input_access is not None else _consumed
    configuration=bind(_configuration,custody=control_custody) if control_custody is not None else _configuration
    programme = entry.programme
    tasks = {task.task_id: task for task in plan.tasks}
    task_id = original.global_node(programme, "assess-programme")
    terminal = tasks[task_id]
    entry_product = None
    if entry_task.task_id in receipts:
        entry_product = product(writer, receipts, entry_task, "product", original.OUTPUTS["entry"])[0]
        if entry_product != entry_seal(programme):
            raise PermissionError("E6_ACTUAL_SUCCESSFUL_ENTRY_SEAL_REQUIRED")
    elif receipts:
        raise PermissionError("E6_RETAINED_PRODUCTS_REQUIRE_THEIR_SUCCESSFUL_ENTRY")
    observations, decisions = {}, {}
    expected_inputs = {"entry"}
    for _, source in programme.sources.source_arms():
        observation, decision = _transport_products(writer, package, plan, tasks, receipts, entry, source,original_input_access=original_input_access,control_custody=control_custody)
        case_id = "case." + source.source_id
        observations[case_id] = observation
        if decision is not None:
            decisions[case_id] = decision
        for port, phase, output in (("points", "point", "product"), ("mechanicals", "mechanical", "product"),
                ("readouts", "response-score", "product"), ("decisions", "point", "decision")):
            name = port + "." + source.source_id
            expected_inputs.add(name)
            edges = tuple(edge for edge in terminal.scientific_inputs if edge.consumer_input_id == name)
            producer = tasks[original.NAMESPACE + "." + source.source_id + "." + phase]
            if (len(edges) != 1 or edges[0].producer_task_id != producer.task_id
                    or edges[0].producer_output_id != producer.task_id + "." + output
                    or edges[0].operational_logical_artifact_id != next(row.logical_artifact_id for row in producer.outputs
                        if row.output_id == edges[0].producer_output_id)):
                raise PermissionError("E6_COMPLETE_ACTUAL_TERMINAL_DECISION_CENSUS_REQUIRED")
    science_edges=_science_edges(terminal)
    if (len(science_edges) != len(expected_inputs)
            or {edge.consumer_input_id for edge in science_edges} != expected_inputs
            or terminal.capability.capability_key != original.capability_key("assess-programme", "2.0.0")):
        raise PermissionError("E6_COMPLETE_ACTUAL_TERMINAL_INPUT_CENSUS_REQUIRED")
    final = configuration(writer, package.run_plan_id, terminal, (MatrixSelectedTransportRootConfig,))
    if (final.phase != "assess-programme" or final.programme != programme
            or (final.transport_policy, final.transport_calibration) != (entry.transport_policy, entry.transport_calibration)):
        raise PermissionError("E6_EXACT_TERMINAL_POLICY_AND_ORIGINAL_CALIBRATION_REQUIRED")
    manifest, assessment = assess_e6_transport(programme, entry.transport_policy, entry.transport_calibration,
        observations, decisions, result_id="result." + task_id)
    products, custody = {"manifest": manifest, "assessment": assessment}, {}
    adjudication = None
    if not partial:
        if consumed(writer, receipts, tasks, terminal, "entry", original.OUTPUTS["entry"], producer=entry_task.task_id,
                product_cache={(entry_task.task_id, "product", original.OUTPUTS["entry"]): entry_product}) != entry_product:
            raise PermissionError("E6_ACTUAL_SUCCESSFUL_ENTRY_REQUIRED")
        for name, output, kind in (("manifest", "manifest", MatrixE6TransportManifest),
                ("assessment", "product", MatrixE6EmpiricalTransportAssessment),
                ("adjudication", "adjudication", ScientificAdjudicationRecord)):
            actual, custody[name] = product(writer, receipts, terminal, output, kind)
            if name in products and actual != products[name]:
                raise PermissionError("E6_EXACT_COMPLETE_TERMINAL_REDUCTION_REQUIRED")
            products[name] = actual
        receipt = receipts[task_id]
        adjudication = ScientificAdjudicationRecord("adjudication." + task_id, package.run_plan_id, task_id,
            _pin(plan, "execution_plan_id"), receipt.input_materialization_ids,
            tuple(sorted(row.logical_artifact_id for row in terminal.outputs)),
            tuple(sorted(receipts[parent].receipt_id for parent in terminal.dependency_task_ids)), package.system.world.world_id,
            package.system.world.kind, _pin(package.experiment.relation, "relation_id"), package.experiment.independent_unit_id,
            tuple(_pin(cutoff, "cutoff_id") for cutoff in package.experiment.information_cutoffs),
            VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED, AdjudicationEvaluability.UNEVALUABLE,
            ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE,
            ("E6_EMPIRICAL_TRANSPORT_WITHOUT_TRANSPORTED_QUALIFICATION",))
        if package.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR or products["adjudication"] != adjudication:
            raise PermissionError("E6_EXACT_TERMINAL_ADJUDICATION_REQUIRED")
    return {**{name: value.to_document() for name, value in products.items()},
        "adjudication": None if adjudication is None else adjudication.to_document(),
        "denominators": {row.comparison_id: {"assigned_units": len(row.assigned_group_ids), "units": list(row.assigned_group_ids),
            "usable_groups": row.usable_groups, "admitted_groups": row.admitted_groups,
            "joint_service_successes": row.successes, "false_admissions_known": row.false_admissions_known,
            "false_admissions_unresolved": row.false_admissions_unresolved,
            "whole_menu_covered": row.covered_groups, "unavailable_coverage": row.unavailable_coverage_groups,
            "vacuous_coverage": row.vacuous_coverage_groups} for row in assessment.comparisons},
        "custody": custody, "phase": programme.phase, "scientific_status": "UNASSESSED" if partial else "UNEVALUABLE",
        "admission_status": "UNASSESSED" if partial else "UNEVALUABLE", "evaluability": "PARTIAL" if partial else "UNEVALUABLE",
        "qualification": assessment.qualification, "reason_codes": ["E6_EMPIRICAL_TRANSPORT_WITHOUT_TRANSPORTED_QUALIFICATION"],
        "downstream_uncertainty": "EMPIRICALLY_ASSESSED_OUTSIDE_ORIGINAL_DOMAIN",
        "assessment_custody": "UNPUBLISHED_PARTIAL_REDUCTION" if partial else "ACTUAL_TERMINAL_RECEIPT",
        "predicted_lifetimes": _transport_predicted_lifetimes(entry.transport_policy, assessment.cases, observations),
        "programme": programme.identity.to_document()}


def _partial_matched_revision_science(writer, package, plan, receipts, entry_task, entry, original_allocation, *,
        original_input_access=None, control_custody=None):
    """Retain receipted admissions when their future readout is still absent."""
    from functools import partial
    programme = entry.programme
    if not programme.criterion.is_matched or programme.phase not in ('E5_CONFIRMATION', 'E6_TRANSFER'):
        raise PermissionError('MATCHED_PARTIAL_SCIENCE_REQUIRES_ORIGINAL_PROTECTED_PROGRAMME')
    tasks = {task.task_id: task for task in plan.tasks}
    terminal = tasks[revision.global_node(programme, 'assess-programme')]
    product = partial(_product, original_input_access=original_input_access)
    consumed = partial(_consumed, original_input_access=original_input_access)
    final = _configuration(writer, package.run_plan_id, terminal, (revision.MatrixRevisionRootConfig,), custody=control_custody)
    if (final.phase != 'assess-programme' or final.programme != programme
            or terminal.capability.capability_key != revision.capability_key('assess-programme', 'PROTECTED')):
        raise PermissionError('MATCHED_PARTIAL_SCIENCE_EXACT_TERMINAL_PROGRAMME_REQUIRED')
    if entry_task.task_id in receipts:
        if (consumed(writer, receipts, tasks, terminal, 'entry', revision.OUTPUTS['entry'], producer=entry_task.task_id)
                != revision_entry_seal(programme)
                or consumed(writer, receipts, tasks, terminal, 'original-allocation', UnitAllocation,
                    producer=entry_task.task_id, output='original-allocation') != original_allocation):
            raise PermissionError('MATCHED_PARTIAL_SCIENCE_ORIGINAL_ENTRY_AND_ALLOCATION_REQUIRED')
    elif receipts:
        raise PermissionError('MATCHED_PARTIAL_SCIENCE_RETAINED_PRODUCTS_REQUIRE_SUCCESSFUL_ENTRY')
    observations, custody = {}, {}
    mechanism = {}
    expected_inputs = {'entry', 'original-allocation'}
    for _, source in programme.source_arms():
        producers = {}
        for port, phase in (('points', 'point'), ('mechanicals', 'mechanical'), ('readouts', 'response-score')):
            name = port + '.' + source.source_id
            expected_inputs.add(name)
            producers[port] = _consumed_producer(tasks, terminal, name,
                producer=revision.NAMESPACE + '.' + source.source_id + '.' + phase)
        case_id = 'case.' + source.source_id
        point_present = producers['points'].task_id in receipts
        if not point_present:
            if producers['readouts'].task_id in receipts:
                raise PermissionError('MATCHED_PARTIAL_FUTURE_REQUIRES_ITS_ORIGINAL_POINT')
            observations[case_id] = None
            continue
        if producers['mechanicals'].task_id not in receipts:
            raise PermissionError('MATCHED_PARTIAL_POINT_REQUIRES_ITS_ORIGINAL_MECHANICS')
        values = []
        for port in ('points', 'mechanicals', 'readouts'):
            producer = producers[port]
            if producer.task_id not in receipts:
                values.append(None)
            else:
                value, location = product(writer, receipts, producer, 'product', revision.FINAL_KINDS[port])
                values.append(value)
                custody[case_id + '.' + port] = location
        observation = tuple(values)
        mechanism[case_id] = _replay_matched_revision_case(writer, package.run_plan_id, programme, source, observation, tasks, receipts,
            original_input_access=original_input_access, control_custody=control_custody, allow_missing_future=True)
        observations[case_id] = observation
    edges = _science_edges(terminal)
    if len(edges) != len(expected_inputs) or {edge.consumer_input_id for edge in edges} != expected_inputs:
        raise PermissionError('MATCHED_PARTIAL_SCIENCE_COMPLETE_ORIGINAL_INPUT_CENSUS_REQUIRED')
    manifest, assessment = assess_revision_programme(programme, observations, result_id='result.' + terminal.task_id,
        original_allocation=original_allocation)
    if terminal.task_id in receipts:
        if (product(writer, receipts, terminal, 'manifest', revision.MatrixRevisionManifest)[0] != manifest
                or product(writer, receipts, terminal, 'product', revision.MatrixRevisionProgrammeAssessment)[0] != assessment):
            raise PermissionError('MATCHED_PARTIAL_SCIENCE_CHANGES_RETAINED_TERMINAL_REDUCTION')
    groups = (revision_transfer_regimes(programme, original_allocation) if programme.phase == 'E6_TRANSFER' else
        (('confirmation', tuple(sorted({case.unit_id for case in programme.roster.cases}))),))
    denominators = {role: {'assigned_units': len(units), 'units': list(units),
        'assigned_cases': sum(case.unit_id in units for case in assessment.functional.cases),
        'assessed_cases': sum(case.functional.unit_id in units and case.readout is not None for case in assessment.cases),
        'conditionally_admitted_cases': sum(case.unit_id in units and case.conditional_admission for case in assessment.functional.cases)}
        for role, units in groups}
    from .matrix_mechanism_read import prepared_mechanism_projection
    return {'manifest': manifest.to_document(), 'assessment': assessment.to_document(), 'adjudication': None,
        **prepared_mechanism_projection(programme, mechanism),
        'assessment_custody': 'UNPUBLISHED_PARTIAL_REDUCTION', 'custody': custody, 'denominators': denominators,
        'secondary_all_horizon_readout': prepared_secondary_projection(programme, observations, groups),
        'phase': programme.phase, 'scientific_status': 'UNASSESSED', 'admission_status': 'UNASSESSED',
        'evaluability': 'PARTIAL', 'qualification': 'NOT_ESTABLISHED',
        'reason_codes': ['PARTIAL_FROZEN_PREDICTIONS_AND_UNKNOWN_FUTURES_NO_QUALIFICATION'],
        'downstream_uncertainty': 'EMPIRICALLY_ASSESSED_FROZEN_E4_TRANSPORT_NO_GUARANTEE',
        'response_adequacy_interpretation': 'SAMPLED_RESPONSE_NOT_IDENTICAL_PHYSICAL_TASK_OR_EXTERNAL_SERVICE',
        'external_delivered_task': 'NOT_SELECTED', 'programme': programme.identity.to_document()}


def _terminal_science(writer, package, plan, receipts, entry_task, entry, is_revision, original_allocation,*,original_input_access=None,control_custody=None):
    from functools import partial as bind
    product=bind(_product,original_input_access=original_input_access) if original_input_access is not None else _product
    consumed=bind(_consumed,original_input_access=original_input_access) if original_input_access is not None else _consumed
    configuration=bind(_configuration,custody=control_custody) if control_custody is not None else _configuration
    if type(entry) is MatrixSelectedTransportRootConfig:
        return _transport_science(writer, package, plan, receipts, entry_task, entry, partial=False,original_input_access=original_input_access,control_custody=control_custody)
    owner = revision if is_revision else original
    programme = entry.programme
    task_id = owner.global_node(programme, "assess-programme")
    tasks = {task.task_id: task for task in plan.tasks}
    task = tasks.get(task_id)
    expected_key = (revision.capability_key("assess-programme", "PROTECTED") if is_revision else
        original.capability_key("assess-programme", "1.0.0"))
    if task is None or task.capability.capability_key != expected_key:
        raise PermissionError("SELECTED_SCIENCE_ACTUAL_TERMINAL_ASSESSOR_REQUIRED")
    final = configuration(writer, package.run_plan_id, task,
        (revision.MatrixRevisionRootConfig,) if is_revision else (original.MatrixSelectedProtectedRootConfig,))
    if final.phase != "assess-programme" or final.programme != programme:
        raise PermissionError("SELECTED_SCIENCE_EXACT_TERMINAL_PROGRAMME_REQUIRED")
    seal = consumed(writer, receipts, tasks, task, "entry", owner.OUTPUTS["entry"], producer=entry_task.task_id)
    if seal != (revision_entry_seal(programme) if is_revision else entry_seal(programme)):
        raise PermissionError("SELECTED_SCIENCE_ACTUAL_SPENT_ENTRY_REQUIRED")
    rows = programme.source_arms() if is_revision else programme.sources.source_arms()
    expected_inputs = {"entry"}
    if is_revision:
        allocation = consumed(writer, receipts, tasks, task, "original-allocation", UnitAllocation,
            producer=entry_task.task_id, output="original-allocation")
        if allocation != original_allocation:
            raise PermissionError("SELECTED_SCIENCE_EXACT_AUTHENTICATED_ORIGINAL_ALLOCATION_REQUIRED")
        expected_inputs.add("original-allocation")
    observations, mechanism = {}, {}
    for _, source in rows:
        names = tuple(port + "." + source.source_id for port in ("points", "mechanicals", "readouts"))
        observations["case." + source.source_id] = tuple(consumed(writer, receipts, tasks, task, name, owner.FINAL_KINDS[port])
            for name, port in zip(names, ("points", "mechanicals", "readouts"), strict=True))
        if is_revision and programme.criterion.is_matched:
            mechanism['case.' + source.source_id] = _replay_matched_revision_case(writer, package.run_plan_id, programme, source, observations["case." + source.source_id], tasks, receipts,
                original_input_access=original_input_access, control_custody=control_custody)
        expected_inputs.update(names)
    science_edges=_science_edges(task)
    if len(science_edges) != len(expected_inputs) or {edge.consumer_input_id for edge in science_edges} != expected_inputs:
        raise PermissionError("SELECTED_SCIENCE_COMPLETE_TERMINAL_INPUT_CENSUS_REQUIRED")
    replay = (assess_revision_programme(programme, observations, result_id="result." + task_id, original_allocation=original_allocation)
        if is_revision else assess_selected_programme(programme, observations, result_id="result." + task_id))
    kinds = ((revision.MatrixRevisionManifest, revision.MatrixRevisionProgrammeAssessment) if is_revision else
        (original.MatrixSelectedProtectedManifest, original.MatrixFunctionalAssessment))
    products, custody = {}, {}
    for name, kind in zip(("manifest", "assessment", "adjudication"), (*kinds, ScientificAdjudicationRecord), strict=True):
        products[name], custody[name] = product(writer, receipts, task, "product" if name == "assessment" else name, kind)
    if (products["manifest"], products["assessment"]) != replay:
        raise PermissionError("SELECTED_SCIENCE_EXACT_COMPLETE_TERMINAL_REDUCTION_REQUIRED")
    receipt = receipts[task_id]
    if package.system.world.kind is not WorldKind.NUMERICAL_SIMULATOR:
        raise PermissionError("SELECTED_SCIENCE_ACTUAL_NUMERICAL_WORLD_REQUIRED")
    expected = ScientificAdjudicationRecord("adjudication." + task_id, package.run_plan_id, task_id,
        _pin(plan, "execution_plan_id"), receipt.input_materialization_ids,
        tuple(sorted(row.logical_artifact_id for row in task.outputs)),
        tuple(sorted(receipts[parent].receipt_id for parent in task.dependency_task_ids)), package.system.world.world_id,
        package.system.world.kind, _pin(package.experiment.relation, "relation_id"), package.experiment.independent_unit_id,
        tuple(_pin(cutoff, "cutoff_id") for cutoff in package.experiment.information_cutoffs),
        VisibilityCeiling.OUTCOME_VISIBLE, OutcomeAccess.EVALUATION_REVEALED, AdjudicationEvaluability.UNEVALUABLE,
        ScientificStatus.UNEVALUABLE, AdmissionStatus.UNEVALUABLE,
        (("EMPIRICAL_RESPONSE_INFERENCE_DOES_NOT_ESTABLISH_SAMPLING_QUALIFICATION_OR_TRANSPORT_GUARANTEE",)
            if is_revision and programme.criterion.is_matched else ("DOWNSTREAM_PREPARATION_OR_TRANSFER_CALIBRATION_APPLICABILITY_NOT_ESTABLISHED",)))
    if products["adjudication"] != expected:
        raise PermissionError("SELECTED_SCIENCE_EXACT_TERMINAL_ADJUDICATION_REQUIRED")
    assessment = products["assessment"]
    functional = assessment.functional if is_revision else assessment
    sources = {"case." + source.source_id: source for _, source in rows}
    panels = dict(programme.panels)
    native_cases = tuple(native_functional_case(programme.criterion, case, sources[case.case_id],
        observations[case.case_id][2], protocol=programme.protocol(sources[case.case_id]), panels=panels[case.unit_id])
        for case in programme.roster.cases)
    groups = (("confirmation", tuple(sorted({case.unit_id for case in programme.roster.cases}))),) if programme.phase == "E5_CONFIRMATION" else (
        revision_transfer_regimes(programme, original_allocation) if is_revision else tuple(
            (role, programme.point_design.package.allocation.unit_ids(role)) for role in ("transfer_nearby", "transfer_shifted")))
    denominators = {}
    for role, unit_ids in groups:
        cases = tuple(row for row in functional.cases if row.unit_id in unit_ids)
        native = tuple(row for row in native_cases if row.unit_id in unit_ids)
        denominators[role] = {"assigned_units": len(unit_ids), "units": list(unit_ids), "assigned_cases": len(cases),
            "case_dispositions": {state: sum(row.disposition == state for row in cases)
                for state in ("FINITE", "UNEVALUABLE", "NONUSE", "MISSING")},
            "native_functional_usable_cases": sum(row.actual_error is not None for row in native),
            "native_functional_reliable_cases": sum(row.functional_reliable for row in native),
            "conditionally_admitted_cases": sum(row.conditional_admission for row in cases)}
    from .matrix_mechanism_read import prepared_mechanism_projection
    return {**{name: value.to_document() for name, value in products.items()},
        **(prepared_mechanism_projection(programme, mechanism) if is_revision else {}),
        "native_functional_diagnostic": {"scope": "NATIVE_ASSAY_ONLY_NO_POINT_OR_ADMISSION_CLAIM",
            "criterion": programme.criterion.to_document(), "roster": programme.roster.identity.to_document(),
            "cases": tuple(row.to_document() for row in native_cases),
            "readouts": tuple((case.case_id, _pin(observations[case.case_id][2]).to_document())
                for case in programme.roster.cases)},
        "secondary_all_horizon_readout": prepared_secondary_projection(programme, observations, groups),
        "denominators": denominators, "custody": custody, "phase": programme.phase,
        "scientific_status": expected.scientific_status.value, "admission_status": expected.admission_status.value,
        "evaluability": expected.evaluability.value, "qualification": functional.qualification,
        "reason_codes": list(expected.reason_codes), "downstream_uncertainty": (
            "EMPIRICALLY_ASSESSED_FROZEN_E4_TRANSPORT_NO_GUARANTEE" if programme.criterion.is_matched else "NOT_ESTABLISHED"),
        "response_adequacy_interpretation": "SAMPLED_RESPONSE_NOT_IDENTICAL_PHYSICAL_TASK_OR_EXTERNAL_SERVICE" if programme.criterion.is_matched else "DECLARED_ORIGINAL_CRITERION",
        "external_delivered_task": "NOT_SELECTED" if programme.criterion.is_matched else "UNESTABLISHED",
        "programme": programme.identity.to_document()}



class _CurrentPreparedScientificRead:
    """Fresh original and own-outcome grants for already joined result facts."""
    def __init__(self,writer,original,binding,package):
        self.writer,self.original,self.binding,self.package=writer,original,binding,package

    def require_current(self,*,artifact_writer=None):
        from .selected_prepared_access import _ordinary
        from .recursive_qualified_parents import _require_parent_authorities_current
        writer=_ordinary(self.writer if artifact_writer is None else artifact_writer)
        if writer.root.contract!=self.writer.root.contract:
            raise PermissionError('prepared scientific read changes its actual guarded root')
        if self.original is not None:self.original.require_current(artifact_writer=writer)
        _require_parent_authorities_current(((self.binding,self.package),),writer)

    def require_member(self,manifest):
        if self.original is None:
            raise PermissionError('prepared result sibling lacks an exact known scientific receipt')
        self.original.require_issued_member(manifest)
        self.require_current()

def read_selected_protected_result(*, selected, artifact_writer, run_id, reveal_authority_id=None, allow_partial=False,read_access=None):
    """Reopen actual protected science; a later read reauthenticates all grants."""
    validate_stable_id(run_id)
    if type(allow_partial) is not bool:
        raise TypeError("selected protected read requires an explicit partial selection")
    access=getattr(selected,"original_input_access",None)
    if access is not None:
        if access.current_access!=read_access:raise PermissionError("selected protected read changes its operation-local original access")
        access.require_current()
    elif read_access is not None:raise PermissionError("selected protected read lacks its original input bootstrap")
    specification, allocation = _design(selected)
    # This lifetime contains static controls only. Receipt and scientific bytes
    # do not repeatedly extend its verification snapshot.
    with artifact_writer.read_context() as controls:
        reader = CurrentResultPlanReader(controls)
        package = _actual_package(controls, run_id, control_reader=reader)
        if (_pin(package.issued_study.candidate, "candidate_id") != selected.association.candidate
                or package.issued_study.source_closure != selected.implementation or package.run_plan_id != run_id):
            raise PermissionError("SELECTED_SCIENCE_ORIGINAL_CANDIDATE_SOURCE_AND_RUN_REQUIRED")
        reveal = None
        if not allow_partial:
            if reveal_authority_id is None:
                raise PermissionError("SELECTED_SCIENCE_CURRENT_REVEAL_REQUIRED")
            validate_stable_id(reveal_authority_id)
            reveal = ExternalStudyOperationAuthorityStore(artifact_writer).load(reveal_authority_id)
            binding = SimpleNamespace(issued_study=_pin(package.issued_study, "issue_id"),
                execution_authority=_pin(package.execution_authority, "authority_id"), reveal_authority=_pin(reveal, "authority_id"))
            issued, reveal = _replay_parent_authority(binding, package, artifact_writer)
        else:
            issued = package.issued_study
        plan = reader.authenticate_execution_plan(package=package, issued=issued, run_id=run_id)
        if {task.task_id for task in plan.tasks} != {task.task_id for task in selected.projection.tasks}:
            raise PermissionError("SELECTED_SCIENCE_COMPLETE_ORIGINAL_TASK_CENSUS_REQUIRED")
        transport = any(task.capability.capability_key == ENTRY_TRANSPORT_KEY for task in plan.tasks)
        matched_revision = specification.account == 'REVISION' and specification.criterion.is_matched
        if allow_partial and not (transport or matched_revision):
            return {"scientific_status": "UNASSESSED", "admission_status": "UNASSESSED", "evaluability": "DEFERRED",
                "qualification": "NOT_ESTABLISHED", "reason_codes": ["PARTIAL_READ_SCIENTIFIC_ASSESSMENT_DEFERRED"],
                "denominators": {regime: {"assigned_units": len(ids), "units": ids, "assessed_units": None}
                    for regime in sorted({unit.family_id for unit in allocation.units})
                    for ids in ([unit.unit_id for unit in allocation.units if unit.family_id == regime],)},
                "assessment": None, "manifest": None, "adjudication": None,
                "assigned_tasks": len(plan.tasks), "typed_product_validation": "DEFERRED",
                "scientific_completion": "NOT_ESTABLISHED", "new_native_contact_count": 0}
        if allow_partial:
            # Expanded E6 may retain a causal admission before a failed future.
            # Replaying that partial science requires the same current grants
            # as complete outcome reading, and creates no terminal publication.
            if reveal_authority_id is None:
                raise PermissionError("E6_PARTIAL_SCIENCE_CURRENT_REVEAL_REQUIRED")
            validate_stable_id(reveal_authority_id)
            reveal = ExternalStudyOperationAuthorityStore(artifact_writer).load(reveal_authority_id)
            binding = SimpleNamespace(issued_study=_pin(package.issued_study, "issue_id"),
                execution_authority=_pin(package.execution_authority, "authority_id"), reveal_authority=_pin(reveal, "authority_id"))
            issued, reveal = _replay_parent_authority(binding, package, artifact_writer)
        from empirical_lawhood.api.recursive_operations import operation_catalog
        codecs = operation_catalog()[2]
        semantic = retained_output_artifact_plane(package, plan, artifact_writer, codecs)
        prefixes = tuple(sorted(manifest.capability_key for manifest in package.registry.capabilities))
        closure = reader.collect_receipt_closure(package=package, execution_plan=plan,
            reveal=reveal, capability_prefixes=prefixes, allow_partial=allow_partial)
        controls.require_verification_snapshot()
        # Fresh scientific source/producer/commitment authentication stays separate
        # from the completed campaign and from the point-only terminal adjudication.
        scientific_access=_CurrentPreparedScientificRead(artifact_writer,access,binding,package)
        scientific_access.require_current()
        from .current_task_custody import CurrentIssuedTaskCustody
        control_custody=CurrentIssuedTaskCustody(writer=semantic,reveal_authority_id=reveal_authority_id,original_input_access=access)
        with control_custody.retained_binding(package=package, execution_plan=plan,
                control_reader=reader, receipt_closure=closure,
                require_current_read=scientific_access.require_current):
            entry_task, entry, is_revision = _entry(semantic, run_id, plan,custody=control_custody)
            _validate_design(selected, specification, allocation, entry, is_revision)
            _current_source_qualifications(package, entry_task)
            evidence = _entry_evidence(semantic, run_id, entry_task, entry, is_revision,custody=control_custody)
            original_allocation = _original_source_operands(semantic, entry, evidence, is_revision, codecs,
                source_scan_bytes=entry_task.capability.requested_resources.source_scan_bytes,current_access=read_access)
            with semantic.read_context() as writer:
                receipts = _verify_receipt_closure(writer, closure)
                if allow_partial and matched_revision:
                    result = _partial_matched_revision_science(writer, package, plan, receipts, entry_task, entry, original_allocation,
                        original_input_access=scientific_access, control_custody=control_custody)
                else:
                    result = (_transport_science(writer, package, plan, receipts, entry_task, entry, partial=True,original_input_access=scientific_access,control_custody=control_custody) if allow_partial else
                        _terminal_science(writer, package, plan, receipts, entry_task, entry, is_revision, original_allocation,original_input_access=scientific_access,control_custody=control_custody))
                writer.require_verification_snapshot()
            scientific_access.require_current(artifact_writer=artifact_writer)
            point_package = entry.programme.selected_package if is_revision else entry.programme.point_design.package
            commitments = getattr(evidence, "original_commitments", None)
            result = {**result, "execution_plan": _pin(plan, "execution_plan_id").to_document(), "completed_tasks": len(receipts),
                "source_qualification": {"specification": evidence.source_specification.to_document(),
                    "result": evidence.source_result.to_document(), "pipeline_receipt": evidence.pipeline.receipt.to_document()},
                "frozen_point_package": _pin(point_package).to_document(),
                "original_commitments": None if commitments is None else commitments.identity.to_document(),
                "original_commitment_scope": "HISTORICAL_NOT_SUPPLIED" if commitments is None else "AUTHENTICATED_ORIGINALS",
                "typed_product_validation": "COMPLETE_FOR_RETAINED_RECEIPTS" if allow_partial else "COMPLETE",
                "scientific_completion": "UNPUBLISHED_PARTIAL_ASSESSMENT" if allow_partial else "RETAINED_ADJUDICATION",
                "new_native_contact_count": 0}
    scientific_access.require_current(artifact_writer=artifact_writer)
    return result
