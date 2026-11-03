# SPDX-License-Identifier: MPL-2.0
"""Exposed arithmetic/software fixtures, never electronic or free-energy evidence."""

from decimal import Decimal as D
from dataclasses import replace
from types import SimpleNamespace as N
import pytest
from empirical_lawhood.adapters.methods.rubisco_insilico_free_energy import (
    science,
    contracts as c,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A


def test_complete_mbar_counts_and_analytic_constant_offset():
    result = science.reweighting(
        ((0.0,) * 8, (2.0,) * 8), (3, 5), tolerance=D("1e-12"), maximum_iterations=20
    )
    assert result.converged
    assert result.free_energies_reduced == pytest.approx((0, 2), abs=1e-12)
    assert result.effective_samples == pytest.approx((8, 8))
    assert result.overlap[0] == pytest.approx((3 / 8, 5 / 8))
    assert result.overlap[1] == pytest.approx((3 / 8, 5 / 8))
    assert [sum(w) for w in result.normalized_weights] == pytest.approx([1, 1])
    with pytest.raises(ValueError, match="denominator"):
        science.reweighting(
            ((0.0,) * 7, (2.0,) * 7),
            (3, 5),
            tolerance=D("1e-12"),
            maximum_iterations=20,
        )
    with pytest.raises(ValueError, match="empty"):
        science.reweighting(
            ((0.0,) * 8, (2.0,) * 8),
            (0, 8),
            tolerance=D("1e-12"),
            maximum_iterations=20,
        )


def test_mbar_nonconvergence_and_unknown_costs_remain_explicit():
    result = science.reweighting(
        ((0.0, 0.0, 1.0, 5.0), (8.0, 6.0, 0.0, 0.0)),
        (2, 2),
        tolerance=D("1e-30"),
        maximum_iterations=1,
    )
    assert not result.converged and result.iterations == 1
    assert science.retained_expense(
        (N(cpu_seconds=D(7), wall_seconds=D(9)), N(cpu_seconds=None, wall_seconds=D(3)))
    ) == {"cpu_seconds": None, "wall_seconds": D(12)}


def test_selected_window_requires_explicit_cv_atoms_and_direction():
    window = c.UmbrellaWindow(
        "window.exposed",
        "model.exposed",
        "REACTANT",
        (("c2", "gas"),),
        ("DISTANCE",),
        (D(2),),
        (D(3),),
        2,
        6,
        2,
        10,
        D(".01"),
    )
    assert window.sampling_steps // window.sample_interval == 3
    with pytest.raises(ValueError, match="identities"):
        c.UmbrellaWindow(
            "window.exposed",
            "model.exposed",
            "REACTANT",
            (("c2",),),
            ("DISTANCE",),
            (D(2),),
            (D(3),),
            2,
            6,
            2,
            10,
            D(".01"),
        )
    with pytest.raises(ValueError, match="initialization"):
        c.UmbrellaWindow(
            "window.exposed",
            "model.exposed",
            "POSTHOC",
            (("c2", "gas"),),
            ("DISTANCE",),
            (D(2),),
            (D(3),),
            2,
            6,
            2,
            10,
            D(".01"),
        )
    with pytest.raises(ValueError, match="finite"):
        replace(window, centers=(D("NaN"),))


def test_reactive_electron_census_and_engine_iteration_settings_are_explicit():
    # H2 is a deliberately exposed schema fixture, not a Rubisco chemical state.
    stock = ObjectIdentity(
        "source.exposed", "empirical-lawhood/test/source", "1.0.0", "a" * 64
    )
    state = c.ChemicalAlternative(
        "alternative.exposed",
        "chemical.exposed",
        (stock,),
        "exposed schema fixture",
        None,
        None,
        (),
        (),
        0,
        ("h1", "h2"),
        ("H", "H"),
        (("h1", "h2", D(1)),),
        (("h1", "h2", D(1)),),
        "o2",
        0,
    )
    assert replace(state, spin=2).spin == 2
    with pytest.raises(ValueError, match="electron census"):
        replace(state, formal_charge=1)
    engine = c.EngineBinding(
        "/exposed/python",
        (("/exposed/engine.py", 1, "b" * 64),),
        "EXPOSED",
        "EXPOSED",
        D("1e-8"),
        10,
        D("1e-6"),
        1,
        1,
    )
    with pytest.raises(ValueError, match="explicit integers"):
        replace(engine, scf_maximum_iterations=0)
    with pytest.raises(ValueError, match="explicit integers"):
        replace(engine, scf_maximum_iterations=True)


def test_supplementary_xyz_preserves_full_tokens_and_refuses_truncated_geometry():
    text = "Original header\nOptimized coordinates\nSyn pathway\n2\nSource state\nH 1.0000 -2.00 0.000\nS10\nH 1.0001 -2.01 0.001\n"
    assert science.supplementary_xyz_blocks(text) == (
        (
            "Syn pathway",
            "Source state",
            (("H", "1.0000", "-2.00", "0.000"), ("H", "1.0001", "-2.01", "0.001")),
        ),
    )
    with pytest.raises(ValueError, match="truncated"):
        science.supplementary_xyz_blocks(text.rsplit("H 1.0001", 1)[0])
    with pytest.raises(ValueError, match="malformed"):
        science.supplementary_xyz_blocks(text.replace("H 1.0001 -2.01 0.001", "3"))
    with pytest.raises(ValueError, match="exceeds"):
        science.supplementary_xyz_blocks(text + "H 0.0 0.0 0.0\n")


def exposed_selection():
    """Synthetic schema closure; never a supported Rubisco state or source."""
    stock = ObjectIdentity(
        "source.exposed", "empirical-lawhood/test/source", "1.0.0", "a" * 64
    )
    engine = c.EngineBinding(
        "/exposed/python",
        (("/exposed/engine.py", 1, "b" * 64),),
        "EXPOSED",
        "EXPOSED",
        D("1e-8"),
        10,
        D("1e-6"),
        1,
        1,
    )
    models = []
    for gas, spin in c.GAS_SPINS:
        tag = f"{gas}.{spin}"
        alternative = c.ChemicalAlternative(
            "alternative.exposed." + tag,
            "chemical.exposed",
            (stock,),
            "exposed H2 schema fixture",
            None,
            None,
            (),
            (),
            0,
            ("h1", "h2"),
            ("H", "H"),
            (("h1", "h2", D(1)),),
            (("h1", "h2", D(1)),),
            gas,
            spin,
        )
        models.append(
            c.ReactiveModel(
                "model.exposed." + tag,
                stock,
                stock,
                alternative,
                ("h1", "h2", "mm1"),
                ("h1", "h2"),
                ((D(0), D(0), D(0)), (D(1), D(0), D(0))),
                (("mm1", D(0), (D(3), D(0), D(0)), D(1)),),
                (),
                "EXPOSED",
                stock,
                stock,
                "FIXED_FULL_ASSEMBLY_EMBEDDING_CONDITIONAL",
            )
        )
    models = tuple(sorted(models, key=lambda x: x.model_id))
    windows = tuple(
        sorted(
            (
                c.UmbrellaWindow(
                    "window." + m.model_id + "." + direction.lower(),
                    m.model_id,
                    direction,
                    (("h1", "h2"),),
                    ("DISTANCE",),
                    (D(1),),
                    (D(3),),
                    2,
                    6,
                    2,
                    10,
                    D(".01"),
                )
                for m in models
                for direction in ("REACTANT", "PRODUCT")
            ),
            key=lambda x: x.window_id,
        )
    )
    return c.FreeEnergySelection(
        "selection.exposed",
        stock,
        stock,
        (stock,),
        ("chemical.exposed",),
        models,
        engine,
        windows,
        D(300),
        "EXPOSED",
        stock,
        stock,
        D(2),
        D(".1"),
        D(1),
        D(1),
        "/media/chevre/SEMIOS/empirical-lawhood-applied-el/20261011/reopen01/rubisco-insilico01/working/exposed-free-energy",
    )


def test_full_gas_state_census_and_negative_window_retention():
    selection = exposed_selection()
    with pytest.raises(ValueError, match="both gases"):
        replace(selection, models=selection.models[:-1])
    with pytest.raises(ValueError, match="reactive atom"):
        replace(
            selection,
            windows=(
                replace(selection.windows[0], cv_atom_ids=(("h1", "foreign"),)),
                *selection.windows[1:],
            ),
        )
    raw = selection.actual_mechanism
    traces = tuple(
        c.WindowTrace(
            "trace." + w.window_id,
            c.identity(selection),
            w,
            ((2, D(0), (D(1),)), (4, D(0), (D(1),)), (6, D(0), (D(1),))),
            9,
            9,
            A.SATISFIED,
            (),
            D(1),
            D(1),
            (raw,),
        )
        for w in selection.windows
    )
    assert science.preliminary_sampling_disposition(selection, traces) is A.SATISFIED
    negative = replace(
        traces[0],
        observations=(),
        completed_energy_calls=0,
        disposition=A.UNEVALUABLE,
        reason_codes=("EXPOSED_SCF_FAILURE",),
        cpu_seconds=None,
    )
    assert (
        science.preliminary_sampling_disposition(selection, (negative, *traces[1:]))
        is A.UNEVALUABLE
    )
    assert science.retained_expense((negative, *traces[1:]))["cpu_seconds"] is None
    for state in (A.FALSIFIED, A.UNSUPPORTED, A.NOT_ATTEMPTED):
        adverse = replace(negative, disposition=state, reason_codes=("EXPOSED_" + state.value,),
                          attempted_energy_calls=0 if state is A.NOT_ATTEMPTED else 9,
                          raw_files=() if state is A.NOT_ATTEMPTED else negative.raw_files)
        assert science.preliminary_sampling_disposition(selection, (adverse, *traces[1:])) is state
    with pytest.raises(ValueError, match="complete attempted"):
        science.complete_window_census(selection, traces[1:])
    with pytest.raises(ValueError, match="observation denominator"):
        science.complete_window_census(
            selection,
            (replace(traces[0], observations=traces[0].observations[:-1]), *traces[1:]),
        )
