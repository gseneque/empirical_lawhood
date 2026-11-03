# SPDX-License-Identifier: MPL-2.0
"""Literal input-label arithmetic; these parents confer no authority."""
from hashlib import sha256
from types import SimpleNamespace

from empirical_lawhood.api.experiment_runtime_bindings import original_input_record_publication
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactLineageParent


def test_mixed_dev_and_sealed_originals_do_not_declassify_model_bearing_input():
    model = object()
    parents = tuple(ArtifactLineageParent(ObjectIdentity(name, "empirical-lawhood/testing/original", "1.0.0",
        sha256(name.encode()).hexdigest()), visibility, access) for name, visibility, access in (
            ("original.dev", VisibilityCeiling.DEVELOPMENT_ONLY, OutcomeAccess.DEVELOPMENT_VISIBLE),
            ("original.sealed", VisibilityCeiling.PROSPECTIVE, OutcomeAccess.EVALUATION_SEALED)))

    def record_parents(record):
        assert record is model
        return parents

    actual_parents, access, visibility = original_input_record_publication(record=model,
        original_input_access=SimpleNamespace(record_parents=record_parents))
    assert actual_parents == parents
    assert access is OutcomeAccess.EVALUATION_SEALED
    assert visibility is VisibilityCeiling.DEVELOPMENT_ONLY


def test_no_original_scope_keeps_intrinsic_publication_blind_and_prospective():
    assert original_input_record_publication(record=object(), original_input_access=None) == (
        (), OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
