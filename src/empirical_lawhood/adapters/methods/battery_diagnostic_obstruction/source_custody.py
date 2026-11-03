# SPDX-License-Identifier: MPL-2.0
"""Reauthenticate original obstruction custody without native contact or copies."""

from hashlib import sha256
import json

from empirical_lawhood.infrastructure.artifacts import GuardedExternalRoot
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from . import science
from .experiment_specification import AuthenticatedObstructionConfig


def _verify_member(root, member):
    path = root.resolve(member.relative_path, for_write=False)
    if bounded_file_sha256(path, maximum_bytes=member.size_bytes) != (member.size_bytes, member.sha256):
        raise ValueError("obstruction original custody member changes its exact size or SHA256: " + member.relative_path)


def _read_member(root, member):
    raw = read_bounded_bytes(root.resolve(member.relative_path, for_write=False), maximum_bytes=member.size_bytes)
    if (len(raw), sha256(raw).hexdigest()) != (member.size_bytes, member.sha256):
        raise ValueError("obstruction original report or cost changes its exact bytes")
    return raw


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("obstruction original report duplicates a custody field")
        result[key] = value
    return result


def authenticate_source_custody(config):
    """Check every original primary member and the current UNKNOWN obstruction.

    No previous successful check is cached across authoring, retained reads or
    execution. A returned diagnostic receipt/result requires reassessment;
    an old UNKNOWN projection cannot hide that changed primary state.
    """
    if type(config) is not AuthenticatedObstructionConfig:
        raise TypeError("obstruction custody requires its exact authenticated operation config")
    config.__post_init__()
    source = config.source
    primary = science.validate_source(source)
    selected = config.custody
    root = GuardedExternalRoot(selected.storage)
    root.verify(for_write=False)
    for member in source.complete_custody:
        _verify_member(root, member)
    report = json.loads(_read_member(root, selected.report), object_pairs_hook=_unique_pairs)
    expected = {row.relative_path: {"bytes": row.size_bytes, "sha256": row.sha256} for row in source.complete_custody}
    actual = report.get("custody_members") if type(report) is dict else None
    if (type(actual) is not dict or set(actual) != set(expected)
            or any(type(row) is not dict or set(row) != {"bytes", "sha256"}
                or type(row["bytes"]) is not int or type(row["sha256"]) is not str
                or row != expected[path] for path, row in actual.items())):
        raise ValueError("obstruction original final report changes its complete custody census")
    if _read_member(root, selected.cost) != source.invocation_cost_raw_utf8.encode():
        raise ValueError("obstruction original complete invocation cost bytes differ")
    receipt = primary["index"].tasks[0].attempts[0].receipt_relative_path
    outputs = tuple(row.relative_path for row in primary["plan"].tasks[0].outputs)
    absent = (receipt, receipt + ".manifest.json", *(path for output in outputs for path in (output, output + ".manifest.json")))
    for relative in absent:
        if root.resolve(relative, for_write=False).exists():
            raise ValueError("obstruction original completion state changed; authenticate the returned result instead of preserving UNKNOWN")
    contact = next(row.relative_path for row in source.records if row.role == "contact")
    directory = root.resolve(contact, for_write=False).parent
    contacts = tuple(sorted(path.name for path in directory.iterdir()
        if path.name.endswith(".json") and not path.name.endswith(".manifest.json")))
    if contacts != (contact.rsplit("/", 1)[-1],):
        raise ValueError("obstruction original native contact census changed")


def authenticate_registered_source_custody(plane, config_inputs):
    """Registered premise; the separately selected original guarded root owns I/O."""
    del plane
    seen = set()
    for row in config_inputs:
        config = row.record
        if type(config) is not AuthenticatedObstructionConfig:
            raise TypeError("obstruction publication substitutes its exact authenticated configuration")
        config.__post_init__()
        key = (config.custody.identity, config.scientific.fingerprint())
        if key not in seen:
            authenticate_source_custody(config)
            seen.add(key)
