"""Focused fake-transport checks of fresh source custody; no network is used.

SPDX-License-Identifier: MPL-2.0
"""

from dataclasses import replace
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import json

import numpy as np
import pyarrow
import pytest

from empirical_lawhood.adapters.physical.mast_archive.fresh_source import FairMastPublicSourceService, load_fair_mast_selection
from empirical_lawhood.adapters.physical.mast_archive.level2_array import Level2Array
from empirical_lawhood.adapters.physical.mast_archive import fresh_source
from empirical_lawhood.storage.artifacts import ExternalArtifactPlane, GuardedExternalRoot
from empirical_lawhood.storage.study_issue import ExternalStudyOperationAuthorityStore
from empirical_lawhood.science.evidence.evidence import OutcomeAccess
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.models.time import CausalPhase, InformationCutoff
from empirical_lawhood.design.study_issue import AccountableHumanIdentity, StudyAuthorityKind, StudyOperationAuthority
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.execution.operator_profile import OperatorStorageProfile


def test_level2_profile_interval_reads_only_intersecting_chunks_and_preserves_original_indices():
    metadata = {"zarr_format": 3, "node_type": "array", "data_type": "float64",
                "dimension_names": ["major_radius", "time"], "attributes": {"units": "eV"},
                "shape": [4, 5], "chunk_grid": {"name": "regular", "configuration": {"chunk_shape": [3, 3]}},
                "chunk_key_encoding": {"name": "default", "configuration": {"separator": "/"}},
                "codecs": [{"name": "bytes", "configuration": {"endian": "little"}}, {"name": "zstd"}]}
    raw = json.dumps(metadata).encode()
    selected = Level2Array.from_metadata(raw, dimensions=("major_radius", "time"), units="eV")
    original = np.arange(36, dtype="<f8").reshape(6, 6)
    calls = []

    def fetch(index):
        row, column = (3 * i for i in index)
        calls.append(index)
        return pyarrow.Codec("zstd").compress(original[row:row+3, column:column+3].tobytes(), asbytes=True)

    np.testing.assert_array_equal(selected.read_interval(3, 5, fetch), original[:4, 3:5])
    assert calls == [(0, 1), (1, 1)]
    np.testing.assert_array_equal(selected.read_interval(2, 4, fetch), original[:4, 2:4])
    for start, stop in ((-1, 2), (2, 2), (3, 6)):
        with pytest.raises(ValueError, match="interval"):
            selected.read_interval(start, stop, fetch)
    with pytest.raises(OSError):
        selected.read_interval(1, 2, lambda index: pyarrow.Codec("zstd").compress(b"short", asbytes=True))
    with pytest.raises(ValueError, match="units"):
        Level2Array.from_metadata(raw, dimensions=("time", "major_radius"), units="eV")
    with pytest.raises(ValueError, match="units"):
        Level2Array.from_metadata(raw, dimensions=("major_radius", "time"), units="keV")


CONFIG = Path(__file__).resolve().parents[1] / "programmes/energy/fusion/workflows/fair-mast-source/fair-mast-level2.json"


def test_short_original_http_transfer_is_refused_before_source_publication(monkeypatch):
    url = fresh_source.ZARR_BASE + "/30421.zarr/summary/time/c/0"

    class ShortResponse(BytesIO):
        status = 200
        headers = {"Content-Length": "100"}

        def geturl(self):
            return url

    class Opener:
        def open(self, request, timeout):
            return ShortResponse(b"partial")

    monkeypatch.setattr(fresh_source, "build_opener", lambda *handlers: Opener())
    with pytest.raises(ValueError, match="declared length"):
        fresh_source.BoundedFairMastHttpGateway().fetch(url, maximum_bytes=200, timeout_seconds=1)


class Gateway:
    def __init__(self, urls: tuple[str, str, str]) -> None:
        self.payloads = dict(
            zip(
                urls,
                (
                    b'{"shot_id":30421,"campaign":"M9"}',
                    b'{"zarr_format":3,"node_type":"array","data_type":"float64",'
                    + b'"shape":[4],"attributes":{"units":"s"},"chunk_grid":'
                    + b'{"name":"regular","configuration":{"chunk_shape":[4]}},'
                    + b'"codecs":[{"name":"bytes"},{"name":"zstd"}]}',
                    b"\x28\xb5\x2f\xfdcompressed-chunk",
                ),
                strict=True,
            )
        )
        self.calls: list[str] = []
        self.fail_once_at: str | None = None

    def fetch(self, url: str, *, maximum_bytes: int, timeout_seconds: int) -> bytes:
        self.calls.append(url)
        if url == self.fail_once_at:
            self.fail_once_at = None
            raise OSError("test interrupted transfer")
        payload = self.payloads[url]
        assert len(payload) <= maximum_bytes
        assert timeout_seconds <= 90
        return payload


class LocalService(FairMastPublicSourceService):
    def _clean_head(self) -> str:
        return "a" * 40


def _authority(kind, subject, issuer, root_id=None, relative_root=None):
    source = kind is StudyAuthorityKind.SOURCE_ACQUISITION
    return StudyOperationAuthority(
        authority_id=f"authority.test.{kind.value.lower()}",
        kind=kind,
        subject=subject,
        prerequisite_authority=None,
        issuer=issuer,
        grantee_id="operator.fair-mast-source-service",
        scope_id="scope.test.fair-mast",
        storage_root_id=root_id,
        relative_root=relative_root,
        allows_source_acquisition=source,
        allows_external_publication=not source,
        allows_execution=False,
        allows_actuation=False,
        allows_reveal=False,
        issued_at_utc="2026-09-28T00:00:00Z",
        expires_at_utc=None,
        outcome_access=OutcomeAccess.OUTCOME_BLIND,
    )


def test_fair_mast_preview_acquire_recover_and_drift(tmp_path):
    selection = load_fair_mast_selection(CONFIG)
    gateway = Gateway(selection.urls)
    contract = ExternalRootContract(
        "test-fair-mast-root",
        "test root",
        str(tmp_path),
        str(next(parent for parent in (tmp_path, *tmp_path.parents) if parent.is_mount())),
        OperatorStorageProfile.SCHEMA,
        1,
        None,
        None,
        (),
    )
    plane = ExternalArtifactPlane(GuardedExternalRoot(contract))
    store = ExternalStudyOperationAuthorityStore(plane)
    human = AccountableHumanIdentity("test-owner", "owner", "test", "1" * 64)
    issuer = ObjectIdentity.from_record(human.human_id, human)
    subject = ObjectIdentity.from_record(selection.source_id, selection)
    source = _authority(StudyAuthorityKind.SOURCE_ACQUISITION, subject, issuer)
    custody = _authority(
        StudyAuthorityKind.CUSTODY_PUBLICATION,
        subject,
        issuer,
        contract.storage_root_id,
        selection.relative_root,
    )
    store.persist(source)
    store.persist(custody)
    service = LocalService(plane=plane, authorities=store, gateway=gateway)
    assert service.preview(selection)["source_contacted"] is False
    assert gateway.calls == []
    gateway.fail_once_at = selection.urls[1]
    with pytest.raises(OSError, match="interrupted"):
        service.acquire(
            selection,
            acquisition_authority_id=source.authority_id,
            custody_authority_id=custody.authority_id,
        )
    with pytest.raises(FileExistsError, match="recover"):
        service.acquire(
            selection,
            acquisition_authority_id=source.authority_id,
            custody_authority_id=custody.authority_id,
        )
    receipt = service.acquire(
        selection,
        acquisition_authority_id=source.authority_id,
        custody_authority_id=custody.authority_id,
        recover=True,
    )
    assert len(receipt.members) == 3
    assert len(gateway.calls) == 5
    service.verify_receipt(selection, receipt)
    design_input = service.design_input(
        selection,
        input_id="test.fair-mast.receipt-input",
        information_cutoff=InformationCutoff(
            "test.cutoff", "test.clock", CausalPhase.PRE_ACTION, Decimal(0)
        ),
        operator_id="test-owner",
        authoring_at_utc="2027-01-01T00:00:00Z",
    )
    assert design_input.object_identity == ObjectIdentity.from_record(
        receipt.receipt_id, receipt
    )
    with pytest.raises(ValueError, match="postdates"):
        service.design_input(
            selection,
            input_id="test.fair-mast.early-input",
            information_cutoff=design_input.information_cutoff,
            operator_id="test-owner",
            authoring_at_utc="2020-01-01T00:00:00Z",
        )
    assert (
        service.acquire(
            selection,
            acquisition_authority_id=source.authority_id,
            custody_authority_id=custody.authority_id,
            recover=True,
        )
        == receipt
    )
    assert len(gateway.calls) == 5
    with pytest.raises(ValueError, match="selection"):
        service.verify_receipt(replace(selection, expected_unit="ms"), receipt)
    member = next(
        m for m in receipt.members if m.media_type == "application/octet-stream"
    )
    (tmp_path / member.relative_locator).write_bytes(b"drift")
    with pytest.raises(Exception, match="drift|differ|hash|materialization"):
        service.verify_receipt(selection, receipt)


def test_fair_mast_config_refuses_endpoint_or_selector_drift():
    selection = load_fair_mast_selection(CONFIG)
    with pytest.raises(ValueError, match="endpoints"):
        replace(selection, zarr_base="https://example.org/elsewhere")
    with pytest.raises(ValueError, match="array path"):
        replace(selection, array_path="../summary/time")
