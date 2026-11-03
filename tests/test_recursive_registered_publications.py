# SPDX-License-Identifier: MPL-2.0
"""Registration preserves domain custody predicates and their pre-I/O census."""

from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import commitment as e1_commitment
from empirical_lawhood.adapters.methods.matrix_factor_confirmation import operation_bindings as e1
from empirical_lawhood.adapters.methods.matrix_scheduled_history import commitment as scheduled_commitment
from empirical_lawhood.adapters.methods.matrix_scheduled_history import compact_bindings as compact
from empirical_lawhood.adapters.methods.matrix_scheduled_history import compact_records
from empirical_lawhood.adapters.methods.matrix_scheduled_history import operation_bindings as scheduled
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.runtime.plans import ScientificStage

OWNERS = (
    (e1, e1_commitment.E1CommitmentConfig, e1_commitment.authenticate_prior_publications,
        "matrix-factor-confirmation.prior-publications.v1",
        "120905bedb6577a1ec051228860827fff6a62fcec7135373c091caea53887485"),
    (scheduled, scheduled_commitment.ScheduledCommitmentConfig, scheduled_commitment.authenticate_prior_publications,
        "matrix-scheduled-history.prior-publications.v1",
        "64336f8c23714324c1521034b34b82c90d86f16b9cf3b2d75e58eaa9518a8c0d"),
    (compact, compact_records.ScheduledCompactCommitmentConfig, compact_records.authenticate_prior_publications,
        "matrix-scheduled-history-compact.prior-publications.v1",
        "be8ba7e4a03addd58d5a294849788a0c4a287617a790ddde758e874cb667fed3"),
)


def _commitment_registration(owner, config_type):
    registrations = owner.operation_registrations()
    selected = tuple(row for row in registrations if row.config_record_type is config_type)
    assert len(selected) == 1
    assert all(not row.publication_requirements for row in registrations if row.config_record_type is not config_type)
    return selected[0]


@pytest.mark.parametrize("owner,config_type,validator,requirement_id,manifest_sha256", OWNERS)
def test_commitment_registration_keeps_original_predicate_scope_and_manifest(
        owner, config_type, validator, requirement_id, manifest_sha256):
    registered = _commitment_registration(owner, config_type)
    assert len(registered.publication_requirements) == 1
    requirement = registered.publication_requirements[0]
    assert requirement.requirement_id == requirement_id and requirement.validate is validator
    assert registered.stage is ScientificStage.FREEZE and not registered.native_effect
    assert registered.outcome_access is OutcomeAccess.OUTCOME_BLIND
    assert registered.visibility_ceiling is VisibilityCeiling.PROSPECTIVE
    manifest = next(row for row in owner.operation_manifests()
        if row.capability_key == registered.selection.capability_key)
    assert manifest.fingerprint() == manifest_sha256


class _ForbiddenCustody:
    def __getattr__(self, name):
        raise AssertionError("incomplete domain configuration census reached custody I/O: " + name)


@pytest.mark.parametrize("owner,config_type,validator,requirement_id,manifest_sha256", OWNERS)
def test_registered_original_validator_retains_complete_config_census_before_custody(
        owner, config_type, validator, requirement_id, manifest_sha256):
    requirement = _commitment_registration(owner, config_type).publication_requirements[0]
    # These uninitialized objects test only the original exact-type/count guard.
    # They contain no source, signer, grant or eligible scientific evidence.
    configs = tuple(SimpleNamespace(record=object.__new__(config_type)) for _ in range(2))
    with pytest.raises(ValueError, match="one complete"):
        requirement.validate(_ForbiddenCustody(), configs)
    assert requirement.validate(_ForbiddenCustody(), (SimpleNamespace(record=None),)) is None
