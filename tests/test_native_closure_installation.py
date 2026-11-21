# SPDX-License-Identifier: MPL-2.0
"""Local installer custody controls; these supply no scientific qualification."""

from hashlib import sha256
import json

import pytest

from empirical_lawhood.storage import native_installation as install


def selection(tmp_path):
    source = tmp_path / "original"
    source.mkdir()
    (source / "tool").write_bytes(b"original executable\n")
    (source / "tool").chmod(0o555)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(dict(schema=install.SCHEMA, version="1.0.0", platform="linux-x86_64",
        executable="tool", files=[dict(path="tool", size_bytes=20, executable=True,
        sha256=sha256(b"original executable\n").hexdigest())])))
    return source, manifest, tmp_path / "installed"


def test_exact_restore_and_existing_destination_refusal(tmp_path):
    source, manifest, destination = selection(tmp_path)
    result = install.restore_closure(manifest_path=manifest, source=source, destination=destination)
    assert result["file_count"] == 1 and not result["upstream_build_reproduced"]
    assert (destination / "tool").read_bytes() == (source / "tool").read_bytes()
    with pytest.raises(ValueError, match="fresh destination"):
        install.restore_closure(manifest_path=manifest, source=source, destination=destination)


@pytest.mark.parametrize("mutation", ("corrupt", "missing", "extra", "symlink", "mode"))
def test_incomplete_or_changed_source_is_refused_before_publication(tmp_path, mutation):
    source, manifest, destination = selection(tmp_path)
    path = source / "tool"
    if mutation == "corrupt":
        path.chmod(0o755); path.write_bytes(b"altered! executable\n")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "extra":
        (source / "extra").write_bytes(b"extra")
    elif mutation == "symlink":
        path.unlink(); path.symlink_to(manifest)
    else:
        path.chmod(0o444)
    with pytest.raises(ValueError):
        install.restore_closure(manifest_path=manifest, source=source, destination=destination)
    assert not destination.exists()


def test_source_mutation_during_copy_and_competing_publication_refuse(tmp_path, monkeypatch):
    source, manifest, destination = selection(tmp_path)
    original = install.shutil.copyfileobj
    def copy_then_mutate(reader, writer, length):
        original(reader, writer, length)
        (source / "extra").write_bytes(b"concurrent source change")
    monkeypatch.setattr(install.shutil, "copyfileobj", copy_then_mutate)
    with pytest.raises(ValueError, match="census"):
        install.restore_closure(manifest_path=manifest, source=source, destination=destination)
    assert not destination.exists()
    (source / "extra").unlink()
    monkeypatch.setattr(install.shutil, "copyfileobj", original)
    publish = install.rename_noreplace
    def compete(staging, target):
        target.mkdir()
        publish(staging, target)
    monkeypatch.setattr(install, "rename_noreplace", compete)
    with pytest.raises(FileExistsError):
        install.restore_closure(manifest_path=manifest, source=source, destination=destination)
    assert list(destination.iterdir()) == []


def test_installed_scope_requires_independent_manifest_pin(tmp_path):
    source, manifest, _ = selection(tmp_path)
    pin = sha256(manifest.read_bytes()).hexdigest()
    with install.verified_native_installation(source, manifest_path=manifest, manifest_sha256=pin) as receipt:
        assert receipt["executable"] == "tool" and receipt["total_bytes"] == 20
    for substituted in (None, "0" * 64):
        with pytest.raises(ValueError, match="manifest"):
            with install.verified_native_installation(source, manifest_path=manifest, manifest_sha256=substituted):
                pytest.fail("different installation was admitted")


@pytest.mark.parametrize("exceptional_exit", [True, False])
def test_installed_scope_rechecks_closure_on_every_exit(tmp_path, exceptional_exit):
    source, manifest, _ = selection(tmp_path)
    pin = sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="census"):
        with install.verified_native_installation(source, manifest_path=manifest, manifest_sha256=pin):
            (source / "extra-library").write_bytes(b"changed during use")
            if exceptional_exit:
                raise ArithmeticError("consumer failed")


def test_installed_scope_rechecks_selected_manifest(tmp_path):
    source, manifest, _ = selection(tmp_path)
    pin = sha256(manifest.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="manifest changed"):
        with install.verified_native_installation(source, manifest_path=manifest, manifest_sha256=pin):
            manifest.write_bytes(manifest.read_bytes() + b"\n")
