# SPDX-License-Identifier: MPL-2.0
"""Truth-disclosed short-sequence controls, with zero biological observations."""

from dataclasses import dataclass
from decimal import Decimal as D
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_prediction.kinetic_model import PARAMETER_ORDER, DissolvedGasQuery, FourStateRates
from empirical_lawhood.domains.rubisco.rubisco_prediction.paired_supply import PairedDecisionRegion
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.domains.rubisco.rubisco_response.contexts import ActiveSiteSelection, ChemicalProtocol, RubiscoAssayContext
from empirical_lawhood.domains.rubisco.rubisco_response.materials import homogeneous_material, paired_case
from empirical_lawhood.domains.rubisco.rubisco_response.rate_contracts import TRANSITIONS, PairedRatePoint, PairedRateScenario, PairedRateSupply, ParameterEvidenceLedger, RateEvidenceBinding


@dataclass(frozen=True, slots=True)
class DisclosedResponseAssumption(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/disclosed-assumption"
    assumption_id: str = "source.rubisco-response.disclosed"
    meaning: str = "EXPOSED_SHORT_SEQUENCE_ARITHMETIC_CONTROL_NOT_A_REAL_ENZYME"
    independent_biological_units: int = 0

    def __post_init__(self):
        if (self.assumption_id != "source.rubisco-response.disclosed"
                or self.meaning != "EXPOSED_SHORT_SEQUENCE_ARITHMETIC_CONTROL_NOT_A_REAL_ENZYME"
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("disclosed arithmetic input cannot become biological evidence")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assumption_id, self)


def disclosed_supply(*, case_role="CANDIDATE", scenario_states=("AVAILABLE",)):
    """Produce declared operands only; native prerequisites are never probed."""
    source = DisclosedResponseAssumption().identity
    parent = homogeneous_material(material_id="material.disclosed.wt", organism="Disclosed short sequence",
        processing_view="complete", lsu="MAK", ssu="MIL", sources=(source,))
    child = parent if case_role == "NO_CHANGE" else homogeneous_material(
        material_id="material.disclosed.mutant", organism=parent.organism,
        processing_view="complete", lsu="MAK", ssu="MML", sources=(source,))
    case = paired_case(case_id="case.disclosed." + case_role.lower(), parent=parent, mutant=child,
        case_role=case_role, exposure_group="exposure.disclosed", sources=(source,))
    sites = tuple(ActiveSiteSelection(f"site.{i:02}", f"lsu.{i:02}", 3, True, True,
        "RUBP", source, source, source) for i in range(1, 9))
    chemistry = ChemicalProtocol("chemistry.disclosed", sites, "EXCHANGEABLE", source, (source,), ())
    context = RubiscoAssayContext("context.disclosed.298p15", D("298.15"), (D(8), D(8)),
        "Fixed disclosed pH assumption, without a chemical admission", chemistry,
        "Initial product-free event flux in the mathematical control", (source,), "NEW_SELECTION")
    wt = FourStateRates(*(D(n) for n in (2, 1, 3, 1, 1, 1, 4, 2)))
    mutant = wt if case_role == "NO_CHANGE" else FourStateRates(*(D(n) for n in (4, 1, 3, 1, 1, 1, 4, 2)))
    rows = tuple(RateEvidenceBinding(parameter, TRANSITIONS[parameter],
        "uM^-1 s^-1" if parameter in {"c", "o"} else "s^-1", "IMPOSED_ASSUMPTION", "DISCLOSED_CONTROL",
        (getattr(wt, parameter),) * 2, (getattr(mutant, parameter),) * 2,
        "PAIRED_JOINT" if parameter == "a" else "IMPOSED_INVARIANT", "dependence.disclosed.joint",
        ("Not a biological rate estimate",), (source,), (), (), D("0.01")) for parameter in PARAMETER_ORDER)
    ledger = ParameterEvidenceLedger("ledger.disclosed", case.identity, context.identity, rows)
    point = PairedRatePoint("point.disclosed", wt, mutant, (source,))
    scenarios = tuple(PairedRateScenario(f"scenario.{i:02}", state, ledger,
        (point,) if state == "AVAILABLE" else (), "Selected four-state closure", (source,),
        () if state == "AVAILABLE" else (f"requirement.scenario.{i:02}",))
        for i, state in enumerate(scenario_states, 1))
    return PairedRateSupply("supply.disclosed." + case_role.lower(), case, context, DissolvedGasQuery(D(10), D(20)),
        tuple(row.scenario_id for row in scenarios), scenarios, (source,), ())


def disclosed_decision(supply):
    return PairedDecisionRegion("decision.disclosed." + supply.case.case_role.lower(),
        supply.case.identity, supply.context.identity, D(1), D(1), None, None, "RAW",
        "Select a further disclosed software control only", (DisclosedResponseAssumption().identity,),
        strict_turnover_increase=True)


@dataclass(frozen=True, slots=True)
class DisclosedMethodSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/disclosed-method-selection"
    method_id: str
    method: str

    def __post_init__(self):
        if (self.method not in {"EXACT_FOUR_STATE_REFERENCE", "CONVENTIONAL_SCALAR_REFERENCE"}
                or self.method_id != "method.disclosed." + self.method.lower()):
            raise ValueError("disclosed method selection changes its stated comparison")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.method_id, self)


def disclosed_study():
    from empirical_lawhood.domains.rubisco.rubisco_response.acceptance import NominatedPrediction, ResponseAcceptance
    from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet
    from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy, exposed_source_allocation

    source = DisclosedResponseAssumption().identity
    supplies = tuple(sorted((disclosed_supply(), disclosed_supply(case_role="NO_CHANGE")),
                            key=lambda row: row.case.case_id))
    cases = RubiscoCaseSet("selection.disclosed.response", tuple(row.case for row in supplies),
                           (source,), exposure="DISCLOSED_SOFTWARE_CONTROL")
    reference = DisclosedMethodSelection("method.disclosed.exact_four_state_reference", "EXACT_FOUR_STATE_REFERENCE")
    baseline = DisclosedMethodSelection("method.disclosed.conventional_scalar_reference", "CONVENTIONAL_SCALAR_REFERENCE")
    acceptance = ResponseAcceptance("acceptance.disclosed.response", (D("0.1"), D("0.1")),
        (D("0.05"), D("0.05")), "FINITE_JOINT_SUPPORT", None, source, D("0.8"), D("0.05"),
        reference.identity, baseline.identity, "complete_cpu_time", "s", 1, (), 0, 0,
        "One fixed mathematical assessment after the complete disclosed census",
        ("Return HOLD for missing support", "Stop after the declared assessment"), None,
        ("requirement.independent-experimental-validation",), "requirement.gp-applicability",
        "requirement.matrix-handoff", ("requirement.scientific-criteria-admission",), (source,))
    predictions = tuple(NominatedPrediction("prediction.nomination." + row.case.case_id,
        row.case.identity, "INCREASE", "PRESERVE_OR_INCREASE", None, (source,), row.case.exposure_group)
        for row in supplies if row.case.case_role == "CANDIDATE")
    return RubiscoResponseStudy("study.disclosed.response", cases, supplies,
        tuple(disclosed_decision(row) for row in supplies), predictions, acceptance,
        exposed_source_allocation(cases, supplies))
