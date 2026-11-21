# SPDX-License-Identifier: MPL-2.0
"""Library-boundary controls; mocked native APIs confer no engine validation."""
from decimal import Decimal as D
import math
import sys
from types import SimpleNamespace as NS

import numpy as np
import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response.library_construction import (
    amber_restart_text, authenticated_missing_residues, complete_amber_minimization, complete_constructed_heavy_atoms, conservative_rms_tolerance,
    construct_i95m_sidechains, construction_input_pdb,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import read_initial_coordinates
from tests.test_rubisco_terminal_templates import fixture


class _Platform:
    def __init__(self):
        self.properties = {"Threads": "17", "DeterministicForces": "false"}

    def getPropertyDefaultValue(self, name):
        return self.properties[name]

    def setPropertyDefaultValue(self, name, value):
        self.properties[name] = value


def _topology(rows):
    chains = []
    for index, chain_id in enumerate(dict.fromkeys(row[0] for row in rows)):
        positions = dict.fromkeys(row[1] for row in rows if row[0] == chain_id)
        residues = [NS(id=str(position), insertionCode="") for position in positions]
        chains.append(NS(id=chain_id, index=index, residues=lambda residues=residues: iter(residues)))
    return NS(chains=lambda: iter(chains))


@pytest.mark.numerical(oracle="A 3N-vector with one nonzero component saturates ||g||infinity <= sqrt(3N)*RMS(g), including every zero-mass coordinate in the denominator.")
@pytest.mark.parametrize("atoms", (1, 8, 300000))
def test_rms_selection_proves_maximum_component_bound(atoms):
    target = .7
    chosen = conservative_rms_tolerance(target, atoms)
    assert chosen*math.sqrt(3*atoms) == pytest.approx(target)
    vector = np.zeros(3*atoms); vector[-1] = target
    assert np.sqrt(np.mean(vector**2)) == pytest.approx(chosen)
    assert np.max(np.abs(vector)) == target


@pytest.mark.parametrize("maximum,atoms", ((0, 1), (float("nan"), 1), (1, 0), (1, True)))
def test_invalid_convergence_selection_refuses(maximum, atoms):
    with pytest.raises(ValueError):
        conservative_rms_tolerance(maximum, atoms)


@pytest.mark.numerical(oracle="Amber 12.7f projection has 5e-8 Angstrom maximum coordinate rounding and retains all six periodic-cell values, independently parsed as Decimal.")
def test_retained_restart_roundtrip_preserves_the_actual_published_endpoint():
    points = np.array(((-12.123456789, .234567891, 2.9), (3., 4.1, 5.2)))
    box = (35., 40., 45., 90., 90., 90.)
    text = amber_restart_text(points, box)
    checked, cell = read_initial_coordinates(text, 2, periodic=True)
    assert np.max(np.abs(np.asarray(checked, float)-points)) <= 5e-8
    assert cell == tuple(D(str(v)) for v in box)
    with pytest.raises(ValueError, match="fixed-width"):
        amber_restart_text(np.array(((1e10, 0, 0),)), box)


def test_library_completion_discards_every_constructed_proposal_and_retains_observed_anchors():
    text, origin, _ = fixture()
    raw, atoms, selected = construction_input_pdb(text, origin)
    assert len(atoms) == 16 and len(selected) == 11
    rows = heavy_pdb_rows(raw)
    assert {row[1] for row in rows} == {2}
    assert "ALA ALA ALA" in raw
    assert not any(line.startswith("CONECT") for line in raw.splitlines())


def test_missing_heavy_completion_pins_cpu_and_retains_protected_heterogens(monkeypatch):
    text, origin, _ = fixture()
    magnesium = "HETATM   17   MG  MG Z   1      80.000   0.000   0.000  1.00  0.00          MG  \n"
    text = text.replace("END\n", magnesium+"END\n")
    origin["complete_heavy_atoms"].append(dict(chain="Z", position=1, component="MG", atom="MG", element="MG",
        status="INHERITED_OBSERVED_SOURCE", source_origin={"exposed":True}))
    full = heavy_pdb_rows(text); calls = []; platform = _Platform()
    class Fixer:
        def __init__(self, *, pdbfile, platform):
            assert isinstance(platform, _Platform)
            inherited = heavy_pdb_rows(pdbfile.read())
            assert len(inherited) == 6 and inherited[-1][2] == "MG"
            self.missingTerminals = {}
            self.topology = _topology(inherited)
        def findMissingResidues(self): pytest.fail("sequence inference must not own authenticated numbering")
        def findMissingAtoms(self): calls.append("atoms")
        def addMissingAtoms(self, *, seed):
            assert seed == 97; calls.append("complete")
            assert self.missingResidues == {(0, 0): ["ALA"], (0, 1): ["ALA"]}
            assert platform.properties == {"Threads": "2", "DeterministicForces": "true"}
            atoms = [NS(index=i, name=n, residue=NS(name=r, id=str(p), chain=NS(id=c)),
                element=NS(atomic_number={"C":6,"N":7,"O":8,"MG":12}[e], symbol=e))
                for i, (c, p, r, n, e, _) in enumerate(full)]
            self.topology = NS(atoms=lambda:iter(atoms))
            self.positions = NS(value_in_unit=lambda unit:np.asarray([row[-1] for row in full], float))
    def selected(name):
        assert name == "CPU"
        return platform
    monkeypatch.setitem(sys.modules, "openmm", NS(unit=NS(angstrom=1), Platform=NS(getPlatformByName=selected)))
    monkeypatch.setitem(sys.modules, "pdbfixer", NS(PDBFixer=Fixer))
    revised, transforms, selected = complete_constructed_heavy_atoms(text, origin, seed=97, threads=2)
    assert calls == ["atoms", "complete"]
    assert revised == text and len(selected) == 11
    assert transforms[0]["platform"] == "CPU" and transforms[0]["threads"] == 2
    assert transforms[0]["protected_heavy_atoms"] == 6
    assert platform.properties == {"Threads": "17", "DeterministicForces": "false"}


def mutant_pdb():
    lines = []; serial = 0
    for index, chain in enumerate("ABCDEFGH"):
        for name, element, offset in (("N", "N", 0), ("CA", "C", 1), ("C", "C", 2), ("O", "O", 3),
                ("CB", "C", 4), ("CG", "C", 0), ("SD", "S", 0), ("CE", "C", 0)):
            serial += 1
            lines.append(f"ATOM  {serial:5d} {' '+name:<4s} MET {chain}{95:4d}    {20*index+offset:8.3f}{0:8.3f}{0:8.3f}  1.00  0.00          {element:>2s}  ")
    return "\n".join((*lines, "END"))+"\n"


@pytest.mark.parametrize("move_anchor", (False, True))
def test_all_eight_mutations_use_library_placement_and_refuse_moved_inherited_atoms(monkeypatch, move_anchor):
    calls = []; platform = _Platform()
    class Quantity:
        def __init__(self, values): self.values = values
        def value_in_unit(self, unit): return self.values
    class Fixer:
        def __init__(self, *, pdbfile, platform):
            assert isinstance(platform, _Platform)
            self.rows = list(heavy_pdb_rows(pdbfile.read()))
            assert all(row[3] not in {"CG", "SD", "CE"} for row in self.rows)
            self.missingTerminals = {}
        def applyMutations(self, changes, chain):
            calls.append((chain, changes))
            self.rows = [(c, p, "MET" if c == chain else r, n, e, xyz) for c, p, r, n, e, xyz in self.rows]
        def findMissingAtoms(self): pass
        def addMissingAtoms(self, *, seed):
            assert seed == 20261114 and self.missingResidues == {} and self.missingTerminals == {}
            for chain in "ABCDEFGH":
                cb = next(row[-1] for row in self.rows if row[0] == chain and row[3] == "CB")
                for shift, name, element in ((1, "CG", "C"), (2, "SD", "S"), (3, "CE", "C")):
                    self.rows.append((chain, 95, "MET", name, element, (cb[0], D(shift), D(0))))
            positions = np.asarray([row[-1] for row in self.rows], float)
            if move_anchor: positions[0, 0] += .01
            self.positions = Quantity(positions)
            atoms = [NS(index=i, name=n, residue=NS(name=r, id=str(p), chain=NS(id=c)),
                element=NS(atomic_number={"C":6,"N":7,"O":8,"S":16}[e], symbol=e))
                for i, (c, p, r, n, e, _) in enumerate(self.rows)]
            self.topology = NS(atoms=lambda: iter(atoms))
    monkeypatch.setitem(sys.modules, "openmm", NS(unit=NS(angstrom=1), Platform=NS(getPlatformByName=lambda n:platform)))
    monkeypatch.setitem(sys.modules, "pdbfixer", NS(PDBFixer=Fixer))
    if move_anchor:
        with pytest.raises(ValueError, match="inherited anchor"):
            construct_i95m_sidechains(mutant_pdb(), tuple("ABCDEFGH"))
    else:
        result, report = construct_i95m_sidechains(mutant_pdb(), tuple("ABCDEFGH"))
        assert report["constructed_sidechain_atom_count"] == 24
        assert report["protected_atom_count"] == 40
        before = heavy_pdb_rows(mutant_pdb()); after = heavy_pdb_rows(result)
        assert sum(a[-1] != b[-1] for a, b in zip(before, after, strict=True)) == 24
    assert calls == [(chain, ["ILE-95-MET"]) for chain in "ABCDEFGH"]


@pytest.mark.parametrize("platform_name,threads", (("CPU", 1), ("CPU", 4), ("Reference", 1)))
def test_complete_minimizer_keeps_original_force_terms_and_pins_fixed_atoms(monkeypatch, platform_name, threads):
    contexts = []; observed = {}
    class Quantity:
        def __init__(self, value): self.value = value
        def value_in_unit(self, unit): return self.value
    class System:
        def __init__(self): self.masses = [12., 1.]; self.force_terms = ("bond", "angle", "torsion", "nonbonded")
        def getNumParticles(self): return 2
        def getNumConstraints(self): return 0
        def isVirtualSite(self, i): return False
        def setParticleMass(self, i, value): self.masses[i] = value
    class Integrator:
        def __init__(self, step): self.groups = None
        def setIntegrationForceGroups(self, groups): self.groups = groups
    class Context:
        def __init__(self, system, integrator, platform, properties):
            assert platform == platform_name and integrator.groups == -1
            assert properties == ({"Threads": str(threads), "DeterministicForces": "true"} if platform == "CPU" else {})
            self.system = system; contexts.append(self)
        def setPositions(self, points): self.points = np.array(points, copy=True)
        def getState(self, **kwargs):
            return NS(getPotentialEnergy=lambda:Quantity(float(np.sum(self.points**2))),
                getForces=lambda **k:Quantity(-2*self.points), getPositions=lambda **k:Quantity(self.points.copy()))
    def minimize(context, *, tolerance, maxIterations, reporter):
        assert reporter is None
        observed.update(tolerance=tolerance, iterations=maxIterations, terms=context.system.force_terms)
        for i, mass in enumerate(context.system.masses):
            if mass: context.points[i] = 0
    unit = NS(picosecond=1., nanometer=1., kilojoule_per_mole=1.)
    module = NS(unit=unit, VerletIntegrator=Integrator, Context=Context,
        Platform=NS(getPlatformByName=lambda name:name), XmlSerializer=NS(serialize=lambda system:"original-all-terms", deserialize=lambda raw:System()),
        LocalEnergyMinimizer=NS(minimize=minimize))
    monkeypatch.setitem(sys.modules, "openmm", module)
    source = System(); coordinates = np.array(((.1, .2, .3), (.5, .4, .3)))
    final, forces, report, _, xml = complete_amber_minimization(source, coordinates, (1,), maximum_component=1., maximum_iterations=17,
        platform_name=platform_name, threads=threads)
    assert observed == {"tolerance": 1/math.sqrt(6), "iterations":17, "terms": source.force_terms}
    assert source.masses == [12., 1.] and contexts[0].system.masses == [0, 1.]
    assert np.array_equal(final[0], coordinates[0]) and np.count_nonzero(final[1]) == 0
    assert np.array_equal(forces, -2*final) and report["success"]
    assert report["maximum_mobile_gradient_kj_mol_nm"] == 0
    assert xml == "original-all-terms"
    assert report["platform"] == platform_name and report["threads"] == threads


@pytest.mark.parametrize("missing,expected", (((1,), {(0, 0): ["ALA"]}), ((2,), {(0, 1): ["ALA"]}),
    ((3,), {(0, 2): ["ALA"]}), ((), {})))
def test_repeated_sequence_completion_uses_authenticated_numbering(missing, expected):
    text, origin, _ = fixture(missing)
    raw, atoms, constructed = construction_input_pdb(text, origin)
    assert authenticated_missing_residues(_topology(heavy_pdb_rows(raw)), atoms, constructed) == expected


def test_completion_refuses_missing_observed_atoms_and_anchorless_chains():
    text, origin, _ = fixture((1,))
    raw, atoms, constructed = construction_input_pdb(text, origin)
    with pytest.raises(ValueError, match="observed atom"):
        authenticated_missing_residues(_topology(heavy_pdb_rows(raw)), atoms, ())
    with pytest.raises(ValueError, match="observed anchor"):
        authenticated_missing_residues(_topology(()), atoms, constructed)


def test_internal_library_platform_defaults_restore_after_failure(monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import library_construction as owner
    platform = _Platform()
    monkeypatch.setitem(sys.modules, "openmm", NS(Platform=NS(getPlatformByName=lambda name: platform)))
    def failed(*, seed):
        assert seed == 97 and platform.properties == {"Threads": "1", "DeterministicForces": "true"}
        raise RuntimeError("exposed native failure")
    with pytest.raises(RuntimeError, match="exposed native failure"):
        owner._add_missing_atoms(NS(addMissingAtoms=failed), seed=97, platform_name="CPU", threads=1)
    assert platform.properties == {"Threads": "17", "DeterministicForces": "false"}


@pytest.mark.parametrize("platform,threads", (("CUDA", 1), ("CPU", 0), ("CPU", True), ("CPU", 9), ("Reference", 2)))
def test_unadmitted_construction_platforms_and_threads_refuse(platform, threads):
    from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import validate_construction_platform
    with pytest.raises(ValueError, match="construction requires"):
        validate_construction_platform(platform, threads)


def test_native_thread_selection_requires_actual_cpu_capacity(monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import library_construction as owner
    monkeypatch.setitem(sys.modules, "openmm", NS())
    monkeypatch.setattr(owner.os, "sched_getaffinity", lambda pid: {7})
    with pytest.raises(ValueError, match="actual CPU affinity"):
        owner.construction_platform("CPU", 2)


@pytest.mark.native("openmm", "pdbfixer")
@pytest.mark.parametrize("missing", ((1,), (3,), ()))
def test_real_pdbfixer_completion_respects_repeated_terminal_numbering(missing, monkeypatch):
    import openmm as mm
    platform = mm.Platform.getPlatformByName("CPU")
    names = ("Threads", "DeterministicForces")
    previous = {name: platform.getPropertyDefaultValue(name) for name in names}
    context = mm.Context
    observed = []
    def create_context(*args, **kwargs):
        selected = context(*args, **kwargs)
        actual = selected.getPlatform()
        observed.append((actual.getName(), {name: actual.getPropertyValue(selected, name) for name in names}))
        return selected
    monkeypatch.setattr(mm, "Context", create_context)
    text, origin, _ = fixture(missing)
    revised, report, constructed = complete_constructed_heavy_atoms(text, origin, seed=97)
    before, after = heavy_pdb_rows(text), heavy_pdb_rows(revised)
    assert [row[:5] for row in before] == [row[:5] for row in after]
    assert all(a[-1] == b[-1] for a, b in zip(before, after, strict=True) if (a[0], a[1], a[3]) not in constructed)
    assert report[0]["platform"] == "CPU" and report[0]["threads"] == 1
    assert {name: platform.getPropertyDefaultValue(name) for name in names} == previous
    if missing:
        assert observed and all(row == ("CPU", {"Threads": "1", "DeterministicForces": "true"}) for row in observed)


@pytest.mark.native("openmm")
@pytest.mark.numerical(oracle="Two-particle harmonic bond E=k(r-r0)^2/2 has equilibrium distance r0=0.109 nm and zero energy; the fixed anchor is exact, and Reference is restricted to this two-particle system.")
def test_real_optimized_cpu_minimizer_matches_small_harmonic_oracle():
    import openmm as mm
    system = mm.System()
    system.addParticle(12); system.addParticle(1)
    bond = mm.HarmonicBondForce(); bond.addBond(0, 1, .109, 1000)
    system.addForce(bond)
    points = np.array(((0., 0., 0.), (.2, 0., 0.)))
    results = []
    for platform, threads in (("CPU", 1), ("CPU", 2), ("Reference", 1)):
        final, forces, report, _, _ = complete_amber_minimization(system, points, (1,),
            maximum_component=1e-6, maximum_iterations=100, platform_name=platform, threads=threads)
        assert np.array_equal(final[0], points[0])
        assert abs(np.linalg.norm(final[1]-final[0])-.109) < 1e-10 and np.max(np.abs(forces)) < 1e-6
        assert report["energy_kj_mol"] < 1e-12
        assert report["success"] and report["platform"] == platform and report["threads"] == threads
        results.append(final)
    assert np.max(np.abs(results[0]-results[-1])) < 1e-10


@pytest.mark.native("openmm")
@pytest.mark.numerical(oracle="Eight-particle periodic PME with explicit grid, charges, LJ, bond, angle and torsion terms is compared to serial OpenMM Reference at the same coordinates. Bounds cover only this exposed implementation control.")
def test_small_periodic_cpu_force_difference_from_reference():
    import openmm as mm
    from empirical_lawhood.adapters.rubisco.rubisco_response.library_construction import evaluate_complete_amber
    system = mm.System()
    nonbonded = mm.NonbondedForce()
    nonbonded.setNonbondedMethod(mm.NonbondedForce.PME)
    nonbonded.setCutoffDistance(1.)
    nonbonded.setPMEParameters(3., 32, 32, 32)
    system.setDefaultPeriodicBoxVectors(mm.Vec3(4, 0, 0), mm.Vec3(0, 4, 0), mm.Vec3(0, 0, 4))
    for index in range(8):
        system.addParticle(12)
        nonbonded.addParticle(-.2 if index % 2 else .2, .3, .2)
    system.addForce(nonbonded)
    bond = mm.HarmonicBondForce(); bond.addBond(0, 1, .36, 800); system.addForce(bond)
    angle = mm.HarmonicAngleForce(); angle.addAngle(0, 1, 2, 1.8, 50); system.addForce(angle)
    torsion = mm.PeriodicTorsionForce(); torsion.addTorsion(0, 1, 2, 3, 3, .2, 1.3); system.addForce(torsion)
    points = np.array(((.3, .4, .5), (.65, .44, .55), (.91, .72, .52), (1.12, .86, .83),
        (1.7, 1.1, .6), (2., 1.8, 1.1), (2.2, 2.2, 1.8), (2.8, 2.6, 2.3)))
    energy, forces = evaluate_complete_amber(system, points, platform_name="Reference")
    for threads in (1, 2):
        actual_energy, actual_forces = evaluate_complete_amber(system, points, platform_name="CPU", threads=threads)
        assert abs(actual_energy-energy) < 1e-5
        assert np.max(np.abs(actual_forces-forces)) < 1e-4
