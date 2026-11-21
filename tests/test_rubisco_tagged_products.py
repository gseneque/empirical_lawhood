# SPDX-License-Identifier: MPL-2.0
"""Controls for the structural product assay and its finite-panel crossing measure."""

from dataclasses import replace
from decimal import Decimal
import math

import numpy as np
import pytest

from empirical_lawhood.api.domain_composition.rubisco_response.tagged_products import (
    assess_tagged_flux_panel, read_oxygen_bound_products,
)
from empirical_lawhood.domains.rubisco.rubisco_response.bound_products import bound_products
from empirical_lawhood.domains.rubisco.rubisco_response.val1_flux import (
    VAL1_MEASURE, incoming_velocity, log_insertion, poses,
)


def draw(state, *, volume=0.25, speed=1, bulk=0, surface=0):
    return dict(transmission=state, log_bulk=bulk, log_surface=surface, bulk_volume_fraction=volume,
                maxwell_mean_positive_nm_ps=speed)


@pytest.mark.numerical(oracle="spherical area times inward speed, reference bath density and exact SI Avogadro constant")
def test_tagged_flux_bounds_and_natural_units():
    rows = {"c": draw("ZERO"), "b": draw("UNRESOLVED", volume=Decimal("0.5"), speed=2, surface=math.log(2)),
            "a": draw("PRODUCT", volume=Decimal("0.25"), bulk=math.log(2))}
    assessment = assess_tagged_flux_panel(assigned_ids=("a","b","c"), trials=rows, measure=VAL1_MEASURE)
    interval = assessment["interval"]
    factor = 4 * math.pi * 4**2 * 0.01 * 6.02214076e11
    # Bulk density is the free-volume weighted mean of the three relative bulk weights.
    baseline = (0.25 * 2 + 0.5 + 0.25) / (0.25 + 0.5 + 0.25)
    assert math.exp(interval["log_lower"]) == pytest.approx(factor / (3 * baseline))
    assert math.exp(interval["log_upper"]) == pytest.approx(5 * factor / (3 * baseline))
    assert interval["unresolved_surface_weight"] == pytest.approx(0.5)
    assert interval["assigned_draws"] == 3 and assessment["assigned_ids"] == ("a","b","c")
    assert interval["transmission_census"] == {"PRODUCT":1,"UNRESOLVED":1,"ZERO":1,"unmeasured":0}
    second = assess_tagged_flux_panel(assigned_ids=("a","b","c"), trials=rows,
                                      measure=replace(VAL1_MEASURE, radius_angstrom=Decimal("8")))
    assert second["interval"]["log_upper"] - interval["log_upper"] == pytest.approx(math.log(4))


def test_assigned_draws_retain_unbounded_missing_and_observed_zero():
    rows = {"a": None, "b": draw("ZERO")}
    censored = assess_tagged_flux_panel(assigned_ids=("b","a"), trials=rows, measure=VAL1_MEASURE)
    assert censored["nonentered_ids"] == ("a",)
    assert censored["interval"]["upper_unbounded"]
    assert censored["interval"]["transmission_census"]["unmeasured"] == 1
    zero = assess_tagged_flux_panel(assigned_ids=("b",), trials={"b": rows["b"]}, measure=VAL1_MEASURE)["interval"]
    assert zero["zero_lower"] and zero["zero_upper"] and not zero["upper_unbounded"]
    for ids in (("a",), ("a","b","a"), ("a","b","c"), ()):
        with pytest.raises(ValueError):
            assess_tagged_flux_panel(assigned_ids=ids, trials=rows, measure=VAL1_MEASURE)


@pytest.mark.parametrize("back,forward,expected", [
    ("BULK","PRODUCT","PRODUCT"), ("BULK","BULK","ZERO"), ("RECROSS","PRODUCT","ZERO"),
    ("HORIZON","PRODUCT","UNRESOLVED"), ("BULK","WATER_PARTITION_UNRESOLVED","UNRESOLVED"),
    ("DISSOCIATED_ELECTRONIC_STATE_UNRESOLVED","BULK","ZERO"), (None,"PRODUCT","UNRESOLVED"),
])
def test_flux_reader_reconstructs_original_paired_path_disposition(back, forward, expected):
    row = draw(expected)
    row.update(back={"outcome":back} if back else None, forward={"outcome":forward})
    del row["transmission"]
    panel = assess_tagged_flux_panel(assigned_ids=("draw",), trials={"draw": row}, measure=VAL1_MEASURE)
    assert panel["interval"]["transmission_census"][expected] == 1
    with pytest.raises(ValueError, match="original pair"):
        assess_tagged_flux_panel(assigned_ids=("draw",), trials={"draw": {**row, "transmission":"wrong"}}, measure=VAL1_MEASURE)


@pytest.mark.parametrize("field,bad", [
    ("bulk_volume_fraction",0), ("bulk_volume_fraction",1.1), ("log_bulk",float("nan")),
    ("maxwell_mean_positive_nm_ps",-1), ("log_surface",True), ("transmission","OTHER"), ("transmission",None),
])
def test_panel_rejects_invalid_weight_or_status(field,bad):
    row = draw("PRODUCT")
    row[field] = bad
    with pytest.raises(ValueError):
        assess_tagged_flux_panel(assigned_ids=("a",), trials={"a":row}, measure=VAL1_MEASURE)


@pytest.mark.parametrize("gas,atoms", [("O2",2),("CO2",3)])
@pytest.mark.numerical(oracle="sphere radius, positive mixture support and mass-weighted Maxwell momentum conservation")
def test_actual_surface_and_volume_proposals_and_mass_flux(gas,atoms):
    x = np.array([[0.,0.,0.], [1.,0.,0.]])
    args = x,np.full(3,110.),[0,1],[0,1],0,gas
    surface,s = poses(*args,np.random.default_rng(10),bulk=False,trials=64)
    bulk,b = poses(*args,np.random.default_rng(11),bulk=True,trials=64)
    assert surface.shape == bulk.shape == (atoms,3)
    assert np.linalg.norm(surface[0]) == pytest.approx(4)
    assert min(np.linalg.norm(bulk[0]-x,axis=1)) > 8 and np.linalg.norm(bulk[0]) < 48
    for obs in (s,b):
        assert obs["selection_probability"] >= 0.01 / obs["eligible"]
        assert 0 < obs["eligible"] <= 64 and math.isfinite(obs["log_measure"])
    m = np.array([12.,16.,1.])
    rt = 0.00831446261815324 * 298.15
    normal = np.array([0.,1.,0.])
    thermal = np.random.default_rng(19).normal(size=(3,3)) * np.sqrt(rt / m)[:,None]
    velocity,speed,mean = incoming_velocity(m,0,1,normal,np.random.default_rng(19))
    assert (velocity[1]-velocity[0]) @ normal == pytest.approx(-speed)
    np.testing.assert_allclose(m @ velocity, m @ thermal,rtol=1e-9)
    assert mean == pytest.approx(math.sqrt(rt*(1/12+1/16)/(2*math.pi)))
    assert log_insertion(1.25,-2.,-2.125,2625.5) == pytest.approx(1.25-0.125*2625.5/rt)


def test_selected_physical_geometry_and_pinned_reference():
    with pytest.raises(ValueError):
        replace(VAL1_MEASURE,radius_angstrom=Decimal("1e-1000"))
    with pytest.raises(ValueError):
        log_insertion(0.,0.,1.,True)
    with pytest.raises(ValueError):
        incoming_velocity([12.,0],0,1,[1.,0,0],np.random.default_rng(2))
    els = ("P","P","C","C","C","O","O")
    xyz = np.arange(21,dtype=float).reshape(7,3)
    assert bound_products(els,xyz,(0,1),(4,5,6),(2,3),singlet=False) is None
    assert bound_products(els,xyz,(0,1),(2,5,6),(2,3),singlet=True) is None
    for gas in ((4,6,6),(4,5,True)):
        with pytest.raises(ValueError):
            bound_products(els,xyz,(0,1),gas,(2,3),singlet=True)
    xyz[0,0]=np.nan
    with pytest.raises(ValueError):
        bound_products(els,xyz,(0,1),(4,5,6),(2,3),singlet=False)
    with pytest.raises(ValueError):
        read_oxygen_bound_products(original_pdf=b"wrong reference",extracted_text=b"other atoms")
