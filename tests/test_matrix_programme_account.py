# SPDX-License-Identifier: MPL-2.0
"""Current immutable account joins over disclosed correspondence metadata."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.api.matrix_researcher_programme_prepared_lineage import require_current_account
from empirical_lawhood.kernel.decoding import decode_canonical_bytes, decode_canonical_record
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixResearchProgrammeSpecification
from tests.test_matrix_selected_opportunity import opportunity  # noqa: F401
from tests.test_matrix_selected_protected import confirmation, transfer  # noqa: F401

ROOT = Path(__file__).parents[1]


def _context(account, commitment):
    # These explicit sentinels isolate account/C correspondence. They are
    # neither an authenticated publication nor permission to read a product.
    return SimpleNamespace(design=SimpleNamespace(downstream_account=account),
        plan=SimpleNamespace(specification=SimpleNamespace(input_commitments=commitment)))


def test_current_programme_has_one_canonical_c_and_no_mutable_slot_or_predecessor():
    from empirical_lawhood.api.experiment_preparation import load_experiment_specification
    current = load_experiment_specification(ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json')
    raw = current.canonical_bytes()
    assert type(current) is MatrixResearchProgrammeSpecification and current.VERSION == '4.0.0'
    assert decode_canonical_bytes(raw, type(current), maximum_bytes=len(raw)) == current
    assert current.operations.VERSION == '2.0.0'
    for value in (current.operations.e1, current.operations.e2, current.operations.training):
        assert not hasattr(value, 'input_commitments')
    for field in ('active_slot', 'components', 'previous_selection', 'downstream_account'):
        assert not hasattr(current, field)
    with pytest.raises(ValueError, match='version'):
        decode_canonical_record({**current.to_document(), 'version': '3.0.0'}, type(current))


@pytest.mark.parametrize('phase', ('e1', 'e2', 'train'))
def test_initial_child_specifications_select_the_single_parent_c_without_authenticating_it(phase):
    from empirical_lawhood.api.experiment_preparation import load_experiment_specification
    from empirical_lawhood.api.matrix_programme_initial_phases import project_initial_phase
    current = load_experiment_specification(ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-programme/specification.example.json')
    native = load_experiment_specification(ROOT / 'programmes/foundations/emergent-structure/workflows/matrix-response-experiment/native-training-assembly.example.json')
    # This exercises projection only; the example C is unwritten and grants no access.
    context = SimpleNamespace(plan=SimpleNamespace(specification=current), namespace='projection.disclosed',
        design=SimpleNamespace(e3=SimpleNamespace(identity=native.candidate)),
        derive=lambda phase, specification, records, **kwargs: (phase, specification, records, kwargs))
    selected_phase, specification, records, options = project_initial_phase(context, phase)
    assert selected_phase == phase and specification.input_commitments == current.input_commitments
    selected = current.operations.training if phase == 'train' else getattr(current.operations, phase)
    assert records == {'selection' if phase == 'e1' else 'request': selected}
    assert getattr(specification, 'selection' if phase == 'e1' else 'request') == selected.identity
    assert options == ({'output_name': 'sources.json'} if phase == 'e1' else {})


@pytest.mark.parametrize('account', ('ORIGINAL_E3', 'REVISION'))
@pytest.mark.parametrize('phase', ('e5.development', 'e5.confirmation', 'e6'))
def test_each_prepared_scientific_phase_keeps_frozen_account_and_original_c(account, phase):
    c = object()
    context = _context(account, c)
    request = SimpleNamespace(original_commitments=SimpleNamespace(input_commitments=c),
        revision=None if account == 'ORIGINAL_E3' else object())
    inputs = SimpleNamespace(request=request)
    specification = SimpleNamespace(account=account)
    require_current_account(context, phase, specification, inputs)
    with pytest.raises(PermissionError, match='original D account'):
        require_current_account(context, phase, SimpleNamespace(account='REVISION' if account == 'ORIGINAL_E3' else 'ORIGINAL_E3'), inputs)
    with pytest.raises(PermissionError, match='original C publication'):
        require_current_account(context, phase, specification, SimpleNamespace(request=SimpleNamespace(
            original_commitments=SimpleNamespace(input_commitments=object()), revision=request.revision)))
    with pytest.raises(PermissionError, match='mix original and revision'):
        require_current_account(context, phase, specification, SimpleNamespace(request=SimpleNamespace(
            original_commitments=request.original_commitments, revision=object() if request.revision is None else None)))


@pytest.mark.parametrize('phase', ('e5.initialize-development', 'e5.initialize-confirmation', 'e6.initialize'))
def test_initialization_has_no_invented_account_field_and_still_joins_exact_c(phase):
    c = object()
    context = _context('ORIGINAL_E3', c)
    request = SimpleNamespace(original_commitments=SimpleNamespace(input_commitments=c))
    require_current_account(context, phase, object(), (request, object()))
    with pytest.raises(PermissionError, match='original C publication'):
        require_current_account(context, phase, object(), (SimpleNamespace(
            original_commitments=SimpleNamespace(input_commitments=object())), object()))


@pytest.mark.parametrize('phase', ('e5.source', 'e6.source'))
def test_original_prepared_source_keeps_instrument_controls_after_failed_nomination(confirmation, transfer, opportunity, phase):  # noqa: F811
    from tests.test_matrix_prepared_source import prepared_bank, disclosed_certificate
    from empirical_lawhood.adapters.methods import matrix_prepared_source_records as controls, matrix_prepared_source_assembly as source
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_opportunity import nominate_selected_opportunity
    from tests.test_matrix_selected_opportunity import literal_observations
    unadmitted = replace(opportunity, criterion=replace(opportunity.criterion, normalized_error_maximum=Decimal(999)))
    _, nomination = nominate_selected_opportunity(unadmitted, literal_observations(unadmitted), result_id='nomination.disclosed.unadmitted')
    assert nomination.disposition == 'NONDISCRIMINATING_OPPORTUNITY'
    assert all(not row.conditional_admission for row in nomination.cases)
    consumer = confirmation if phase == 'e5.source' else transfer
    bank = prepared_bank(consumer)
    certificate = disclosed_certificate(bank, unadmitted)
    assert controls.prepared_instrument_controls_supported(bank, certificate)
    inputs = source.MatrixPreparedSourceAssemblyInputs(prepared_programme=consumer, development_product=certificate.locator)
    require_current_account(_context('ORIGINAL_E3', object()), phase, object(), inputs)
    with pytest.raises(PermissionError, match='original D account'):
        require_current_account(_context('REVISION', object()), phase, object(), inputs)
