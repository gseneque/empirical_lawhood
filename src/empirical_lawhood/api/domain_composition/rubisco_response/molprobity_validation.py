# SPDX-License-Identifier: MPL-2.0
"""Prepare, execute and independently read coordinate-bound MolProbity selections."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.domain_composition.rubisco_response.active_scaffolds import (
    read_active_gp_scaffolds,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_export import (
    export_models,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import (
    file_sha,
    json_bytes,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_parent import (
    PARENT,
    export_parent,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molprobity_read import (
    COMPONENTS,
    assess_model,
)
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import (
    native_result_reader,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import (
    CAPABILITY as PARENT_CAPABILITY,
    GpGeometryRepairConfig,
    GpGeometryRepairResult,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import (
    MODEL_NAMES,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import (
    CAPABILITY,
    GpAmberOperationConfig,
    GpAmberPreparationResult,
)
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import validate_sha256

from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import (
    selected_bytes,
    strict_json,
)
from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_runtime import (
    run_validation_driver,
)
from empirical_lawhood.api.domain_composition.rubisco_response.construction_operations import (
    context_file,
    original_wave,
    relative,
)


@dataclass(frozen=True)
class MolProbitySelection:
    command: str
    context: Path
    operator_profile: Path
    output_directory: Path
    authoring_directory: Path | None = None
    scaffold_directory: Path | None = None
    export_directory: Path | None = None
    export_sha256: str | None = None
    runtime_receipt_sha256: str | None = None
    runtime_prefix: Path | None = None
    timeout_seconds: int | None = None
    restraint: tuple[tuple[str, str], ...] = ()
    run_directory: Path | None = None
    run_sha256: str | None = None

    def __post_init__(self):
        required = {
            "export": ("authoring_directory", "scaffold_directory"),
            "export-parent": ("authoring_directory",),
            "run": (
                "export_directory",
                "export_sha256",
                "runtime_receipt_sha256",
                "runtime_prefix",
                "timeout_seconds",
            ),
            "assess": (
                "export_directory",
                "export_sha256",
                "runtime_receipt_sha256",
                "run_directory",
                "run_sha256",
            ),
        }
        if self.command not in required or any(
            getattr(self, key) is None for key in required[self.command]
        ):
            raise ValueError(
                "Select the original inputs required by this structural operation"
            )
        if self.command == "run" and (
            type(self.timeout_seconds) is not int or self.timeout_seconds <= 0
        ):
            raise ValueError("Supply a positive wall-clock limit per material")


ROSTERS = {
    "MATCHED_ACTIVE_CHILDREN": list(MODEL_NAMES),
    "COMMON_INHIBITED_PARENT": [PARENT],
}


def original_material_pins(export, row):
    def identity(doc):
        record = ObjectIdentity(**doc["value"])
        if doc != record.to_document():
            raise ValueError(
                "Validation export has no canonical original object identity"
            )
        return record

    source, model = identity(export["source"]), identity(row["model"])
    identity(row["definition"])
    if (
        row["construction_disposition"] not in ("FALSIFIED", "SATISFIED")
        or row["validated_material_eligible"]
        is not (row["construction_disposition"] == "SATISFIED")
        or type(row["construction_findings"]) is not list
        or bool(row["construction_findings"]) == row["validated_material_eligible"]
    ):
        raise ValueError(
            "Available structural material changes its original construction eligibility"
        )
    for key in (
        "assessment_sha256",
        "completion_sha256",
        "mmcif_sha256",
        "atom_map_sha256",
        "coordinate_array_sha256",
    ):
        validate_sha256(row[key])
    validate_sha256(export["construction_sha256"])
    if export["roster"] == "COMMON_INHIBITED_PARENT":
        identity(row["parent_integrity"])
        identity(row["original_geometry_receipt"])
        if (
            model != source
            or source.object_schema
            != "empirical-lawhood/rubisco-response/gp-geometry-repair-input"
            or row["original_ligand"] != "CAP"
            or row["physical_periodicity"] != "NONPERIODIC"
        ):
            raise ValueError(
                "Single-parent validation substitutes its original material, ligand or physical boundary"
            )
        for key in (
            "native_receipt_sha256",
            "raw_topology_sha256",
            "raw_endpoint_nm_npy_sha256",
            "original_atom_origins_sha256",
            "heavy_join_sha256",
        ):
            validate_sha256(row[key])
    else:
        if (
            source.object_schema
            != "empirical-lawhood/rubisco-response/gp-initial-amber-input"
            or model.object_schema
            != "empirical-lawhood/rubisco-response/gp-amber-model-input"
        ):
            raise ValueError(
                "Matched validation requires its original Amber source and material"
            )
        for key in ("scaffold", "material", "chemical_graph"):
            identity(row[key])
        validate_sha256(row["receipt_sha256"])
        for key, kind in (("topology", "topology"), ("relaxed_restart", "coordinates")):
            material = identity(row[key])
            if (
                material.object_schema
                != "empirical-lawhood/rubisco-response/native-amber-" + kind + "-bytes"
                or material.object_id
                != "native.initial-amber." + kind + "." + material.object_fingerprint
            ):
                raise ValueError(
                    "Matched validation substitutes a native topology or relaxed restart identity"
                )


def original_export(directory, digest):
    if directory.is_symlink():
        raise ValueError("Select an original validation export")
    record = strict_json(selected_bytes(directory / "export.json", digest, 8 * 2**20))
    if (
        record["schema"] != "el-molprobity-export-1"
        or record["roster"] not in ROSTERS
        or [m["name"] for m in record["models"]] != ROSTERS[record["roster"]]
        or any(
            r["status"] not in ("EXPORTED", "CONSTRUCTION_UNAVAILABLE")
            for r in record["models"]
        )
    ):
        raise ValueError("Select the complete tagged parent or four-material roster")
    for row in record["models"]:
        if row["status"] == "EXPORTED":
            original_material_pins(record, row)
            child = directory / row["name"]
            if child.is_symlink():
                raise ValueError("Exported material directory is indirect")
            for filename, field in (
                ("model.cif", "mmcif_sha256"),
                ("atom-map.json", "atom_map_sha256"),
            ):
                path = child / filename
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or file_sha(path) != row[field]
                ):
                    raise ValueError(
                        "Exported coordinate material or atom mapping differs from the original"
                    )
    return record


def terms_selected(args, dest):
    paths, names = [], set()
    for name, digest in args.restraint:
        source = Path(name)
        if (
            not source.is_absolute()
            or source.suffix.lower() != ".cif"
            or digest in names
        ):
            raise ValueError(
                "Select distinct original absolute restraint CIFs with their SHA-256"
            )
        raw = selected_bytes(source, digest, 32 * 2**20)
        names.add(digest)
        path = dest / (digest + ".cif")
        with path.open("xb") as stream:
            stream.write(raw)
        paths.append(path)
    return paths


def run_components(args, dest):
    from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_driver
    from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_runtime import (
        verify_runtime,
    )

    if args.timeout_seconds <= 0:
        raise ValueError("Supply a positive wall-clock limit per material")
    export = original_export(args.export_directory, args.export_sha256)
    engine = verify_runtime(
        args.runtime_prefix, receipt_sha256=args.runtime_receipt_sha256
    )
    driver = Path(molprobity_driver.__file__).resolve()
    driver_sha = file_sha(driver)
    restraints = terms_selected(args, dest)
    rows = []
    try:
        for model in export["models"]:
            name = model["name"]
            row = dict(
                name=name,
                export_row_sha256=sha256(json_bytes(model)).hexdigest(),
                status=model["status"],
            )
            rows.append(row)
            if row["status"] != "EXPORTED":
                continue
            selected = args.export_directory / name
            work = dest / name
            work.mkdir()
            try:
                completed = run_validation_driver(
                    engine,
                    driver,
                    selected,
                    work,
                    work_directory=work,
                    log_path=work / "native.log",
                    restraints=restraints,
                    timeout=args.timeout_seconds,
                )
                row.update(
                    status="FINISHED"
                    if completed.returncode == 0
                    else "NATIVE_FAILURE",
                    returncode=completed.returncode,
                )
            except subprocess.TimeoutExpired:
                row.update(status="TIMED_OUT", returncode=None)
            metadata = work / "components.json"
            row.update(
                log_sha256=file_sha(work / "native.log"),
                components_sha256=file_sha(metadata) if metadata.is_file() else None,
            )
    finally:
        # Verify input, configuration, source and installed native files through the whole use.
        original_export(args.export_directory, args.export_sha256)
        if (
            driver_sha != file_sha(driver)
            or engine
            != verify_runtime(
                args.runtime_prefix, receipt_sha256=args.runtime_receipt_sha256
            )
            or any(file_sha(p) != p.stem for p in restraints)
        ):
            raise ValueError(
                "Validator runtime, source or selected restraints changed during the batch"
            )
    return dict(
        schema="el-molprobity-run-1",
        roster=export["roster"],
        export_sha256=args.export_sha256,
        engine_receipt_sha256=engine["receipt_sha256"],
        lock_sha256=engine["lock_sha256"],
        cctbx_version=engine["cctbx_version"],
        driver_sha256=driver_sha,
        restraint_sha256=[p.stem for p in restraints],
        per_model_timeout_seconds=args.timeout_seconds,
        xh_distance_convention="NUCLEAR",
        keep_input_hydrogens=True,
        allow_nqh_flips=False,
        models=rows,
    )


def review_batch(args):
    export = original_export(args.export_directory, args.export_sha256)
    run = strict_json(
        selected_bytes(args.run_directory / "run.json", args.run_sha256, 8 * 2**20)
    )
    if (
        run["schema"] != "el-molprobity-run-1"
        or run["export_sha256"] != args.export_sha256
        or run["engine_receipt_sha256"] != args.runtime_receipt_sha256
        or not run["keep_input_hydrogens"]
        or run["allow_nqh_flips"]
        or run["xh_distance_convention"] != "NUCLEAR"
        or run["roster"] != export["roster"]
        or [r["name"] for r in run["models"]] != ROSTERS[export["roster"]]
    ):
        raise ValueError(
            "Selected external report has another material, runtime, mode or incomplete roster"
        )
    from empirical_lawhood.adapters.rubisco.rubisco_response import molprobity_driver

    if file_sha(Path(molprobity_driver.__file__)) != run["driver_sha256"]:
        raise ValueError(
            "Select the original independent structural validation driver revision"
        )
    for digest in run["restraint_sha256"]:
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid retained restraint identity")
        selected_bytes(args.run_directory / (digest + ".cif"), digest, 32 * 2**20)
    rows = []
    for model, returned in zip(export["models"], run["models"], strict=True):
        name = model["name"]
        if returned["export_row_sha256"] != sha256(json_bytes(model)).hexdigest():
            raise ValueError(
                "External case result substitutes another topology, restart, model or scaffold"
            )
        row = dict(
            name=name,
            export_row_sha256=returned["export_row_sha256"],
            native_status=returned["status"],
            original_construction_disposition=model["construction_disposition"],
            original_construction_findings=model["construction_findings"],
            validated_material_eligible=model["validated_material_eligible"],
        )
        rows.append(row)
        if model["status"] == "CONSTRUCTION_UNAVAILABLE":
            if returned["status"] != model["status"]:
                raise ValueError(
                    "A missing original received external validation results"
                )
            row.update(status="UNEVALUABLE", unreturned=list(COMPONENTS))
            continue
        directory = args.run_directory / name
        log = directory / "native.log"
        if (
            returned["status"] not in ("FINISHED", "NATIVE_FAILURE", "TIMED_OUT")
            or directory.is_symlink()
            or log.is_symlink()
            or file_sha(log) != returned["log_sha256"]
        ):
            raise ValueError("External native report or its exact log was substituted")
        if not returned["components_sha256"]:
            row.update(status="UNEVALUABLE", unreturned=list(COMPONENTS))
            continue
        details = strict_json(
            selected_bytes(
                directory / "components.json", returned["components_sha256"], 8 * 2**20
            )
        )
        if (
            details["input_mmcif_sha256"] != model["mmcif_sha256"]
            or details["input_atom_map_sha256"] != model["atom_map_sha256"]
        ):
            raise ValueError(
                "External native report did not read this exact CIF and topology mapping"
            )
        table = strict_json(
            selected_bytes(
                args.export_directory / name / "atom-map.json", model["atom_map_sha256"]
            )
        )
        row.update(assess_model(directory, table, details))
        if returned["status"] != "FINISHED":
            row["status"] = "UNEVALUABLE"
    return dict(
        schema="el-molprobity-review-1",
        roster=export["roster"],
        export_sha256=args.export_sha256,
        run_sha256=args.run_sha256,
        models=rows,
        independent_biological_units=0,
        full_chemistry_or_forecast="UNEVALUABLE",
    )


def validate_structure(args: MolProbitySelection):
    """Operate on the selected matched children or inhibited parent under its own storage profile."""
    context = context_file(args.context)
    if (
        context.operator_profile != args.operator_profile
        or context.python_executable != Path(sys.executable).absolute()
    ):
        raise ValueError(
            "Use the selected original operator profile and application interpreter"
        )
    _, _, plane = application_storage(context, for_write=True)
    for field in (
        "authoring_directory",
        "scaffold_directory",
        "export_directory",
        "run_directory",
    ):
        folder = getattr(args, field, None)
        if folder is not None:
            plane.root.resolve(relative(folder, plane), for_write=False)
    dest = plane.root.resolve(relative(args.output_directory, plane), for_write=True)
    dest.mkdir(parents=True, exist_ok=False)
    try:
        if args.command == "export":
            _, config, original = original_wave(
                args.authoring_directory,
                plane,
                CAPABILITY,
                GpAmberOperationConfig,
                GpAmberPreparationResult,
            )
            scaffolds = read_active_gp_scaffolds(
                directory_relative_path=relative(args.scaffold_directory, plane),
                artifact_writer=plane,
            )
            with native_result_reader(plane, original.units[0]) as native:
                record = export_models(
                    config.source, original, scaffolds["scaffolds"], native, dest
                )
            record["context_sha256"] = context.fingerprint()
        elif args.command == "export-parent":
            _, config, original = original_wave(
                args.authoring_directory,
                plane,
                PARENT_CAPABILITY,
                GpGeometryRepairConfig,
                GpGeometryRepairResult,
            )
            with native_result_reader(plane, original) as native:
                record = export_parent(config.source, original, native, dest)
            record["context_sha256"] = context.fingerprint()
        elif args.command == "run":
            record = run_components(args, dest)
        else:
            record = review_batch(args)
        path = dest / (
            "export.json" if args.command == "export-parent" else args.command + ".json"
        )
        with path.open("xb") as stream:
            stream.write(json_bytes(record))
        plane.root.resolve(relative(path, plane), for_write=False)
        return {"record": str(path), "sha256": file_sha(path)}
    except Exception as error:
        with (dest / "failure.json").open("xb") as stream:
            stream.write(
                json_bytes(
                    dict(
                        operation=args.command,
                        error_type=type(error).__name__,
                        detail=str(error),
                    )
                )
            )
        raise
