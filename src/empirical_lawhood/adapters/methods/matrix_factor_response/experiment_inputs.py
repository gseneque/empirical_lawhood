# SPDX-License-Identifier: MPL-2.0
"""Closed Matrix source-bank bindings after generic canonical byte verification.

Binding a retained record authenticates its selected bytes. Source eligibility,
causal joins, full unit census and numerical admissibility remain preparation
checks; exposed banks never establish prospective or protected authority.
"""

from collections.abc import Mapping

from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentInputs

from .experiment_methods import MatrixE3FeatureBank, MatrixE3MethodInputs, MatrixE3OutcomeBank
from .experiment_specification import MatrixResponseErrorSpecification


ROLES = ("train", "calibration", "evaluation")


def input_record_types() -> tuple[type[CanonicalRecord], ...]:
    """The complete code-owned decoder set for this exposed input route."""
    from .protected_preparation import ProtectedE3PreparationSelection

    return (UnitAllocation, CampaignSpec, MatrixE3FeatureBank, MatrixE3OutcomeBank, ProtectedE3PreparationSelection)


def bind_matrix_response_inputs(
    specification: MatrixResponseErrorSpecification,
    records: Mapping[str, CanonicalRecord],
    *, files=None,
) -> PreparedExperimentInputs:
    """Resolve closed typed keys while retaining missing banks for preflight.

    The caller has already bounded and authenticated each original canonical
    member. This callback performs no I/O, import selection, fitting or native
    acquisition. Missing campaign and bank operands remain explicit prerequisites.
    """
    if type(specification) is not MatrixResponseErrorSpecification:
        raise TypeError("Matrix input binding requires its typed specification")
    specification.__post_init__()
    if specification.evidence_scope == "PROSPECTIVE_REQUIRED":
        from .protected_preparation import bind_protected_e3_experiment_inputs

        return bind_protected_e3_experiment_inputs(specification, records, files=files)
    if files:
        raise ValueError("exposed Matrix inputs use canonical source banks")
    if not isinstance(records, Mapping):
        raise TypeError("Matrix input binding requires authenticated keyed canonical records")
    source_keys = {selection.source_key for selection in specification.populations}
    bank_types = {role + "-" + kind: record_type for role in ROLES
        for kind, record_type in (("features", MatrixE3FeatureBank), ("outcomes", MatrixE3OutcomeBank))}
    reserved_keys = {"campaign", *bank_types}
    if source_keys & reserved_keys:
        raise ValueError("Matrix population source keys collide with the closed method input keys")
    expected_types = {**dict.fromkeys(source_keys, UnitAllocation), "campaign": CampaignSpec, **bank_types}
    unknown = set(records) - set(expected_types)
    if unknown:
        raise ValueError("Matrix input binding includes unknown keys: " + ", ".join(sorted(unknown)))
    for key, record in records.items():
        if type(record) is not expected_types[key]:
            raise TypeError("Matrix input " + key + " has the wrong closed record type")
        record.__post_init__()
        if key in bank_types and record.role != key.rsplit("-", 1)[0]:
            raise ValueError("Matrix bank key changes its original role: " + key)
    supplied_banks = set(records) & set(bank_types)
    campaign = records.get("campaign")
    method_inputs = None if campaign is None and not supplied_banks else MatrixE3MethodInputs(campaign,
        tuple(records[role + "-features"] for role in ROLES if role + "-features" in records),
        tuple(records[role + "-outcomes"] for role in ROLES if role + "-outcomes" in records))
    return PreparedExperimentInputs({key: records[key] for key in sorted(source_keys) if key in records}, method_inputs)
