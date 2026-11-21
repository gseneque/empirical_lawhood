# SPDX-License-Identifier: MPL-2.0
"""Pure selection of complete scientific construction engine closures."""
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id

NUMERIC_PACKAGES = ("OpenMM.libs", "numpy", "numpy.libs", "openmm", "scipy", "scipy.libs")
CONSTRUCTION_PACKAGES = (*NUMERIC_PACKAGES, "pdbfixer")
COMPILED_PACKAGE = "rubisco_native"
COMPILED_FILES = ("build.json", "lib_mobile_pairs.so", "mobile_pairs.c")


def validate_construction_platform(platform, threads):
    """CPU kernels are the construction default; Reference is a serial oracle.

    GPU construction is not admitted by this selection: the coupled operator's
    pinned PME guards remain separate and unchanged.
    """
    if (platform not in ("CPU", "Reference") or type(threads) is not int or not 1 <= threads <= 8
            or (platform == "Reference" and threads != 1)):
        raise ValueError("construction requires CPU with 1–8 threads or serial Reference")


def _absolute(value):
    path = PurePosixPath(value)
    if not path.is_absolute() or str(path) != value or ".." in path.parts:
        raise ValueError("geometry repair requires an exact absolute selected path")


@dataclass(frozen=True, slots=True)
class GpRepairNumericEngine(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-repair-numeric-engine"
    engine_id: str
    site_packages: str
    files: tuple[FileEvidence, ...]
    interpreter: str
    interpreter_sha256: str

    def __post_init__(self):
        validate_stable_id(self.engine_id)
        _absolute(self.site_packages)
        _absolute(self.interpreter)
        if (type(self.files) is not tuple or not self.files
                or tuple(r.relative_path for r in self.files) != tuple(sorted({r.relative_path for r in self.files}))
                or {PurePosixPath(r.relative_path).parts[0] for r in self.files}
                    not in (set(NUMERIC_PACKAGES), set(CONSTRUCTION_PACKAGES), set(NUMERIC_PACKAGES)|{COMPILED_PACKAGE})
                or len(self.interpreter_sha256) != 64
                or any(c not in "0123456789abcdef" for c in self.interpreter_sha256)):
            raise ValueError("geometry repair loses its complete numerical package/interpreter selection")
        for row in self.files:exact(row,FileEvidence)
        compiled=tuple(row.relative_path for row in self.files if row.relative_path.startswith(COMPILED_PACKAGE+"/"))
        if compiled and compiled!=tuple(COMPILED_PACKAGE+"/"+name for name in COMPILED_FILES):
            raise ValueError("compiled geometry kernel loses its complete source, build and binary selection")

    @property
    def compiled_mobile(self):
        return any(row.relative_path.startswith(COMPILED_PACKAGE+"/") for row in self.files)


