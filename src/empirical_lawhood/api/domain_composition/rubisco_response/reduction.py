# SPDX-License-Identifier: MPL-2.0
"""Authenticate retained reference scope before reporting unresolved target selection."""

from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.reduction_target import assess_reduction_target
from empirical_lawhood.api.domain_composition.rubisco_response.report import read_reference_report


def read_reduction_target(*, directory, information_cutoff, artifact_writer,
                          source_audit=None, nomination_dossier=None, nomination_receipt=None):
    """Read original custody; no worker, acquisition or convenient target selection."""
    report = read_reference_report(directory=directory, information_cutoff=information_cutoff,
        artifact_writer=artifact_writer, source_audit=source_audit,
        nomination_dossier=nomination_dossier, nomination_receipt=nomination_receipt)
    return assess_reduction_target(report,
        assessment_id="target.rubisco-response." + sha256(report.canonical_bytes()).hexdigest())
