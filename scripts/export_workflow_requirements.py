# SPDX-License-Identifier: MPL-2.0
"""Read exact workflow requirements from a selected wheel before installing it.

This stdlib-only tool copies software metadata. It never imports the wheel,
installs packages, opens scientific inputs or executes an external source.
"""

from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile


MAX_WHEEL_BYTES = 512 * 1024**2
PREFIX = "empirical_lawhood/package_data/workflow_installations/"
INDEX = "empirical_lawhood/adapters/composition/generated_installation_manifest.py"


def _wheel_hash(path):
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_WHEEL_BYTES:
        raise ValueError("select a bounded regular wheel file")
    checksum = sha256()
    with path.open("rb") as stream:
        total = 0
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_WHEEL_BYTES:
                raise ValueError("wheel exceeds its byte bound")
            checksum.update(chunk)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) or total != before.st_size:
        raise ValueError("selected wheel changed during inspection")
    return checksum.hexdigest()


def selected_requirements(wheel, *, expected_sha256, workflow_id, profile="standard"):
    wheel = Path(wheel).resolve(strict=True)
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None or _wheel_hash(wheel) != expected_sha256:
        raise ValueError("selected wheel differs from its explicit SHA-256")
    with zipfile.ZipFile(wheel) as archive:
        members = {}
        total = 0
        for member in archive.infolist():
            name = member.filename
            path = PurePosixPath(name)
            kind = stat.S_IFMT(member.external_attr >> 16)
            if (name != member.orig_filename or name in members or path.is_absolute() or "\\" in name
                    or any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))
                    or (member.is_dir() and (kind not in (0, stat.S_IFDIR) or member.file_size))
                    or (not member.is_dir() and kind not in (0, stat.S_IFREG))):
                raise ValueError("wheel member census is duplicated or nonregular")
            total += member.file_size
            if total > MAX_WHEEL_BYTES:
                raise ValueError("wheel expanded contents exceed their byte bound")
            members[name] = member

        def read(name, limit):
            member = members.get(name)
            if member is None or member.is_dir() or member.file_size > limit:
                raise ValueError("wheel omits a bounded required metadata member: " + name)
            with archive.open(member) as stream:
                raw = stream.read(limit + 1)
            if len(raw) != member.file_size or len(raw) > limit:
                raise ValueError("wheel metadata member changes its byte count")
            return raw

        metadata_names = [name for name in members if name.endswith(".dist-info/extra_metadata/source.json")]
        if len(metadata_names) != 1:
            raise ValueError("selected wheel omits unique build-source metadata")
        source_raw = read(metadata_names[0], 8 * 1024**2)
        source = json.loads(source_raw)
        if (source.get("schema") != "empirical-lawhood/build/source" or source.get("version") != "1.0.0"
                or (json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode() != source_raw):
            raise ValueError("wheel build-source metadata changes its canonical contract")
        tracked = {row["relative_path"]: row for row in source["tracked_files"]}
        if len(tracked) != len(source["tracked_files"]):
            raise ValueError("wheel build-source metadata repeats an input")

        def bound(name, limit):
            raw = read(name, limit)
            row = tracked.get("src/" + name)
            if row is None or (row["size_bytes"], row["sha256"]) != (len(raw), sha256(raw).hexdigest()):
                raise ValueError("wheel metadata differs from its build source: " + name)
            return raw

        manifest_raw = bound(PREFIX + "manifest.json", 16 * 1024**2)
        tree = ast.parse(bound(INDEX, 4096))
        assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                       and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id == "MANIFEST_SHA256"]
        if len(assignments) != 1 or ast.literal_eval(assignments[0].value) != sha256(manifest_raw).hexdigest():
            raise ValueError("wheel installation manifest differs from its generated binding")
        manifest = json.loads(manifest_raw)
        if manifest.get("schema") != "empirical-lawhood/software/workflow-installations" or manifest.get("version") != "1.0.0":
            raise ValueError("wheel workflow manifest has an unsupported contract")
        selected = [row for row in manifest["profiles"] if row["declaration"]["workflow_id"] == workflow_id
                    and row["declaration"]["profile_id"] == profile]
        if len(selected) != 1:
            raise ValueError("wheel has no unique selected workflow installation profile")
        selected = selected[0]
        declaration = selected["declaration"]
        roles = {"controller": declaration["controller_environment"],
                 **{row["role_id"]: row["environment_id"] for row in declaration["workers"]}}
        payloads, outputs, source_pins = {}, [], [selected["owner"]]
        for role, identifier in roles.items():
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,191}", role) is None:
                raise ValueError("workflow installation has an unsafe role identifier")
            environment = manifest["environments"][identifier]
            source_pins.extend((environment["project"], environment["lock"]))
            export = environment["requirements_export"]
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*\.requirements\.txt", export["resource"]) is None:
                raise ValueError("workflow installation has an unsafe requirements member")
            raw = bound(PREFIX + export["resource"], 4 * 1024**2)
            if (len(raw), sha256(raw).hexdigest()) != (export["size_bytes"], export["sha256"]):
                raise ValueError("workflow requirements differ from the selected manifest")
            filename = role + ".requirements.txt"
            payloads[filename] = raw
            outputs.append({"role_id": role, "environment_id": identifier, "file": filename,
                "sha256": export["sha256"], "size_bytes": len(raw), "declaration": environment["declaration"]})
        for pin in source_pins:
            row = tracked.get(pin["path"])
            if row is None or (row["size_bytes"], row["sha256"]) != (pin["size_bytes"], pin["sha256"]):
                raise ValueError("workflow requirements change their owning source or lock")
    if _wheel_hash(wheel) != expected_sha256:
        raise ValueError("selected wheel changed during inspection")
    report = {"schema": "empirical-lawhood/software/workflow-requirements-export", "version": "1.0.0",
        "workflow_id": workflow_id, "profile_id": profile, "wheel": str(wheel), "wheel_sha256": expected_sha256,
        "implementation_commit": source["implementation_commit"], "implementation_sha256": source["implementation_sha256"],
        "source_tree_sha256": source["source_tree_sha256"], "source_metadata_sha256": sha256(source_raw).hexdigest(),
        "manifest_sha256": sha256(manifest_raw).hexdigest(), "profile": selected, "requirements": outputs,
        "software_installed": False, "prerequisites_inspected": False, "scientific_authority": "NONE"}
    return report, payloads


def export_requirements(wheel, *, expected_sha256, workflow_id, output_directory, profile="standard"):
    destination = Path(output_directory)
    if (not destination.is_absolute() or destination.resolve() != destination or destination.exists()
            or not destination.parent.is_dir()):
        raise ValueError("select a new absolute output directory beneath an existing regular parent")
    report, payloads = selected_requirements(wheel, expected_sha256=expected_sha256, workflow_id=workflow_id, profile=profile)
    destination.mkdir()
    for name, raw in payloads.items():
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    report["requirements"] = [{**row, "path": str(destination / row["file"])} for row in report["requirements"]]
    report["report_path"] = str(destination / "selection.json")
    with (destination / "selection.json").open("xb") as stream:
        stream.write((json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--profile", default="standard")
    parser.add_argument("--output-directory", required=True, type=Path)
    args = parser.parse_args(argv)
    report = export_requirements(args.wheel, expected_sha256=args.wheel_sha256, workflow_id=args.workflow,
        profile=args.profile, output_directory=args.output_directory)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
