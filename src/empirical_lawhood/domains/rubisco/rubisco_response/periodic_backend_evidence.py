# SPDX-License-Identifier: MPL-2.0
"""Bounded original apparatus and per-force GPU observations for long traces.

Each observation has its own authenticated file. Readers retain one evaluation
at a time; the complete native log remains original custody, including failures.
"""

import json
import re

from empirical_lawhood.domains.rubisco.rubisco_response.gpu_periodic_read import verify_gpu_observations


_APPARATUS = frozenset(('compute-backend', 'openmm-platform'))
_FORCE = frozenset(('entry', 'gpu-evaluation-cost', 'gpu-cost-unavailable', 'return', 'error',
    'constrained-state-entry', 'constrained-state-return'))
_MEMBER = re.compile(r'gpu\.(?:apparatus\.(compute-backend|openmm-platform)|evaluation\.([0-9]{16})\.(entry|gpu-evaluation-cost|gpu-cost-unavailable|return|error|constrained-state-entry|constrained-state-return))\.json\Z')


def selected_gpu_member(name):
    return _MEMBER.fullmatch(name) is not None


def record_gpu_observation(directory, row, *, name_prefix=''):
    """Retain exact original selected observations before their scientific read."""
    event = row.get('event')
    if event in _APPARATUS:
        name = 'gpu.apparatus.'+event+'.json'
    elif event in _FORCE:
        number = row.get('evaluation')
        if type(number) is not int or number <= 0:
            raise ValueError('GPU observation omits its actual evaluation number')
        name = f'gpu.evaluation.{number:016d}.{event}.json'
    else:
        return
    if name_prefix:
        from empirical_lawhood.science.records.serialization import validate_stable_id
        validate_stable_id(name_prefix.rstrip('.'))
        if not name_prefix.endswith('.'):
            raise ValueError('GPU observation prefix requires an explicit separator')
    with (directory/(name_prefix+name)).open('x') as stream:
        json.dump(row, stream, sort_keys=True, allow_nan=True)
        stream.write('\n')


class GpuTraceAssessment:
    """Independently join selected apparatus, force returns and complete costs."""

    def __init__(self, engine, state=None):
        self.engine = engine
        self.state = state
        self.apparatus = []
        self.current = []
        self.number = 0
        self.groups = 0
        self.entries = 0
        self.returns = 0
        self.costs = 0
        self.failed_costs = 0
        self.unavailable_costs = 0
        self.last_failed = False
        self.device_ms = 0.

    def _flush(self):
        if not self.current:
            return
        returned = [r for r in self.current if r['event'] == 'return']
        entries = [r for r in self.current if r['event'] == 'entry']
        if (len(returned) > 1 or self.last_failed or self.number != self.groups+1
                or any(type(r.get('evaluation')) is not int or r['evaluation'] != self.number for r in self.current)):
            raise ValueError('GPU trace drops, repeats or continues an unsuccessful evaluation')
        success = bool(returned) and not any(r['event'] in ('error', 'gpu-cost-unavailable') for r in self.current)
        if len(entries) > 1 or success and len(entries) != 1:
            raise ValueError('GPU trace omits or repeats an original force entry')
        raw = b'\n'.join(json.dumps(r, sort_keys=True, allow_nan=True).encode() for r in (*self.apparatus, *self.current))
        verify_gpu_observations(raw, engine=self.engine, successful=success, evaluation=self.number)
        if self.state is not None:
            from empirical_lawhood.domains.rubisco.rubisco_response.constrained_observations import verify_constrained_observations
            verify_constrained_observations(self.current, state=self.state, successful=success, evaluation=self.number)
        elif any(r['event'].startswith('constrained-state-') for r in self.current):
            raise ValueError('unconstrained trace contains an unselected electronic constraint')
        costs = [r for r in self.current if r['event'] == 'gpu-evaluation-cost']
        if len(costs) > 1:
            raise ValueError('GPU trace repeats an original evaluation cost')
        self.groups += 1
        self.entries += len(entries)
        self.returns += len(returned)
        self.costs += len(costs)
        self.failed_costs += sum(r['failed'] for r in costs)
        self.unavailable_costs += not costs
        self.device_ms += sum(r['synchronized_device_interval_ms'] for r in costs)
        self.last_failed = not success
        self.current = []

    def consume(self, name, raw):
        match = _MEMBER.fullmatch(name)
        if match is None:
            if name.startswith('gpu.'):
                raise ValueError('GPU trace has an undeclared observation member')
            return
        if type(raw) is not bytes:
            raise ValueError('GPU trace omits a selected original observation')
        row = json.loads(raw)
        event = match[1] or match[3]
        if type(row) is not dict or row.get('event') != event:
            raise ValueError('GPU trace substitutes its original observation kind')
        if match[1]:
            if self.number or event in {r['event'] for r in self.apparatus}:
                raise ValueError('GPU trace repeats or reorders its original apparatus')
            self.apparatus.append(row)
        else:
            number = int(match[2])
            if number <= 0:
                raise ValueError('GPU trace changes its evaluation numbering')
            if number != self.number:
                self._flush()
                self.number = number
            self.current.append(row)

    def finish(self, *, successful, expected_evaluations):
        if (type(successful) is not bool or type(expected_evaluations) is not int or expected_evaluations <= 0):
            raise ValueError('GPU trace requires its exact completion status and positive evaluation denominator')
        self._flush()
        # Validate apparatus even when a native failure precedes the first call.
        raw = b'\n'.join(json.dumps(r, sort_keys=True).encode() for r in self.apparatus)
        verify_gpu_observations(raw, engine=self.engine, successful=False)
        if successful and (self.last_failed or self.groups != expected_evaluations
                or self.returns != expected_evaluations or self.costs != expected_evaluations):
            raise ValueError('successful GPU trace omits complete original force or cost observations')
        if self.groups > expected_evaluations:
            raise ValueError('GPU trace exceeds its selected evaluation denominator')
        return dict(recorded_evaluations=self.groups, recorded_entries=self.entries, complete_returns=self.returns,
            recorded_costs=self.costs, failed_costs=self.failed_costs, unavailable_costs=self.unavailable_costs,
            measured_synchronized_device_interval_ms=self.device_ms,
            summed_synchronized_device_interval_ms=None if self.unavailable_costs else self.device_ms,
            interpretation='SUMMED_FORCE_INTERVALS_NOT_CAMPAIGN_ELAPSED_TIME')


def assess_gpu_log(raw, *, engine, expected_evaluations, successful, state=None):
    """Check an already bounded original log, including every force and cost."""
    assessment = GpuTraceAssessment(engine, state=state)
    for line in raw.splitlines():
        row = json.loads(line)
        if type(row) is not dict:
            raise ValueError('GPU trace requires complete original observation objects')
        event = row.get('event')
        if event in _APPARATUS:
            name = 'gpu.apparatus.'+event+'.json'
        elif event in _FORCE:
            number = row.get('evaluation')
            if type(number) is not int or number <= 0:
                raise ValueError('GPU trace omits its original force number')
            name = f'gpu.evaluation.{number:016d}.{event}.json'
        else:
            continue
        assessment.consume(name, line)
    return assessment.finish(successful=successful, expected_evaluations=expected_evaluations)
