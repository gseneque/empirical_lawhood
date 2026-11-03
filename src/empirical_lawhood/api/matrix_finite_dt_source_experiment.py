# SPDX-License-Identifier: MPL-2.0
"""Owning public preparation, issued binding and actual finite-dt source reads."""
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.methods import matrix_finite_dt_source_experiment as domain
from empirical_lawhood.adapters.methods import matrix_finite_dt_source_records as r
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
from empirical_lawhood.api.matrix_finite_dt_source_runtime import (
    _authenticate_bank_publications, authenticate_instrument_certificate, bind_finite_dt_source_handoff)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs


def _selection(specification, allocation, draft, source_records):
    domain.validate_instance(specification=specification, allocation=allocation, draft=draft, source_records=source_records)
    selected, = (value for _, value in source_records if type(value) in domain.selection_types())
    return selected


def pipeline_evidence(selection):
    """Pure original owner operands; actual producing receipts are separate."""
    _, _, qualification, result = domain.lower(selection)
    evidence = MatrixSourcePipelineEvidence("pipeline-evidence." + selection.scope.record_id,
        selection.pipeline, selection.scope.pipeline_receipt, qualification, selection.scope.evidence_profile)
    return evidence, result


def authenticate_selection(*, writer, selection, control_reader=None):
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import authenticate_finite_dt_source_materialization
    from empirical_lawhood.api.matrix_source_runtime import (
        _authenticate_source_publication, matrix_source_publication_references)
    selection.__post_init__()
    _authenticate_bank_publications(writer, selection.bank, selection.exposure_support)
    authenticate_instrument_certificate(writer=writer, certificate=selection.certificate,
        programme=selection.programme, bank=selection.bank,
        original_future_reservation=selection.original_future_reservation, control_reader=control_reader)
    evidence, result = pipeline_evidence(selection)
    authenticate_finite_dt_source_materialization(writer=writer, programme=selection.programme,
        bank=selection.bank, rows=selection.rows, rule=selection.rule, pipeline=evidence,
        source_publication=selection.source_publication, output_publication=selection.output_publication,
        verification=selection.verification, verification_publication=selection.verification_publication)
    expected = set(matrix_source_publication_references(evidence.qualification_config.specification, result, evidence))
    for pin, publication in selection.metadata_publications:
        if pin not in expected:
            raise PermissionError("finite-dt source adds an undeclared original metadata publication")
        _authenticate_source_publication(writer, pin, publication, evidence)
    return evidence, result


def prepare_finite_dt_source_authoring(preparation, *, project_root, artifact_writer, output_dir):
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.prospective_experiment import preview_prepared_prospective_experiment_candidate
    if (type(preparation) is not ExperimentPreparation
            or type(preparation.specification_record) not in domain.specification_types()
            or preparation.dependencies or preparation.execution is None or preparation.prospective_spec is None):
        raise PermissionError("finite-dt authoring requires its complete original public preparation")
    selected = _selection(preparation.specification_record, preparation.allocation,
        preparation.draft, preparation.design_records)
    if (preparation.prospective_spec != selected.authoring
            or preparation.source_configs != selected.source_configs
            or preparation.input_records != domain.lower(selected)[1]):
        raise PermissionError("finite-dt authoring changes its original scientific/resource/source selection")
    preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root), artifact_writer=artifact_writer)
    custody = CurrentIssuedTaskCustody(writer=artifact_writer)
    with custody.verification_scope():
        reader = custody._control_reader
        writer = artifact_writer if reader is None else reader.writer
        authenticate_selection(writer=writer, selection=selected, control_reader=reader)
    preview = preview_prepared_prospective_experiment_candidate(preparation=preparation,
        design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.authoring),
        source_configs=selected.source_configs, project_root=project_root, artifact_writer=artifact_writer)
    # The actual author/loader validates these unchanged selected resources;
    # preparation creates no issue, execution, reveal or scientific authority.
    return replace(preparation, prospective_candidate_preview=preview)


def bind_finite_dt_source_experiment(handoff, *, specification, allocation, source_records,
        artifact_writer, reveal_authority_id=None):
    selected = _selection(specification, allocation, handoff.compilation.draft, source_records)
    custody = CurrentIssuedTaskCustody(writer=artifact_writer)
    with custody.verification_scope():
        reader = custody._control_reader
        writer = artifact_writer if reader is None else reader.writer
        authenticate_selection(writer=writer, selection=selected, control_reader=reader)
    return bind_finite_dt_source_handoff(handoff, writer=artifact_writer, reveal_authority_id=reveal_authority_id)


def _retained_selection(selected):
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.runtime.prospective_experiment import (
        ALLOCATION_FILENAME, SPECIFICATION_FILENAME, source_filename)
    if len(selected.instance.sources) != 1:
        raise PermissionError("finite-dt source read requires one exact original selected input")
    source_pin, = selected.instance.sources
    source_kinds = {kind.SCHEMA: kind for kind in domain.selection_types()}
    source_kind = source_kinds.get(source_pin.object_schema)
    if source_kind is None:
        raise PermissionError("finite-dt source read changes its original selected input revision")
    specification = decode_canonical_bytes(selected.payloads[SPECIFICATION_FILENAME],
        domain.MatrixFiniteDtSourceQualificationSpecification,
        maximum_bytes=len(selected.payloads[SPECIFICATION_FILENAME]))
    allocation = decode_canonical_bytes(selected.payloads[ALLOCATION_FILENAME], UnitAllocation,
        maximum_bytes=len(selected.payloads[ALLOCATION_FILENAME]))
    records = []
    for pin in selected.instance.sources:
        if (pin.object_schema, pin.object_version) != (source_kind.SCHEMA, source_kind.VERSION):
            raise PermissionError("finite-dt source read changes its original selected input revision")
        raw = selected.payloads[source_filename(pin)]
        value = decode_canonical_bytes(raw, source_kind, maximum_bytes=len(raw))
        if value.identity != pin or value.canonical_bytes() != raw:
            raise PermissionError("finite-dt source read changes its original complete canonical selection")
        records.append((pin.object_id, value))
    return _selection(specification, allocation, selected.draft, tuple(records))


def _source_publications(*, writer, package, plan, selection, evidence, result):
    from empirical_lawhood.api.matrix_source_runtime import retained_source_publications
    return retained_source_publications(writer=writer, package=package, plan=plan,
        selection=selection, evidence=evidence, result=result)


def read_finite_dt_source_result(*, selected, artifact_writer, run_id, reveal_authority_id=None, allow_partial=False):
    from empirical_lawhood.api.current_result_custody import authenticate_current_execution_plan, retained_output_artifact_plane
    from empirical_lawhood.api.matrix_source_runtime import authenticate_matrix_source_qualification
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.recursive_qualified_parents import (
        _actual_package, _collect_receipt_closure, _ParentReadScope)
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    if type(allow_partial) is not bool:
        raise TypeError("finite-dt source read requires an explicit partial selection")
    selection = _retained_selection(selected)
    package = _actual_package(artifact_writer, run_id)
    if (package.run_plan_id != run_id or r.pin(package.issued_study.candidate, "candidate_id") != selected.association.candidate
            or package.issued_study.source_closure != selected.implementation):
        raise PermissionError("finite-dt source read changes its actual original issued run/candidate/source")
    # This pure plan correspondence creates no payload/authority verdict. Each
    # original source producer below replays its actual current execution grant.
    plan = authenticate_current_execution_plan(package=package, issued=package.issued_study,
        run_id=run_id, writer=artifact_writer)
    if {value.task_id for value in plan.tasks} != {value.task_id for value in selected.projection.tasks}:
        raise PermissionError("finite-dt source read changes its actual complete original task census")
    if allow_partial:
        return {"scientific_completion": "NOT_ESTABLISHED", "scientific_qualification": "NOT_ESTABLISHED",
            "source_premise": "DEFERRED", "new_native_contact_count": 0}
    codecs = operation_catalog()[2]
    semantic = retained_output_artifact_plane(package, plan, artifact_writer, codecs)
    with semantic.verification_scope() as writer:
        scope = _ParentReadScope(writer)
        evidence, result = authenticate_selection(writer=writer, selection=selection, control_reader=scope.plan_reader)
        expected = {domain.node_id(selection.scope, "pipeline"): (evidence.receipt, "receipt_id"),
            domain.node_id(selection.scope, "qualification"): (result, "result_id")}
        from empirical_lawhood.adapters.methods.matrix_finite_dt_source_bindings import gate_declaration
        for gate in result.gate_evidence:
            kind, = (value for value in r.GATES if gate.method.capability_key ==
                gate_declaration(value).capability_key)
            expected[domain.node_id(selection.scope, kind.value.lower())] = gate, "evidence_id"
        closure = _collect_receipt_closure(package, plan, writer, None,
            tuple(sorted(value.capability_key for value in package.registry.capabilities)))
        bindings = []
        for task_id, (product, field) in expected.items():
            receipt = closure.by_task[task_id]
            logical, = (value for value in receipt.output_logical_artifacts
                if (value.payload_schema, value.content_sha256) == (product.SCHEMA, product.fingerprint()))
            bindings.append(RecursivePriorExecutionBinding("binding." + task_id,
                r.pin(package.issued_study, "issue_id"), r.pin(package.execution_authority, "authority_id"),
                r.pin(package, "package_id"), r.pin(plan, "execution_plan_id"), run_id, task_id,
                r.pin(receipt, "receipt_id"), logical.logical_artifact_id,
                ObjectIdentity.from_record(getattr(product, field), product), record_id_field=field))
        executions = tuple(sorted(bindings, key=lambda value: value.record.object_id))
        publications = _source_publications(writer=writer, package=package, plan=plan,
            selection=selection, evidence=evidence, result=result)
        authenticate_matrix_source_qualification(writer=writer, specification=evidence.qualification_config.specification,
            result=result, pipeline=evidence, executions=executions, publications=publications,
            codecs=codecs, read_scope=scope)
        writer.require_verification_snapshot()
    return {"scientific_completion": "COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT",
        "scientific_qualification": "NOT_ESTABLISHED", "source_premise": result.disposition.value,
        "source_evidence_ceiling": "MEASUREMENT", "sampling": "NOT_ESTABLISHED", "transport": "NOT_ESTABLISHED",
        "qualification_specification": evidence.qualification_config.specification.to_document(),
        "qualification_result": result.to_document(), "pipeline_evidence": evidence.to_document(),
        "prior_executions": tuple(value.to_document() for value in executions),
        "publications": tuple((pin.to_document(), value.to_document()) for pin, value in publications),
        "new_native_contact_count": 0}
