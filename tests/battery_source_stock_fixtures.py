# SPDX-License-Identifier: MPL-2.0
"""Authenticated exposed source stock for PURE metadata checks; no provider import."""

import gzip
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySource, PROTOCOL_SHA256, SOURCE_MEMBERS, SOURCE_VERSION,
)

FIXTURE = Path(__file__).parent / 'fixtures/battery/thermal_source_stock'
CENSUS_SHA256 = '0df981752de8a66903db017e141893de77361ee5c8d5084ef13d5b0d814e4705'
ARCHIVE_SHA256 = 'a1ae2eaa026ba1f0dfaa789114f3f2f024548d1540a2388197d6d7acbb48a077'


def unpack_source_stock(destination):
    """Copy every original stock member, authenticating archive and exact roster."""
    raw_census = (FIXTURE / 'source-census.json').read_bytes()
    assert len(raw_census) == 11896 and sha256(raw_census).hexdigest() == CENSUS_SHA256
    census = json.loads(raw_census)
    source = BatteryInquirySource()
    assert census['source'] == source.to_document()
    assert census['source_sha256'] == source.fingerprint()
    assert census['exposure'] == 'EXPOSED_DEVELOPMENT_STOCK_NONPROMOTABLE'
    assert not census['scientific_qualification'] and census['native_contacts'] == 0
    assert census['source_member_count'] == len(SOURCE_MEMBERS)
    expected = {'pybamm/' + name: digest for name, digest in SOURCE_MEMBERS}
    expected.update({
        'm50-original.pdf': source.manufacturer_document_sha256,
        'battery-thermal-inquiry-selection.json': PROTOCOL_SHA256,
        'licenses/PyBaMM-LICENSE.txt': census['license_origin']['sha256'],
        'provenance/source-intake-register.json': census['source_origin']['source_intake_register_sha256'],
    })
    rows = {row['path']: row for row in census['members']}
    assert len(rows) == len(census['members']) == len(expected)
    assert {name: row['sha256'] for name, row in rows.items()} == expected
    raw = (FIXTURE / 'source-operands.tar.gz').read_bytes()
    assert len(raw) == 698758 and sha256(raw).hexdigest() == ARCHIVE_SHA256
    assert census['archive']['bytes'] == len(raw)
    assert census['archive']['sha256'] == ARCHIVE_SHA256
    expanded = gzip.decompress(raw)
    assert len(expanded) == census['archive']['expanded_tar_bytes'] == 1351680
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as archive:
        members = archive.getmembers()
        assert len(members) == len(expected)
        assert len({member.name for member in members}) == len(members)
        assert {member.name for member in members} == set(expected)
        for member in members:
            path = PurePosixPath(member.name)
            assert member.isfile() and member.mtime == 0
            assert not path.is_absolute() and '..' not in path.parts
            payload = archive.extractfile(member).read()
            assert len(payload) == rows[member.name]['bytes']
            assert sha256(payload).hexdigest() == expected[member.name]
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(payload)
    original = json.loads((destination / 'provenance/source-intake-register.json').read_bytes())
    assert original['source'] == source.to_document()
    assert original['source_sha256'] == source.fingerprint()
    assert len(original['members']) == len(SOURCE_MEMBERS) + 2
    assert len((destination / 'm50-original.pdf').read_bytes()) == 576273
    return destination


def stock_distribution(stock, *, version=SOURCE_VERSION):
    """Exposed metadata locator backed by authenticated bytes, never an engine."""
    def locate_file(name):
        assert name == 'pybamm'
        return stock / name
    return SimpleNamespace(version=version, locate_file=locate_file)
