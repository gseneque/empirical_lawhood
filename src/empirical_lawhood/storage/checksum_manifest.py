# SPDX-License-Identifier: MPL-2.0
"""Decode an independently selected SHA256SUMS roster before opening its members."""

from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
import os
from threading import get_ident
from types import MappingProxyType

from empirical_lawhood.science.records.serialization import (
    validate_relative_locator,
    validate_sha256,
)


def checksum_manifest(raw: bytes, expected_sha256: str) -> dict[str, str]:
    if type(raw) is not bytes or sha256(raw).hexdigest() != validate_sha256(
        expected_sha256
    ):
        raise ValueError("selected original return differs from its checksum manifest")
    entries = {}
    for line in raw.decode("utf-8").splitlines():
        digest, name = line.split("  ", 1)
        name = validate_relative_locator(name.removeprefix("./"))
        if name in entries:
            raise ValueError("original return manifest duplicates a source")
        entries[name] = validate_sha256(digest)
    if not entries:
        raise ValueError("original return manifest has no source members")
    return entries


@contextmanager
def selected_checksum_members(root, expected_sha256):
    """Read named original return bytes and verify every consumed path again on exit."""
    from empirical_lawhood.storage.bounded_io import read_bounded_bytes
    from empirical_lawhood.storage.file_census import FileHashCensus
    from empirical_lawhood.storage.native_installation import real_path

    root = real_path(root)
    name = "SHA256SUMS"
    raw = read_bounded_bytes(real_path(root / name), maximum_bytes=16 * 1024**2)
    roster = checksum_manifest(raw, expected_sha256)
    consumed = {name: expected_sha256}
    context = ContextVar("selected_checksum_members")
    token = context.set(True)
    owner = os.getpid(), get_ident()
    active = True

    def original(name, *, claimed=None):
        nonlocal token
        if not active or owner != (os.getpid(), get_ident()):
            raise RuntimeError("original return reads require their active owner")
        # A copied Context inherits values but cannot reset another Context's token.
        try:
            context.reset(token)
        except ValueError as error:
            raise RuntimeError(
                "original return reads require their owning context"
            ) from error
        token = context.set(True)
        if name not in roster or (claimed is not None and roster[name] != claimed):
            raise ValueError(
                f"the original return and selected member disagree for {name}"
            )
        consumed[name] = roster[name]
        data = read_bounded_bytes(real_path(root / name), maximum_bytes=256 * 1024**2)
        if sha256(data).hexdigest() != roster[name]:
            raise ValueError(f"original return member changed for {name}")
        return data

    try:
        yield MappingProxyType(roster), original, MappingProxyType(consumed)
    finally:
        active = False
        context.reset(token)
        with FileHashCensus() as census:
            for name, expected in consumed.items():
                if (
                    census.sha256(real_path(root / name), maximum_bytes=None)[1]
                    != expected
                ):
                    raise ValueError(
                        f"original return member changed during consumption for {name}"
                    )
