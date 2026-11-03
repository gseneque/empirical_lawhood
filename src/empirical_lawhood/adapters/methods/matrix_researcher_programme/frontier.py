# SPDX-License-Identifier: MPL-2.0
"""Finite Matrix eligibility over authenticated ordinary owner observations.

These transient values are not receipts, scientific outcomes or entry authority.
The API constructs observations only after the selected child owner's read.
"""
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping


# Internal operations, not an operator-authored component roster. Structural
# assessment is part of the three ordinary E4 result owners.
PHASES = ('e1', 'e2', 'train', 'e3', 'e4.development', 'e4.revision',
    'e4.source-cal', 'e4.calibration', 'e4.source-conf', 'e4.confirmation',
    'e5.initialize-development', 'e5.development', 'e5.initialize-confirmation',
    'e5.source', 'e5.confirmation', 'e6.initialize', 'e6.source', 'e6')
METADATA_PHASES = ('e5.initialize-development', 'e5.initialize-confirmation', 'e6.initialize')
_E5_CONFIRMATION = ('e5.initialize-confirmation', 'e5.source', 'e5.confirmation')
_PREPARED_PHASES = tuple(phase for phase in PHASES if phase.startswith(('e5.', 'e6')))
_NOMINATION_DISPOSITIONS = ('NOMINATED', 'NONDISCRIMINATING_OPPORTUNITY', 'UNEVALUABLE_OPPORTUNITY')
_PARENTS = {
    'e1': (), 'e2': (), 'train': (), 'e3': ('train',),
    'e4.development': ('e3',), 'e4.revision': ('e4.development',),
    'e4.source-cal': ('e3', 'e4.revision'),
    'e4.calibration': ('e4.source-cal', 'e4.revision'),
    'e4.source-conf': ('e3', 'e4.revision'),
    'e4.confirmation': ('e4.source-conf', 'e4.revision'),
    'e5.initialize-development': ('e3', 'e4.confirmation'),
    'e5.development': ('e5.initialize-development',),
    'e5.initialize-confirmation': ('e5.development',),
    'e5.source': ('e3', 'e4.confirmation', 'e5.development', 'e5.initialize-confirmation'),
    'e5.confirmation': ('e5.source', 'e5.development'),
    'e6.initialize': ('e3', 'e4.confirmation'),
    'e6.source': ('e3', 'e4.confirmation', 'e5.development', 'e6.initialize'),
    'e6': ('e6.source', 'e3', 'e4.confirmation'),
}


@dataclass(frozen=True, slots=True)
class MatrixProgrammeObservation:
    phase: str
    report: Mapping
    complete: bool
    revision_trigger: str | None = None
    nomination_disposition: str | None = None
    downstream_choice: str | None = None
    execution_complete: bool = False

    def __post_init__(self):
        if (self.phase not in PHASES or not isinstance(self.report, Mapping)
                or type(self.complete) is not bool or type(self.execution_complete) is not bool):
            raise TypeError('Matrix observation requires an actual phase and ordinary owner report')
        if self.execution_complete and self.phase in METADATA_PHASES:
            raise ValueError('metadata-only phases have no native execution completion')
        completed = self.complete or self.execution_complete
        if self.revision_trigger is not None and (self.phase != 'e4.revision' or not completed
                or self.revision_trigger not in ('TRIGGERED', 'NOT_TRIGGERED', 'UNEVALUABLE', 'FIT_AVAILABLE', 'FIT_UNAVAILABLE')):
            raise ValueError('conditional CAL requires the authenticated complete actual DEV revision decision')
        if self.nomination_disposition is not None and (self.phase != 'e5.development' or not completed
                or self.nomination_disposition not in _NOMINATION_DISPOSITIONS):
            raise ValueError('conditional CONF requires the authenticated complete actual E5 nomination')
        if self.downstream_choice is not None and (self.phase != 'e4.confirmation' or not completed
                or self.downstream_choice not in ('REVISION', 'ORIGINAL_E3', 'UNSELECTED')):
            raise ValueError('prepared account requires the authenticated complete actual E4 downstream decision')
        object.__setattr__(self, 'report', MappingProxyType(dict(self.report)))


@dataclass(frozen=True, slots=True)
class MatrixProgrammeFrontier:
    eligible: tuple[str, ...]
    unentered: tuple[tuple[str, str], ...]
    waiting: tuple[tuple[str, tuple[str, ...]], ...]
    complete: bool


def programme_frontier(observations, *, downstream_account, operational=False):
    """Compute eligibility without filesystem reads, new selections or effects.

    An adverse completed result satisfies ancestry. Unknown/refused/incomplete
    custody does not. E6 has no dependency on E5 confirmation or its success.
    """
    if type(operational) is not bool:
        raise TypeError('Matrix frontier requires an explicit operational/scientific scope')
    if downstream_account not in ('ORIGINAL_E3', 'REVISION'):
        raise ValueError('Matrix frontier requires its exact frozen D downstream account')
    if (not isinstance(observations, Mapping) or any(name not in PHASES
            or type(value) is not MatrixProgrammeObservation or value.phase != name
            for name, value in observations.items())):
        raise TypeError('Matrix frontier requires distinct exact typed current phase observations')
    completed = {name for name, value in observations.items()
        if value.complete or operational and value.execution_complete}
    revision = observations.get('e4.revision')
    trigger = None if revision is None else revision.revision_trigger
    bypass = trigger in ('NOT_TRIGGERED', 'UNEVALUABLE')
    skipped = {} if not bypass else {phase: 'UNENTERED_REVISION_' + trigger
        for phase in ('e4.source-cal', 'e4.calibration')}
    if trigger == 'FIT_UNAVAILABLE':
        skipped.update((phase, 'UNENTERED_REQUIRED_SR_BR_FIT_UNAVAILABLE') for phase in
            ('e4.source-cal', 'e4.calibration', 'e4.source-conf', 'e4.confirmation', *_PREPARED_PHASES))
    confirmation = observations.get('e4.confirmation')
    choice = None if confirmation is None else confirmation.downstream_choice
    if (bypass or trigger == 'FIT_UNAVAILABLE') and choice == 'REVISION':
        raise ValueError('downstream revision package contradicts its authenticated original nonentry decision')
    if downstream_account == 'REVISION' and (bypass or choice in ('ORIGINAL_E3', 'UNSELECTED')):
        reason = 'UNENTERED_REVISION_' + (trigger if bypass else 'PACKAGE_' + choice)
        skipped.update((phase, reason) for phase in _PREPARED_PHASES)
    development = observations.get('e5.development')
    nomination = None if development is None else development.nomination_disposition
    if nomination in ('NONDISCRIMINATING_OPPORTUNITY', 'UNEVALUABLE_OPPORTUNITY'):
        for phase in _E5_CONFIRMATION:
            skipped.setdefault(phase, 'UNENTERED_E5_' + nomination)
    for phase in skipped:
        observed = observations.get(phase)
        if observed is not None and (observed.complete or observed.execution_complete or _has_contact_facts(observed.report)):
            raise ValueError('conditional nonentry conflicts with retained phase completion or native custody: ' + phase)
    eligible, waiting = [], []
    for phase in PHASES:
        if phase in completed or phase in skipped:
            continue
        parents = _PARENTS[phase]
        if phase in ('e4.source-conf', 'e4.confirmation') and trigger in ('TRIGGERED', 'FIT_AVAILABLE'):
            parents = (*parents, 'e4.calibration')
        missing = tuple(parent for parent in parents if parent not in completed)
        if downstream_account == 'REVISION' and phase in _PREPARED_PHASES and choice != 'REVISION':
            missing = (*missing, 'e4.confirmation.authenticated-revision-package')
        if phase in _E5_CONFIRMATION and nomination is None:
            missing = (*missing, 'e5.development.authenticated-nomination')
        if phase.startswith(('e4.source-', 'e4.calibration', 'e4.confirmation')) and trigger is None:
            missing = (*missing, 'e4.revision.authenticated-decision')
        if missing:
            waiting.append((phase, tuple(dict.fromkeys(missing))))
        else:
            eligible.append(phase)
    return MatrixProgrammeFrontier(tuple(eligible), tuple((phase, skipped[phase]) for phase in PHASES if phase in skipped), tuple(waiting),
        all(phase in completed or phase in skipped for phase in PHASES))


def _has_contact_facts(report):
    """An observed original native attempt cannot be rewritten as unentered.

    Even a parent with only uncontacted child definitions may still be running.
    This is an obstruction, not a claim that an effect or completion happened.
    """
    return bool(report.get('native_observation_unavailable') or report.get('current_native_facts')
        or report.get('operational_terminal') == 'AUTHENTICATED'
        or (report.get('read_scope') == 'EXECUTION_RECORDS' and report.get('status') == 'INCOMPLETE'
            and report.get('recovery_index') is not None)
        or any(row.get('attempt_id') is not None or row.get('receipt_id') is not None
            for row in report.get('operational_census', ()) if isinstance(row, Mapping)))
