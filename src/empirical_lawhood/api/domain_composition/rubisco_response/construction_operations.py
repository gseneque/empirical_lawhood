# SPDX-License-Identifier: MPL-2.0
"""Prepare and independently read local Gp construction through public owners.

Native execution uses the returned authoring directory with the shared recursive
command. This recipe never constructs task rosters or replays a native contact.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys

from empirical_lawhood.api.application_context import application_storage
from empirical_lawhood.api.application_contracts import (
    ApplicationContext,
    MAX_REQUEST_BYTES,
    absolute_path,
    exact_mapping,
    load_application_json,
)
from empirical_lawhood.api.domain_composition.rubisco_response.active_scaffolds import (
    prepare_active_gp_scaffolds,
)
from empirical_lawhood.api.domain_composition.rubisco_response.construction_preparation import (
    prepare_gp_repair_from_original,
    select_gp_amber_engine,
    select_gp_amber_parameters,
    select_gp_construction_engine,
)
from empirical_lawhood.api.domain_composition.rubisco_response.geometry_repair import (
    author_gp_geometry_repair,
    read_gp_geometry_repair,
)
from empirical_lawhood.api.domain_composition.rubisco_response.initial_amber import (
    author_initial_gp_amber,
    prepare_initial_gp_amber,
    read_initial_gp_amber,
)
from empirical_lawhood.api.domain_composition.rubisco_response.molecular_preparation import (
    read_rubp_template,
)
from empirical_lawhood.api.domain_composition.rubisco_response.preparation_response_analysis import (
    native_result_reader,
)
from empirical_lawhood.api.domain_composition.rubisco_response.refined_geometry import (
    prepare_refined_gp_parent,
)
from empirical_lawhood.api.recursive_execution import read_recursive_wave
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import (
    FileEvidence,
    SourceMember,
)
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import (
    StructuralSourceMember,
)
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import (
    GpRepairNumericEngine,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import (
    AMBER_FRAGMENT_PROTOCOL,
    CARBOXYLATE_REPAIR_PROTOCOL,
    LEGACY_REPAIR_PROTOCOL,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import (
    CAPABILITY as REPAIR,
    AMBER_FRAGMENT_CAPABILITY,
    CARBOXYLATE_CAPABILITY,
    GpGeometryRepairConfig,
    GpGeometryRepairResult,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import (
    GpAmberEngine,
    MODEL_NAMES,
)
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import (
    CAPABILITY as AMBER,
    GpAmberOperationConfig,
    GpAmberPreparationResult,
)
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


FIELDS = {
    "select-engines": (
        "amber_manifest_file",
        "amber_directory",
        "site_packages",
        "interpreter",
    ),
    "select-parameters": ("members",),
    "prepare-parent": (
        "original_context_file",
        "parent_file",
        "assessment_file",
        "gp_source_file",
        "amber_engine_file",
        "numeric_engine_file",
        "native_work_directory",
    ),
    "read-parent": ("authoring_directory",),
    "prepare-scaffolds": (
        "repair_authoring_directory",
        "gp_source_file",
        "case_set_file",
        "methionine_file",
        "ligand_context_file",
        "ligand_directory",
        "component_sha256",
    ),
    "prepare-models": (
        "scaffold_directory",
        "ligand_context_file",
        "ligand_directory",
        "component_sha256",
        "parameter_source_files",
        "amber_engine_file",
        "numeric_engine_file",
        "native_work_directory",
    ),
    "read-models": ("authoring_directory",),
}
OPTIONAL = ("maximum_iterations", "construction_seed", "construction_threads")
PARENT_OPTIONAL = (
    *OPTIONAL,
    "parent_repair_protocol",
    "maximum_refined_displacement_angstrom",
)


def decode_file(path, kind, maximum=512 * 2**20):
    return decode_canonical_bytes(
        read_bounded_bytes(Path(path), maximum_bytes=maximum),
        kind,
        maximum_bytes=maximum,
    )


def context_file(path):
    return ApplicationContext.from_document(
        load_application_json(
            read_bounded_bytes(Path(path), maximum_bytes=MAX_REQUEST_BYTES)
        )
    )


def relative(path, plane):
    return (
        absolute_path(path, "selected path")
        .relative_to(plane.root.contract.canonical_path)
        .as_posix()
    )


def retain(path, record, plane):
    raw = (
        record
        if type(record) is bytes
        else record.canonical_bytes()
        if hasattr(record, "canonical_bytes")
        else (
            json.dumps(
                record, default=json_default, indent=2, sort_keys=True, allow_nan=False
            )
            + "\n"
        ).encode()
    )
    locator = relative(path, plane)
    target = plane.root.resolve(
        locator, for_write=True, operation_minimum_free_bytes=len(raw)
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(raw)
    plane.root.resolve(locator, for_write=False)
    return str(target)


def json_default(value):
    if hasattr(value, "to_document"):
        return value.to_document()
    if isinstance(value, (Path, Decimal)):
        return str(value)
    raise TypeError("Construction output requires explicit serialization")


def validate_request(operation, request):
    required = ("output_directory", *FIELDS[operation])
    optional = (
        PARENT_OPTIONAL
        if operation == "prepare-parent"
        else OPTIONAL
        if operation == "prepare-models"
        else ()
    )
    exact_mapping(request, (*required, *optional), required=required)
    if operation == "prepare-parent":
        protocol = request.get("parent_repair_protocol", LEGACY_REPAIR_PROTOCOL)
        if protocol not in (
            LEGACY_REPAIR_PROTOCOL,
            CARBOXYLATE_REPAIR_PROTOCOL,
            AMBER_FRAGMENT_PROTOCOL,
        ):
            raise ValueError("select a supported parent_repair_protocol")
        if (protocol != LEGACY_REPAIR_PROTOCOL) != (
            "maximum_refined_displacement_angstrom" in request
        ):
            raise ValueError(
                "the named Glu213 repair requires a prospective displacement limit"
            )
        if protocol == AMBER_FRAGMENT_PROTOCOL:
            budget = request.get("maximum_iterations", 2000)
            seed = request.get("construction_seed", 20261114)
            if (
                type(budget) is not int
                or budget < 1
                or type(seed) is not int
                or seed != 20261114
            ):
                raise ValueError(
                    "select a positive finite iteration budget and the fixed seed field 20261114 for Amber fragments"
                )
        if "maximum_refined_displacement_angstrom" in request:
            value = request["maximum_refined_displacement_angstrom"]
            if type(value) is not str:
                raise ValueError(
                    "supply the displacement limit as an exact Decimal string in angstrom"
                )
            try:
                limit = Decimal(value)
            except InvalidOperation as error:
                raise ValueError(
                    "invalid inherited-coordinate displacement limit"
                ) from error
            if not limit.is_finite() or limit <= 0:
                raise ValueError(
                    "supply a finite positive inherited-coordinate displacement limit"
                )
    for name, value in request.items():
        if name.endswith(("_directory", "_file")) or name in (
            "site_packages",
            "interpreter",
        ):
            absolute_path(value, name)
    if "parameter_source_files" in request:
        paths = request["parameter_source_files"]
        if type(paths) is not list or len(paths) != 6 or len(set(paths)) != 6:
            raise ValueError("Select six distinct original Amber parameter records")
        for path in paths:
            absolute_path(path, "parameter_source_files")


def original_wave(directory, plane, capability, config_type, result_type):
    report, products, draft, _ = read_recursive_wave(
        directory=Path(directory), artifact_writer=plane, include_products=True
    )
    allowed = (
        (REPAIR, CARBOXYLATE_CAPABILITY, AMBER_FRAGMENT_CAPABILITY)
        if capability == REPAIR
        else (capability,)
    )
    if len(draft.operations) != 1 or draft.operations[0].node_id not in allowed:
        raise ValueError("Select the original complete construction wave")
    capability = draft.operations[0].node_id
    config = decode_canonical_bytes(
        draft.operations[0].config_payload.encode(),
        config_type,
        maximum_bytes=512 * 2**20,
    )
    results = tuple(
        record
        for record in products["records"].get(capability, {}).values()
        if type(record) is result_type
    )
    if len(results) != 1:
        raise ValueError(
            "Construction has no unique completed original result; inspect its retained operational report"
        )
    return report, config, results[0]


def operate(operation, request, context, plane):
    destination = Path(request["output_directory"])
    if destination.exists() or destination.is_symlink():
        raise ValueError("Select a fresh output directory for this operation")
    plane.root.resolve(relative(destination, plane), for_write=True)
    if operation == "select-parameters":
        sources = select_gp_amber_parameters(members=request["members"])
        return dict(
            parameter_source_files=[
                retain(destination / (source.member_id + ".json"), source, plane)
                for source in sources
            ],
            new_native_calls=0,
        )
    if operation == "select-engines":
        manifest = json.loads(
            read_bounded_bytes(
                Path(request["amber_manifest_file"]), maximum_bytes=4 * 2**20
            )
        )
        if (manifest.get("schema"), manifest.get("version")) != (
            "empirical-lawhood/native-installation-manifest",
            "1.0.0",
        ):
            raise ValueError(
                "Select the versioned repository native installation manifest"
            )
        files = tuple(
            FileEvidence(row["path"], row["size_bytes"], row["sha256"])
            for row in manifest["files"]
        )
        amber = select_gp_amber_engine(
            directory=request["amber_directory"], files=files
        )
        numeric = select_gp_construction_engine(
            site_packages=request["site_packages"], interpreter=request["interpreter"]
        )
        return dict(
            amber_engine_file=retain(destination / "amber-engine.json", amber, plane),
            numeric_engine_file=retain(
                destination / "numeric-engine.json", numeric, plane
            ),
            new_native_calls=0,
        )
    if operation == "prepare-parent":
        _, _, original_plane = application_storage(
            context_file(request["original_context_file"]), for_write=False
        )
        gp = decode_file(request["gp_source_file"], StructuralSourceMember)
        source = prepare_gp_repair_from_original(
            parent_file=request["parent_file"],
            assessment_file=request["assessment_file"],
            gp_source=gp,
            original_artifact_writer=original_plane,
            destination_relative_path=relative(
                destination / "original-operands", plane
            ),
            artifact_writer=plane,
            amber_engine=decode_file(request["amber_engine_file"], GpAmberEngine),
            numeric_engine=decode_file(
                request["numeric_engine_file"], GpRepairNumericEngine
            ),
            **{
                name: Decimal(request[name])
                if name == "maximum_refined_displacement_angstrom"
                else request[name]
                for name in PARENT_OPTIONAL
                if name in request
            },
        )
        source_file = retain(destination / "source.json", source, plane)
        authored = author_gp_geometry_repair(
            source=source,
            project_root=context.project_root,
            work_directory=request["native_work_directory"],
            artifact_writer=plane,
            output_dir=destination / "authoring",
        )
        return dict(source_file=source_file, authored=authored, new_native_calls=0)
    if operation in ("read-parent", "read-models"):
        parent = operation == "read-parent"
        report, config, result = original_wave(
            request["authoring_directory"],
            plane,
            REPAIR if parent else AMBER,
            GpGeometryRepairConfig if parent else GpAmberOperationConfig,
            GpGeometryRepairResult if parent else GpAmberPreparationResult,
        )
        selected = result if parent else result.units[0]
        with native_result_reader(plane, selected) as native:
            reader = read_gp_geometry_repair if parent else read_initial_gp_amber
            assessed = reader(
                source=config.source,
                original_result=result,
                native_subwork=native,
                result_id="read.local-construction." + config.source.fingerprint(),
            )
            path = retain(destination / "independent-result.json", assessed, plane)
        return dict(
            operational_report=report,
            independent_result_file=path,
            new_native_calls=0,
            material_denominator=list(MODEL_NAMES),
            independent_biological_replicates=0,
        )
    if operation == "prepare-scaffolds":
        _, config, result = original_wave(
            request["repair_authoring_directory"],
            plane,
            REPAIR,
            GpGeometryRepairConfig,
            GpGeometryRepairResult,
        )
        gp = decode_file(request["gp_source_file"], StructuralSourceMember)
        _, _, ligand_plane = application_storage(
            context_file(request["ligand_context_file"]), for_write=False
        )
        ligand_relative = relative(request["ligand_directory"], ligand_plane)
        ligand = read_rubp_template(
            directory_relative_path=ligand_relative,
            component_sha256=request["component_sha256"],
            artifact_writer=ligand_plane,
        )["preparation"]
        with native_result_reader(plane, result) as native:
            refined = prepare_refined_gp_parent(
                source=config.source,
                original_result=result,
                native_subwork=native,
                gp_source=gp,
                output_relative_path=relative(destination / "refined-parent", plane),
                artifact_writer=plane,
                include_records=True,
            )
            scaffolds = prepare_active_gp_scaffolds(
                cases=decode_file(request["case_set_file"], RubiscoCaseSet),
                original_supply=refined["supply"],
                parent_assessment=refined["assessment"],
                parent_heavy_path=refined["paths"]["complete-heavy.pdb"],
                parent_origin_path=refined["paths"]["atom-origin-provenance.json"],
                gp_source=gp,
                ligand=ligand,
                methionine=decode_file(
                    request["methionine_file"], StructuralSourceMember
                ),
                output_relative_path=relative(destination / "scaffolds", plane),
                artifact_writer=plane,
            )
        return dict(
            scaffold_paths=scaffolds["paths"],
            refined_parent_paths=refined["paths"],
            new_native_calls=0,
        )
    if operation == "prepare-models":
        _, _, ligand_plane = application_storage(
            context_file(request["ligand_context_file"]), for_write=False
        )
        ligand_relative = relative(request["ligand_directory"], ligand_plane)
        source = prepare_initial_gp_amber(
            scaffold_relative_path=relative(request["scaffold_directory"], plane),
            ligand_relative_path=ligand_relative,
            component_sha256=request["component_sha256"],
            parameter_sources=tuple(
                decode_file(path, SourceMember)
                for path in request["parameter_source_files"]
            ),
            engine=decode_file(request["amber_engine_file"], GpAmberEngine),
            numeric_engine=decode_file(
                request["numeric_engine_file"], GpRepairNumericEngine
            ),
            artifact_writer=plane,
            ligand_artifact_writer=ligand_plane,
            maximum_minimization_iterations=request.get("maximum_iterations", 2000),
            construction_seed=request.get("construction_seed", 20261114),
            construction_threads=request.get("construction_threads", 8),
        )
        source_file = retain(destination / "source.json", source, plane)
        authored = author_initial_gp_amber(
            source=source,
            project_root=context.project_root,
            work_directory=request["native_work_directory"],
            artifact_writer=plane,
            output_dir=destination / "authoring",
        )
        return dict(source_file=source_file, authored=authored, new_native_calls=0)
    raise ValueError("Unsupported construction operation")


def run_construction_operation(
    operation: str, *, context_path: Path, operator_profile: Path, request_path: Path
):
    """Prepare or read one original construction using the selected application context and storage."""
    context_raw = read_bounded_bytes(context_path, maximum_bytes=MAX_REQUEST_BYTES)
    context = ApplicationContext.from_document(load_application_json(context_raw))
    if (
        operator_profile != context.operator_profile
        or context.python_executable != Path(sys.executable).absolute()
    ):
        raise ValueError(
            "Use the context's explicit operator profile and selected interpreter"
        )
    request_raw = read_bounded_bytes(request_path, maximum_bytes=MAX_REQUEST_BYTES)
    request = load_application_json(request_raw)
    validate_request(operation, request)
    _, _, plane = application_storage(context, for_write=True)
    destination = Path(request["output_directory"])
    if destination.exists() or destination.is_symlink():
        raise ValueError("Select a fresh output directory for this operation")
    plane.root.resolve(relative(destination, plane), for_write=True)
    try:
        result = operate(operation, request, context, plane)
    except Exception as error:
        retain(
            destination / "operation-failure.json",
            dict(
                operation=operation,
                status="REFUSED",
                error_type=type(error).__name__,
                message=str(error),
                context_sha256=context.fingerprint(),
                new_native_calls=0,
            ),
            plane,
        )
        raise
    finally:
        retain(destination / "request.json", request_raw, plane)
        retain(destination / "context.json", context_raw, plane)
    path = retain(
        destination / "operation-return.json",
        dict(
            operation=operation,
            completed_at_utc=datetime.now(timezone.utc).isoformat(),
            context_sha256=context.fingerprint(),
            result=result,
        ),
        plane,
    )
    return {"operation": operation, "output": path}
