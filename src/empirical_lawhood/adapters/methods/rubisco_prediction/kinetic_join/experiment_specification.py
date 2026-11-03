# SPDX-License-Identifier: MPL-2.0
"""Editable gas action and exact source selections for conditional W1 science."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.simulators.rubisco_assay.records import AssayQuery
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_nonempty, validate_stable_id,
)
from empirical_lawhood.planning.campaigns import CampaignSpec

from ..kinetic_supply import JointKineticSupply, KineticSupplyContext, KineticTargetComparison
from .disclosed_examples import DisclosedAssumption


PROTOCOL_ID = "rubisco.kinetic-join.exposed"
SOURCE_QUERY_ID = "source.rubisco-kinetic-experiment.query"
QUESTION = "Assess complete supplied joint kinetics and both conditional reference bounds at the selected gas action."


@dataclass(frozen=True, slots=True)
class RubiscoKineticExperimentSpecification(CanonicalRecord):
    """A proposed action is editable; its original supplied evidence is fixed.

    Supported members remain nested conditional scenarios. This specification
    creates no biological population, calibrated predictor or challenge warrant.
    """

    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-kinetic-experiment/specification"
    specification_id: str
    question: str
    campaign: ObjectIdentity
    material: ObjectIdentity
    supply: ObjectIdentity
    source_query: ObjectIdentity
    comparison: ObjectIdentity
    context: KineticSupplyContext
    expected_member_ids: tuple[str, ...]
    query: AssayQuery
    numerical_relative_tolerance: Decimal = Decimal("1e-10")
    evidence_scope: str = "EXPOSED_CONFORMANCE"
    independent_biological_units: int = 0
    biological_predictive_calibration: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        validate_nonempty(self.question, field_name="question")
        if self.question != QUESTION:
            raise ValueError("kinetic experiment changes its conditional question")
        for identity, record_type in ((self.campaign, CampaignSpec), (self.material, DisclosedAssumption),
                (self.supply, JointKineticSupply), (self.source_query, AssayQuery),
                (self.comparison, KineticTargetComparison)):
            if (type(identity) is not ObjectIdentity or identity.object_schema != record_type.SCHEMA
                    or identity.object_version != record_type.VERSION):
                raise ValueError("kinetic experiment substitutes an exact source type/revision")
            identity.__post_init__()
        if self.source_query.object_id != SOURCE_QUERY_ID:
            raise ValueError("kinetic experiment changes its original query source alias")
        if type(self.context) is not KineticSupplyContext or type(self.query) is not AssayQuery:
            raise TypeError("kinetic experiment requires its exact context and selected gas action")
        self.context.__post_init__()
        self.query.__post_init__()
        if (self.context.temperature_k != Decimal("298.15")
                or self.context.material != self.material or self.context.assay_conditions != self.material):
            raise ValueError("kinetic experiment changes its disclosed matched 298.15 K material/assay context")
        require_sorted_unique_strings(self.expected_member_ids, field_name="expected_member_ids", allow_empty=False)
        validate_decimal(self.numerical_relative_tolerance, field_name="numerical_relative_tolerance",
            minimum=Decimal(0))
        if (self.numerical_relative_tolerance == 0
                or self.evidence_scope not in ("EXPOSED_CONFORMANCE", "PROSPECTIVE_REQUIRED")
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0
                or self.biological_predictive_calibration != "NOT_ESTABLISHED"):
            raise ValueError("kinetic experiment changes numerical protocol or biological evidence meaning")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def kinetic_experiment_specification(*, specification_id, campaign, material, supply,
        source_query, comparison, query=None, relative_tolerance=Decimal("1e-10")):
    """Select existing immutable records; editing ``query`` selects a new action."""
    return RubiscoKineticExperimentSpecification(specification_id, QUESTION,
        ObjectIdentity.from_record(campaign.campaign_id, campaign),
        ObjectIdentity.from_record(material.assumption_id, material),
        ObjectIdentity.from_record(supply.supply_id, supply),
        ObjectIdentity.from_record(SOURCE_QUERY_ID, source_query),
        ObjectIdentity.from_record(comparison.comparison_id, comparison), supply.context,
        supply.expected_member_ids, source_query if query is None else query, relative_tolerance)
