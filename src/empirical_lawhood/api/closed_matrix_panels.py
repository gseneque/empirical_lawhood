# SPDX-License-Identifier: MPL-2.0
"""Calculate the frozen numerical assessments from a settled, complete acquisition roster.

This evaluator never dispatches a worker or writes a receipt to the original study.
An original blocked task retains its original terminal status in the exported census.
"""

from argparse import ArgumentParser
from hashlib import sha256
from contextlib import ExitStack
from io import BytesIO
import json
from pathlib import Path

from empirical_lawhood.api.investigations import create_investigation_service
from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
from empirical_lawhood.storage.recovery import ExternalRunRecoveryStore
from empirical_lawhood.execution.prepared_native_invocation import WorkerPreflightResult
from empirical_lawhood.execution.experiment_preparation import ExperimentInstanceBinding
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.storage.recursive_custody import iter_exact_custody_file_chunks


def find_record(payloads, name, cls):
    raw = payloads[name]
    result = decode_canonical_bytes(raw, cls, maximum_bytes=len(raw))
    if result.canonical_bytes() != raw:
        raise ValueError("Noncanonical authored operand " + name)
    return result


def refusal_checks(writer, terminal, operational, missing, allowed, plan, *, control):
    if not terminal or terminal.run_id != plan.source_plan.object_id:
        raise ValueError("An authenticated settled original terminal is required")
    if set(missing) - set(allowed):
        raise ValueError("Original acquisition, forecast or seal is missing")
    if not missing and (not control or terminal.operational_status != "SUCCEEDED"):
        raise ValueError("Complete terminal requires an explicitly selected exposed control")
    if missing and (control or terminal.operational_status not in ("BLOCKED", "FAILED", "PARTIAL")):
        raise ValueError("The originally interrupted terminal has not settled")
    rows = {k: [] for k in missing}
    for row in operational:
        if row["task_id"] in rows:
            rows[row["task_id"]].append(row)
    refusals = {}
    for task in missing:
        attempt = rows[task]
        if len(attempt) != 1:
            raise ValueError("Missing or ambiguous retained reduction attempt " + task)
        (a,) = attempt
        if a["receipt_sha256"] is not None or a["operational_status"] not in ("BLOCKED", "NOT_ATTEMPTED"):
            raise ValueError("Reduction is not an original receipt-free block " + task)
        event = a["recovery_event"]
        ev = event["value"] if event else None
        if a["reason_code"] == "dependency-blocked":
            if not any(parent in missing for parent in plan.task(task).dependency_task_ids):
                raise ValueError("No missing permitted parent explains " + task)
            if ev and ev["disposition"] != "NOT_ATTEMPTED":
                raise ValueError("Dependent reduction was already entered")
            refusals[task] = {"reason": "original dependency blocked", "event": event}
            continue
        if (
            not ev
            or ev["disposition"] != "BLOCKED"
            or a["reason_code"] != "resource-computability-unavailable"
            or ev["failure"]["value"]["sanitized_exception_type"] != "WorkerPreflightError"
            or ev["failure"]["value"]["failure_class"] != "RESOURCE_REFUSAL"
        ):
            raise ValueError("This refusal requires a separate scientific review " + task)
        attempt_id = a["attempt_id"]
        digest = sha256(attempt_id.encode()).hexdigest()
        path = f"runs/{terminal.run_id}/recovery/wave.development/preflight/{digest}.json"
        raw = ExternalRunRecoveryStore(writer)._read_payload(
            path,
            expected_schema=WorkerPreflightResult.SCHEMA,
            maximum_bytes=writer.custody_limits.recovery_index_bytes,
        )
        rec = (
            None
            if raw is None
            else decode_canonical_bytes(raw, WorkerPreflightResult, maximum_bytes=len(raw))
        )
        if (
            rec is None
            or rec.canonical_bytes() != raw
            or rec.ready
            or rec.invocation.object_id != "prepared." + attempt_id
            or rec.producing_provenance is not None
            or rec.native_work is not None
            or [(m.operand_id, m.reason) for m in rec.mismatches]
            != [("worker.implementation", "bounded local command timed out")]
        ):
            raise ValueError("Original preflight has a different identity, cause or entry scope")
        refusals[task] = {
            "reason": "source check timed out before calculation",
            "event": event,
            "preflight": rec.fingerprint(),
        }
    return refusals


def read_array(product, outputs, writer):
    ref = product.array_artifact
    manifest = outputs[ref.artifact_id]
    logical, material = manifest.logical, manifest.materialization
    if (logical.logical_artifact_id, logical.payload_schema, logical.media_type, logical.content_sha256) != (
        ref.artifact_id,
        ref.payload_schema,
        ref.media_type,
        ref.sha256,
    ) or (material.size_bytes, material.physical_sha256) != (ref.size_bytes, ref.sha256):
        raise ValueError("Array companion is not the original receipted operand")
    path = writer.root.resolve(material.relative_path, for_write=False)
    body = BytesIO()
    for part in iter_exact_custody_file_chunks(
        path,
        size_bytes=ref.size_bytes,
        expected_sha256=ref.sha256,
        read_guard=writer.require_verification_snapshot,
    ):
        body.write(part)
    body.seek(0)
    return body


def gather(configs, kind, products, plan):
    found = {}
    if set(c.node_id for c in configs) != {t.task_id for t in plan.tasks}:
        raise ValueError("The original complete operation roster changed")
    for c in configs:
        r = products["receipts"].get(c.node_id)
        if r is None:
            continue
        if (r.operational_status.value, r.run_id, r.task_id) != (
            "SUCCEEDED",
            plan.source_plan.object_id,
            c.node_id,
        ):
            raise ValueError("Foreign or unsuccessful receipt in authenticated products")
        v = products["records"][c.node_id][c.node_id + ".product"]
        if type(v) is not kind or v.config != c:
            raise ValueError("Authenticated product differs from the assigned scientific configuration")
        found[c.node_id] = v
    return found


def _reduce_waveforms(configs, spec, found, products, writer, payloads):
    from empirical_lawhood.domains.matrix.waveform_preparation.bindings import calculate, read_operand
    from empirical_lawhood.domains.matrix.finite_response_law.original_f import OriginalFiniteResponseLaw
    from empirical_lawhood.domains.matrix.preparation_applicability.waveform_evaluation import WaveformCohort

    def root_readout(row):
        return dict(
            root=row.draw.unit_id,
            observation=row.fingerprint(),
            complete=row.complete,
            covered_pairs=list(row.measured.covered_counts),
            false_admissions=list(row.measured.false_admissions),
            conjuncts=list(row.measured.conjuncts),
            native_intervals=row.native_intervals,
            primary_margin=None if row.primary.margin is None else str(row.primary.margin),
            signed_port_two=[None if v is None else str(v) for v in row.signed_port_two],
            failures=list(row.failures),
        )

    def source(ref, kind):
        value = find_record(
            payloads, "experiment-source-" + sha256(ref.object_id.encode()).hexdigest() + ".json", kind
        )
        if value.identity != ref:
            raise ValueError("Original authored scientific operand differs")
        return value

    lower = source(spec.lower, OriginalFiniteResponseLaw)
    parent = source(spec.development, WaveformCohort) if spec.development else None
    reduced = {}
    parity = {}
    stages = sorted(
        (c for c in configs if c.phase in ("measure", "cohort")),
        key=lambda c: (c.phase == "cohort", c.index or 0),
    )
    for c in stages:
        parents = [found[p.node_id] for p in c.suppliers()]
        with ExitStack() as streams:
            handles = {
                p.array_artifact.artifact_id: streams.enter_context(
                    read_array(p, products["outputs"], writer)
                )
                for p in parents
                if p.array_artifact
            }
            sources = {"lower": lower} if c.phase == "measure" else {"development": parent} if parent else {}
            new, companion = calculate(c, sources, parents, handles)
            if companion is not None or any(stream.read(1) for stream in handles.values()):
                raise ValueError("Pure reduction emitted an array or left trailing input")
        if c.node_id in found:
            if new.canonical_bytes() != found[c.node_id].canonical_bytes():
                raise ValueError("Independent replay changed a published waveform measurement")
            parity[c.node_id] = new.fingerprint()
        else:
            reduced[c.node_id] = new
            found[c.node_id] = new
    cohort = read_operand(found[stages[-1].node_id])
    if cohort.role != spec.role or len(cohort.rows) != spec.count:
        raise ValueError("Reconstructed cohort lost assigned waveforms")
    science = dict(
        role=cohort.role,
        assigned_waveforms=spec.count,
        disposition=cohort.disposition,
        statistics=json.loads(cohort.statistics_json),
        cohort=cohort.identity.to_document(),
        roots=[root_readout(r) for r in cohort.rows],
        full_census_evaluated=True,
        framework_evidence_ceiling="NON_PROMOTABLE",
        new_native_acquisitions=0,
    )
    return science, {"cohort.canonical.json": cohort.canonical_bytes()}, parity, reduced


def _reduce_handoffs(configs, spec, found, products, writer, payloads):
    from empirical_lawhood.domains.matrix.model_free.bindings import calculate
    from empirical_lawhood.domains.matrix.classical_series.arrays import decode_acquisition
    from empirical_lawhood.api.model_free_matrix import _exposure_readout

    reduced = {}
    parity = {}
    summaries = {}
    rows = {
        r.unit_id: dict(unit_id=r.unit_id, seed=r.seed, role=r.role, modules={}) for r in spec.assignments
    }
    artifacts = {}
    stages = sorted(
        (c for c in configs if c.phase in ("analyse", "synthesise")),
        key=lambda c: (c.phase == "synthesise", c.node_id),
    )

    def comparison(p):
        x = p.payload.copy()
        x.pop("execution_metrics")
        return x

    for c in stages:
        parents = [found[k] for k in products["reduction_plans"][c.node_id].dependency_task_ids]
        if c.phase == "analyse":
            (acquired,) = parents
            if acquired.config.phase != "acquire":
                raise ValueError("Root analysis requires its original acquisition")
            with read_array(acquired, products["outputs"], writer) as handle:
                content = decode_acquisition(acquired, handle)
                if handle.read(1):
                    raise ValueError("Trailing native acquisition bytes")
            new = calculate(c, parents, acquired_payloads={acquired.identity.object_fingerprint: content})
            del content
        else:
            new = calculate(c, parents)
        if c.node_id in found:
            old = found[c.node_id]
            if (
                new.config != old.config
                or comparison(new) != comparison(old)
                or new.dependencies != old.dependencies
            ):
                raise ValueError(
                    "Recomputed model-free analysis differs in its scientific operands or result"
                )
            parity[c.node_id] = old.fingerprint()
            chosen = old
        else:
            reduced[c.node_id] = new
            found[c.node_id] = new
            chosen = new
        if c.phase == "analyse":
            (unit,) = c.assignments
            rows[unit.unit_id]["modules"][c.module] = {
                "identity": chosen.identity.to_document(),
                "acquisition": parents[0].identity.to_document(),
                "payload": chosen.payload,
                "original_receipt": None
                if c.node_id in reduced
                else products["receipts"][c.node_id].fingerprint(),
            }
        else:
            summaries[c.module] = {"identity": chosen.identity.to_document(), "result": chosen.payload}
    if len(rows) != len(spec.assignments) or any(
        set(rows[r.unit_id]["modules"]) != set(r.modules) for r in spec.assignments
    ):
        raise ValueError("Independent reduction loses an assigned root or module")
    science = dict(
        assigned_roots=len(rows),
        population_summaries=summaries,
        full_census_evaluated=True,
        new_native_acquisitions=0,
        **_exposure_readout(spec),
    )
    artifacts["assigned-roots.json"] = (
        json.dumps(list(rows.values()), sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    return science, artifacts, parity, reduced


def reduce_closed_matrix_panel(
    *, study, directory, artifact_writer, project_root, expected_git, exposed_complete_control=False
):
    """Replay pure reductions only after full authentication in the exact producer checkout."""
    from empirical_lawhood.domains.matrix import __file__ as matrix_source

    if not Path(matrix_source).resolve().is_relative_to(Path(project_root).resolve() / "src"):
        raise ValueError("Import the numerical methods from the selected producer checkout")
    if study == "r25":
        from empirical_lawhood.domains.matrix.waveform_preparation.records import (
            WaveformSpecification as Specification,
            WaveformProduct as Product,
        )
        from empirical_lawhood.domains.matrix.waveform_preparation.design import configurations

        allowed = ("measure", "cohort")
        reduce = _reduce_waveforms
    elif study == "r26":
        from empirical_lawhood.domains.matrix.model_free.records import Specification, Product
        from empirical_lawhood.domains.matrix.model_free.design import configs_for as configurations

        allowed = ("analyse", "synthesise")
        reduce = _reduce_handoffs
    else:
        raise ValueError("Select R25 or R26")
    retained = {}

    def consume(*, report, products, payloads, artifact_writer, plan, allow_partial, **unused):
        if (
            allow_partial
            or report["operational_terminal"] != "AUTHENTICATED"
            or report["new_native_contact_count"] != 0
        ):
            raise ValueError("A full guarded read of the settled original terminal is required")
        if report["observed_producing_git_head"] != expected_git:
            raise ValueError("The original scientific worker source changed")
        from empirical_lawhood.storage.numerical_provenance import observe_implementation_source

        _, code, lock, head, clean = observe_implementation_source(project_root)
        if (code, lock, head, clean) != (
            report["producing_code_sha256"],
            report["dependency_lock_sha256"],
            expected_git,
            True,
        ):
            raise ValueError("Select the clean frozen numerical source and lock for this reduction")
        term = products["terminal"]
        spec = find_record(payloads, "experiment-specification.json", Specification)
        instance = find_record(payloads, "experiment-instance.json", ExperimentInstanceBinding)
        if instance.specification != spec.identity:
            raise ValueError("Authored experiment does not select this specification")
        configs = configurations(spec)
        found = gather(configs, Product, products, plan)
        missing = {c.node_id for c in configs if c.node_id not in found}
        scope = refusal_checks(
            artifact_writer,
            term,
            report["operational_census"],
            missing,
            {c.node_id for c in configs if c.phase in allowed},
            plan,
            control=exposed_complete_control,
        )
        products = {**products, "reduction_plans": {t.task_id: t for t in plan.tasks}}
        science, rows, parity, reduced = reduce(configs, spec, found, products, artifact_writer, payloads)
        if missing != set(reduced) or len(found) != len(configs):
            raise ValueError("Reconstructed products differ from the closed operation roster")
        for task, value in reduced.items():
            rows[task + ".reanalysis.canonical.json"] = value.canonical_bytes()
        retained.update(rows)
        science.update(
            evaluator="Independent reduction with the exact original scientific functions",
            source_terminal_status=term.operational_status,
            source_report_status=report["status"],
            source_run=term.run_id,
            source_terminal_sha256=term.fingerprint(),
            specification=spec.fingerprint(),
            source=report["observed_producing_git_head"],
            code=report["producing_code_sha256"],
            lock=report["dependency_lock_sha256"],
            plan=plan.fingerprint(),
            original_successful_receipts={
                k: {"id": r.receipt_id, "sha256": r.fingerprint()} for k, r in products["receipts"].items()
            },
            preserved_original_refusals=scope,
            checked_original_reductions=parity,
            reconstructed_products={k: p.fingerprint() for k, p in reduced.items()},
            control=exposed_complete_control,
            analysis_files={name: sha256(body).hexdigest() for name, body in retained.items()},
        )
        retained["scientific-result.json"] = (
            json.dumps(science, sort_keys=True, indent=2, allow_nan=False) + "\n"
        ).encode()
        return {"full_assignment": True, "recomputed": len(reduced), "native_acquisitions": 0}

    _read_recursive_wave_with_retained_roots(
        directory=directory,
        artifact_writer=artifact_writer,
        terminal_product_format="references",
        _scientific_consumer=consume,
    )
    return retained


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("study", choices=("r25", "r26"))
    parser.add_argument("--project-root", type=Path, required=True, help="Original clean producing checkout")
    parser.add_argument(
        "--profile", type=Path, required=True, help="Selected current access profile for the original store"
    )
    parser.add_argument(
        "--artifact-root-contract", type=Path, help="Frozen storage contract for a relocated access profile"
    )
    parser.add_argument("--authored-directory", type=Path, required=True)
    parser.add_argument("--expected-git", required=True)
    parser.add_argument("--exposed-complete-control", action="store_true")
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists() or args.output_directory.is_symlink():
        raise FileExistsError(args.output_directory)
    service = create_investigation_service(
        project_root=args.project_root,
        operator_profile=args.profile,
        artifact_root_contract=args.artifact_root_contract,
    )
    evidence = reduce_closed_matrix_panel(
        study=args.study,
        directory=args.authored_directory,
        artifact_writer=service.artifact_writer,
        project_root=args.project_root,
        expected_git=args.expected_git,
        exposed_complete_control=args.exposed_complete_control,
    )
    # A partial directory never advertises a completed scientific result.
    args.output_directory.mkdir()
    for name in sorted(evidence, key=lambda k: k == "scientific-result.json"):
        with (args.output_directory / name).open("xb") as stream:
            stream.write(evidence[name])
    print(sha256(evidence["scientific-result.json"]).hexdigest(), args.output_directory)


if __name__ == "__main__":
    main()
