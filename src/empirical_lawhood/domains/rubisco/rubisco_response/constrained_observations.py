"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

import math


UPSTREAM_FILES = {
    'dft/ucdft.py': '647544e18b512e3ed4a40c206ead8e67429a06f1329971cf95a73ef2ebc048cc',
    'grad/ucdft.py': 'bf70efd69884c32748c3ccdb61c71ddfdf35922456c89017c53c7cfe22151549',
    'dft/rkspu.py': 'bbf154c7a060901fe88d76c6d0208b2175f947a5f309750ecb34d773672cdef1',
    'grad/rkspu.py': '24b90a730a4bf69b4f468156fbda3b0b023f3692ecd534f47fd38f0d0fbb3e00',
}


def verify_constrained_observations(rows, *, state, successful, evaluation):
    """Check the exact selected constraint census on one original force call."""
    entered = [r for r in rows if r.get('event') == 'constrained-state-entry']
    returned = [r for r in rows if r.get('event') == 'constrained-state-return']
    if (len(entered) > 1 or len(returned) > 1 or returned and not entered
            or successful and (len(entered) != 1 or len(returned) != 1)):
        raise ValueError('constrained force omits or repeats its original state construction or return')
    for row in (*entered, *returned):
        if row.get('state') != state.identity.to_document() or row.get('evaluation') != evaluation:
            raise ValueError('constrained force substitutes its original state or evaluation')
    if entered and entered[0].get('upstream') != 'GPU4PYSCF_1.8.1_CDFT_UKS_MINAO_LAGRANGE':
        raise ValueError('constrained force substitutes its selected upstream implementation')
    if returned:
        row = returned[0]
        target = [float(r.target_electrons) for r in state.solver_order]
        if (row.get('constraint_ids') != [r.constraint_id for r in state.solver_order]
                or row.get('target_electrons') != target or row.get('projection') != state.projection
                or row.get('upstream_files') != UPSTREAM_FILES
                or row.get('spin_purity_admission') != 'UNEVALUABLE'):
            raise ValueError('constrained return substitutes its complete population or interpretation contract')
        keys = ('observed_electrons', 'residual_electrons', 'lagrange_multipliers_hartree')
        for key in keys:
            values = row.get(key)
            if (type(values) is not list or len(values) != len(target)
                    or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)):
                raise ValueError('constrained return omits complete finite original diagnostics')
        residual = [a-b for a, b in zip(row['observed_electrons'], target, strict=True)]
        if residual != row['residual_electrons']:
            raise ValueError('constrained return changes its observed population residuals')
        if successful and max(abs(v) for v in residual) > float(state.population_tolerance_electrons):
            raise ValueError('successful constrained force violates the selected population tolerances')
    return dict(entered=len(entered), returned=len(returned), physical_state_admission='UNEVALUABLE')
