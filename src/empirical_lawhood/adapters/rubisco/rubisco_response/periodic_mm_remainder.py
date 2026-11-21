# SPDX-License-Identifier: MPL-2.0
"""OpenMM System mutation for the declared periodic QM/MM remainder.

Pure link-coordinate, pullback and embedding-charge calculations remain in the
Rubisco domain. Only this native binding clones and changes engine force terms.
"""
from itertools import combinations
from math import fsum, isfinite

from empirical_lawhood.adapters.rubisco.rubisco_insilico_free_energy.native_coupling import correct_coulomb_exceptions
from empirical_lawhood.adapters.rubisco.rubisco_response.amber_system_copy import PARAMETER_ENCODING, clone_amber_system, native_system_sha256
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_remainder import _qm_selection


def periodic_mm_remainder(original, qm_indices, source_scee, *, mm, unit):
    """Copy and mask only QM-internal terms; preserve all cross/boundary terms.

    The input selects unconstrained natural-mass Amber dynamics, PME/Ewald and
    no analytical dispersion-tail correction. Every classical MM charge is
    retained unchanged. Any charge redistribution used for the electronic
    embedding is a separate operand and never changes this MM potential.
    """
    count = original.getNumParticles()
    qm = _qm_selection(qm_indices, count)
    if original.getNumConstraints() or any(original.isVirtualSite(i) for i in range(count)):
        raise ValueError('selected explicit unconstrained atoms cannot contain constraints or virtual sites')
    masses = tuple(original.getParticleMass(i).value_in_unit(unit.dalton) for i in range(count))
    if any(not isfinite(m) or m <= 0 for m in masses):
        raise ValueError('every selected physical atom requires a finite positive natural mass')
    permitted = {'HarmonicBondForce', 'HarmonicAngleForce', 'PeriodicTorsionForce',
                 'NonbondedForce', 'CMMotionRemover'}
    kinds = [type(force).__name__ for force in original.getForces()]
    if (set(kinds)-permitted or kinds.count('NonbondedForce') != 1
            or any(kinds.count(kind) != 1 for kind in set(kinds))):
        raise ValueError('selected periodic Amber remainder has an unsupported or duplicate force')
    original_nb = next(force for force in original.getForces() if type(force).__name__ == 'NonbondedForce')
    if (original_nb.getNonbondedMethod() not in (mm.NonbondedForce.PME, mm.NonbondedForce.Ewald)
            or original_nb.getUseDispersionCorrection() or original_nb.getNumGlobalParameters()
            or original_nb.getNumParticleParameterOffsets() or original_nb.getNumExceptionParameterOffsets()):
        raise ValueError('periodic remainder requires its explicit unmodified Ewald/PME and dispersion convention')
    original_q = tuple(original_nb.getParticleParameters(i)[0].value_in_unit(unit.elementary_charge) for i in range(count))
    if any(not isfinite(float(q)) for q in original_q):
        raise ValueError('the original MM system contains a nonfinite charge')
    classical_charges = tuple(0.0 if i in qm else q for i, q in enumerate(original_q))
    before = fsum(q for i, q in enumerate(original_q) if i not in qm)
    after = fsum(float(q) for q in classical_charges)
    if before != after:
        raise ValueError('masking QM charges changes the complete MM charge')
    result, before_digest = clone_amber_system(original, mm=mm, unit=unit)
    masked, retained = {}, {}
    for force in result.getForces():
        kind = type(force).__name__
        if kind == 'HarmonicBondForce':
            n, get, put, size = force.getNumBonds(), force.getBondParameters, force.setBondParameters, 2
        elif kind == 'HarmonicAngleForce':
            n, get, put, size = force.getNumAngles(), force.getAngleParameters, force.setAngleParameters, 3
        elif kind == 'PeriodicTorsionForce':
            n, get, put, size = force.getNumTorsions(), force.getTorsionParameters, force.setTorsionParameters, 4
        else:
            continue
        removed = []
        for i in range(n):
            row = get(i)
            if all(int(a) in qm for a in row[:size]):
                put(i, *row[:-1], row[-1]*0)
                removed.append(i)
        masked[kind] = tuple(removed)
        retained[kind] = n-len(removed)
    nb = next(force for force in result.getForces() if type(force).__name__ == 'NonbondedForce')
    for i, q in enumerate(classical_charges):
        _, sigma, epsilon = nb.getParticleParameters(i)
        nb.setParticleParameters(i, float(q), sigma, epsilon)
    exception_audit = correct_coulomb_exceptions(result, qm_indices, classical_charges, source_scee, unit=unit)
    existing = {tuple(sorted(map(int, nb.getExceptionParameters(i)[:2]))): i for i in range(nb.getNumExceptions())}
    qm_pairs = []
    for a, b in combinations(qm_indices, 2):
        if (a,b) in existing:
            ordinal = existing[(a,b)]
            _, _, _, sigma, epsilon = nb.getExceptionParameters(ordinal)
            nb.setExceptionParameters(ordinal, a, b, 0, sigma, epsilon*0)
            role = 'existing'
        else:
            sigma = (nb.getParticleParameters(a)[1]+nb.getParticleParameters(b)[1])/2
            ordinal = nb.addException(a,b,0,sigma,0)
            role = 'new-internal-exclusion'
        qm_pairs.append((a,b,int(ordinal),role))
    if native_system_sha256(original, unit) != before_digest:
        raise ValueError('remainder construction changed the original physical system')
    return result, dict(atoms=count, qm_atoms=qm_indices, mm_atoms=count-len(qm_indices),
        parameter_encoding=PARAMETER_ENCODING, original_parameter_sha256=before_digest,
        remainder_parameter_sha256=native_system_sha256(result, unit),
        original_mm_charge=before, remainder_mm_charge=after,
        original_mm_particle_charges_preserved=True, embedding_charge_redistribution_applied=False,
        masked_internal_bonded_terms=masked, retained_bonded_counts=retained,
        coulomb_exception_audit=exception_audit, qm_internal_nonbonded_pairs=tuple(qm_pairs),
        dispersion_tail=False, original_unchanged=True)


