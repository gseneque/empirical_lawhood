# SPDX-License-Identifier: MPL-2.0
"""Current-access retained comparison through the ordinary source and decision readers."""

from collections.abc import Mapping
from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.comparison_assessment import RetainedComparisonArm, assess_retained_comparison
from empirical_lawhood.domains.rubisco.rubisco_response.comparison_preparation import ARMS, ResponseComparisonDesign
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.requirements import scientific_scope
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.api.domain_composition.rubisco_response.policy import read_finite_response_policy
from empirical_lawhood.api.domain_composition.rubisco_response.report import read_reference_report


def read_comparison_analysis(*, design, arm_directories, information_cutoff, artifact_writer,
                             decision_directories=None, source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Read exact original custody; neither run nor recover an uncompleted effect.

    Supply all three arm keys, using None for an absent original programme.
    Decision paths are optional per-case complete checkpoint histories. Missing
    cases remain explicit unknown actions. Every supplied read revalidates
    current access and complete original source/receipt joins in its owner.
    """
    exact(design, ResponseComparisonDesign)
    exact(information_cutoff, InformationCutoff)
    if information_cutoff.phase is not CausalPhase.POST_OUTCOME or information_cutoff.clock_id != scientific_scope(design.study).clock_id:
        raise ValueError("retained comparison requires the exact explicit post-outcome clock")
    if not isinstance(arm_directories, Mapping) or set(arm_directories) != set(ARMS):
        raise ValueError("comparison reading requires every declared arm, including absent originals")
    decision_directories = {} if decision_directories is None else decision_directories
    if not isinstance(decision_directories, Mapping) or not set(decision_directories) <= {row.case.object_id for row in design.cases}:
        raise ValueError("comparison reading introduces a foreign decision case")
    if any(type(paths) is not tuple for paths in decision_directories.values()):
        raise ValueError("comparison decision paths must retain the original ordered checkpoint tuple")
    arms = tuple(RetainedComparisonArm(arm, None if arm_directories[arm] is None else read_reference_report(
        directory=arm_directories[arm], information_cutoff=information_cutoff, artifact_writer=artifact_writer,
        source_audit=source_audit, nomination_dossier=nomination_dossier, nomination_receipt=nomination_receipt)) for arm in ARMS)
    decisions = []
    for case in design.cases:
        paths = decision_directories.get(case.case.object_id, ())
        for path in paths:
            decision = read_finite_response_policy(directory=path, artifact_writer=artifact_writer)
            if decision.selection.case_id != case.case.object_id:
                raise ValueError("comparison path points to another case's original decision")
            decisions.append(decision)
    seed = design.canonical_bytes() + b"".join(row.canonical_bytes() for row in (*arms, *decisions))
    return assess_retained_comparison(design, arms, tuple(decisions),
        assessment_id="comparison.rubisco-response." + sha256(seed).hexdigest())
