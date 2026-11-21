# SPDX-License-Identifier: MPL-2.0
"""Author and operate new R01--R22 studies through the public shared lifecycle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    new=commands.add_parser("new",help="write a researcher-editable scientific recipe")
    new.add_argument("--family",required=True,choices=tuple(f"R{i:02d}" for i in range(1,23)))
    new.add_argument("--recipe",type=Path,required=True)
    for name in ("prepare","author","run","read","recover"):
        command=commands.add_parser(name)
        command.add_argument("--project-root",type=Path,required=True)
        command.add_argument("--workspace",type=Path,required=True)
        if name=="prepare":
            command.add_argument("--recipe",type=Path,required=True)
            command.add_argument("--raw-cohort",type=Path)
            command.add_argument("--device",choices=("cpu","gpu"),default="cpu")
    args=parser.parse_args(argv)
    from empirical_lawhood.api.joint_description import create_inputs,new_recipe
    if args.command=="new":
        args.recipe.parent.mkdir(parents=True,exist_ok=True)
        with args.recipe.open("x",encoding="utf-8") as stream:
            json.dump(new_recipe(args.family),stream,indent=2,sort_keys=True);stream.write("\n")
        print(json.dumps({"recipe":str(args.recipe.absolute()),"scientific_execution_performed":False},indent=2))
        return 0
    from empirical_lawhood.api.investigations import create_local_workspace,create_investigation_service,prepare_investigation,experiment_preparation_report
    root=args.workspace.absolute();project=args.project_root.absolute()
    if args.command=="prepare":
        workspace=create_local_workspace(root,project_root=project,maximum_parallel_tasks=1)
        create_inputs(recipe_path=args.recipe,project_root=project,output_directory=workspace.scratch_root/"inputs",
            device=args.device,raw_cohort_path=args.raw_cohort)
    service=create_investigation_service(project_root=project,operator_profile=root/"operator-storage.json")
    inputs=root/"scratch"/"inputs";directory=root/"artifacts"/"investigation"
    if args.command in ("prepare","author"):
        selected=json.loads((inputs/"selected.json").read_text())["value"]
        preparation=prepare_investigation(service,specification_path=inputs/"specification.json",
            source_selection_path=inputs/"sources.json",environment_id="environment.joint-description."+selected["device"])
        report=experiment_preparation_report(preparation)
        if args.command=="author" and preparation.executable:
            report=service.author(preparation=preparation,output_dir=directory)
    elif args.command=="run":
        from empirical_lawhood.execution.operational_configuration import accelerated_compute_operation
        selected=json.loads((inputs/"selected.json").read_text())["value"]
        with accelerated_compute_operation(selected["device"]=="gpu"):
            report=service.run(directory=directory)
    elif args.command=="read":
        report=service.read(directory=directory)
    else:
        from empirical_lawhood.execution.operational_configuration import accelerated_compute_operation
        selected=json.loads((inputs/"selected.json").read_text())["value"]
        with accelerated_compute_operation(selected["device"]=="gpu"):
            report=service.recover(directory=directory)
    path=root/"scratch"/(args.command+"-report.json")
    path.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True,default=str))
    return 2 if args.command in ("prepare","author") and not preparation.executable else 0


if __name__=="__main__":
    raise SystemExit(main())
