# SPDX-License-Identifier: MPL-2.0
"""Closed original-parent bootstrap for the current prepared-source protocol.

Only the existing assembly request and DEV product locator are intrinsic input
metadata. The source Selection, bank, root and model-bearing graph stay guarded.
No object here creates qualification, an issued package or a reveal grant.
"""
from contextlib import contextmanager
from dataclasses import dataclass, fields, replace
from pathlib import Path

from empirical_lawhood.adapters.methods import matrix_prepared_source_experiment as domain
from empirical_lawhood.adapters.methods.matrix_prepared_source_records import (
    MatrixPreparedSourceGateConfig, MatrixPreparedSourceScope, gate_configs,
)
from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import prepared_assembly_request_types, prepared_assembly_request_kind, DEVELOPMENT_TYPES
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
from empirical_lawhood.api import selected_prepared_access as original
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactManifest, lineage_parent_sort_key


def _specification(value):
    if type(value) is not domain.MatrixPreparedSourceQualificationSpecification:
        raise TypeError("prepared source access requires its exact current public specification")
    value.__post_init__()


def _graph_record_types():
    from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft, RecursiveScientificSelection
    from empirical_lawhood.runtime.candidate_compiler import StudyTemplate, ExecutableStudyCompilationReport, ExecutableStudyCandidate
    from empirical_lawhood.runtime.plans import CandidateRunPlan, CandidateExecutionPlan
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveAuthoringSpec
    from empirical_lawhood.planning.experiment_entry import ExecutableStudyDefinition
    from empirical_lawhood.runtime.recursive_prospective_envelope import (
        RecursiveProspectiveAuthoringEnvelope, RecursiveProspectiveAuthoringEnvelopeV3,
        RecursiveProspectiveAuthoringEnvelopeV4,
    )
    return (RecursiveStudyDraft, RecursiveScientificSelection, StudyTemplate, ExecutableStudyCompilationReport,
        ExecutableStudyCandidate, CandidateRunPlan, CandidateExecutionPlan, RecursiveProspectiveAuthoringSpec,
        ExecutableStudyDefinition, RecursiveProspectiveAuthoringEnvelope,
        RecursiveProspectiveAuthoringEnvelopeV3, RecursiveProspectiveAuthoringEnvelopeV4)


@dataclass(frozen=True, slots=True)
class PreparedSourceOriginalInputAccess(original.SelectedPreparedOriginalInputAccess):
    """The existing actual parent owners with a closed source publication role."""

    training_scope: object = None
    source_scope: MatrixPreparedSourceScope | None = None

    def __post_init__(self):
        if self.source_scope is not None:
            if type(self.source_scope) is not MatrixPreparedSourceScope:
                raise TypeError("prepared source access requires its exact immutable selected scope")
            self.source_scope.__post_init__()

    def record_parents(self, record):
        if type(record) is MatrixPreparedSourceGateConfig:
            record.__post_init__()
            if self.source_scope is None or sum(record == expected for expected in gate_configs(self.source_scope)) != 1:
                raise PermissionError("prepared gate configuration differs from its exact selected source scope")
            return self.parents
        if type(record) in domain.locator_record_types():
            return ()
        # Every source graph below belongs to the exact full model-bearing
        # selection. Its config JSON/pins need not repeat fitted coefficients.
        if type(record) in (*_graph_record_types(), domain.MatrixPreparedSourceQualificationSelection):
            return self.parents
        return original.produced_record_parents(record, self.parents)

    def bind_issued_members(self, manifests, *, packet, association, directory=None):
        _specification(self.issued_specification)
        return original._bind_issued_members(self, manifests, packet=packet, association=association,
            directory=directory, model_source_schemas=frozenset((domain.MatrixPreparedSourceQualificationSelection.SCHEMA,)),
            locator_schemas=frozenset(kind.SCHEMA for kind in domain.locator_record_types()))

    def require_original_member(self, manifest):
        # Existing E3 and DEV owners retain their full frozen receipt checks.
        # The separate TRAIN context supplies data custody only, not permission.
        if type(manifest) is not ArtifactManifest:
            raise TypeError("prepared source original requires an exact member manifest")
        self.require_current()
        fact = manifest.logical, manifest.materialization
        if fact in self.original_members or any(fact in custody._original_member_facts or any(
                output.logical_artifact_id == manifest.logical.logical_artifact_id
                for task in custody.plan.tasks for output in task.outputs)
                for custody in self.development_custodies):
            return super(PreparedSourceOriginalInputAccess, self).require_original_member(manifest)
        if self.training_scope is None:
            raise PermissionError("prepared source original member is outside its live exact producer scopes")
        if self.training_scope.require_member(manifest) is not None:
            raise ValueError("native TRAIN member guard must return None or raise")
        self.require_current()


@contextmanager
def authenticated_prepared_source_access(*, scope, locator):
    """Compose the actual finite TRAIN data lifetime with fresh parent grants."""
    from empirical_lawhood.api.native_training_read_scope import authenticated_native_training_read_scope
    if type(scope) is not PreparedSourceOriginalInputAccess or scope.training_scope is not None:
        raise TypeError("prepared source TRAIN composition requires its unbound actual original scope")
    scope.require_current()
    with authenticated_native_training_read_scope(artifact_writer=original._ordinary(scope.writer), locator=locator) as training:
        bound = replace(scope, training_scope=training)
        bound.require_current()
        yield bound
        bound.require_current()
    scope.require_current()


def _original_access(*, artifact_writer, request, development, read_access=None):
    from empirical_lawhood.api.matrix_programme_e4_inputs import _require_original_e3_access, prepared_source_lineage
    from empirical_lawhood.infrastructure.publication_metadata import read_publication_metadata

    if type(request) not in prepared_assembly_request_types() or type(development) not in DEVELOPMENT_TYPES:
        raise TypeError("prepared source bootstrap requires its exact original request and DEV locator")
    request.__post_init__(); development.__post_init__()
    if request.development_product != development.identity:
        raise PermissionError("prepared source bootstrap substitutes its actual selected DEV locator")
    locators = tuple(("original." + str(index), value) for index, value in enumerate(request.original_products))
    locators = (*locators, ("development.0", development))
    access = original.original_input_access(artifact_writer=artifact_writer, locators=locators, read_access=read_access)
    # The original export is an actual produced publication, not a new grant.
    # Reprove its exact eight producing parents before touching export bytes.
    access.require_current()
    _require_original_e3_access(writer=artifact_writer, original_e3=request.original_e3,
        original_products=access.selected_originals)
    exported = read_publication_metadata(artifact_writer, request.original_e3.publication)
    expected = prepared_source_lineage(original_e3=request.original_e3, development_product=development)
    if not set(access.parents).issubset(expected):
        raise PermissionError("prepared source export drops actual original or DEV ancestry")
    if any(parent.identity == request.original_e3.record for parent in access.parents):
        raise PermissionError("prepared source export aliases an original producer")
    added = ArtifactLineageParent(request.original_e3.record, exported.logical.visibility_ceiling, exported.logical.outcome_access)
    if tuple(sorted({*access.parents, *exported.logical.lineage_parents,
            *development.publication.logical.lineage_parents, added}, key=lineage_parent_sort_key)) != expected:
        raise PermissionError("prepared source export changes its exact closed producer census")
    values = {field.name: getattr(access, field.name) for field in fields(original.SelectedPreparedOriginalInputAccess)}
    values.update(parents=expected, original_members=access.original_members | frozenset(((exported.logical, exported.materialization),)))
    result = PreparedSourceOriginalInputAccess(**values)
    result.require_current()
    return result


def _companions(bindings, read):
    selected = dict(bindings)
    if len(selected) != len(bindings) or set(selected) != {"selection", "source-request", "development.0"}:
        raise PermissionError("prepared source bootstrap changes its exact automatic companion census")
    request = read("source-request", selected["source-request"], prepared_assembly_request_kind(selected['source-request']))
    choices = tuple(kind for kind in DEVELOPMENT_TYPES if (kind.SCHEMA, kind.VERSION) ==
        (selected["development.0"].object_schema, selected["development.0"].object_version))
    if len(choices) != 1:
        raise PermissionError("prepared source bootstrap refuses a fitted body as a DEV locator")
    development = read("development.0", selected["development.0"], choices[0])
    return request, development, selected["selection"]


def bootstrap_selected_input_access(*, specification, selection, read_locator, artifact_writer,
        read_access=None, selection_path=None):
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputSelection, ExperimentFileInputSelection

    _specification(specification)
    if type(selection) not in (ExperimentInputSelection, ExperimentFileInputSelection):
        raise TypeError("prepared source bootstrap requires its exact copied selector")
    selection.__post_init__()
    if selection.protocol_id != domain.PROTOCOL_ID or getattr(selection, "files", ()):
        raise PermissionError("prepared source bootstrap changes its exact metadata protocol")
    request, development, pin = _companions(tuple((row.key, row.identity) for row in selection.bindings), read_locator)
    if specification.selection != pin:
        raise PermissionError("prepared source bootstrap substitutes its frozen model-bearing selection")
    access = _original_access(artifact_writer=artifact_writer, request=request, development=development, read_access=read_access)
    _verify_selected_members(access=access, selection=selection, selection_path=selection_path,
        artifact_writer=artifact_writer, model_key="selection")
    return access.require_current


def _verify_selected_members(*, access, selection, selection_path, artifact_writer, model_key):
    from empirical_lawhood.api.experiment_preparation import _input_member
    if model_key not in ("selection", "prepared-programme"):
        raise PermissionError("prepared source metadata changes its code-owned model role")
    if not isinstance(selection_path, Path) or selection_path != selection_path.resolve(strict=True):
        raise PermissionError("prepared source bootstrap requires its actual canonical selector path")
    manifests = []
    for row in selection.bindings:
        path = _input_member(selection_path.parent, row.relative_path)
        relative = path.relative_to(artifact_writer.root.contract.canonical_path).as_posix()
        manifest = artifact_writer.read_manifest(relative)
        logical, physical = manifest.logical, manifest.materialization
        if ((logical.payload_schema, logical.content_sha256, physical.physical_sha256) !=
                (row.identity.object_schema, row.identity.object_fingerprint, row.identity.object_fingerprint)
                or physical.relative_path != relative or physical.storage_root_id != artifact_writer.root.contract.storage_root_id
                or not 0 < physical.size_bytes <= row.maximum_bytes or logical.media_type != "application/json"
                or logical.profile.value != "CANONICAL_JSON" or physical.compression != "none"
                or physical.partition_selector is not None):
            raise PermissionError("prepared source bootstrap substitutes its exact selected manifest")
        if row.key == model_key:
            if logical.lineage_parents != access.parents or (logical.outcome_access, logical.visibility_ceiling) != produced_access(
                    declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                    declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=access.parents):
                raise PermissionError("prepared source model omits its exact authenticated ancestry or custody")
        elif logical.lineage_parents or (logical.outcome_access, logical.visibility_ceiling) != (
                OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE):
            raise PermissionError("prepared source locator changes its intrinsic blind metadata role")
        manifests.append(manifest)
    facts = frozenset((manifest.logical, manifest.materialization) for manifest in manifests)
    def before_member(member):
        if (member.logical, member.materialization) not in facts:
            raise PermissionError("prepared source selected publication includes an unselected sibling")
        access.require_current()
    for manifest in manifests:
        artifact_writer.verify_manifest(manifest, before_member=before_member)
    access.require_current()
    return None


def bootstrap_authoring_input_access(*, preparation, artifact_writer, read_access=None):
    _specification(preparation.specification_record)
    selected = tuple(value for _, value in preparation.design_records if type(value) is domain.MatrixPreparedSourceQualificationSelection)
    companions = tuple((key, value) for key, value in preparation.design_records if type(value) is not domain.MatrixPreparedSourceQualificationSelection)
    if len(selected) != 1 or len(companions) != 2 or set(dict(companions)) != {"source-request", "development.0"}:
        raise PermissionError("prepared source authoring requires its exact automatic locator companions")
    values = dict(companions)
    inputs = domain.MatrixPreparedSourceInputs(selected[0], values["source-request"], values["development.0"])
    domain.validate_input_companions(inputs)
    if preparation.specification_record.selection != selected[0].identity:
        raise PermissionError("prepared source authoring changes its selected scientific body")
    access = _original_access(artifact_writer=artifact_writer, request=inputs.source_request,
        development=inputs.development_product, read_access=read_access)
    return replace(access, issued_specification=preparation.specification_record, source_scope=selected[0].scope)


def bootstrap_prospective_input_access(*, directory, artifact_writer, specification, instance,
        association, read_member, read_access=None):
    _specification(specification)
    if instance.specification != specification.identity:
        raise PermissionError("prepared source cold bootstrap changes its actual scientific instance")
    # Instance aliases are code-owned record roles; body fingerprints remain
    # their exact actual original canonical values.
    rows = tuple(("selection" if (pin.object_schema, pin.object_version) ==
        (domain.MatrixPreparedSourceQualificationSelection.SCHEMA, domain.MatrixPreparedSourceQualificationSelection.VERSION)
        else pin.object_id, pin) for pin in instance.sources)
    request, development, selected = _companions(rows, lambda key, pin, kind: read_member(pin, kind))
    if selected != specification.selection:
        raise PermissionError("prepared source cold bootstrap substitutes its frozen selection")
    access = _original_access(artifact_writer=artifact_writer, request=request, development=development, read_access=read_access)
    return replace(access, issued_specification=specification, issued_directory=Path(directory).resolve(strict=True))


def require_prepared_source_scope(scope, specification, read_access):
    _specification(specification)
    if (type(scope) is not PreparedSourceOriginalInputAccess or scope.issued_specification != specification
            or scope.current_access != read_access):
        raise PermissionError("prepared source lacks its exact current original bootstrap scope")
    scope.require_current()
    return scope



def bootstrap_assembly_selected_input_access(*, specification, selection, read_locator, artifact_writer,
        read_access=None, selection_path=None):
    """Read existing request/DEV locators before the assembly programme body."""
    from empirical_lawhood.adapters.methods.matrix_prepared_source_assembly import (
        MatrixPreparedSourceAssemblySpecification, MatrixPreparedRetainedE3AssemblySpecification)
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputSelection, ExperimentFileInputSelection
    from empirical_lawhood.adapters.methods import matrix_prepared_source_assembly as assembly
    if type(specification) not in (MatrixPreparedSourceAssemblySpecification, MatrixPreparedRetainedE3AssemblySpecification):
        raise TypeError("prepared source assembly bootstrap requires its exact specification")
    specification.__post_init__()
    if type(selection) not in (ExperimentInputSelection, ExperimentFileInputSelection):
        raise TypeError("prepared source assembly requires its exact copied selector")
    selection.__post_init__()
    protocol = (assembly.CONTINUED_PROTOCOL_ID if type(specification) is MatrixPreparedRetainedE3AssemblySpecification
        else assembly.PROTOCOL_ID)
    if selection.protocol_id != protocol or getattr(selection, "files", ()):
        raise PermissionError("prepared source assembly changes its exact metadata protocol")
    rows = {row.key: row.identity for row in selection.bindings}
    if len(rows) != len(selection.bindings) or set(rows) not in (
            {"request"}, {"request", "prepared-programme", "development-product"}):
        raise PermissionError("prepared source assembly changes its closed locator/programme census")
    if (specification.request != rows["request"] or (rows["request"].object_schema, rows["request"].object_version) !=
            (specification.REQUEST_TYPE.SCHEMA, specification.REQUEST_TYPE.VERSION)):
        raise PermissionError("prepared source assembly substitutes its exact request")
    if set(rows) == {"request"}:
        # This exact intrinsic request-only selection opens no locator/model
        # body here and grants no access. Ordinary decoding still checks the
        # selected request bytes before reporting its missing scientific roles.
        return lambda: None
    request = read_locator("request", rows["request"], specification.REQUEST_TYPE)
    kinds = tuple(kind for kind in DEVELOPMENT_TYPES if (kind.SCHEMA, kind.VERSION) ==
        (rows["development-product"].object_schema, rows["development-product"].object_version))
    if len(kinds) != 1:
        raise PermissionError("prepared source assembly refuses a fitted DEV locator")
    development = read_locator("development-product", rows["development-product"], kinds[0])
    if request.prepared_programme != rows["prepared-programme"]:
        raise PermissionError("prepared source assembly substitutes its selected model-bearing programme")
    access = _original_access(artifact_writer=artifact_writer, request=request,
        development=development, read_access=read_access)
    _verify_selected_members(access=access, selection=selection, selection_path=selection_path,
        artifact_writer=artifact_writer, model_key="prepared-programme")
    return access.require_current
