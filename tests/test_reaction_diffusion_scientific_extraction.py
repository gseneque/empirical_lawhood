"""Pure field balances and failed-native census; no FiPy engine is launched."""
from dataclasses import replace
from decimal import Decimal
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.simulators.fipy_reaction_diffusion_response.runtime import execute_fipy_complete_unit
from empirical_lawhood.domains.chemistry.reaction_diffusion.design import fipy_design
from empirical_lawhood.domains.chemistry.reaction_diffusion.preparation_inputs import fipy_preparation_input
from empirical_lawhood.domains.chemistry.reaction_diffusion import response
from empirical_lawhood.methods.selective_dependence_response.contracts import SelectiveDependenceResponseDisposition, SelectiveDependenceResponsePhase


@pytest.mark.numerical(oracle="Four-cell constant field: rectangular source/boundary flux and trapezoidal decay mass balance")
def test_supplied_field_balance_and_scientific_margins():
    design = replace(
        fipy_design(), maximum_balance_error=Decimal('.1'),
        maximum_boundary_flux=Decimal('1'), target_downstream_lower=Decimal('.2'),
        target_downstream_upper=Decimal('.4'), nonnegativity_tolerance=Decimal('.01'),
        maximum_peak_field=Decimal('.5'),
    )
    final = np.full(4, .3)
    balance = response.FieldBalance(initial_mass=.25)
    balance.observe(previous_mass=.25, current=final, applied=2,
                    source_region=np.array([True, True, False, False]),
                    dx=.25, diffusivity=.1, decay_rate=.2, step=.1)
    assert balance.source_integral == pytest.approx(.1)
    assert balance.decay_integral == pytest.approx(.0055)
    assert balance.boundary_outflow_integral == pytest.approx(.024)
    observed, margins = response.receiver_margins(
        design, final=final, x=np.array([.125, .375, .625, .875]),
        dx=.25, diffusivity=.1, balance=balance,
    )
    assert observed['balance-error'] == pytest.approx(.0205)
    assert observed['field-mass'] == pytest.approx(.3)
    assert observed['boundary-flux'] == pytest.approx(.24)
    assert margins == (Decimal('.0795'), Decimal('.76'), Decimal('.1'), Decimal('.31'), Decimal('.2'))


class _FakeTerm:
    def __add__(self, _other):
        return self

    __radd__ = __add__
    __sub__ = __add__
    __rsub__ = __add__
    __mul__ = __add__
    __rmul__ = __add__

    def __eq__(self, _other):
        return self

    def solve(self, **_kwargs):
        raise RuntimeError('disclosed-fake-native-solver-failure')


class _FakeField(_FakeTerm):
    def __init__(self, *, mesh, value, **_kwargs):
        self.value = np.broadcast_to(value, (mesh.nx,)).copy()

    def constrain(self, *_args):
        pass

    def updateOld(self):
        pass

    def setValue(self, value, *, where):
        self.value[where] = value


def _fake_mesh(*, nx, dx):
    return SimpleNamespace(nx=nx, cellCenters=(np.arange(nx) * dx + dx / 2,), facesRight=object())


def test_failed_native_solver_retains_complete_unevaluable_census(monkeypatch):
    fake = SimpleNamespace(Grid1D=_fake_mesh, CellVariable=_FakeField,
                           TransientTerm=lambda: _FakeTerm(),
                           DiffusionTerm=lambda **_kwargs: _FakeTerm())
    monkeypatch.setitem(sys.modules, 'fipy', fake)
    design = fipy_design()
    unit_id = 'fipy.selective-dependence-response.canary.unit-000'
    phase = SelectiveDependenceResponsePhase.CANARY
    result = execute_fipy_complete_unit(
        design, complete_unit_id=unit_id, phase=phase,
        preparation_input=fipy_preparation_input(design, unit_id, phase),
    )
    assert len(result.conditions) == 32
    assert len(result.context_decisions) == 8
    assert result.nested_conditions_count_as_units is False
    for condition in result.conditions:
        assert condition.stopped is True
        assert condition.stop_code == 'fipy-runtimeerror'
        assert condition.disposition is SelectiveDependenceResponseDisposition.UNEVALUABLE
        assert condition.fibre_admitted is None
        assert condition.gate_margins == ()
        assert tuple(r.receiver_id for r in condition.receivers) == design.receiver_ids
        assert all(not receiver.valid for receiver in condition.receivers)
    qualification, _panel = response.source_qualification(
        design, units=(result,), replay=result, observed_version=design.fipy_version,
    )
    assert qualification.source_ready is False
    assert qualification.equation_constructed is False
    assert qualification.balance_qualified is False
