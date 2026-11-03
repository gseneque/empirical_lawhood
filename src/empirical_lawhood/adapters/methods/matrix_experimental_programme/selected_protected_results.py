# SPDX-License-Identifier: MPL-2.0
"""Complete selected protected reductions using original endpoint arithmetic."""

from collections.abc import Mapping
from .preparation_records import is_baseline_recipe

from dataclasses import dataclass
from types import SimpleNamespace
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .functional_case_reduction import _prepared_endpoint
from .functional_outcome_reduction import _confirmation_comparisons, _transfer_comparisons
from .prepared_forecast import MatrixPreparedMechanicalForecast
from .prepared_prefix import identity
from .prepared_response_science import MatrixPreparedResponseReadout
from .science import MatrixFunctionalAssessment, MatrixFunctionalCaseResult
from .selected_point import MatrixSelectedPointForecast, forecast_selected_point
from .selected_public import package_identity
from .selected_protected_programme import MatrixSelectedProtectedProgramme, MatrixSelectedPublicProgramme


@dataclass(frozen=True, slots=True)
class MatrixSelectedProtectedEntrySeal(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-protected-entry-seal"
    record_id: str
    programme: ObjectIdentity
    source_closure: ObjectIdentity
    point_design: ObjectIdentity
    package: ObjectIdentity
    source_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixSelectedPublicProgramme.SCHEMA
                or not self.source_ids or self.source_ids != tuple(sorted(set(self.source_ids)))):
            raise ValueError("selected entry seal changes its complete original protected source census")


def entry_seal(programme):
    if type(programme) is MatrixSelectedProtectedProgramme:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    programme.__post_init__()
    return MatrixSelectedProtectedEntrySeal("entry." + programme.fingerprint(), programme.identity,
        programme.sources.closure.identity, programme.point_design.identity, package_identity(programme.point_design.package),
        tuple(sorted(source.source_id for _, source in programme.sources.source_arms())))


@dataclass(frozen=True, slots=True)
class MatrixSelectedProtectedManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/selected-protected-manifest"
    record_id: str
    programme: ObjectIdentity
    rows: tuple[tuple[str, ObjectIdentity | None, ObjectIdentity | None, ObjectIdentity | None], ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if (self.programme.object_schema != MatrixSelectedPublicProgramme.SCHEMA or not self.rows
                or tuple(row[0] for row in self.rows) != tuple(sorted({row[0] for row in self.rows}))):
            raise ValueError("selected protected manifest omits complete sorted assigned cases")
        for _, point, mechanical, readout in self.rows:
            if point is None:
                if (mechanical, readout) != (None, None):
                    raise ValueError("selected protected manifest invents a partial observation")
            elif (point.object_schema != MatrixSelectedPointForecast.SCHEMA or mechanical is None or readout is None
                    or mechanical.object_schema != MatrixPreparedMechanicalForecast.SCHEMA
                    or readout.object_schema != MatrixPreparedResponseReadout.SCHEMA):
                raise ValueError("selected protected manifest substitutes actual numerical product types")

    @property
    def identity(self):
        return identity(self)


def assess_selected_programme(programme, observations, *, result_id):
    """Guard actual selected products, then reuse original private arithmetic.

    The small namespace projections below are numerical operands only. They are
    never canonical records, publication subjects, source declarations or access
    contexts. Original selected identities are retained in the manifest.
    """
    if type(programme) is MatrixSelectedProtectedProgramme:
        programme = MatrixSelectedPublicProgramme.from_programme(programme)
    if type(programme) is not MatrixSelectedPublicProgramme or not isinstance(observations, Mapping):
        raise TypeError("selected assessment requires its exact complete programme and received products")
    programme.__post_init__()
    roster = programme.roster
    if set(observations) - {case.case_id for case in roster.cases}:
        raise ValueError("selected assessment receives an unassigned scientific case")
    sources = {"case." + source.source_id: source for _, source in programme.sources.source_arms()}
    cases, manifest_rows = [], []
    model = identity(programme.point_design.package.models)
    package_values = SimpleNamespace(identity=package_identity(programme.point_design.package), component=lambda role: model)
    for case in roster.cases:
        observation = observations.get(case.case_id)
        if observation is None:
            cases.append(MatrixFunctionalCaseResult(case.case_id, case.unit_id, case.arm_id, "MISSING", None, None, None,
                False, False, None, False, case.preparation_effort, ("MISSING_ORIGINAL_FORECAST_OR_SCORE",)))
            manifest_rows.append((case.case_id, None, None, None))
            continue
        point, mechanical, readout = observation
        source = sources[case.case_id]
        protocol = programme.protocol(source)
        if (type(point) is not MatrixSelectedPointForecast or type(mechanical) is not MatrixPreparedMechanicalForecast
                or type(readout) is not MatrixPreparedResponseReadout
                or point != forecast_selected_point(programme.point_design, point.feature, record_id=point.record_id)
                or point.feature.public_source.source != source.identity or mechanical.source != source.identity or readout.source != source.identity
                or mechanical.causal != point.feature.prefix or mechanical.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
                or readout.original_protocol != mechanical.original_protocol or readout.preparation != mechanical.arrays.preparation
                or readout.panels != tuple(row.identity for row in dict(programme.panels)[case.unit_id])):
            raise ValueError("selected assessment substitutes actual pre-future selected forecasts or independent readout")
        if readout.forecast is not None and readout.forecast != mechanical.arrays.identity:
            raise ValueError("selected assessment changes the actual independently checked physical prediction")
        f = point.feature
        feature_values = SimpleNamespace(source=f.public_source.source, prefix=f.prefix, values=f.values,
            cutoff=source.coordinate.physical_time(source.total_ticks), family_id=programme.point_design.family(f.public_source),
            frame_sha256=f.frame_sha256, disposition=f.disposition)
        point_values = dict(point.log_points)
        common = {"package": point.package, "criterion": protocol.criterion, "feature": feature_values,
            "log_error_uppers": (None,) * 15}
        main = SimpleNamespace(**common, log_error_points=point_values["SPECTRAL_RIDGE"])
        comparator = SimpleNamespace(**common, model=model, log_error_points=point_values["ALL_ORIGIN_RIDGE"])
        numeric = SimpleNamespace(point=main, mechanical=mechanical, readout=readout, comparator=comparator)
        cases.append(_prepared_endpoint(programme.criterion, package_values, case, source, numeric, protocol=protocol,
            panels=dict(programme.panels)[case.unit_id]))
        manifest_rows.append((case.case_id, identity(point), identity(mechanical), identity(readout)))
    cases = tuple(cases)
    manifest = MatrixSelectedProtectedManifest(result_id + ".received", programme.identity, tuple(manifest_rows))
    hold = programme.sources.hold_arm_id
    if programme.phase == "E5_CONFIRMATION":
        groups = tuple(sorted({case.unit_id for case in roster.cases}))
        selected = next(arm for arm, recipe in programme.point_design.arms if not is_baseline_recipe(recipe))
        comparisons = _confirmation_comparisons(programme.criterion, groups, selected, hold, cases)
    else:
        regimes = []
        for role in ("transfer_nearby", "transfer_shifted"):
            groups = programme.point_design.package.allocation.unit_ids(role)
            matching = tuple(case for case in roster.cases if case.unit_id in groups)
            names = {case.public_source.root.regime_id for case in matching}
            if len(names) != 1 or tuple(sorted(case.unit_id for case in matching)) != groups:
                raise ValueError("selected transfer substitutes its original separate nearby/shifted reserve census")
            regimes.append((next(iter(names)), groups))
        regimes = tuple(regimes)
        comparisons = _transfer_comparisons(programme.criterion, regimes, programme.transfer_domain_claims, hold, cases)
    used = {row.comparison_id for row in comparisons}
    result = MatrixFunctionalAssessment(result_id, programme.identity, package_identity(programme.point_design.package), roster.identity, manifest.identity,
        None if programme.nomination is None else programme.nomination.original_nomination, comparisons, cases,
        tuple(slot for slot in programme.criterion.family_slots if slot not in used))
    return manifest, result
