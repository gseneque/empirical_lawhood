# SPDX-License-Identifier: MPL-2.0
"""Shared prefix custody projection after each domain's exact input joins."""
from empirical_lawhood.runtime.execution import TaskContext
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.native_subwork import NativeSubworkDefinition, NativeSubworkRoster
from empirical_lawhood.runtime.prepared_native_invocation import PreparedNativeWork


def prepare_prefix_native_work(operands, *, context: TaskContext,
        expected_parent: NativeEffectContact, native_contract) -> PreparedNativeWork:
    """Shared work projection after the owning decoder's exact input joins."""
    source = operands.source
    if type(expected_parent) is not NativeEffectContact:
        raise TypeError("protected E3 prefix requires its exact anticipated ordinary parent")
    expected_parent.__post_init__()
    if ((expected_parent.run_id, expected_parent.task_id, expected_parent.attempt_id,
            expected_parent.implementation_commit, expected_parent.input_materialization_ids,
            expected_parent.dependency_receipt_ids) !=
            (context.run_id, context.task_id, context.attempt_id, source.provenance.observed_git_head,
                context.input_materialization_ids, context.dependency_receipt_ids)):
        raise ValueError("protected E3 prefix changes its actual anticipated ordinary parent")
    prepared = context.prepared_invocation
    if prepared is not None:
        if expected_parent != prepared.expected_parent_contact:
            raise ValueError("protected E3 prefix changes its complete prepared execution plan or task")
        implementation = prepared.implementation
        if ((source.provenance.package_sources, source.provenance.code_sources_sha256,
                source.provenance.dependency_lock_sha256, source.provenance.observed_git_head) !=
                (implementation.package_sources, implementation.code_sources_sha256,
                    implementation.dependency_lock_sha256, implementation.observed_git_head)):
            raise ValueError("protected E3 prefix changes its selected producing source or dependency lock")
    _, configuration, _, operation, sources, outputs = native_contract(
        operands.config, operands.manifest, specification=operands.specification)
    definition = NativeSubworkDefinition("prefix." + source.root_id, operation, expected_parent,
        configuration, sources, source.provenance.code_sources_sha256, source.provenance.dependency_lock_sha256,
        context.input_materialization_ids,
        tuple(sorted((source.root.stream_identity(stream) for stream in source.root.streams), key=lambda row: row.object_id)),
        outputs)
    roster = NativeSubworkRoster("selected.native-subwork", expected_parent, (definition.identity,))
    return PreparedNativeWork(expected_parent, (source.root.root.independent_group_id,),
        ("prefix." + source.root_id,), (definition,), (roster,))
