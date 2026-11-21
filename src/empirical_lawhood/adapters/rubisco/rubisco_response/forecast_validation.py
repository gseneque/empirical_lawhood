# SPDX-License-Identifier: MPL-2.0
"""Project each exact observed-core endpoint for the retained local diagnostics."""

from collections import Counter
import json
from pathlib import Path
import resource
import time

from .forecast_core import LSU, SSU, digest, observed_residues, write_json
from .forecast_conditioning import load_system
from . import kcx_backbone_driver, molprobity_driver
from .molprobity_runtime import run_validation_driver, verify_runtime
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import (
    COMPONENTS,
    protected,
    report_atom_name,
    write_projection,
)


def project(build, conditioned, destination):
    import numpy as np

    manifest, native, _ = load_system(build)
    target = json.loads((conditioned / "conditioned.json").read_text())
    if target["build_sha256"] != digest(build / "built.json") or target[
        "final_sha256"
    ] != digest(conditioned / "final.npz"):
        raise ValueError("Changed native endpoint")
    with np.load(conditioned / "final.npz", allow_pickle=False) as arrays:
        xyz = np.asarray(arrays["coordinates_A"], dtype="<f8", order="C")
        box = arrays["box_A"]
        if (
            not np.isfinite(xyz).all()
            or xyz.shape != (native.topology.getNumAtoms(), 3)
            or not np.allclose(np.diag(np.diag(box)), box)
        ):
            raise ValueError("Incomplete or mismatched snapshot")
    inputs = observed_residues((build / "library-heavy.pdb").read_text())
    positions = Counter()
    native_names = native._prmtop.getAtomNames()
    rows, atoms = [], []
    for res in native.topology.residues():
        ri = res.index
        raw_name = native._prmtop.getResidueLabel(iRes=ri)
        comp = COMPONENTS.get(raw_name, raw_name)
        if ri < len(inputs):
            (chain, author, insertion, original), _ = inputs[ri]
            if COMPONENTS.get(original, original) != comp:
                raise ValueError(f"Input and Amber residues disagree at {ri}")
            role = {"MG": "MAGNESIUM", "RUB": "LIGAND"}.get(comp, "PROTEIN")
            if role == "PROTEIN":
                positions[chain] += 1
                pos = positions[chain] + (14 if chain in LSU else 0)
                site = (
                    f"site.{chain}" if chain in LSU and pos in (210, 212, 213) else None
                )
                labels = protected(chain, "LSU" if chain in LSU else "SSU", pos, site)
                loc = pos
            else:
                pos, site, loc = (
                    None,
                    f"site.{chain}",
                    500 if role == "MAGNESIUM" else 501,
                )
                labels = [site]
        else:
            chain = f"w{(ri - len(inputs)) // 9000}"
            loc = (ri - len(inputs)) % 9000 + 1
            author, insertion, pos, site, labels = None, "", None, None, []
            role = "WATER" if comp == "HOH" else "ION"
        rows.append(
            dict(
                id=f"residue.{ri + 1}",
                chain=chain,
                seq=loc,
                component=comp,
                original_component=raw_name,
                original_chain=chain if ri < len(inputs) else None,
                original_number=author,
                original_insertion=insertion,
                role=role,
                chain_id=chain if role == "PROTEIN" else None,
                site=site,
                critical=labels,
                position=pos,
                chain_length=(493 if chain in LSU else 138)
                if role == "PROTEIN"
                else None,
            )
        )
        atoms.extend(
            [
                ri,
                report_atom_name(raw_name, native_names[a.index]),
                a.element.symbol.upper(),
            ]
            for a in res.atoms()
        )
    if any(positions[c] != 472 for c in LSU) or any(positions[c] != 138 for c in SSU):
        raise ValueError("Cut-core sequence mapping differs")
    edges = ((a.index, b.index) for a, b in native.topology.bonds())
    return {
        "case": manifest["case"],
        "build_sha256": digest(build / "built.json"),
        "final_sha256": target["final_sha256"],
        **write_projection(
            destination,
            rows,
            atoms,
            edges,
            xyz.tobytes(),
            np.diag(box).tolist() + [90] * 3,
            [f"site.{c}" for c in LSU],
            native_names=native_names,
        ),
    }


def validate(build, conditioned, destination, prefix, pin):
    start = time.monotonic()
    destination.mkdir(exist_ok=False)
    engine = verify_runtime(prefix, receipt_sha256=pin)
    export = project(build, conditioned, destination)
    write_json(destination / "export.json", export)
    stages = []
    try:
        for source, output in (
            (molprobity_driver, destination),
            (kcx_backbone_driver, destination / "supplement.json"),
        ):
            t = time.monotonic()
            ret = run_validation_driver(engine, Path(source.__file__).resolve(), destination, output,
                                        work_directory=destination, log_path=destination / (source.__name__.split(".")[-1] + ".log"),
                                        locale="C")
            stages.append(
                {
                    "driver": Path(source.__file__).name,
                    "sha256": digest(source.__file__),
                    "returncode": ret.returncode,
                    "wall_s": time.monotonic() - t,
                }
            )
    finally:
        if engine != verify_runtime(prefix, receipt_sha256=pin):
            raise ValueError("Validator was changed while in use")
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    write_json(
        destination / "validation.json",
        {
            "case": export["case"],
            "export_sha256": digest(destination / "export.json"),
            "engine": engine,
            "stages": stages,
            "wall_s": time.monotonic() - start,
            "child_cpu_s": usage.ru_stime + usage.ru_utime,
        },
    )
