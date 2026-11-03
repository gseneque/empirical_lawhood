# SPDX-License-Identifier: MPL-2.0
"""Read the four E3 products across an authenticated unfinished continuation.

The model and its freeze retain their actual earlier producing plan. Calibration
belongs to the completed new plan. No combined plan or receipt is manufactured.
"""
from contextlib import contextmanager
from dataclasses import dataclass

from empirical_lawhood.kernel.provenance import ObjectIdentity


@dataclass(frozen=True, slots=True)
class ImportedE3ProductCustody:
    original: object
    package: object
    plan: object
    reveal: object
    receipt: object
    logical: object
    prefixes: tuple
    producer: object
    imported: bool
    require_access: object


@contextmanager
def imported_e3_product_custody(writer, originals, codecs):
    """Keep all actual producers inside their complete continuation proof."""
    from .configured_e3_retained_read import continued_plan_read
    from .matrix_sampling_runtime import _original_product_metadata
    from .protected_e3_read_custody import configured_receipt_read
    from .recursive_qualified_parents import (
        _ParentReadScope, _semantic_writer,
        _require_parent_authorities_current,
    )
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_unfinished_execution import ConfiguredE3UnfinishedExecution
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_closeout_execution import ConfiguredE3ClosedExecution

    if len(originals) != 4:
        raise PermissionError('imported E3 products require their four original products')
    with writer.read_context() as controls:
        read_scope = _ParentReadScope(controls)
        entries = tuple(_original_product_metadata(controls, original, expected,
            _control_reader=read_scope.plan_reader) for original, expected in originals)
        plans = tuple(read_scope.plan_reader.authenticate(package=package, issued=issued,
            receipt=receipt, logical=logical, capability_prefixes=prefixes)
            for package, issued, _, receipt, logical, prefixes in entries)
        for (original, _), plan in zip(originals, plans, strict=True):
            if ObjectIdentity.from_record(plan.execution_plan_id, plan) != original.prior_execution.execution_plan:
                raise PermissionError('imported E3 product substitutes its original execution plan')
        candidates = {plan.source_plan.object_id: (entry, plan)
            for entry, plan in zip(entries, plans, strict=True)
            if any(spec.expected_payload_schema in (ConfiguredE3UnfinishedExecution.SCHEMA, ConfiguredE3ClosedExecution.SCHEMA)
                for task in plan.tasks for spec in task.external_inputs)}
        if len(candidates) != 1:
            raise PermissionError('imported E3 products lack one actual unfinished continuation')
        (entry, plan), = candidates.values()
        package, _, reveal, _, _, _ = entry
        semantic = _semantic_writer(package, plan, writer, codecs)
        with configured_receipt_read(semantic, package, plan, reveal_authority_id=reveal.authority_id) as completed, \
                continued_plan_read(writer=completed.writer, plan=plan, receipts=completed.receipts) as retained:
            if retained is None or retained.unfinished is None or retained.predecessor is None:
                raise PermissionError('imported E3 products lose their authenticated predecessor')
            predecessor, boundary = retained.predecessor, retained.unfinished
            runs = {value.prior_execution.run_id for value, _ in originals}
            original_owners = {value.prior_execution.task_id: (predecessor.product_source(value.prior_execution.task_id)
                if hasattr(predecessor, 'product_source') else predecessor) for value, _ in originals
                if value.prior_execution.task_id in predecessor.receipts}
            if runs != {package.run_plan_id, *(owner.package.run_plan_id for owner in original_owners.values())}:
                raise PermissionError('imported E3 products combine an unrelated original run')
            imported = {row.logical.logical_artifact_id: row for row in boundary.imported_outputs}
            seen, products = set(), []
            def require_access():
                predecessor.require_access()
                completed.require_access()
            for (original, expected), before, producing_plan in zip(originals, entries, plans, strict=True):
                binding = original.prior_execution
                task, = (task for task in producing_plan.tasks if task.task_id == binding.task_id)
                phase = task.capability.capability_key
                owner = original_owners.get(binding.task_id)
                old = owner is not None
                allowed = ('retained-fit', 'retained-model-freeze') if old else ('calibrate', 'calibration-freeze')
                if phase not in tuple('matrix-e3-configured-protected.' + name for name in allowed) or phase in seen:
                    raise PermissionError('imported E3 products change their four exact producing phases')
                seen.add(phase)
                original_package = owner.package if old else package
                original_receipts = owner.receipts if old else completed.receipts
                expected_plan = owner.plan if old else plan
                receipt = original_receipts.get(binding.task_id)
                if (before[0] != original_package or producing_plan != expected_plan or receipt != before[3]
                        or receipt is None or ObjectIdentity.from_record(receipt.receipt_id, receipt) != binding.receipt):
                    raise PermissionError('imported E3 product changes its actual producing receipt')
                logical = before[4]
                if old:
                    row = imported.get(binding.logical_artifact_id)
                    if row is None or (row.task_id, row.receipt, row.logical) != (binding.task_id, binding.receipt, logical):
                        raise PermissionError('imported E3 product is absent from the current receipt-bound inputs')
                products.append(ImportedE3ProductCustody(original, original_package, producing_plan,
                    before[2], receipt, logical, before[5], owner if old else completed, old, require_access))
            require_access()
            yield tuple(products), read_scope
            for (original, expected), before in zip(originals, entries, strict=True):
                if _original_product_metadata(controls, original, expected, _control_reader=read_scope.plan_reader) != before:
                    raise PermissionError('imported E3 product grants or custody changed during its read')
            predecessor.require_current()
            completed.require_current()
        controls.require_verification_snapshot()
    _require_parent_authorities_current(tuple((original, entry[0])
        for (original, _), entry in zip(originals, entries, strict=True)), writer)


def read_imported_e3_products(writer, originals, codecs, *, scope_validator):
    from .recursive_qualified_parents import MAX_PARENT_BYTES, _output_payload

    if not callable(scope_validator):
        raise PermissionError('imported E3 products require their scientific scope validator')
    payloads = []
    with imported_e3_product_custody(writer, originals, codecs) as (products, read_scope):
        for value in products:
            value.require_access()
            if scope_validator(binding=value.original.prior_execution, package=value.package,
                    execution_plan=value.plan, receipt=value.receipt, logical=value.logical,
                    writer=value.producer.writer, read_scope=read_scope) is not None:
                raise PermissionError('original scientific scope validator must return no authority token')
            payloads.append(_output_payload(value.producer.writer, value.receipt, value.logical, MAX_PARENT_BYTES))
    return tuple(payloads)
