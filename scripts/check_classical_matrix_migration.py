# SPDX-License-Identifier: MPL-2.0
"""Compare actual native kernels in two explicitly selected source checkouts.

This bounded migration control is separate from reproduction of a published
study. Both checkouts run in separate processes with the same interpreter,
dependencies, thread limits, physical operands and fixed exposed random seed.
No scientific qualification or equivalence outside this corpus is inferred.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np


CORPUS = r'''
from dataclasses import asdict
from decimal import Decimal as D
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys
import numpy as np
import empirical_lawhood

root, output = map(Path, sys.argv[1:3])
assert Path(empirical_lawhood.__file__).resolve() == root / 'src/empirical_lawhood/__init__.py'
prefix = 'empirical_lawhood.' + ('domains.matrix' if (root/'src/empirical_lawhood/domains/matrix/six_matrix_response').exists() else 'adapters.simulators') + '.six_matrix_response.'
loaded = {name:import_module(prefix+name) for name in ('model','gradients','simulation','contracts','parameter_derivatives')}
model, grad, sim, contract, derivative = (loaded[name] for name in ('model','gradients','simulation','contracts','parameter_derivatives'))
rng = np.random.Generator(np.random.PCG64DXSM(2026111601))
draw = lambda: sim.hermitian_noise(rng=rng, q=2)
q, p, force = .15*draw(), .03*draw(), draw()
force /= np.linalg.norm(force)
directions = [draw() for _ in range(3)]
noise = np.asarray([draw() for _ in range(32)])
arrays = {'initial_q':q, 'initial_p':p, 'force':force, 'noise':noise}
for cross in ('.5','1','2'):
    member = contract.SixMatrixResponseModelFamilyMember('migration.member.'+cross,D('.5'),D('.5'),D(cross),contract.BetaCouplingRule.PUBLISHED_DETERMINISTIC)
    view = contract.SixMatrixResponseNumericalView('migration.primary',contract.MatrixIntegratorKind.BAOAB_UNDERDAMPED_LANGEVIN,D('.001'),'dimensionless-langevin-time',D(1),D(1),contract.MatrixPrecision.COMPLEX128,'numpy.pcg64dxsm','1.0.0','migration.stream',32)
    pars = grad.SixMatrixParameters(2,.5,.5,float(cross),2/3,22/3)
    arrays[cross+'.literal_terms'] = np.asarray(list(asdict(grad.reference_action_terms(q,pars)).values()))
    arrays[cross+'.optimized_terms'] = np.asarray(list(asdict(grad.optimized_action_terms(q,pars)).values()))
    arrays[cross+'.gradient'] = grad.analytic_gradient_terms(q,pars).total
    arrays[cross+'.hessian_actions'] = np.asarray([derivative.hessian_image(q,v,pars) for v in directions])
    for sign in (-1,0,1):
        state = model.SixMatrixState(2,q.copy(),p.copy(),0,2/3,22/3)
        qs, ps = [state.positions], [state.momenta]
        cache = sim.BAOABGradientCache()
        for tick, innovation in enumerate(noise):
            state = derivative.scheduled_force_step(state,direction=force,amplitude=sign*.01 if tick<16 else 0.,member=member,numerical_view=view,next_alpha_tilde_x=2/3,next_alpha_tilde_y=22/3,standardized_noise=innovation,gradient_cache=cache)
            qs.append(state.positions);ps.append(state.momenta)
        arrays[cross+'.'+str(sign)+'.q'] = np.asarray(qs)
        arrays[cross+'.'+str(sign)+'.p'] = np.asarray(ps)
np.savez(output,**arrays)
identity = {name:{'path':str(Path(m.__file__).resolve().relative_to(root)), 'sha256':sha256(Path(m.__file__).read_bytes()).hexdigest()} for name,m in loaded.items()}
print(json.dumps({'python':sys.version.split()[0],'numpy':np.__version__,'package_root':str(root),'modules':identity,'arrays':len(arrays)},sort_keys=True))
'''


def _run(root: Path, destination: Path) -> dict:
    environment = dict(os.environ)
    environment.update(PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    process = subprocess.run(
        [sys.executable, "-c", CORPUS, str(root), str(destination)],
        cwd=root, env=environment, capture_output=True, text=True, timeout=120,
    )
    if process.returncode:
        raise RuntimeError(f"Selected native corpus failed in {root}: {process.stderr[-8000:]}")
    result = json.loads(process.stdout)
    result["commit"] = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    return result


def compare(reference_root: Path, current_root: Path) -> dict:
    rows = []
    with tempfile.TemporaryDirectory(prefix="el-matrix-migration-") as temporary:
        folder = Path(temporary)
        reference = _run(reference_root.resolve(strict=True), folder / "reference.npz")
        current = _run(current_root.resolve(strict=True), folder / "current.npz")
        with np.load(folder / "reference.npz", allow_pickle=False) as left, np.load(folder / "current.npz", allow_pickle=False) as right:
            if set(left.files) != set(right.files):
                raise ValueError("Native control changed its complete output roster")
            for key in sorted(left.files):
                a, b = left[key], right[key]
                if a.shape != b.shape or a.dtype != b.dtype:
                    raise ValueError(f"Native operand contract changed at {key}")
                rows.append({"name":key, "shape":list(a.shape), "dtype":a.dtype.str,
                    "exact_bytes_equal":a.tobytes()==b.tobytes(),
                    "finite":bool(np.isfinite(a).all() and np.isfinite(b).all()),
                    "maximum_absolute_difference":float(np.max(np.abs(a-b))),
                    "reference_sha256":sha256(a.tobytes()).hexdigest(),
                    "current_sha256":sha256(b.tobytes()).hexdigest()})
    return {"schema":"empirical-lawhood/classical-series/migration-control", "version":"1.0.0",
        "status":"PASS" if all(r["exact_bytes_equal"] and r["finite"] for r in rows) else "FAIL",
        "scope":"Exposed native-kernel migration control, not a historical study replay or scientific qualification",
        "corpus":"Three cross couplings; literal/optimized potentials; full96 gradients and Hessian actions; 9 paired/zero 32-step BAOAB branches",
        "reference":reference, "current":current, "arrays":rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = compare(args.reference_root,args.project_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,sort_keys=True,indent=2);stream.write("\n")
    print(json.dumps({"status":report["status"],"arrays":len(report["arrays"]),"output":str(args.output)}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
