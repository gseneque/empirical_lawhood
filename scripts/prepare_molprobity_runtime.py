# SPDX-License-Identifier: MPL-2.0
"""Install the chemistry tables and authenticate a fresh, locked local CCTBX prefix."""

import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
from zipfile import ZipFile

import pyarrow as pa

from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_runtime import (
    CHEM_DATA_SHA256, DATA_SELECTION, LOCK_SHA256, RECEIPT, VERSION, runtime_inventory, verify_runtime,
)
from empirical_lawhood.storage.bounded_io import bounded_file_sha256


COMPONENTS = set("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL "
                 "CAP KCX RUB MG HOH WAT NA CL".split())
TABLES = {"mon_lib", "rotarama_data", "rotamer_chi_angles", "cablam_data", "rama_z", "amino_acid_resources"}
COMPONENT_FILES = {f"data_{component}.cif" for component in COMPONENTS}


@contextmanager
def conda_tar(package, part):
    if package.name.endswith(".tar.bz2"):
        with tarfile.open(package, "r:bz2") as tar:
            yield tar
        return
    with ZipFile(package) as archive:
        member, = (name for name in archive.namelist() if name.startswith(part + "-") and name.endswith(".tar.zst"))
        with archive.open(member) as raw, pa.CompressedInputStream(raw, "zstd") as stream:
            with tarfile.open(fileobj=stream, mode="r|") as tar:
                yield tar


def safe_path(name):
    rel = PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts or rel.as_posix() != name or "\\" in name:
        raise ValueError("unexpected archive path: " + name)
    return rel


def chemistry_member(name):
    parts = safe_path(name).parts
    if parts[:2] != ("site-packages", "chem_data") or len(parts) < 3:
        return False
    if len(parts) == 3:
        return parts[2] == "__init__.py"
    if parts[2] in TABLES:
        return True
    if parts[2] in {"geostd", "chemical_components"}:
        # Single-letter/digit directories are monomer stores. CCTBX loads
        # global link definitions, including RNA links, even for pure protein.
        return len(parts[3]) != 1 or parts[-1] in COMPONENT_FILES
    return False


def copy_member(tar, member, dest):
    if not member.isfile():
        raise ValueError("selected archive member must be a regular file: " + member.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tar.extractfile(member) as src, dest.open("xb") as out:
        shutil.copyfileobj(src, out, length=2**20)


def notices(package, destination, *, chem=False):
    selection = None
    with conda_tar(package, "info") as tar:
        for m in tar:
            if m.isfile() and (m.name.startswith("info/licenses/") or m.name == "info/about.json"):
                copy_member(tar, m, destination / safe_path(m.name))
            elif chem and m.name == "info/paths.json":
                selection = {r["_path"]: r["sha256"] for r in json.load(tar.extractfile(m))["paths"]
                             if chemistry_member(r["_path"])}
    return selection


def authenticated_packages(prefix, cache, lock):
    raw = lock.read_bytes()
    if sha256(raw).hexdigest() != LOCK_SHA256:
        raise ValueError("the selected CCTBX binary distribution lock differs")
    expected = dict(line.rsplit("#", 1) for line in raw.decode().splitlines() if line.startswith("https://"))
    seen = set()
    for path in sorted((prefix / "conda-meta").glob("*.json")):
        record = json.loads(path.read_bytes())
        url = record["url"]
        if url in seen or url not in expected or expected[url] != record["sha256"]:
            raise ValueError("installed conda transaction differs from the selected lock")
        seen.add(url)
        original = Path(record["link"]["source"]).parent / record["fn"]
        if not original.resolve(strict=True).is_relative_to(cache) or bounded_file_sha256(
                original, maximum_bytes=None)[1] != expected[url]:
            raise ValueError("conda package cache differs from its selected original: " + str(original))
        for entry in record["paths_data"]["paths"]:
            kind = entry["path_type"]
            member = prefix / safe_path(entry["_path"])
            if not member.resolve(strict=True).is_relative_to(prefix):
                raise ValueError("installed distribution member escapes its selected prefix")
            if kind == "softlink" and member.is_symlink() and member.is_dir():
                continue
            if kind in {"softlink", "hardlink"}:
                expected_file = entry["sha256_in_prefix"]
                if (kind == "softlink") != member.is_symlink():
                    raise ValueError("installed file differs from its locked package transaction: " + entry["_path"])
                if bounded_file_sha256(member.resolve(strict=True), maximum_bytes=None)[1] != expected_file:
                    # Install-time Python can recompile stock .pyc files after linking.
                    # Restore only an unrelocated package bytecode member, by digest.
                    stock = Path(record["link"]["source"]) / safe_path(entry["_path"])
                    if (kind != "hardlink" or member.suffix != ".pyc" or entry.get("sha256") != expected_file
                            or not stock.resolve(strict=True).is_relative_to(cache)
                            or bounded_file_sha256(stock, maximum_bytes=None)[1] != expected_file):
                        raise ValueError("installed file differs from its locked package transaction: " + entry["_path"])
                    with tempfile.NamedTemporaryFile(dir=member.parent, delete=False) as tmp:
                        replacement = Path(tmp.name)
                    try:
                        shutil.copy2(stock, replacement)
                        if bounded_file_sha256(replacement, maximum_bytes=None)[1] != expected_file:
                            raise ValueError("package bytecode changed during restore")
                        os.replace(replacement, member)
                    finally:
                        replacement.unlink(missing_ok=True)
        yield record, original
    if seen != set(expected):
        raise ValueError("incomplete conda package selection")


def prepare(prefix, cache, lock, chemistry):
    if (not prefix.is_absolute() or prefix.resolve(strict=True) != prefix or (prefix / RECEIPT).exists()
            or not (prefix / "bin/python").is_file()):
        raise ValueError("select the new, real, unsealed CCTBX installation")
    if bounded_file_sha256(chemistry, maximum_bytes=None)[1] != CHEM_DATA_SHA256:
        raise ValueError("original CCTBX chem_data distribution differs")
    cache = cache.resolve(strict=True)
    packages = list(authenticated_packages(prefix, cache, lock))
    site = prefix / "lib/python3.11/site-packages"
    data = site / "chem_data"
    licenses = prefix / "share/molprobity-notices"
    # Existing directories can be a prior incomplete preparation; authenticate
    # stock tables against the original package again before sealing.
    with tempfile.TemporaryDirectory(dir=prefix) as tmp:
        root = Path(tmp)
        docs = root / "notices"
        for record, original in packages:
            notices(original, docs / record["name"])
        selected = notices(chemistry, docs / "chem_data", chem=True)
        if not selected or not (docs / "chem_data/info/licenses").is_dir() or not (docs / "cctbx-base/info/licenses").is_dir():
            raise ValueError("incomplete reference data or upstream license evidence")
        if not licenses.exists():
            docs.rename(licenses)
        else:
            for f in docs.rglob("*"):
                if f.is_file() and bounded_file_sha256(licenses/f.relative_to(docs), maximum_bytes=None) != bounded_file_sha256(f, maximum_bytes=None):
                    raise ValueError("installed notices differ from the verified originals")
        if not data.exists():
            seen = set()
            with conda_tar(chemistry, "pkg") as tar:
                for m in tar:
                    if m.name in selected:
                        copy_member(tar, m, root / safe_path(m.name))
                        seen.add(m.name)
            if seen != set(selected):
                raise ValueError("selected reference tables missing from the original archive")
            (root / "site-packages/chem_data").rename(data)
        for name, expected in selected.items():
            member = site / PurePosixPath(name).relative_to("site-packages")
            if bounded_file_sha256(member, maximum_bytes=None)[1] != expected:
                raise ValueError("installed reference table differs from the original: " + name)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    for program in ("rebuild_rotarama_cache", "rebuild_cablam_cache"):
        subprocess.run([prefix / "bin/python", "-I", "-B", "-m", "mmtbx.command_line." + program],
                       cwd=prefix, env=env, check=True)
    for directory, pattern in [("rotarama_data", "rota8000-*.pickle"), ("cablam_data", "*.pickle")]:
        if not any((data / directory).glob(pattern)):
            raise ValueError("CCTBX did not build required original lookup tables in " + directory)
    receipt = dict(schema="empirical-lawhood/molprobity-runtime-installation/v1", prefix=str(prefix),
                   lock_sha256=LOCK_SHA256, chem_data_sha256=CHEM_DATA_SHA256, cctbx_version=VERSION,
                   reference_selection=DATA_SELECTION,
                   distribution_packages=len(packages), selected_chemical_data_files=len(selected),
                   inventory=runtime_inventory(prefix))
    raw = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    with (prefix / RECEIPT).open("xb") as f:
        f.write(raw)
    return verify_runtime(prefix, receipt_sha256=sha256(raw).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--package-cache", type=Path, required=True)
    parser.add_argument("--chem-data", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.prefix, args.package_cache, args.lock, args.chem_data), sort_keys=True))


if __name__ == "__main__":
    main()
