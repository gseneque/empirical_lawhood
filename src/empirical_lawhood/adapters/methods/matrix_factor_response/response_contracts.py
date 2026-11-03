# SPDX-License-Identifier: MPL-2.0
"""Common development policy and distinct realised causal origin selections."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.science import eligible_origins
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_stable_id,
)

from .response_frontier import MatrixResponseFrontierProtocol


@dataclass(frozen=True, slots=True)
class MatrixResponsePopulationPolicy(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/population-policy"
    policy_id: str
    population: ObjectIdentity
    supplier_result: ObjectIdentity
    supplier_case: ArtifactIdentity
    protocol: MatrixResponseFrontierProtocol
    requested_root_ids: tuple[str, ...]
    origin_selector: str = "FIRST_CAUSALLY_ELIGIBLE_UNAMBIGUOUS_PRIMARY_Y_AFTER_RISK_START"
    evidence_role: str = "EXPOSED_DEVELOPMENT_NONPROMOTABLE"

    def __post_init__(self):
        validate_stable_id(self.policy_id)
        require_sorted_unique_strings(self.requested_root_ids, field_name="requested_root_ids", allow_empty=False)
        if (self.origin_selector != "FIRST_CAUSALLY_ELIGIBLE_UNAMBIGUOUS_PRIMARY_Y_AFTER_RISK_START"
                or self.evidence_role != "EXPOSED_DEVELOPMENT_NONPROMOTABLE"):
            raise ValueError("response policy changes its causal selector or promotes exposed evidence")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.policy_id, self)


@dataclass(frozen=True, slots=True)
class MatrixResponseOriginSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-frontier/origin-selection"
    selection_id: str
    policy: ObjectIdentity
    root_id: str
    independent_group_id: str
    family_id: str
    trace: ArtifactIdentity
    diagnostics: ArtifactIdentity | None
    disposition: str
    origin_tick: int | None
    cutoff: Decimal | None
    reasons: tuple[str, ...]

    def __post_init__(self):
        for name in ("selection_id", "root_id", "independent_group_id", "family_id"):
            validate_stable_id(getattr(self, name))
        require_sorted_unique_strings(self.reasons, field_name="reasons", allow_empty=False)
        selected = self.disposition == "SELECTED"
        if (self.disposition not in {"SELECTED", "NO_CAUSAL_ORIGIN", "OBSERVATION_UNRESOLVED"}
                or selected != (self.origin_tick is not None) or selected != (self.cutoff is not None)
                or selected and (self.diagnostics is None or type(self.origin_tick) is not int or self.origin_tick < 0)
                or self.policy.object_schema != MatrixResponsePopulationPolicy.SCHEMA):
            raise ValueError("response selection confuses a missing/uncertain origin with a supplied frame")
        if self.cutoff is not None:
            validate_decimal(self.cutoff, field_name="cutoff", minimum=Decimal(0))


def select_population_origins(policy, result, *, trace_artifacts):
    """Select saved causal frames without acquiring or producing spectra.

    The caller authenticates the supplier result against the policy artifact.
    That result's complete original population remains the denominator.
    """
    if (result.population.identity != policy.population
            or ObjectIdentity.from_record(result.result_id, result) != policy.supplier_result
            or result.rule.identity != policy.protocol.factor_rule
            or tuple(r.root_id for r in result.population.roots) != policy.requested_root_ids):
        raise ValueError("response origin selection substitutes its complete supplier population/rule")
    traces = {t.root.root_id: t for t in result.traces if t.view == "PRIMARY" and t.sector == "Y"}
    selected_traces = tuple(t for t in result.traces if t.view == "PRIMARY" and t.sector == "Y")
    if len(traces) != len(selected_traces) or set(traces) != set(policy.requested_root_ids):
        raise ValueError("response origin selection omits/duplicates a requested primaryY root")
    if set(trace_artifacts) != set(policy.requested_root_ids):
        raise ValueError("response origin selection lacks every original published trace identity")
    rows = []
    for root_id in policy.requested_root_ids:
        trace = traces[root_id]
        artifact = trace_artifacts[root_id]
        if (artifact.payload_schema != trace.SCHEMA or artifact.sha256 != trace.fingerprint()
                or artifact.size_bytes != len(trace.canonical_bytes())):
            raise ValueError("response origin selection substitutes original published trace bytes")
        available = eligible_origins(trace, result.rule)
        tick = available[0] if available else None
        uncertain = any(o.tick >= result.rule.risk_start_tick and o.causal_admitted is None for o in trace.observations)
        disposition = "SELECTED" if tick is not None else "OBSERVATION_UNRESOLVED" if uncertain else "NO_CAUSAL_ORIGIN"
        reasons = ("first-causal-origin-selected",) if tick is not None else (
            "origin-observation-unresolved",) if uncertain else ("no-causal-unambiguous-y-origin",)
        rows.append(MatrixResponseOriginSelection("selection." + root_id, policy.identity, root_id,
            trace.root.independent_unit_id, trace.root.family_id,
            artifact, trace.diagnostics,
            disposition, tick, None if tick is None else tick * result.rule.primary_dt, reasons))
    return tuple(rows)
