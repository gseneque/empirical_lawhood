# SPDX-License-Identifier: MPL-2.0
"""PURE E3 worker orchestration behind exact version-specific input owners.

The facades supply their installed decoder, scientific method and result owner.
No native operation, receipt/array validation, scientific algorithm or immutable
record edition is replaced by these control-flow mechanics.
"""
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload


def execute_prefix_pure(runner, context, *, decode_inputs, phases, science):
    try:
        inputs = decode_inputs(context, runner.phase, manifest=runner.manifest)
        arguments = dict(prefix_config=inputs.prefix_config, manifest=inputs.source_manifest, specification=inputs.specification)
        raw = None
        if runner.phase is phases.NUMERICAL:
            product = science.assess_prefix(inputs.history, inputs.prefix_raw, **arguments)
        elif runner.phase is phases.MEASURE:
            artifact = next(port.logical_artifact_id for port in inputs.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, product = science.measure_prefix(inputs.history, inputs.numerical, inputs.prefix_raw, artifact_id=artifact, **arguments)
        elif runner.phase is phases.CHECK:
            product = science.check_frames(inputs.history, inputs.numerical, inputs.witness,
                inputs.prefix_raw, inputs.diagnostic_raw, **arguments)
        else:
            artifact = next(port.logical_artifact_id for port in inputs.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, product = science.causal_delivery(inputs.history, inputs.numerical, inputs.witness, inputs.assessment,
                inputs.prefix_raw, inputs.diagnostic_raw, artifact_id=artifact, **arguments)
        payloads = {product.SCHEMA: product.canonical_bytes(), MATRIX_ARRAY_SCHEMA: raw}
        return RunnerResult(tuple(TaskOutputPayload(port.output_id, payloads[port.payload_schema]) for port in inputs.output_ports),
            (ReceiptCheck("protected-e3-pure-prefix-current-context-and-complete-dependency-custody", True, ()),))
    finally:
        for port in context.input_ports:
            port.close()


def execute_response_pure(runner, context, *, decode_inputs, statistical_task_id, array_roles, science, limits, make_result):
    try:
        if runner.operation == "responses":
            raise ValueError("protected E3 response requires its existing issued native-subwork authorization")
        operands = decode_inputs(context, capability=runner.manifest, operation=runner.operation, statistical_task_id=statistical_task_id)
        records = operands.records
        fetch = lambda artifact: operands.ports[next(name for name in array_roles(runner.operation)
            if operands.ports[name].artifact_id == artifact.artifact_id)]
        if runner.operation == "physical-forecast":
            array_port = next(port for port in context.output_ports if port.profile is ArtifactProfile.MATRIX_ARRAY_NPZ)
            raw, product = science.forecast_physical(operands.config, records["causal"],
                **{key.replace("-", "_"): records[key] for key in ("specification", "protocol", "numerical-profile", "mathematical-protocol", "projection")},
                fetch=fetch, **limits, artifact_id=array_port.logical_artifact_id,
                forecast_id="physical." + context.task_id, outcome_access=operands.outcome_access, visibility_ceiling=operands.visibility)
            payloads = {"arrays": raw, "product": product.canonical_bytes()}
        else:
            arguments = operands.science_arguments()
            score = science.assess_responses(operands.config, records["native-config"], records["responses"], **arguments,
                fetch=fetch, **limits, score_id="score." + context.task_id)
            outcome = science.project_outcome(operands.config, records["native-config"], records["responses"], score,
                **arguments, record_id="outcome." + context.task_id)
            payloads = {"score": score.canonical_bytes(), "outcome": outcome.canonical_bytes()}
        return make_result(context, payloads)
    finally:
        for port in context.input_ports:
            port.close()
