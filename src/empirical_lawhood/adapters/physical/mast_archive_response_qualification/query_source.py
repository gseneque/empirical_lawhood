"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from hashlib import sha256
from typing import Protocol
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity

from empirical_lawhood.domains.fusion.mast_archive_response_qualification.query_contracts import (
    MASTUArchiveAcquisitionUnitManifest as _science_MASTUArchiveAcquisitionUnitManifest,
    MASTUArchiveCompactUnitManifest as _science_MASTUArchiveCompactUnitManifest,
    MASTUArchiveObjectReceipt as _science_MASTUArchiveObjectReceipt,
    MASTUArchiveQuery as _science_MASTUArchiveQuery,
    MASTUArchiveQueryManifest as _science_MASTUArchiveQueryManifest,
    MASTUArchiveQuerySourceConfig as _science_MASTUArchiveQuerySourceConfig,
    MASTUArchiveResponseObject as _science_MASTUArchiveResponseObject,
)

class MASTUArchiveQueryClient(Protocol):
    """Authorized provider client; constructing a manifest never invokes this port."""

    def retrieve(self, query: _science_MASTUArchiveQuery) -> _science_MASTUArchiveResponseObject: ...

class MASTUArchiveCustodyPort(Protocol):
    """Durably custody one response before another source retrieval is permitted."""

    def custody(
        self,
        *,
        query: _science_MASTUArchiveQuery,
        native_object: ArtifactIdentity,
        data_bytes: bytes,
        metadata_bytes: bytes,
    ) -> str: ...

def retrieve_mastu_archive_query(
    *,
    manifest: _science_MASTUArchiveQueryManifest,
    config: _science_MASTUArchiveQuerySourceConfig,
    query: _science_MASTUArchiveQuery,
    client: MASTUArchiveQueryClient,
    custody: MASTUArchiveCustodyPort,
    unit_manifest_id: str,
    maximum_remaining_response_bytes: int | None = None,
) -> tuple[_science_MASTUArchiveObjectReceipt, _science_MASTUArchiveAcquisitionUnitManifest]:
    """Retrieve and custody exactly one predeclared acquisition-group object."""

    manifest_identity = ObjectIdentity.from_record(manifest.manifest_id, manifest)
    if config.query_manifest != manifest_identity or query not in manifest.queries:
        raise ValueError("MAST-U group retrieval substitutes its frozen query manifest")
    if (
        config.provider_key != manifest.provider_key
        or config.provider_version != manifest.provider_version
        or config.request_schema != manifest.request_schema
        or config.response_object_schema != manifest.response_object_schema
        or config.maximum_query_count != manifest.maximum_query_count
        or config.maximum_object_count != manifest.maximum_object_count
        or config.maximum_total_response_bytes != manifest.maximum_total_response_bytes
    ):
        raise ValueError("MAST-U group retrieval config differs from frozen manifest bounds")
    response = client.retrieve(query)
    if response.query_id != query.query_id or not response.data_bytes:
        raise ValueError("MAST-U provider returned another or empty group object")
    observed_bytes = len(response.data_bytes) + len(response.metadata_bytes)
    remaining_bound = (
        manifest.maximum_total_response_bytes
        if maximum_remaining_response_bytes is None
        else maximum_remaining_response_bytes
    )
    if remaining_bound < 1 or observed_bytes > min(
        manifest.maximum_total_response_bytes,
        remaining_bound,
    ):
        raise ValueError("MAST-U group response exceeds the frozen byte bound")
    data_sha256 = sha256(response.data_bytes).hexdigest()
    metadata_sha256 = sha256(response.metadata_bytes).hexdigest()
    native_object = ArtifactIdentity(
        artifact_id=f"artifact.{query.query_id}",
        role="mastu-native-response-object",
        payload_schema=manifest.response_object_schema,
        sha256=data_sha256,
        media_type=response.media_type,
        size_bytes=len(response.data_bytes),
    )
    locator = custody.custody(
        query=query,
        native_object=native_object,
        data_bytes=response.data_bytes,
        metadata_bytes=response.metadata_bytes,
    )
    receipt = _science_MASTUArchiveObjectReceipt(
        receipt_id=f"receipt.{query.query_id}",
        query=ObjectIdentity.from_record(query.query_id, query),
        native_object=native_object,
        observed_data_sha256=data_sha256,
        observed_metadata_sha256=metadata_sha256,
        observed_size_bytes=len(response.data_bytes),
        custody_relative_locator=locator,
        custodied_before_next_retrieval=True,
    )
    unit = _science_MASTUArchiveAcquisitionUnitManifest(
        manifest_id=unit_manifest_id,
        query_manifest=manifest_identity,
        query=ObjectIdentity.from_record(query.query_id, query),
        object_receipt=ObjectIdentity.from_record(receipt.receipt_id, receipt),
        acquisition_group_id=query.acquisition_group_id,
        preparation_instance_id=query.preparation_instance_id,
        physical_independent_unit_id=query.physical_independent_unit_id,
        view_ids=query.view_ids,
        observed_total_response_bytes=observed_bytes,
        complete_after_object_custody=True,
    )
    return receipt, unit

def retrieve_mastu_archive_query_manifest(
    *,
    manifest: _science_MASTUArchiveQueryManifest,
    config: _science_MASTUArchiveQuerySourceConfig,
    client: MASTUArchiveQueryClient,
    custody: MASTUArchiveCustodyPort,
    compact_manifest_id: str,
) -> tuple[tuple[_science_MASTUArchiveObjectReceipt, ...], _science_MASTUArchiveCompactUnitManifest]:
    """Retrieve sequentially, custody immediately, and emit only compact lineage.

    The function deliberately has no batching hook: a failed or delayed custody call
    raises before the next ``client.retrieve`` invocation. Response hashes and sizes
    are calculated from returned bytes and cannot be supplied by issued config.
    """

    manifest_identity = ObjectIdentity.from_record(manifest.manifest_id, manifest)
    if config.query_manifest != manifest_identity:
        raise ValueError("MAST-U query config substitutes the frozen query manifest")
    if (
        config.provider_key != manifest.provider_key
        or config.provider_version != manifest.provider_version
        or config.request_schema != manifest.request_schema
        or config.response_object_schema != manifest.response_object_schema
        or config.maximum_query_count != manifest.maximum_query_count
        or config.maximum_object_count != manifest.maximum_object_count
        or config.maximum_total_response_bytes != manifest.maximum_total_response_bytes
    ):
        raise ValueError("MAST-U query config differs from frozen manifest bounds")

    receipts: list[_science_MASTUArchiveObjectReceipt] = []
    total_bytes = 0
    for query in manifest.queries:
        response = client.retrieve(query)
        if response.query_id != query.query_id:
            raise ValueError("MAST-U provider response is attributed to another query")
        if not response.data_bytes:
            raise ValueError("MAST-U provider returned an empty native object")
        total_bytes += len(response.data_bytes) + len(response.metadata_bytes)
        if len(receipts) + 1 > manifest.maximum_object_count:
            raise ValueError("MAST-U provider exceeded the frozen object count")
        if total_bytes > manifest.maximum_total_response_bytes:
            raise ValueError("MAST-U provider exceeded the frozen response-byte bound")

        data_sha256 = sha256(response.data_bytes).hexdigest()
        metadata_sha256 = sha256(response.metadata_bytes).hexdigest()
        native_object = ArtifactIdentity(
            artifact_id=f"artifact.{query.query_id}",
            role="mastu-native-response-object",
            payload_schema=manifest.response_object_schema,
            sha256=data_sha256,
            media_type=response.media_type,
            size_bytes=len(response.data_bytes),
        )
        custody_locator = custody.custody(
            query=query,
            native_object=native_object,
            data_bytes=response.data_bytes,
            metadata_bytes=response.metadata_bytes,
        )
        receipts.append(
            _science_MASTUArchiveObjectReceipt(
                receipt_id=f"receipt.{query.query_id}",
                query=ObjectIdentity.from_record(query.query_id, query),
                native_object=native_object,
                observed_data_sha256=data_sha256,
                observed_metadata_sha256=metadata_sha256,
                observed_size_bytes=len(response.data_bytes),
                custody_relative_locator=custody_locator,
                custodied_before_next_retrieval=True,
            )
        )

    compact = _science_MASTUArchiveCompactUnitManifest(
        manifest_id=compact_manifest_id,
        query_manifest=manifest_identity,
        object_receipts=tuple(
            sorted(
                (ObjectIdentity.from_record(value.receipt_id, value) for value in receipts),
                key=lambda value: value.object_id,
            )
        ),
        preparation_instance_ids=tuple(
            sorted({value.preparation_instance_id for value in manifest.queries})
        ),
        acquisition_group_ids=tuple(
            sorted({value.acquisition_group_id for value in manifest.queries})
        ),
        physical_independent_unit_ids=tuple(
            sorted({value.physical_independent_unit_id for value in manifest.queries})
        ),
        view_ids=tuple(sorted({view for value in manifest.queries for view in value.view_ids})),
        complete_after_all_object_custody=True,
    )
    return tuple(receipts), compact
