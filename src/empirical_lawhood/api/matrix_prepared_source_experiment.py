# SPDX-License-Identifier: MPL-2.0
"""Owning public preparation, issued binding and actual finite-dt source reads."""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_support as current_exposure_support
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
from empirical_lawhood.adapters.methods import matrix_prepared_source_records as r
from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineEvidence
from empirical_lawhood.api.current_task_custody import CurrentIssuedTaskCustody
from .matrix_prepared_source_runtime import (
    authenticate_prepared_source_certificate, bind_prepared_source_handoff)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.experiment_preparation import ExperimentPreparation
from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs


def _authenticate_bank_publications(writer, bank, exposure_support):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    required = {artifact for artifact, _ in current_exposure_support(bank.audit)}
    if len(exposure_support) != len(required) or {value for value, _ in exposure_support} != required:
        raise PermissionError('prepared source omits its exact current census publication support')
    for artifact, custody in exposure_support:
        _authenticate_artifact(writer, artifact, custody)
    for publication, value in ((bank.reservation.publication, bank.reservation.allocation),
            (bank.specification.publication, bank.specification.selection), (bank.audit_publication, bank.audit)):
        authenticate_publication(writer, publication, value)
    originals = (bank.audit.census, *bank.audit.prior_scheduled_coordinates)
    for publication in bank.audit.prior_corpus:
        values = tuple(value for value in originals if (value.SCHEMA, value.fingerprint()) ==
            (publication.logical.payload_schema, publication.logical.content_sha256))
        if len(values) != 1:
            raise PermissionError('prepared source changes its actual retained prior-corpus publication')
        authenticate_publication(writer, publication, values[0])


def _selection(specification, allocation, draft, source_records):
    domain.validate_instance(specification=specification, allocation=allocation, draft=draft, source_records=source_records)
    selected, = (value for _, value in source_records if type(value) is domain.MatrixPreparedSourceQualificationSelection)
    return selected


def pipeline_evidence(selection):
    """Pure original owner operands; actual producing receipts are separate."""
    _, _, qualification, result = domain.lower(selection)
    evidence = MatrixSourcePipelineEvidence("pipeline-evidence." + selection.scope.record_id,
        selection.pipeline, selection.scope.pipeline_receipt, qualification, selection.scope.evidence_profile)
    return evidence, result


def authenticate_selection(*, writer, selection, control_reader=None, original_input_access=None):
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import authenticate_finite_dt_source_materialization
    from .matrix_source_runtime import (
        _authenticate_source_publication, matrix_source_publication_references)
    selection.__post_init__()
    _authenticate_bank_publications(writer, selection.bank, selection.exposure_support)
    authenticate_prepared_source_certificate(writer=writer, certificate=selection.certificate,
        bank=selection.bank, maximum_source_bytes=selection.scope.resource_budget.source_scan_bytes, control_reader=control_reader, original_input_access=original_input_access)
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


def prepare_prepared_source_authoring(preparation, *, project_root, artifact_writer, output_dir,
        read_access=None, original_input_access=None):


    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from .prospective_experiment import preview_prepared_prospective_experiment_candidate
    if (type(preparation) is not ExperimentPreparation
            or type(preparation.specification_record) is not domain.MatrixPreparedSourceQualificationSpecification
            or preparation.dependencies or preparation.execution is None or preparation.prospective_spec is None):
        raise PermissionError("finite-dt authoring requires its complete original public preparation")
    from .prepared_source_access import require_prepared_source_scope
    access = require_prepared_source_scope(original_input_access, preparation.specification_record, read_access)
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
        authenticate_selection(writer=writer, selection=selected, control_reader=reader, original_input_access=access)
    preview = preview_prepared_prospective_experiment_candidate(preparation=preparation,
        design_inputs=RecursiveProspectiveDesignInputs.from_spec(selected.authoring),
        source_configs=selected.source_configs, project_root=project_root, artifact_writer=artifact_writer,
        read_access=read_access, original_input_access=access)
    # The actual author/loader validates these unchanged selected resources;
    # preparation creates no issue, execution, reveal or scientific authority.
    access.require_current()
    return replace(preparation, prospective_candidate_preview=preview)


def bind_prepared_source_experiment(handoff, *, specification, allocation, source_records,
        artifact_writer, reveal_authority_id=None, read_access=None, original_input_access=None):


    from .prepared_source_access import require_prepared_source_scope
    access = require_prepared_source_scope(original_input_access, specification, read_access)
    selected = _selection(specification, allocation, handoff.compilation.draft, source_records)
    custody = CurrentIssuedTaskCustody(writer=artifact_writer)
    with custody.verification_scope():
        reader = custody._control_reader
        writer = artifact_writer if reader is None else reader.writer
        authenticate_selection(writer=writer, selection=selected, control_reader=reader, original_input_access=access)
    access.require_current()
    return bind_prepared_source_handoff(handoff, writer=artifact_writer, reveal_authority_id=reveal_authority_id,
        original_input_access=access)


def _retained_selection(selected):
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.runtime.prospective_experiment import (
        ALLOCATION_FILENAME, SPECIFICATION_FILENAME, source_filename)
    specification = decode_canonical_bytes(selected.payloads[SPECIFICATION_FILENAME],
        domain.MatrixPreparedSourceQualificationSpecification,
        maximum_bytes=len(selected.payloads[SPECIFICATION_FILENAME]))
    allocation = decode_canonical_bytes(selected.payloads[ALLOCATION_FILENAME], UnitAllocation,
        maximum_bytes=len(selected.payloads[ALLOCATION_FILENAME]))
    records = []
    codecs = {(kind.SCHEMA, kind.VERSION): kind for kind in domain.input_record_types()}
    for pin in selected.instance.sources:
        kind = codecs.get((pin.object_schema, pin.object_version))
        if kind is None:
            raise PermissionError("prepared source read changes its exact selected companion revision")
        raw = selected.payloads[source_filename(pin)]
        value = decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))
        original_pin = ObjectIdentity.from_record(pin.object_id, value)
        if original_pin != pin or value.canonical_bytes() != raw:
            raise PermissionError("prepared source read changes an exact canonical selected input")
        records.append((pin.object_id, value))
    if len(records) != 3:
        raise PermissionError("prepared source read omits its automatic locator companions")
    return _selection(specification, allocation, selected.draft, tuple(records))


def _source_publications(*, writer, package, plan, selection, evidence, result):
    from .matrix_source_runtime import retained_source_publications
    return retained_source_publications(writer=writer, package=package, plan=plan,
        selection=selection, evidence=evidence, result=result)



def prepared_source_bootstrap_publications(*, writer, selected, access):
    """Observe the exact seven existing companion handles, without payload I/O.

    This runs only after the ordinary owning source read. The association and
    its complete pinned roster supply locators for a later independent owning
    producer read; they supply no cached admission or permission verdict.
    """
    from empirical_lawhood.api.prospective_experiment import RetainedProspectiveExperiment
    from .prepared_source_access import PreparedSourceOriginalInputAccess
    from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import prepared_assembly_request_types, DEVELOPMENT_TYPES
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
    from empirical_lawhood.runtime.prospective_experiment import (
        ALLOCATION_FILENAME, ASSOCIATION_FILENAME, INSTANCE_FILENAME, SPECIFICATION_FILENAME,
        ProspectiveExperimentAssociation, instance_identity, source_filename,
    )
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    if (type(selected) is not RetainedProspectiveExperiment
            or type(access) is not PreparedSourceOriginalInputAccess
            or type(selected.association) is not ProspectiveExperimentAssociation
            or type(selected.instance) is not ExperimentInstanceBinding
            or type(access.issued_specification) is not domain.MatrixPreparedSourceQualificationSpecification
            or writer.root.contract != access.writer.root.contract):
        raise PermissionError("prepared source bootstrap handles require their actual retained owner and original scope")
    association, instance = selected.association, selected.instance
    association.__post_init__(); instance.__post_init__()
    if (instance.specification != access.issued_specification.identity
            or association.instance != instance_identity(instance) or len(instance.sources) != 3):
        raise PermissionError("prepared source bootstrap handles substitute their exact selected instance")
    models = tuple(pin for pin in instance.sources if (pin.object_schema, pin.object_version) ==
        (domain.MatrixPreparedSourceQualificationSelection.SCHEMA, domain.MatrixPreparedSourceQualificationSelection.VERSION))
    requests = tuple(pin for pin in instance.sources if pin.object_id == 'source-request'
        and (pin.object_schema, pin.object_version) in {(kind.SCHEMA, kind.VERSION) for kind in prepared_assembly_request_types()})
    developments = tuple(pin for pin in instance.sources if pin.object_id == "development.0" and
        (pin.object_schema, pin.object_version) in {(kind.SCHEMA, kind.VERSION) for kind in DEVELOPMENT_TYPES})
    if (len(models) != 1 or models[0] != access.issued_specification.selection
            or len(requests) != 1 or len(developments) != 1):
        raise PermissionError("prepared source bootstrap handles change their closed source/DEV/request roles")
    expected = {SPECIFICATION_FILENAME: instance.specification, ALLOCATION_FILENAME: instance.allocation,
        INSTANCE_FILENAME: association.instance, **{source_filename(pin): pin for pin in instance.sources}}
    if len(association.members) != 6 or {row.filename: row.identity for row in association.members} != expected:
        raise PermissionError("prepared source bootstrap handles change the complete six-member companion census")
    directory = access.issued_directory
    if (not isinstance(directory, Path) or not directory.is_absolute() or directory != directory.resolve(strict=True)
            or not directory.is_relative_to(Path(writer.root.contract.canonical_path))):
        raise PermissionError("prepared source bootstrap handles change the actual retained canonical directory")
    prefix = directory.relative_to(Path(writer.root.contract.canonical_path)) / "experiment"
    rows = [(ASSOCIATION_FILENAME, association.identity, len(association.canonical_bytes()))]
    rows.extend((row.filename, row.identity, row.size_bytes) for row in association.members)
    result = []
    for filename, pin, size in rows:
        access.require_current()
        relative = (prefix / filename).as_posix()
        manifest = writer.read_manifest(relative)
        logical, physical = manifest.logical, manifest.materialization
        if ((logical.payload_schema, logical.content_sha256, physical.physical_sha256, physical.size_bytes) !=
                (pin.object_schema, pin.object_fingerprint, pin.object_fingerprint, size)
                or physical.relative_path != relative or physical.storage_root_id != writer.root.contract.storage_root_id
                or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"
                or physical.compression != "none" or physical.partition_selector is not None):
            raise PermissionError("prepared source bootstrap handle changes an exact pinned member")
        # The actual original owner already admitted this closed packet member
        # before any body hash. Retain its exact labels and full ancestry.
        access.require_issued_member(manifest)
        sidecar_path = relative + ".manifest.json"
        raw = read_bounded_bytes(writer.root.resolve(sidecar_path, for_write=False),
            maximum_bytes=writer.custody_limits.manifest_bytes)
        sidecar = writer._manifest_materialization(logical_artifact_id=logical.logical_artifact_id,
            relative_path=sidecar_path, payload=raw)
        publication = ArtifactWriteResult(logical, physical, sidecar, False)
        actual = read_publication_metadata(writer, publication)
        if actual != manifest or read_bounded_bytes(writer.root.resolve(sidecar_path, for_write=False),
                maximum_bytes=writer.custody_limits.manifest_bytes) != raw:
            raise PermissionError("prepared source bootstrap handle changes its actual durable publication")
        access.require_current()
        result.append((pin, publication))
    if len({pin.object_id for pin, _ in result}) != 7:
        raise PermissionError("prepared source bootstrap handles alias distinct retained roles")
    access.require_current()
    return tuple(sorted(result, key=lambda row: row[0].object_id))

def read_prepared_source_result(*, selected, artifact_writer, run_id, reveal_authority_id=None,
        allow_partial=False, read_access=None):


    from .current_result_custody import authenticate_current_execution_plan, retained_output_artifact_plane
    from .matrix_source_runtime import authenticate_matrix_source_qualification
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from .recursive_qualified_parents import (
        _actual_package, _ParentReadScope)
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding
    if type(allow_partial) is not bool:
        raise TypeError("finite-dt source read requires an explicit partial selection")
    from .prepared_source_access import require_prepared_source_scope
    access = require_prepared_source_scope(getattr(selected, "original_input_access", None),
        getattr(getattr(selected, "original_input_access", None), "issued_specification", None), read_access)
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
        access.require_current()
        return {"scientific_completion": "NOT_ESTABLISHED", "scientific_qualification": "NOT_ESTABLISHED",
            "source_premise": "DEFERRED", "new_native_contact_count": 0}
    codecs = operation_catalog()[2]
    semantic = retained_output_artifact_plane(package, plan, artifact_writer, codecs)
    with semantic.verification_scope() as writer:
        scope = _ParentReadScope(writer)
        retained_plan = scope.plan_reader.authenticate_execution_plan(package=package,
            issued=package.issued_study, run_id=run_id)
        if retained_plan != plan:
            raise PermissionError("prepared source read changes its actual frozen execution plan")
        plan = retained_plan
        prefixes = tuple(sorted(value.capability_key for value in package.registry.capabilities))
        closure = scope.plan_reader.collect_receipt_closure(package=package, execution_plan=plan,
            reveal=None, capability_prefixes=prefixes, allow_partial=False)
        # Reuse exactly this reader-owned closure in every product replay.
        scope.closures[(package.fingerprint(), id(plan), None, prefixes)] = closure
        custody = CurrentIssuedTaskCustody(writer=semantic, reveal_authority_id=reveal_authority_id,
            original_input_access=access)
        with custody.retained_binding(package=package, execution_plan=plan,
                control_reader=scope.plan_reader, receipt_closure=closure, require_current_read=access.require_current):
            evidence, result = authenticate_selection(writer=writer, selection=selection,
                control_reader=scope.plan_reader, original_input_access=access)
            expected = {domain.node_id(selection.scope, "pipeline"): (evidence.receipt, "receipt_id"),
                domain.node_id(selection.scope, "qualification"): (result, "result_id")}
            for gate in result.gate_evidence:
                kind, = (value for value in r.GATES if gate.method.capability_key == r.NAMESPACE + "." + selection.bank.phase.lower() + "." + value.value.lower())
                expected[domain.node_id(selection.scope, kind.value.lower())] = gate, "evidence_id"
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
            from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
            # These exact intrinsic source publications were independently
            # authenticated by authenticate_selection above. Their source
            # roles are fixed by Selection, not inferred from artifact labels.
            source_metadata = set()
            for publication in (selection.source_publication, selection.output_publication,
                    selection.verification_publication, *(value for _, value in selection.metadata_publications)):
                actual = read_publication_metadata(writer, publication)
                if (actual.logical, actual.materialization) != (publication.logical, publication.materialization):
                    raise PermissionError("prepared source read substitutes selected source publication metadata")
                source_metadata.add((actual.logical, actual.materialization))
            source_metadata = frozenset(source_metadata)
            def require_source_member(manifest):
                access.require_current()
                if (manifest.logical, manifest.materialization) not in source_metadata:
                    custody.require_input_member(manifest)
                access.require_current()
            # Every dependent hash, including publication siblings and final
            # rechecks, finishes before this actual retained binding exits.
            with semantic.read_context(before_member=require_source_member) as source_writer:
                publications = _source_publications(writer=source_writer, package=package, plan=plan,
                    selection=selection, evidence=evidence, result=result)
                authenticate_matrix_source_qualification(writer=source_writer, specification=evidence.qualification_config.specification,
                    result=result, pipeline=evidence, executions=executions, publications=publications,
                    codecs=codecs, read_scope=scope, prepared_source_custody=custody,
                    prepared_source_selection=selection)
                bootstrap_publications = prepared_source_bootstrap_publications(writer=source_writer,
                    selected=selected, access=access)
                if {pin.object_id for pin, _ in publications}.intersection(pin.object_id for pin, _ in bootstrap_publications):
                    raise PermissionError("prepared source report aliases scientific and bootstrap publication roles")
                report_publications = tuple(sorted((*publications, *bootstrap_publications), key=lambda row: row[0].object_id))
                source_writer.require_verification_snapshot()
                access.require_current()
            writer.require_verification_snapshot()
            access.require_current()
    access.require_current(artifact_writer=artifact_writer)
    return {"scientific_completion": "COMPLETE_SOURCE_INSTRUMENT_ASSESSMENT",
        "scientific_qualification": "NOT_ESTABLISHED", "source_premise": result.disposition.value,
        "source_evidence_ceiling": "MEASUREMENT", "sampling": "NOT_ESTABLISHED", "transport": "NOT_ESTABLISHED",
        "qualification_specification": evidence.qualification_config.specification.to_document(),
        "qualification_result": result.to_document(), "pipeline_evidence": evidence.to_document(),
        "prior_executions": tuple(value.to_document() for value in executions),
        "publications": tuple((pin.to_document(), value.to_document()) for pin, value in report_publications),
        "new_native_contact_count": 0}
