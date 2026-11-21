# SPDX-License-Identifier: MPL-2.0
"""Disclosed locator metadata only; no original execution or authority exists."""

from hashlib import sha256
import json

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.plans import ExecutionPlan
from empirical_lawhood.execution.recursive_qualified_parents import RecursivePriorExecutionBinding, RecursivePriorNativeBinding, inspect_prior_execution_bindings


def disclosed_locator(group, *, native_count=216, companion_count=4):
    """Invent bounded metadata to exercise representation, never custody."""
    prefix = f'disclosed.prior.{group}'

    def pin(suffix, schema):
        name = prefix + '.' + suffix
        return ObjectIdentity(name, schema, '1.0.0', sha256(name.encode()).hexdigest())

    natives = []
    for number in range(native_count):
        definition = pin(f'native.{number}', 'empirical-lawhood/runtime/native-subwork-definition')
        natives.append(RecursivePriorNativeBinding(prefix + '.native-task', definition,
            ObjectIdentity('completion.' + definition.object_id,
                'empirical-lawhood/runtime/native-subwork-completion', '1.0.0', sha256(
                    ('disclosed.completion.' + definition.object_id).encode()).hexdigest()),
            pin(f'native-receipt.{number}', CanonicalTaskReceipt.SCHEMA)))
    return RecursivePriorExecutionBinding(prefix + '.binding',
        pin('issue', 'empirical-lawhood/runtime/issued-executable-study-manifest'),
        pin('authority', 'empirical-lawhood/planning/study-operation-authority'),
        pin('package', 'empirical-lawhood/api/experiment-package'), pin('plan', ExecutionPlan.SCHEMA),
        prefix + '.run', prefix + '.collect', pin('receipt', CanonicalTaskReceipt.SCHEMA),
        prefix + '.artifact', pin('result', 'empirical-lawhood/testing/prior-result'),
        additional_output_schema_ids=tuple(f'empirical-lawhood/testing/companion-{number}' for number in range(companion_count)),
        native_subwork=tuple(natives))


def main():
    report = inspect_prior_execution_bindings((disclosed_locator(0), disclosed_locator(1)))
    report['fixture_scope'] = 'EXPOSED_LOCATOR_METADATA_ONLY'
    report['qualification'] = 'NOT_ESTABLISHED'
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
