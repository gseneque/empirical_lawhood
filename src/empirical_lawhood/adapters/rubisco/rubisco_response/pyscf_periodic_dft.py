# SPDX-License-Identifier: Apache-2.0
# Copyright 2014-2019 The PySCF Developers. All Rights Reserved.
# Copyright 2026 Empirical Lawhood project.
# Derived from PySCF 2.14.0 dft/numint.py and grad/rks.py, grad/uks.py.
# Author of the upstream gradient implementation: Qiming Sun.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. See pyscf-periodic-LICENSE.txt and NOTICE.
"""Instance-local bounded DFT grids, including every grid-response derivative.

This native-only module is imported at explicit operator construction. It does
not modify installed PySCF modules. The selected reference is GGA wB97X with
Becke partitioning; unsupported functional/partition choices refuse explicitly.
The upstream formulas are unchanged. Blocks precede both atom-pair partition
and AO allocations, and all points and derivative terms remain present.
"""
from types import MethodType

import numpy
from pyscf import gto, lib
from pyscf.dft import numint, radi, gen_grid
from pyscf.grad import rks as rks_grad

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_memory import grid_block_size


class MemoryBoundedNumInt(numint.NumInt):
    """Preserve upstream integration and masks with a bounded reusable AO buffer."""

    def __init__(self, original, *, memory_megabytes, observe):
        if type(original) is not numint.NumInt or not callable(observe):
            raise ValueError('bounded reference integration requires the standard NumInt and an observer')
        self.__dict__.update(original.__dict__)
        self.memory_megabytes, self.observe = memory_megabytes, observe
        # A smaller explicit block is useful for exposed equivalence controls.
        # It changes allocation only, never the grid or the electronic method.
        self.response_block_limit = None

    def block_loop(self, mol, grids, nao=None, deriv=0, max_memory=2000,
                   non0tab=None, blksize=None, buf=None):
        if grids.coords is None:
            grids.build(with_non0tab=True)
        if nao is None:
            nao = mol.nao
        if len(grids.coords) == 0:
            return
        selected = grid_block_size(len(grids.coords), nao=int(nao), derivative=deriv,
            maximum_memory_mb=self.memory_megabytes, alignment=numint.BLKSIZE,
            working_memory_mb=max_memory, requested_size=blksize, observe=self.observe)
        # PySCF reuses this single selected buffer over the complete grid.
        yield from super().block_loop(mol, grids, nao, deriv, max_memory,
            non0tab=non0tab, blksize=selected, buf=buf)


def grids_response_becke(grids, ni, nao):
    mol = grids.mol
    atom_grids_tab = grids.gen_atomic_grids(mol, grids.atom_grid,
                                            grids.radi_method,
                                            grids.level, grids.prune)
    atm_coords = numpy.asarray(mol.atom_coords() , order='C')
    atm_dist = gto.inter_distance(mol, atm_coords)

    def _radii_adjust(mol, atomic_radii):
        charges = mol.atom_charges()
        if grids.radii_adjust == radi.treutler_atomic_radii_adjust:
            rad = numpy.sqrt(atomic_radii[charges]) + 1e-200
        elif grids.radii_adjust == radi.becke_atomic_radii_adjust:
            rad = atomic_radii[charges] + 1e-200
        else:
            fadjust = lambda i, j, g: g
            gadjust = lambda *args: 1
            return fadjust, gadjust

        rr = rad.reshape(-1,1) * (1./rad)
        a = .25 * (rr.T - rr)
        a[a<-.5] = -.5
        a[a>0.5] = 0.5

        def fadjust(i, j, g):
            return g + a[i,j]*(1-g**2)

        #: d[g + a[i,j]*(1-g**2)] /dg = 1 - 2*a[i,j]*g
        def gadjust(i, j, g):
            return 1 - 2*a[i,j]*g
        return fadjust, gadjust

    fadjust, gadjust = _radii_adjust(mol, grids.atomic_radii)

    def get_smooth_function_derivative(mu):
        if grids.becke_scheme == gen_grid.original_becke:
            p0 = mu
            p1 = (3 - p0**2) * p0 * .5
            p2 = (3 - p1**2) * p1 * .5
            p3 = (3 - p2**2) * p2 * .5
            t_uab = 27./8. * (1-p2**2) * (1-p1**2) * (1-p0**2)
            return p3, t_uab
        elif grids.becke_scheme == gen_grid.stratmann:
            a = .64
            ma = mu/a
            ma2 = ma * ma
            g1 = (1/16.)*(ma*(35 + ma2*(-35 + ma2*(21 - 5 *ma2))))
            g1[mu<=-a] = -1
            g1[mu>= a] =  1

            t_uab = (35.0/16.0 / a) * (1.0 - ma2 * (3.0 - ma2 * (3.0 - ma2)))
            t_uab[mu<=-a] = 0
            t_uab[mu>= a] = 0
            return g1, t_uab
        else:
            raise NotImplementedError(f"Grid response for becke_scheme = {grids.becke_scheme} is not implemented")

    def gen_grid_partition(coords, atom_id):
        ngrids = coords.shape[0]
        grid_dist = []
        grid_norm_vec = []
        for ia in range(mol.natm):
            v = (atm_coords[ia] - coords).T
            normv = numpy.linalg.norm(v,axis=0) + 1e-200
            v /= normv
            grid_dist.append(normv)
            grid_norm_vec.append(v)

        def get_du(ia, ib):  # JCP 98, 5612 (1993); (B10)
            uab = atm_coords[ia] - atm_coords[ib]
            duab = 1./atm_dist[ia,ib] * grid_norm_vec[ia]
            duab-= uab[:,None]/atm_dist[ia,ib]**3 * (grid_dist[ia]-grid_dist[ib])
            return duab

        pbecke = numpy.ones((mol.natm,ngrids))
        dpbecke = numpy.zeros((mol.natm,mol.natm,3,ngrids))
        for ia in range(mol.natm):
            for ib in range(ia):
                g = 1/atm_dist[ia,ib] * (grid_dist[ia]-grid_dist[ib])
                g_radii_adjusted = fadjust(ia, ib, g)
                smoothed, t_uab = get_smooth_function_derivative(g_radii_adjusted)
                t_uab *= 0.5 * gadjust(ia, ib, g)

                s_uab = .5 * (1 - smoothed + 1e-200)
                s_uba = .5 * (1 + smoothed + 1e-200)
                pbecke[ia] *= s_uab
                pbecke[ib] *= s_uba
                pt_uab =-t_uab / s_uab
                pt_uba = t_uab / s_uba

# * When grid is on atom ia/ib, ua/ub == 0, d_uba/d_uab may have huge error
#   How to remove this error?
                duab = get_du(ia, ib)
                duba = get_du(ib, ia)
                if ia == atom_id:
                    dpbecke[ia,ia] += pt_uab * duba
                    dpbecke[ia,ib] += pt_uba * duba
                else:
                    dpbecke[ia,ia] += pt_uab * duab
                    dpbecke[ia,ib] += pt_uba * duab

                if ib == atom_id:
                    dpbecke[ib,ib] -= pt_uba * duab
                    dpbecke[ib,ia] -= pt_uab * duab
                else:
                    dpbecke[ib,ib] -= pt_uba * duba
                    dpbecke[ib,ia] -= pt_uab * duba

# * JCP 98, 5612 (1993); (B8) (B10) miss many terms
                if ia != atom_id and ib != atom_id:
                    ua_ub = grid_norm_vec[ia] - grid_norm_vec[ib]
                    ua_ub /= atm_dist[ia,ib]
                    dpbecke[atom_id,ia] -= pt_uab * ua_ub
                    dpbecke[atom_id,ib] -= pt_uba * ua_ub

        for ia in range(mol.natm):
            dpbecke[:,ia] *= pbecke[ia]

        return pbecke, dpbecke

    natm = mol.natm
    for ia in range(natm):
        atomic_coords, atomic_vol = atom_grids_tab[mol.atom_symbol(ia)]
        offset = 0
        while offset < len(atomic_coords):
            block = grid_block_size(len(atomic_coords)-offset, nao=nao, derivative=2,
                maximum_memory_mb=ni.memory_megabytes, alignment=numint.BLKSIZE,
                requested_size=ni.response_block_limit, response_atoms=natm, observe=ni.observe)
            end = min(offset+block, len(atomic_coords))
            coords = atomic_coords[offset:end] + atm_coords[ia]
            vol = atomic_vol[offset:end]
            pbecke, dpbecke = gen_grid_partition(coords, ia)
            z = 1./pbecke.sum(axis=0)
            w1 = dpbecke[:,ia] * z
            w1 -= pbecke[ia] * z**2 * dpbecke.sum(axis=1)
            w1 *= vol
            w0 = vol * pbecke[ia] * z
            # Do not retain the atom-pair tensor during AO evaluation.
            del pbecke, dpbecke, z
            yield ia, coords, w0, w1
            del coords, vol, w0, w1
            offset = end



def get_vxc_full_response(ni, mol, grids, xc_code, dms, *, unrestricted):
    """The upstream RKS/UKS GGA contractions, with both response terms intact."""
    if ni._xc_type(xc_code) != 'GGA' or grids.becke_scheme not in (
            gen_grid.original_becke, gen_grid.stratmann):
        raise ValueError('bounded reference gradient requires GGA and supported Becke partitioning')
    make_rho, nset, nao = ni._gen_rho_evaluator(mol, dms, 1, False, grids)
    if nset != (2 if unrestricted else 1):
        raise ValueError('reference gradient changes the complete selected spin-density denominator')
    ao_loc = mol.ao_loc_nr()
    excsum = numpy.zeros((mol.natm, 3))
    vmat = numpy.zeros((2, 3, nao, nao) if unrestricted else (3, nao, nao))
    for atm_id, coords, weight, weight1 in grids_response_becke(grids, ni, int(nao)):
        mask = gen_grid.make_mask(mol, coords)
        ao = ni.eval_ao(mol, coords, deriv=2, non0tab=mask, cutoff=grids.cutoff)
        if unrestricted:
            rho_a = make_rho(0, ao[:4], mask, 'GGA')
            rho_b = make_rho(1, ao[:4], mask, 'GGA')
            exc, vxc = ni.eval_xc_eff(xc_code, (rho_a, rho_b), 1, xctype='GGA')[:2]
            wv = weight * vxc
            wv[:, 0] *= .5
            excsum += numpy.einsum('r,r,nxr->nx', exc, rho_a[0]+rho_b[0], weight1)
            for spin in range(2):
                vtmp = numpy.zeros((3, nao, nao))
                rks_grad._gga_grad_sum_(vtmp, mol, ao, wv[spin], mask, ao_loc)
                vmat[spin] += vtmp
                excsum[atm_id] += numpy.einsum('xij,ji->x', vtmp, dms[spin])*2
                del vtmp
            del rho_a, rho_b
        else:
            rho = make_rho(0, ao[:4], mask, 'GGA')
            exc, vxc = ni.eval_xc_eff(xc_code, rho, 1, xctype='GGA')[:2]
            wv = weight * vxc
            wv[0] *= .5
            vtmp = numpy.zeros((3, nao, nao))
            rks_grad._gga_grad_sum_(vtmp, mol, ao, wv, mask, ao_loc)
            vmat += vtmp
            excsum += numpy.einsum('r,r,nxr->nx', exc, rho[0], weight1)
            excsum[atm_id] += numpy.einsum('xij,ji->x', vtmp, dms)*2
            del vtmp, rho
        del ao, mask, exc, vxc, wv, coords, weight, weight1
    return excsum, -vmat


def _get_veff(ks_grad, mol=None, dm=None):
    """Preserve the upstream hybrid/range-separated J/K and tagged grid force."""
    if mol is None:
        mol = ks_grad.mol
    mf = ks_grad.base
    if dm is None:
        dm = mf.make_rdm1()
    if not ks_grad.grid_response or mf.do_nlc() or mf.xc.lower() != 'wb97x':
        raise ValueError('bounded reference derivative requires full grid response for selected wB97X')
    grids, _ = rks_grad._initialize_grids(ks_grad)
    ni = mf._numint
    unrestricted = ks_grad._rubisco_unrestricted
    ni.observe(dict(event='dft-full-grid-response-entry'))
    exc, vxc = get_vxc_full_response(ni, mol, grids, mf.xc, dm, unrestricted=unrestricted)
    ni.observe(dict(event='dft-full-grid-response-return'))
    omega, alpha, hyb = ni.rsh_and_hybrid_coeff(mf.xc, spin=mol.spin)
    vj, vk = ks_grad.get_jk(mol, dm)
    vk *= hyb
    if omega != 0:
        vk += ks_grad.get_k(mol, dm, omega=omega)*(alpha-hyb)
    vxc += vj[0]+vj[1]-vk if unrestricted else vj-vk*.5
    ni.observe(dict(event='dft-gradient-coulomb-exchange-return'))
    return lib.tag_array(vxc, exc1_grid=exc)


def bind_bounded_gradient(derivative, *, unrestricted):
    """Bind only this derivative instance; retain periodic QM/MM methods."""
    if type(derivative.base._numint) is not MemoryBoundedNumInt or type(unrestricted) is not bool:
        raise ValueError('bounded gradient requires its selected bounded integration instance and spin flavour')
    derivative._rubisco_unrestricted = unrestricted
    derivative.get_veff = MethodType(_get_veff, derivative)
    return derivative
