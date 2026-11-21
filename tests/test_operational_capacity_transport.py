# SPDX-License-Identifier: MPL-2.0
"""Scientific identity and selected budgets without hidden data-size ceilings."""
from dataclasses import dataclass
from hashlib import sha256
from types import SimpleNamespace
from typing import ClassVar
import subprocess

import pytest

from empirical_lawhood.api import codecs
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.local import execution
from empirical_lawhood.execution.recursive_handoff import RecursiveClosureLimits
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage import transfer_files
from empirical_lawhood.storage.bounded_io import BoundedFileIOError


@dataclass(frozen=True, slots=True)
class CapacityRecord(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/testing/observed-capacity'
    label: str


def test_authoring_file_above_previous_128_mib_cap_preserves_materialization(tmp_path):
    record = CapacityRecord('disclosed software fixture')
    path = tmp_path / 'large-observed.json'
    with path.open('wb') as stream:
        stream.write(record.canonical_bytes())
        block = b' ' * 2**20
        for _ in range(129):
            stream.write(block)
    loaded = codecs.load_registered_authoring_materialization(path, root_schemas={record.SCHEMA: type(record)})
    assert loaded.record == record and loaded.byte_count == path.stat().st_size > 128*2**20
    assert loaded.raw_materialization_sha256 == sha256(b'application/json\0' + loaded.raw_bytes).hexdigest()
    with pytest.raises(codecs.AuthoringCodecError, match='byte limit'):
        codecs.load_registered_authoring(path, root_schemas={record.SCHEMA: type(record)}, maximum_bytes=128*2**20)


def test_pure_result_above_previous_256_mib_cap_keeps_bounded_ipc_chunks():
    payload = b'x' * (256*2**20 + 1)
    result = RunnerResult((TaskOutputPayload('output.payload', payload),), ())
    context = SimpleNamespace(resource_budget=SimpleNamespace(output_bytes=len(payload)),
        output_ports=(SimpleNamespace(output_id='output.payload'),))
    messages, observed_bytes, largest_chunk = [], 0, 0
    class Connection:
        def send(self, message):
            nonlocal observed_bytes, largest_chunk
            if isinstance(message, execution._ProcessChunk):
                observed_bytes += len(message.payload)
                largest_chunk = max(largest_chunk, len(message.payload))
            else:
                messages.append(message)
    execution._return_nonstreaming_result(Connection(), context, result)
    assert observed_bytes == len(payload)
    assert largest_chunk <= execution.STREAM_CHUNK_BYTES
    assert len(messages) == 1 and isinstance(messages[0], execution._ProcessStreamComplete)
    context.resource_budget.output_bytes -= 1
    with pytest.raises(execution.ResourceAdmissionError, match='explicitly selected output allowance'):
        execution._return_nonstreaming_result(Connection(), context, result)


def test_generic_transfer_handles_unicode_spaces_and_exact_observed_allowances(tmp_path, monkeypatch):
    root = tmp_path / 'scientific inputs'; root.mkdir()
    (root / 'energy μ arrays.txt').write_bytes(b'exact scientific file\n')
    (root / 'empty').write_bytes(b'')
    calls = []
    census = transfer_files.census_transfer_files
    def observed(*args, **kwargs):
        calls.append(True)
        return census(*args, **kwargs)
    monkeypatch.setattr(transfer_files, 'census_transfer_files', observed)
    output = tmp_path / 'prepared'
    result = transfer_files.prepare_transfer(root, output)
    assert len(calls) == 2
    assert result['files'] == 2 and result['bytes'] == len(b'exact scientific file\n')
    assert transfer_files.verify_transfer(root, output/'payload-manifest.json', expected_sha256=result['sha256'])['status'] == 'BYTE_VERIFIED'
    checked = subprocess.run(['sha256sum', '--check', str(output/'SHA256SUMS')], cwd=root, capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
    with pytest.raises(BoundedFileIOError, match='byte limit'):
        transfer_files.prepare_transfer(root, tmp_path/'refused', maximum_bytes=1)
    assert not (tmp_path/'refused'/'payload-manifest.json').exists()


def test_transfer_manifest_above_previous_16_mib_cap_is_digest_authenticated(tmp_path):
    # Metadata only: long, valid distinct locators, no manufactured science.
    prefix = ('p'*100 + '/') * 8
    rows = [{'relative_path': prefix+f'file-{i:05d}', 'size_bytes': 0, 'sha256': sha256(b'').hexdigest()}
        for i in range(19000)]
    document = {'schema':'empirical-lawhood/operational/transfer-files','version':'1.0.0',
        'maximum_bytes':1,'maximum_files':len(rows),'files':rows,
        'scientific_qualification':'NOT_ESTABLISHED','native_completion':'NOT_INFERRED','primary_receipts':'UNCHANGED'}
    raw = transfer_files.encode_document(document)
    assert len(raw) > 16*2**20
    path = tmp_path/'manifest.json';path.write_bytes(raw)
    parsed, members = transfer_files.read_transfer_manifest(path, expected_sha256=sha256(raw).hexdigest())
    assert len(members) == len(rows) and parsed == document
    with pytest.raises(ValueError, match='authenticated digest'):
        transfer_files.read_transfer_manifest(path, expected_sha256='f'*64)


def test_closure_defaults_are_observed_and_explicit_allowances_have_no_hidden_upper_clamp():
    assert RecursiveClosureLimits().maximum_total_bytes is None
    limits = RecursiveClosureLimits(maximum_member_bytes=2**40, maximum_total_bytes=2**42,
        maximum_control_bytes=2**35, maximum_hashed_bytes=2**44)
    assert limits.maximum_member_bytes == 2**40
