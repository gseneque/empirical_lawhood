# SPDX-License-Identifier: MPL-2.0
"""Temporary construction barriers, zero in the accepted geometry interior.

These are not molecular energy terms. They prevent a preparation optimizer
from crossing the selected stereochemical and trans-peptide domains. Final
acceptance still requires zero barrier and the original Amber force tolerance.
"""

import math
import numpy as np


class GeometryDomainViolation(ValueError):
    """A trial leaves the declared construction domain before native contact."""


class ConstructedGeometryDomain:
    def __init__(self, atom_count, stereocentres, peptides):
        self.atom_count = atom_count
        self.stereocentres = tuple(tuple(row) for row in stereocentres)
        self.peptides = tuple(tuple(row) for row in peptides)
        if type(atom_count) is not int or atom_count < 4 or not self.stereocentres:
            raise ValueError("construction domain needs its complete native atom count and stereocentres")
        for rows in (self.stereocentres, self.peptides):
            if len(set(rows)) != len(rows) or any(len(row) != 4 or len(set(row)) != 4
                    or any(type(i) is not int or not 0 <= i < atom_count for i in row) for row in rows):
                raise ValueError("construction domain has repeated or incomplete atom definitions")
        self.volume_interior_nm3 = 0.001  # 1 Angstrom cubed; determinant, not tetrahedral volume/6.
        self.cosine_boundary = math.cos(math.radians(150))
        self.cosine_interior = math.cos(math.radians(160))
        self.energy_scale_kj_mol = 1.0

    def settings(self):
        return dict(atom_count=self.atom_count, stereocentres=self.stereocentres, peptides=self.peptides,
            volume_interior_nm3=self.volume_interior_nm3, cosine_boundary=self.cosine_boundary,
            cosine_interior=self.cosine_interior, energy_scale_kj_mol=self.energy_scale_kj_mol,
            barrier="s-2+1/s for 0<s<1; exactly zero for s>=1; outside domain for s<=0",
            scope="CONSTRUCTION_ONLY_REQUIRES_ZERO_FINAL_BARRIER_AND_ORIGINAL_AMBER_FORCES")

    def evaluate(self, coordinates_nm):
        xyz = np.asarray(coordinates_nm, dtype=float)
        if xyz.shape != (self.atom_count, 3) or not np.isfinite(xyz).all():
            raise ValueError("construction domain requires complete finite native coordinates")
        gradient = np.zeros_like(xyz)
        energy, stereo_active, peptide_active = 0.0, 0, 0
        minimum_volume, maximum_cosine = math.inf, -math.inf
        for centre, first, second, third in self.stereocentres:
            a, b, c = xyz[[first, second, third]]-xyz[centre]
            volume = float(np.dot(a, np.cross(b, c)))
            minimum_volume = min(minimum_volume, volume)
            s = volume/self.volume_interior_nm3
            if s <= 0:
                raise GeometryDomainViolation("inverted-or-planar-stereocentre")
            if s < 1:
                stereo_active += 1
                energy += self.energy_scale_kj_mol*(s-1)**2/s
                coefficient = self.energy_scale_kj_mol*(1-1/s**2)/self.volume_interior_nm3
                derivatives = np.array([np.cross(b, c), np.cross(c, a), np.cross(a, b)])
                gradient[[first, second, third]] += coefficient*derivatives
                gradient[centre] -= coefficient*derivatives.sum(axis=0)
        width = self.cosine_boundary-self.cosine_interior
        for first, second, third, fourth in self.peptides:
            a, b, c, d = xyz[[first, second, third, fourth]]
            p, q, r = b-a, c-b, d-c
            u, v = np.cross(p, q), np.cross(q, r)
            lu, lv = np.linalg.norm(u), np.linalg.norm(v)
            if min(lu, lv) <= 1e-14:
                raise GeometryDomainViolation("degenerate-peptide-plane")
            cosine = float(np.dot(u, v)/(lu*lv))
            maximum_cosine = max(maximum_cosine, cosine)
            s = (self.cosine_boundary-cosine)/width
            if s <= 0:
                raise GeometryDomainViolation("nonproline-peptide-outside-trans-domain")
            if s < 1:
                peptide_active += 1
                energy += self.energy_scale_kj_mol*(s-1)**2/s
                coefficient = -self.energy_scale_kj_mol*(1-1/s**2)/width
                du = v/(lu*lv)-cosine*u/lu**2
                dv = u/(lu*lv)-cosine*v/lv**2
                dp = np.cross(q, du)
                dq = np.cross(du, p)+np.cross(r, dv)
                dr = np.cross(dv, q)
                gradient[[first, second, third, fourth]] += coefficient*np.array([-dp, dp-dq, dq-dr, dr])
        if not math.isfinite(energy) or not np.isfinite(gradient).all():
            raise ValueError("construction barrier has nonfinite energy or gradient")
        return energy, gradient, dict(active_stereocentres=stereo_active, active_peptides=peptide_active,
            minimum_volume_nm3=minimum_volume, maximum_peptide_cosine=maximum_cosine if self.peptides else None)

    def restrict_step(self, coordinates_nm, movable_indices, direction):
        """Restrict only atoms whose proposed geometry leaves the domain.

        Each local multiplier remains nonnegative. A diagonally scaled steepest
        descent therefore stays a descent direction. The caller must still test
        the actual energy decrease and original force convergence. This filter
        performs no molecular force call and changes no fixed coordinate.
        """
        xyz=np.asarray(coordinates_nm,dtype=float)
        moving=np.asarray(movable_indices,dtype=int)
        original=np.asarray(direction,dtype=float)
        if (xyz.shape!=(self.atom_count,3) or not np.isfinite(xyz).all()
                or moving.ndim!=1 or not len(moving) or tuple(moving)!=tuple(sorted(set(moving)))
                or moving[0]<0 or moving[-1]>=self.atom_count
                or original.shape!=(len(moving),3) or not np.isfinite(original).all()):
            raise ValueError('local geometry proposal loses its complete variables or fixed environment')
        self.evaluate(xyz)
        local=original.copy();scales=np.ones(len(moving));passes=0
        lookup=np.full(self.atom_count,-1,dtype=int);lookup[moving]=np.arange(len(moving))
        stereo=np.asarray(self.stereocentres,dtype=int)
        peptides=np.asarray(self.peptides,dtype=int).reshape((-1,4))
        while True:
            trial=xyz.copy();trial[moving]+=local
            abc=trial[stereo[:,1:]]-trial[stereo[:,0],None,:]
            volumes=np.einsum('ij,ij->i',abc[:,0],np.cross(abc[:,1],abc[:,2]))
            bad_stereo=(volumes<=0)|~np.isfinite(volumes)
            bad_peptide=np.zeros(len(peptides),dtype=bool)
            if len(peptides):
                p=trial[peptides[:,1]]-trial[peptides[:,0]]
                q=trial[peptides[:,2]]-trial[peptides[:,1]]
                r=trial[peptides[:,3]]-trial[peptides[:,2]]
                u,v=np.cross(p,q),np.cross(q,r)
                lu,lv=np.linalg.norm(u,axis=1),np.linalg.norm(v,axis=1)
                with np.errstate(divide='ignore',invalid='ignore'):
                    cosine=np.einsum('ij,ij->i',u,v)/(lu*lv)
                bad_peptide=(np.minimum(lu,lv)<=1e-14)|(cosine>=self.cosine_boundary)|~np.isfinite(cosine)
            bad=np.unique(np.concatenate((stereo[bad_stereo].reshape(-1),peptides[bad_peptide].reshape(-1))))
            if not len(bad):
                try:
                    self.evaluate(trial)
                    break
                except GeometryDomainViolation:
                    # Preserve the exact scalar predicate at a floating-point
                    # boundary where vectorized evaluation differs by an ulp.
                    bad=moving
            selected=lookup[bad];selected=selected[selected>=0]
            if not len(selected):
                raise ValueError('a fixed-only construction constraint changed')
            before=local[selected].copy()
            local[selected]*=.5;scales[selected]*=.5;passes+=1
            if np.array_equal(before,local[selected]):
                raise GeometryDomainViolation('local-construction-proposal-coordinate-resolution')
        return local,dict(local_restriction_passes=passes,
            locally_restricted_atoms=int(np.count_nonzero(scales!=1)),
            minimum_local_step_scale=float(np.min(scales)))


def domain_from_heavy_source(heavy_text, heavy_join, constructed, atom_count):
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
    return domain_from_heavy_rows(heavy_pdb_rows(heavy_text), heavy_join, constructed, atom_count)


def domain_from_heavy_rows(rows, heavy_join, constructed, atom_count):
    """Resolve ordered protein quartets from an already decoded heavy-atom census."""
    joined = dict(heavy_join)
    moving = set(constructed)
    keys = {(a, b, d) for a, b, _, d, _, _ in rows}
    if (len(joined) != len(heavy_join) or set(joined) != keys or not moving <= keys
            or len(set(joined.values())) != len(joined)):
        raise ValueError("construction domain loses the complete source/native heavy correspondence")
    residues = {}
    for chain, position, component, name, _, _ in rows:
        if chain != "Z":
            residues.setdefault((chain, position, component), set()).add(name)
    stereo, peptides, stereo_labels, peptide_labels = [], [], [], []
    by_residue = {(chain, pos): (component, names) for (chain, pos, component), names in residues.items()}
    for (chain, pos, component), names in residues.items():
        definitions = [] if component == "GLY" else [("CA", "N", "C", "CB")]
        if component == "ILE": definitions.append(("CB", "CA", "CG1", "CG2"))
        elif component == "THR": definitions.append(("CB", "CA", "OG1", "CG2"))
        for definition in definitions:
            if not set(definition) <= names:
                raise ValueError("construction domain has an incomplete protein stereocentre")
            selected = tuple((chain, pos, name) for name in definition)
            if moving.intersection(selected):
                stereo.append(tuple(joined[key] for key in selected))
                stereo_labels.append((chain, pos, definition[0]))
        following = by_residue.get((chain, pos+1))
        if following is not None and following[0] != "PRO":
            selected = ((chain, pos, "CA"), (chain, pos, "C"), (chain, pos+1, "N"), (chain, pos+1, "CA"))
            if not set(selected) <= keys:
                raise ValueError("construction domain has an incomplete nonproline peptide")
            if moving.intersection(selected):
                peptides.append(tuple(joined[key] for key in selected))
                peptide_labels.append((chain, pos, pos+1))
    return ConstructedGeometryDomain(atom_count, stereo, peptides), dict(
        stereocentre_labels=stereo_labels, peptide_labels=peptide_labels)
