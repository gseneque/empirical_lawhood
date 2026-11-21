"""Reusable supplied-array scientific records and calculations."""
from dataclasses import dataclass
from typing import Callable, Any
from collections.abc import Mapping
import numpy as np
import numpy.typing as npt
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.matrix.matrix_preparation.native_inputs import PreparationRoot
from empirical_lawhood.domains.matrix.matrix_preparation.contracts import PreparationProjectionRecord


Array = npt.NDArray[np.float64]


METHOD_MAXIMUM_BYTES = 16 * 1024**2


METHOD_METADATA = {
    "empirical_lawhood_units": '{"responses,halfwidths,scales":"hilbert-schmidt-native","probabilities,flags":"1","features":"declared-nine-observable-chart"}',
    "empirical_lawhood_frames": '{"response":"primary-preparent-mode;common-parents-views","scope":"exposed-development-only"}',
    "empirical_lawhood_clocks": '{"readout":"64,128,192,256,320-after-handoff","prospective-task":"independent-purpose;concealed-until-prediction-lock"}',
    "empirical_lawhood_keys": '["candidate","root","parent","numerical-view","audit","sign","readout"]',
}


NUMERICAL_SEMANTICS_SCHEMA = 'empirical-lawhood/methods/matrix-preparation/numerical-semantics-arrays-hdf5'


FORECAST_SCHEMA = 'empirical-lawhood/methods/matrix-preparation/locked-development-forecasts-hdf5'


DECISION_SCHEMA = 'empirical-lawhood/methods/matrix-preparation/locked-development-decisions-hdf5'


BENCHMARK_SCHEMA = 'empirical-lawhood/methods/matrix-preparation/description-and-benchmark-assessment-hdf5'


DESCRIPTION_SCHEMA = 'empirical-lawhood/methods/matrix-preparation/observable-description-assessment-hdf5'


TASK_ASSESSMENT_SCHEMA = 'empirical-lawhood/methods/matrix-preparation/development-task-assessment-hdf5'


@dataclass(frozen=True)
class ProjectedContext:
    context: str
    roots: tuple[PreparationRoot, ...]
    reports: tuple[PreparationProjectionRecord, ...]
    role: str
    arrays: Mapping[str, Array]

    @property
    def identities(self) -> tuple[ObjectIdentity, ...]:
        return tuple(ObjectIdentity.from_record(r.report_id, r) for r in self.reports)


def stack_projected_arrays(context, roots, reports, role, decoded):
    """Aggregate the supplied complete ordered root/view arrays into the declared tensor axes."""
    arrays = {}
    for key in decoded[0]:
        stacked = np.stack([v[key] for v in decoded]).reshape(64, 2, *decoded[0][key].shape)
        arrays[key] = stacked if key == "preparent_features" else stacked.swapaxes(1, 2)
    return ProjectedContext(context, roots, reports, role, arrays)


@dataclass(frozen=True)
class PreparedMethodArrays:
    """Scientific array outputs plus a pure report constructor over encoded bytes.

    The caller owns physical encoding. Each declaration is (schema, context,
    configuration identity, named array groups); finalize never opens a resource.
    """
    outputs: tuple[tuple[str, str, ObjectIdentity, Mapping[str, Mapping[str, Array]]], ...]
    finalize: Callable[..., Any]
