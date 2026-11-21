# SPDX-License-Identifier: MPL-2.0
"""Prepare a selected observed-core Gp material and read its standard Amber outputs."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_core import (
    CASES,
    build_case,
)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    ops = cli.add_subparsers(dest="operation", required=True)
    build = ops.add_parser("build")
    build.add_argument("--selection", type=Path, required=True)
    build.add_argument("--case", choices=CASES, required=True)
    build.add_argument("--output", type=Path, required=True)
    condition = ops.add_parser("condition")
    condition.add_argument("--build", type=Path, required=True)
    condition.add_argument("--protocol", type=Path, required=True)
    condition.add_argument("--output", type=Path, required=True)
    validation = ops.add_parser("validate")
    for flag in ("build", "condition", "output", "runtime-prefix"):
        validation.add_argument("--" + flag, type=Path, required=True)
    validation.add_argument("--runtime-receipt-sha256", required=True)
    force = ops.add_parser("force")
    force.add_argument("--build", type=Path, required=True)
    force.add_argument("--condition", type=Path, required=True)
    force.add_argument("--threads", type=int, required=True)
    read = ops.add_parser("read")
    read.add_argument("--build", type=Path, required=True)
    read.add_argument("--condition", type=Path)
    archive = argparse.ArgumentParser(add_help=False)
    for name in ("ledger", "native-root", "reference-root", "installation", "installation-manifest"):
        archive.add_argument("--" + name, type=Path, required=True)
    archive.add_argument("--ledger-sha256", required=True)
    archive.add_argument("--installation-manifest-sha256", required=True)
    archive_read = ops.add_parser("read-sander", parents=[archive], help="Read the complete selected native return ledger")
    archive_read.add_argument("--precursor-panel", type=Path, action="append", default=[],
                              help="Compare a selected JSON roster of coupled and outer releases for one material")
    successor = argparse.ArgumentParser(add_help=False, parents=[archive])
    successor.add_argument("--parent-directory", required=True)
    successor.add_argument("--parent-receipt-sha256", required=True)
    successor.add_argument("--parent-restart-sha256", required=True)
    successor.add_argument("--steps", type=int, required=True)
    ops.add_parser("prepare-sander-continuation", parents=[successor], help="Verify a selected gas-free continuation")
    run = ops.add_parser("run-sander-continuation", parents=[successor], help="Run one verified gas-free continuation")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--timeout-seconds", type=float, required=True)
    core = ops.add_parser("inspect-periodic-core", help="Read a selected hydrated Val1 return in its original atom order")
    core.add_argument("--native-root", type=Path, required=True)
    core.add_argument("--manifest-sha256", required=True)
    core.add_argument("--material", choices=("V1-WT", "V1-I95M"), required=True)
    core.add_argument("--site-packages", type=Path, required=True)
    core.add_argument("--interpreter", type=Path, required=True)
    oxygen = ops.add_parser("read-oxygen-products", help="Read bound-product geometry from the original oxygen supplement")
    oxygen.add_argument("--original-pdf", type=Path, required=True)
    oxygen.add_argument("--extracted-text", type=Path, required=True)
    crossing = ops.add_parser("read-crossing-orbitals", help="Reconstruct every occupied-space comparison in the selected Val1 return")
    crossing.add_argument("--native-root", type=Path, required=True)
    crossing.add_argument("--manifest-sha256", required=True)
    fields = ops.add_parser("read-crossed-fields", help="Reconstruct the signed field bounds and their recorded recovery")
    fields.add_argument("--native-root", type=Path, required=True)
    fields.add_argument("--manifest-sha256", required=True)
    args = cli.parse_args()
    if args.operation == "read-crossed-fields":
        from empirical_lawhood.api.domain_composition.rubisco_response.crossed_fields import read_crossed_fields
        print(json.dumps(read_crossed_fields(args.native_root, manifest_sha256=args.manifest_sha256),
                         indent=2, allow_nan=False))
        return
    if args.operation == "read-crossing-orbitals":
        from empirical_lawhood.api.domain_composition.rubisco_response.crossing_orbitals import CrossingOrbitalSources, read_crossing_orbitals
        print(json.dumps(read_crossing_orbitals(CrossingOrbitalSources(args.native_root,args.manifest_sha256)),
                         indent=2,allow_nan=False))
        return
    if args.operation == "read-oxygen-products":
        from empirical_lawhood.api.domain_composition.rubisco_response.tagged_products import read_oxygen_bound_products
        from empirical_lawhood.storage.bounded_io import read_bounded_bytes
        result = read_oxygen_bound_products(
            original_pdf=read_bounded_bytes(args.original_pdf, maximum_bytes=32 * 1024**2),
            extracted_text=read_bounded_bytes(args.extracted_text, maximum_bytes=32 * 1024**2),
        )
        print(json.dumps(result, indent=2, allow_nan=False))
        return
    if args.operation == "inspect-periodic-core":
        from empirical_lawhood.api.domain_composition.rubisco_response.construction_preparation import select_gp_construction_engine
        from empirical_lawhood.api.domain_composition.rubisco_response.observed_core import ObservedCoreSources, inspect_observed_core
        selection = ObservedCoreSources(args.native_root, args.manifest_sha256, args.material)
        engine = select_gp_construction_engine(site_packages=args.site_packages, interpreter=args.interpreter)
        print(json.dumps(inspect_observed_core(selection, engine=engine), indent=2, allow_nan=False))
        return
    if args.operation in ("read-sander", "prepare-sander-continuation", "run-sander-continuation"):
        from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import (
            SanderArchiveSelection, SanderContinuation, prepare_sander_continuation, read_sander_release_archive,
            run_sander_continuation,
        )
        selection = SanderArchiveSelection(args.ledger, args.ledger_sha256, args.native_root, args.reference_root,
                                          args.installation, args.installation_manifest, args.installation_manifest_sha256)
        if args.operation == "read-sander":
            from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import SanderPrecursorPanel

            panels = tuple(SanderPrecursorPanel.from_file(path) for path in args.precursor_panel)
            result = read_sander_release_archive(selection, precursor_panels=panels)
        else:
            request = SanderContinuation(args.parent_directory, args.parent_receipt_sha256, args.parent_restart_sha256, args.steps)
            if args.operation == "prepare-sander-continuation":
                result = prepare_sander_continuation(selection, request)
            else:
                result = run_sander_continuation(selection, request, output=args.output, timeout_seconds=args.timeout_seconds)
        print(json.dumps(result, indent=2, allow_nan=False))
        if args.operation == "run-sander-continuation" and result["status"] != "complete":
            raise SystemExit(1)
        return
    if args.operation == "build":
        selection = json.loads(args.selection.read_text())
        for spec in selection.values():
            path = Path(spec["path"])
            if not path.is_absolute():
                spec["path"] = str((args.selection.parent / path).resolve())
        build_case(selection, args.case, args.output)
    elif args.operation == "condition":
        from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_conditioning import (
            condition_case,
        )

        condition_case(args.build, json.loads(args.protocol.read_text()), args.output)
    elif args.operation == "force":
        from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_conditioning import (
            independent_force,
        )

        print(
            json.dumps(
                independent_force(args.build, args.condition, args.threads),
                indent=2,
                allow_nan=False,
            )
        )
    elif args.operation == "validate":
        from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_validation import (
            validate,
        )

        validate(
            args.build,
            args.condition,
            args.output,
            args.runtime_prefix,
            args.runtime_receipt_sha256,
        )
    else:
        from empirical_lawhood.adapters.rubisco.rubisco_response.forecast_conditioning import (
            read_case,
        )

        print(
            json.dumps(read_case(args.build, args.condition), indent=2, allow_nan=False)
        )


if __name__ == "__main__":
    main()
