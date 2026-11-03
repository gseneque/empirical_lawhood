# SPDX-License-Identifier: MPL-2.0
"""Finite original prepared-source custody for later E5/E6 consumers.

The existing association is a locator, never authority. Its exact committed
member census and producing candidate are joined before any fitted selection
is read. Every payload remains under the ordinary current original grants.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import (
    DEVELOPMENT_TYPES, prepared_assembly_request_types,
)
from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import (
    ArtifactProfile, ArtifactWriteResult, artifact_publication_member,
)
from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.runtime.prospective_experiment import (
    ALLOCATION_FILENAME, ASSOCIATION_FILENAME, INSTANCE_FILENAME, SPECIFICATION_FILENAME,
    ProspectiveExperimentAssociation,
)
from empirical_lawhood.runtime.recursive_qualified_parents import RecursivePriorExecutionBinding


def is_prepared_source_result(result):
    return any(gate.method.capability_key.startswith("matrix-source.prepared-finite-dt.")
        for gate in result.gate_evidence)


def _publication_rows(publications):
    if (type(publications) is not tuple or any(type(row) is not tuple or len(row) != 2
            or type(row[0]) is not ObjectIdentity or type(row[1]) is not ArtifactWriteResult
            for row in publications)):
        raise TypeError("prepared source replay requires exact original pin/publication rows")
    pins = tuple(pin for pin, _ in publications)
    if tuple(pin.object_id for pin in pins) != tuple(sorted({pin.object_id for pin in pins})):
        raise PermissionError("prepared source replay aliases or reorders its publication census")
    for pin, publication in publications:
        pin.__post_init__()
        publication.__post_init__()
        if (publication.logical.payload_schema, publication.logical.content_sha256,
                publication.materialization.physical_sha256) != (
                pin.object_schema, pin.object_fingerprint, pin.object_fingerprint):
            raise PermissionError("prepared source replay changes its exact published record identity")


def _association(writer, publications):
    from .prospective_experiment import _directory, _read_prospective_locator
    candidates = tuple(row for row in publications
        if row[0].object_schema == ProspectiveExperimentAssociation.SCHEMA)
    if len(candidates) != 1:
        raise PermissionError("prepared source replay requires one exact original association publication")
    pin, publication = candidates[0]
    if pin.object_version != ProspectiveExperimentAssociation.VERSION:
        raise PermissionError("prepared source replay changes its original association revision")
    actual = read_publication_metadata(writer, publication)
    relative = Path(actual.materialization.relative_path)
    if relative.name != ASSOCIATION_FILENAME or relative.parent.name != "experiment":
        raise PermissionError("prepared source association substitutes its code-owned original path")
    directory = _directory(writer.root.resolve(relative.parent.parent.as_posix(), for_write=False), writer)
    association = _read_prospective_locator(directory / "experiment", ASSOCIATION_FILENAME,
        writer, ProspectiveExperimentAssociation)
    if association.identity != pin:
        raise PermissionError("prepared source replay changes its actual association identity")
    return association, directory


def _closed_bootstrap_members(association):
    kinds = {SPECIFICATION_FILENAME: domain.MatrixPreparedSourceQualificationSpecification,
        ALLOCATION_FILENAME: UnitAllocation, INSTANCE_FILENAME: ExperimentInstanceBinding}
    source_kinds = (*prepared_assembly_request_types(), domain.MatrixPreparedSourceQualificationSelection,
        *DEVELOPMENT_TYPES)
    selected = {}
    for member in association.members:
        kind = kinds.get(member.filename)
        if kind is None:
            matches = tuple(kind for kind in source_kinds if (
                kind.SCHEMA, kind.VERSION) == (member.identity.object_schema, member.identity.object_version))
            if len(matches) != 1:
                raise PermissionError("prepared source association includes an undeclared original companion")
            kind, = matches
        if (kind.SCHEMA, kind.VERSION) != (member.identity.object_schema, member.identity.object_version):
            raise PermissionError("prepared source association changes a fixed companion codec")
        if ((kind in prepared_assembly_request_types() and member.identity.object_id != "source-request")
                or (kind in DEVELOPMENT_TYPES and member.identity.object_id != "development.0")):
            raise PermissionError("prepared source association changes its fixed request or DEV alias")
        if kind in selected:
            raise PermissionError("prepared source association duplicates an original companion role")
        selected[kind] = member
    required = {domain.MatrixPreparedSourceQualificationSpecification, UnitAllocation, ExperimentInstanceBinding,
        domain.MatrixPreparedSourceQualificationSelection}
    if (len(association.members) != 6 or not required.issubset(selected)
            or sum(kind in selected for kind in DEVELOPMENT_TYPES) != 1
            or sum(kind in selected for kind in prepared_assembly_request_types()) != 1):
        raise PermissionError("prepared source association omits its complete six-member original census")
    return selected


def partition_prepared_source_publications(*, writer, publications):
    """Separate only the exact seven association-pinned original publications.

    This reads the closed unprivileged association and publication metadata,
    never a model/array body or any companion body to discover its role.
    Remaining rows still face the unchanged exact scientific operand census.
    """
    _publication_rows(publications)
    association, directory = _association(writer, publications)
    selected = _closed_bootstrap_members(association)
    expected = {association.identity, *(member.identity for member in association.members)}
    rows = tuple(row for row in publications if row[0] in expected)
    if len(rows) != 7 or {pin for pin, _ in rows} != expected:
        raise PermissionError("prepared source replay omits an association-pinned original publication")
    members = {member.identity: (kind, member) for kind, member in selected.items()}
    for pin, publication in rows:
        actual = read_publication_metadata(writer, publication)
        logical, physical = actual.logical, actual.materialization
        if pin == association.identity:
            name, expected_bytes, intrinsic = ASSOCIATION_FILENAME, len(association.canonical_bytes()), True
        else:
            kind, member = members[pin]
            name, expected_bytes = member.filename, member.size_bytes
            intrinsic = kind is not domain.MatrixPreparedSourceQualificationSelection
        relative = (directory / "experiment" / name).relative_to(writer.root.contract.canonical_path).as_posix()
        if (physical.relative_path != relative or physical.storage_root_id != writer.root.contract.storage_root_id
                or physical.size_bytes != expected_bytes or expected_bytes <= 0
                or logical.logical_artifact_id != association.association_id + "." + name.removesuffix(".json")
                or logical.profile is not ArtifactProfile.CANONICAL_JSON or logical.media_type != "application/json"
                or physical.compression != "none" or physical.partition_selector is not None
                or actual.publication is None
                or actual.publication.publication_scope.publication_scope_id != association.association_id
                or actual.publication.publication_scope.relative_root !=
                    (directory / "experiment").relative_to(writer.root.contract.canonical_path).as_posix()
                or actual.publication.members != (artifact_publication_member(logical, physical),)):
            raise PermissionError("prepared source replay substitutes an exact original companion publication")
        if intrinsic and (logical.lineage_parents or (logical.outcome_access, logical.visibility_ceiling) != (
                OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)):
            raise PermissionError("prepared source replay changes an intrinsic locator custody role")
    return tuple(row for row in publications if row[0] not in expected), rows


def _producer_bindings(executions):
    if (type(executions) is not tuple or not executions
            or any(type(binding) is not RecursivePriorExecutionBinding for binding in executions)):
        raise TypeError("prepared source replay requires its exact current producing execution bindings")
    first = executions[0]
    for binding in executions:
        binding.__post_init__()
        if (binding.run_id, binding.package, binding.execution_plan, binding.issued_study,
                binding.execution_authority) != (first.run_id, first.package, first.execution_plan,
                first.issued_study, first.execution_authority):
            raise PermissionError("prepared source replay mixes different original source-producing runs")
    if tuple(binding.record.object_id for binding in executions) != tuple(sorted(
            {binding.record.object_id for binding in executions})):
        raise PermissionError("prepared source replay aliases its original producing bindings")
    return first


def _require_associated_package(association, package, binding):
    from .models import ExperimentPackage
    if (type(package) is not ExperimentPackage or package.run_plan_id != binding.run_id
            or ObjectIdentity.from_record(package.package_id, package) != binding.package
            or ObjectIdentity.from_record(package.issued_study.issue_id, package.issued_study) != binding.issued_study
            or ObjectIdentity.from_record(package.execution_authority.authority_id,
                package.execution_authority) != binding.execution_authority
            or ObjectIdentity.from_record(package.issued_study.candidate.candidate_id,
                package.issued_study.candidate) != association.candidate):
        raise PermissionError("prepared source association substitutes its actual producing package or candidate")


@dataclass(frozen=True, slots=True)
class PreparedSourceReplay:
    """Immutable operands within one live original producer read, never authority."""
    selection: object
    original_input_access: object
    package: object
    plan: object
    read_scope: object
    receipt_closure: object
    custody: object
    writer: object


@contextmanager
def authenticated_prepared_source_replay(*, writer, executions, bootstrap_publications, codecs,
        current_access=None):
    """Reopen the actual source producer; never bind the consumer as its parent."""
    from .current_result_custody import retained_output_artifact_plane
    from .current_task_custody import CurrentIssuedTaskCustody
    from .matrix_prepared_source_experiment import _retained_selection, authenticate_selection
    from .prepared_source_access import PreparedSourceOriginalInputAccess, require_prepared_source_scope
    from .prospective_experiment import (
        _bootstrap_prospective_original_inputs, _read_retained_prospective_experiment,
    )
    from .recursive_qualified_parents import _actual_package, _ParentReadScope
    from .selected_prepared_access import _ordinary
    ordinary = _ordinary(writer)
    first = _producer_bindings(executions)
    rest, supplied = partition_prepared_source_publications(writer=ordinary,
        publications=bootstrap_publications)
    if rest:
        raise PermissionError("prepared source bootstrap includes an unselected scientific publication")
    association, directory = _association(ordinary, supplied)
    # Existing bootstrap opens only exact intrinsic request/DEV locators and
    # refreshes genuine original grants before any model-bearing packet read.
    access = _bootstrap_prospective_original_inputs(directory=directory,
        artifact_writer=ordinary, read_access=current_access)
    if type(access) is not PreparedSourceOriginalInputAccess:
        raise PermissionError("prepared source replay lacks its exact source-owning original bootstrap")
    access = require_prepared_source_scope(access, access.issued_specification, current_access)
    access.require_current()
    package = _actual_package(ordinary, first.run_id)
    _require_associated_package(association, package, first)
    access.require_current()
    selected = _read_retained_prospective_experiment(directory=directory,
        artifact_writer=ordinary, original_input_access=access)
    if (selected.association != association or selected.candidate != package.issued_study.candidate
            or selected.implementation != package.issued_study.source_closure):
        raise PermissionError("prepared source replay changes its exact authored wave or producing source")
    selection = _retained_selection(selected)
    # The retained parser authenticated the actual candidate/instance/member
    # association; the source owner still validates the whole scientific body.
    access.require_current()
    from .current_result_custody import authenticate_current_execution_plan
    actual_plan = authenticate_current_execution_plan(package=package, issued=package.issued_study,
        run_id=first.run_id, writer=ordinary)
    if (ObjectIdentity.from_record(actual_plan.execution_plan_id, actual_plan) != first.execution_plan
            or {task.task_id for task in actual_plan.tasks} != {task.task_id for task in selected.projection.tasks}):
        raise PermissionError("prepared source replay changes its complete actual producing plan")
    semantic = retained_output_artifact_plane(package, actual_plan, ordinary, codecs)
    with semantic.verification_scope() as reading:
        scope = _ParentReadScope(reading)
        plan = scope.plan_reader.authenticate_execution_plan(package=package,
            issued=package.issued_study, run_id=first.run_id)
        if plan != actual_plan:
            raise PermissionError("prepared source replay substitutes the reader's exact producing plan")
        prefixes = tuple(sorted(value.capability_key for value in package.registry.capabilities))
        closure = scope.plan_reader.collect_receipt_closure(package=package, execution_plan=plan,
            reveal=None, capability_prefixes=prefixes, allow_partial=False)
        scope.closures[(package.fingerprint(), id(plan), None, prefixes)] = closure
        for binding in executions:
            receipt = closure.by_task.get(binding.task_id)
            if (receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != binding.receipt
                    or not any(logical.logical_artifact_id == binding.logical_artifact_id
                        and (logical.payload_schema, logical.content_sha256) == (
                            binding.record.object_schema, binding.record.object_fingerprint)
                        for logical in receipt.output_logical_artifacts)):
                raise PermissionError("prepared source replay changes its exact successful producing receipt")
        custody = CurrentIssuedTaskCustody(writer=semantic, original_input_access=access)
        with custody.retained_binding(package=package, execution_plan=plan, control_reader=scope.plan_reader,
                receipt_closure=closure, require_current_read=access.require_current):
            authenticate_selection(writer=reading, selection=selection,
                control_reader=scope.plan_reader, original_input_access=access)
            facts = set()
            for publication in (selection.source_publication, selection.output_publication,
                    selection.verification_publication, *(value for _, value in selection.metadata_publications),
                    *(value for _, value in supplied)):
                actual = read_publication_metadata(reading, publication)
                facts.add((actual.logical, actual.materialization))
            facts = frozenset(facts)
            def require_source_member(manifest):
                access.require_current()
                if (manifest.logical, manifest.materialization) not in facts:
                    custody.require_input_member(manifest)
                access.require_current()
            with semantic.read_context(before_member=require_source_member) as source_writer:
                yield PreparedSourceReplay(selection, access, package, plan, scope, closure, custody, source_writer)
                source_writer.require_verification_snapshot()
                access.require_current()
            reading.require_verification_snapshot()
            access.require_current()
    # Re-read actual committed locator metadata; no retained pointer is a permit.
    final_rest, final_rows = partition_prepared_source_publications(writer=ordinary,
        publications=bootstrap_publications)
    if final_rest or final_rows != supplied:
        raise PermissionError("prepared source replay changes its original locator publications")
    access.require_current()
