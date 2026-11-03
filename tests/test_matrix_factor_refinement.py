"""Independent weighted-OU bridge controls without retired response wrappers."""

from decimal import Decimal as D
from types import SimpleNamespace
import numpy as np
import pytest
from empirical_lawhood.adapters.methods.matrix_factor_response import refinement


def test_weighted_ou_bridge_exact_coupling_and_orthogonal_normal_transform():
    from empirical_lawhood.adapters.methods.matrix_factor_response.independent import noise_panel
    coarse = noise_panel(SimpleNamespace(seed=40),3)
    bridge = noise_panel(SimpleNamespace(seed=41),3)
    fine = refinement.weighted_ou_bridge(coarse,bridge,friction=D(1),coarse_timestep=D('.001'))
    a = np.exp(-.0005)
    transform = np.asarray(((a,1),(1,-a)))/np.sqrt(1+a*a)
    np.testing.assert_allclose(transform@transform.T,np.eye(2),atol=2e-16)
    np.testing.assert_allclose(a*fine[0::2]+fine[1::2],np.sqrt(1+a*a)*coarse,atol=2e-15)
    np.testing.assert_allclose((fine[0::2]**2+fine[1::2]**2).sum(),(coarse**2+bridge**2).sum(),atol=1e-12)
    with pytest.raises(ValueError,match='full finite Hermitian'):
        refinement.weighted_ou_bridge(coarse,bridge.real,friction=1,coarse_timestep=.001)
