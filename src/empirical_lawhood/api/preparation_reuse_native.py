# SPDX-License-Identifier: MPL-2.0
"""Select only published, completed native assignments for an exposed numerical replication."""

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from os import sched_getaffinity

from threadpoolctl import threadpool_limits

from .preparation_reuse_operands import open_released_operands


def _reacquire(task):
    study, operands = task
    with threadpool_limits(limits=1):
        if study == "r23":
            from empirical_lawhood.adapters.simulators.constructed_preparation_applicability.replay import (
                verify_measured_native_panel,
            )

            return verify_measured_native_panel(*operands)
        from empirical_lawhood.adapters.simulators.finite_response_law.replay import verify_native_root

        return verify_native_root(*operands)


def reproduce_native_roots(*, study, cohort, directory, root_index=None, workers=1):
    """Re-run each selected physical root from its committed seeds and original causal selections."""
    counts = {"r23": {"Q": 8, "E": 32}, "r24": {"calibration": 32, "retained": 64, "disjoint": 64}}
    count = counts.get(study, {}).get(cohort)
    if count is None or workers < 1 or (root_index is not None and root_index not in range(count)):
        raise ValueError("Select a published R23 Q/E or R24 calibration/retained/disjoint root census")
    indices = range(count) if root_index is None else (root_index,)
    if min(len(indices), workers) > len(sched_getaffinity(0)):
        raise ValueError("Native replication requires one available CPU per active worker")
    with open_released_operands(directory, study) as data:
        if study == "r23":
            from empirical_lawhood.domains.matrix.constructed_preparation_applicability.config import (
                ConstructedPreparationStage,
            )
            from empirical_lawhood.domains.matrix.constructed_preparation_applicability.records import (
                ConstructedPreparationLowerSeal,
                ConstructedPreparationMeasuredRoot,
                ConstructedPreparationSelection,
            )

            stage = data.record(cohort + "/stage", ConstructedPreparationStage)
            if (
                len(stage.root_ids) != count
                or stage.source.object_fingerprint != data.members[cohort + "/source"]["sha256"]
            ):
                raise ValueError("Native replication changes the original source or roster")
            data.raw(cohort + "/source")
            tasks = []
            for i in indices:
                prefix = f"{cohort}/{i:03d}/"
                tasks.append(
                    (
                        study,
                        (
                            stage.allocation.roots[i],
                            stage.source.object_fingerprint,
                            data.record(prefix + "selection", ConstructedPreparationSelection),
                            data.record(prefix + "seal", ConstructedPreparationLowerSeal),
                            data.record(prefix + "measurement", ConstructedPreparationMeasuredRoot),
                        ),
                    )
                )
        else:
            from empirical_lawhood.domains.matrix.finite_response_law.assigned_native_records import (
                FiniteResponseLawAssignedCalibrationNativeEvaluation,
                FiniteResponseLawAssignedEvaluationNativeCompletion,
            )

            kind = (
                FiniteResponseLawAssignedCalibrationNativeEvaluation
                if cohort == "calibration"
                else FiniteResponseLawAssignedEvaluationNativeCompletion
            )
            completion = data.record(cohort + "/native", kind)
            config = completion.config.projection.native_spec
            if len(config.roots) != count:
                raise ValueError("Native completion has a different assigned cohort")
            views = {(v.root, v.refinement): v for v in completion.views}
            tasks = [
                (study, (config, config.roots[i], tuple(views[config.roots[i], v] for v in (1, 2))))
                for i in indices
            ]
    if workers == 1 or len(tasks) == 1:
        results = list(map(_reacquire, tasks))
    else:
        with ProcessPoolExecutor(
            max_workers=min(workers, len(tasks)), mp_context=get_context("spawn")
        ) as pool:
            results = list(pool.map(_reacquire, tasks, chunksize=1))
    return {
        "study": study,
        "cohort": cohort,
        "scope": "EXPOSED_NATIVE_REPRODUCTION",
        "new_qualification": False,
        "new_native_acquisitions": len(results),
        "assigned_cohort_size": count,
        "roots": results,
    }
