# SPDX-License-Identifier: MPL-2.0
"""Run the authored model-free matrix programme through the public recursive lifecycle."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

from empirical_lawhood.api.investigations import (
    create_local_workspace, create_investigation_service, prepare_investigation, experiment_preparation_report,
)
from empirical_lawhood.api.model_free_matrix import create_inputs, create_reanalysis_inputs, create_successor_inputs, create_population_deployment_inputs, parent_readout_sha256
from empirical_lawhood.storage.progress import OperationalProgressReporter


def write_report(path, value):
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _resource_snapshot():
    """OS counters, never a fabricated simultaneous process-tree measurement."""
    output={}
    try:
        import resource
        multiplier=1 if sys.platform=='darwin' else 1024 if sys.platform.startswith('linux') else None
        for name,who in (('process',resource.RUSAGE_SELF),('reaped_children',resource.RUSAGE_CHILDREN)):
            value=resource.getrusage(who)
            output[name]={'user_cpu_seconds':value.ru_utime,'system_cpu_seconds':value.ru_stime,
                'peak_rss_raw':value.ru_maxrss,
                'peak_rss_bytes':None if multiplier is None else int(value.ru_maxrss*multiplier),
                'block_input_operations':value.ru_inblock,'block_output_operations':value.ru_oublock,
                'rss_scope':'THIS_PROCESS_LIFETIME_PEAK' if name=='process' else
                    'KERNEL_REAPED_CHILDREN_MAXIMUM_INDIVIDUAL_PEAK; NOT_SIMULTANEOUS_TREE_RSS'}
    except (ImportError,OSError,ValueError) as error:
        output['resource_unavailable']=type(error).__name__
    try:
        output['proc_self_io']={name.strip():int(value.strip()) for name,value in
            (line.split(':',1) for line in Path('/proc/self/io').read_text().splitlines())}
    except (OSError,ValueError):
        output['proc_self_io']=None
    return output


class InvocationMetrics:
    """One invocation's operational observations of an already returned result."""
    def __init__(self,path,operation,prepare_only):
        self.path=path
        self.operation=operation
        self.prepare_only=prepare_only
        self.started=perf_counter()
        self.before=_resource_snapshot()
        self.scientific_result=None
        self.exit_code=None
        self.error=None

    def observe_result(self,result):
        value=result.get('scientific_result')
        if value is None:
            return
        # Stream the exact defined canonical JSON representation from the
        # existing in-memory readout; do not revisit custody or replay science.
        encoder=json.JSONEncoder(sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
        digest=sha256(); count=0
        for fragment in encoder.iterencode(value):
            raw=fragment.encode('utf-8'); digest.update(raw); count+=len(raw)
        digest.update(b'\n'); count+=1
        self.scientific_result={'sha256':digest.hexdigest(),'canonical_json_bytes':count,
            'encoding':'UTF8_SORTED_COMPACT_JSON_ENSURE_ASCII_ALLOW_NAN_FALSE_WITH_FINAL_NEWLINE',
            'source':'EXACT_SCIENTIFIC_RESULT_RETURNED_BY_THIS_INVOCATION; NO_EXTRA_READ_OR_REPLAY'}

    def write(self):
        after=_resource_snapshot()
        deltas={}
        for name in ('process','reaped_children'):
            if name in self.before and name in after:
                deltas[name]={key:after[name][key]-self.before[name][key] for key in
                    ('user_cpu_seconds','system_cpu_seconds','block_input_operations','block_output_operations')}
        if self.before.get('proc_self_io') is not None and after.get('proc_self_io') is not None:
            deltas['proc_self_io']={key:after['proc_self_io'][key]-self.before['proc_self_io'][key]
                for key in after['proc_self_io'].keys() & self.before['proc_self_io'].keys()}
        value={'schema':'model-free-matrix-invocation-metrics.v1','operation':self.operation,
            'prepare_only':self.prepare_only,'exit_code':self.exit_code,'error':self.error,
            'operation_elapsed_seconds':perf_counter()-self.started,
            'timing_scope':'THIS_INVOCATION_AFTER_ARGUMENT_VALIDATION_THROUGH_RESULT_REPORTING; EXCLUDES_METRICS_FILE_WRITE',
            'resource_before':self.before,'resource_after':after,'counter_deltas':deltas,
            'scientific_result':self.scientific_result,
            'memory_scope':'SEPARATE_KERNEL_LIFETIME_MAXIMA; NOT_ADDITIVE; NO_SIMULTANEOUS_PROCESS_TREE_PEAK_MEASURED',
            'io_scope':'KERNEL_COUNTERS_WHERE_AVAILABLE; OS_SPECIFIC_ACCOUNTING; NO_GLOBAL_PROCESS_TOTAL',
            'scientific_scope':'OPERATIONAL_BENCHMARK_ONLY; TIMING_AND_RESOURCE_COUNTERS_DO_NOT_VERIFY_NATIVE_CALL_COUNTS'}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('x',encoding='utf-8') as stream:
            json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False)
            stream.write('\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("prepare", "run", "reanalyse", "read", "recover", "execute", "confirm", "deploy-population"), default="run")
    parser.add_argument("--prepare-only", action="store_true", help="Authenticate and author development, reanalysis, confirmation or sparse population deployment without executing it.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True,
        help="Explicit fresh root for prepare/run/reanalyse/confirm/deploy-population; original root for read/recover/execute.")
    parser.add_argument("--definition", type=Path,
        help="Editable scientific JSON; required for prepare/run/reanalyse/confirm/deploy-population.")
    parser.add_argument("--parent-workspace", type=Path, help="Authenticated parent for reanalysis, fresh confirmation or reveal-all-to-sparse deployment.")
    parser.add_argument("--maximum-parallel-tasks", type=int,
        help="Optional operational cap; otherwise use automatic usable host capacity.")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--partial", action="store_true", help="Read available operational custody without a new scientific assessment.")
    parser.add_argument("--metrics-json", type=Path, help="Fresh absolute output for scoped invocation time, RSS, IO and canonical result hash; no extra read or replay.")
    args = parser.parse_args(argv)
    if args.prepare_only:
        if args.operation not in ("run", "prepare", "reanalyse", "confirm", "deploy-population"):
            parser.error("--prepare-only requires a development, reanalysis, confirmation or population-deployment authoring operation")
        if args.operation == "run":
            args.operation = "prepare"
    args.prepare_only = args.prepare_only or args.operation == "prepare"
    if args.metrics_json is not None and (not args.metrics_json.is_absolute() or args.metrics_json.exists()):
        parser.error("--metrics-json requires a fresh absolute file path")
    project, root = args.project_root.absolute(), args.workspace.absolute()
    new = args.operation in ("prepare", "run", "reanalyse", "confirm", "deploy-population")
    if new and args.definition is None:
        parser.error("select --definition for a new authored study")
    if (args.operation in ("reanalyse", "confirm", "deploy-population")) != (args.parent_workspace is not None):
        parser.error("--parent-workspace is required for reanalyse, confirm or deploy-population only")
    if args.partial and args.operation != "read":
        parser.error("--partial is an operational read selection only")
    metrics=None if args.metrics_json is None else InvocationMetrics(args.metrics_json,args.operation,args.prepare_only)
    try:
        result=_invoke(args,project,root,new,metrics)
        if metrics is not None:
            metrics.exit_code=result
        return result
    except BaseException as error:
        if metrics is not None:
            metrics.error={'type':type(error).__name__,'message':str(error)}
        raise
    finally:
        if metrics is not None:
            try:
                metrics.write()
            except Exception as error:
                if metrics.error is None:
                    raise
                print('Could not write invocation metrics: '+str(error),file=sys.stderr)


def _invoke(args,project,root,new,metrics):
    if new:
        workspace = create_local_workspace(root, project_root=project,
            maximum_parallel_tasks=args.maximum_parallel_tasks)
        profile, artifact_root, scratch = workspace.profile_path, workspace.artifact_root, workspace.scratch_root
    else:
        profile, artifact_root, scratch = root / "operator-storage.json", root / "artifacts", root / "scratch"
    service = create_investigation_service(project_root=project, operator_profile=profile)
    directory = artifact_root / "model-free-matrix"
    # Each invocation owns its progress file; later reads/recovery must not
    # overwrite a previous or still-running invocation's snapshot.
    progress_path = scratch / ("progress.json" if new else "progress." + args.operation + "." + uuid4().hex + ".json")
    with OperationalProgressReporter(progress_path, "model-free matrix programme",
            stream=None if args.no_progress else sys.stderr):
        if new:
            if args.operation in ("reanalyse", "confirm", "deploy-population"):
                parent = args.parent_workspace.absolute()
                parent_service = create_investigation_service(project_root=project, operator_profile=parent / "operator-storage.json")
                creator = {'reanalyse': create_reanalysis_inputs, 'confirm': create_successor_inputs,
                    'deploy-population': create_population_deployment_inputs}[args.operation]
                inputs = creator(definition_path=args.definition, project_root=project,
                    output_directory=scratch / "inputs", parent_directory=parent / "artifacts" / "model-free-matrix",
                    parent_service=parent_service)
            else:
                inputs = create_inputs(definition_path=args.definition, project_root=project, output_directory=scratch / "inputs")
            write_report(scratch / "inputs.json", inputs)
            prepared = prepare_investigation(service, specification_path=Path(inputs["specification"]),
                source_selection_path=Path(inputs["sources"]), environment_id="environment.matrix-model-free.base")
            report = experiment_preparation_report(prepared)
            write_report(scratch / "preparation.json", report)
            if not prepared.executable:
                print(json.dumps({"status":"BLOCKED","preparation_report":str(scratch / "preparation.json"),
                    "dependencies":report.get("dependencies")}, indent=2))
                return 2
            authored = service.author(preparation=prepared, output_dir=directory)
            write_report(scratch / "authoring.json", authored)
            # Execution owns a fresh authenticated read of the authored inputs.
            # Retained reanalysis preparation can contain the full native roster.
            del prepared
        if not args.prepare_only and args.operation in ("run", "reanalyse", "execute", "confirm", "deploy-population"):
            result = service.run(directory=directory, maximum_parallel_tasks=args.maximum_parallel_tasks)
            write_report(scratch / "execution.json", result)
        elif args.operation == "recover":
            result = service.recover(directory=directory, maximum_parallel_tasks=args.maximum_parallel_tasks)
            write_report(scratch / "recovery.json", result)
        elif args.operation == "read":
            result = service.read(directory=directory, allow_partial=args.partial)
        if not args.prepare_only:
            # Run/recover already return the complete authenticated readout.
            # A separate cold read is an explicit --operation read invocation.
            write_report(scratch / "result.json", result)
            if metrics is not None:
                metrics.observe_result(result)
            science = result.get("scientific_result") or {}
            print(json.dumps({"status":result.get("status"),"scientific_completion":science.get("scientific_completion"),
                "qualification":science.get("qualification"),"assigned_roots":science.get("assigned_roots"),
                "selected_modules":science.get("selected_modules"),
                "completed_operations":science.get("completed_operations"),"assigned_operations":science.get("assigned_operations"),
                "confirmation_parent_readout_sha256":parent_readout_sha256(science),
                "mode":science.get("mode"),"result_report":str(scratch / "result.json"),
                "operator_profile":str(profile),"authoring_directory":str(directory),
                "progress_report":str(progress_path)}, indent=2))
            return 0 if args.partial or science.get("scientific_completion") == "COMPLETED" else 3
        print(json.dumps({"status":"PREPARED_NOT_EXECUTED","operator_profile":str(profile),
            "authoring_directory":str(directory),"preparation_report":str(scratch / "preparation.json"),
            "progress_report":str(progress_path)}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
