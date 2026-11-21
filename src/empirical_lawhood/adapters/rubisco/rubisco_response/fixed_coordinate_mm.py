# SPDX-License-Identifier: MPL-2.0
"""Exact variable part of a nonperiodic Amber potential with fixed coordinates.

Construction repair keeps the full molecular environment. Terms involving only
fixed atoms are constants and are omitted. Every term involving a movable atom,
including its interactions with all fixed atoms and native 1-4 exceptions, is
retained. This is a preparation potential, not the selected periodic QM/MM rate
supplier. Native imports remain inside the explicitly invoked builder.
"""

import math


from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import COULOMB_KJ_NM_PER_MOL_E2


def mobile_amber_system(original, movable):
    """Retain the exact coordinate-dependent part of an unconstrained MM System.

    Refuse unimplemented forces, constraints, virtual sites, parameter offsets
    and periodic electrostatics. Particle order, natural masses and coefficients
    survive unchanged; the optimizer, rather than particle masses, fixes atoms.
    """
    import openmm as mm
    from openmm import unit

    movable = tuple(movable)
    count = original.getNumParticles()
    if (not movable or movable != tuple(sorted(set(movable)))
            or any(type(i) is not int or not 0 <= i < count for i in movable)
            or original.getNumConstraints() or original.usesPeriodicBoundaryConditions()
            or any(original.isVirtualSite(i) for i in range(count))):
        raise ValueError("fixed-coordinate MM needs a complete unambiguous unconstrained nonperiodic atom selection")
    moving = set(movable)
    result = mm.System()
    for i in range(count):
        result.addParticle(original.getParticleMass(i))
    census = []
    nonbonded_count = 0
    for source in original.getForces():
        kind = type(source)
        if kind in (mm.HarmonicBondForce, mm.HarmonicAngleForce, mm.PeriodicTorsionForce):
            if source.usesPeriodicBoundaryConditions():
                raise ValueError("fixed-coordinate MM refuses periodic bonded terms")
            target = kind()
            target.setName(source.getName())
            if kind is mm.HarmonicBondForce:
                size, getter, adder, atoms = source.getNumBonds(), source.getBondParameters, target.addBond, 2
            elif kind is mm.HarmonicAngleForce:
                size, getter, adder, atoms = source.getNumAngles(), source.getAngleParameters, target.addAngle, 3
            else:
                size, getter, adder, atoms = source.getNumTorsions(), source.getTorsionParameters, target.addTorsion, 4
            kept = 0
            for i in range(size):
                row = getter(i)
                if moving.intersection(row[:atoms]):
                    adder(*row)
                    kept += 1
            result.addForce(target)
            census.append((kind.__name__, size, kept))
        elif kind is mm.NonbondedForce:
            nonbonded_count += 1
            if (source.getNonbondedMethod() != mm.NonbondedForce.NoCutoff
                    or source.getNumParticles() != count or source.getNumParticleParameterOffsets()
                    or source.getNumExceptionParameterOffsets() or source.getNumGlobalParameters()
                    or source.getExceptionsUsePeriodicBoundaryConditions()):
                raise ValueError("fixed-coordinate MM refuses unsupported nonbonded semantics")
            expression = (f"{COULOMB_KJ_NM_PER_MOL_E2!r}*q1*q2/r+4*epsilon*((sigma/r)^12-(sigma/r)^6);"
                          "sigma=(sigma1+sigma2)/2;epsilon=sqrt(epsilon1*epsilon2)")
            target = mm.CustomNonbondedForce(expression)
            for name in ("q", "sigma", "epsilon"):
                target.addPerParticleParameter(name)
            target.setNonbondedMethod(mm.CustomNonbondedForce.NoCutoff)
            target.setUseLongRangeCorrection(False)
            for i in range(count):
                q,sigma,epsilon = source.getParticleParameters(i)
                target.addParticle((q.value_in_unit(unit.elementary_charge),sigma.value_in_unit(unit.nanometer),
                                    epsilon.value_in_unit(unit.kilojoule_per_mole)))
            target.addInteractionGroup(moving, set(range(count)))
            exceptions = mm.CustomBondForce(f"{COULOMB_KJ_NM_PER_MOL_E2!r}*qprod/r+4*epsilon*((sigma/r)^12-(sigma/r)^6)")
            for name in ("qprod", "sigma", "epsilon"):
                exceptions.addPerBondParameter(name)
            kept = 0
            for i in range(source.getNumExceptions()):
                a,b,qprod,sigma,epsilon = source.getExceptionParameters(i)
                target.addExclusion(a,b)
                if moving.intersection((a,b)):
                    kept += 1
                    q = qprod.value_in_unit(unit.elementary_charge**2)
                    e = epsilon.value_in_unit(unit.kilojoule_per_mole)
                    if q != 0 or e != 0:
                        exceptions.addBond(a,b,(q,sigma.value_in_unit(unit.nanometer),e))
            result.addForce(target)
            result.addForce(exceptions)
            census.extend((("NonbondedForce-particles",count,count),
                           ("NonbondedForce-exceptions",source.getNumExceptions(),kept)))
        elif kind is mm.CMMotionRemover:
            census.append(("CMMotionRemover-no-coordinate-energy",1,0))
        else:
            raise ValueError("fixed-coordinate MM has no assessed mapping for " + kind.__name__)
    if nonbonded_count != 1:
        raise ValueError("fixed-coordinate MM requires exactly one complete Amber nonbonded force")
    return result, tuple(census)


class FixedCoordinateObjective:
    """Expose only selected Cartesian coordinates to an optimizer.

    The native Context always receives the complete coordinate array. Fixed
    entries are copied from the immutable original on every evaluation.
    """
    def __init__(self, context, coordinates_nm, movable, observer=None, nonbonded=None):
        import numpy as np
        self.coordinates = np.asarray(coordinates_nm,dtype=float).copy()
        self.movable = tuple(movable)
        if (self.coordinates.ndim != 2 or self.coordinates.shape[1] != 3
                or not np.isfinite(self.coordinates).all() or not self.movable
                or context.getSystem().getNumParticles() != len(self.coordinates)
                or self.movable != tuple(sorted(set(self.movable)))
                or any(type(i) is not int or not 0 <= i < len(self.coordinates) for i in self.movable)):
            raise ValueError("fixed-coordinate objective requires complete finite coordinates and unique selected atoms")
        self.coordinates.setflags(write=False)
        self.context, self.observer, self.evaluations = context, observer, 0
        self.nonbonded = nonbonded

    def complete_coordinates(self, values):
        import numpy as np
        selected = np.asarray(values,dtype=float)
        if selected.size != 3*len(self.movable) or not np.isfinite(selected).all():
            raise ValueError("fixed-coordinate objective lost its selected finite Cartesian coordinates")
        coordinates = self.coordinates.copy()
        coordinates[list(self.movable)] = selected.reshape((-1,3))
        return coordinates

    def __call__(self, values, *, original_potential=False):
        import numpy as np
        from openmm import unit
        coordinates = self.complete_coordinates(values)
        self.context.setPositions(coordinates*unit.nanometer)
        arguments = {"groups":1} if self.nonbonded is not None and not original_potential else {}
        state = self.context.getState(getEnergy=True,getForces=True,**arguments)
        energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        forces = np.array(state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer),dtype=float)
        if self.nonbonded is not None and not original_potential:
            pair_energy,pair_forces = self.nonbonded(coordinates)
            energy += pair_energy
            forces += pair_forces
        self.evaluations += 1
        gradient = -np.array(forces[list(self.movable)],dtype=float).reshape(-1)
        if self.observer is not None:
            self.observer(self.evaluations,coordinates,energy,forces)
        if not math.isfinite(energy) or not np.isfinite(gradient).all():
            raise ValueError("native fixed-coordinate MM returned a nonfinite energy or movable force")
        return float(energy),gradient
