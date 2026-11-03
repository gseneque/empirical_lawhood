"""Synthetic source fixtures check denominators, exact tokens and exposed roles."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from io import StringIO
import csv
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import csv_source

from empirical_lawhood.adapters.physical.rubisco_kinetics.csv_source import (
    CROSSWALK_HEADERS, FLAMHOLZ_HEADERS, NativeKineticCSVTableV1,
    ReportedQuantityKind, SourceCSVProfile, SourceQuantityAdmission, decode_source_csv,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.records import (
    HistoricalFeatureSliceV1, HistoricalLabelSliceV1, HistoricalTrainingSliceV1,
    ReportedSubstitutionV1,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.rr2018 import (
    DOI, HEADERS, LABELS, MAX_INPUT_BYTES, Rr2018NativeAuditV1, decode_rr2018,
    role_slices, selected_endpoints, selected_features,
)
from empirical_lawhood.kernel.decoding import decode_canonical_record


def article() -> bytes:
    root = Element("article")
    meta = SubElement(SubElement(root, "front"), "article-meta")
    SubElement(meta, "article-id", {"pub-id-type": "doi"}).text = DOI
    table = SubElement(SubElement(root, "table-wrap", {"id": "Tab1"}), "table")
    for cells in (HEADERS, *((label, "synthetic", "1", "1 ± 0", "2 ± 0.1", "1 ± 0",
                              "3 ± 0.2", "1 ± 0", "1 ± 0") for label in LABELS)):
        row = SubElement(table, "tr")
        for value in cells:
            SubElement(row, "td").text = value
    return tostring(root, encoding="utf-8")


def decode_article(payload: bytes) -> Rr2018NativeAuditV1:
    return decode_rr2018(payload, expected_sha256=sha256(payload).hexdigest())


def test_complete_roster_exclusions_and_feature_label_separation():
    payload = article()
    audit = decode_article(payload + b" " * (MAX_INPUT_BYTES - len(payload)))
    assert len(audit.rows) == 9
    assert sum(r.disposition == "INCLUDED" for r in audit.rows) == 3
    assert sum(r.disposition == "EXCLUDED_MULTIPLE_SUBSTITUTIONS" for r in audit.rows) == 2
    assert sum(r.disposition == "EXCLUDED_ANCESTRAL_PARENT" for r in audit.rows) == 4
    assert audit.rows[1].native_cells[6] == "3 ± 0.2"
    assert not audit.physical_independent_units_known
    assert not audit.biological_joint_uncertainty_available
    assert not audit.supplement_bytes_verified
    assert decode_canonical_record(audit.to_document(), Rr2018NativeAuditV1) == audit
    assert tuple(e.sample_id for e in selected_endpoints(audit)) == ("d206e", "m100t", "wt")
    assert tuple(f.position for f in selected_features(audit)) == (206, 100, None)
    slices = role_slices(audit)
    assert len(slices) == 6
    for fold in ("site100", "site206"):
        records = [s for s in slices if s.fold_id == fold]
        training = next(s for s in records if isinstance(s, HistoricalTrainingSliceV1))
        features = next(s for s in records if isinstance(s, HistoricalFeatureSliceV1))
        labels = next(s for s in records if isinstance(s, HistoricalLabelSliceV1))
        assert b'"endpoints"' not in features.canonical_bytes()
        assert {e.sample_id for e in training.endpoints}.isdisjoint(e.sample_id for e in labels.endpoints)
        assert len(features.features) == len(labels.endpoints) == 1
        for record in records:
            assert decode_canonical_record(record.to_document(), type(record)) == record


@pytest.mark.parametrize("change", [
    lambda p: p.replace(b"s41598-018-23869-3", b"wrong-doi"),
    lambda p: p.replace(b"Clone 11", b"Clone 12"),
    lambda p: p.replace(b"kcatC (s-1)", b"kcatC (min-1)"),
    lambda p: b'<!DOCTYPE article [<!ENTITY e "expanded">]>' + p,
    lambda p: (b'<!DOCTYPE article [<!ENTITY e "expanded">]>' + p).decode().encode("utf-16"),
    lambda p: p + b" " * MAX_INPUT_BYTES,
    lambda p: p.replace(b"</article>", b'<table-wrap id="Tab1"/></article>'),
    lambda p: p.replace("3 ± 0.2".encode(), b"3"),
])
def test_changed_or_hostile_article_refused(change):
    with pytest.raises(ValueError):
        decode_article(change(article()))


def test_source_hash_and_unverified_supplement_refused():
    with pytest.raises(ValueError, match="custody"):
        decode_rr2018(article(), expected_sha256="0" * 64)
    with pytest.raises(ValueError, match="supplement"):
        decode_rr2018(article(), expected_sha256=sha256(article()).hexdigest(), supplement_payload=b"wrong")
    with pytest.raises(ValueError, match="evidence ceiling"):
        replace(decode_article(article()), biological_joint_uncertainty_available=True)


def test_residue_delta_preserves_exact_historical_feature_convention():
    mutation = ReportedSubstitutionV1("m100t", "M100T")
    assert mutation.position == 100 and mutation.ancestral_residue == "M" and mutation.replacement_residue == "T"
    assert sum(mutation.vector()) == 0
    assert sum(v * v for v in mutation.vector()) == 2
    assert not any(ReportedSubstitutionV1("wt", "WT").vector())
    with pytest.raises(ValueError):
        ReportedSubstitutionV1("bad", "M100M")


def csv_payload(headers: tuple[str, ...], changes: dict[str, str] | None = None) -> bytes:
    row = dict.fromkeys(headers, "")
    row.update({"identifier": "synthetic-parent", "primary": "1" if headers == FLAMHOLZ_HEADERS else "TRUE"})
    row.update(changes or {})
    out = StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(headers)
    writer.writerow(tuple(row[h] for h in headers))
    return out.getvalue().encode()


def decode_csv(payload: bytes, profile=SourceCSVProfile.FLAMHOLZ_SOURCE):
    return decode_source_csv(payload, expected_sha256=sha256(payload).hexdigest(), profile=profile)


def test_missing_endpoint_ambiguous_conditions_and_native_sd_header_are_preserved():
    payload = csv_payload(FLAMHOLZ_HEADERS, {"vC": "1.600", "vC_SD": "0.10", "S": "", "pH": "7.2 or 8.0",
                                           "temp_C": "25", "primary": "0", "pmid_or_doi": "review-only"})
    table = decode_csv(payload)
    row = table.rows[0]
    turnover = row.quantity(ReportedQuantityKind.KCAT_C)
    specificity = row.quantity(ReportedQuantityKind.SPECIFICITY_CO)
    assert turnover.value == Decimal("1.600") and turnover.native_value == "1.600"
    assert turnover.error_header == "vC_SD" and turnover.error == Decimal("0.10")
    assert turnover.native_ph == "7.2 or 8.0" and turnover.ph is None
    assert specificity.value is None and not row.primary_source_flag
    assert not table.physical_independent_units_known and not table.biological_joint_uncertainty_available
    assert table.exposure == "EXPOSED_DEVELOPMENT_SOURCE"
    assert decode_canonical_record(table.to_document(), NativeKineticCSVTableV1) == table
    with pytest.raises(ValueError, match="projections"):
        replace(table, rows=(replace(row, primary_source_flag=True),))


def test_endpoint_specific_conditions_override_shared_metadata_without_dropping_it():
    payload = csv_payload(CROSSWALK_HEADERS, {"kcat_val": "4.50", "kcat_T": "30", "temp": "25", "pH": "8.0",
                                            "S_val": "80", "S_pH": "8.1", "note": "Distinct endpoint preparations"})
    table = decode_csv(payload, SourceCSVProfile.DE_PINS_CROSSWALK)
    row = table.rows[0]
    assert row.quantity(ReportedQuantityKind.KCAT_C).temperature_c == Decimal(30)
    assert row.quantity(ReportedQuantityKind.SPECIFICITY_CO).temperature_c == Decimal(25)
    assert row.quantity(ReportedQuantityKind.KCAT_C).ph == Decimal("8.0")
    assert row.quantity(ReportedQuantityKind.SPECIFICITY_CO).ph == Decimal("8.1")
    assert row.native_cells[CROSSWALK_HEADERS.index("temp")] == "25"


@pytest.mark.parametrize("changes", [{"vC": "=1+2"}, {"vC": "nan"}, {"vC": "1e99999999"},
                                      {"vC": "1e9999999999999999999999999999"},
                                      {"vC_SD": "0.1"}, {"primary": "unknown"}, {"vC": "0"}])
def test_csv_invalid_numerical_or_primary_semantics_refused(changes):
    with pytest.raises(ValueError):
        decode_csv(csv_payload(FLAMHOLZ_HEADERS, changes))


def test_csv_changed_header_width_hash_and_encoding_refused():
    payload = csv_payload(FLAMHOLZ_HEADERS, {"vC": "3.0"})
    for altered in (payload.replace(b"vC_SD", b"vC_SE"), payload + b"extra,row\n", payload + b"\xff"):
        with pytest.raises(ValueError):
            decode_csv(altered)
    with pytest.raises(ValueError, match="custody"):
        decode_source_csv(payload, expected_sha256="0" * 64, profile=SourceCSVProfile.FLAMHOLZ_SOURCE)


def test_known_quantity_role_conflict_retains_raw_value_but_refuses_endpoint_admission(monkeypatch):
    payload = csv_payload(CROSSWALK_HEADERS, {
        "identifier": "marinus_davidi_2020_corrected", "kcat_val": "24.0", "Kc_val": "162", "S_val": "148"})
    # Bind the software fixture to the reviewed disposition rule without claiming
    # it is the physical historical artifact or an eligible scientific source.
    monkeypatch.setattr(csv_source, "CROSSWALK_CONFLICT_SOURCE_SHA256", sha256(payload).hexdigest())
    table = decode_csv(payload, SourceCSVProfile.DE_PINS_CROSSWALK)
    specificity = table.rows[0].quantity(ReportedQuantityKind.SPECIFICITY_CO)
    assert specificity.native_value == "148" and specificity.value == Decimal(148)
    assert specificity.admitted_value is None
    assert specificity.scientific_admission is SourceQuantityAdmission.REJECTED_QUANTITY_ROLE_CONFLICT
    assert specificity.admission_reasons == ("NATIVE_S_VAL_IS_CARBOXYLATION_EFFICIENCY_NOT_SPECIFICITY",)
    assert table.rows[0].quantity(ReportedQuantityKind.KCAT_C).admitted_value == Decimal(24)
    assert table.rows[0].native_cells[CROSSWALK_HEADERS.index("S_val")] == "148"
    with pytest.raises(ValueError, match="projections"):
        altered = replace(specificity, scientific_admission=SourceQuantityAdmission.REPORTED_ENDPOINT_ONLY, admission_reasons=())
        row = replace(table.rows[0], quantities=tuple(altered if q.kind is specificity.kind else q for q in table.rows[0].quantities))
        replace(table, rows=(row,))


def test_known_mixed_identity_row_requires_reconciliation_and_rule_is_exact_source_bound(monkeypatch):
    payload = csv_payload(CROSSWALK_HEADERS, {
        "identifier": "elongatus_davidi_2020_corrected", "kcat_val": "16.4", "Kc_val": "130", "S_val": "162"})
    original_hash = sha256(payload).hexdigest()
    monkeypatch.setattr(csv_source, "CROSSWALK_CONFLICT_SOURCE_SHA256", original_hash)
    table = decode_csv(payload, SourceCSVProfile.DE_PINS_CROSSWALK)
    assert all(q.admitted_value is None for q in table.rows[0].quantities)
    assert all(q.scientific_admission is SourceQuantityAdmission.REJECTED_ROW_IDENTITY_JOIN_CONFLICT for q in table.rows[0].quantities)
    assert table.rows[0].quantity(ReportedQuantityKind.KCAT_C).value == Decimal("16.4")
    assert len(table.rows[0].quantity(ReportedQuantityKind.SPECIFICITY_CO).admission_reasons) == 2
    # A future independently inspected source revision is not silently rewritten
    # using findings bound to different physical bytes.
    changed = payload.replace(b",162,", b",42.7,")
    assert sha256(changed).hexdigest() != original_hash
    revised = decode_csv(changed, SourceCSVProfile.DE_PINS_CROSSWALK)
    assert revised.rows[0].quantity(ReportedQuantityKind.SPECIFICITY_CO).admitted_value == Decimal("42.7")
