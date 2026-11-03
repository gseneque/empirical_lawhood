# SPDX-License-Identifier: MPL-2.0
"""Public prospective programme input compilation, without acquisition.

The copied request selects mathematics, exclusions, stream materials and finite
resources. C is a later produced publication, never an issue or freshness act.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs,
)
from .allocation_request import MatrixProgrammeAllocationRequest
from .known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from .scientific_design import MatrixProgrammeScientificDesign

PROTOCOL_ID = "matrix.programme.input-assembly"


def required_support_files(design):
    """Scientific input identities; no path discovery or publication lookup."""
    return frozenset((design.training_assay.array_artifact, design.e2.assay.array_artifact,
        design.training_protocol.full_factor_rule.scalar_closure.normalization_owner))


@dataclass(frozen=True, slots=True)
class MatrixProgrammeInputAssemblySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-programme/input-assembly-specification"
    specification_id: str
    request: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (type(self.request) is not ObjectIdentity or (self.request.object_schema, self.request.object_version)
                != (MatrixProgrammeAllocationRequest.SCHEMA, MatrixProgrammeAllocationRequest.VERSION)):
            raise TypeError("programme input compilation requires its exact current allocation request")
        self.request.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeInputAssemblyInputs:
    request: MatrixProgrammeAllocationRequest | None
    design: MatrixProgrammeScientificDesign | None
    census: MatrixFactorExposureCensus | None
    input_commitments: MatrixProgrammePublishedInput | None
    record_paths: tuple
    files: tuple


def bind_inputs(specification, records, *, record_paths=None, files=None):
    if type(specification) is not MatrixProgrammeInputAssemblySpecification:
        raise TypeError("programme input compilation requires its exact current specification")
    specification.__post_init__()
    if set(records) - {"request", "scientific-design", "exposure-census", "input-commitments"}:
        raise ValueError("programme input compilation refuses undeclared record operands")
    kinds = {"request": MatrixProgrammeAllocationRequest, "scientific-design": MatrixProgrammeScientificDesign,
        "exposure-census": MatrixFactorExposureCensus, "input-commitments": MatrixProgrammePublishedInput}
    for key, value in records.items():
        if type(value) is not kinds[key]:
            raise TypeError("programme input compilation changes its exact " + key)
        value.__post_init__()
    request, design, census = (records.get(key) for key in ("request", "scientific-design", "exposure-census"))
    commitment = records.get("input-commitments")
    if commitment is not None:
        commitment.require_kind(MatrixProgrammeInputCommitments)
    if request is not None:
        if request.identity != specification.request:
            raise ValueError("programme input compilation substitutes its selected request")
        if design is not None and design.identity != request.scientific_design:
            raise ValueError("programme input compilation substitutes its exact scientific design D")
        if census is not None and census.identity != request.exposure_census:
            raise ValueError("programme input compilation substitutes its selected exposure census")
        if design is not None and {row.identity for row in request.files} != required_support_files(design):
            raise ValueError("programme input compilation requires exactly its template arrays and normalization FILE")
        if files and (set(files) != {row.key for row in request.files}
                or any(files[row.key].identity != row.identity or files[row.key].record_version != row.record_version
                    or files[row.key].maximum_bytes != row.maximum_bytes for row in request.files)):
            raise ValueError("programme input compilation changes its exact copied support FILE selection")
    elif files:
        raise ValueError("programme input compilation FILE operands require their explicit request")
    return PreparedExperimentInputs({}, MatrixProgrammeInputAssemblyInputs(request, design, census, commitment,
        tuple(sorted((record_paths or {}).items())), tuple(sorted((files or {}).items()))))


def prepare(specification, *, execution, method_inputs=None, **_kwargs):
    specification.__post_init__()
    dependencies = []
    bound = method_inputs
    if bound is not None and type(bound) is not MatrixProgrammeInputAssemblyInputs:
        raise TypeError("programme input compilation requires exact bound current inputs")
    for field, kind in (("workers", DependencyKind.ENVIRONMENT), ("environment_id", DependencyKind.ENVIRONMENT),
            ("source_snapshot", DependencyKind.ENVIRONMENT), ("output_root", DependencyKind.STORAGE)):
        if getattr(execution, field) is None:
            dependencies.append(ExperimentDependency("programme-inputs.execution." + field.replace("_", "-"),
                kind, "Select explicit " + field + "."))
    if bound is not None and bound.input_commitments is not None:
        dependencies.append(ExperimentDependency("programme-inputs.use-commitment", DependencyKind.EXTERNAL_INPUT,
            "Use the published C through the current programme workflow; it grants no source, issue or execution authority."))
    else:
        for key, field in (("request", "request"), ("scientific-design", "design"), ("exposure-census", "census")):
            if bound is None or getattr(bound, field) is None:
                dependencies.append(ExperimentDependency("programme-inputs." + key, DependencyKind.EXTERNAL_INPUT,
                    "Supply the exact current " + key + ".", key))
        if bound is not None and bound.request is not None:
            actual = dict(bound.files)
            for binding in bound.request.files:
                if binding.key not in actual:
                    dependencies.append(ExperimentDependency("programme-inputs.file." + binding.key,
                        DependencyKind.EXTERNAL_INPUT, "Supply the exact selected support FILE.", binding.key))
            dependencies.append(ExperimentDependency("programme-inputs.derive", DependencyKind.EXTERNAL_INPUT,
                "Use experiment-derive-inputs to publish the complete prospective C before dependent observations."))
    return ExperimentPreparation(specification.identity, ExperimentCensus((), (), (), (), 0),
        tuple(sorted(dependencies, key=lambda value: value.code)), execution=execution,
        specification_record=specification)
