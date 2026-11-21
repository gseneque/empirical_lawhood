# SPDX-License-Identifier: MPL-2.0
"""Passive telemetry at native composition boundaries, without numerical policy."""

from empirical_lawhood.execution.progress import active_progress, report_progress


def observe_native_progress(row):
    """Project already emitted native observations; never infer convergence."""
    event = row.get('event')
    if type(event) is not str:
        return
    evaluation = row.get('evaluation')
    detail = None if evaluation is None else f'Complete reference evaluation {evaluation}'
    if event == 'scf-entry':
        report_progress(phase='rubisco.scf', done=0, unit='iterations', detail=detail)
    elif event == 'scf-iteration':
        cycle = row.get('cycle')
        if type(cycle) in (int, float) and cycle >= 0 and float(cycle).is_integer():
            report_progress(phase='rubisco.scf', done=int(cycle) + 1,
                unit='iterations', detail=detail)
    elif event == 'scf-chunk-return':
        report_progress(phase='rubisco.scf', done=row.get('cumulative_cycles'),
            unit='iterations', detail=detail)
    elif event in {'accepted-minimizer-step', 'accepted-preparation-state'}:
        report_progress(phase='rubisco.geometry', done=row.get('iteration'),
            unit='accepted-iterations', detail='Convergence denominator unknown; numerical stopping criteria unchanged')
    elif event == 'relaxation-return':
        report_progress(phase='rubisco.reference-evaluations', done=evaluation,
            unit='evaluations', detail='Complete native return observed; convergence not implied')
    elif event in {'qm-gradient-entry', 'qm-gradient-return', 'embedding-gradient-return'}:
        report_progress(phase='rubisco.' + event, detail=detail)
    elif event == 'relaxation-entry':
        report_progress(phase='rubisco.reference-evaluation', detail=detail)


def progress_observer(observe):
    """Compose the original observer with advisory projection, preserving its row."""
    def emit(row):
        observe(row)
        observe_native_progress(row)
    return emit


def minimization_reporter(mm, original=None):
    """Use OpenMM's native callback without changing its stop decision.

    Native iteration numbers can reset when constraints are tightened. The
    operational counter counts observed callbacks, not a convergence fraction.
    """
    if not active_progress():
        return original

    class Reporter(mm.MinimizationReporter):
        def __init__(self):
            super().__init__()
            self.observed = 0
            report_progress(phase="rubisco.openmm-minimization", done=0, unit="iteration-callbacks",
                detail="Waiting for native iteration callback; convergence denominator unknown")

        def report(self, iteration, x, grad, args):
            self.observed += 1
            report_progress(phase='rubisco.openmm-minimization', done=self.observed,
                unit='iteration-callbacks',
                detail=f'Native iteration {iteration}; convergence denominator unknown')
            return False if original is None else original.report(iteration, x, grad, args)
    return Reporter()
