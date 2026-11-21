# SPDX-License-Identifier: MPL-2.0
"""Authenticate the separately installed CCTBX distribution and reference tables."""

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import subprocess

from empirical_lawhood.storage.bounded_io import bounded_file_sha256, read_bounded_bytes


LOCK_SHA256 = "b3f8d7c5e34f50d9d74f2b2222ca073525b9317761fac155caec9fa537553a8c"
CHEM_DATA_SHA256 = "16aa7bd57b53918135fa9c6002417933fbe15f9f185332508d11bc534f1d2d27"
VERSION = "2026.10"
DATA_SELECTION = "gp-components-and-global-geostd-links-v2"
RECEIPT = "molprobity-installation.json"


def runtime_inventory(prefix):
    """Hash every installed member, including data, library links and modes."""
    prefix = Path(prefix)
    if not prefix.is_absolute() or prefix.resolve(strict=True) != prefix or not prefix.is_dir():
        raise ValueError("MolProbity requires its selected absolute installation directory")
    summary = sha256()
    count = size = 0

    def traversal_failure(error):
        raise error

    for base, dirs, files in os.walk(prefix, followlinks=False, onerror=traversal_failure):
        dirs.sort()
        for name in sorted([*dirs, *files]):
            path = Path(base) / name
            relative = path.relative_to(prefix).as_posix()
            if relative == RECEIPT:
                continue
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                link = os.readlink(path)
                if os.path.isabs(link) or not path.resolve(strict=True).is_relative_to(prefix):
                    raise ValueError(f"external or dangling MolProbity runtime link: {relative}")
                content = link
            elif stat.S_ISREG(mode):
                length, content = bounded_file_sha256(path, maximum_bytes=None)
                size += length
            elif stat.S_ISDIR(mode):
                content = None
            else:
                raise ValueError(f"unexpected special member in MolProbity runtime: {relative}")
            summary.update(json.dumps([relative, mode, content], separators=(",", ":")).encode() + b"\n")
            count += 1
    return dict(tree_sha256=summary.hexdigest(), member_count=count, regular_file_bytes=size)


def verify_runtime(prefix, *, receipt_sha256):
    """Bind the actual program and data to the operator's original install receipt."""
    prefix = Path(prefix)
    raw = read_bounded_bytes(prefix / RECEIPT, maximum_bytes=2**15)
    if sha256(raw).hexdigest() != receipt_sha256:
        raise ValueError("MolProbity installation receipt differs from its selected SHA-256")
    receipt = json.loads(raw)
    if (receipt.get("schema") != "empirical-lawhood/molprobity-runtime-installation/v1"
            or receipt.get("prefix") != str(prefix) or receipt.get("lock_sha256") != LOCK_SHA256
            or receipt.get("chem_data_sha256") != CHEM_DATA_SHA256 or receipt.get("cctbx_version") != VERSION
            or receipt.get("reference_selection") != DATA_SELECTION
            or receipt.get("inventory") != runtime_inventory(prefix)):
        raise ValueError("MolProbity executable, reference data or installed runtime closure differs")
    return dict(python=str(prefix/"bin"/"python"), receipt_sha256=receipt_sha256,
                lock_sha256=LOCK_SHA256, cctbx_version=VERSION)


def run_validation_driver(engine, driver, material_directory, output, *, work_directory, log_path,
                          restraints=(), timeout=None, check=False, locale=None):
    """Run an isolated CCTBX driver on the selected CIF and atom map with explicit native outputs."""
    interpreter = Path(engine["python"])
    env = {key: value for key, value in os.environ.items() if key in {"LANG", "LC_ALL", "LC_CTYPE", "TZ"}}
    if locale is not None:
        env = {"LC_ALL": locale}
    env.update(PATH=str(interpreter.parent) + os.pathsep + os.defpath, HOME=str(work_directory),
               TMPDIR=str(work_directory), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    command = [str(interpreter), "-I", "-B", str(driver), str(material_directory / "model.cif"),
               str(material_directory / "atom-map.json"), str(output), *map(str, restraints)]
    with log_path.open("xb") as log:
        return subprocess.run(command, cwd=work_directory, env=env, stdout=log,
                              stderr=subprocess.STDOUT, timeout=timeout, check=check)
