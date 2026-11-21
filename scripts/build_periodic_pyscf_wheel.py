# SPDX-License-Identifier: MPL-2.0
"""Build the repository's CPU periodic J/K allocator in a fresh, source-bound PySCF wheel."""

import argparse
import base64
import csv
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from empirical_lawhood.domains.rubisco.rubisco_response.pyscf_cvhf_allocation import (
    patch_complete_output_cache,
)
from empirical_lawhood.storage.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.storage.native_installation import real_path


SOURCE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "configs/native/pyscf-cvhf-2.14.0-linux-x86_64.json"
)
OLD_INFO = "pyscf-2.14.0.dist-info"
LIBRARY = "pyscf/lib/libcvhf.so"
PATCHED_SOURCE = "pyscf/lib/vhf/nr_direct.c"


def compile_library(extracted, compiler):
    lib = extracted / "pyscf/lib"
    vhf = lib / "vhf"
    declarations = (vhf / "CMakeLists.txt").read_text()
    target = re.search(r"add_library\(cvhf SHARED\s+([^()]+)\)", declarations)
    if target is None:
        raise ValueError("upstream CVHF source declaration missing")
    objects = []
    compile_flags = [
        "-std=gnu99",
        "-O3",
        "-DNDEBUG",
        "-fPIC",
        "-fopenmp",
        "-msse3",
        "-I",
        str(lib),
        "-I",
        str(lib / "deps/include"),
        "-I",
        str(vhf),
    ]
    for name in target[1].split():
        if Path(name).name != name or not name.endswith(".c"):
            raise ValueError("invalid member in the upstream CVHF source declaration")
        obj = extracted / Path(name).with_suffix(".o")
        subprocess.run(
            [compiler, *compile_flags, "-c", vhf / name, "-o", obj], check=True
        )
        objects.append(obj)
    # Use the BLAS, integral and OpenMP implementations distributed in this wheel.
    # Adding -fopenmp at link time would introduce the compiler's own OpenMP runtime.
    dependencies = [
        "libcgto.so",
        "libnp_helper.so",
        "libcint.so",
        "libopenblas-r0-f650aae0.3.3.so",
        "libgomp-a34b3233.so.1.0.0",
    ]
    rpath = "$ORIGIN:$ORIGIN/deps/lib:$ORIGIN/deps/lib64:$ORIGIN/."
    binary = extracted / LIBRARY
    subprocess.run(
        [
            compiler,
            "-shared",
            "-Wl,-z,defs",
            "-Wl,-soname,libcvhf.so",
            "-Wl,--disable-new-dtags,-rpath," + rpath,
            "-L",
            lib,
            "-L",
            lib / "deps/lib",
            *objects,
            *("-l:" + d for d in dependencies),
            "-lm",
            "-lpthread",
            "-o",
            binary,
        ],
        check=True,
    )
    return {
        "sources": [obj.with_suffix(".c").name for obj in objects],
        "compile_flags": [v.replace(str(extracted) + "/", "") for v in compile_flags],
        "wheel_runtime_libraries": {
            d: bounded_file_sha256(
                lib / d if (lib / d).is_file() else lib / "deps/lib" / d,
                maximum_bytes=None,
            )[1]
            for d in dependencies
        },
        "rpath": rpath,
        "library_sha256": bounded_file_sha256(binary, maximum_bytes=None)[1],
    }


def repack(source, inputs, output, manifest):
    new_info = "pyscf-" + manifest["local_version"] + ".dist-info"
    record_name = new_info + "/RECORD"
    metadata = source.read(OLD_INFO + "/METADATA")
    if metadata.count(b"\nVersion: 2.14.0\n") != 1:
        raise ValueError("upstream wheel has unexpected version metadata")
    replacements = {
        LIBRARY: (inputs / LIBRARY).read_bytes(),
        PATCHED_SOURCE: (inputs / PATCHED_SOURCE).read_bytes(),
        OLD_INFO + "/METADATA": metadata.replace(
            b"\nVersion: 2.14.0\n", f"\nVersion: {manifest['local_version']}\n".encode()
        ),
        OLD_INFO + "/WHEEL": (
            "Wheel-Version: 1.0\nGenerator: Empirical Lawhood\nRoot-Is-Purelib: false\n"
            f"Tag: {manifest['wheel_tag']}\n"
        ).encode(),
    }
    entries = []
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as wheel:
        for original in source.infolist():
            name = original.filename
            if original.is_dir() or name == OLD_INFO + "/RECORD":
                continue
            target = (
                new_info + name[len(OLD_INFO) :]
                if name.startswith(OLD_INFO + "/")
                else name
            )
            data = replacements[name] if name in replacements else source.read(original)
            encoded = (
                base64.urlsafe_b64encode(sha256(data).digest())
                .decode("ascii")
                .rstrip("=")
            )
            entries.append((target, "sha256=" + encoded, str(len(data))))
            info = ZipInfo(target, date_time=original.date_time)
            info.external_attr = original.external_attr
            wheel.writestr(info, data, compress_type=ZIP_DEFLATED)
        buffer = StringIO(newline="")
        csv.writer(buffer, lineterminator="\n").writerows(
            [*entries, (record_name, "", "")]
        )
        wheel.writestr(
            ZipInfo(
                record_name, date_time=source.getinfo(OLD_INFO + "/RECORD").date_time
            ),
            buffer.getvalue(),
            compress_type=ZIP_DEFLATED,
        )


def build(wheel, destination, scratch, compiler):
    if (platform.system(), platform.machine()) != ("Linux", "x86_64"):
        raise ValueError("this source selection requires Linux x86_64")
    manifest = json.loads(SOURCE_MANIFEST.read_bytes())
    wheel, destination, scratch = map(real_path, (wheel, destination, scratch))
    compiler = Path(compiler).resolve(strict=True)
    if destination.exists() or not scratch.is_dir() or not compiler.is_file():
        raise ValueError(
            "select a fresh output, an existing scratch parent and a C compiler"
        )
    buf = read_bounded_bytes(wheel, maximum_bytes=manifest["size_bytes"])
    if (
        len(buf) != manifest["size_bytes"]
        or sha256(buf).hexdigest() != manifest["sha256"]
    ):
        raise ValueError(
            "CVHF build requires the exact PySCF wheel selected in uv.lock"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        TemporaryDirectory(dir=scratch) as temp,
        TemporaryDirectory(dir=destination.parent) as staging,
    ):
        tree = Path(temp)
        release = Path(staging) / "build"
        release.mkdir()
        with ZipFile(BytesIO(buf)) as source:
            for info in source.infolist():
                if info.filename.startswith("pyscf/lib/"):
                    source.extract(info, tree)
            target = tree / PATCHED_SOURCE
            if (
                sha256(target.read_bytes()).hexdigest()
                != manifest["upstream_c_source_sha256"]
            ):
                raise ValueError("upstream CVHF C source identity changed")
            target.write_bytes(patch_complete_output_cache(target.read_bytes()))
            if (
                sha256(target.read_bytes()).hexdigest()
                != manifest["patched_c_source_sha256"]
            ):
                raise ValueError("CVHF allocator correction identity changed")
            report = compile_library(tree, compiler)
            name = f"pyscf-{manifest['local_version']}-{manifest['wheel_tag']}.whl"
            repack(source, tree, release / name, manifest)
        report.update(
            source_manifest_sha256=sha256(SOURCE_MANIFEST.read_bytes()).hexdigest(),
            upstream_wheel_sha256=manifest["sha256"],
            patched_c_source_sha256=manifest["patched_c_source_sha256"],
            compiler=str(compiler),
            compiler_sha256=bounded_file_sha256(compiler, maximum_bytes=None)[1],
            compiler_version=subprocess.check_output(
                [compiler, "--version"], text=True
            ).splitlines()[0],
            wheel=name,
            wheel_sha256=bounded_file_sha256(release / name, maximum_bytes=None)[1],
        )
        (release / "build.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        if destination.exists():
            raise FileExistsError(destination)
        release.rename(destination)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-wheel", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, default=shutil.which("gcc"))
    args = parser.parse_args()
    if args.compiler is None:
        parser.error("select an installed GNU C compiler")
    print(
        json.dumps(
            build(args.upstream_wheel, args.destination, args.scratch, args.compiler),
            sort_keys=True,
            indent=2,
        )
    )
