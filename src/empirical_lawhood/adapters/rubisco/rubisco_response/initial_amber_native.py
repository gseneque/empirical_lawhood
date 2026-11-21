# SPDX-License-Identifier: MPL-2.0
"""One registered full-assembly PDBFixer/Amber/OpenMM construction contact."""

import json
from pathlib import Path
import subprocess

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import SourceMember
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import STOCK_NAMES
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def select_gp_amber_parameters(*, members):
    """Freeze the six explicitly pinned original stock files in their owning records."""
    if set(members) != set(STOCK_NAMES):
        raise ValueError("initial Amber parameter selection requires all six stock members")
    result = []
    for name in STOCK_NAMES:
        selected = members[name]
        if set(selected) != {"path", "sha256", "original_url"}:
            raise ValueError("parameter selection requires its exact path, original URL and digest")
        path = Path(selected["path"])
        if not path.is_absolute() or path.is_symlink() or path.resolve() != path:
            raise ValueError("parameter selection requires an absolute real source path")
        raw = read_bounded_bytes(path, maximum_bytes=16 * 2**20)
        result.append(SourceMember("source.gp-initial-amber." + name, selected["original_url"],
            selected["sha256"], raw.decode("utf-8")))
    return tuple(result)


def execute_initial_amber(source, directory):
    from empirical_lawhood.adapters.rubisco.rubisco_response.library_construction import construct_i95m_sidechains, relax_solvated_amber
    from empirical_lawhood.adapters.rubisco.rubisco_response.construction_engine import authenticate_numeric_engine
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import amber_command

    authenticate_numeric_engine(source.numeric_engine)
    models = [model for model in source.models if "initial-gp."+model.name == directory.name]
    if len(models) != 1:
        raise ValueError("native construction cannot identify its selected material")
    model = models[0]
    chains = {row.chain_id for row in model.material.chains if row.subunit == "SSU"}
    mutations = tuple(physical for physical, declared in model.chain_map if declared in chains) if model.name.endswith("i95m") else ()
    heavy, mutation = construct_i95m_sidechains((directory/"complete-heavy.pdb").read_text(), mutations, seed=source.construction_seed,
        platform_name=source.construction_platform, threads=source.construction_threads)
    (directory/"library-heavy.pdb").write_text(heavy)
    (directory/"mutation-construction.json").write_text(json.dumps(mutation, sort_keys=True, indent=2)+"\n")
    engine = Path(source.engine.root)
    stock = engine/"toolchain/dat/leap"
    argv = amber_command(source.engine)
    for part in ("prep", "lib", "parm", "cmd"):
        argv.extend(("-I", str(stock/part)))
    argv.extend(("-f", "build.leap"))
    environment = {"PATH": "/usr/bin:/bin", "AMBERHOME": str(engine/"toolchain"),
        "LD_LIBRARY_PATH": str(engine/source.engine.library_directory), "LC_ALL": "C", "OMP_NUM_THREADS": "1"}
    with (directory/"stdout.txt").open("xb") as out, (directory/"stderr.txt").open("xb") as err:
        completed = subprocess.run(argv, cwd=directory, env=environment, stdin=subprocess.DEVNULL,
            stdout=out, stderr=err, check=True, timeout=source.per_model_timeout_seconds)
    # Parameter failures are native failures; geometric LEaP warnings are
    # preserved and independently resolved only after full molecular repair.
    relax_solvated_amber(source, model, directory)
    authenticate_numeric_engine(source.numeric_engine, loaded=True)
    return completed.returncode, False
