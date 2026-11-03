# SPDX-License-Identifier: MPL-2.0
"""Authenticated protected E3 science from original issued custody, without work."""

from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_adjudication import adjudication_task_id, conditional_reasons
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import ConfiguredProtectedE3Assessment, ConfiguredProtectedE3Calibration, ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3ModelSet
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
from ...codecs import MAX_CAMPAIGN_PACKAGE_BYTES
from ...current_result_custody import _current_control, authenticate_current_execution_plan, retained_output_artifact_plane
from empirical_lawhood.api.models import ExperimentPackage
from ...protected_e3_read_custody import authorize as _authorize, configured_receipt_read, original_design, product as _product
from ...protected_e3_read_custody import identity as _identity  # noqa: F401 - retained reader helper
from empirical_lawhood.api.matrix_training_provenance import fitted_training_provenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord


def _retained_scientific_writer(package, plan, writer):
    """Project typed codecs only; preserve the original stored manifests."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_composition import operation_declarations

    codecs = {}
    for declaration in operation_declarations():
        for schema, kind in declaration.record_codecs.items():
            if codecs.setdefault(schema, kind) is not kind:
                raise PermissionError('PROTECTED_E3_READ_EXACT_TYPED_CODEC_REQUIRED')
    return retained_output_artifact_plane(package, plan, writer, codecs)


def _original_design(selected):
    return original_design(selected, specification_type=MatrixResponseErrorSpecification)


def _scientific_projection(specification, allocation, calibration, frozen, assessment, adjudication, *, execution_plan, run_id, receipts):
    from empirical_lawhood.api.protected_e3_read_projection import scientific_projection
    return scientific_projection(specification, allocation, calibration, frozen, assessment, adjudication,
        execution_plan=execution_plan, run_id=run_id, receipts=receipts,
        conditional_reasons=conditional_reasons, adjudication_task_id=adjudication_task_id,
        statistical_task_id=statistical_task_id)


def _selected_preparation(selected):
    """Decode the one exact retained configured source, with no provider work.

    The retained loader has already authenticated the companion payload bytes.
    This owner selects its exact declared schema/revision and preserves the raw
    canonical record. Prepared callers retain the same source contract. Decode
    once for primary-amendment and frozen secondary-target consumers together.
    """
    from hashlib import sha256
    from ...prospective_experiment import RetainedProspectiveExperiment
    from empirical_lawhood.runtime.prospective_experiment import PreparedProspectiveExperimentHandoff, source_filename
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import configured_preparation_types
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes

    if type(selected) not in (RetainedProspectiveExperiment, PreparedProspectiveExperimentHandoff):
        raise TypeError('protected configured read requires its actual retained or prepared companion')
    kinds = {(kind.SCHEMA, kind.VERSION): kind for kind in configured_preparation_types()}
    refs = tuple(pin for pin in selected.instance.sources if (pin.object_schema, pin.object_version) in kinds)
    if len(refs) != 1:
        raise PermissionError('PROTECTED_E3_READ_EXACT_CONFIGURED_SOURCE_REQUIRED')
    pin, = refs
    if type(selected) is RetainedProspectiveExperiment:
        name = source_filename(pin)
        if tuple(member.identity for member in selected.association.members if member.filename == name) != (pin,):
            raise PermissionError('PROTECTED_E3_READ_EXACT_RETAINED_SOURCE_MEMBER_REQUIRED')
        raw = selected.payloads[name]
        record = decode_canonical_bytes(raw, kinds[(pin.object_schema, pin.object_version)], maximum_bytes=len(raw))
    elif type(selected) is PreparedProspectiveExperimentHandoff:
        records = tuple(record for key, record in selected.design_records if key == pin.object_id
            and type(record) is kinds[(pin.object_schema, pin.object_version)])
        if len(records) != 1:
            raise PermissionError('PROTECTED_E3_READ_EXACT_PREPARED_SOURCE_REQUIRED')
        record, = records
        raw = record.canonical_bytes()
    canonical = raw if type(selected) is PreparedProspectiveExperimentHandoff else record.canonical_bytes()
    if (canonical != raw or record.selection_id != pin.object_id
            or (record.SCHEMA, record.VERSION, sha256(canonical).hexdigest())
                != (pin.object_schema, pin.object_version, pin.object_fingerprint)):
        raise PermissionError('PROTECTED_E3_READ_EXACT_CONFIGURED_SOURCE_BYTES_REQUIRED')
    return record


def _selected_secondary_target(selection, writer):
    from empirical_lawhood.api.configured_e3_secondary_target import authenticate_secondary_target
    target = authenticate_secondary_target(writer=writer, selection=selection)
    return None if target is None else (*target, selection.secondary_readout.lineage_scope)


@dataclass(frozen=True, slots=True)
class ConfiguredE3OriginalProducts:
    package: object
    execution_plan: object
    specification: object
    preparation: object
    allocation: object
    receipts: object
    models: object
    model_freeze: object
    calibration: object
    calibrated_freeze: object
    prefit: object
    report: object
    reveal_authority: ObjectIdentity
    _current_read: object
    _product_source: object = None
    _access_read: object = None

    def require_current(self):
        """Recheck this open read immediately before a metadata publication."""
        self._current_read()

    def product_source(self, task_id):
        self.require_access()
        if self._product_source is not None:
            return self._product_source(task_id)
        return self.package, self.execution_plan, self.receipts, self.reveal_authority

    def require_access(self):
        # Legacy explicit constructions keep their stronger current guard.
        (self._access_read or self._current_read)()


@contextmanager
def _configured_e3_read(*, selected, artifact_writer, run_id, reveal_authority_id=None,
        allow_partial=False, assess_incomplete=False,
        original_products=False, expected_package=None):
    """Read actual retained scientific products; never schedule or reacquire."""


    validate_stable_id(run_id)
    if type(allow_partial) is not bool or type(assess_incomplete) is not bool:
        raise TypeError('protected E3 read requires an explicit partial selection')
    if allow_partial and assess_incomplete or original_products and assess_incomplete:
        raise ValueError('incomplete scientific assessment requires its own explicit result-read selection')
    specification, allocation = _original_design(selected)
    # Finite control authentication here; task publications get separate scopes.
    # No mutable global cache survives this read or grants outcome authority.
    writer = artifact_writer
    package = _current_control(writer=writer, run_id=run_id, name='campaign-package',
        record_type=ExperimentPackage, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    if (ObjectIdentity.from_record(package.issued_study.candidate.candidate_id, package.issued_study.candidate)
            != selected.association.candidate
            or package.issued_study.source_closure != selected.implementation
            or package.run_plan_id != run_id):
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_CANDIDATE_AND_SOURCE_REQUIRED')
    if expected_package is not None and (type(expected_package) is not ExperimentPackage
            or package != expected_package):
        raise PermissionError('PROTECTED_E3_READ_EXACT_EXPECTED_PACKAGE_REQUIRED')
    del expected_package
    if not allow_partial:
        _authorize(writer, package, reveal_authority_id)
    # This replays only persisted issued metadata and its stored registry.
    # It never compiles a current source checkout or domain operation catalog.
    plan = authenticate_current_execution_plan(package=package, issued=package.issued_study,
        run_id=run_id, writer=writer)
    if {task.task_id for task in plan.tasks} != {task.task_id for task in selected.projection.tasks}:
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_COMPLETE_TASK_CENSUS_REQUIRED')
    if allow_partial:
        del selected
        yield {'scientific_status': 'UNASSESSED', 'admission_status': 'UNASSESSED',
            'evaluability': 'DEFERRED', 'qualification': 'NOT_ESTABLISHED',
            'reason_codes': ['PARTIAL_READ_SCIENTIFIC_ASSESSMENT_DEFERRED'],
            'denominators': {public_role: {'assigned_units': len(allocation.unit_ids(role)),
                'units': list(allocation.unit_ids(role)), 'assessed_units': None}
                for public_role, role in (('calibration', 'calibration'), ('confirmation', 'evaluation'))},
            'calibration': None, 'assessment': None, 'adjudication': None, 'training_provenance': None,
            'secondary_response_readout': {'status': 'DEFERRED_PARTIAL_READ'},
            'assigned_tasks': len(plan.tasks), 'typed_product_validation': 'DEFERRED',
            'scientific_completion': 'NOT_ESTABLISHED', 'native_contact': 'none'}
        return
    writer = _retained_scientific_writer(package, plan, writer)
    from empirical_lawhood.api.configured_e3_primary_amendment import authenticate_primary_amendment
    source_selection = _selected_preparation(selected)
    # Its candidate, projection, draft and raw companion have completed their
    # exact joins. Scientific operands and the owning byte/access guards remain.
    del selected
    primary_amendment = authenticate_primary_amendment(writer=writer, selection=source_selection)
    amendment_report = None
    if primary_amendment is not None:
        amendment = source_selection.primary_amendment.amendment
        amendment_report = {'binding': primary_amendment.to_document(), 'scope': amendment.scope,
            'original_native_candidate': amendment.original_candidate.identity.to_document(),
            'current_candidate': amendment.candidate.identity.to_document(),
            'alpha_numerator': amendment.assessment.alpha_numerator, 'alpha_denominator': amendment.assessment.alpha_denominator,
            'comparison_ids': list(amendment.assessment.comparison_ids)}
    if assess_incomplete:
        from empirical_lawhood.api.configured_e3_retained_read import continued_plan_read
        from empirical_lawhood.api.configured_e3_incomplete_read import read_incomplete_assessment
        from empirical_lawhood.api.protected_e3_read_custody import _require_current_read_layout

        _require_current_read_layout(writer, run_id)
        with writer.read_context() as view, continued_plan_read(writer=view, plan=plan) as retained:
            if retained is not None and (getattr(source_selection, 'retention', None) != retained.retention
                    or getattr(source_selection, 'unfinished', getattr(source_selection, 'closeout', None)) != retained.unfinished
                    or source_selection.retained_tasks != tuple(retained.tasks[key] for key in sorted(retained.tasks))):
                raise PermissionError('PROTECTED_E3_READ_EXACT_RETAINED_SELECTION_REQUIRED')
            report = read_incomplete_assessment(writer=view, package=package, plan=plan,
                specification=specification, allocation=allocation, retained=retained)
            if retained is not None:
                report['retained_execution'] = {'continuation': retained.retention.to_document(),
                    'original_terminal_status': retained.original.terminal.operational_status,
                    'fit_status': 'ORIGINAL_FIT_RETAINED'}
                if retained.unfinished is not None:
                    report['retained_execution']['unfinished_execution'] = retained.unfinished.to_document()
                    report['retained_execution']['completed_receipts_reused'] = len(retained.unfinished.completed_receipts)
            report['primary_family_amendment'] = amendment_report
            report['secondary_response_readout'] = {'status': 'UNASSESSED_INCOMPLETE_READ'}
            view.require_verification_snapshot()
        _authorize(artifact_writer, package, reveal_authority_id)
        yield report
        _authorize(artifact_writer, package, reveal_authority_id)
        return
    secondary_target = _selected_secondary_target(source_selection, writer)
    from empirical_lawhood.api.configured_e3_retained_read import continued_plan_read
    with configured_receipt_read(writer, package, plan, reveal_authority_id=reveal_authority_id) as read, \
            continued_plan_read(writer=read.writer, plan=plan, receipts=read.receipts) as retained:
        writer, receipts, terminal = read.writer, read.receipts, read.terminal
        if retained is not None and (getattr(source_selection, 'retention', None) != retained.retention
                or getattr(source_selection, 'unfinished', getattr(source_selection, 'closeout', None)) != retained.unfinished
                or source_selection.retained_tasks != tuple(retained.tasks[key] for key in sorted(retained.tasks))):
            raise PermissionError('PROTECTED_E3_READ_EXACT_RETAINED_SELECTION_REQUIRED')
        decoded = {}

        def read_product(current_writer, current_plan, current_receipts, task_id, kind):
            if current_writer is not writer or current_plan is not plan or current_receipts is not receipts:
                raise PermissionError('PROTECTED_E3_READ_PRODUCT_CACHE_SCOPE_CHANGED')
            key = task_id, kind
            if key not in decoded:
                if retained is not None and retained.predecessor is not None and task_id in retained.predecessor.receipts:
                    from empirical_lawhood.api.configured_e3_retained_read import producing_custody
                    previous = producing_custody(writer, plan, task_id)
                    previous.require_access()
                    decoded[key] = _product(previous.writer, previous.plan, previous.receipts, task_id, kind)
                else:
                    decoded[key] = _product(writer, plan, receipts, task_id, kind)
            return decoded[key]

        ids = (specification.identity, allocation.identity)
        requests = (('models', statistical_task_id(*ids, 'fit'), ConfiguredProtectedE3ModelSet),
            ('calibration', statistical_task_id(*ids, 'calibrate'), ConfiguredProtectedE3Calibration),
            ('calibrated_freeze', statistical_task_id(*ids, 'freeze', mode='calibration'), ConfiguredProtectedE3FrozenProducts),
            ('assessment', statistical_task_id(*ids, 'assess'), ConfiguredProtectedE3Assessment),
            ('adjudication', adjudication_task_id(*ids), ScientificAdjudicationRecord))
        products, custody = {}, {}
        for name, task_id, kind in requests:
            products[name], custody[name] = read_product(writer, plan, receipts, task_id, kind)
        result = _scientific_projection(specification, allocation, products['calibration'], products['calibrated_freeze'],
            products['assessment'], products['adjudication'],
            execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan), run_id=run_id, receipts=receipts)
        training = fitted_training_provenance(specification, allocation, products['models'], products['calibrated_freeze'])
        matched_read, matched_custody = None, ()
        if specification.measurement.is_matched:
            from empirical_lawhood.api.protected_e3_secondary_read import read_matched_response
            model_freeze, freeze_custody = read_product(writer, plan, receipts,
                statistical_task_id(*ids, 'freeze', mode='model'), ConfiguredProtectedE3FrozenProducts)
            custody['model_freeze'] = freeze_custody
            if retained is not None:
                from empirical_lawhood.api.configured_e3_retained_read import authenticate_continued_response_custody
                authenticate_continued_response_custody(writer=writer, plan=plan, receipts=receipts,
                    selection=source_selection, specification=specification, allocation=allocation,
                    models=products['models'], model_freeze=model_freeze, calibration=products['calibration'],
                    calibrated_freeze=products['calibrated_freeze'], product_reader=read_product)
            matched_read, matched_custody = read_matched_response(specification=specification, allocation=allocation,
                models=products['models'], model_freeze=model_freeze, calibrated_freeze=products['calibrated_freeze'],
                calibration=products['calibration'], assessment=products['assessment'], source_selection=source_selection,
                writer=writer, plan=plan, receipts=receipts, product_reader=read_product, statistical_task_id=statistical_task_id)
        secondary, secondary_custody = {"status": "NOT_SUPPLIED", "reason": "NO_AUTHENTICATED_FROZEN_SECONDARY_TARGET"}, ()
        if secondary_target is not None:
            from empirical_lawhood.api.protected_e3_secondary_read import read_secondary_response
            secondary, secondary_custody = read_secondary_response(specification=specification, allocation=allocation,
                calibration=products['calibration'], assessment=products['assessment'], writer=writer, plan=plan, receipts=receipts,
                product_reader=read_product, statistical_task_id=statistical_task_id,
                normalized_tolerance=secondary_target[0], target_origin=secondary_target[1], configured_edition=True)
            secondary["configuration_lineage_scope"] = secondary_target[2]
        report = {**result, 'primary_family_amendment': amendment_report, 'training_provenance': training, 'secondary_response_readout': secondary,
            **({'matched_response_readout': matched_read, 'matched_response_custody': matched_custody}
                if specification.measurement.is_matched else {}),
            'secondary_response_custody': secondary_custody, 'custody': custody, 'execution_plan': ObjectIdentity.from_record(plan.execution_plan_id, plan).to_document(),
            'terminal': ObjectIdentity.from_record(terminal.terminal_event_id, terminal).to_document(),
            'assigned_tasks': len(plan.tasks), 'completed_tasks': len(terminal.completed_task_ids),
            'typed_product_validation': 'COMPLETE',
            'scientific_completion': 'RETAINED_ADJUDICATION', 'native_contact': 'none'}
        if retained is not None:
            report['retained_execution'] = {
                'continuation': retained.retention.to_document(),
                'original_models': _identity(retained.original.models).to_document(),
                'original_model_freeze': _identity(retained.original.model_freeze).to_document(),
                'retained_tasks': len(retained.tasks), 'copy_validation': 'EXACT_ORIGINAL_RECEIPT_BYTES',
                'fit_status': 'ORIGINAL_FIT_RETAINED', 'original_terminal_status': retained.original.terminal.operational_status}
            if retained.unfinished is not None:
                report['retained_execution']['unfinished_execution'] = retained.unfinished.to_document()
                report['retained_execution']['completed_receipts_reused'] = len(retained.unfinished.completed_receipts)
        output = report
        if original_products:
            from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
            from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore

            model_freeze, _ = read_product(writer, plan, receipts,
                statistical_task_id(*ids, 'freeze', mode='model'), ConfiguredProtectedE3FrozenProducts)
            prefit, _ = read_product(writer, plan, receipts,
                statistical_task_id(*ids, 'fit'), ConfiguredProtectedE3PreFitJoin)
            if products['models'].reservation_join != _identity(prefit):
                raise PermissionError('PROTECTED_E3_READ_EXACT_ORIGINAL_PREFIT_REQUIRED')
            reveal = ExternalStudyOperationAuthorityStore(writer).load(reveal_authority_id)

            def access():
                read.require_active()
                if retained is not None:
                    retained.original.require_access()
                    if retained.predecessor is not None:
                        retained.predecessor.require_access()
                if ExternalStudyOperationAuthorityStore(writer).load(reveal_authority_id) != reveal:
                    raise PermissionError('PROTECTED_E3_READ_ORIGINAL_PRODUCT_REVEAL_CHANGED')
                read.require_access()

            def current():
                access()
                read.require_current()

            current()
            def product_source(task_id):
                if retained is not None and retained.predecessor is not None and task_id in retained.predecessor.receipts:
                    from empirical_lawhood.api.configured_e3_retained_read import producing_custody
                    previous = producing_custody(writer, plan, task_id)
                    previous.require_access()
                    return previous.package, previous.plan, previous.receipts, ObjectIdentity.from_record(previous.reveal.authority_id, previous.reveal)
                return package, plan, receipts, ObjectIdentity.from_record(reveal.authority_id, reveal)

            output = ConfiguredE3OriginalProducts(package, plan, specification, source_selection, allocation,
                MappingProxyType(dict(receipts)), products['models'], model_freeze,
                products['calibration'], products['calibrated_freeze'], prefit,
                MappingProxyType(report), ObjectIdentity.from_record(reveal.authority_id, reveal), current, product_source, access)
        # Replay is complete. The output retains every required original product
        # and report; root-level decoded bodies are not needed by its live guards.
        decoded.clear()
        products.clear()
        yield output


def read_protected_e3_result(*, selected, artifact_writer, run_id, reveal_authority_id=None,
        allow_partial=False, assess_incomplete=False):
    """Read full retained science, preserving actual operational and missing states."""
    reading = _configured_e3_read(selected=selected, artifact_writer=artifact_writer, run_id=run_id,
        reveal_authority_id=reveal_authority_id, allow_partial=allow_partial, assess_incomplete=assess_incomplete)
    del selected
    with reading as report:
        return report


@contextmanager
def read_protected_e3_original_products(*, selected, artifact_writer, run_id,
        expected_package, reveal_authority_id):
    """Read full E3 science and its four original E4 parents in one live lifetime."""
    if type(expected_package) is not ExperimentPackage:
        raise TypeError('original configured products require their exact expected package')
    reading = _configured_e3_read(selected=selected, artifact_writer=artifact_writer, run_id=run_id,
        reveal_authority_id=reveal_authority_id, original_products=True, expected_package=expected_package)
    del selected, expected_package
    with reading as products:
        yield products
