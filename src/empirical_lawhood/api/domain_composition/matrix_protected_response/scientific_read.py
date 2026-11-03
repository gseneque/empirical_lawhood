# SPDX-License-Identifier: MPL-2.0
"""Authenticated protected E3 science from original issued custody, without work."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from empirical_lawhood.adapters.methods.matrix_factor_response.experiment_specification import MatrixResponseErrorSpecification
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_adjudication import adjudication_task_id, conditional_reasons
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_methods import ProtectedE3Assessment, ProtectedE3Calibration, ProtectedE3FrozenProducts, ProtectedE3ModelSet
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import ProtectedE3PreFitJoin
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_statistical_bindings import statistical_task_id
from empirical_lawhood.api.codecs import MAX_CAMPAIGN_PACKAGE_BYTES
from empirical_lawhood.api.current_result_custody import _current_control, authenticate_current_execution_plan, retained_output_artifact_plane
from empirical_lawhood.api.models import ExperimentPackage
from empirical_lawhood.api.protected_e3_read_custody import authorize as _authorize, completed_receipts, original_design, product as _product
from empirical_lawhood.api.protected_e3_read_custody import identity as _identity  # noqa: F401 - retained reader helper
from empirical_lawhood.api.matrix_training_provenance import fitted_training_provenance
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.adjudication import ScientificAdjudicationRecord
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.plans import ExecutionPlan


def _retained_scientific_writer(package, plan, writer):
    """Project typed codecs only; preserve the original stored manifests."""
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_composition import operation_declarations

    codecs = {}
    for declaration in operation_declarations():
        for schema, kind in declaration.record_codecs.items():
            if codecs.setdefault(schema, kind) is not kind:
                raise PermissionError('PROTECTED_E3_READ_EXACT_TYPED_CODEC_REQUIRED')
    return retained_output_artifact_plane(package, plan, writer, codecs)


def _original_design(selected):
    return original_design(selected, specification_type=MatrixResponseErrorSpecification)


def _completed_receipts(writer, package, plan):
    return completed_receipts(writer, package, plan, capability_prefix='matrix-e3-protected.')


def _scientific_projection(specification, allocation, calibration, frozen, assessment, adjudication, *, execution_plan, run_id, receipts):
    from empirical_lawhood.api.protected_e3_read_projection import scientific_projection
    return scientific_projection(specification, allocation, calibration, frozen, assessment, adjudication,
        execution_plan=execution_plan, run_id=run_id, receipts=receipts,
        conditional_reasons=conditional_reasons, adjudication_task_id=adjudication_task_id,
        statistical_task_id=statistical_task_id)


def _read_protected_e3_result(*, selected, artifact_writer, run_id, reveal_authority_id=None, allow_partial=False,
                              expected_package=None, include_original_products=False):
    """Read actual retained scientific products; never schedule or reacquire."""
    validate_stable_id(run_id)
    if type(allow_partial) is not bool:
        raise TypeError('protected E3 read requires an explicit partial selection')
    specification, allocation = _original_design(selected)
    # Finite control authentication here; task publications get separate scopes.
    # No mutable global cache survives this read or grants outcome authority.
    writer = artifact_writer
    package = _current_control(writer=writer, run_id=run_id, name='campaign-package',
        record_type=ExperimentPackage, maximum_bytes=MAX_CAMPAIGN_PACKAGE_BYTES)
    if expected_package is not None and package != expected_package:
        raise PermissionError('PROTECTED_E3_READ_EXACT_EXPECTED_PACKAGE_REQUIRED')
    if (ObjectIdentity.from_record(package.issued_study.candidate.candidate_id, package.issued_study.candidate)
            != selected.association.candidate
            or package.issued_study.source_closure != selected.implementation
            or package.run_plan_id != run_id):
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_CANDIDATE_AND_SOURCE_REQUIRED')
    if not allow_partial:
        _authorize(writer, package, reveal_authority_id)
    # This replays only persisted issued metadata and its stored registry.
    # It never compiles a current source checkout or domain operation catalog.
    plan = authenticate_current_execution_plan(package=package, issued=package.issued_study,
        run_id=run_id, writer=writer)
    if {task.task_id for task in plan.tasks} != {task.task_id for task in selected.projection.tasks}:
        raise PermissionError('PROTECTED_E3_READ_ORIGINAL_COMPLETE_TASK_CENSUS_REQUIRED')
    if allow_partial:
        return {'scientific_status': 'UNASSESSED', 'admission_status': 'UNASSESSED',
            'evaluability': 'DEFERRED', 'qualification': 'NOT_ESTABLISHED',
            'reason_codes': ['PARTIAL_READ_SCIENTIFIC_ASSESSMENT_DEFERRED'],
            'denominators': {public_role: {'assigned_units': len(allocation.unit_ids(role)),
                'units': list(allocation.unit_ids(role)), 'assessed_units': None}
                for public_role, role in (('calibration', 'calibration'), ('confirmation', 'evaluation'))},
            'calibration': None, 'assessment': None, 'adjudication': None, 'training_provenance': None,
            'secondary_response_readout': {'status': 'DEFERRED_PARTIAL_READ'},
            'assigned_tasks': len(plan.tasks), 'typed_product_validation': 'DEFERRED',
            'scientific_completion': 'NOT_ESTABLISHED', 'native_contact': 'none'}
    writer = _retained_scientific_writer(package, plan, writer)
    receipts, terminal = _completed_receipts(writer, package, plan)
    ids = (specification.identity, allocation.identity)
    requests = (('models', statistical_task_id(*ids, 'fit'), ProtectedE3ModelSet),
        ('calibration', statistical_task_id(*ids, 'calibrate'), ProtectedE3Calibration),
        ('calibrated_freeze', statistical_task_id(*ids, 'freeze', mode='calibration'), ProtectedE3FrozenProducts),
        ('assessment', statistical_task_id(*ids, 'assess'), ProtectedE3Assessment),
        ('adjudication', adjudication_task_id(*ids), ScientificAdjudicationRecord))
    products, custody = {}, {}
    for name, task_id, kind in requests:
        products[name], custody[name] = _product(writer, plan, receipts, task_id, kind)
    result = _scientific_projection(specification, allocation, products['calibration'], products['calibrated_freeze'],
        products['assessment'], products['adjudication'],
        execution_plan=ObjectIdentity.from_record(plan.execution_plan_id, plan), run_id=run_id, receipts=receipts)
    training = fitted_training_provenance(specification, allocation, products['models'], products['calibrated_freeze'])
    secondary, secondary_custody = {"status": "NOT_SUPPLIED", "reason": "NO_AUTHENTICATED_FROZEN_SECONDARY_TARGET"}, ()
    report = {**result, 'training_provenance': training, 'secondary_response_readout': secondary,
        'secondary_response_custody': secondary_custody, 'custody': custody, 'execution_plan': ObjectIdentity.from_record(plan.execution_plan_id, plan).to_document(),
        'terminal': ObjectIdentity.from_record(terminal.terminal_event_id, terminal).to_document(),
        'completed_tasks': len(receipts), 'typed_product_validation': 'COMPLETE',
        'scientific_completion': 'RETAINED_ADJUDICATION', 'native_contact': 'none'}
    if not include_original_products:
        _authorize(artifact_writer, package, reveal_authority_id)
        return report
    models = products['models']
    model_freeze, _ = _product(writer, plan, receipts,
        statistical_task_id(*ids, 'freeze', mode='model'), ProtectedE3FrozenProducts)
    prefit, _ = _product(writer, plan, receipts, statistical_task_id(*ids, 'fit'), ProtectedE3PreFitJoin)
    _authorize(artifact_writer, package, reveal_authority_id)
    return ProtectedE3OriginalProducts(package, plan, specification, allocation, receipts, models, model_freeze,
        products['calibration'], products['calibrated_freeze'], prefit, report)

@dataclass(frozen=True, slots=True)
class ProtectedE3OriginalProducts:
    """Data from one fresh read call; never a reusable authority or writer.

    Receipt records and typed products retain their original canonical identities.
    The outer receipt map is immutable. A later protected entry must authenticate
    its own current grants, source and receipt closure.
    """

    package: ExperimentPackage
    execution_plan: ExecutionPlan
    specification: MatrixResponseErrorSpecification
    allocation: UnitAllocation
    receipts: Mapping[str, CanonicalTaskReceipt]
    models: ProtectedE3ModelSet
    model_freeze: ProtectedE3FrozenProducts
    calibration: ProtectedE3Calibration
    calibrated_freeze: ProtectedE3FrozenProducts
    prefit: ProtectedE3PreFitJoin
    report: dict

    def __post_init__(self):
        object.__setattr__(self, "receipts", MappingProxyType(dict(self.receipts)))


def read_protected_e3_original_products(*, selected, artifact_writer, run_id,
                                       expected_package, reveal_authority_id):
    """Authenticate original products once within this bounded read lifetime.

    The expected package is an independent exact-byte selector, not a receipt or
    an authority substitute. All actual control, grant, output and source joins
    are replayed by the same owner used by the unchanged public report route.
    """
    if type(expected_package) is not ExperimentPackage or expected_package.run_plan_id != run_id:
        raise PermissionError('PROTECTED_E3_READ_EXACT_EXPECTED_PACKAGE_REQUIRED')
    # The core owns finite control/receipt/output verification scopes. An
    # outer scope would retain every receipt snapshot and recheck the growing
    # whole-run census on each read. Sharing typed data grants no authority.
    return _read_protected_e3_result(selected=selected, artifact_writer=artifact_writer,
        run_id=run_id, reveal_authority_id=reveal_authority_id,
        expected_package=expected_package, include_original_products=True)


def read_protected_e3_result(*, selected, artifact_writer, run_id, reveal_authority_id=None, allow_partial=False):
    """Read actual retained scientific products; never schedule or reacquire."""
    return _read_protected_e3_result(selected=selected, artifact_writer=artifact_writer,
        run_id=run_id, reveal_authority_id=reveal_authority_id, allow_partial=allow_partial)
