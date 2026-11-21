# SPDX-License-Identifier: MPL-2.0
"""Selected compiled double pair kernel with deterministic full force reduction."""
from concurrent.futures import ThreadPoolExecutor
import ctypes
import math
from pathlib import Path

import numpy as np

from empirical_lawhood.adapters.rubisco.rubisco_response.fixed_coordinate_mm import COULOMB_KJ_NM_PER_MOL_E2


class CompiledMobileNonbonded:
    def __init__(self, parameters, movable, exclusions, *, library, threads=1, block_rows=32):
        if any(isinstance(i,(bool,np.bool_)) or not isinstance(i,(int,np.integer)) for i in movable):
            raise ValueError("compiled movable indices must be exact integers")
        self.parameters = np.asarray(parameters,dtype=np.float64).copy()
        self.movable = np.asarray(movable,dtype=np.int64)
        self.threads, self.block_rows = threads, block_rows
        n = len(self.parameters)
        if (self.parameters.shape != (n,3) or not n or not np.isfinite(self.parameters).all()
                or np.any(self.parameters[:,1:] < 0) or not len(self.movable)
                or tuple(self.movable) != tuple(sorted(set(self.movable)))
                or self.movable[0] < 0 or self.movable[-1] >= n
                or type(threads) is not int or threads < 1
                or type(block_rows) is not int or block_rows < 1):
            raise ValueError("double nonbonded evaluation requires complete finite pair parameters and selection")
        self.movable = np.ascontiguousarray(self.movable)
        self.movable.setflags(write=False)
        self.q,self.sigma,self.sqrt_epsilon=(np.ascontiguousarray(v) for v in (
            self.parameters[:,0],self.parameters[:,1],np.sqrt(self.parameters[:,2])))
        self.is_moving=np.zeros(n,dtype=np.uint8);self.is_moving[self.movable]=1
        neighbours = {i:set() for i in self.movable}
        seen=set()
        for a,b in exclusions:
            pair=tuple(sorted((a,b)))
            if (any(isinstance(i,(bool,np.bool_)) or not isinstance(i,(int,np.integer)) for i in (a,b))
                    or a == b or pair in seen or min(a,b) < 0 or max(a,b) >= n):
                raise ValueError("double nonbonded evaluation has an invalid exception pair census")
            seen.add(pair)
            if a in neighbours:neighbours[a].add(b)
            if b in neighbours:neighbours[b].add(a)
        offsets=[0];flat=[]
        for i in self.movable:
            flat.extend(sorted(neighbours[i]));offsets.append(len(flat))
        self.offsets=np.array(offsets,dtype=np.int64)
        self.excluded=np.array(flat,dtype=np.int64)
        for values in (self.parameters,self.q,self.sigma,self.sqrt_epsilon,self.is_moving,self.offsets,self.excluded):
            values.setflags(write=False)
        library=Path(library)
        if library.is_symlink() or library.resolve()!=library or not library.is_file():
            raise ValueError("compiled double kernel requires its exact selected regular library")
        self.library=ctypes.CDLL(str(library))
        self.kernel=self.library.rubisco_mobile_pairs
        i64=np.ctypeslib.ndpointer(dtype=np.int64,ndim=1,flags='C_CONTIGUOUS')
        u8=np.ctypeslib.ndpointer(dtype=np.uint8,ndim=1,flags='C_CONTIGUOUS')
        f64=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS')
        self.kernel.argtypes=[ctypes.c_int64,ctypes.c_int64,ctypes.c_int64,i64,u8,i64,i64,
                              f64,f64,f64,f64,ctypes.c_double,ctypes.POINTER(ctypes.c_double),f64]
        self.kernel.restype=ctypes.c_int

    @classmethod
    def from_projected_system(cls, system, movable, **kwargs):
        import openmm as mm
        expression = (f"{COULOMB_KJ_NM_PER_MOL_E2!r}*q1*q2/r+4*epsilon*((sigma/r)^12-(sigma/r)^6);"
                      "sigma=(sigma1+sigma2)/2;epsilon=sqrt(epsilon1*epsilon2)")
        matches=[f for f in system.getForces() if type(f) is mm.CustomNonbondedForce]
        if len(matches)!=1:
            raise ValueError("double nonbonded mapping requires exactly one projected pair force")
        force=matches[0];n=system.getNumParticles()
        if (force.getEnergyFunction()!=expression or force.getNumParticles()!=n
                or force.getNumPerParticleParameters()!=3
                or [force.getPerParticleParameterName(i) for i in range(3)]!=["q","sigma","epsilon"]
                or force.getNonbondedMethod()!=mm.CustomNonbondedForce.NoCutoff
                or force.getUseLongRangeCorrection() or force.getNumGlobalParameters()
                or force.getNumEnergyParameterDerivatives() or force.getNumTabulatedFunctions()
                or force.getNumInteractionGroups()!=1
                or tuple(map(set,force.getInteractionGroupParameters(0)))!=(set(movable),set(range(n)))):
            raise ValueError("double nonbonded mapping refuses different pair semantics")
        return cls([force.getParticleParameters(i) for i in range(n)],movable,
                   [force.getExclusionParticles(i) for i in range(force.getNumExclusions())],**kwargs)

    def _block(self,xyz,start):
        forces=np.zeros_like(xyz)
        energy=ctypes.c_double()
        code=self.kernel(len(xyz),start,min(start+self.block_rows,len(self.movable)),self.movable,
            self.is_moving,self.offsets,self.excluded,xyz.reshape(-1),self.q,self.sigma,self.sqrt_epsilon,
            COULOMB_KJ_NM_PER_MOL_E2,ctypes.byref(energy),forces.reshape(-1))
        if code:
            raise ValueError(f"original compiled double pair potential is singular or nonfinite (code {code})")
        return energy.value,forces

    def __call__(self,coordinates_nm):
        xyz=np.ascontiguousarray(coordinates_nm,dtype=np.float64)
        if xyz.shape!=self.parameters.shape or not np.isfinite(xyz).all():
            raise ValueError("double nonbonded evaluation requires every finite Cartesian coordinate")
        energy,forces=0.0,np.zeros_like(xyz)
        starts=range(0,len(self.movable),self.block_rows)
        if self.threads==1:
            for start in starts:
                e,f=self._block(xyz,start);energy+=e;forces+=f
        else:
            with ThreadPoolExecutor(max_workers=self.threads) as pool:
                for e,f in pool.map(lambda start:self._block(xyz,start),starts):
                    energy+=e;forces+=f
        if not math.isfinite(energy) or not np.isfinite(forces).all():
            raise ValueError("original compiled double pair potential is nonfinite")
        return energy,forces
