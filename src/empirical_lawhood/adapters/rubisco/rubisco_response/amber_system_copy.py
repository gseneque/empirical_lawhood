# SPDX-License-Identifier: MPL-2.0
"""Complete unconstrained Amber system copying without a full XML tree."""

from hashlib import sha256
import json


PARAMETER_ENCODING = "openmm-unconstrained-amber-parameter-rows-v1"


def native_parameter_rows(system, unit):
    """Yield every supported parameter and numerical option in native order."""
    count = system.getNumParticles()
    if system.getNumConstraints() or any(system.isVirtualSite(i) for i in range(count)):
        raise ValueError("complete Amber system copy requires unconstrained atoms without virtual sites")
    yield (PARAMETER_ENCODING, count, system.getNumForces(), bool(system.usesPeriodicBoundaryConditions()))
    yield ("box-nm", tuple(tuple(float(v) for v in row.value_in_unit(unit.nanometer))
        for row in system.getDefaultPeriodicBoxVectors()))
    for i in range(count):
        yield ("mass", i, float(system.getParticleMass(i).value_in_unit(unit.dalton)))
    for ordinal, force in enumerate(system.getForces()):
        kind = type(force).__name__
        yield ("force", ordinal, kind, force.getName(), force.getForceGroup(), bool(force.usesPeriodicBoundaryConditions()))
        if kind == "NonbondedForce":
            if (force.getNumGlobalParameters() or force.getNumParticleParameterOffsets()
                    or force.getNumExceptionParameterOffsets()):
                raise ValueError("complete Amber system copy refuses parameter offsets and global parameters")
            yield ("nonbonded-options", force.getNonbondedMethod(),
                float(force.getCutoffDistance().value_in_unit(unit.nanometer)),
                bool(force.getUseSwitchingFunction()), float(force.getSwitchingDistance().value_in_unit(unit.nanometer)),
                bool(force.getUseDispersionCorrection()), float(force.getEwaldErrorTolerance()),
                bool(force.getExceptionsUsePeriodicBoundaryConditions()), bool(force.getIncludeDirectSpace()),
                force.getReciprocalSpaceForceGroup(), force.getNumParticles(), force.getNumExceptions())
            for label, selected in (("pme", force.getPMEParameters()), ("ljpme", force.getLJPMEParameters())):
                alpha, x, y, z = selected
                yield (label, float(alpha.value_in_unit(unit.nanometer**-1) if unit.is_quantity(alpha) else alpha), int(x), int(y), int(z))
            for i in range(force.getNumParticles()):
                q, sigma, epsilon = force.getParticleParameters(i)
                yield ("particle", i, float(q.value_in_unit(unit.elementary_charge)),
                    float(sigma.value_in_unit(unit.nanometer)), float(epsilon.value_in_unit(unit.kilojoule_per_mole)))
            for i in range(force.getNumExceptions()):
                a, b, q, sigma, epsilon = force.getExceptionParameters(i)
                yield ("exception", i, int(a), int(b), float(q.value_in_unit(unit.elementary_charge**2)),
                    float(sigma.value_in_unit(unit.nanometer)), float(epsilon.value_in_unit(unit.kilojoule_per_mole)))
        elif kind == "HarmonicBondForce":
            yield ("bonds", force.getNumBonds())
            for i in range(force.getNumBonds()):
                a, b, distance, k = force.getBondParameters(i)
                yield ("bond", i, int(a), int(b), float(distance.value_in_unit(unit.nanometer)),
                    float(k.value_in_unit(unit.kilojoule_per_mole/unit.nanometer**2)))
        elif kind == "HarmonicAngleForce":
            yield ("angles", force.getNumAngles())
            for i in range(force.getNumAngles()):
                a, b, c, angle, k = force.getAngleParameters(i)
                yield ("angle", i, int(a), int(b), int(c), float(angle.value_in_unit(unit.radian)),
                    float(k.value_in_unit(unit.kilojoule_per_mole/unit.radian**2)))
        elif kind == "PeriodicTorsionForce":
            yield ("torsions", force.getNumTorsions())
            for i in range(force.getNumTorsions()):
                a, b, c, d, periodicity, phase, k = force.getTorsionParameters(i)
                yield ("torsion", i, int(a), int(b), int(c), int(d), int(periodicity),
                    float(phase.value_in_unit(unit.radian)), float(k.value_in_unit(unit.kilojoule_per_mole)))
        elif kind == "CMMotionRemover":
            yield ("center-of-mass-frequency", force.getFrequency())
        else:
            raise ValueError("complete Amber system copy refuses an unknown force class: "+kind)


def native_system_sha256(system, unit):
    """Hash complete length-delimited rows with bounded temporary memory."""
    digest = sha256()
    for row in native_parameter_rows(system, unit):
        raw = json.dumps(row, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def clone_amber_system(original, *, mm, unit):
    """Copy selected force vectors directly and verify every resulting field."""
    before = native_system_sha256(original, unit)
    result = mm.System()
    result.setDefaultPeriodicBoxVectors(*original.getDefaultPeriodicBoxVectors())
    for i in range(original.getNumParticles()):
        result.addParticle(original.getParticleMass(i))
    for force in original.getForces():
        result.addForce(getattr(mm, type(force).__name__)(force))
    if native_system_sha256(result, unit) != before:
        raise ValueError("direct Amber force copy changes its complete native parameters")
    return result, before
