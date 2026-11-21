# SPDX-License-Identifier: MPL-2.0
"""Original-format clean implementation source custody for post-hoc freezes."""
import subprocess
from hashlib import sha256
from pathlib import Path
from empirical_lawhood.science.records.serialization import validate_relative_locator


def repository_head(repository_root: Path) -> str:
    return subprocess.check_output(
        ("git", "rev-parse", "HEAD"),
        cwd=repository_root,
        text=True,
    ).strip()



def implementation_source_closure(
    repository_root: Path, implementation_files: tuple[str, ...]
) -> dict[str, object]:
    rows = []
    accumulator = sha256()
    if not implementation_files or len(set(implementation_files)) != len(implementation_files):
        raise ValueError("post-hoc implementation source roster is empty or duplicated")
    repository_root = repository_root.resolve(strict=True)
    status = subprocess.run(
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    if status:
        raise PermissionError("post-hoc freeze requires a clean source commit")
    for relative in implementation_files:
        validate_relative_locator(relative)
        path = repository_root / relative
        if path.is_symlink() or not path.resolve(strict=False).is_relative_to(repository_root):
            raise PermissionError("post-hoc implementation source escapes target")
        if not path.is_file():
            raise ValueError(f"implementation source is absent: {relative}")
        payload = path.read_bytes()
        digest = sha256(payload).hexdigest()
        accumulator.update(relative.encode("utf-8"))
        accumulator.update(b"\0")
        accumulator.update(bytes.fromhex(digest))
        rows.append({"relative_path": relative, "sha256": digest, "size_bytes": len(payload)})
    return {
        "schema": 'empirical-lawhood/methods/posthoc-response-composition/implementation-source-closure',
        "version": "1.0.0",
        "value": {
            "base_commit": repository_head(repository_root),
            "implementation_sha256": accumulator.hexdigest(),
            "source_files": rows,
        },
    }

