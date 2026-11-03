"""Independent native XLSX fixtures exercise source roles and hostile archives."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
from html import escape
from io import BytesIO
import stat
import warnings
import xml.etree.ElementTree as ET
import zipfile

import pytest

from empirical_lawhood.adapters.physical.rubisco_kinetics import direct_panels
from empirical_lawhood.adapters.physical.rubisco_kinetics.direct_panels import (
    DAVIDI_SHEETS, MCDONALD_SHEETS, DavidiCorrectionRowV1, DavidiCorrectionTableV1,
    DirectEndpointPanelV1, build_davidi2020_panel, build_mcdonald2025_panel, decode_tsai2025_correction,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.workbook import (
    MAX_SELECTED_XML_BYTES, NS, OFFICE_REL_NS, REL_NS, NativeWorkbookV1,
    decode_native_workbook,
)
from empirical_lawhood.kernel.decoding import decode_canonical_record


def worksheet(cells):
    root = ET.Element(NS + "worksheet")
    data = ET.SubElement(root, NS + "sheetData")
    rows = {}
    for address, token, formula in cells:
        row_num = int("".join(c for c in address if c.isdigit()))
        if row_num not in rows:
            rows[row_num] = ET.SubElement(data, NS + "row", {"r": str(row_num)})
        numeric = token is not None and token.replace(".", "", 1).replace("-", "", 1).isdigit()
        c = ET.SubElement(rows[row_num], NS + "c", {"r": address, "t": "n" if numeric else "str"})
        if formula is not None:
            ET.SubElement(c, NS + "f").text = formula
        if token is not None:
            ET.SubElement(c, NS + "v").text = token
    return ET.tostring(root, encoding="utf-8")


def workbook_members(sheets):
    workbook = ET.Element(NS + "workbook")
    roster = ET.SubElement(workbook, NS + "sheets")
    rels = ET.Element(REL_NS + "Relationships")
    members = {}
    for i, (name, content) in enumerate(sheets, 1):
        ET.SubElement(roster, NS + "sheet", {"name": name, "sheetId": str(i), OFFICE_REL_NS + "id": f"rId{i}"})
        ET.SubElement(rels, REL_NS + "Relationship", {"Id": f"rId{i}", "Type": OFFICE_REL_NS[1:-1] + "/worksheet",
                                                     "Target": f"worksheets/sheet{i}.xml"})
        members[f"xl/worksheets/sheet{i}.xml"] = content
    members["xl/workbook.xml"] = ET.tostring(workbook, encoding="utf-8")
    members["xl/_rels/workbook.xml.rels"] = ET.tostring(rels, encoding="utf-8")
    return members


def archive(members, extras=()):
    out = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, content in members.items():
                z.writestr(name, content)
            for name, content in extras:
                z.writestr(name, content)
    return out.getvalue()


def decode(payload, sheets):
    return decode_native_workbook(payload, expected_sha256=sha256(payload).hexdigest(), selected_sheets=sheets)


def mcdonald_members():
    raw = []
    kinetic = []
    for address, token in (("F2", "(mol/mol)"), ("G2", "SD"), ("J2", "(s−1)"), ("K2", "SD"), ("S2", "SD")):
        kinetic.append((address, token, None))
    for address, token in (("Z2", "N ="), ("AA2", "Mean"), ("AB2", "Standard Deviation"), ("AC2", "SE of Mean"),
                           ("AP2", "N ="), ("AQ2", "Mean"), ("AR2", "Standard Deviation"), ("AS2", "SE of Mean"),
                           ("CM2", "SE of Mean")):
        raw.append((address, token, None))
    for r in range(3, 11):
        name = "GWS1B" if r == 3 else "GWS1B-TM" if r == 9 else f"GWS1B-M{r}T"
        raw.extend([(f"A{r}", str(r - 2), None), (f"B{r}", name, None),
                    (f"D{r}", "nil" if r == 3 else "R172C, H237R, K446E" if r == 9 else f"M{r}T", None)])
        kinetic.append((f"A{r}", name, f"'{MCDONALD_SHEETS[0]}'!B{r}"))
        for kind in ("turnover", "specificity"):
            ncol, mcol, sdcol, semcol, summary, error, scol, gcol, vcol = (
                ("AP", "AQ", "AR", "AS", "J", "K", "AN", "AL", "AM") if kind == "turnover"
                else ("Z", "AA", "AB", "AC", "F", "G", "X", "V", "W"))
            missing = kind == "specificity" and r == 9
            mean = "nm" if missing else str(r + 10)
            sd = "nm" if missing else "2" if kind == "turnover" and r == 10 else "1.4142135623730951"
            sem = "nm" if missing else "1"
            raw.extend([(f"{ncol}{r}", "0" if missing else "2", None), (f"{mcol}{r}", mean, None),
                        (f"{sdcol}{r}", sd, None), (f"{semcol}{r}", sem, None), (f"{scol}{r}", str(r - 2), None)])
            kinetic.extend([(f"{summary}{r}", mean, f"'{MCDONALD_SHEETS[0]}'!{mcol}{r}"),
                            (f"{error}{r}", sd, f"'{MCDONALD_SHEETS[0]}'!{sdcol}{r}")])
            if not missing:
                for offset, value in enumerate((r + 9, r + 11)):
                    raw.extend([(f"{gcol}{20 + 2*r + offset}", str(r - 2), None),
                                (f"{vcol}{20 + 2*r + offset}", str(value), None)])
    return workbook_members([(MCDONALD_SHEETS[0], worksheet(raw)), (MCDONALD_SHEETS[1], worksheet(kinetic)),
                             ("unselected calculated curve", b"not parsed as measurements")])


def davidi_members():
    spectro = [("A1", "Identifier", None), ("F1", "Protein seq", None), ("G1", "DNA seq", None)]
    radio = [(address, token, None) for address, token in (("A1", "Organism"), ("B1", "Form"),
              ("C1", "Oligomeric state"), ("D1", "kcat [s-1]"), ("G1", "Sc/o"), ("I1", "Identifier"))]
    for r in range(2, 11):
        radio.extend([(f"A{r}", f"organism{r}", None), (f"B{r}", "II", None), (f"C{r}", "L2", None),
                      (f"D{r}", "12.0 ± 0.3", None), (f"G{r}", "20.0 ± 0.1", None), (f"I{r}", f"native-id-{r}", None)])
        spectro.extend([(f"A{r}", f"native-id-{r}", None), (f"F{r}", "MACD", None), (f"G{r}", "ATGGCTTGCGAT", None)])
    return workbook_members([(DAVIDI_SHEETS[0], worksheet(spectro)), (DAVIDI_SHEETS[1], worksheet(radio))])


def test_native_formula_cache_roles_complete_census_and_raw_uncertainty_conflict():
    payload = archive(mcdonald_members())
    native = decode(payload, MCDONALD_SHEETS)
    panel = build_mcdonald2025_panel(native)
    assert len(native.sheet_catalog) == 3 and len(native.worksheets) == 2
    assert "xl/worksheets/sheet3.xml" not in {m.member for m in native.selected_members}
    assert len(panel.rows) == 8 and sum(r.joint_complete for r in panel.rows) == 7
    missing = panel.rows[6]
    assert missing.native_name == "GWS1B-TM" and missing.specificity.reported_mean is None
    assert missing.specificity.summary_cell.token == "nm" and missing.specificity.reported_n == 0
    assert not panel.biological_joint_uncertainty_available and panel.independent_biological_units is None
    first = panel.rows[0].turnover
    assert first.reported_n == 2 and len(first.raw_values) == 2 and first.recomputed_raw_mean == Decimal(13)
    assert first.summary_cell.formula == "'Figure 3 Raw Data + Stats'!AQ3"
    assert first.source_mean_cell.address == "AQ3" and not first.diagnostic_flags
    assert panel.rows[-1].turnover.diagnostic_flags == (
        "REPORTED_SD_DIFFERS_FROM_LISTED_SAMPLE_SD", "REPORTED_SEM_DIFFERS_FROM_SD_OVER_SQRT_REPORTED_N")
    assert "KO_UNCERTAINTY_HEADER_SD_VERSUS_SOURCE_SEM_CONFLICT" in panel.limitations
    assert decode_canonical_record(native.to_document(), NativeWorkbookV1) == native
    assert decode_canonical_record(panel.to_document(), DirectEndpointPanelV1) == panel
    with pytest.raises(ValueError, match="diagnostic"):
        replace(panel.rows[-1].turnover, diagnostic_flags=())
    with pytest.raises(ValueError, match="biological"):
        replace(panel, independent_biological_units=8)


def test_davidi_original_corrected_and_remeasured_rates_remain_separate_sources():
    workbook = decode(archive(davidi_members()), DAVIDI_SHEETS)
    original = build_davidi2020_panel(workbook)
    assert len(original.rows) == 9 and all(r.joint_complete for r in original.rows)
    assert original.rows[0].turnover.reported_mean == Decimal(12)
    assert original.rows[0].turnover.reported_n is None and original.rows[0].turnover.raw_values == ()
    assert len(original.rows[0].sequence_matches) == 1 and original.rows[0].sequence_matches[0].protein_cell.token == "MACD"
    annotation = DavidiCorrectionRowV1("native-id-2", 3, ("organism2", "18.0 ± 0.3", "19.0 ± 0.4"),
                                      "18.0 ± 0.3", "19.0 ± 0.4")
    correction = DavidiCorrectionTableV1("1" * 64, "10.1038/s44318-025-00419-y", "Table1/row3",
                                        ("Enzyme", "Corrected historical", "Remeasured2025"), (annotation,))
    corrected = build_davidi2020_panel(workbook, correction_table=correction)
    assert corrected.rows[0].turnover.reported_mean == Decimal(12)
    assert corrected.rows[0].specificity.reported_mean == Decimal(20)
    assert corrected.rows[0].correction.corrected_historical_turnover_token == "18.0 ± 0.3"
    assert corrected.rows[0].correction.remeasured_2025_turnover_token == "19.0 ± 0.4"
    assert corrected.rows[1].correction is None
    with pytest.raises(ValueError, match="identity"):
        replace(corrected.rows[0], correction=replace(annotation, original_identifier="different-enzyme"))


@pytest.mark.parametrize("hostile_name", ["../outside.xml", "/absolute.xml", "xl\\outside.xml", "xl/./sheet.xml"])
def test_zip_unsafe_names_refused_before_any_xml_decode(hostile_name):
    with pytest.raises(ValueError):
        decode(archive(davidi_members(), [(hostile_name, b"unused")]), DAVIDI_SHEETS)


def test_duplicate_members_symlinks_unsupported_compression_and_hash_refused():
    members = davidi_members()
    with pytest.raises(ValueError):
        decode(archive(members, [("xl/workbook.xml", members["xl/workbook.xml"])]), DAVIDI_SHEETS)
    symlink = zipfile.ZipInfo("xl/link.xml")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(ValueError):
        decode(archive(members, [(symlink, b"../../outside")]), DAVIDI_SHEETS)
    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_BZIP2) as z:
        for name, content in members.items():
            z.writestr(name, content)
    with pytest.raises(ValueError):
        decode(out.getvalue(), DAVIDI_SHEETS)
    with pytest.raises(ValueError, match="custody"):
        decode_native_workbook(archive(members), expected_sha256="0" * 64, selected_sheets=DAVIDI_SHEETS)


@pytest.mark.parametrize("change", [
    lambda b: b'<!DOCTYPE worksheet [<!ENTITY x "expanded">]>' + b,
    lambda b: (b'<!DOCTYPE worksheet [<!ENTITY x "expanded">]>' + b).decode().encode("utf-16"),
    lambda b: b + b" " * MAX_SELECTED_XML_BYTES,
    lambda b: b.replace(b'A1', b'A0'),
])
def test_selected_xml_entities_encoding_size_and_coordinate_refused(change):
    members = davidi_members()
    members["xl/worksheets/sheet1.xml"] = change(members["xl/worksheets/sheet1.xml"])
    with pytest.raises(ValueError):
        decode(archive(members), DAVIDI_SHEETS)


def test_unselected_curve_member_is_inventoried_but_never_expanded_or_parsed():
    members = mcdonald_members()
    members["xl/worksheets/sheet3.xml"] = b'<!DOCTYPE unused [<!ENTITY e "unsafe-if-selected">]>'
    native = decode(archive(members), MCDONALD_SHEETS)
    assert len(native.archive_inventory) == 5 and len(native.selected_members) == 4
    with pytest.raises(ValueError, match="DTD/entity"):
        decode(archive(members), ("unselected calculated curve",))


def test_external_relationship_and_missing_requested_sheet_refused():
    members = davidi_members()
    relationships = ET.fromstring(members["xl/_rels/workbook.xml.rels"])
    relationships[0].set("TargetMode", "External")
    members["xl/_rels/workbook.xml.rels"] = ET.tostring(relationships)
    with pytest.raises(ValueError, match="external"):
        decode(archive(members), DAVIDI_SHEETS)
    with pytest.raises(ValueError, match="absent"):
        decode(archive(davidi_members()), ("missing-sheet",))


def test_changed_formula_join_and_raw_header_units_are_refused():
    members = mcdonald_members()
    altered = dict(members)
    altered["xl/worksheets/sheet2.xml"] = altered["xl/worksheets/sheet2.xml"].replace(b"!AQ3", b"!AQ4")
    with pytest.raises(ValueError, match="formula/cache"):
        build_mcdonald2025_panel(decode(archive(altered), MCDONALD_SHEETS))
    altered = dict(members)
    altered["xl/worksheets/sheet2.xml"] = altered["xl/worksheets/sheet2.xml"].replace("(s−1)".encode(), b"(min-1)")
    with pytest.raises(ValueError, match="units"):
        build_mcdonald2025_panel(decode(archive(altered), MCDONALD_SHEETS))


# Independent software fixtures. Values deliberately differ from published
# measurements; source names are the versioned interpretation under test.
TSAI_NAMES = ("Gallionella", "Zetaproteobacterium", "H. marinus", "Sulfurivirga",
              "Unknown organism (Actinosporangium)", "Zetaproteobacteria_53_45",
              "A. ferrooxidans", "R. rubrum", "S. elongatus")
ORIGINAL_NAMES = ("S. elongatus", "R. rubrum", "A. ferrooxidans", "Zetaproteobacteria_53_45",
                  "Unknown organism", "S. caldicuralii", "H. marinus", "Zetaproteobacterium", "Gallionella sp.")


def named_original_panel(monkeypatch):
    members = davidi_members()
    radio = ET.fromstring(members["xl/worksheets/sheet2.xml"])
    for row, name in enumerate(ORIGINAL_NAMES, 2):
        radio.find(f".//{NS}c[@r='A{row}']/{NS}v").text = name
    members["xl/worksheets/sheet2.xml"] = ET.tostring(radio)
    payload = archive(members)
    monkeypatch.setattr(direct_panels, "DAVIDI_SOURCE_SHA256", sha256(payload).hexdigest())
    workbook = decode(payload, DAVIDI_SHEETS)
    return workbook, build_davidi2020_panel(workbook)


def tsai_html():
    main = ("", "Rate, kcat [s−1]", "Affinity, Km (CO2) [µM]",
            "Carboxylation efficiency, kcat/Km [s−1 mM−1]")
    secondary = ("", "Davidi et al corrected", "This study", "Davidi et al corrected",
                 "This study", "Davidi et al corrected", "This study")
    header = "<tr>" + "".join(f'<th colspan="{span}" rowspan="1">{escape(label)}</th>'
                              for label, span in zip(main, (1, 2, 2, 2), strict=True)) + "</tr>"
    header += "<tr>" + "".join(f'<th colspan="1" rowspan="1">{escape(s)}</th>' for s in secondary) + "</tr>"
    body = []
    for index, name in enumerate(TSAI_NAMES, 1):
        values = (name, f"{index + 20}.0 ± 0.3", f"{index + 30}.0 ± 0.4",
                  f"{index + 200} ± 2", f"{index + 300} ± 3", str(index + 100), str(index + 110))
        body.append("<tr>" + "".join(f"<td>{escape(v)}</td>" for v in values) + "</tr>")
    return ('<!DOCTYPE html><html><head><meta name="citation_doi" content="10.1038/s44318-025-00419-y">'
            '</head><body><section id="Tab1"><table>' + header + "".join(body)
            + "</table></section></body></html>").encode()


def admit_fixture_correction(monkeypatch, payload, original):
    digest = sha256(payload).hexdigest()
    monkeypatch.setattr(direct_panels, "TSAI_2025_SOURCE_SHA256", digest)
    return decode_tsai2025_correction(payload, original, expected_sha256=digest)


def test_native_correction_name_join_retains_columns_and_exact_original_binding(monkeypatch):
    workbook, original = named_original_panel(monkeypatch)
    correction = admit_fixture_correction(monkeypatch, tsai_html(), original)
    assert len(correction.rows) == 9 and len(correction.native_header_rows) == 2
    assert len(correction.native_body_rows) == 9
    assert correction.source_name_aliases[0] == ("Gallionella", "Gallionella sp.", "native-id-10")
    assert correction.rows[0].native_table_row == 3
    assert correction.rows[0].corrected_historical_turnover_token == "21.0 ± 0.3"
    assert correction.rows[0].remeasured_2025_turnover_token == "31.0 ± 0.4"
    assert correction.native_header_rows[0].cells[1].colspan == 2
    corrected = build_davidi2020_panel(workbook, correction_table=correction)
    assert corrected.rows[0].native_name == "S. elongatus"
    assert corrected.rows[0].correction.native_cells[0] == "S. elongatus"
    assert corrected.rows[0].correction.corrected_historical_turnover_token == "29.0 ± 0.3"
    assert corrected.rows[-1].correction.corrected_historical_turnover_token == "21.0 ± 0.3"
    assert all(r.turnover.reported_mean == Decimal(12) and r.specificity.reported_mean == Decimal(20)
               for r in corrected.rows)
    assert "NO_NEW_SPECIFICITY" in correction.interpretation
    assert decode_canonical_record(correction.to_document(), DavidiCorrectionTableV1) == correction
    assert decode_canonical_record(corrected.to_document(), DirectEndpointPanelV1) == corrected
    with pytest.raises(ValueError, match="exact original"):
        replace(corrected, rows=(replace(corrected.rows[0], native_name="wrong original name"), *corrected.rows[1:]))
    with pytest.raises(ValueError, match="original source version"):
        admit_fixture_correction(monkeypatch, tsai_html(), corrected)
    with pytest.raises(ValueError, match="hierarchy"):
        header = correction.native_header_rows[0]
        replace(correction, native_header_rows=(replace(header, cells=(header.cells[0],
            replace(header.cells[1], raw_text="Rate, kcat [min−1]"), *header.cells[2:])), correction.native_header_rows[1]))
    with pytest.raises(ValueError, match="complete source-version"):
        replace(correction, native_body_rows=correction.native_body_rows[:-1])


@pytest.mark.parametrize("change", [
    lambda b: b.replace(b"s44318-025-00419-y", b"wrong-doi"),
    lambda b: b.replace("Rate, kcat [s−1]".encode(), b"Rate, kcat [min-1]"),
    lambda b: b.replace(b'colspan="2"', b'colspan="1"', 1),
    lambda b: b.replace(b"Zetaproteobacterium</td>", b"Gallionella</td>"),
    lambda b: b.replace(b"Gallionella</td>", b"unreviewed enzyme</td>"),
    lambda b: b.replace(b"<td>101</td>", b"<td>nm</td>"),
    lambda b: b.replace(b"<td>101</td>", b"<td>-101</td>"),
    lambda b: b.replace(b"<td>101</td>", b"<td><table></table>101</td>"),
    lambda b: b.replace(b"<!DOCTYPE html>", b'<!DOCTYPE html [<!ENTITY x "unsafe">]>'),
])
def test_correction_refuses_changed_roles_denominator_or_unsafe_html(monkeypatch, change):
    _, original = named_original_panel(monkeypatch)
    with pytest.raises(ValueError):
        admit_fixture_correction(monkeypatch, change(tsai_html()), original)


def test_correction_requires_exact_source_versions_and_complete_original_roster(monkeypatch):
    _, original = named_original_panel(monkeypatch)
    payload = tsai_html()
    digest = sha256(payload).hexdigest()
    monkeypatch.setattr(direct_panels, "TSAI_2025_SOURCE_SHA256", digest)
    with pytest.raises(ValueError, match="custody"):
        decode_tsai2025_correction(payload, original, expected_sha256="0" * 64)
    with pytest.raises(ValueError, match="custody"):
        decode_tsai2025_correction(payload + b" ", original, expected_sha256=digest)
    with pytest.raises(ValueError, match="original source version"):
        decode_tsai2025_correction(payload, replace(original, source_sha256="0" * 64), expected_sha256=digest)
    wrong_name = replace(original, rows=(replace(original.rows[0], native_name="unreviewed name"), *original.rows[1:]))
    with pytest.raises(ValueError, match="denominator"):
        decode_tsai2025_correction(payload, wrong_name, expected_sha256=digest)
