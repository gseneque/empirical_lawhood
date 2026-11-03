# SPDX-License-Identifier: MPL-2.0
"""Pure selected E3 prefix readers over exact current source envelopes.

The original scheduled owner supplies every numerical equation. These wrappers
bind current typed evidence and immutable array bytes; they acquire nothing and
confer no custody, source qualification, issue, execution or outcome authority.
The owning API must authenticate the actual input/configuration receipts.
"""

from contextlib import contextmanager

from empirical_lawhood.adapters.methods.matrix_dataset_readers import MatrixDatasetBridge, retained_array_mappings
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled, science
from empirical_lawhood.infrastructure.dataset_readers import ArrayDatasetReader
from empirical_lawhood.kernel.matrix_inputs import MAXIMUM_MATRIX_ARRAY_BYTES
from empirical_lawhood.runtime.execution import WorkerInputPort

from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_prefix_records import (
    ConfiguredProtectedE3CausalPrefix, ConfiguredProtectedE3FrameAssessment, ConfiguredProtectedE3NumericalAssessment,
    ConfiguredProtectedE3PrefixHistory, ConfiguredProtectedE3PrefixWitness,
)
from .configured_protected_source_records import (
    NAMESPACE, ProtectedE3NativeSourceManifest, ConfiguredProtectedE3SourceConfig, identity,
)


ArrayInput = bytes | WorkerInputPort | MatrixDatasetBridge | ArrayDatasetReader

def _exact(record, kind):
    if type(record) is not kind:
        raise TypeError("protected E3 prefix reader requires exact current scientific records")
    record.__post_init__()


def _bound_history(history, prefix_config, manifest, specification):
    _exact(history, ConfiguredProtectedE3PrefixHistory)
    source = history.validate_source(prefix_config, manifest, specification=specification)
    measurement = specification.measurement
    if (source.policy.cutoff_tick != measurement.origin_tick or source.policy.origin_sector != "Y"
            or source.coordinate.primary_view.timestep != measurement.primary_timestep
            or source.coordinate.fine_view.timestep != measurement.fine_timestep):
        raise ValueError("protected E3 prefix reader changes selected PRIMARY-Y cutoff or paired clocks")
    return source


def _raw(raw):
    if type(raw) not in (bytes, WorkerInputPort, MatrixDatasetBridge, ArrayDatasetReader):
        raise TypeError("protected E3 prefix reader requires immutable bytes or an authenticated array dataset")


@contextmanager
def _array_values(owners, inputs):
    """Use one complete verified session for each original scientific operand."""
    if len(owners) != len(inputs):
        raise ValueError("protected E3 reader omits an exact original array input")
    for value in inputs:
        _raw(value)
    selected = iter(inputs)
    with retained_array_mappings(owners, lambda artifact: next(selected),
            maximum_chunk_bytes=1024 * 1024, maximum_slice_bytes=MAXIMUM_MATRIX_ARRAY_BYTES) as values:
        yield values


@contextmanager
def _prefix_values(source, history, prefix_input, *others):
    science.validate_prefix_operand(source, history.arrays)
    with _array_values((history.arrays, *(owner for owner, _ in others)),
            (prefix_input, *(value for _, value in others))) as values:
        science.validate_prefix_arrays(source, values[0])
        yield values


def _product_id(role, source):
    return role + "." + NAMESPACE + "." + source.root_id


def _frame_product(source, witness, controls):
    result = ConfiguredProtectedE3FrameAssessment(_product_id("frames", source), scheduled.identity(source), identity(witness),
        scheduled.identity(source.policy.factor_numerical_design), controls,
        all(c.disposition in ("SATISFIED", "NOT_APPLICABLE") for c in controls))
    result.validate_source(source, witness)
    return result


def assess_prefix(history: ConfiguredProtectedE3PrefixHistory, prefix_raw: ArrayInput, *,
        prefix_config: ConfiguredProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
        specification: MatrixResponseErrorSpecification) -> ConfiguredProtectedE3NumericalAssessment:
    """Read every original phase/noise/clock coordinate through cutoff256."""
    source = _bound_history(history, prefix_config, manifest, specification)
    with _prefix_values(source, history, prefix_raw) as (arrays,):
        controls = science.assess_prefix_values(source, arrays)
    result = ConfiguredProtectedE3NumericalAssessment(_product_id("numerical", source), scheduled.identity(source), identity(history),
        scheduled.identity(source.numerical_design), controls, all(c.disposition == "SATISFIED" for c in controls))
    result.validate_source(source, history)
    return result


def measure_prefix(history: ConfiguredProtectedE3PrefixHistory, numerical: ConfiguredProtectedE3NumericalAssessment,
        prefix_raw: ArrayInput, *, prefix_config: ConfiguredProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
        specification: MatrixResponseErrorSpecification, artifact_id: str) -> tuple[bytes, ConfiguredProtectedE3PrefixWitness]:
    """Measure the unchanged complete paired-view/sector prefix lattice."""
    source = _bound_history(history, prefix_config, manifest, specification)
    _exact(numerical, ConfiguredProtectedE3NumericalAssessment)
    numerical.validate_source(source, history)
    with _prefix_values(source, history, prefix_raw) as (native,):
        arrays, traces = science.measure_prefix_values(source, native)
    raw, operand = science._array_product(source, arrays, role="PREFIX_DIAGNOSTICS", artifact_id=artifact_id,
        producers=(scheduled.identity(source), identity(history), identity(numerical)),
        nonfinite=tuple(name for name in arrays if not name.endswith(("_ticks", "_available", "_identifiable"))))
    result = ConfiguredProtectedE3PrefixWitness(_product_id("witness", source), scheduled.identity(source), identity(history),
        identity(numerical), scheduled.identity(source.policy), traces, operand)
    result.validate_source(source, history, numerical)
    return raw, result


def check_frames(history: ConfiguredProtectedE3PrefixHistory, numerical: ConfiguredProtectedE3NumericalAssessment,
        witness: ConfiguredProtectedE3PrefixWitness, prefix_raw: ArrayInput, diagnostic_raw: ArrayInput, *,
        prefix_config: ConfiguredProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
        specification: MatrixResponseErrorSpecification) -> ConfiguredProtectedE3FrameAssessment:
    """Independently read raw operators and all15 retained eigenpairs."""
    source = _bound_history(history, prefix_config, manifest, specification)
    _exact(witness, ConfiguredProtectedE3PrefixWitness)
    witness.validate_source(source, history, numerical)
    with _prefix_values(source, history, prefix_raw, (witness.arrays, diagnostic_raw)) as (native, diagnostic):
        controls = science.check_prefix_frame_values(source, witness.traces, native, diagnostic)
    return _frame_product(source, witness, controls)


def causal_delivery(history: ConfiguredProtectedE3PrefixHistory, numerical: ConfiguredProtectedE3NumericalAssessment,
        witness: ConfiguredProtectedE3PrefixWitness, assessment: ConfiguredProtectedE3FrameAssessment,
        prefix_raw: ArrayInput, diagnostic_raw: ArrayInput, *, prefix_config: ConfiguredProtectedE3SourceConfig,
        manifest: ProtectedE3NativeSourceManifest, specification: MatrixResponseErrorSpecification,
        artifact_id: str, raw: bytes | None = None) -> tuple[bytes, ConfiguredProtectedE3CausalPrefix]:
    """Retain exact nonuse/missingness and deliver no innovations or RNG state."""
    source = _bound_history(history, prefix_config, manifest, specification)
    _exact(assessment, ConfiguredProtectedE3FrameAssessment)
    _exact(witness, ConfiguredProtectedE3PrefixWitness)
    witness.validate_source(source, history, numerical)
    if raw is not None:
        _raw(raw)
    with _prefix_values(source, history, prefix_raw, (witness.arrays, diagnostic_raw)) as (native, diagnostic):
        observed = _frame_product(source, witness,
            science.check_prefix_frame_values(source, witness.traces, native, diagnostic))
        if observed != assessment:
            raise ValueError("protected E3 causal delivery substitutes retained independent frame assessment")
        arrays, frame_sha, disposition, reason = science.causal_cutoff_values(source, witness.traces,
            numerical.numerical_pass, assessment.numerical_pass, native, diagnostic)
    encoded, operand = science._array_product(source, arrays, role="CAUSAL_STATE", artifact_id=artifact_id,
        producers=(scheduled.identity(source), identity(history), identity(witness), identity(assessment)),
        nonfinite=() if disposition == "AVAILABLE" else ("frame",), raw=raw)
    result = ConfiguredProtectedE3CausalPrefix(_product_id("causal", source), scheduled.identity(source), identity(history), identity(numerical),
        identity(witness), identity(assessment), scheduled.identity(source.policy), source.root.root, source.policy.cutoff_tick,
        frame_sha, disposition, reason, operand)
    result.validate_source(source, history, numerical, witness, assessment)
    return encoded, result
