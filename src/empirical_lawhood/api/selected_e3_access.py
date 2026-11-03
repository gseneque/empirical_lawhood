# SPDX-License-Identifier: MPL-2.0
"""Fresh access to immutable original E3 parents of a development operation.

The locator selection is operational and has no canonical identity. Immutable
publication facts may be reused within one operation; permission requires
current stored grant bytes and fresh expiry checks at every access boundary.
"""
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass, replace

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import (
    produced_access, produced_record_parents, validate_produced_input_parents,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import SelectedE3E4Evidence
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactManifest, lineage_parent_sort_key


_ORIGINAL_AUTHORITY_READING = ContextVar('original_e3_authority_reading', default=None)
_ORIGINAL_AUTHORITY_RECORDS = ContextVar('original_e3_authority_records', default=None)
_STOCK_AUTHORITY_LOAD = ExternalStudyOperationAuthorityStore.load


def _current_authority_reader(writer):
    """Select only this operation's live, separate immutable grant closure."""
    from empirical_lawhood.infrastructure.artifacts import _has_stock_manifest_reads

    from threading import get_ident
    reading = _ORIGINAL_AUTHORITY_READING.get()
    records = _ORIGINAL_AUTHORITY_RECORDS.get()
    if (reading is not None and reading._read_verification.active
            and records is not None and records[0] is reading and records[1] == get_ident()
            and _has_stock_manifest_reads(writer) and _has_stock_manifest_reads(reading)
            and writer.root is reading.root and writer.validators is reading.validators
            and writer.semantic_validations is reading.semantic_validations
            and writer.custody_limits is reading.custody_limits):
        return reading
    return None


@contextmanager
def original_e3_authority_read_context(writer):
    """Share grant custody across an effect-free original-input projection.

    Independently bootstrapped access objects see this finite context. Exact
    decoded grants can be shared only while their complete byte census is
    freshly checked and UTC is sampled at each access. No scientific preflight
    or permission verdict enters this lifetime. Custom policies stay eager.
    """
    from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, _has_stock_manifest_reads
    from threading import get_ident

    if _current_authority_reader(writer) is not None or not _has_stock_manifest_reads(writer):
        yield
        return
    authority_plane = ExternalArtifactPlane(writer.root, writer.validators, writer.semantic_validations,
        custody_limits=writer.custody_limits, artifact_verification='strict')
    with authority_plane.read_context() as reading:
        token = _ORIGINAL_AUTHORITY_READING.set(reading)
        records = {}
        record_token = _ORIGINAL_AUTHORITY_RECORDS.set((reading, get_ident(), records))
        try:
            yield
        finally:
            _ORIGINAL_AUTHORITY_RECORDS.reset(record_token)
            _ORIGINAL_AUTHORITY_READING.reset(token)
            records.clear()


def _original_roster(originals):
    if (type(originals) is not tuple or len(originals) != 4
            or any(type(value) is not MatrixSelectedOriginalProduct for value in originals)
            or tuple(value.record.object_id for value in originals) !=
                tuple(sorted({value.record.object_id for value in originals}))):
        raise ValueError('current E3 access requires the exact four original product locators')
    for original in originals:
        original.__post_init__()


@dataclass(frozen=True, slots=True)
class SelectedE3CurrentAccess:
    """Select replacement reveals without changing any original scientific byte."""
    originals: tuple[MatrixSelectedOriginalProduct, ...]

    def __post_init__(self):
        _original_roster(self.originals)

    def effective_originals(self, originals):
        _original_roster(originals)
        self.__post_init__()
        if (tuple(value.record for value in self.originals) != tuple(value.record for value in originals)
                or any(replace(selected, reveal_authority=original.reveal_authority) != original
                    for selected, original in zip(self.originals, originals, strict=True))):
            raise PermissionError('current E3 access changes its original product, package, run, plan, issue or execution')
        return self.originals


def selected_e3_originals(originals, current_access=None):
    _original_roster(originals)
    if current_access is None:
        return originals
    if type(current_access) is not SelectedE3CurrentAccess:
        raise TypeError('current E3 access requires its exact operation-local selection')
    return current_access.effective_originals(originals)


def select_current_e3_access(records):
    """Compose only the four declared original-product access selections."""
    if type(records) is not tuple or any(type(value) is not MatrixSelectedOriginalProduct for value in records):
        raise TypeError('current E3 access requires exact original-product selection records')
    return SelectedE3CurrentAccess(tuple(sorted(records, key=lambda value: value.record.object_id)))


@dataclass(frozen=True, slots=True)
class SelectedE3OriginalInputAccess:
    """Authenticated original facts, never a retained authorization verdict.

    Construct this only through the owning bootstrap below. No scientific
    product bytes, calibrated scores, new execution authority or qualification
    are supplied by this object.
    """
    writer: object
    originals: tuple[MatrixSelectedOriginalProduct, ...]
    selected_originals: tuple[MatrixSelectedOriginalProduct, ...]
    parents: tuple[ArtifactLineageParent, ...]
    entries: tuple

    def member_read_scope(self):
        """Keep grant decoding local to one complete member verification call.

        The callback still checks exact grant bytes and current time for every
        member. A different thread owns a separate authority reader.
        """
        return original_e3_authority_read_context(self.writer)

    def require_current(self, *, artifact_writer=None):
        from empirical_lawhood.api.recursive_qualified_parents import (
            _load_parent_authorities_in_scope, _require_parent_authorities_current,
            _validate_parent_authorities_now,
        )
        from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, _ScopedArtifactPlane

        writer = self.writer if artifact_writer is None else artifact_writer
        if writer.root.contract != self.writer.root.contract:
            raise PermissionError('original E3 access changes its actual guarded storage root')
        authority_reader = _current_authority_reader(writer)
        if authority_reader is not None:
            # Only immutable decoded records are shared. Every access checks
            # all stored grant bytes again, then samples current expiry below.
            records = _ORIGINAL_AUTHORITY_RECORDS.get()[2]
            retained = records.get(id(self))
            stock = ExternalStudyOperationAuthorityStore.load is _STOCK_AUTHORITY_LOAD
            if not stock:
                records.pop(id(self), None)
                current = _load_parent_authorities_in_scope(self.entries, authority_reader)
            elif retained is None:
                current = _load_parent_authorities_in_scope(self.entries, authority_reader)
                records[id(self)] = self, self.entries, current
            else:
                original, entries, current = retained
                if original is not self or entries is not self.entries:
                    raise PermissionError('original E3 access changes its finite grant selection')
                authority_reader.require_full_verification_snapshot()
            _validate_parent_authorities_now(self.entries, current)
            return
        if type(writer) is _ScopedArtifactPlane:
            # Authority I/O owns its fresh, small closure. Reentering a growing
            # scientific snapshot from its before-member callback could recurse
            # and must never turn that snapshot into a permission cache.
            writer = ExternalArtifactPlane(writer.root, writer.validators, writer.semantic_validations,
                custody_limits=writer.custody_limits, artifact_verification='strict')
        _require_parent_authorities_current(self.entries, writer)

    def record_parents(self, record):
        # This exact current record contains locators and labels, never the
        # protected bodies they name. No other input codec gains this exception.
        return () if type(record) is SelectedE3E4Evidence else produced_record_parents(record, self.parents)

    def require_member(self, manifest):
        """Require exact inherited custody before hashing an authored body."""
        if type(manifest) is not ArtifactManifest:
            raise TypeError('original input access requires its exact authenticated member manifest')
        logical = manifest.logical
        selected = tuple(value for value in logical.lineage_parents
            if value.identity in {parent.identity for parent in self.parents})
        if selected and selected != self.parents:
            raise PermissionError('authored member changes its complete original E3 parent census')
        pair = (logical.outcome_access, logical.visibility_ceiling)
        if selected:
            expected = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=logical.lineage_parents)
            if pair != expected:
                raise PermissionError('authored member changes its exact inherited original E3 custody')
        elif pair != (OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY):
            raise PermissionError('protected authored member lacks its exact original E3 parent custody')
        self.require_current()


def original_input_access(*, artifact_writer, evidence, read_access=None):
    """Authenticate exact producer metadata and historical plans without outcomes."""
    from empirical_lawhood.api.current_result_custody import CurrentResultPlanReader
    from empirical_lawhood.api.matrix_sampling_runtime import _original_product_metadata
    from empirical_lawhood.infrastructure.artifacts import _has_stock_manifest_reads
    from empirical_lawhood.infrastructure.study_issue import (
        ExternalIssuedStudyPublisher, ExternalStudyOperationAuthorityStore, PROGRAMME_ISSUE_GRANTEE_ID,
    )

    if type(evidence) is not SelectedE3E4Evidence:
        raise TypeError('original E3 bootstrap requires its exact current locator evidence')
    evidence.__post_init__()
    originals = selected_e3_originals(evidence.upstream_products, read_access)
    parents, entries = [], {}
    with artifact_writer.read_context() as writer:
        publisher = ExternalIssuedStudyPublisher(artifact_plane=writer,
            authority_store=ExternalStudyOperationAuthorityStore(writer), grantee_id=PROGRAMME_ISSUE_GRANTEE_ID)
        issued_context = (publisher.read_context() if _has_stock_manifest_reads(artifact_writer)
            else nullcontext(None))
        with issued_context as issued_reader:
            from .retained_e3_evidence import current_e3_evidence
            retained = current_e3_evidence(writer)
            reader = CurrentResultPlanReader(writer) if retained is None else retained.reader
            for original in originals:
                package, issued, _, receipt, logical, prefixes = _original_product_metadata(
                    writer, original, original.record, _control_reader=reader, _issued_reader=issued_reader)
                plan = reader.authenticate(package=package, issued=issued, receipt=receipt,
                    logical=logical, capability_prefixes=prefixes)
                if ObjectIdentity.from_record(plan.execution_plan_id, plan) != original.prior_execution.execution_plan:
                    raise PermissionError('original E3 bootstrap changes the exact producing execution plan')
                parents.extend(ArtifactLineageParent(pin, logical.visibility_ceiling, logical.outcome_access)
                    for pin in (original.record, ObjectIdentity.from_record(receipt.receipt_id, receipt)))
                key = (original.prior_execution.run_id, original.issued_study,
                    original.execution_authority, original.reveal_authority)
                if key in entries and entries[key][1] != package:
                    raise PermissionError('original E3 bootstrap combines different original packages')
                entries[key] = (original, package)
            writer.require_verification_snapshot()
    parents = tuple(sorted(set(parents), key=lineage_parent_sort_key))
    validate_produced_input_parents(parents)
    if parents != evidence.produced_input_parents:
        raise PermissionError('original E3 bootstrap changes its exact actual eight produced parents')
    result = SelectedE3OriginalInputAccess(artifact_writer, evidence.upstream_products,
        originals, parents, tuple(entries.values()))
    result.require_current()
    return result


def bootstrap_development_input_access(*, directory, artifact_writer, specification, instance,
        packet, read_member, read_access=None):
    """Use only the specification/instance-pinned current locator companion."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4ExperimentSpecification

    if type(specification) is not SelectedE3E4ExperimentSpecification:
        raise TypeError('original E3 bootstrap requires its exact current DEV specification')
    selected = tuple(value for value in instance.sources if value == specification.evidence)
    if len(selected) != 1:
        raise PermissionError('original E3 bootstrap omits its exact instance-bound evidence')
    evidence = read_member(selected[0], SelectedE3E4Evidence)
    if evidence.programme != specification.programme:
        raise PermissionError('original E3 bootstrap substitutes its declared scientific programme')
    return original_input_access(artifact_writer=artifact_writer, evidence=evidence, read_access=read_access)


def bootstrap_selected_input_access(*, specification, selection, read_locator,
        artifact_writer, read_access=None, selection_path=None):
    """Authenticate only the exact selected locator before model or FILE reads."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import (
        PROTOCOL_ID, SelectedE3E4ExperimentSpecification,
    )
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputSelection

    if type(specification) is not SelectedE3E4ExperimentSpecification:
        raise TypeError('original E3 selected inputs require their exact current DEV specification')
    specification.__post_init__()
    if type(selection) not in (ExperimentInputSelection, ExperimentFileInputSelection):
        raise TypeError('original E3 selected inputs require their exact closed selector')
    selection.__post_init__()
    selected = tuple(value for value in selection.bindings if value.key == 'evidence')
    if (selection.protocol_id != PROTOCOL_ID or len(selected) != 1
            or selected[0].identity != specification.evidence):
        raise PermissionError('original E3 selected inputs omit their exact specification-bound evidence')
    evidence = read_locator('evidence', specification.evidence, SelectedE3E4Evidence)
    if (type(evidence) is not SelectedE3E4Evidence or evidence.identity != specification.evidence
            or evidence.programme != specification.programme):
        raise PermissionError('original E3 selected inputs substitute their exact scientific programme or evidence')
    return original_input_access(artifact_writer=artifact_writer,
        evidence=evidence, read_access=read_access).require_current


def bootstrap_authoring_input_access(*, preparation, artifact_writer, read_access=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4ExperimentSpecification

    specification = preparation.specification_record
    if type(specification) is not SelectedE3E4ExperimentSpecification:
        raise TypeError('original E3 authoring requires its exact current DEV specification')
    rows = tuple(record for _, record in preparation.design_records if type(record) is SelectedE3E4Evidence)
    if (len(rows) != 1 or rows[0].identity != specification.evidence
            or rows[0].programme != specification.programme):
        raise PermissionError('original E3 authoring omits its exact declared locator evidence')
    return original_input_access(artifact_writer=artifact_writer, evidence=rows[0], read_access=read_access)


def validate_development_read_access(*, payloads, read_access=None, **_):
    access = getattr(payloads, 'original_input_access', None)
    if type(access) is not SelectedE3OriginalInputAccess:
        raise PermissionError('current DEV read lacks its authenticated original E3 bootstrap')
    if selected_e3_originals(access.originals, read_access) != access.selected_originals:
        raise PermissionError('current DEV read changes its selected original E3 access')
    access.require_current()
