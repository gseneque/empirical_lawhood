# SPDX-License-Identifier: MPL-2.0
"""Score only the Gp 209–211 KCX neighborhood beside the original native ramalyze rows."""

from collections import Counter
from hashlib import sha256
from dataclasses import dataclass
import math
from pathlib import Path

from empirical_lawhood.adapters.rubisco.rubisco_response import (
    kcx_backbone_driver,
    molprobity_driver,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_runtime import (
    run_validation_driver,
    verify_runtime,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import (
    file_sha,
    json_bytes,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_read import (
    assessed_result,
    eligible_residue,
    finite,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import (
    selected_bytes,
    strict_json,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_validation import (
    original_export,
)


@dataclass(frozen=True)
class BackboneSelection:
    export_directory: Path
    component_directory: Path
    runtime_prefix: Path
    output_directory: Path
    material: str
    export_sha256: str
    components_sha256: str
    runtime_receipt_sha256: str
    timeout_seconds: int

    def __post_init__(self):
        for path in (
            self.export_directory,
            self.component_directory,
            self.runtime_prefix,
            self.output_directory,
        ):
            if not path.is_absolute() or path.resolve() != path:
                raise ValueError("Select absolute, direct input and output paths")
        if type(self.timeout_seconds) is not int or self.timeout_seconds <= 0:
            raise ValueError("Supply a positive supplemental deadline in seconds")


def native_ramalyze(directory, metadata, table):
    """Bind every original native row and retain its denominator and classification."""
    returned = metadata["components"]["ramalyze"]
    if returned["status"] != "RETURNED":
        raise ValueError(
            "Supply a returned original ramalyze component for this separate comparison"
        )
    raw = selected_bytes(directory / "ramalyze.jsonl", returned["sha256"])
    rs = table["residues"]
    keys = {(r["chain"], r["seq"], r["component"]): i for i, r in enumerate(rs)}
    if len(keys) != len(rs):
        raise ValueError("Ambiguous source residue in the selected structural evidence")
    seen = {}
    for line in raw.splitlines():
        if not line or len(line) > 256 * 1024:
            raise ValueError("Invalid original ramalyze row length")
        row = strict_json(line)
        i, _, _, _ = assessed_result("ramalyze", row, keys, {})
        if (
            str(row["model_id"]).strip() != metadata["input_census"]["model_id"]
            or i in seen
        ):
            raise ValueError(
                "Native ramalyze row duplicates a residue or selects another model"
            )
        seen[i] = row
    if len(raw) != returned["bytes"]:
        raise ValueError("Native ramalyze byte denominator changed")
    return seen, ramalyze_summary(table, returned, seen)


def ramalyze_summary(table, returned, seen):
    """Compare the complete previously authenticated row index with the native census."""
    if returned["status"] != "RETURNED" or len(seen) != returned["rows"]:
        raise ValueError("Supply the complete returned native ramalyze row census")
    rs = table["residues"]
    categories = Counter()
    for row in seen.values():
        if (
            any(abs(finite(row[key])) > 180 for key in ("phi", "psi"))
            or not 0 <= finite(row["score"]) <= 100
        ):
            raise ValueError(
                "Original native ramalyze angle or reference value lies outside its physical domain"
            )
        categories[row["rama_type"].upper()] += 1
    if (
        returned.get("native_total", len(seen)) != len(seen)
        or returned.get("native_favored", categories["FAVORED"])
        != categories["FAVORED"]
    ):
        raise ValueError("Native ramalyze summary disagrees with original rows")
    expected = {i for i, r in enumerate(rs) if eligible_residue("ramalyze", r)}
    return dict(
        assigned=len(expected),
        returned=len(seen),
        joined=len(expected.intersection(seen)),
        categories=dict(categories),
        missing_native_residues=sorted(expected.difference(seen)),
        extra_native_residues=sorted(set(seen).difference(expected)),
        original_rows_sha256=returned["sha256"],
        original_component_metadata=returned,
    )


def compare(native, row):
    return (
        native["res_type"] == row["reference_class"]
        and native["rama_type"].upper() == row["category"]
        and native["outlier"] is row["outlier"]
        and all(
            abs(math.remainder(native[key] - row[key + "_deg"], 360)) <= 1e-7
            for key in ("phi", "psi")
        )
        and math.isclose(
            native["score"], row["ramalyze_score"], rel_tol=1e-10, abs_tol=1e-8
        )
    )


def assess_supplement(table, report, seen, native_summary):
    expected = kcx_backbone_driver.target_backbones(table)
    rows = report["rows"]
    if len(rows) != len(expected):
        raise ValueError("Incomplete supplementary large-subunit roster")
    groups = {"STANDARD_AMINO_ACID": Counter(), "PARENT_LYS_GENERAL_PROXY": Counter()}
    counts = Counter()
    controls, targets = [], []
    for selected, row in zip(expected, rows, strict=True):
        if any(row.get(key) != v for key, v in selected.items() if key != "status"):
            raise ValueError(
                "Supplement substitutes the original atom mapping or reference class"
            )
        if (
            selected["status"] == "UNEVALUABLE"
            and row["status"] != "UNEVALUABLE"
            or row["status"] not in ("UNEVALUABLE", "MEASURED")
        ):
            raise ValueError(
                "Supplement changed an unavailable topology or native measurement"
            )
        native = seen.get(row["native_residue_index"])
        row = dict(row, native_ramalyze_returned=native is not None)
        if row["status"] == "MEASURED":
            if (
                any(abs(finite(row[key])) > 180 for key in ("phi_deg", "psi_deg"))
                or not 0 <= finite(row["cctbx_raw_table_value"]) <= 1
                or row["ramalyze_score"] != row["cctbx_raw_table_value"] * 100
                or row["category"] not in ("FAVORED", "ALLOWED", "OUTLIER")
                or row["outlier"] is not (row["category"] == "OUTLIER")
            ):
                raise ValueError(
                    "Invalid supplementary angles, score or reference category"
                )
        if row["role"] == "NATIVE_FLANK_CONTROL":
            row["matches_original_native_row"] = bool(
                row["status"] == "MEASURED" and native and compare(native, row)
            )
            controls.append(row)
        else:
            targets.append(row)
    sound = {
        row["chain"]
        for row in controls
        if all(
            other["matches_original_native_row"]
            for other in controls
            if other["chain"] == row["chain"]
        )
    }
    for row in targets:
        row["both_flanks_match_native"] = row["chain"] in sound
        if row["status"] == "MEASURED" and row["both_flanks_match_native"]:
            groups[row["reference_scope"]][row["category"]] += 1
            if not row["native_ramalyze_returned"]:
                counts[row["reference_scope"]] += 1
    measured = sum(sum(c.values()) for c in groups.values())
    return dict(
        native_ramalyze=native_summary,
        assigned_supplementary_positions=len(targets),
        evaluated_with_two_flank_controls=measured,
        native_flank_controls=controls,
        supplementary_positions=targets,
        categories_by_reference_scope={scope: dict(c) for scope, c in groups.items()},
        additional_missing_native_positions_by_reference_scope=dict(counts),
        status="COMPLETE_SCOPED_BACKBONE_OBSERVATIONS"
        if measured == 24
        else "INCOMPLETE_SCOPED_BACKBONE_OBSERVATIONS",
        kcx_chemical_reference_transfer="UNEVALUABLE",
        modifies_native_molprobity_scores=False,
    )


def assess_files(args: BackboneSelection):
    export = original_export(args.export_directory, args.export_sha256)
    (model,) = (r for r in export["models"] if r["name"] == args.material)
    if model["status"] != "EXPORTED":
        raise ValueError("Selected construction has no original diagnostic coordinates")
    source = args.export_directory / args.material
    metadata = strict_json(
        selected_bytes(
            args.component_directory / "components.json",
            args.components_sha256,
            8 * 2**20,
        )
    )
    table = strict_json(
        selected_bytes(source / "atom-map.json", model["atom_map_sha256"])
    )
    if (
        metadata["input_mmcif_sha256"] != model["mmcif_sha256"]
        or metadata["input_atom_map_sha256"] != model["atom_map_sha256"]
        or metadata["input_census"]["coordinate_array_sha256"]
        != model["coordinate_array_sha256"]
        or metadata["input_census"]["atom_count"] != len(table["atoms"])
        or table["coordinate_array_sha256"] != model["coordinate_array_sha256"]
    ):
        raise ValueError(
            "Select the original ramalyze input with identical coordinates and topology mapping"
        )
    seen, native = native_ramalyze(args.component_directory, metadata, table)
    engine = verify_runtime(
        args.runtime_prefix, receipt_sha256=args.runtime_receipt_sha256
    )
    identities = {
        Path(module.__file__).name: file_sha(Path(module.__file__))
        for module in (kcx_backbone_driver, molprobity_driver)
    }
    reviewer_path = Path(__file__).resolve()
    reviewer_sha = file_sha(reviewer_path)
    out = args.output_directory
    out.mkdir(parents=True, exist_ok=False)
    raw = out / "original-cctbx-supplement.json"
    try:
        run_validation_driver(
            engine,
            Path(kcx_backbone_driver.__file__).resolve(),
            source,
            raw,
            work_directory=out,
            log_path=out / "native.log",
            timeout=args.timeout_seconds,
            check=True,
        )
        raw_bytes = raw.read_bytes()
        returned = strict_json(raw_bytes)
        if returned["input_census"] != metadata["input_census"]:
            raise ValueError(
                "Supplementary CCTBX analysis used another model or atom population"
            )
        assessment = assess_supplement(table, returned, seen, native)
    finally:
        if (
            original_export(args.export_directory, args.export_sha256) != export
            or file_sha(args.component_directory / "components.json")
            != args.components_sha256
            or file_sha(args.component_directory / "ramalyze.jsonl")
            != native["original_rows_sha256"]
            or any(
                identities[Path(m.__file__).name] != file_sha(Path(m.__file__))
                for m in (kcx_backbone_driver, molprobity_driver)
            )
            or file_sha(reviewer_path) != reviewer_sha
            or engine
            != verify_runtime(
                args.runtime_prefix, receipt_sha256=args.runtime_receipt_sha256
            )
        ):
            raise ValueError(
                "Selected material, native observations, source or reference tables changed during analysis"
            )
    assessment.update(
        schema="el-gp-kcx-backbone-supplement-1",
        export_sha256=args.export_sha256,
        roster=export["roster"],
        material=args.material,
        source=export["source"],
        export_material_sha256=sha256(json_bytes(model)).hexdigest(),
        construction_disposition=model["construction_disposition"],
        components_sha256=args.components_sha256,
        coordinate_array_sha256=model["coordinate_array_sha256"],
        original_map_sha256=model["atom_map_sha256"],
        input_mmcif_sha256=model["mmcif_sha256"],
        cctbx_version=engine["cctbx_version"],
        runtime_receipt_sha256=args.runtime_receipt_sha256,
        driver_source_sha256=identities,
        assessor_source_sha256=reviewer_sha,
        native_log_sha256=file_sha(out / "native.log"),
        native_supplement_sha256=sha256(raw_bytes).hexdigest(),
        original_native_overall_score_if_reported=metadata.get(
            "cctbx_molprobity_score"
        ),
    )
    path = out / "kcx-backbone.json"
    with path.open("xb") as stream:
        stream.write(json_bytes(assessment))
    return path
