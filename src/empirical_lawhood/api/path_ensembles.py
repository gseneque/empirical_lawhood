# SPDX-License-Identifier: MPL-2.0
"""Author, acquire, recover and read the physical path experiments through EL."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.api.investigations import (
    create_investigation_service,
    create_local_workspace,
    prepare_investigation,
)
from empirical_lawhood.api.recursive_authoring import implementation_binding
from empirical_lawhood.design.experiment_inputs import ExperimentInputSelection
from empirical_lawhood.methods.path_likelihood.records import (
    PathDesign,
    PathSpecification,
    PathProduct,
    numerical_json,
    operations,
    required_parents,
)
from empirical_lawhood.science.records.status import OperationalStatus


def unique_fields(pairs):
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("duplicate scientific definition field")
    return fields


def create_inputs(*, definition_path, project_root, output_directory):
    from empirical_lawhood.api.generated_experiment_protocols import (
        EXPERIMENT_PROTOCOL_DECLARATIONS,
    )

    raw = Path(definition_path).read_bytes()
    original = json.loads(raw, object_pairs_hook=unique_fields)
    if set(original) != {
        "schema",
        "first_root",
        "development_roots",
        "evaluation_roots",
        "batch_size",
        "parameters",
    }:
        raise ValueError("path recipe requires the complete frozen selection")
    types = (p.specification_type for p in EXPERIMENT_PROTOCOL_DECLARATIONS)
    cls = {
        t.definition_schema_id(): t
        for t in types
        if issubclass(t, PathSpecification)
    }[original["schema"]]
    spec = cls(
        PathDesign(
            cls.FAMILY,
            original["first_root"],
            original["development_roots"],
            original["evaluation_roots"],
            original["batch_size"],
            numerical_json(original["parameters"]),
        )
    )
    selection = ExperimentInputSelection(
        "inputs." + spec.specification_id, cls.FAMILY + ".numerical", ()
    )
    output = Path(output_directory)
    output.mkdir(exist_ok=True, parents=True)
    for name, data in (
        ("definition.json", raw),
        ("specification.json", spec.canonical_bytes()),
        ("sources.json", selection.canonical_bytes()),
        (
            "source-snapshot.json",
            implementation_binding(project_root).canonical_bytes(),
        ),
    ):
        path = output / name
        if path.exists():
            if path.read_bytes() != data:
                raise FileExistsError(
                    "Different original selection already exists at " + str(path)
                )
        else:
            with path.open("xb") as f:
                f.write(data)
    return spec


def read_result(
    *,
    directory,
    artifact_writer,
    specification,
    instance,
    payloads,
    report,
    products,
    draft,
    plan,
    allow_partial=False,
):
    configs = operations(specification)
    if (
        report.get("run_id") != plan.source_plan.object_id
        or instance.specification != specification.identity
        or set(t.task_id for t in plan.tasks) != {c.node_id for c in configs}
    ):
        raise PermissionError("path reader requires the complete original selection")
    found, census = {}, []
    for c in configs:
        receipt = products["receipts"].get(c.node_id)
        value = products["records"].get(c.node_id, {}).get(c.node_id + ".product")
        success = (
            receipt is not None
            and receipt.operational_status is OperationalStatus.SUCCEEDED
        )
        if success and (type(value) is not PathProduct or value.config != c):
            if not allow_partial:
                raise PermissionError(
                    "successful path stage lacks its original typed result"
                )
            value = None
        elif success:
            found[c.node_id] = value
            if c.acquires:
                original = value.arrays
                material = products["outputs"].get(original.artifact_id)
                if (
                    material is None
                    or original.role != "path-array-container"
                    or (
                        material.logical.payload_schema,
                        material.logical.media_type,
                        material.logical.content_sha256,
                        material.materialization.size_bytes,
                    )
                    != (
                        original.payload_schema,
                        original.media_type,
                        original.sha256,
                        original.size_bytes,
                    )
                ):
                    raise PermissionError(
                        "path measurement lost its original binary companion"
                    )
        if c.acquires:
            measured = value.measurement if success and value else {}
            census.append(
                {
                    "first_root": c.first,
                    "count": c.count,
                    "phase": c.phase,
                    "operation": c.node_id,
                    "status": str(receipt.operational_status)
                    if receipt
                    else "UNSTARTED",
                    "array": value.arrays.to_document() if success and value else None,
                    "native_intervals": measured.get("native_intervals"),
                    "execution_seconds": measured.get("execution_seconds"),
                    "root_failures": measured.get("root_failures"),
                    **(
                        {
                            "component_cpu_seconds": measured.get(
                                "component_cpu_seconds"
                            ),
                            "process_peak_rss_kib": measured.get(
                                "process_peak_rss_kib"
                            ),
                        }
                        if specification.ISSUED_FORECAST
                        else {}
                    ),
                }
            )
    for value in found.values():
        required = required_parents(value.config, configs)
        if any(p.node_id not in found for p in required) or value.parents != tuple(
            found[p.node_id].identity for p in required
        ):
            raise PermissionError("path outcome changes its original parent evidence")

    def stage(phase):
        value = next((v for v in found.values() if v.config.phase == phase), None)
        return (
            {"identity": value.identity.to_document(), "measurement": value.measurement}
            if value
            else None
        )

    return {
        "study": specification.FAMILY,
        "specification": specification.identity.to_document(),
        "run_id": report.get("run_id"),
        "scientific_completion": "COMPLETED"
        if len(found) == len(configs)
        else "INCOMPLETE",
        "evidence_scope": "PREDECLARED_NUMERICAL_DEVELOPMENT_WITH_DISJOINT_EVALUATION",
        "development": stage("freeze"),
        "evaluation": stage("assess"),
        "batches": census,
    }


def portable_readout(report):
    """Project the original held-out decisions and receipt joins for publication."""
    science = report["scientific_result"]
    if science["scientific_completion"] != "COMPLETED":
        raise ValueError(
            "a portable result requires every original scientific operation"
        )
    products = {
        (row["task_id"], row["output_id"]): row
        for row in report["retained_product_index"]
    }
    receipts = {
        row["task_id"]: row
        for row in report["operational_census"]
        if row["operational_status"] == "SUCCEEDED"
    }
    if len(receipts) != report["task_count"]:
        raise PermissionError(
            "portable path record lacks a successful original for every operation"
        )
    for (task, _), product in products.items():
        receipt = product["producing_receipt"]["value"]
        if (receipt["object_id"], receipt["object_fingerprint"]) != (
            receipts[task]["receipt_id"],
            receipts[task]["receipt_sha256"],
        ):
            raise PermissionError("portable path record changes a producing receipt")
    for phase in ("development", "evaluation"):
        original = science[phase]["identity"]["value"]
        output = original["object_id"]
        physical = products[(output.removesuffix(".product"), output)]
        if (original["object_schema"], original["object_fingerprint"]) != (
            physical["schema"],
            physical["sha256"],
        ):
            raise PermissionError("portable path record changes an assessed original")
    for batch in science["batches"]:
        task = batch["operation"]
        actual = products[(task, task + ".arrays")]
        pin = batch["array"]["value"]
        if (
            actual["logical_artifact_id"],
            actual["schema"],
            actual["sha256"],
            actual["size_bytes"],
        ) != (
            pin["artifact_id"],
            pin["payload_schema"],
            pin["sha256"],
            pin["size_bytes"],
        ):
            raise PermissionError(
                "portable path record changes the binary or its producing receipt"
            )
    return {
        **science,
        "producer": {
            k: report[k]
            for k in (
                "observed_producing_git_head",
                "observed_producing_checkout_clean",
                "producing_code_sha256",
                "dependency_lock_sha256",
                "packet_sha256",
                "execution_plan_sha256",
                "task_count",
                "qualification",
                "scientific_authority",
                "new_native_contact_count",
            )
        },
        "receipt_sha256": {k: v["receipt_sha256"] for k, v in sorted(receipts.items())},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("prepare", "run", "read", "recover", "diagnose")
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--definition", type=Path)
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument(
        "--portable",
        action="store_true",
        help="publish the complete scientific result and original receipt identities",
    )
    args = parser.parse_args()
    if args.portable and (args.operation != "read" or args.partial):
        parser.error("--portable requires a complete read")
    workspace = args.workspace.absolute()
    profile = workspace / "operator-storage.json"
    if args.operation == "prepare" and not profile.exists():
        create_local_workspace(
            workspace,
            project_root=args.project_root,
            maximum_parallel_tasks=args.workers,
        )
    service = create_investigation_service(
        project_root=args.project_root, operator_profile=profile
    )
    inputs, authored = (
        workspace / "artifacts" / "inputs",
        workspace / "artifacts" / "investigation",
    )
    if args.operation == "prepare":
        if args.definition is None:
            parser.error("prepare requires --definition")
        spec = create_inputs(
            definition_path=args.definition,
            project_root=args.project_root,
            output_directory=inputs,
        )
        prep = prepare_investigation(
            service,
            specification_path=inputs / "specification.json",
            source_selection_path=inputs / "sources.json",
            environment_id=spec.FAMILY,
        )
        if not prep.executable:
            raise ValueError(str(prep.dependencies))
        service.author(preparation=prep, output_dir=authored)
        print(spec.specification_id, authored, flush=True)
    elif args.operation == "diagnose":
        from .path_ensemble_diagnostics import read_diagnostics

        print(numerical_json(read_diagnostics(service, authored)))
    elif args.operation == "read":
        result = service.read(directory=authored, allow_partial=args.partial)
        if args.portable:
            print(numerical_json(portable_readout(result)))
        else:
            print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        operation = service.run if args.operation == "run" else service.recover
        report = operation(directory=authored, maximum_parallel_tasks=args.workers)
        science = report.get("scientific_result") or {}
        print(
            json.dumps(
                {
                    "run_id": report.get("run_id"),
                    "status": report.get("status"),
                    "scientific_completion": science.get("scientific_completion"),
                    "diagnostics": [
                        (v.get("task_id"), v.get("actual"))
                        for v in report.get("failure_diagnostics", ())
                        if v.get("attempt_id")
                    ],
                },
                sort_keys=True,
            )
        )
        if science.get("scientific_completion") != "COMPLETED":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
