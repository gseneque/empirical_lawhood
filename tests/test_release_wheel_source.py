# SPDX-License-Identifier: MPL-2.0
"""Exact software-artifact members, bounded comparison and adverse ZIP structure."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import stat
import zipfile

import pytest


@pytest.fixture
def wheel_source_case(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/release_check.py"
    spec = importlib.util.spec_from_file_location("wheel_source_release_owner", script)
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    payloads = {"empirical_lawhood/__init__.py": b"# selected package\n",
                "empirical_lawhood/resources/opaque.bin": b"retained source bytes\0"}
    checkout = tmp_path / "selected-inputs"
    for name, raw in payloads.items():
        path = checkout / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    # Only Git enumeration is synthetic. The actual release owner compares all
    # physical source and ZIP bodies; this creates no development checkout.
    monkeypatch.setattr(release, "output", lambda *a, **k: "\n".join("src/" + name for name in payloads))
    monkeypatch.setattr(release, "source_metadata_bytes", lambda root: source_metadata(payloads))
    return release, checkout, payloads


def source_metadata(payloads):
    return json.dumps({"schema": "empirical-lawhood/build/source", "version": "1.0.0",
        "implementation_commit": "a" * 40, "implementation_sha256": "b" * 64,
        "source_tree_sha256": "c" * 64, "tracked_files": [
            {"relative_path": "src/" + name, "mode": "100644", "size_bytes": len(raw),
             "sha256": sha256(raw).hexdigest()} for name, raw in sorted(payloads.items())]},
        sort_keys=True, separators=(",", ":")).encode() + b"\n"


def make_wheel(path, payloads, *, compression=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name, raw in payloads.items():
            archive.writestr(name, raw)
        archive.writestr("empirical_lawhood-0.0.test.dist-info/METADATA", b"software fixture\n")
        archive.writestr("empirical_lawhood-0.0.test.dist-info/extra_metadata/source.json", source_metadata(payloads))
    return path


@pytest.mark.parametrize("compression", (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED))
def test_exact_regular_wheel_retains_original_inventory(wheel_source_case, tmp_path, compression):
    release, checkout, payloads = wheel_source_case
    wheel = make_wheel(tmp_path / "selected.whl", payloads, compression=compression)
    expected = [{"path": name, "size_bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                for name, raw in sorted(payloads.items())]
    assert release.compare_wheel_source(checkout, wheel) == expected


@pytest.mark.parametrize("member", ("empirical_lawhood/__init__.py",
                                    "empirical_lawhood-0.0.test.dist-info/METADATA"))
def test_duplicate_even_with_final_matching_bytes_cannot_pass(wheel_source_case, tmp_path, member):
    release, checkout, payloads = wheel_source_case
    wheel = make_wheel(tmp_path / "duplicate.whl", payloads)
    with zipfile.ZipFile(wheel, "a") as archive, pytest.warns(UserWarning, match="Duplicate name"):
        archive.writestr(member, payloads.get(member, b"software fixture\n"))
    with pytest.raises(RuntimeError, match="duplicate"):
        release.compare_wheel_source(checkout, wheel)


@pytest.mark.parametrize("kind", (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK))
def test_matching_bytes_in_nonregular_zip_member_refuse(wheel_source_case, tmp_path, kind):
    release, checkout, payloads = wheel_source_case
    wheel = tmp_path / "nonregular.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, raw in payloads.items():
            entry = zipfile.ZipInfo(name)
            entry.create_system = 3
            entry.external_attr = (kind | 0o644) << 16
            archive.writestr(entry, raw)
    with pytest.raises(RuntimeError, match="nonregular"):
        release.compare_wheel_source(checkout, wheel)


@pytest.mark.parametrize("change", ("missing", "extra", "changed", "changed-size"))
def test_complete_package_census_and_exact_bytes_remain_required(wheel_source_case, tmp_path, change):
    release, checkout, payloads = wheel_source_case
    selected = dict(payloads)
    name = "empirical_lawhood/__init__.py"
    if change == "missing":
        del selected[name]
    elif change == "extra":
        selected["empirical_lawhood/unselected.py"] = b"extra"
    elif change == "changed":
        selected[name] = b"x" * len(selected[name])
    else:
        selected[name] += b"x"
    wheel = make_wheel(tmp_path / "changed.whl", selected)
    with pytest.raises(RuntimeError, match="wheel/source mismatch"):
        release.compare_wheel_source(checkout, wheel)


@pytest.mark.parametrize("name", ("empirical_lawhood/../escape", "empirical_lawhood//alias",
                                  "empirical_lawhood/./alias", "/absolute", "empirical_lawhood\\alias",
                                  "empirical_lawhood/unused//", "empirical_lawhood/unused///"))
def test_noncanonical_or_escaping_zip_names_refuse(wheel_source_case, tmp_path, name):
    release, checkout, payloads = wheel_source_case
    wheel = make_wheel(tmp_path / "escaping.whl", payloads)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr(name, b"unselected")
    with pytest.raises(RuntimeError, match="escaping"):
        release.compare_wheel_source(checkout, wheel)


def test_zip_directory_cannot_hide_payload_bytes(wheel_source_case, tmp_path):
    release, checkout, payloads = wheel_source_case
    wheel = make_wheel(tmp_path / "directory.whl", payloads)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("empirical_lawhood/unused/", b"hidden")
    with pytest.raises(RuntimeError, match="directory"):
        release.compare_wheel_source(checkout, wheel)


def test_source_symlink_is_not_regular_selected_input(wheel_source_case, tmp_path):
    release, checkout, payloads = wheel_source_case
    wheel = make_wheel(tmp_path / "source-link.whl", payloads)
    source = checkout / "src/empirical_lawhood/__init__.py"
    target = tmp_path / "other.py"
    target.write_bytes(payloads["empirical_lawhood/__init__.py"])
    source.unlink()
    source.symlink_to(target)
    with pytest.raises(RuntimeError, match="regular selected source"):
        release.compare_wheel_source(checkout, wheel)


def test_member_bodies_use_bounded_delivery_without_whole_bank_reads(wheel_source_case, tmp_path, monkeypatch):
    release, checkout, payloads = wheel_source_case
    payloads["empirical_lawhood/resources/opaque.bin"] = bytes(range(256)) * 16385
    source = checkout / "src/empirical_lawhood/resources/opaque.bin"
    source.write_bytes(payloads["empirical_lawhood/resources/opaque.bin"])
    wheel = make_wheel(tmp_path / "bounded.whl", payloads)
    calls = []
    original = zipfile.ZipExtFile.read

    def bounded(stream, size=-1):
        assert 0 < size <= 1024 * 1024
        raw = original(stream, size)
        calls.append((size, len(raw)))
        return raw

    def forbidden(*a, **k):
        pytest.fail("comparison retained an entire source or ZIP body")

    monkeypatch.setattr(zipfile.ZipExtFile, "read", bounded)
    monkeypatch.setattr(zipfile.ZipFile, "read", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    result = release.compare_wheel_source(checkout, wheel)
    assert sum(delivered for _, delivered in calls) == sum(map(len, payloads.values())) + len(source_metadata(payloads))
    assert result[-1]["sha256"] == sha256(payloads[result[-1]["path"]]).hexdigest()



def test_original_nul_alias_cannot_borrow_unique_matching_package_body(wheel_source_case, tmp_path, monkeypatch):
    release, checkout, payloads = wheel_source_case
    canonical = "empirical_lawhood/__init__.py"
    placeholder = canonical + "~alias"
    selected = dict(payloads)
    selected[placeholder] = selected.pop(canonical)
    literal = make_wheel(tmp_path / "literal-name.whl", selected)
    raw = literal.read_bytes()
    # Both local and central headers retain exactly the same original alias.
    # ZipInfo normalizes its public filename, but archive.open still accepts
    # those matching original headers and yields the correct selected body.
    assert raw.count(placeholder.encode()) == 2
    wheel = tmp_path / "nul-alias.whl"
    wheel.write_bytes(raw.replace(placeholder.encode(), (canonical + "\0alias").encode()))
    with zipfile.ZipFile(wheel) as archive:
        members = archive.infolist()
        matches = [member for member in members if member.filename == canonical]
        assert len(matches) == 1
        member, = matches
        assert member.orig_filename == canonical + "\0alias"
        assert len({value.filename for value in members}) == len(members)
        with archive.open(member) as stream:
            assert stream.read() == payloads[canonical]

    def unopened(*args, **kwargs):
        pytest.fail("noncanonical original ZIP name reached a package body reader")

    monkeypatch.setattr(zipfile.ZipFile, "open", unopened)
    with pytest.raises(RuntimeError, match="noncanonical original member name"):
        release.compare_wheel_source(checkout, wheel)


@pytest.mark.parametrize("defect", ("missing", "commit", "archive", "tree", "census", "encoding", "executable", "wrong-root"))
def test_build_source_metadata_is_mandatory_and_exact(wheel_source_case, tmp_path, defect):
    release, checkout, payloads = wheel_source_case
    name = "empirical_lawhood-0.0.test.dist-info/extra_metadata/source.json"
    value = json.loads(source_metadata(payloads))
    if defect in ("commit", "archive", "tree"):
        key = {"commit": "implementation_commit", "archive": "implementation_sha256", "tree": "source_tree_sha256"}[defect]
        value[key] = "d" * len(value[key])
    if defect == "census":
        value["tracked_files"] = value["tracked_files"][:1]
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    if defect == "encoding":
        raw = raw.rstrip(b"\n")
    wheel = tmp_path / "metadata.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for package_name, payload in payloads.items():
            archive.writestr(package_name, payload)
        archive.writestr("empirical_lawhood-0.0.test.dist-info/METADATA", b"software fixture\n")
        if defect != "missing":
            member = zipfile.ZipInfo(name.replace("0.0.test", "foreign") if defect == "wrong-root" else name)
            member.create_system = 3
            member.external_attr = (stat.S_IFREG | (0o755 if defect == "executable" else 0o644)) << 16
            archive.writestr(member, raw)
    with pytest.raises(RuntimeError, match="source metadata"):
        release.compare_wheel_source(checkout, wheel)
