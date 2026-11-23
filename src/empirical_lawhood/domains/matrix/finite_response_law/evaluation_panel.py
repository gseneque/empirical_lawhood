"""All-assigned prospective operands, with separate response and use masks.

This is evaluator-only projection of authenticated native records. It performs
no prediction, admission, qualification, selection or complete-case filtering.
"""

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedEvaluationConfig
from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import FiniteResponseLawAssignedEvaluationNativeCompletion
from empirical_lawhood.domains.matrix.finite_response_law.evaluation_native_records import FiniteResponseLawEvaluationNativeCompletion
from empirical_lawhood.domains.matrix.finite_response_law.paired_assay import positive_pair_readouts
from empirical_lawhood.domains.matrix.finite_response_law.science import PARENTS

Array = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class EvaluationPanel:
    y: Array  # root, canonical pair, quantity, future, numerical view
    observed: NDArray[np.bool_]
    response_valid: NDArray[np.bool_]  # root, pair, signed response coordinate, future, view
    use_valid: NDArray[np.bool_]  # root, pair, future, view; includes actual HOLD
    prefix: Array
    handoff: Array
    parent_work: Array
    parent_indices: NDArray[np.int64]
    root_ids: tuple[str, ...]
    assigned_source: FiniteResponseLawAssignedEvaluationConfig | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.assigned_source is None:
            expected_ids = tuple(f"prospective-evaluation.r{r:03d}" for r in range(64))
        else:
            if type(self.assigned_source) is not FiniteResponseLawAssignedEvaluationConfig:
                raise ValueError("Evaluation panel requires the exact prospective allocation")
            roots = self.assigned_source.roots
            expected_ids = tuple(root.stage_unit for root in roots)
            if not np.array_equal(self.parent_indices, [PARENTS.index(root.assigned_parent) for root in roots]):
                raise ValueError("Evaluation panel changes an assigned preparation")
        shape = (64, 4, 8, 2, 2)
        if (
            self.y.shape != shape
            or self.y.dtype != np.float64
            or self.observed.shape != shape
            or self.observed.dtype != np.bool_
            or self.response_valid.shape != (64, 4, 2, 2, 2)
            or self.response_valid.dtype != np.bool_
            or self.use_valid.shape != (64, 4, 2, 2)
            or self.use_valid.dtype != np.bool_
            or any(
                a.shape != (64, 24, 2) or a.dtype != np.float64 for a in (self.prefix, self.handoff)
            )
            or self.parent_work.shape != (64, 2)
            or self.parent_work.dtype != np.float64
            or self.parent_indices.shape != (64,)
            or self.parent_indices.dtype != np.int64
            or ((self.parent_indices < 0) | (self.parent_indices >= 5)).any()
            or self.root_ids != expected_ids
            or np.any(self.observed != np.isfinite(self.y))
            or np.any(self.response_valid & ~self.observed[:, :, :2])
            or np.any(self.use_valid & ~self.observed.all(axis=2))
        ):
            raise ValueError("Finite response-law evaluation operands change the complete assigned census or endpoint masks")
        for name in (
            "y",
            "observed",
            "response_valid",
            "use_valid",
            "prefix",
            "handoff",
            "parent_work",
            "parent_indices",
        ):
            value = getattr(self, name)
            object.__setattr__(
                self, name, np.frombuffer(value.tobytes(), dtype=value.dtype).reshape(value.shape)
            )


def evaluation_panel(evaluation: FiniteResponseLawEvaluationNativeCompletion) -> EvaluationPanel:
    """Keep loss availability independent of HOLD-dependent preservation.

    Signed endpoint values are retained even when their preservation/HOLD
    observations are unavailable. Actual signed delivery and the two paired
    source identities are still required; a shadow with failed delivery never
    becomes valid response evidence.
    """
    if type(evaluation) not in (FiniteResponseLawEvaluationNativeCompletion, FiniteResponseLawAssignedEvaluationNativeCompletion):
        raise ValueError("Finite response-law evaluation reduction requires its separate prospective completion record")
    source = evaluation.config.projection.native_spec
    roots = source.roots
    y = np.full((64, 4, 8, 2, 2), np.nan)
    response_valid = np.zeros((64, 4, 2, 2, 2), dtype=bool)
    use_valid = np.zeros((64, 4, 2, 2), dtype=bool)
    prefix, handoff = (np.full((64, 24, 2), np.nan) for _ in range(2))
    work = np.full((64, 2), np.nan)
    for r, root in enumerate(roots):
        views = evaluation.views[2 * r:2 * r + 2]
        if tuple((v.root, v.refinement) for v in views) != ((root, 1), (root, 2)):
            raise ValueError("Finite response-law evaluation reduction loses one of the two coupled numerical views")
        for v, view in enumerate(views):
            if view.prefix_interface is not None:
                prefix[r, :, v] = view.prefix_interface.values
            if view.handoff_interface is not None:
                handoff[r, :, v] = view.handoff_interface.values
            if view.parent_absolute_density_work is not None:
                work[r, v] = float(view.parent_absolute_density_work)
        for k, _, readout, valid_delivery in positive_pair_readouts(views, parent=root.assigned_parent):
            f, v = int(readout.purpose[-1]) - 1, readout.refinement - 1
            use_valid[r, k, f, v] = readout.source_valid
            for j, value in enumerate(readout.values):
                if value is not None:
                    y[r, k, j, f, v] = float(value)
                    if j < 2:
                        response_valid[r, k, j, f, v] = valid_delivery
    return EvaluationPanel(
        y,
        np.isfinite(y),
        response_valid,
        use_valid,
        prefix,
        handoff,
        work,
        np.asarray([PARENTS.index(root.assigned_parent) for root in roots], dtype=np.int64),
        tuple(root.stage_unit for root in roots),
        assigned_source=source if type(source) is FiniteResponseLawAssignedEvaluationConfig else None,
    )
