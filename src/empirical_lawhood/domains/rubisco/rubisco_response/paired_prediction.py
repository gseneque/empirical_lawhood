# SPDX-License-Identifier: MPL-2.0
"""Conditional kinetic production from a finite joint parameter support."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import FourStateResult
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import EndpointValues, JointEndpointRegion, PairedJointValue, PairedKineticSupport, PairedScenarioSupport, anchor_joint_value
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.rate_contracts import PairedRateSupply


def source_union(*groups):
    """Merge identical ancestors and refuse an identifier with different bytes."""
    sources = {}
    for group in groups:
        for record in group:
            exact(record, ObjectIdentity)
            if sources.setdefault(record.object_id, record) != record:
                raise ValueError("source identifier aliases different exact records")
    return tuple(sources[key] for key in sorted(sources))


@dataclass(frozen=True, slots=True)
class PairedPointPrediction(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-point-prediction"
    scenario_id: str
    point_id: str
    wild_type: FourStateResult
    mutant: FourStateResult

    def __post_init__(self):
        for value in (self.scenario_id, self.point_id):
            validate_stable_id(value)
        for result in (self.wild_type, self.mutant):
            exact(result, FourStateResult)


@dataclass(frozen=True, slots=True)
class PairedPrediction(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/paired-prediction"
    prediction_id: str
    supply: ObjectIdentity
    points: tuple[PairedPointPrediction, ...]
    support: PairedKineticSupport

    def __post_init__(self):
        validate_stable_id(self.prediction_id)
        exact(self.supply, ObjectIdentity)
        if self.supply.object_schema != PairedRateSupply.SCHEMA or self.supply.object_version != PairedRateSupply.VERSION:
            raise ValueError("paired prediction changes its exact rate-supply revision")
        if type(self.points) is not tuple:
            raise TypeError("paired prediction requires an immutable point census")
        for point in self.points:
            exact(point, PairedPointPrediction)
        keys = tuple((point.scenario_id, point.point_id) for point in self.points)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("paired prediction drops its unique ordered point correspondence")
        exact(self.support, PairedKineticSupport)


def predict_paired_rates(supply, *, prediction_id):
    """No new physical inputs, rate identification, interpolation or acquisition."""
    from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import solve_four_state

    exact(supply, PairedRateSupply)
    records, scenarios = [], []
    for scenario in supply.scenarios:
        values = []
        for point in scenario.points:
            results = tuple(solve_four_state(getattr(point, arm), supply.query,
                result_id=f"{prediction_id}.{scenario.scenario_id}.{point.point_id}.{arm}")
                for arm in ("wild_type", "mutant"))
            records.append(PairedPointPrediction(scenario.scenario_id, point.point_id, *results))
            value = PairedJointValue(point.point_id,
                *(EndpointValues(result.intrinsic.kcat_c, result.intrinsic.specificity) for result in results))
            if point.anchor_wild_type is not None:
                value = anchor_joint_value(value, point.anchor_wild_type)
            values.append(value)
        sources = source_union(scenario.sources, (scenario.ledger.identity,),
                               *(point.sources for point in scenario.points))
        region = None
        if scenario.original_state == "AVAILABLE":
            region = JointEndpointRegion(f"{prediction_id}.{scenario.scenario_id}.region",
                tuple(values), "FINITE_POINTS", "FINITE_JOINT_SUPPORT", sources,
                anchor_source=None if not scenario.points else scenario.points[0].anchor_source)
        pending = tuple(sorted(set(scenario.unresolved_requirement_ids) | set(scenario.ledger.unresolved_requirement_ids)))
        scenarios.append(PairedScenarioSupport(scenario.scenario_id, scenario.original_state,
                                               region, sources, pending))
    pending = tuple(sorted(set(supply.prerequisite_requirement_ids)
                           | set(supply.context.chemistry.unresolved_requirement_ids)))
    support = PairedKineticSupport(prediction_id + ".support", supply.case.identity, supply.context.identity,
        supply.expected_scenario_ids, tuple(scenarios), source_union(supply.shared_sources, (supply.identity,)), pending)
    return PairedPrediction(prediction_id, supply.identity, tuple(records), support)
