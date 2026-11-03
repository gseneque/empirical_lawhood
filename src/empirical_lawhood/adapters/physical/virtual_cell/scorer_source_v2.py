# SPDX-License-Identifier: MPL-2.0
"""Authenticate the selected installed scorer against its original public source.

The original MetricContract digest identifies the 33,122-byte v0.6.6 GitHub
source archive, not one installed module. Its 26 package files are byte-identical
to the retained PyPI 0.6.6 wheel. This fixed census authenticates software only.
"""

import ast
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import distribution
from importlib.util import MAGIC_NUMBER, cache_from_source, find_spec, resolve_name
from io import BytesIO
import marshal
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import CodeType, FunctionType, ModuleType

from .contracts import MetricContract, VirtualCellContractError

SOURCE_ARCHIVE_SHA256 = (
    "799adf3a40103fe74457887f207c5552aea9c9d81d06295c69926664a19bb011"
)
# Original support manifest: 0fe1b03212d664417ecec8239ed0987439a5706feb682271a29e63b6d7fedaa2.
# Original wheel SHA256: fcf72a07fb08c696695d678b29b027807460bcf91bce831eb055360d997e29d4.
SCORER_SOURCE_FILES_V2 = (
    (
        "cell_eval/__init__.py",
        820,
        "c50bcc93efa4912cf3903d2b1fa2bbafa2952b9aee0ec56a23d5192dcdd55da1",
    ),
    (
        "cell_eval/__main__.py",
        987,
        "629ba99c398150583509f250410ff2a1a359fd34d10d413133dcd9d9cd414e87",
    ),
    (
        "cell_eval/_baseline.py",
        6042,
        "95cc800f6bfb8cee0309dd90ffbf3654d1aa22616cb11d88b5df8e4563bbbd21",
    ),
    (
        "cell_eval/_cli/__init__.py",
        385,
        "9f1a99c83b8938d079b90ac88326f81b7137e9f92203d18bac883c55b484ec12",
    ),
    (
        "cell_eval/_cli/_baseline.py",
        2858,
        "eb3887dd6a4df83637a23cae16e8f1711f015067f8bf7beeb268e04107e30fad",
    ),
    (
        "cell_eval/_cli/_const.py",
        203,
        "f116f30eb9205d829d9d9e6b87b38007952cfc3b32c433e4a4a1e356f69274d2",
    ),
    (
        "cell_eval/_cli/_prep.py",
        9044,
        "a22236b2822895c28b60efe4c5f73d3726ae2685e4d72bdff84b5bf07b8eee8d",
    ),
    (
        "cell_eval/_cli/_run.py",
        6284,
        "42687b61ad4ceb199c0e5e9d34d279cf7e3685bae1a4d4a1b9a2c443321b30df",
    ),
    (
        "cell_eval/_cli/_score.py",
        1072,
        "f88ba43d18a256993bd2ba46fe55ef09a2f5ad1edc6e965fb569ebf70abed160",
    ),
    (
        "cell_eval/_evaluator.py",
        12256,
        "20ec34e78d75d8a89734c8f8be4b5b13f93cf4af2769238e901bfb2250f3490a",
    ),
    (
        "cell_eval/_pipeline/__init__.py",
        100,
        "7442e73b4849df83d8b7c33f3c3539a02e9dc6118f456fbfd4f65217cc283f7d",
    ),
    (
        "cell_eval/_pipeline/_runner.py",
        8282,
        "ac0ade7e53eb7a6dc06552e1831eead69d8388073e430eb4bebe5c4a038fc8d3",
    ),
    (
        "cell_eval/_score.py",
        4294,
        "a67ddf39a225e3be7fb04754236e19fb41fc2053a6de28eca856609627796f53",
    ),
    (
        "cell_eval/_types/__init__.py",
        403,
        "5ca704cadbab67e497ee49248492146bc54bb15fb57a3557757000c19c71efe2",
    ),
    (
        "cell_eval/_types/_anndata.py",
        11237,
        "e073ae7eadd775903b51b41f1c0fbce99f5e4bba57c5ef3151721af2efaf9a30",
    ),
    (
        "cell_eval/_types/_de.py",
        9593,
        "3ae904529b16f93ab9c16561d55895748c5ad1ee180611f87596d50c920f07bf",
    ),
    (
        "cell_eval/_types/_enums.py",
        758,
        "d3c679f54863e6740685c1ce0b211065495614ddb2acd8ed9eb8146b9c96949e",
    ),
    (
        "cell_eval/data.py",
        2112,
        "f6f35a3ad2769dd25b0e3f444a621be71952978f54d095b4cd618d32d4fddaf2",
    ),
    (
        "cell_eval/metrics/__init__.py",
        982,
        "90a493d4b59b3894f2a95eebd67804133af0945a89651623476f5ee7474fa520",
    ),
    (
        "cell_eval/metrics/_anndata.py",
        11460,
        "fa0a450ba486ac5c77e93aa383038cf723b6d2b4368e42f9b61add52220bf7d8",
    ),
    (
        "cell_eval/metrics/_de.py",
        8354,
        "2a1d98367724d06ee62e7764156c54e9a9b2e6a7723b0d37970e720c7f391a25",
    ),
    (
        "cell_eval/metrics/_impl.py",
        4685,
        "97c0ceb17f47b547da4c564893bc955782b8ef3e5953a316220c284992192040",
    ),
    (
        "cell_eval/metrics/_registry.py",
        4101,
        "d043d00616db2622fb3605c083b596193dfcf13812b7894d84767269c451ce04",
    ),
    (
        "cell_eval/metrics/base.py",
        1123,
        "986a471f5e335fb678c950494934e129c2170a0d65aeb3f0ada2f97b8214db61",
    ),
    (
        "cell_eval/py.typed",
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ),
    (
        "cell_eval/utils.py",
        3574,
        "0ba490caecbab8bbacf8739ba63b3b7be0871e166259f2a44a8145e1479d7f19",
    ),
)


@dataclass(frozen=True, slots=True)
class ScorerSourceAuthenticationV2:
    archive_sha256: str
    package_root: Path
    files: tuple[tuple[str, int, str], ...]


class ScorerSourceUnavailable(VirtualCellContractError):
    reason_code = "VIRTUAL_CELL_V2_SCORER_SOURCE_UNAUTHENTICATED"


def require_selected_scorer_contract_v2(contract):
    if type(contract) is not MetricContract:
        raise TypeError(
            "scorer source authentication requires the original typed metric contract"
        )
    contract.__post_init__()
    if (
        contract.scorer_distribution,
        contract.scorer_version,
        contract.scorer_source_sha256,
    ) != ("cell-eval", "0.6.6", SOURCE_ARCHIVE_SHA256):
        raise ScorerSourceUnavailable(
            "SOFTWARE: selected scorer changes the original pinned official source archive"
        )


def _read_file(path, size):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        selected = os.fstat(descriptor)
        if not stat.S_ISREG(selected.st_mode) or selected.st_size != size:
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: installed scorer source changes exact file type or size"
            )
        chunks = []
        total = 0
        while chunk := os.read(descriptor, min(65536, size + 1 - total)):
            total += len(chunk)
            if total > size:
                raise ScorerSourceUnavailable(
                    "ENVIRONMENT: installed scorer source exceeds its exact bound"
                )
            chunks.append(chunk)
        after = os.fstat(descriptor)
        stable = lambda value: (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )
        if total != size or stable(after) != stable(selected):
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: installed scorer source changed during authentication"
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _require_source_bytecode(path, source):
    # Python can execute unchecked-hash or timestamp caches without reading the
    # source. Authenticate their actual code, including otherwise valid headers.
    for optimization in ("", "1", "2"):
        cache = Path(cache_from_source(str(path), optimization=optimization))
        if not cache.exists():
            continue
        size = cache.stat().st_size
        if size > 1024 * 1024:
            raise ScorerSourceUnavailable("ENVIRONMENT: scorer bytecode exceeds its bound")
        data = _read_file(cache, size)
        if (
            len(data) < 16
            or data[:4] != MAGIC_NUMBER
            or int.from_bytes(data[4:8], "little") not in (0, 1, 3)
        ):
            raise ScorerSourceUnavailable("ENVIRONMENT: scorer bytecode header is invalid")
        stream = BytesIO(data[16:])
        try:
            code = marshal.load(stream)
        except (EOFError, ValueError, TypeError) as error:
            raise ScorerSourceUnavailable("ENVIRONMENT: scorer bytecode is invalid") from error
        expected = compile(source, str(path), "exec", optimize=int(optimization or 0))
        # Code equality compares nested instructions/constants while allowing a
        # legitimate cache to have been compiled at another installation path.
        if not isinstance(code, CodeType) or code != expected or stream.read(1):
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: scorer bytecode differs from authenticated source"
            )


def _module_name(name):
    parts = PurePosixPath(name).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _require_loaded_source(package, sources):
    modules = {
        _module_name(name): (package / PurePosixPath(name).relative_to("cell_eval"), data)
        for name, data in sources.items()
        if name.endswith(".py")
    }
    for name, module in tuple(sys.modules.items()):
        if name != "cell_eval" and not name.startswith("cell_eval."):
            continue
        selected = modules.get(name)
        origin = getattr(module, "__file__", None)
        if (
            selected is None
            or type(module) is not ModuleType
            or origin is None
            or Path(origin).resolve(strict=True) != selected[0]
        ):
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: loaded scorer module differs from authenticated module ownership"
            )
        path, source = selected
        code = compile(source, str(path), "exec", optimize=sys.flags.optimize)
        codes = {}

        def collect(value):
            codes[value.co_qualname] = value
            for item in value.co_consts:
                if isinstance(item, CodeType):
                    collect(item)

        collect(code)
        namespace = vars(module)
        tree = ast.parse(source)

        def require_function(value, qualified):
            if (
                type(value) is not FunctionType
                or value.__globals__ is not namespace
                or value.__code__ != codes.get(qualified)
            ):
                raise ScorerSourceUnavailable(
                    "ENVIRONMENT: loaded scorer definition differs from authenticated source"
                )

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                require_function(namespace.get(node.name), node.name)
            elif isinstance(node, ast.ClassDef):
                value = namespace.get(node.name)
                if not isinstance(value, type) or value.__module__ != name:
                    raise ScorerSourceUnavailable(
                        "ENVIRONMENT: loaded scorer class differs from authenticated source"
                    )
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method = vars(value).get(member.name)
                        if isinstance(method, (staticmethod, classmethod)):
                            method = method.__func__
                        require_function(method, node.name + "." + member.name)
            elif isinstance(node, ast.ImportFrom):
                # Re-exported evaluator classes/functions must remain the exact
                # objects from their authenticated defining sibling module.
                if node.level:
                    base = name if path.name == "__init__.py" else name.rpartition(".")[0]
                    imported = resolve_name("." * node.level + (node.module or ""), base)
                else:
                    imported = node.module or ""
                if imported == "cell_eval" or imported.startswith("cell_eval."):
                    owner = sys.modules.get(imported)
                    for alias in node.names:
                        if (
                            alias.name == "*"
                            or owner is None
                            or namespace.get(alias.asname or alias.name)
                            is not vars(owner).get(alias.name)
                        ):
                            raise ScorerSourceUnavailable(
                                "ENVIRONMENT: loaded scorer re-export differs from authenticated source"
                            )


def authenticate_installed_scorer_source_v2(contract):
    require_selected_scorer_contract_v2(contract)
    try:
        selected = distribution("cell-eval")
        if selected.version != "0.6.6" or selected.files is None:
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: installed scorer lacks exact distribution ownership"
            )
        expected = {
            name: (size, digest) for name, size, digest in SCORER_SOURCE_FILES_V2
        }
        owned = {}
        for member in selected.files:
            name = str(member)
            if not name.startswith("cell_eval/"):
                continue
            relative = PurePosixPath(name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or str(relative) != name
                or name in owned
            ):
                raise ScorerSourceUnavailable(
                    "ENVIRONMENT: installed scorer aliases package ownership paths"
                )
            if "__pycache__" in relative.parts and relative.suffix == ".pyc":
                continue
            owned[name] = Path(selected.locate_file(member))
        if set(owned) != set(expected):
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: installed scorer changes the complete 26-file source census"
            )
        package = Path(selected.locate_file("cell_eval"))
        if package.is_symlink() or not package.is_dir():
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: installed scorer package root is not a regular directory"
            )
        package = package.resolve(strict=True)
        actual = set()
        for path in package.rglob("*"):
            if path.is_symlink():
                raise ScorerSourceUnavailable(
                    "ENVIRONMENT: installed scorer contains a source symlink"
                )
            if path.is_file() and not (
                "__pycache__" in path.relative_to(package).parts
                and path.suffix == ".pyc"
            ):
                actual.add("cell_eval/" + path.relative_to(package).as_posix())
        if actual != set(expected):
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: installed scorer contains unowned or missing package sources"
            )
        sources = {}
        for name, (size, digest) in expected.items():
            path = owned[name]
            exact = package / PurePosixPath(name).relative_to("cell_eval")
            data = _read_file(path, size)
            if (
                path.is_symlink()
                or path.resolve(strict=True) != exact
                or sha256(data).hexdigest() != digest
            ):
                raise ScorerSourceUnavailable(
                    "ENVIRONMENT: installed scorer differs from the original pinned package bytes"
                )
            sources[name] = data
            if name.endswith(".py"):
                _require_source_bytecode(path, data)
        specification = find_spec("cell_eval")
        if (
            specification is None
            or specification.origin is None
            or Path(specification.origin).resolve(strict=True)
            != package / "__init__.py"
            or tuple(
                Path(value).resolve(strict=True)
                for value in specification.submodule_search_locations or ()
            )
            != (package,)
        ):
            raise ScorerSourceUnavailable(
                "ENVIRONMENT: actual scorer import origin differs from its authenticated distribution"
            )
        _require_loaded_source(package, sources)
        return ScorerSourceAuthenticationV2(
            SOURCE_ARCHIVE_SHA256, package, SCORER_SOURCE_FILES_V2
        )
    except ScorerSourceUnavailable:
        raise
    except (OSError, ValueError, ImportError) as error:
        raise ScorerSourceUnavailable(
            "ENVIRONMENT: exact installed scorer source is unavailable"
        ) from error
