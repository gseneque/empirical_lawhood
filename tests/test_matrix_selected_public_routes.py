# SPDX-License-Identifier: MPL-2.0
"""One public preparation lifecycle; retained low-level science is distinct."""
import pytest

from empirical_lawhood.adapters.methods.matrix_experimental_programme import selected_declarative_preparation as current
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_prepared_choices import (
    SelectedPreparedDevelopmentSpecification, SelectedPreparedProtectedSpecification,
)
from empirical_lawhood.api.experiment_preparation import experiment_protocols, prepare_experiment
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import transfer, confirmation  # noqa: F401


RETIRED = frozenset(('matrix.selected-prepared.opportunity', 'matrix.selected-protected.prepared',
    'matrix.selected-protected.prepared-v2', 'matrix.selected-revision-prepared.opportunity',
    'matrix.selected-revision-prepared.protected'))


def test_five_duplicate_public_frontdoors_are_absent_and_current_routes_have_real_runtime_owners():
    from empirical_lawhood.api.experiment_runtime_bindings import experiment_runtime_binding
    protocols = {value.protocol_id: value for value in experiment_protocols()}
    assert not RETIRED & protocols.keys()
    for name, development in ((current.DEVELOPMENT_PROTOCOL_ID, True), (current.PROTECTED_PROTOCOL_ID, False)):
        protocol = protocols[name]
        binding = experiment_runtime_binding(protocol)
        assert protocol.specification_type is (SelectedPreparedDevelopmentSpecification if development
            else SelectedPreparedProtectedSpecification)
        assert callable(binding.derive_inputs)
        assert callable(binding.bind_development_runtime) is development
        assert callable(binding.bind_handoff) is not development
        assert callable(binding.read_development_result if development else binding.read_result)


@pytest.mark.parametrize('account', ('ORIGINAL_E3', 'REVISION'))
@pytest.mark.parametrize('phase', ('E5_OPPORTUNITY', 'E5_CONFIRMATION', 'E6_TRANSFER'))
def test_both_current_accounts_keep_full_declared_population_and_refuse_unbound_inputs(
        opportunity, confirmation, transfer, monkeypatch, account, phase):  # noqa: F811
    # These existing disclosed mathematical bodies supply no actual source,
    # producer, C publication or authority. No scientific outcome is inferred.
    programme = {'E5_OPPORTUNITY': opportunity, 'E5_CONFIRMATION': confirmation, 'E6_TRANSFER': transfer}[phase]
    groups = 16 if phase == 'E5_OPPORTUNITY' else 64
    kind = SelectedPreparedDevelopmentSpecification if phase == 'E5_OPPORTUNITY' else SelectedPreparedProtectedSpecification
    nomination = phase == 'E5_OPPORTUNITY' or account == 'REVISION'
    specification = kind('specification.current-unbound.' + phase.lower() + '.' + account.lower(),
        account, phase, groups, programme.point_design.arms, programme.criterion,
        opportunity.minimum_recoverable_groups if nomination else None,
        opportunity.tie_policy if nomination else None, programme.transfer_domain_claims if phase == 'E6_TRANSFER' else ())
    def forbidden(*args, **kwargs):
        pytest.fail('unbound public preparation entered scientific lowering or native work')
    monkeypatch.setattr(current, 'lower', forbidden)
    prepared = prepare_experiment(specification, execution=ExecutionSelection(workers=1))
    assert prepared.draft is None and not prepared.executable
    assert dict(prepared.census.role_counts) == {'groups': 2 * groups if phase == 'E6_TRANSFER' else groups,
        'sources': groups * (3 if phase == 'E5_OPPORTUNITY' else 2)}
    assert dict(prepared.census.resolved_role_counts) == {'groups': 0, 'sources': 0}
    assert prepared.census.native_effect_count == 0
    assert {value.source_key for value in prepared.dependencies} == {'request'}
