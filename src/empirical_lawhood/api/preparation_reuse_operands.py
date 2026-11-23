# SPDX-License-Identifier: MPL-2.0
"""Lossless transport of the publicly exposed R23–R27 numerical operands."""

from collections.abc import Mapping
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_LZMA, ZipFile, ZipInfo

from empirical_lawhood.domains.matrix.preparation_reuse_manifests import (
    MANIFEST_FORMAT,
    RELEASE_MANIFESTS,
    STUDIES,
    WORKFLOW as WORKFLOW,
)
from empirical_lawhood.science.records.decoding import decode_canonical_bytes


class ReleasedOperands:
    """Read only the fixed members of a checked-in study manifest."""

    def __init__(self, manifest, archive):
        self.context = manifest["context"]
        self.members = manifest["members"]
        self.archive = archive
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(self.members):
            raise ValueError("Released operand census differs from the manifest")

    def raw(self, name):
        info = self.archive.getinfo(name)
        entry = self.members[name]
        if info.file_size != entry["size"]:
            raise ValueError(f"Released operand has a different length: {name}")
        raw = self.archive.read(info)
        if sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError(f"Released operand has a different digest: {name}")
        return raw

    def document(self, name):
        return json.loads(self.raw(name))

    def record(self, name, record_type):
        raw = self.raw(name)
        return decode_canonical_bytes(raw, record_type, maximum_bytes=len(raw))


def _manifest(directory, study):
    if study not in STUDIES:
        raise ValueError("Select one of R23 through R27")
    raw = (directory / f"{study}.json").read_bytes()
    if sha256(raw).hexdigest() != RELEASE_MANIFESTS[study]:
        raise ValueError("The selected manifest differs from the published study")
    manifest = json.loads(raw)
    if manifest["study"] != study or manifest["format"] != MANIFEST_FORMAT:
        raise ValueError("Unexpected released operand manifest")
    return manifest


@contextmanager
def open_released_operands(directory: Path, study: str):
    manifest = _manifest(directory, study)
    with ZipFile(directory / f"{study}.zip") as archive:
        yield ReleasedOperands(manifest, archive)


def rebuild_released_archive(*, directory: Path, study: str, sources: Mapping[str, Path], destination: Path):
    """Rebuild the release from a copy of the already disclosed files, preserving every byte."""
    manifest = _manifest(directory, study)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        staged = Path(temporary) / "archive"
        with ZipFile(staged, "w") as archive:
            for name, entry in sorted(manifest["members"].items()):
                root = sources[entry["source"]].resolve(strict=True)
                path = (root / entry["path"]).resolve(strict=True)
                if not path.is_relative_to(root) or path.stat().st_size != entry["size"]:
                    raise ValueError(f"Source path or length differs for {name}")
                raw = path.read_bytes()
                if sha256(raw).hexdigest() != entry["sha256"]:
                    raise ValueError(f"Source bytes differ for {name}")
                member = ZipInfo(name)
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                codec = ZIP_LZMA if study == "r24" and name.endswith(("/seal", "/reveal")) else ZIP_DEFLATED
                archive.writestr(member, raw, compress_type=codec, compresslevel=6)
        try:
            destination.hardlink_to(staged)
        except FileExistsError:
            with ZipFile(destination) as existing:
                release = ReleasedOperands(manifest, existing)
                for name in release.members:
                    release.raw(name)


def export_recursive_inputs(*, directory: Path, study: str, destination: Path):
    """Export the exact closed study's scientific selections for the recursive workflow."""
    if study not in ("r25", "r26"):
        raise ValueError("Select the waveform or handoff-entry recursive experiment")
    with open_released_operands(directory, study) as data:
        names = ["source-snapshot.json", "specification.json"]
        if study == "r25":
            names.extend(("lower.json", "exposure.json"))
        names.append("sources.json")
        selected = {name: data.raw("recursive/" + name) for name in names}
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in selected.items():
        with (destination / name).open("xb") as stream:
            stream.write(raw)
