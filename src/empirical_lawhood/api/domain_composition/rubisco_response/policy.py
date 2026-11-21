# SPDX-License-Identifier: MPL-2.0
"""Commit the Rubisco finite menu through the ordinary inquiry custody service."""

from decimal import localcontext

from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import _cost_precision, recheck_policy_composition
from empirical_lawhood.api.recursive_inquiry import commit_inquiry_decision


def commit_finite_response_policy(composition, *, sources, campaign, right, actor_id,
                                  project_root, artifact_writer, output_dir):
    """Recheck domain gating, actual source projection, authority and successor work.

    This only commits a decision. It neither enters an ACT nor grants scientific
    qualification. The exact frozen selection is retained in the shared policy's
    declared assumption. Actual source/access checks remain owned by the shared
    projector and each registered domain hook.
    """
    actual = recheck_policy_composition(composition)
    with localcontext() as context:
        context.prec = _cost_precision(actual.state, actual.selection, actual.templates)
        return commit_inquiry_decision(specification=actual.specification, state=actual.state,
            sources=sources, menu=actual.menu, policy=actual.policy, campaign=campaign, right=right,
            actor_id=actor_id, project_root=project_root, artifact_writer=artifact_writer, output_dir=output_dir)


def read_finite_response_policy(*, directory, artifact_writer):
    """Authenticate the original shared packet and recover its exact selection."""
    from empirical_lawhood.domains.rubisco.rubisco_response.comparison_decisions import retained_policy_decision
    from empirical_lawhood.domains.rubisco.rubisco_response.finite_policy import FiniteResponsePolicy
    from empirical_lawhood.api.recursive_inquiry import read_inquiry_decision
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes

    packet, records = read_inquiry_decision(directory=directory, artifact_writer=artifact_writer)
    assumptions = records["policy.json"].assumptions
    if len(assumptions) != 1:
        raise ValueError("finite Rubisco decision lacks its exact original policy selection")
    payload = (assumptions[0].reason + "\n").encode("utf-8")
    selection = decode_canonical_bytes(payload, FiniteResponsePolicy, maximum_bytes=8 * 1024 * 1024)
    return retained_policy_decision(selection, packet, records)
