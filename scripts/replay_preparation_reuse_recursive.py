# SPDX-License-Identifier: MPL-2.0
"""Run the released R25 or R26 selection through EL's original recursive investigation service."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.api import investigations
from empirical_lawhood.storage.numerical_provenance import observe_implementation_source


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("study", choices=("r25", "r26"))
    parser.add_argument("operation", choices=("prepare", "run", "recover", "read"))
    parser.add_argument("--producer-checkout", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True, help="Explicit external replica workspace")
    parser.add_argument("--inputs", type=Path, help="Directory produced by --export-recursive-inputs")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    checkout = args.producer_checkout.resolve(strict=True)
    if not Path(investigations.__file__).resolve().is_relative_to(checkout / "src"):
        raise ValueError("Use the selected producer checkout's Python imports and locked environment")
    if args.workers < 1:
        parser.error("Select a positive worker count")
    programme = (
        Path(__file__).resolve().parents[1]
        / "programmes/foundations/emergent-structure/workflows/preparation-and-reuse"
    )
    members = json.loads((programme / "operands" / (args.study + ".json")).read_bytes())["members"]
    root = args.workspace.absolute()
    profile = root / "operator-storage.json"
    directory = root / "artifacts" / args.study
    if args.operation == "prepare":
        if args.inputs is None:
            parser.error("Select the complete exported input directory")
        for name, member in members.items():
            if name.startswith("recursive/"):
                raw = (args.inputs / name.removeprefix("recursive/")).read_bytes()
                if len(raw) != member["size"] or sha256(raw).hexdigest() != member["sha256"]:
                    raise ValueError("Released native selection differs for " + name)
        declared = json.loads((args.inputs / "source-snapshot.json").read_bytes())["value"]
        _, code, lock, head, clean = observe_implementation_source(checkout)
        if (code, lock, head, clean) != (
            declared["code_sources_sha256"],
            declared["dependency_lock_sha256"],
            declared["observed_git_head"],
            True,
        ):
            raise ValueError("Select the clean original producer revision and dependency lock")
        investigations.create_local_workspace(
            root, project_root=checkout, maximum_parallel_tasks=args.workers
        )
    service = investigations.create_investigation_service(project_root=checkout, operator_profile=profile)
    if args.operation == "prepare":
        environment = {
            "r25": "environment.matrix-waveform-preparation.base",
            "r26": "environment.matrix-model-free.base",
        }[args.study]
        prepared = investigations.prepare_investigation(
            service,
            specification_path=args.inputs / "specification.json",
            source_selection_path=args.inputs / "sources.json",
            environment_id=environment,
        )
        service.author(preparation=prepared, output_dir=directory)
        print("Authored exposed native replication", directory)
    else:
        result = (
            service.read(directory=directory)
            if args.operation == "read"
            else getattr(service, args.operation)(directory=directory, maximum_parallel_tasks=args.workers)
        )
        print(
            json.dumps(
                {
                    "scope": "EXPOSED_NATIVE_REPRODUCTION",
                    "status": result["status"],
                    "run_id": result["run_id"],
                    "directory": str(directory),
                },
                sort_keys=True,
            )
        )
        if result["status"] != "SUCCEEDED":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
