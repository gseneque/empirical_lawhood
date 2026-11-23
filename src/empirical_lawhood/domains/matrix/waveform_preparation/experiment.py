# SPDX-License-Identifier: MPL-2.0
"""Freeze and verify the original F, independent population and development parent."""

from empirical_lawhood.domains.matrix.finite_response_law.authoring.exposure import (
    native_seed_collisions,
)
from empirical_lawhood.domains.matrix.finite_response_law.authoring.rerun_input import (
    FiniteResponseLawCurrentExposure,
)
from empirical_lawhood.domains.matrix.finite_response_law.original_f import (
    OriginalFiniteResponseLaw,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_evaluation import (
    WaveformCohort,
    statistics,
)
from empirical_lawhood.execution.experiment_preparation import (
    DependencyKind,
    ExperimentCensus,
    ExperimentDependency,
    ExperimentPreparation,
    PreparedExperimentInputs,
)
from empirical_lawhood.science.experiments.experimental_design import (
    IndependentUnit,
    UnitAllocation,
    UnitRoleAssignment,
)
from . import design
from .records import NAMESPACE, WaveformSpecification


def allocation(spec):
    return UnitAllocation(
        "allocation." + spec.specification_id,
        (spec.identity,),
        tuple(
            IndependentUnit(
                u,
                spec.specification_id,
                "family.waveform-preparation",
                ("view.primary", "view.refined"),
                False,
            )
            for u in spec.unit_ids
        ),
        tuple(UnitRoleAssignment(u, spec.role) for u in spec.unit_ids),
    )


def population_seeds(draws):
    seeds = [
        f"seed.pcg64.{s.seed:032x}"
        for draw in draws
        for s in draw.allocation.scientific_seeds
    ]
    seeds.extend(
        "seed.pcg64." + s[:32] for draw in draws for s in draw.nominal_seed_digests
    )
    if len(set(seeds)) != len(seeds):
        raise ValueError(
            "Independent waveform purposes collide within the assigned cohort"
        )
    return tuple(sorted(seeds))


def bind_inputs(specification, records, *, files=None):
    spec = specification
    if type(spec) is not WaveformSpecification or files:
        raise ValueError(
            "Waveform population requires its own complete scientific definition"
        )
    kinds = {
        "exposure": FiniteResponseLawCurrentExposure,
        "lower": OriginalFiniteResponseLaw,
    }
    if spec.development is not None:
        kinds["development"] = WaveformCohort
    if any(
        name not in kinds
        or type(r) is not kinds[name]
        or r.identity != getattr(spec, name)
        for name, r in records.items()
    ):
        raise ValueError(
            "Waveform study substituted a scientific input or its identity"
        )
    draws = [spec.draw(i) for i in range(spec.count)]
    seeds = population_seeds(draws)
    if "exposure" in records:
        census = records["exposure"]
        if set(spec.unit_ids) & set(census.excluded_unit_ids) or native_seed_collisions(
            seeds, census.excluded_seed_ids
        ):
            raise ValueError("Waveform draws overlap known earlier exposure")
    if "development" in records:
        parent = records["development"]
        if (
            parent.role != "development"
            or parent.disposition != "ENTER_CONFIRMATION"
            or parent.fitted is None
            or statistics(parent.rows, parent.bootstrap_seed)["disposition"]
            != "ENTER_CONFIRMATION"
            or parent.master_seed == spec.master_seed
            or parent.rows[0].primary.lower_sha256 != spec.lower.object_fingerprint
            or native_seed_collisions(
                seeds, population_seeds([r.draw for r in parent.rows])
            )
        ):
            raise ValueError(
                "A distinct, complete and passing waveform screen is required before confirmation"
            )
    return PreparedExperimentInputs({"allocation": allocation(spec)}, records)


def prepare(
    specification,
    *,
    scientific_inputs,
    execution,
    method_inputs=None,
    protocol_bytes=None,
):
    records = method_inputs or {}
    bound = bind_inputs(specification, records)
    if scientific_inputs != bound.scientific_inputs or protocol_bytes is not None:
        raise ValueError(
            "Waveform study substituted its assigned allocation or protocol"
        )
    dependencies = [
        ExperimentDependency(
            NAMESPACE + ".input." + key,
            DependencyKind.EXTERNAL_INPUT,
            "Select the original " + key + " for this population.",
            key,
        )
        for key in ("exposure", "lower", "development")
        if getattr(specification, key) is not None and key not in records
    ]
    dependencies.extend(
        ExperimentDependency(
            NAMESPACE + ".execution." + k,
            DependencyKind.ENVIRONMENT,
            "Select explicit " + k + ".",
        )
        for k in ("environment_id", "source_snapshot", "output_root", "workers")
        if getattr(execution, k) is None
    )
    if (
        execution.source_snapshot is not None
        and execution.source_snapshot.object_fingerprint
        != specification.source_snapshot_sha256
    ):
        raise ValueError(
            "Waveform scientific definition and selected producing checkout differ"
        )
    count = specification.count
    draft, inputs = (None, ()) if dependencies else design.lower(specification, records)
    return ExperimentPreparation(
        specification.identity,
        ExperimentCensus(
            (("independent-waveforms", count),),
            (("independent-waveforms", 0 if dependencies else count),),
            (("operations", 6 * count + 1),),
            (
                ("canonical-products", 6 * count + 1),
                ("native-array-containers", 3 * count),
            ),
            0,
        ),
        tuple(sorted(dependencies, key=lambda d: d.code)),
        allocation=None if dependencies else allocation(specification),
        draft=draft,
        input_records=inputs,
        execution=execution,
        specification_record=specification,
        design_records=tuple(
            sorted((r.identity.object_id, r) for r in records.values())
        ),
    )


def validate_instance(*, specification, allocation, draft, source_records):
    by_schema = {
        OriginalFiniteResponseLaw.SCHEMA: "lower",
        FiniteResponseLawCurrentExposure.SCHEMA: "exposure",
        WaveformCohort.SCHEMA: "development",
    }
    records = {by_schema[r.SCHEMA]: r for _, r in source_records}
    expected = {"lower", "exposure"} | (
        {"development"} if specification.development else set()
    )
    if len(records) != len(source_records) or set(records) != expected:
        raise ValueError("Waveform instance omitted original inputs")
    bound = bind_inputs(specification, records)
    if (
        allocation != bound.scientific_inputs["allocation"]
        or draft != design.lower(specification, records)[0]
    ):
        raise ValueError(
            "Waveform instance changed its population or causal dependencies"
        )
