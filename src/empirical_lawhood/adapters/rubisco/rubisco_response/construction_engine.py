# SPDX-License-Identifier: MPL-2.0
"""Authenticate native construction package bytes and loaded module origins."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import file_chunks
from empirical_lawhood.domains.rubisco.rubisco_response import construction_engine as contract_owner
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import GpRepairNumericEngine, COMPILED_PACKAGE
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

def authenticate_numeric_engine(engine, *, loaded=False):
    """Authenticate complete selected package directories and actual import origins."""
    import sys
    exact(engine,GpRepairNumericEngine)
    root = Path(engine.site_packages)
    if root.is_symlink() or root.resolve() != root or Path(sys.executable).resolve() != Path(engine.interpreter):
        raise ValueError("geometry repair changes its selected numerical environment")
    if sha256(Path(engine.interpreter).read_bytes()).hexdigest() != engine.interpreter_sha256:
        raise ValueError("geometry repair interpreter bytes changed")
    actual = []
    for name in sorted({PurePosixPath(row.relative_path).parts[0] for row in engine.files}):
        if (root/name).is_symlink() or not (root/name).is_dir():
            raise ValueError("geometry repair numerical package root changed")
        for path in (root/name).rglob("*"):
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError("geometry repair numerical packages contain an undeclared link or special member")
            if path.is_file():actual.append(path.relative_to(root).as_posix())
    if tuple(sorted(actual)) != tuple(r.relative_path for r in engine.files):
        raise ValueError("geometry repair numerical package file census changed")
    for row in engine.files:
        for _ in file_chunks(root/row.relative_path,expected=row):pass
    if engine.compiled_mobile:
        selected=root/COMPILED_PACKAGE
        if (selected/"mobile_pairs.c").read_bytes()!=Path(contract_owner.__file__).with_name("mobile_pairs.c").read_bytes():
            raise ValueError("selected compiled geometry kernel source differs from the producing implementation")
        build=json.loads((selected/"build.json").read_bytes())
        if (build.get("exit_code")!=0
                or build.get("source_sha256")!=sha256((selected/"mobile_pairs.c").read_bytes()).hexdigest()
                or build.get("library_sha256")!=sha256((selected/"lib_mobile_pairs.so").read_bytes()).hexdigest()):
            raise ValueError("selected compiled geometry kernel loses its original successful build binding")
    if loaded:
        from empirical_lawhood.adapters.rubisco.rubisco_insilico_dynamics.durable_native_entry import authenticate_loaded_engine_modules
        inventory = {"entries":[dict(kind="file",actual_path=str(root/r.relative_path),
            size=r.byte_count,sha256=r.sha256) for r in engine.files]}
        return authenticate_loaded_engine_modules(inventory)
    return ()


