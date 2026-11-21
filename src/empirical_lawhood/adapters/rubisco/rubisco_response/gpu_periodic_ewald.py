# SPDX-License-Identifier: Apache-2.0
# Copyright 2021-2024 The PySCF Developers. All Rights Reserved.
# Modified by the Empirical Lawhood project, 2026-11-05.
# Derived from GPU4PySCF 1.8.1 qmmm/pbc/{mm_mole,itrf}.py.
# See gpu-periodic-ewald-provenance.json and pyscf-periodic-LICENSE.txt.
"""Bound reciprocal Ewald work arrays without changing the selected operator.

The pinned upstream real-space, multipole and derivative expressions are retained.
Every reciprocal vector and MM charge contributes once, in float64 blocks.
Only the reduction order differs. Installed dependency files remain unchanged.
"""

from types import MethodType


# A workspace ceiling, not a smaller physical mesh or an evaluation limit.
RECIPROCAL_WORKSPACE_BYTES = 2 * 2**30


def reciprocal_block_length(*, points, mm_atoms, qm_atoms, free_bytes, allocation_bytes):
    """Bound live phase, trigonometric and derivative arrays by current headroom."""
    values = (points, mm_atoms, qm_atoms, free_bytes, allocation_bytes)
    if any(type(value) is not int or value <= 0 for value in values):
        raise ValueError('reciprocal blocking requires positive integer extents and allocations')
    # Eight MM rows cover phases, sine/cosine and charged contraction temporaries.
    # QM self/multipole derivatives have up to 27 Cartesian components.
    bytes_per_point = 8 * (8 * mm_atoms + 64 * qm_atoms + 128)
    budget = min(RECIPROCAL_WORKSPACE_BYTES, allocation_bytes // 8, free_bytes // 4)
    block = min(points, 1024, budget // bytes_per_point)
    if block < 1:
        raise MemoryError('insufficient observed GPU headroom for one reciprocal Ewald block')
    return block, bytes_per_point, budget


def reciprocal_blocks(cell, points, mm_atoms, qm_atoms, *, operation):
    import cupy as cp
    start = 0
    blocks = 0
    maximum_block = 0
    minimum_free = None
    while start < points:
        free, _ = cp.cuda.runtime.memGetInfo()
        block, per_point, budget = reciprocal_block_length(points=points-start,
            mm_atoms=mm_atoms, qm_atoms=qm_atoms, free_bytes=int(free),
            allocation_bytes=cell._el_ewald_device_memory_bytes)
        minimum_free = int(free) if minimum_free is None else min(minimum_free, int(free))
        maximum_block = max(maximum_block, block)
        if blocks == 0:
            cell._el_ewald_observe(dict(event='gpu-ewald-reciprocal-entry', operation=operation,
                mm_atoms=mm_atoms, qm_atoms=qm_atoms, reciprocal_points=points,
                original_phase_bytes=8*mm_atoms*points, workspace_budget_bytes=budget,
                estimated_bytes_per_point=per_point, block_points=block, precision='float64'))
        stop = min(points, start+block)
        yield start, stop
        start = stop
        blocks += 1
    cell._el_ewald_observe(dict(event='gpu-ewald-reciprocal-return', operation=operation,
        reciprocal_points=points, blocks=blocks, maximum_block_points=maximum_block,
        minimum_observed_free_bytes=minimum_free, precision='float64'))


def bind_bounded_ewald(mean_field, *, device_memory_bytes, observe):
    cell = mean_field.mm_mol
    if hasattr(cell, '_el_ewald_device_memory_bytes'):
        raise ValueError('bounded GPU Ewald was already bound')
    cell._el_ewald_device_memory_bytes = device_memory_bytes
    cell._el_ewald_observe = observe
    cell.get_ewald_pot = MethodType(get_ewald_pot, cell)
    return mean_field


def bind_bounded_ewald_gradient(derivative):
    if not hasattr(derivative.base.mm_mol, '_el_ewald_device_memory_bytes'):
        raise ValueError('GPU Ewald gradient requires the same bounded potential')
    derivative.grad_ewald = MethodType(grad_ewald, derivative)
    return derivative


def get_ewald_pot(self, coords1, coords2=None, charges2=None, zetas2=None):
    import cupy as cp
    from pyscf import lib, pbc
    from pyscf.lib import logger
    from gpu4pyscf.lib import cupy_helper
    from gpu4pyscf.qmmm.pbc.tools import get_multipole_tensors_pp, get_multipole_tensors_pg
    contract = cupy_helper.contract
    assert self.dimension == 3
    assert (coords2 is None and charges2 is None) or \
        (coords2 is not None and charges2 is not None and zetas2 is not None)
    coords1 = cp.asarray(coords1)
    if coords2 is not None:
        coords2 = cp.asarray(coords2)

    if charges2 is not None:
        assert len(charges2) == len(coords2)
        charges2 = cp.asarray(charges2)
        coords2 = cp.asarray(coords2)
    else:
        coords2 = coords1

    ew_eta, ew_cut = self.get_ewald_params()
    mesh = self.mesh

    logger.debug(self, f"Ewald exponent {ew_eta}")

    # TODO Lall should respect ew_rcut
    Lall = cp.asarray(self.get_lattice_Ls())

    all_coords2 = (coords2[None,:,:] - Lall[:,None,:]).reshape(-1,3)
    all_coords2 = cp.asarray(all_coords2)
    if charges2 is not None:
        all_charges2 = cp.hstack([charges2] * len(Lall))
    else:
        all_charges2 = None
    dist2 = all_coords2 - cp.mean(coords1, axis=0)[None]
    dist2 = contract('jx,jx->j', dist2, dist2)

    if all_charges2 is not None:
        ewovrl0 = cp.zeros(len(coords1))
        ewovrl1 = cp.zeros((len(coords1), 3))
        ewovrl2 = cp.zeros((len(coords1), 3, 3))
    else:
        ewovrl00 = cp.zeros((len(coords1), len(coords1)))
        ewovrl01 = cp.zeros((len(coords1), len(coords1), 3))
        ewovrl11 = cp.zeros((len(coords1), len(coords1), 3, 3))
        ewovrl02 = cp.zeros((len(coords1), len(coords1), 3, 3))
        ewself00 = cp.zeros((len(coords1), len(coords1)))
        ewself01 = cp.zeros((len(coords1), len(coords1), 3))
        ewself11 = cp.zeros((len(coords1), len(coords1), 3, 3))
        ewself02 = cp.zeros((len(coords1), len(coords1), 3, 3))

    mem_avail = cupy_helper.get_avail_mem()
    blksize = int(mem_avail/64/3/len(all_coords2))
    if blksize == 0:
        raise RuntimeError(f"Not enough GPU memory, mem_avail = {mem_avail}, blkszie = {blksize}")
    for i0, i1 in lib.prange(0, len(coords1), blksize):
        R = coords1[i0:i1,None,:] - all_coords2[None,:,:]
        r = cp.linalg.norm(R, axis=-1)
        r[r<1e-16] = 1e100
        rmax_qm = max(cp.linalg.norm(coords1 - cp.mean(coords1, axis=0), axis=-1))

        # substract the real-space Coulomb within rcut_hcore
        mask = dist2 <= self.rcut_hcore**2
        Tij, Tija, Tijab = get_multipole_tensors_pp(R[:,mask], [0,1,2], r[:,mask])
        if all_charges2 is not None:
            charges = all_charges2[mask]
            # ew0 = -d^2 E / dQi dqj qj
            # ew1 = -d^2 E / dDia dqj qj
            # ew2 = -d^2 E / dOiab dqj qj
            # qm pc - mm pc
            ewovrl0[i0:i1] += -contract('ij,j->i', Tij, charges)
            # qm dip - mm pc
            ewovrl1[i0:i1] += -contract('j,ija->ia', charges, Tija)
            # qm quad - mm pc
            ewovrl2[i0:i1] += -contract('j,ijab->iab', charges, Tijab) / 3
        else:
            # NOTE a too small rcut_hcore truncates QM atoms, while this correction
            # should be applied to all QM pairs regardless of rcut_hcore
            # NOTE this is now checked in get_hcore
            #assert r[:,mask].shape[0] == r[:,mask].shape[1]   # real-space should not see qm images
            # ew00 = -d^2 E / dQi dQj
            # ew01 = -d^2 E / dQi dDja
            # ew11 = -d^2 E / dDia dDjb
            # ew02 = -d^2 E / dQi dOjab
            ewovrl00[i0:i1] += -Tij
            ewovrl01[i0:i1] +=  Tija
            ewovrl11[i0:i1] +=  Tijab
            ewovrl02[i0:i1] += -Tijab / 3

        # difference between MM gaussain charges and MM point charges
        if all_charges2 is not None and self.charge_model == 'gaussian':
            zetas = cp.asarray(zetas2)
            mask = dist2 > self.rcut_hcore**2
            min_expnt = cp.min(zetas)
            max_ewrcut = pbc.gto.cell._estimate_rcut(min_expnt, 0, 1., self.precision)
            cut2 = (max_ewrcut + rmax_qm)**2
            mask = mask & (dist2 <= cut2)
            expnts = cp.hstack([cp.sqrt(zetas)] * len(Lall))[mask]
            r_ = r[:,mask]
            R_ = R[:,mask]
            if expnts.size != 0:
                Tij, Tija, Tijab = get_multipole_tensors_pg(R_, expnts, [0,1,2], r_)
                ewovrl0[i0:i1] -= contract('ij,j->i', Tij, all_charges2[mask])
                ewovrl1[i0:i1] -= contract('j,ija->ia', all_charges2[mask], Tija)
                ewovrl2[i0:i1] -= contract('j,ijab->iab', all_charges2[mask], Tijab) / 3

        # ewald real-space sum
        if all_charges2 is not None:
            cut2 = (ew_cut + rmax_qm)**2
            mask = dist2 <= cut2
            r_ = r[:,mask]
            R_ = R[:,mask]
            all_charges2_ = all_charges2[mask]
        else:
            # ewald sum will run over all qm images regardless of ew_cut
            # this is to ensure r and R will always have the shape of (i1-i0, L*num_qm)
            r_ = r
            R_ = R
        Tij, Tija, Tijab = get_multipole_tensors_pg(R_, ew_eta, [0,1,2], r_)

        if all_charges2 is not None:
            ewovrl0[i0:i1] += contract('ij,j->i', Tij, all_charges2_)
            ewovrl1[i0:i1] += contract('j,ija->ia', all_charges2_, Tija)
            ewovrl2[i0:i1] += contract('j,ijab->iab', all_charges2_, Tijab) / 3
        else:
            Tij = cp.sum(Tij.reshape(i1-i0, len(Lall), len(coords1)), axis=1)
            Tija = cp.sum(Tija.reshape(i1-i0, len(Lall), len(coords1), 3), axis=1)
            Tijab = cp.sum(Tijab.reshape(i1-i0, len(Lall), len(coords1), 3, 3), axis=1)
            ewovrl00[i0:i1] += Tij
            ewovrl01[i0:i1] -= Tija
            ewovrl11[i0:i1] -= Tijab
            ewovrl02[i0:i1] += Tijab / 3
        Tij = Tijab = None

        if all_charges2 is not None:
            pass
        else:
            ewself01[i0:i1] += 0
            ewself02[i0:i1] += 0
            # -d^2 Eself / dQi dQj
            ewself00[i0:i1] += -cp.eye(len(coords1))[i0:i1] * 2 * ew_eta / cp.sqrt(cp.pi)
            # -d^2 Eself / dDia dDjb
            ewself11[i0:i1] += -contract('ij,ab->ijab', cp.eye(len(coords1))[i0:i1], cp.eye(3)) \
                    * 4 * ew_eta**3 / 3 / cp.sqrt(cp.pi)

        r_ = R_ = all_charges2_ = None

    R = r = dist2 = all_charges2 = all_coords2 = mask = Tij = Tija = Tijab = None

    # g-space sum (using g grid)
    logger.debug(self, f"Ewald mesh {mesh}")

    Gv, Gvbase, weights = self.get_Gv_weights(mesh)
    Gv = cp.asarray(Gv)
    absG2 = contract('gx,gx->g', Gv, Gv)
    absG2[absG2==0] = 1e200

    coulG = 4*cp.pi / absG2
    coulG *= weights
    # NOTE Gpref is actually Gpref*2
    Gpref = cp.exp(-absG2/(4*ew_eta**2)) * coulG

    all_Gv, all_Gpref = Gv, Gpref
    if charges2 is not None:
        reciprocal = (cp.zeros(len(coords1)), cp.zeros((len(coords1), 3)),
                      cp.zeros((len(coords1), 3, 3)))
    else:
        reciprocal = (cp.zeros((len(coords1), len(coords1))),
                      cp.zeros((len(coords1), len(coords1), 3)),
                      cp.zeros((len(coords1), len(coords1), 3, 3)),
                      cp.zeros((len(coords1), len(coords1), 3, 3)))
    for g0, g1 in reciprocal_blocks(self, len(all_Gv), len(coords2), len(coords1),
                                    operation='potential'):
        Gv, Gpref = all_Gv[g0:g1], all_Gpref[g0:g1]
        GvR2 = contract('gx,ix->ig', Gv, coords2)
        cosGvR2 = cp.cos(GvR2)
        sinGvR2 = cp.sin(GvR2)

        if charges2 is not None:
            GvR1 = contract('gx,ix->ig', Gv, coords1)
            cosGvR1 = cp.cos(GvR1)
            sinGvR1 = cp.sin(GvR1)
            zcosGvR2 = contract("i,ig->g", charges2, cosGvR2)
            zsinGvR2 = contract("i,ig->g", charges2, sinGvR2)
            # qm pc - mm pc
            ewg0  = contract('ig,g->i', cosGvR1, zcosGvR2 * Gpref)
            ewg0 += contract('ig,g->i', sinGvR1, zsinGvR2 * Gpref)
            # qm dip - mm pc
            #p = ['einsum_path', (2, 3), (0, 2), (0, 1)]
            #ewg1  = contract('gx,ig,g,g->ix', Gv, cosGvR1, zsinGvR2, Gpref, optimize=p)
            #ewg1 -= contract('gx,ig,g,g->ix', Gv, sinGvR1, zcosGvR2, Gpref, optimize=p)
            tempGsR2  = contract('gx,g->gx', Gv, zsinGvR2 * Gpref)
            ewg1  = contract('gx,ig->ix', tempGsR2, cosGvR1)
            tempGcR2  = contract('gx,g->gx', Gv, zcosGvR2 * Gpref)
            ewg1 -= contract('gx,ig->ix', tempGcR2, sinGvR1)
            # qm quad - mm pc
            #p = ['einsum_path', (3, 4), (0, 3), (0, 2), (0, 1)]
            #ewg2  = -contract('gx,gy,ig,g,g->ixy', Gv, Gv, cosGvR1, zcosGvR2, Gpref, optimize=p)
            #ewg2 += -contract('gx,gy,ig,g,g->ixy', Gv, Gv, sinGvR1, zsinGvR2, Gpref, optimize=p)
            temp  =  contract('gx,gy->gxy', tempGcR2, Gv)
            ewg2  = -contract('gxy,ig->ixy', temp, cosGvR1)
            temp  =  contract('gx,gy->gxy', tempGsR2, Gv)
            ewg2 += -contract('gxy,ig->ixy', temp, sinGvR1)
            ewg2 /= 3
        else:
            # qm pc - qm pc
            #ewg00  = contract('ig,jg,g->ij', cosGvR2, cosGvR2, Gpref)
            #ewg00 += contract('ig,jg,g->ij', sinGvR2, sinGvR2, Gpref)
            temp   = contract('ig,g->ig', cosGvR2, Gpref)
            ewg00  = contract('ig,jg->ij', temp, cosGvR2)
            temp   = contract('ig,g->ig', sinGvR2, Gpref)
            ewg00 += contract('ig,jg->ij', temp, sinGvR2)
            # qm pc - qm dip
            #ewg01  = contract('gx,ig,jg,g->ijx', Gv, sinGvR2, cosGvR2, Gpref)
            #ewg01 -= contract('gx,ig,jg,g->ijx', Gv, cosGvR2, sinGvR2, Gpref)
            temp1   = contract('gx,g->gx', Gv, Gpref)
            temp   = contract('gx,ig->igx', temp1, sinGvR2)
            ewg01  = contract('igx,jg->ijx', temp, cosGvR2)
            temp   = contract('gx,ig->igx', temp1, cosGvR2)
            ewg01 -= contract('igx,jg->ijx', temp, sinGvR2)
            # qm dip - qm dip
            #ewg11  = contract('gx,gy,ig,jg,g->ijxy', Gv, Gv, cosGvR2, cosGvR2, Gpref)
            #ewg11 += contract('gx,gy,ig,jg,g->ijxy', Gv, Gv, sinGvR2, sinGvR2, Gpref)
            temp2   = contract('gx,gy->gxy', temp1, Gv)
            temp   = contract('gxy,ig->igxy', temp2, cosGvR2)
            ewg11  = contract('igxy,jg->ijxy', temp, cosGvR2)
            temp   = contract('gxy,ig->igxy', temp2, sinGvR2)
            ewg11 += contract('igxy,jg->ijxy', temp, sinGvR2)
            # qm pc - qm quad
            #ewg02  = -contract('gx,gy,ig,jg,g->ijxy', Gv, Gv, cosGvR2, cosGvR2, Gpref)
            #ewg02 += -contract('gx,gy,ig,jg,g->ijxy', Gv, Gv, sinGvR2, sinGvR2, Gpref)
            ewg02 = -ewg11 / 3

        part = (ewg0, ewg1, ewg2) if charges2 is not None else (ewg00, ewg01, ewg11, ewg02)
        for total, value in zip(reciprocal, part):
            total += value
        GvR2 = cosGvR2 = sinGvR2 = None
        GvR1 = cosGvR1 = sinGvR1 = None
        temp = tempGcR2 = tempGsR2 = temp1 = temp2 = part = None
    if charges2 is not None:
        ewg0, ewg1, ewg2 = reciprocal
    else:
        ewg00, ewg01, ewg11, ewg02 = reciprocal

    temp = tempGcR2 = tempGsR2 = temp1 = temp2 = None

    if charges2 is not None:
        return ewovrl0 + ewg0, ewovrl1 + ewg1, ewovrl2 + ewg2
    else:
        return ewovrl00 + ewself00 + ewg00, \
               ewovrl01 + ewself01 + ewg01, \
               ewovrl11 + ewself11 + ewg11, \
               ewovrl02 + ewself02 + ewg02


def grad_ewald(self, dm=None, with_mm=False, mm_ewald_pot=None, qm_ewald_pot=None):
    '''PBC correction energy grad w.r.t. qm and mm atom positions
    '''
    import cupy as cp
    import numpy as np
    from pyscf import gto, lib
    from pyscf.lib import logger
    from gpu4pyscf.lib import cupy_helper
    from gpu4pyscf.qmmm.pbc.tools import get_multipole_tensors_pp, get_multipole_tensors_pg
    contract = cupy_helper.contract
    cput0 = (logger.process_clock(), logger.perf_counter())
    if dm is None: dm = self.base.make_rdm1()
    if dm.ndim == 3:
        dm = dm[0] + dm[1]
    dm = cp.asarray(dm)
    mol = self.base.mol
    cell = self.base.mm_mol
    assert cell.dimension == 3
    qm_charges = self.base.get_qm_charges(dm)
    qm_dipoles = self.base.get_qm_dipoles(dm)
    qm_quads = self.base.get_qm_quadrupoles(dm)
    qm_coords = cp.asarray(self.base.mol.atom_coords())
    mm_charges = cp.asarray(self.base.mm_mol.atom_charges())
    mm_coords = cp.asarray(self.base.mm_mol.atom_coords())
    aoslices = mol.aoslice_by_atom()

    # nuc grad due to qm multipole change due to ovlp change
    qm_multipole_grad = cp.zeros_like(qm_coords)

    if mm_ewald_pot is None:
        if self.base.mm_ewald_pot is not None:
            mm_ewald_pot = self.base.mm_ewald_pot
        else:
            mm_ewald_pot = self.base.get_mm_ewald_pot(mol, cell)
    if qm_ewald_pot is None:
        qm_ewald_pot = self.base.get_qm_ewald_pot(mol, dm, self.base.qm_ewald_hess)
    ewald_pot = \
        mm_ewald_pot[0] + qm_ewald_pot[0], \
        mm_ewald_pot[1] + qm_ewald_pot[1], \
        mm_ewald_pot[2] + qm_ewald_pot[2]

    dEds = cp.zeros((mol.nao, mol.nao))
    dEdsr = cp.zeros((3, mol.nao, mol.nao))
    dEdsrr = cp.zeros((3, 3, mol.nao, mol.nao))
    s1 = cp.asarray(self.get_ovlp(mol)) # = -mol.intor('int1e_ipovlp')
    s1r = list()
    s1rr = list()
    bas_atom = mol._bas[:,gto.ATOM_OF]
    for iatm in range(mol.natm):
        v0 = cp.asarray(ewald_pot[0][iatm])
        v1 = cp.asarray(ewald_pot[1][iatm])
        v2 = cp.asarray(ewald_pot[2][iatm])
        p0, p1 = aoslices[iatm, 2:]

        dEds[p0:p1] -= v0 * dm[p0:p1]
        dEdsr[:,p0:p1] -= contract('x,uv->xuv', v1, dm[p0:p1])
        dEdsrr[:,:,p0:p1] -= contract('xy,uv->xyuv', v2, dm[p0:p1])

        b0, b1 = np.where(bas_atom == iatm)[0][[0,-1]]
        shlslc = (b0, b1+1, 0, mol.nbas)
        with mol.with_common_orig(qm_coords[iatm].get()):
            # s1r[a,x,u,v] = \int phi_u (r_a-Ri_a) (-\nabla_x phi_v) dr
            s1r.append(
                cp.asarray(-mol.intor('int1e_irp', shls_slice=shlslc).
                           reshape(3, 3, -1, mol.nao)))
            # s1rr[a,b,x,u,v] =
            # \int phi_u [3/2*(r_a-Ri_a)(r_b-Ri_b)-1/2*(r-Ri)^2 delta_ab] (-\nable_x phi_v) dr
            s1rr_ = cp.asarray(-mol.intor('int1e_irrp', shls_slice=shlslc).
                        reshape(3, 3, 3, -1, mol.nao))
            s1rr_trace = cp.einsum('aaxuv->xuv', s1rr_)
            s1rr_ *= 3 / 2
            for k in range(3):
                s1rr_[k,k] -= 0.5 * s1rr_trace
            s1rr.append(s1rr_)

    for jatm in range(mol.natm):
        p0, p1 = aoslices[jatm, 2:]

        # d E_qm_pc / d Ri with fixed ewald_pot
        qm_multipole_grad[jatm] += \
            contract('uv,xuv->x', dEds[p0:p1], s1[:,p0:p1]) \
          - contract('uv,xuv->x', dEds[:,p0:p1], s1[:,:,p0:p1])

        # d E_qm_dip / d Ri
        qm_multipole_grad[jatm] -= \
             contract('auv,axuv->x', dEdsr[:,p0:p1], s1r[jatm])
        s1r_ = list()
        for iatm in range(mol.natm):
            s1r_.append(s1r[iatm][...,p0:p1])
        s1r_ = cp.concatenate(s1r_, axis=-2)
        qm_multipole_grad[jatm] += contract('auv,axuv->x', dEdsr[...,p0:p1], s1r_)

        # d E_qm_quad / d Ri
        qm_multipole_grad[jatm] -= \
                contract('abuv,abxuv->x', dEdsrr[:,:,p0:p1], s1rr[jatm])
        s1rr_ = list()
        for iatm in range(mol.natm):
            s1rr_.append(s1rr[iatm][...,p0:p1])
        s1rr_ = cp.concatenate(s1rr_, axis=-2)
        qm_multipole_grad[jatm] += contract('abuv,abxuv->x', dEdsrr[...,p0:p1], s1rr_)

    cput1 = logger.timer(self, 'grad_ewald pulay', *cput0)
    s1 = s1r = s1rr = dEds = dEdsr = dEdsrr = None

    ew_eta, ew_cut = cell.get_ewald_params()

    # ---------------------------------------------- #
    # -------- Ewald real-space gradient ----------- #
    # ---------------------------------------------- #

    Lall = cp.asarray(cell.get_lattice_Ls())

    from pyscf import pbc
    rmax_qm = max(cp.linalg.norm(qm_coords - cp.mean(qm_coords, axis=0), axis=-1))
    qm_ewovrl_grad = cp.zeros_like(qm_coords)

    grad_Tij = lambda R, r: get_multipole_tensors_pp(R, [1,2,3], r)
    grad_kTij = lambda R, r, eta: get_multipole_tensors_pg(R, eta, [1,2,3], r)

    def grad_qm_multipole(Tija, Tijab, Tijabc,
                          qm_charges, qm_dipoles, qm_quads,
                          mm_charges):
        Tc   = contract('ijx,j->ix', Tija, mm_charges)
        res  = contract('i,ix->ix', qm_charges, Tc)
        Tc   = contract('ijxa,j->ixa', Tijab, mm_charges)
        res += contract('ia,ixa->ix', qm_dipoles, Tc)
        Tc   = contract('ijxab,j->ixab', Tijabc, mm_charges)
        res += contract('iab,ixab->ix', qm_quads, Tc) / 3
        return res

    def grad_mm_multipole(Tija, Tijab, Tijabc,
                          qm_charges, qm_dipoles, qm_quads,
                          mm_charges):
        Tc  = contract('i,ijx->jx', qm_charges, Tija)
        Tc += contract('ia,ijxa->jx', qm_dipoles, Tijab)
        Tc += contract('iab,ijxab->jx', qm_quads, Tijabc) / 3
        return contract('jx,j->jx', Tc, mm_charges)

    #------ qm - mm clasiical ewald energy gradient ------#
    all_mm_coords = (mm_coords[None,:,:] - Lall[:,None,:]).reshape(-1,3)
    all_mm_charges = cp.hstack([mm_charges] * len(Lall))
    dist2 = all_mm_coords - cp.mean(qm_coords, axis=0)[None]
    dist2 = contract('jx,jx->j', dist2, dist2)
    if with_mm:
        mm_ewovrl_grad = np.zeros_like(all_mm_coords)
    mem_avail = cupy_helper.get_avail_mem()
    blksize = int(mem_avail/64/3/len(all_mm_coords))
    if blksize == 0:
        raise RuntimeError(f"Not enough GPU memory, mem_avail = {mem_avail}, blkszie = {blksize}")
    for i0, i1 in lib.prange(0, mol.natm, blksize):
        R = qm_coords[i0:i1,None,:] - all_mm_coords[None,:,:]
        r = cp.linalg.norm(R, axis=-1)
        r[r<1e-16] = cp.inf

        # subtract the real-space Coulomb within rcut_hcore
        mask = dist2 <= cell.rcut_hcore**2
        Tija, Tijab, Tijabc = grad_Tij(R[:,mask], r[:,mask])
        qm_ewovrl_grad[i0:i1] -= grad_qm_multipole(Tija, Tijab, Tijabc,
                qm_charges[i0:i1], qm_dipoles[i0:i1], qm_quads[i0:i1], all_mm_charges[mask])
        if with_mm:
            mm_ewovrl_grad[mask] += grad_mm_multipole(Tija, Tijab, Tijabc,
                    qm_charges[i0:i1], qm_dipoles[i0:i1], qm_quads[i0:i1], all_mm_charges[mask])

        # difference between MM gaussain charges and MM point charges
        mask = dist2 > cell.rcut_hcore**2
        zetas = cp.asarray(cell.get_zetas())
        min_expnt = cp.min(zetas)
        max_ewrcut = pbc.gto.cell._estimate_rcut(min_expnt, 0, 1., cell.precision)
        cut2 = (max_ewrcut + rmax_qm)**2
        mask = mask & (dist2 <= cut2)
        expnts = cp.hstack([cp.sqrt(zetas)] * len(Lall))[mask]
        if expnts.size != 0:
            Tija, Tijab, Tijabc = grad_kTij(R[:,mask], r[:,mask], expnts)
            qm_ewovrl_grad[i0:i1] -= grad_qm_multipole(Tija, Tijab, Tijabc,
                    qm_charges[i0:i1], qm_dipoles[i0:i1], qm_quads[i0:i1], all_mm_charges[mask])
            if with_mm:
                mm_ewovrl_grad[mask] += grad_mm_multipole(Tija, Tijab, Tijabc,
                        qm_charges[i0:i1], qm_dipoles[i0:i1], qm_quads[i0:i1], all_mm_charges[mask])

        # ewald real-space sum
        cut2 = (ew_cut + rmax_qm)**2
        mask = dist2 <= cut2
        Tija, Tijab, Tijabc = grad_kTij(R[:,mask], r[:,mask], ew_eta)
        qm_ewovrl_grad[i0:i1] += grad_qm_multipole(Tija, Tijab, Tijabc,
                qm_charges[i0:i1], qm_dipoles[i0:i1], qm_quads[i0:i1], all_mm_charges[mask])
        if with_mm:
            mm_ewovrl_grad[mask] -= grad_mm_multipole(Tija, Tijab, Tijabc,
                    qm_charges[i0:i1], qm_dipoles[i0:i1], qm_quads[i0:i1], all_mm_charges[mask])

    if with_mm:
        mm_ewovrl_grad = mm_ewovrl_grad.reshape(len(Lall), -1, 3)
        mm_ewovrl_grad = cp.sum(mm_ewovrl_grad, axis=0)
    all_mm_coords = all_mm_charges = None

    #------ qm - qm clasiical ewald energy gradient ------#
    R = qm_coords[:,None,:] - qm_coords[None,:,:]
    r = np.sqrt(contract('ijx,ijx->ij', R, R))
    r[r<1e-16] = 1e100

    # subtract the real-space Coulomb within rcut_hcore
    Tija, Tijab, Tijabc = grad_Tij(R, r)
    #qm_ewovrl_grad -= cp.einsum('i,ijx,j->ix', qm_charges, Tija, qm_charges)
    #qm_ewovrl_grad += cp.einsum('i,ijxa,ja->ix', qm_charges, Tijab, qm_dipoles)
    #qm_ewovrl_grad -= cp.einsum('i,ijxa,ja->jx', qm_charges, Tijab, qm_dipoles) #
    #qm_ewovrl_grad += cp.einsum('ia,ijxab,jb->ix', qm_dipoles, Tijabc, qm_dipoles)
    #qm_ewovrl_grad -= cp.einsum('i,ijxab,jab->ix', qm_charges, Tijabc, qm_quads) / 3
    #qm_ewovrl_grad += cp.einsum('i,ijxab,jab->jx', qm_charges, Tijabc, qm_quads) / 3 #
    temp = contract('ijx,j->ix', Tija, qm_charges)
    qm_ewovrl_grad -= contract('i,ix->ix', qm_charges, temp)
    temp = contract('ijxa,ja->ix', Tijab, qm_dipoles)
    qm_ewovrl_grad += contract('i,ix->ix', qm_charges, temp)
    temp = contract('i,ijxa->jxa', qm_charges, Tijab)
    qm_ewovrl_grad -= contract('jxa,ja->jx', temp, qm_dipoles) #
    temp = contract('ijxab,jb->ixa', Tijabc, qm_dipoles)
    qm_ewovrl_grad += contract('ia,ixa->ix', qm_dipoles, temp)
    temp = contract('ijxab,jab->ix', Tijabc, qm_quads)
    qm_ewovrl_grad -= contract('i,ix->ix', qm_charges, temp) / 3
    temp = contract('ijxab,jab->ijx', Tijabc, qm_quads)
    qm_ewovrl_grad += contract('i,ijx->jx', qm_charges, temp) / 3 #
    temp = None

    # ewald real-space sum
    # NOTE here I assume ewald real-space sum is over all qm images
    # consistent with mm_mole.get_ewald_pot
    R = (R[:,:,None,:] - Lall[None,None]).reshape(len(qm_coords), len(Lall)*len(qm_coords), 3)
    r = np.sqrt(contract('ijx,ijx->ij', R, R))
    r[r<1e-16] = 1e100
    Tija, Tijab, Tijabc = grad_kTij(R, r, ew_eta)
    Tija = Tija.reshape(len(qm_coords), len(qm_coords), len(Lall), 3)
    Tijab = Tijab.reshape(len(qm_coords), len(qm_coords), len(Lall), 3, 3)
    Tijabc = Tijabc.reshape(len(qm_coords), len(qm_coords), len(Lall), 3, 3, 3)
    #qm_ewovrl_grad += cp.einsum('i,ijLx,j->ix', qm_charges, Tija, qm_charges)
    #qm_ewovrl_grad -= cp.einsum('i,ijLxa,ja->ix', qm_charges, Tijab, qm_dipoles)
    #qm_ewovrl_grad += cp.einsum('i,ijLxa,ja->jx', qm_charges, Tijab, qm_dipoles) #
    #qm_ewovrl_grad -= cp.einsum('ia,ijLxab,jb->ix', qm_dipoles, Tijabc, qm_dipoles)
    #qm_ewovrl_grad += cp.einsum('i,ijLxab,jab->ix', qm_charges, Tijabc, qm_quads) / 3
    #qm_ewovrl_grad -= cp.einsum('i,ijLxab,jab->jx', qm_charges, Tijabc, qm_quads) / 3 #
    temp = contract('ijLx,j->ix', Tija, qm_charges)
    qm_ewovrl_grad += contract('i,ix->ix', qm_charges, temp)
    temp = contract('ijLxa,ja->ix', Tijab, qm_dipoles)
    qm_ewovrl_grad -= contract('i,ix->ix', qm_charges, temp)
    temp = contract('i,ijLxa->jxa', qm_charges, Tijab)
    qm_ewovrl_grad += contract('jxa,ja->jx', temp, qm_dipoles) #
    temp = contract('ijLxab,jb->ixa', Tijabc, qm_dipoles)
    qm_ewovrl_grad -= contract('ia,ixa->ix', qm_dipoles, temp)
    temp = contract('ijLxab,jab->ix', Tijabc, qm_quads)
    qm_ewovrl_grad += contract('i,ix->ix', qm_charges, temp) / 3
    temp = contract('i,ijLxab->jxab', qm_charges, Tijabc)
    qm_ewovrl_grad -= contract('jxab,jab->jx', temp, qm_quads) / 3 #

    R = r = dist2 = mask = Tija = Tijab = Tijabc = temp = None
    cput2 = logger.timer(self, 'grad_ewald real-space', *cput1)

    # ---------------------------------------------- #
    # ---------- Ewald k-space gradient ------------ #
    # ---------------------------------------------- #

    mesh = cell.mesh
    Gv, Gvbase, weights = cell.get_Gv_weights(mesh)
    Gv = cp.asarray(Gv)
    absG2 = contract('gi,gi->g', Gv, Gv)
    absG2[absG2==0] = 1e200
    coulG = 4*np.pi / absG2
    coulG *= weights
    Gpref = cp.exp(-absG2/(4*ew_eta**2)) * coulG

    all_Gv, all_Gpref = Gv, Gpref
    qm_ewg_grad = cp.zeros_like(qm_coords)
    if with_mm:
        mm_ewg_grad = cp.zeros_like(mm_coords)
    for g0, g1 in reciprocal_blocks(cell, len(all_Gv), len(mm_coords), len(qm_coords),
                                    operation='gradient'):
        Gv, Gpref = all_Gv[g0:g1], all_Gpref[g0:g1]
        GvRmm = contract('gx,ix->ig', Gv, mm_coords)
        cosGvRmm = cp.cos(GvRmm)
        sinGvRmm = cp.sin(GvRmm)
        zcosGvRmm = contract("i,ig->g", mm_charges, cosGvRmm)
        zsinGvRmm = contract("i,ig->g", mm_charges, sinGvRmm)

        GvRqm = contract('gx,ix->ig', Gv, qm_coords)
        cosGvRqm = cp.cos(GvRqm)
        sinGvRqm = cp.sin(GvRqm)
        zcosGvRqm = contract("i,ig->g", qm_charges, cosGvRqm)
        zsinGvRqm = contract("i,ig->g", qm_charges, sinGvRqm)
        #DGcosGvRqm = cp.einsum("ia,ga,ig->g", qm_dipoles, Gv, cosGvRqm)
        #DGsinGvRqm = cp.einsum("ia,ga,ig->g", qm_dipoles, Gv, sinGvRqm)
        #TGGcosGvRqm = cp.einsum("iab,ga,gb,ig->g", qm_quads, Gv, Gv, cosGvRqm)
        #TGGsinGvRqm = cp.einsum("iab,ga,gb,ig->g", qm_quads, Gv, Gv, sinGvRqm)
        temp = contract('ia,ig->ag', qm_dipoles, cosGvRqm)
        DGcosGvRqm = contract('ga,ag->g', Gv, temp)
        temp = contract('ia,ig->ag', qm_dipoles, sinGvRqm)
        DGsinGvRqm = contract('ga,ag->g', Gv, temp)
        temp = contract('iab,ig->abg', qm_quads, cosGvRqm)
        temp = contract('abg,ga->bg', temp, Gv)
        TGGcosGvRqm = contract('gb,bg->g', Gv, temp)
        temp = contract('iab,ig->abg', qm_quads, sinGvRqm)
        temp = contract('abg,ga->bg', temp, Gv)
        TGGsinGvRqm = contract('gb,bg->g', Gv, temp)


        # qm pc - mm pc
        #p = ['einsum_path', (3, 4), (1, 3), (1, 2), (0, 1)]
        #qm_ewg_grad -= cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, sinGvRqm, zcosGvRmm, Gpref, optimize=p)
        #qm_ewg_grad += cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, cosGvRqm, zsinGvRmm, Gpref, optimize=p)
        temp = contract('g,g->g', zcosGvRmm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', sinGvRqm, temp)
        qm_ewg_grad -= contract('i,ix->ix', qm_charges, temp)
        temp = contract('g,g->g', zsinGvRmm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', cosGvRqm, temp)
        qm_ewg_grad += contract('i,ix->ix', qm_charges, temp)
        if with_mm:
            #p = ['einsum_path', (0, 2), (1, 2), (0, 2), (0, 1)]
            #mm_ewg_grad -= cp.einsum('i,gx,ig,g,g->ix', mm_charges, Gv, sinGvRmm, zcosGvRqm, Gpref, optimize=p)
            #mm_ewg_grad += cp.einsum('i,gx,ig,g,g->ix', mm_charges, Gv, cosGvRmm, zsinGvRqm, Gpref, optimize=p)
            temp = contract('i,ig->gi', mm_charges, sinGvRmm)
            temp2 = contract('g,g->g', zcosGvRqm, Gpref)
            temp2 = contract('gx,g->gx', Gv, temp2)
            mm_ewg_grad -= contract('gi,gx->ix', temp, temp2)
            temp = contract('i,ig->gi', mm_charges, cosGvRmm)
            temp2 = contract('g,g->g', zsinGvRqm, Gpref)
            temp2 = contract('gx,g->gx', Gv, temp2)
            mm_ewg_grad += contract('gi,gx->ix', temp, temp2)
        # qm dip - mm pc
        #p = ['einsum_path', (4, 5), (1, 4), (0, 1), (0, 2), (0, 1)]
        #qm_ewg_grad -= cp.einsum('ia,gx,ga,ig,g,g->ix', qm_dipoles, Gv, Gv, sinGvRqm, zsinGvRmm, Gpref, optimize=p)
        #qm_ewg_grad -= cp.einsum('ia,gx,ga,ig,g,g->ix', qm_dipoles, Gv, Gv, cosGvRqm, zcosGvRmm, Gpref, optimize=p)
        temp = contract('g,g->g', zsinGvRmm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp2 = contract('ia,ga->gi', qm_dipoles, Gv)
        temp2 = contract('ig,gi->ig', sinGvRqm, temp2)
        qm_ewg_grad -= contract('gx,ig->ix', temp, temp2)
        temp = contract('g,g->g', zcosGvRmm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp2 = contract('ia,ga->gi', qm_dipoles, Gv)
        temp2 = contract('ig,gi->ig', cosGvRqm, temp2)
        qm_ewg_grad -= contract('gx,ig->ix', temp, temp2)
        if with_mm:
            #p = ['einsum_path', (1, 3), (0, 2), (0, 2), (0, 1)]
            #mm_ewg_grad += cp.einsum('g,j,gx,jg,g->jx', DGcosGvRqm, mm_charges, Gv, cosGvRmm, Gpref, optimize=p)
            #mm_ewg_grad += cp.einsum('g,j,gx,jg,g->jx', DGsinGvRqm, mm_charges, Gv, sinGvRmm, Gpref, optimize=p)
            temp = contract('j,jg->gj', mm_charges, cosGvRmm)
            temp2 = contract('g,g->g', DGcosGvRqm, Gpref)
            temp2 = contract('gx,g->gx', Gv, temp2)
            mm_ewg_grad += contract('gj,gx->jx', temp, temp2)
            temp = contract('j,jg->gj', mm_charges, sinGvRmm)
            temp2 = contract('g,g->g', DGsinGvRqm, Gpref)
            temp2 = contract('gx,g->gx', Gv, temp2)
            mm_ewg_grad += contract('gj,gx->jx', temp, temp2)
        # qm quad - mm pc
        #p = ['einsum_path', (5, 6), (0, 5), (0, 2), (2, 3), (1, 2), (0, 1)]
        #qm_ewg_grad += cp.einsum('ga,gb,iab,gx,ig,g,g->ix', Gv, Gv, qm_quads, Gv, sinGvRqm, zcosGvRmm, Gpref, optimize=p) / 3
        #qm_ewg_grad -= cp.einsum('ga,gb,iab,gx,ig,g,g->ix', Gv, Gv, qm_quads, Gv, cosGvRqm, zsinGvRmm, Gpref, optimize=p) / 3
        temp = contract('g,g->g', zcosGvRmm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp2 = contract('gb,gx->gbx', Gv, Gv)
        temp = contract('ag,gbx->abgx', temp, temp2)
        temp = contract('ig,abgx->iabx', sinGvRqm, temp)
        qm_ewg_grad += contract('iab,iabx->ix', qm_quads, temp) / 3
        temp = contract('g,g->g', zsinGvRmm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp2 = contract('gb,gx->gbx', Gv, Gv)
        temp = contract('ag,gbx->abgx', temp, temp2)
        temp = contract('ig,abgx->iabx', cosGvRqm, temp)
        qm_ewg_grad -= contract('iab,iabx->ix', qm_quads, temp) / 3
        if with_mm:
            #p = ['einsum_path', (1, 3), (0, 2), (0, 2), (0, 1)]
            #mm_ewg_grad += cp.einsum('g,j,gx,jg,g->jx', TGGcosGvRqm, mm_charges, Gv, sinGvRmm, Gpref, optimize=p) / 3
            #mm_ewg_grad -= cp.einsum('g,j,gx,jg,g->jx', TGGsinGvRqm, mm_charges, Gv, cosGvRmm, Gpref, optimize=p) / 3
            temp = contract('j,jg->gj', mm_charges, sinGvRmm)
            temp2 = contract('g,g->g', TGGcosGvRqm, Gpref)
            temp2 = contract('gx,g->gx', Gv, temp2)
            mm_ewg_grad += contract('gj,gx->jx', temp, temp2) / 3
            temp = contract('j,jg->gj', mm_charges, cosGvRmm)
            temp2 = contract('g,g->g', TGGsinGvRqm, Gpref)
            temp2 = contract('gx,g->gx', Gv, temp2)
            mm_ewg_grad -= contract('gj,gx->jx', temp, temp2) / 3

        # qm pc - qm pc
        #p = ['einsum_path', (3, 4), (1, 3), (1, 2), (0, 1)]
        #qm_ewg_grad -= cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, sinGvRqm, zcosGvRqm, Gpref, optimize=p)
        #qm_ewg_grad += cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, cosGvRqm, zsinGvRqm, Gpref, optimize=p)
        temp = contract('g,g->g', zcosGvRqm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', sinGvRqm, temp)
        qm_ewg_grad -= contract('i,ix->ix', qm_charges, temp)
        temp = contract('g,g->g', zsinGvRqm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', cosGvRqm, temp)
        qm_ewg_grad += contract('i,ix->ix', qm_charges, temp)
        # qm pc - qm dip
        #qm_ewg_grad += cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, cosGvRqm, DGcosGvRqm, Gpref, optimize=p)
        #qm_ewg_grad += cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, sinGvRqm, DGsinGvRqm, Gpref, optimize=p)
        temp = contract('g,g->g', DGcosGvRqm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', cosGvRqm, temp)
        qm_ewg_grad += contract('i,ix->ix', qm_charges, temp)
        temp = contract('g,g->g', DGsinGvRqm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', sinGvRqm, temp)
        qm_ewg_grad += contract('i,ix->ix', qm_charges, temp)
        #p = ['einsum_path', (3, 5), (1, 4), (1, 3), (1, 2), (0, 1)]
        #qm_ewg_grad -= cp.einsum('ja,ga,gx,g,jg,g->jx', qm_dipoles, Gv, Gv, zsinGvRqm, sinGvRqm, Gpref, optimize=p)
        #qm_ewg_grad -= cp.einsum('ja,ga,gx,g,jg,g->jx', qm_dipoles, Gv, Gv, zcosGvRqm, cosGvRqm, Gpref, optimize=p)
        temp = contract('g,g->g', zsinGvRqm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp = contract('gx,ag->axg', Gv, temp)
        temp = contract('jg,axg->ajx', sinGvRqm, temp)
        qm_ewg_grad -= contract('ja,ajx->jx', qm_dipoles, temp)
        temp = contract('g,g->g', zcosGvRqm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp = contract('gx,ag->axg', Gv, temp)
        temp = contract('jg,axg->ajx', cosGvRqm, temp)
        qm_ewg_grad -= contract('ja,ajx->jx', qm_dipoles, temp)
        # qm dip - qm dip
        #p = ['einsum_path', (4, 5), (1, 4), (1, 3), (1, 2), (0, 1)]
        #qm_ewg_grad -= cp.einsum('ia,ga,gx,ig,g,g->ix', qm_dipoles, Gv, Gv, sinGvRqm, DGcosGvRqm, Gpref, optimize=p)
        #qm_ewg_grad += cp.einsum('ia,ga,gx,ig,g,g->ix', qm_dipoles, Gv, Gv, cosGvRqm, DGsinGvRqm, Gpref, optimize=p)
        temp = contract('g,g->g', DGcosGvRqm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp = contract('gx,ag->axg', Gv, temp)
        temp = contract('ig,axg->aix', sinGvRqm, temp)
        qm_ewg_grad -= contract('ia,aix->ix', qm_dipoles, temp)
        temp = contract('g,g->g', DGsinGvRqm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp = contract('gx,ag->axg', Gv, temp)
        temp = contract('ig,axg->aix', cosGvRqm, temp)
        qm_ewg_grad += contract('ia,aix->ix', qm_dipoles, temp)
        # qm pc - qm quad
        #p = ['einsum_path', (3, 4), (1, 3), (1, 2), (0, 1)]
        #qm_ewg_grad += cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, sinGvRqm, TGGcosGvRqm, Gpref, optimize=p) / 3
        #qm_ewg_grad -= cp.einsum('i,gx,ig,g,g->ix', qm_charges, Gv, cosGvRqm, TGGsinGvRqm, Gpref, optimize=p) / 3
        temp = contract('g,g->g', TGGcosGvRqm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', sinGvRqm, temp)
        qm_ewg_grad += contract('i,ix->ix', qm_charges, temp) / 3
        temp = contract('g,g->g', TGGsinGvRqm, Gpref)
        temp = contract('gx,g->gx', Gv, temp)
        temp = contract('ig,gx->ix', cosGvRqm, temp)
        qm_ewg_grad -= contract('i,ix->ix', qm_charges, temp) / 3
        #p = ['einsum_path', (4, 6), (1, 5), (1, 2), (2, 3), (1, 2), (0, 1)]
        #qm_ewg_grad += cp.einsum('jab,ga,gb,gx,g,jg,g->jx', qm_quads, Gv, Gv, Gv, zcosGvRqm, sinGvRqm, Gpref, optimize=p) / 3
        #qm_ewg_grad -= cp.einsum('jab,ga,gb,gx,g,jg,g->jx', qm_quads, Gv, Gv, Gv, zsinGvRqm, cosGvRqm, Gpref, optimize=p) / 3
        temp = contract('g,g->g', zcosGvRqm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp2 = contract('gb,gx->bgx', Gv, Gv)
        temp = contract('ag,bgx->abgx', temp, temp2)
        temp = contract('jg,abgx->abjx', sinGvRqm, temp)
        qm_ewg_grad += contract('jab,abjx->jx', qm_quads, temp) / 3
        temp = contract('g,g->g', zsinGvRqm, Gpref)
        temp = contract('ga,g->ag', Gv, temp)
        temp2 = contract('gb,gx->bgx', Gv, Gv)
        temp = contract('ag,bgx->abgx', temp, temp2)
        temp = contract('jg,abgx->abjx', cosGvRqm, temp)
        qm_ewg_grad -= contract('jab,abjx->jx', qm_quads, temp) / 3

        GvRmm = cosGvRmm = sinGvRmm = None
        GvRqm = cosGvRqm = sinGvRqm = temp = temp2 = None

    logger.timer(self, 'grad_ewald k-space', *cput2)
    logger.timer(self, 'grad_ewald', *cput0)
    if not with_mm:
        return (qm_multipole_grad + qm_ewovrl_grad + qm_ewg_grad).get()
    else:
        return (qm_multipole_grad + qm_ewovrl_grad + qm_ewg_grad).get(), \
               (mm_ewovrl_grad + mm_ewg_grad).get()
