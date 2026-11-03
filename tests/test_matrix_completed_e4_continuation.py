# SPDX-License-Identifier: MPL-2.0
"""Exposed metadata controls, without original science or native execution."""
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_researcher_programme import source_continuation as domain
from empirical_lawhood.adapters.methods.matrix_researcher_programme.selection import MatrixProgrammePhaseBinding
from empirical_lawhood.api import matrix_programme_completed_continuation as owner
from empirical_lawhood.api.matrix_researcher_programme import _publish
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.development_output_repair import DevelopmentOutputRepairTerminalEvent
from empirical_lawhood.runtime.development_controller_repair import DevelopmentControllerRepairTerminalEvent
from empirical_lawhood.runtime.native_continuation_execution import DevelopmentNativeContinuationTerminalEvent
from empirical_lawhood.runtime.recovery import RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent
from tests.test_matrix_programme_source_continuation import _plans, metadata_case  # noqa: F401


def _pin(name, kind, fingerprint='a' * 64):
    return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, fingerprint)


def _report(name, kind=DevelopmentRunRecoveryTerminalEvent):
    return dict(read_scope='EXECUTION_RECORDS', execution_complete=True,
        operational_terminal='AUTHENTICATED', terminal=_pin('terminal.' + name, kind).to_document())


@pytest.mark.parametrize('kind', (DevelopmentRunRecoveryTerminalEvent, DevelopmentOutputRepairTerminalEvent,
    DevelopmentControllerRepairTerminalEvent, DevelopmentNativeContinuationTerminalEvent))
def test_completed_e4_record_retains_acquisition_and_separate_structural_terminal(metadata_case, kind):  # noqa: F811
    _, request, target = _plans(metadata_case)
    bindings = tuple((phase, _pin('binding.' + phase, MatrixProgrammePhaseBinding))
        for phase in domain.COMPLETED_E4_PHASES)
    kinds = (RunRecoveryTerminalEvent, DevelopmentRunRecoveryTerminalEvent,
        DevelopmentRunRecoveryTerminalEvent, RunRecoveryTerminalEvent, kind)
    terminals = tuple((phase, _pin('terminal.' + phase, item))
        for phase, item in zip(domain.COMPLETED_E4_PHASES, kinds, strict=True))
    structure = _pin('terminal.e4.structure', DevelopmentRunRecoveryTerminalEvent)
    record = domain.MatrixProgrammeCompletedE4SourceContinuation('continuation.exposed-e4', request,
        target, bindings, terminals, structure)
    writer = metadata_case.case.writer
    relative = 'disclosed-completed-e4/' + kind.__name__ + '/source-continuation.json'
    _publish(writer, Path(writer.root.contract.canonical_path) / relative, record)
    assert owner.read_source_continuation(writer, relative, 64 * 1024**2) == record
    assert decode_canonical_bytes(record.canonical_bytes(), type(record), maximum_bytes=None) == record
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.extension_bundle import EXPERIMENT_PROTOCOL_DECLARATIONS
    declaration, = (row for row in EXPERIMENT_PROTOCOL_DECLARATIONS if row.protocol_id == domain.PROTOCOL_ID)
    assert type(record) in declaration.input_record_types
    with pytest.raises(ValueError, match='complete E1/E2/TRAIN/E3'):
        replace(record, predecessor_bindings=bindings[:-1])
    with pytest.raises(ValueError, match='terminal contract'):
        replace(record, predecessor_terminals=(*terminals[:-1], ('e4.development', bindings[-1][1])))
    with pytest.raises(TypeError, match='structural development terminal'):
        replace(record, completed_e4_structure_terminal=terminals[0][1])


@pytest.mark.parametrize('phase', ('e4.revision', 'e4.source-cal', 'e4.calibration', 'e5.development', 'e6'))
@pytest.mark.parametrize('kind', ('metadata', 'child', 'binding', 'run', 'dangling'))
def test_completed_e4_never_discards_an_authored_later_phase(tmp_path, phase, kind):
    context = SimpleNamespace(directory=tmp_path, bindings=dict.fromkeys(domain.COMPLETED_E4_PHASES),
        pending_bindings={}, child_directory=lambda phase: tmp_path/'children'/phase,
        metadata_directory=lambda phase: tmp_path/'derived'/phase)
    context.child_directory('e4.development').mkdir(parents=True)
    owner.require_unentered_successors(context, completed_phases=domain.COMPLETED_E4_PHASES)
    path = (context.metadata_directory(phase) if kind == 'metadata' else context.child_directory(phase)
        if kind == 'child' else tmp_path/'runs'/(phase + '.main.json') if kind == 'run'
        else tmp_path/'bindings'/(phase + '.json'))
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == 'dangling':
        path.symlink_to(tmp_path/'absent')
    else:
        path.mkdir()
    with pytest.raises(PermissionError, match='entered or authored successor'):
        owner.require_unentered_successors(context, completed_phases=domain.COMPLETED_E4_PHASES)


@pytest.mark.parametrize('part', ('acquisition', 'structure'))
@pytest.mark.parametrize('field,value', (('execution_complete', False),
    ('read_scope', 'INCOMPLETE'), ('operational_terminal', 'UNAUTHENTICATED')))
def test_completed_e4_requires_both_authenticated_complete_censuses(part, field, value):
    report = _report('e4', DevelopmentOutputRepairTerminalEvent)
    report['structure'] = _report('structure')
    assert owner.completed_e4_terminals(report) == (
        _pin('terminal.e4', DevelopmentOutputRepairTerminalEvent),
        _pin('terminal.structure', DevelopmentRunRecoveryTerminalEvent))
    (report if part == 'acquisition' else report['structure'])[field] = value
    with pytest.raises(PermissionError, match='complete original E4'):
        owner.completed_e4_terminals(report)


@dataclass
class _Service:
    artifact_writer: object
    storage_profile: object


@dataclass
class _Context:
    service: object
    directory: Path
    bindings: dict
    pending_bindings: dict
    phase_origins: dict

    @property
    def writer(self):
        return self.service.artifact_writer

    def child_directory(self, phase):
        return self.directory/'children'/phase

    def metadata_directory(self, phase):
        return self.directory/'derived'/phase


def test_completed_e4_custody_holds_structural_controls_and_never_selects_unentered_adoption(
        metadata_case, monkeypatch, tmp_path):  # noqa: F811
    # Scientific reads and current grants are deliberately absent. This checks
    # the composition of already-authenticated reports and live control pins.
    controls = {phase: ('exact-control.' + phase,) for phase in (*domain.COMPLETED_E4_PHASES, 'structure')}
    reports = {phase: _report(phase) for phase in domain.COMPLETED_E4_PHASES}
    reports['e4.development']['structure'] = _report('structure')
    reads = []

    class ExposedOwner:
        def __init__(self, *, service, descriptor):
            self.service, self.descriptor = service, descriptor

        def _read_phase(self, context, phase, *, execution_only, observe_controls):
            assert execution_only
            reads.append(phase)
            observe_controls(phase, controls[phase])
            if phase == 'e4.development':
                observe_controls('structure', controls['structure'])
            return reports[phase]

    @contextmanager
    def forbid_unentered(*_args, **_kwargs):
        pytest.fail('completed E4 attempted unentered adoption')
        yield

    monkeypatch.setattr(owner, '_pin_original_selection', lambda *_: lambda: None)
    monkeypatch.setattr(owner, 'retained_run_binding', lambda *_: 'exposed-original-e3-run')
    monkeypatch.setattr(owner, 'scientific_reconstruction_enabled', lambda: False)
    monkeypatch.setattr('empirical_lawhood.api.retained_e3_evidence.current_e3_evidence', lambda *_: None)
    monkeypatch.setattr('empirical_lawhood.api.recursive_execution._custody_control_pins', lambda writer, index: controls[index])
    monkeypatch.setattr('empirical_lawhood.api.matrix_programme_unentered_e4.unentered_e4_custody', forbid_unentered)
    service = _Service(metadata_case.case.writer, 'exposed-profile')
    context = _Context(service, tmp_path, dict.fromkeys(domain.COMPLETED_E4_PHASES), {}, {})
    selected = ExposedOwner(service=service, descriptor=None)
    with owner.original_completed_custody(selected, context) as retained:
        assert retained.phases == domain.COMPLETED_E4_PHASES
        assert retained.unentered_e4 is None
        assert retained.completed_e4_structure_terminal == _pin('terminal.structure', DevelopmentRunRecoveryTerminalEvent)
        assert tuple(retained.reports) == domain.COMPLETED_E4_PHASES
        assert sorted(reads) == sorted(domain.COMPLETED_E4_PHASES)
        retained.require_current()
        original = controls['structure']
        controls['structure'] = ('substituted-control',)
        with pytest.raises(PermissionError, match='original execution custody'):
            retained.require_current()
        controls['structure'] = original
    with pytest.raises(PermissionError, match='read lifetime'):
        retained.require_current()


@pytest.mark.parametrize('damage', ('none', 'acquisition', 'structure', 'missing-control', 'terminal', 'later-phase'))
def test_recorded_e4_custody_keeps_both_controls_live_through_consumer(tmp_path, monkeypatch, damage):
    report = _report('e4', DevelopmentOutputRepairTerminalEvent)
    report['structure'] = _report('structure')
    acquisition, structure = owner.completed_e4_terminals(report)
    record = SimpleNamespace(predecessor_terminals=(('e4.development', acquisition),),
        completed_e4_structure_terminal=structure, RETAINED_PHASES=domain.COMPLETED_E4_PHASES)
    context = _Context(_Service(object(), None), tmp_path, dict.fromkeys(domain.COMPLETED_E4_PHASES), {}, {})
    controls = dict(acquisition=('original-acquisition',), structure=('original-structure',))
    monkeypatch.setattr('empirical_lawhood.api.recursive_execution._custody_control_pins', lambda writer, index: controls[index])
    def read(_context, phase, *, execution_only, observe_controls):
        assert _context is context and phase == 'e4.development' and execution_only
        observe_controls('acquisition', controls['acquisition'])
        if damage != 'missing-control':
            observe_controls('structure', controls['structure'])
        return report
    selected = SimpleNamespace(_read_phase=read)
    if damage == 'terminal':
        record.completed_e4_structure_terminal = replace(structure, object_fingerprint='b' * 64)
    def consume():
        with owner.recorded_completed_e4_custody(selected, context, record) as observed:
            assert observed is report
            if damage in controls:
                controls[damage] = ('new-unexpected-attempt',)
            elif damage == 'later-phase':
                context.child_directory('e4.revision').mkdir(parents=True)
    if damage == 'none':
        consume()
    else:
        with pytest.raises(PermissionError, match='original E4|control censuses|authored successor'):
            consume()
