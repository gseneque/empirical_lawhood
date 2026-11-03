# SPDX-License-Identifier: MPL-2.0
"""Unpublished commitment shapes for preparation controls, never authority.

Actual authoring/entry must reopen these original locators and will refuse them.
No native source, scientific result or durable publication is fabricated here.
"""
from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_original_commitments import (
    MatrixPreparedOriginalCommitments, committed_entry_evidence,
)
from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtTrainingLocator
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments, MatrixProgrammePublishedInput
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recursive_handoff import AuthoredRecursiveWave


def unpublished_programme_commitments(record, name):
    """Explicit UNWRITTEN current C handle for refusal/shape controls only."""
    from tests.test_matrix_selected_protected import unpublished
    publication = unpublished(record, name)
    publication = replace(publication, logical=replace(publication.logical,
        payload_schema=MatrixProgrammeInputCommitments.SCHEMA,
        generic_validation=replace(publication.logical.generic_validation,
            payload_schema=MatrixProgrammeInputCommitments.SCHEMA)))
    reference = ObjectIdentity(name, MatrixProgrammeInputCommitments.SCHEMA, MatrixProgrammeInputCommitments.VERSION,
        publication.logical.content_sha256)
    return MatrixProgrammePublishedInput(reference, publication)


def unpublished_committed_evidence(evidence):
    def pin(name, kind):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a" * 64)

    locator = MatrixFiniteDtTrainingLocator("unpublished/disclosed-native-training", "run.disclosed-native-training",
        pin("packet.disclosed-native-training", AuthoredRecursiveWave),
        pin("plan.disclosed-native-training", DevelopmentExecutionPlan))
    commitment = unpublished_programme_commitments(evidence, "commitments.disclosed-unpublished-c")
    commitments = MatrixPreparedOriginalCommitments("commitments.disclosed-unpublished", locator, commitment, 128 * 1024**2)
    return committed_entry_evidence(evidence, commitments)
