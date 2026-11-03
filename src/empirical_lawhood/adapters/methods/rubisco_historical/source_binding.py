"""Bounded exposed RR2018 source preparation with separated role outputs.

The source is an already captured typed UTF-8 operand. This operation has no
path, network, acquisition, interpreter, environment or qualification effect.
Original public biology remains exposed, with unknown endpoint pairing and n.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import (
    MAX_INPUT_BYTES, Rr2018NativeAuditV1, SOURCE_SHA256, decode_rr2018, role_slices,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from .analysis import rr2018_science
from .operation_contracts import HistoricalCommitConfigV1


@dataclass(frozen=True, slots=True)
class Rr2018ArticleInputV1(CanonicalRecord):
    """Exact raw UTF-8 bytes represented canonically without an arbitrary path."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/rr2018-article-input"
    input_id: str
    source_sha256: str
    raw_xml_utf8: str

    def __post_init__(self) -> None:
        validate_stable_id(self.input_id, field_name="input_id")
        validate_sha256(self.source_sha256, field_name="source_sha256")
        if not isinstance(self.raw_xml_utf8, str) or not 1 <= len(self.raw_xml_utf8) <= MAX_INPUT_BYTES:
            raise ValueError("RR2018 raw UTF-8 source exceeds its bounded text contract")
        try:
            payload = self.raw_xml_utf8.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError("RR2018 article source must be valid UTF-8 text") from error
        if len(payload) > MAX_INPUT_BYTES or sha256(payload).hexdigest() != self.source_sha256:
            raise ValueError("RR2018 raw source differs from its bounded exact-byte identity")


@dataclass(frozen=True, slots=True)
class HistoricalSourceConfigV1(HistoricalCommitConfigV1):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/historical/operations/source-config"

    def __post_init__(self) -> None:
        super(HistoricalSourceConfigV1, self).__post_init__()
        if self.science.source.object_schema != Rr2018NativeAuditV1.SCHEMA:
            raise ValueError("RR2018 source preparation requires its native audit identity")


SOURCE_OUTPUTS = (
    ("audit", Rr2018NativeAuditV1),
    ("features.site100", HistoricalFeatureSliceV1),
    ("features.site206", HistoricalFeatureSliceV1),
    ("labels.site100", HistoricalLabelSliceV1),
    ("labels.site206", HistoricalLabelSliceV1),
    ("training.site100", HistoricalTrainingSliceV1),
    ("training.site206", HistoricalTrainingSliceV1),
)


def prepare_source(config: HistoricalSourceConfigV1,
                    article: Rr2018ArticleInputV1) -> tuple[tuple[str, CanonicalRecord], ...]:
    """Hash first, reuse the native decoder, bind complete source semantics.

    No supplement port is declared here. Its retained digest is descriptive;
    supplement_bytes_verified therefore remains false in the produced audit.
    """
    if not isinstance(config, HistoricalSourceConfigV1) or not isinstance(article, Rr2018ArticleInputV1):
        raise ValueError("RR2018 source preparation requires its exact typed ports")
    if article.source_sha256 != SOURCE_SHA256:
        raise ValueError("RR2018 source preparation requires the actual retained raw-source digest")
    audit = decode_rr2018(article.raw_xml_utf8.encode("utf-8"), expected_sha256=SOURCE_SHA256)
    if rr2018_science(audit) != config.science:
        raise ValueError("RR2018 source preparation changes its exact audit/science/root source identity")
    slices = role_slices(audit)
    names = {HistoricalTrainingSliceV1: "training", HistoricalFeatureSliceV1: "features",
             HistoricalLabelSliceV1: "labels"}
    products = (("audit", audit), *(sorted((f"{names[type(record)]}.{record.fold_id}", record)
                                           for record in slices)))
    if tuple((name, type(record)) for name, record in products) != SOURCE_OUTPUTS:
        raise ValueError("RR2018 source preparation drops or substitutes a declared role product")
    return tuple(products)
