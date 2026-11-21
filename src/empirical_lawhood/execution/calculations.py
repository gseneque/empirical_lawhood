# SPDX-License-Identifier: MPL-2.0
"""Shared canonical worker adaptation for code-owned pure calculations."""
from __future__ import annotations

from empirical_lawhood.execution.execution import RunnerResult, TaskContext, TaskOutputPayload
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck

class CalculationRunner:
    """Internal adapter to the existing task runner; pure calculations own no I/O."""
    def __init__(self, calculation):
        self.calculation = calculation
        self.manifest = calculation.operation.manifest()

    def execute(self, context: TaskContext) -> RunnerResult:
        calculation = self.calculation
        try:
            declaration = calculation.operation
            if (context.config.config_schema != calculation.config_type.SCHEMA
                    or context.permissions != declaration.permissions
                    or context.outcome_access is not declaration.outcome_access
                    or not declaration.resources.contains(context.resource_budget)):
                raise ValueError("calculation worker differs from its frozen capability, permissions or resource contract")
            input_by_schema = {port.record_type.SCHEMA: port for port in calculation.inputs}
            received, config = {}, None
            for port in context.input_ports:
                if port.media_type != "application/json":
                    raise ValueError("calculation worker input changes its canonical media type")
                if port.payload_schema == calculation.config_type.SCHEMA:
                    if config is not None or port.artifact_id != context.config.artifact_id:
                        raise ValueError("calculation worker substitutes its unique configuration input")
                    config = port.decode_canonical_record(calculation.config_type,
                        maximum_bytes=calculation.maximum_config_bytes)
                    if config.fingerprint() != context.config.content_sha256:
                        raise ValueError("calculation worker configuration differs from the authored bytes")
                else:
                    declared = input_by_schema.get(port.payload_schema)
                    if declared is None or declared.name in received:
                        raise ValueError("calculation worker input changes its complete role census")
                    received[declared.name] = port.decode_canonical_record(declared.record_type,
                        maximum_bytes=declared.maximum_bytes)
            if config is None:
                raise ValueError("calculation worker lacks its authored configuration")
            expected_outputs = tuple(sorted((context.task_id + "." + port.name,
                port.record_type.SCHEMA) for port in calculation.outputs))
            actual_outputs = tuple((port.output_id, port.payload_schema) for port in context.output_ports)
            if actual_outputs != expected_outputs or any(port.profile is not ArtifactProfile.CANONICAL_JSON
                    or port.media_type != "application/json" for port in context.output_ports):
                raise ValueError("calculation worker output changes its complete declared contract")
            products = calculation(config, received)
            outputs = tuple(TaskOutputPayload(context.task_id + "." + name, product.canonical_bytes())
                for name, product in sorted(products.items()))
            return RunnerResult(outputs, (ReceiptCheck("calculation.complete-census", True, ()),))
        finally:
            # Each port's close performs its original current-access/final-byte checks.
            # ExitStack ensures all guards close even when one guard refuses.
            from contextlib import ExitStack
            with ExitStack() as stack:
                for port in reversed(context.input_ports):
                    stack.callback(port.close)
