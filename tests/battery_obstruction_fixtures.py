# SPDX-License-Identifier: MPL-2.0
"""Exact retained adverse-history bytes for portable PURE checks; no native entry."""

import gzip
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.adapters.methods.battery_diagnostic_obstruction.contracts import (
    ObstructionSource, ROLES,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes


FIXTURE = Path(__file__).parent / 'fixtures/battery/diagnostic_obstruction'
CENSUS_SHA256 = '160aa46c319309af0003745573138957e954a05725e82010c998ecbaa3ae00ac'
COMPRESSED_SHA256 = '1d4c7fec773cb76f7061ba39d42978c8fa810424d999da409a4c99bc273c599a'
SOURCE_SHA256 = 'f147680f49187838e7d712b7b642e312f34d5fac1029d1a44548378108541303'


def load_retained_obstruction_source():
    """Authenticate the whole original source, including its trailing newline."""
    raw_census = (FIXTURE / 'source-census.json').read_bytes()
    assert len(raw_census) == 2026 and sha256(raw_census).hexdigest() == CENSUS_SHA256
    census = json.loads(raw_census)
    assert census['exposure'] == 'EXPOSED_RETAINED_HISTORY_NONPROMOTABLE'
    assert not census['scientific_qualification'] and census['fresh_native_contacts'] == 0
    compressed = (FIXTURE / 'source01.json.gz').read_bytes()
    assert len(compressed) == census['compressed']['bytes'] == 31765
    assert sha256(compressed).hexdigest() == census['compressed']['sha256'] == COMPRESSED_SHA256
    raw = gzip.decompress(compressed)
    assert len(raw) == census['source']['bytes'] == 207993
    assert sha256(raw).hexdigest() == census['source']['sha256'] == SOURCE_SHA256
    source = decode_canonical_bytes(raw, ObstructionSource, maximum_bytes=None)
    assert source.SCHEMA == census['source']['schema']
    assert source.VERSION == census['source']['version'] == '1.0.0'
    assert source.source_id == census['source']['source_id']
    assert source.to_document() == json.loads(raw)
    assert len(source.complete_custody) == 475 and len(source.input_manifests) == 3
    assert tuple(row.role for row in source.records) == ROLES
    return source
