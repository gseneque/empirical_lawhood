# SPDX-License-Identifier: MPL-2.0
"""Selected-input access ordering over actual bounded canonical and FILE I/O.

The small payloads are disclosed software data. Stored-grant controls below use
actual ordinary test authority custody, but their four literal E3 locators are
unpublished: they prove permission refresh/order, not a four-product scientific
E3 lifecycle, qualification, installed CLI acceptance or native execution.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import os
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_PYTHON_SOURCE_CODEC
from empirical_lawhood.api import experiment_preparation as owner
from empirical_lawhood.api import experiment_runtime_bindings as bindings
from empirical_lawhood.api import recursive_qualified_parents as authority
from empirical_lawhood.api import selected_e3_access as access_owner
from empirical_lawhood.infrastructure.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.experiment_inputs import (
    ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.experiment_preparation import (
    ExperimentProtocolDeclaration, ExperimentRuntimeBinding, PreparedExperimentInputs,
)
from tests.test_current_result_custody import actual_issued_current_task_controls  # noqa: F401
from tests.test_current_result_historical_access import later_reveal
from tests.test_rubisco_gas_contrast import _real_plane
from tests.test_selected_e3_current_access import LaterClock, evidence, literal_originals


@dataclass(frozen=True, slots=True)
class Locator(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/selected-bootstrap-locator'
    record_id: str
    original: ObjectIdentity


@dataclass(frozen=True, slots=True)
class Model(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/selected-bootstrap-model'
    record_id: str
    disclosed_values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Specification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/tests/selected-bootstrap-experiment'
    specification_id: str
    evidence: ObjectIdentity

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def _scope(directory, monkeypatch, *, guard, bootstrap=None, hooked=True, after_bind=None):
    """Real selected bytes; callbacks only expose the shared loader boundary."""
    from empirical_lawhood.adapters.composition import generated_extension_bundles as generated

    directory.mkdir(parents=True, exist_ok=True)
    model = Model('model.disclosed.bootstrap', (2, 3, 5))
    locator = Locator('locator.disclosed.bootstrap', ObjectIdentity.from_record(model.record_id, model))
    specification = Specification('specification.disclosed.bootstrap',
        ObjectIdentity.from_record(locator.record_id, locator))
    records = {'evidence': locator, 'model': model}
    rows = []
    for key, record in sorted(records.items()):
        raw = record.canonical_bytes()
        (directory / (key + '.json')).write_bytes(raw)
        rows.append(ExperimentInputBinding(key, ObjectIdentity.from_record(record.record_id, record),
            key + '.json', len(raw)))
    raw_file = b'values = (7, 11)\n'
    member = directory / 'original.py'
    member.write_bytes(raw_file)
    codec = MATRIX_PYTHON_SOURCE_CODEC
    artifact = ArtifactIdentity('artifact.disclosed.bootstrap', 'disclosed-software', codec.payload_schema,
        sha256(raw_file).hexdigest(), codec.media_type, len(raw_file))
    protocol_id = 'test.selected-bootstrap'
    selector = ExperimentFileInputSelection('selection.disclosed.bootstrap', protocol_id, tuple(rows),
        (ExperimentFileInputBinding('original', artifact, codec.record_version, member.name, len(raw_file)),))
    source = directory / 'sources.json'
    source.write_bytes(selector.canonical_bytes())
    calls = []

    def bind(specification, selected, *, files):
        calls.append((specification, dict(selected), dict(files)))
        if after_bind is not None:
            after_bind()
        return PreparedExperimentInputs({}, (dict(selected), dict(files)))

    def forbidden(*args, **kwargs):
        raise AssertionError('selected-input decoding invoked a scientific or native lifecycle')

    declaration = ExperimentProtocolDeclaration(protocol_id, Specification, forbidden,
        'test-selected-bootstrap', input_record_types=(Locator, Model), bind_inputs=bind,
        input_storage_codecs=(codec,), requires_development_runtime_binding=hooked)

    def selected_bootstrap(**arguments):
        assert arguments['specification'] is specification
        assert arguments['selection'] == selector
        assert arguments['selection_path'] == source.resolve(strict=True)
        if bootstrap is not None:
            return bootstrap(**arguments)
        assert arguments['read_locator']('evidence', specification.evidence, Locator) == locator
        guard()
        return guard

    runtime = ExperimentRuntimeBinding(protocol_id, None, bind_development_runtime=forbidden,
        read_development_result=forbidden, specification_schema=Specification.SCHEMA,
        development_bootstrap_record_types=(Locator,), bootstrap_development_input_access=forbidden,
        bootstrap_selected_input_access=selected_bootstrap) if hooked else None
    monkeypatch.setattr(generated, 'EXPERIMENT_PROTOCOL_DECLARATIONS', (declaration,))
    monkeypatch.setattr(bindings, 'experiment_runtime_binding', lambda declaration: runtime)
    return SimpleNamespace(specification=specification, selector=selector, source=source,
        records=records, calls=calls, locator=locator, member=member, runtime=runtime)


def _observe_protected_opens(monkeypatch, events, *, before_open=None):
    original_open = os.open

    def observed(path, *args, **kwargs):
        if not isinstance(path, int) and Path(path).name in ('model.json', 'original.py', 'guarded-sibling.json'):
            if before_open is not None:
                before_open(Path(path).name)
            events.append(('open', Path(path).name))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(os, 'open', observed)


def test_current_guard_precedes_actual_canonical_and_file_opens_and_final_return(tmp_path, monkeypatch):
    events = []
    def guard():
        events.append(('guard', None))
    case = _scope(tmp_path, monkeypatch, guard=guard)
    writer = object()
    _observe_protected_opens(monkeypatch, events)
    result = owner.load_experiment_inputs(case.specification, case.source, artifact_writer=writer)
    assert len(case.calls) == 1 and result.method_inputs[0] == case.records
    opens = [(index, value) for index, value in enumerate(events) if value[0] == 'open']
    assert {value[1] for _, value in opens} == {'model.json', 'original.py'}
    assert all(index > 0 and events[index - 1][0] == 'guard' for index, _ in opens)
    assert events[-1][0] == 'guard'


def test_initial_permission_refusal_opens_no_model_or_file(tmp_path, monkeypatch):
    events = []
    def guard():
        raise PermissionError('original grant refused before selected body')
    case = _scope(tmp_path, monkeypatch, guard=guard)
    _observe_protected_opens(monkeypatch, events)
    with pytest.raises(PermissionError, match='original grant refused'):
        owner.load_experiment_inputs(case.specification, case.source, artifact_writer=object())
    assert not events and not case.calls


@pytest.mark.parametrize('target', ('model.json', 'original.py', 'bind', 'return'))
def test_permission_is_refreshed_at_later_reads_and_after_binder(tmp_path, monkeypatch, target):
    state = {'refuse': False}
    events = []
    def guard():
        if state['refuse']:
            raise PermissionError('original grant changed during selected inputs')
        events.append(('guard', None))
    def bound():
        if target == 'return':
            state['refuse'] = True
    case = _scope(tmp_path, monkeypatch, guard=guard, after_bind=bound)
    def opened(name):
        if ((name == 'model.json' and target == 'original.py')
                or name == 'original.py' and target == 'bind'):
            state['refuse'] = True
    _observe_protected_opens(monkeypatch, events, before_open=opened)
    if target == 'model.json':
        # The locator may be read without exposing its referenced model. Expiry
        # after that metadata read must refuse before the model is opened.
        from empirical_lawhood.infrastructure import bounded_io
        read = bounded_io.read_bounded_bytes
        def locator_read(path, **kwargs):
            raw = read(path, **kwargs)
            if Path(path).name == 'evidence.json':
                state['refuse'] = True
            return raw
        monkeypatch.setattr(bounded_io, 'read_bounded_bytes', locator_read)
    with pytest.raises(PermissionError, match='grant changed'):
        owner.load_experiment_inputs(case.specification, case.source, artifact_writer=object())
    assert len(case.calls) == (1 if target == 'return' else 0)
    if target == 'model.json':
        assert not any(row[0] == 'open' for row in events)
    elif target == 'original.py':
        assert ('open', 'original.py') not in events


@pytest.mark.parametrize('mutation', ('key', 'pin', 'kind', 'file'))
def test_closed_locator_reader_cannot_open_model_or_file(tmp_path, monkeypatch, mutation):
    events = []
    def bootstrap(*, read_locator, specification, **_):
        key, pin, kind = 'evidence', specification.evidence, Locator
        if mutation == 'key':
            key = 'model'
        elif mutation == 'pin':
            pin = replace(pin, object_id=pin.object_id + '.foreign')
        elif mutation == 'kind':
            kind = Model
        else:
            key = 'original'
        read_locator(key, pin, kind)
        pytest.fail('closed locator reader accepted a different selected operand')
    case = _scope(tmp_path, monkeypatch, guard=lambda: None, bootstrap=bootstrap)
    _observe_protected_opens(monkeypatch, events)
    with pytest.raises((ValueError, TypeError, PermissionError), match='locator|exact|selected|bootstrap'):
        owner.load_experiment_inputs(case.specification, case.source, artifact_writer=object())
    assert not events and not case.calls


@pytest.mark.parametrize('returned', (None, True, False))
def test_hook_requires_actual_writer_and_callable_guard(tmp_path, monkeypatch, returned):
    case = _scope(tmp_path, monkeypatch, guard=lambda: None, bootstrap=lambda **_: returned)
    with pytest.raises(PermissionError, match='actual selected artifact writer'):
        owner.load_experiment_inputs(case.specification, case.source)
    with pytest.raises((ValueError, TypeError), match='callable|guard'):
        owner.load_experiment_inputs(case.specification, case.source, artifact_writer=object())
    assert not case.calls


def test_callable_hook_cannot_open_selected_model_or_file_without_actual_writer(tmp_path, monkeypatch):
    events = []
    case = _scope(tmp_path, monkeypatch, guard=lambda: None,
        bootstrap=lambda **_: events.append(('callback', None)) or (lambda: None))
    _observe_protected_opens(monkeypatch, events)
    with pytest.raises(PermissionError, match='actual selected artifact writer'):
        owner.load_experiment_inputs(case.specification, case.source)
    assert not events and not case.calls


def test_private_guard_is_composed_and_no_hook_blind_route_still_needs_no_writer(tmp_path, monkeypatch):
    case = _scope(tmp_path, monkeypatch, guard=lambda: None)
    def refused():
        raise PermissionError('existing private guard remains mandatory')
    with pytest.raises(PermissionError, match='private guard'):
        owner.load_experiment_inputs(case.specification, case.source,
            artifact_writer=object(), _input_access_guard=refused)
    assert not case.calls
    blind = _scope(tmp_path, monkeypatch, guard=refused, hooked=False)
    assert owner.load_experiment_inputs(blind.specification, blind.source).method_inputs[0] == blind.records
    assert len(blind.calls) == 1


def _stored_access(f, *, replacement):
    original = literal_originals(f, f.control.reveal)
    selected = literal_originals(f, replacement)
    return access_owner.SelectedE3OriginalInputAccess(f.control.service.artifact_plane,
        original, selected, evidence(original).produced_input_parents, ((selected[0], f.control.package),))


def test_actual_stored_expired_grant_refuses_before_selected_body(
        actual_issued_current_task_controls, tmp_path, monkeypatch):  # noqa: F811
    f = actual_issued_current_task_controls
    access = _stored_access(f, replacement=f.control.reveal)
    monkeypatch.setattr(authority, 'datetime', LaterClock)
    case = _scope(tmp_path, monkeypatch, guard=access.require_current)
    events = []
    _observe_protected_opens(monkeypatch, events)
    with pytest.raises(PermissionError, match='expired'):
        owner.load_experiment_inputs(case.specification, case.source,
            artifact_writer=f.control.service.artifact_plane)
    assert not events and not case.calls and not f.control.executor.invocations


def test_actual_stored_replacement_is_reloaded_between_model_and_file(
        actual_issued_current_task_controls, tmp_path, monkeypatch):  # noqa: F811
    f = actual_issued_current_task_controls
    replacement = later_reveal(f)
    access = _stored_access(f, replacement=replacement)
    monkeypatch.setattr(authority, 'datetime', LaterClock)
    state = {'revoked': False}
    original_load = ExternalStudyOperationAuthorityStore.load
    def load(store, authority_id):
        if state['revoked'] and authority_id == replacement.authority_id:
            raise PermissionError('actual replacement no longer available')
        return original_load(store, authority_id)
    monkeypatch.setattr(ExternalStudyOperationAuthorityStore, 'load', load)
    case = _scope(tmp_path, monkeypatch, guard=access.require_current)
    events = []
    def opened(name):
        if name == 'model.json':
            state['revoked'] = True
    _observe_protected_opens(monkeypatch, events, before_open=opened)
    with pytest.raises(PermissionError, match='actual replacement'):
        owner.load_experiment_inputs(case.specification, case.source,
            artifact_writer=f.control.service.artifact_plane)
    assert ('open', 'model.json') in events and ('open', 'original.py') not in events
    assert not case.calls and not f.control.executor.invocations


def test_derived_target_access_precedes_actual_publication_sibling_hash(tmp_path, monkeypatch):
    plane = _real_plane(tmp_path / 'guarded-publication')
    def refused():
        raise PermissionError('original grant refused before target custody hash')
    case = _scope(Path(plane.root.contract.canonical_path) / 'derived', monkeypatch, guard=refused)
    target = case.source.parent / 'specification.json'
    sibling = Model('model.disclosed.publication-sibling', (13, 17))
    # The real writer owns these publications from their first write; do not
    # ask it to adopt the fixture's initially unowned copied selector file.
    case.source.unlink()
    pubs = plane.write_batch(tuple(ArtifactWriteRequest(record_id, 'derived/' + name, record.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, 'application/json', 'publication.disclosed.bootstrap', 'derived',
        record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
        for name, record_id, record in ((target.name, case.specification.specification_id, case.specification),
            (case.source.name, case.selector.selection_id, case.selector),
            ('guarded-sibling.json', sibling.record_id, sibling))))
    result = SimpleNamespace(target_specification=case.specification, target_specification_path=target,
        source_selection=case.selector, source_selection_path=case.source, publications=pubs)
    events = []
    _observe_protected_opens(monkeypatch, events)
    with pytest.raises(PermissionError, match='before target custody hash'):
        owner._authenticate_derived_target(result, plane)
    assert not events and not case.calls


@pytest.fixture(scope='module')
def domain_locator_case():
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as records
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorResources
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import (
        PROTOCOL_ID, SelectedE3E4ExperimentSpecification,
    )
    from empirical_lawhood.kernel.authority import ResourceBudget
    from empirical_lawhood.planning.campaigns import CampaignSpec
    from tests.test_matrix_programme_scientific_design import build_scientific_design
    value = evidence(literal_originals())
    design = build_scientific_design()
    resources = ScheduledFullFactorResources('resources.disclosed.bootstrap', tuple((phase,
        ResourceBudget(1, 1024**2, 0, 60, 1024**2, 1024**2)) for phase in ('assess', 'measure', 'reduce')))
    specification = SelectedE3E4ExperimentSpecification('specification.disclosed.e3-bootstrap', value.programme,
        ObjectIdentity('bank.disclosed.e3-bootstrap', records.SelectedE3E4DevelopmentBank.SCHEMA,
            records.SelectedE3E4DevelopmentBank.VERSION, 'a' * 64), value.identity,
        ObjectIdentity('campaign.disclosed.e3-bootstrap', CampaignSpec.SCHEMA, CampaignSpec.VERSION, 'b' * 64),
        design.e4_structure, resources)
    selection = ExperimentFileInputSelection('selection.disclosed.e3-bootstrap', PROTOCOL_ID,
        (ExperimentInputBinding('evidence', value.identity, 'evidence.json', len(value.canonical_bytes())),), ())
    return specification, selection, value


def test_exact_domain_locator_joins_precede_original_metadata_authentication(domain_locator_case, monkeypatch):
    specification, selection, value = domain_locator_case
    writer, read_access, guard = object(), object(), lambda: None
    seen = []
    def authenticate(**arguments):
        seen.append(arguments)
        return SimpleNamespace(require_current=guard)
    monkeypatch.setattr(access_owner, 'original_input_access', authenticate)
    def read_locator(key, pin, kind):
        assert (key, pin, kind) == ('evidence', value.identity, type(value))
        return value
    assert access_owner.bootstrap_selected_input_access(specification=specification, selection=selection,
        read_locator=read_locator, artifact_writer=writer, read_access=read_access) is guard
    assert seen == [dict(artifact_writer=writer, evidence=value, read_access=read_access)]


@pytest.mark.parametrize('mutation', ('missing', 'key', 'pin', 'programme', 'body'))
def test_domain_locator_substitution_never_reaches_original_authentication(domain_locator_case, monkeypatch, mutation):
    specification, selection, value = domain_locator_case
    if mutation == 'missing':
        selection = replace(selection, bindings=())
    elif mutation == 'key':
        selection = replace(selection, bindings=(replace(selection.bindings[0], key='other'),))
    elif mutation == 'pin':
        selection = replace(selection, bindings=(replace(selection.bindings[0],
            identity=replace(specification.evidence, object_id='evidence.disclosed.foreign')),))
    elif mutation == 'programme':
        specification = replace(specification, programme=replace(specification.programme, object_id='programme.disclosed.foreign'))
    else:
        value = replace(value, record_id=value.record_id + '.foreign')
    def forbidden(**_):
        pytest.fail('foreign selected locator reached original metadata/authority reads')
    monkeypatch.setattr(access_owner, 'original_input_access', forbidden)
    with pytest.raises(PermissionError, match='evidence|programme'):
        access_owner.bootstrap_selected_input_access(specification=specification, selection=selection,
            read_locator=lambda *args: value, artifact_writer=object())


def test_declared_read_access_selection_is_only_four_exact_original_locators():
    values = literal_originals()
    selected = access_owner.select_current_e3_access(tuple(reversed(values)))
    assert selected.originals == values
    assert selected.effective_originals(values) == values
    for malformed in (values[:3], (*values, values[0]), (values[0], values[0], *values[2:])):
        with pytest.raises(ValueError, match='four original product locators'):
            access_owner.select_current_e3_access(malformed)
    with pytest.raises(TypeError, match='exact original-product'):
        access_owner.select_current_e3_access((object(),))
