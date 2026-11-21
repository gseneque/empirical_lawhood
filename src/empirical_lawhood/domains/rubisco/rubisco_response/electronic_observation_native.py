# SPDX-License-Identifier: MPL-2.0
"""Original same-frame electronic points inside the existing equilibrium call."""

from hashlib import sha256
import json
from pathlib import Path
import traceback
import time

from empirical_lawhood.adapters.rubisco.rubisco_response.constrained_electronic_native import record_constrained_state
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import ARRAY_KEYS
from empirical_lawhood.adapters.rubisco.rubisco_response.periodic_trajectory_native import _array, _json


def state_prefix(prototype, ordinal):
    return f'sample.{ordinal:016d}.state.'+prototype.electronic.state.state_id+'.'


def point_name(ordinal, state_id):
    return f'sample.{ordinal:016d}.state.{state_id}.json'


class ElectronicSampleRecorder:
    """No separate scheduler, retry or checkpoint authority is introduced.

    Auxiliary failures remain observations in the complete sample population;
    they are not silently removed or replayed. The parent native call owns
    total costs, UNKNOWN contact and original archive custody.
    """
    def __init__(self, *, selection, prototype, directory, operator_factory):
        self.selection, self.prototype = selection, prototype
        self.root, self.factory = Path(directory), operator_factory
        self.samples, self.points, self.failed = 0, 0, 0
        self.current_ordinal = None

    def capture_for(self, prototype):
        def capture(mf, gpu, number, diagnostics):
            ordinal = (self.selection.settings.sample_ordinal(number-1)
                if prototype == self.prototype else self.current_ordinal)
            if ordinal is not None:
                record_constrained_state(self.root, mf=mf, gpu=gpu,
                    state=prototype.electronic.state, evaluation=number, diagnostics=diagnostics,
                    name_prefix=state_prefix(prototype, ordinal))
        return capture

    def observe_sample(self, frame):
        ordinal = frame['sample_ordinal']
        if ordinal is None:
            return
        if ordinal != self.samples+1:
            raise ValueError('electronic observation changes the complete original sample clock')
        self.samples += 1
        self.current_ordinal = ordinal
        for prototype in self.selection.observations.prototypes:
            state = prototype.electronic.state
            primary = prototype == self.prototype
            evaluation = frame['evaluation'] if primary else 1
            point = dict(sample_ordinal=ordinal, sample_step=frame['step'],
                sampled_prototype=self.prototype.identity.to_document(),
                observed_prototype=prototype.identity.to_document(), state=state.identity.to_document(),
                coordinate_sha256=sha256(frame['coordinates_angstrom'].tobytes()).hexdigest(),
                evaluation=evaluation, primary=primary, energy_hartree=None, error=None,
                auxiliary_elapsed_seconds=None)
            if primary:
                point['energy_hartree'] = frame['reference_energy_hartree']
            else:
                started = time.perf_counter()
                try:
                    prefix = state_prefix(prototype, ordinal)
                    with (self.root/(prefix+'native-observations.jsonl')).open('x', buffering=1) as log:
                        def observe(row):
                            from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import record_gpu_observation
                            log.write(json.dumps(row, sort_keys=True, allow_nan=True)+'\n')
                            record_gpu_observation(self.root, row, name_prefix=prefix)
                        # A failed vertical point cannot poison a later point's
                        # mutable operator. Every assigned point is cold and
                        # records its own complete construction/force cost.
                        operator = self.factory(prototype, observe, self.capture_for(prototype))
                        try:
                            returned = operator.evaluate(frame['coordinates_angstrom'])
                            if operator.evaluations != 1:
                                raise ValueError('electronic observation changes its single original evaluation')
                        finally:
                            del operator
                    prefix += f'evaluation.{evaluation:016d}.'
                    for name in ('energy_hartree', *ARRAY_KEYS):
                        if name in returned:
                            _array(self.root/(prefix+name+'.npy'), returned[name])
                    _json(self.root/(prefix+'native-return.json'),
                        {k:v for k, v in returned.items() if k not in ARRAY_KEYS}, diagnostic=True)
                    point['energy_hartree'] = returned['energy_hartree']
                except Exception:
                    # The successful equilibrium sample remains in its original
                    # population. This failed vertical point remains missing.
                    point['error'] = traceback.format_exc()
                    self.failed += 1
                finally:
                    point['auxiliary_elapsed_seconds'] = time.perf_counter()-started
            _json(self.root/point_name(ordinal, state.state_id), point, diagnostic=True)
            self.points += 1

    def summary(self):
        return dict(original_samples=self.samples, assigned_electronic_points=self.points,
            failed_electronic_points=self.failed, selected_state_count=len(self.selection.observations.prototypes),
            source='EVERY_ORIGINAL_SAMPLED_CONFIGURATION_WITHOUT_SUCCESS_SUBSET')

    def close(self):
        self.current_ordinal = None
