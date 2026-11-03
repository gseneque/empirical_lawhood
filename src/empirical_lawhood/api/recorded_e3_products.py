# SPDX-License-Identifier: MPL-2.0
"""Consume original frozen E3 products without reconstructing their computation.

The issued plans and actual receipts supply producer custody. Typed products
keep their exact scientific contracts. Current reveals are checked before
protected bytes and after the finite read; this is not a scientific reanalysis.
"""
from contextlib import contextmanager
from types import MappingProxyType

from empirical_lawhood.kernel.provenance import ObjectIdentity

from .retained_e3_evidence import retained_e3_evidence_context


def _identity(record, name='record_id'):
    return ObjectIdentity.from_record(getattr(record, name), record)


def _boundary(read, producer):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3UnfinishedExecution
    from .matrix_selected_runtime import _published_input
    kinds = {kind.SCHEMA: kind for kind in (ConfiguredE3ClosedExecution, ConfiguredE3UnfinishedExecution)}
    specs = tuple(spec for task in producer.plan.tasks for spec in task.external_inputs
        if spec.expected_payload_schema in kinds)
    if not specs:
        return None
    if any(spec != specs[0] for spec in specs):
        raise PermissionError('recorded E3 products change their complete continuation selection')
    scope = _published_input(producer.writer, producer.package.run_plan_id, specs[0], kinds[specs[0].expected_payload_schema])
    if (scope.retention.continued_run_id != producer.package.run_plan_id
            or set(scope.unfinished_task_ids) != {task.task_id for task in producer.plan.tasks}):
        raise PermissionError('recorded E3 products change their original execution suffix')
    read.boundary(scope)
    return scope


@contextmanager
def recorded_original_product_custody(writer, originals):
    """Join original product metadata inside the live recorded continuation.

    This owner does not open scientific product bodies. It keeps the actual
    model and calibration producers, imported receipts and current grants.
    """
    from .configured_e3_imported_products import ImportedE3ProductCustody
    from .recursive_qualified_parents import _ParentReadScope
    if len(originals) != 4:
        raise PermissionError('recorded E3 requires four original products')
    with retained_e3_evidence_context(writer) as read:
        metadata = tuple(read.product_metadata(original, expected) for original, expected in originals)
        owners = tuple(read.producer(original.prior_execution.run_id, original.reveal_authority.object_id)
            for original, _ in originals)
        distinct = {owner.package.run_plan_id: owner for owner in owners}
        boundaries = {run_id: _boundary(read, owner) for run_id, owner in distinct.items()}
        runs = set(boundaries)
        boundary = None
        if len(runs) > 1:
            values = tuple(value for value in boundaries.values() if value is not None)
            if len(runs) != 2 or len(values) != 1:
                raise PermissionError('recorded E3 combines unrelated original producers')
            boundary, = values
        scope = _ParentReadScope(read.writer, plan_reader=read.reader)
        products, seen = [], set()
        for (original, _), owner, data in zip(originals, owners, metadata, strict=True):
            package, _, reveal, receipt, logical, prefixes = data
            binding = original.prior_execution
            task = read.reader.execution_task(execution_plan=owner.plan, task_id=binding.task_id)
            phase = task.capability.capability_key
            imported = False
            if boundary is not None:
                imported = owner.package.run_plan_id != boundary.retention.continued_run_id
                allowed = ('retained-fit', 'retained-model-freeze') if imported else ('calibrate', 'calibration-freeze')
                if phase not in tuple('matrix-e3-configured-protected.' + name for name in allowed):
                    raise PermissionError('recorded E3 changes the original model/calibration producer roles')
                if imported:
                    actual_owner, actual_receipt = read.imported(boundary, binding.task_id)
                    if actual_owner.package != package or actual_receipt != receipt:
                        raise PermissionError('recorded E3 import substitutes the actual producer')
            if phase in seen:
                raise PermissionError('recorded E3 aliases an original producing phase')
            seen.add(phase)
            read.require_access(owner)
            products.append(ImportedE3ProductCustody(original, package, owner.plan, reveal,
                receipt, logical, prefixes, owner, imported,
                lambda owner=owner: read.require_access(owner)))
        yield tuple(products), scope
        for (original, expected), before in zip(originals, metadata, strict=True):
            if read.product_metadata(original, expected) != before:
                raise PermissionError('recorded E3 product custody changed during its read')
        read.require_access()


def recorded_original_members(writer, originals):
    """Collect complete original member facts without retrospective replay."""
    from .recursive_qualified_parents import _collect_receipt_closure
    from .selected_prepared_access import _receipt_closure_members
    members, completed = set(), set()
    with recorded_original_product_custody(writer,
            tuple((value, value.record) for value in originals)) as (products, scope):
        for value in products:
            value.require_access()
            original, owner = value.original, value.producer
            key = (original.prior_execution.run_id, original.issued_study,
                original.execution_authority, original.reveal_authority)
            if key in completed:
                continue
            closure = _collect_receipt_closure(value.package, value.plan, owner.writer,
                value.reveal, value.prefixes, control_reader=scope.plan_reader, allow_partial=value.imported)
            recorded = {row['task_id']: (row['receipt_id'], row['receipt_sha256'])
                for row in owner.report['operational_census'] if row['operational_status'] == 'SUCCEEDED'}
            observed = {task_id: (receipt.receipt_id, receipt.fingerprint())
                for task_id, receipt in closure.by_task.items()}
            if observed != recorded:
                raise PermissionError('prepared recorded E3 closure changes its authenticated producing receipts')
            members.update(_receipt_closure_members(owner.writer, closure))
            completed.add(key)
            value.require_access()
    return members, completed


def read_recorded_original_products(writer, originals, codecs, *, scope_validator):
    """Authenticate the four original products, including their actual imports."""
    from .recursive_qualified_parents import MAX_PARENT_BYTES, _output_payload
    if not callable(scope_validator):
        raise PermissionError('recorded E3 requires its consuming scientific predicate')
    output = []
    with recorded_original_product_custody(writer, originals) as (products, scope):
        for value in products:
            value.require_access()
            if scope_validator(binding=value.original.prior_execution, package=value.package,
                    execution_plan=value.plan, receipt=value.receipt, logical=value.logical,
                    writer=value.producer.writer, read_scope=scope) is not None:
                raise PermissionError('original scientific predicate must return no authority token')
            output.append(_output_payload(value.producer.writer, value.receipt, value.logical, MAX_PARENT_BYTES))
            value.require_access()
    return tuple(output)


def _companion(read, producer, directory, expected_specification):
    """Read only the original operands pinned by the published companion."""
    from .prospective_experiment import _read_prospective_locator
    from .matrix_researcher_programme_lineage import read_published_record
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import configured_preparation_types
    from empirical_lawhood.kernel.experimental_design import UnitAllocation
    from empirical_lawhood.runtime.experiment_preparation import ExperimentInstanceBinding
    from empirical_lawhood.runtime.prospective_experiment import (
        ProspectiveExperimentAssociation, ASSOCIATION_FILENAME, INSTANCE_FILENAME,
        SPECIFICATION_FILENAME, ALLOCATION_FILENAME, source_filename,
    )
    from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave
    writer = read.writer
    association = _read_prospective_locator(directory / 'experiment', ASSOCIATION_FILENAME, writer,
        ProspectiveExperimentAssociation)
    packet = _read_prospective_locator(directory / 'prospective', 'authored-wave.json', writer, AuthoredRecursiveWave)
    if (association.candidate != _identity(producer.package.issued_study.candidate, 'candidate_id')
            or association.prospective_wave != _identity(packet, 'packet_id')
            or packet.implementation != ObjectIdentity.from_record('recursive-member.implementation',
                producer.package.issued_study.source_closure)):
        raise PermissionError('recorded E3 changes its actual issued child or source')
    members = {member.filename: member for member in association.members}

    def member(name, kind):
        read.require_access(producer)
        selected = members[name]
        record = read_published_record(writer,
            (directory / 'experiment' / name).relative_to(writer.root.contract.canonical_path).as_posix(),
            kind, selected.size_bytes)
        if ObjectIdentity.from_record(selected.identity.object_id, record) != selected.identity:
            raise PermissionError('recorded E3 changes its exact original companion operand')
        return record

    instance = member(INSTANCE_FILENAME, ExperimentInstanceBinding)
    specification = member(SPECIFICATION_FILENAME, ConfiguredProtectedE3Specification)
    allocation = member(ALLOCATION_FILENAME, UnitAllocation)
    if (instance.specification != specification.identity or instance.allocation != allocation.identity
            or expected_specification != specification.identity or specification.evidence_scope != 'PROSPECTIVE_REQUIRED'):
        raise PermissionError('recorded E3 changes its original scientific scope or allocation')
    kinds = {(kind.SCHEMA, kind.VERSION): kind for kind in configured_preparation_types()}
    refs = tuple(pin for pin in instance.sources if (pin.object_schema, pin.object_version) in kinds)
    if len(refs) != 1:
        raise PermissionError('recorded E3 omits its original configured preparation')
    pin, = refs
    preparation = member(source_filename(pin), kinds[pin.object_schema, pin.object_version])
    if _identity(preparation, 'selection_id') != pin:
        raise PermissionError('recorded E3 changes its original preparation identity')
    return specification, allocation, preparation


@contextmanager
def recorded_programme_e3_products(context):
    """Expose exact consumed products; make no retrospective scientific claim."""
    from .matrix_researcher_programme_lineage import retained_run_binding
    from .domain_composition.matrix_configured_protected_response.scientific_read import ConfiguredE3OriginalProducts
    from .protected_e3_read_custody import product
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_methods import (
        ConfiguredProtectedE3ModelSet, ConfiguredProtectedE3FrozenProducts, ConfiguredProtectedE3Calibration,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_inputs import ConfiguredProtectedE3PreFitJoin
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import statistical_task_id
    origin = context.phase_origins.get('e3', context)
    binding = retained_run_binding(origin, 'e3')
    if binding is None:
        raise PermissionError('recorded E3 products require the actual retained completed run')
    authority = binding.authority
    candidates = () if context.operation is None else tuple(row for row in context.operation.authorities
        if row.package_path == authority.package_path)
    if candidates:
        if len(candidates) != 1:
            raise PermissionError('recorded E3 has ambiguous current reveal selections')
        authority, = candidates
    with retained_e3_evidence_context(context.writer) as read, read.writer.verification_dependencies() as dependencies:
        producer = read.producer(binding.run_id, authority.reveal_authority_id, package_pin=binding.package)
        if producer.report.get('execution_complete') is not True:
            raise PermissionError('recorded E3 requires every completed task in the original execution')
        specification, allocation, preparation = _companion(read, producer, origin.child_directory('e3'), binding.specification)
        boundary = _boundary(read, producer)
        if boundary != getattr(preparation, 'closeout', getattr(preparation, 'unfinished', None)):
            raise PermissionError('recorded E3 changes its original preparation/execution boundary')
        owners, receipts, outputs = {}, {}, {}
        requests = (
            ('models', 'fit', '', ConfiguredProtectedE3ModelSet),
            ('model_freeze', 'freeze', 'model', ConfiguredProtectedE3FrozenProducts),
            ('calibration', 'calibrate', '', ConfiguredProtectedE3Calibration),
            ('calibrated_freeze', 'freeze', 'calibration', ConfiguredProtectedE3FrozenProducts),
            ('prefit', 'fit', '', ConfiguredProtectedE3PreFitJoin),
        )
        for name, operation, mode, kind in requests:
            task_id = statistical_task_id(specification.identity, allocation.identity, operation, mode=mode)
            if task_id in {task.task_id for task in producer.plan.tasks}:
                owner, receipt = producer, read.receipt(producer, task_id)
            elif boundary is not None:
                owner, receipt = read.imported(boundary, task_id)
            else:
                raise PermissionError('recorded E3 omits an original frozen product')
            read.require_access(owner)
            outputs[name], _ = product(owner.writer, owner.plan, {task_id: receipt}, task_id, kind)
            owners[task_id], receipts[task_id] = owner, receipt
        if outputs['models'].reservation_join != _identity(outputs['prefit']):
            raise PermissionError('recorded E3 changes its frozen pre-fit join')

        def product_source(task_id):
            owner = owners[task_id]
            read.require_access(owner)
            return owner.package, owner.plan, receipts, _identity(owner.reveal, 'authority_id')

        def require_current():
            read.require_access()
            dependencies.require_current()

        require_current()
        yield ConfiguredE3OriginalProducts(producer.package, producer.plan, specification, preparation, allocation,
            MappingProxyType(receipts), outputs['models'], outputs['model_freeze'], outputs['calibration'],
            outputs['calibrated_freeze'], outputs['prefit'], MappingProxyType(producer.report),
            _identity(producer.reveal, 'authority_id'), require_current, product_source, read.require_access)
        require_current()
