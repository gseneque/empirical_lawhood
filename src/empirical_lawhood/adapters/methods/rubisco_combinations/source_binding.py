# SPDX-License-Identifier: MPL-2.0
"""Hash-first Wilson HTML/GenBank interpretation with separate information roles.

The worker independently decodes original bounded source text. It performs no
acquisition, filesystem lookup, native biology or scientific qualification.
"""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.physical.rubisco_kinetics.genbank import (
    NativeTeParentConstructV1, decode_te_parent_genbank,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import (
    MAX_HTML_BYTES, WilsonMutantPanelV1, build_wilson2017_panel, decode_wilson2017_html,
)
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id

from . import analysis
from .operation_contracts import CombinationSourceConfigV1
from .records import CombinationFeaturesV1, CombinationLabelsV1, CombinationTrainingV1

WILSON_SOURCE_SHA256 = "102a96a551bf11104b7ca7563572010adf8dc540a937165c671f23c618a24316"
GENBANK_SOURCE_SHA256 = "62f8c50c51ba007b4d6b99273b9c397ceea85d97985449f6c0bcef376e51b305"
PROTOCOL_SHA256 = "2c27de0e3b6d88bf3e18f4e69aec9c76abf7be04c0a0e3194a922aaadfb03bd9"
MAX_GENBANK_BYTES = 128 * 1024


def _validate_raw(input_id, source_sha256, text, maximum_bytes):
    validate_stable_id(input_id, field_name="input_id")
    validate_sha256(source_sha256, field_name="source_sha256")
    if not isinstance(text, str) or not 1 <= len(text) <= maximum_bytes:
        raise ValueError("native source exceeds its bounded UTF-8 text contract")
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("native source must be valid UTF-8 text") from error
    if len(raw) > maximum_bytes or sha256(raw).hexdigest() != source_sha256:
        raise ValueError("native source differs from its exact bounded byte identity")


@dataclass(frozen=True, slots=True)
class WilsonArticleInputV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/wilson-article-input"
    input_id: str
    source_sha256: str
    raw_html_utf8: str

    def __post_init__(self) -> None:
        _validate_raw(self.input_id, self.source_sha256, self.raw_html_utf8, MAX_HTML_BYTES)


@dataclass(frozen=True, slots=True)
class TeParentGenbankInputV1(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco/combinations/te-parent-genbank-input"
    input_id: str
    source_sha256: str
    raw_genbank_utf8: str

    def __post_init__(self) -> None:
        _validate_raw(self.input_id, self.source_sha256, self.raw_genbank_utf8, MAX_GENBANK_BYTES)


SOURCE_OUTPUTS = (
    ("features", CombinationFeaturesV1),
    ("labels", CombinationLabelsV1),
    ("panel", WilsonMutantPanelV1),
    ("training", CombinationTrainingV1),
)


def decode_source(article: WilsonArticleInputV1, genbank: TeParentGenbankInputV1) -> tuple[WilsonMutantPanelV1, NativeTeParentConstructV1]:
    if type(article) is not WilsonArticleInputV1 or type(genbank) is not TeParentGenbankInputV1:
        raise ValueError("combination source requires both exact typed raw source roles")
    if article.source_sha256 != WILSON_SOURCE_SHA256 or genbank.source_sha256 != GENBANK_SOURCE_SHA256:
        raise ValueError("combination source differs from the exact reviewed article or deposited parent version")
    table = decode_wilson2017_html(article.raw_html_utf8.encode("utf-8"), expected_sha256=WILSON_SOURCE_SHA256)
    parent = decode_te_parent_genbank(genbank.raw_genbank_utf8.encode("utf-8"), expected_sha256=GENBANK_SOURCE_SHA256)
    return build_wilson2017_panel(table, parent), parent


def prepare_source(config: CombinationSourceConfigV1, article: WilsonArticleInputV1,
                   genbank: TeParentGenbankInputV1) -> tuple[tuple[str, CanonicalRecord], ...]:
    if type(config) is not CombinationSourceConfigV1 or config.science.protocol_sha256 != PROTOCOL_SHA256:
        raise ValueError("combination source changes its exact configuration or frozen assessment protocol")
    panel, parent = decode_source(article, genbank)
    science, training, features, labels = analysis.prepare_roles(panel, parent)
    if science != config.science:
        raise ValueError("independent native source preparation changes the exact panel/parent/selection scientific identity")
    products = (("features", features), ("labels", labels), ("panel", panel), ("training", training))
    if tuple((name, type(record)) for name, record in products) != SOURCE_OUTPUTS:
        raise ValueError("native source preparation changes its complete typed information-role census")
    return products
