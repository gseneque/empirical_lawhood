# SPDX-License-Identifier: MPL-2.0
"""Public authoring and retained-result access for the classical matrix series."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection, ExperimentFileInputBinding, ExperimentFileInputSelection
from empirical_lawhood.domains.matrix.classical_series import design, experiment
from empirical_lawhood.domains.matrix.classical_series.records import (
    Acquisition, Analysis, Calibration, PopulationSummary, RootAssignment, RetainedInput, RetainedArray,
    NAMESPACE, PROTOCOL_ID, SeriesSpecification, json_text, _pairs,
)

DEFINITION_SCHEMA = "classical-series-definition.v1"


def load_definition(path):
    """Read the sole editable scientific document; no hand-authored identities."""
    from empirical_lawhood.domains.matrix.classical_series.science import normalise_config
    raw = Path(path).read_bytes()
    def invalid(value):
        raise ValueError("nonfinite authored number: " + value)
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=invalid)
    if type(value) is not dict or set(value) != {"schema", "label", "roots", "settings"} or value["schema"] != DEFINITION_SCHEMA:
        raise ValueError("classical series definition requires schema, label, roots and settings only")
    if type(value["label"]) is not str or not value["label"].strip():
        raise ValueError("author a meaningful study label")
    roles = value["roots"]
    if type(roles) is not dict or set(roles) != {"training", "calibration", "confirmation"}:
        raise ValueError("author the complete disjoint TRAIN/CAL/CONF seed allocation")
    assignments = []
    for role in ("training", "calibration", "confirmation"):
        if type(roles[role]) is not list or not roles[role]:
            raise ValueError("every root role requires its explicit seed list")
        assignments.extend(RootAssignment(seed, role) for seed in roles[role])
    assignments = tuple(sorted(assignments, key=lambda r: r.seed))
    if len({r.seed for r in assignments}) != len(assignments):
        raise ValueError("TRAIN/CAL/CONF seeds overlap; labels do not confer independence")
    settings = normalise_config(value["settings"])
    return raw, value["label"], assignments, settings


def _specification(label, assignments, settings, *, mode="new-development", records=(), arrays=()):
    pins = tuple(sorted((RetainedInput(key, value.identity) for key, value in records), key=lambda r: r.key))
    binary = tuple(sorted((RetainedArray(key, value) for key, value in arrays), key=lambda r: r.key))
    selected = {"label":label, "assignments":[r.to_document() for r in assignments], "settings":settings,
        "mode":mode,"retained":[r.to_document() for r in pins],"arrays":[r.to_document() for r in binary]}
    identifier = "specification." + NAMESPACE + "." + sha256(json_text(selected).encode()).hexdigest()
    return SeriesSpecification(identifier, json_text(settings), assignments, label, mode, pins,
        "PREDECLARED_DEVELOPMENT" if mode == "new-development" else "EXPOSED_REANALYSIS", binary)


def _write_inputs(*, destination, project_root, raw_definition, specification, records, files, extra=None):
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    source = implementation_binding(Path(project_root))
    bindings = []
    payloads = {"definition.json":raw_definition,"specification.json":specification.canonical_bytes(),
        "source-snapshot.json":source.canonical_bytes()}
    for key, record in sorted(records.items()):
        name = key + ".json"
        raw = record.canonical_bytes()
        payloads[name] = raw
        bindings.append(ExperimentInputBinding(key, record.identity, name, len(raw)))
    file_bindings = tuple(ExperimentFileInputBinding(key, identity, "1.0.0", name, identity.size_bytes)
        for key, (identity, name) in sorted(files.items()))
    if file_bindings:
        sources = ExperimentFileInputSelection("inputs." + NAMESPACE + "." + specification.fingerprint(),
            PROTOCOL_ID, tuple(bindings), file_bindings)
    else:
        sources = ExperimentInputSelection("inputs." + NAMESPACE + "." + specification.fingerprint(), PROTOCOL_ID, tuple(bindings))
    payloads["sources.json"] = sources.canonical_bytes()
    if extra:
        payloads.update(extra)
    for name, raw in sorted(payloads.items()):
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    return {"specification":str(destination / "specification.json"), "sources":str(destination / "sources.json"),
        "source_snapshot":str(destination / "source-snapshot.json"), "definition":str(destination / "definition.json"),
        "assigned_roots":len(specification.assignments),"mode":specification.mode,
        "qualification":"NOT_ESTABLISHED", "native_acquisition_performed":False}


def create_inputs(*, definition_path, project_root, output_directory):
    """Freeze one human-authored definition and derive the complete recursive plan."""
    raw, label, assignments, settings = load_definition(definition_path)
    specification = _specification(label, assignments, settings)
    experiment.bind_inputs(specification, {})
    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError("classical inputs require a new explicit destination")
    destination.mkdir(parents=True, exist_ok=False)
    return _write_inputs(destination=destination, project_root=project_root, raw_definition=raw,
        specification=specification, records={}, files={})


def create_reanalysis_inputs(*, definition_path, project_root, output_directory, parent_directory, parent_service):
    """Copy exact original products inside their active custody verification scope.

    This derives a new analysis identity and reuses the original native array
    bytes and frozen calibration. No parent native work or model fit is replayed.
    """
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    from empirical_lawhood.api.experiment_scientific_read import read_prepared_development_science
    from empirical_lawhood.storage.recursive_custody import iter_exact_custody_file_chunks
    raw, label, assignments, settings = load_definition(definition_path)
    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError("reanalysis requires a new explicit destination")
    destination.mkdir(parents=True, exist_ok=False)
    records, files, provenance = {}, {}, {}

    def consume(**kwargs):
        scientific = read_prepared_development_science(**kwargs)
        if (scientific is None or scientific.get("namespace") != NAMESPACE
                or scientific.get("scientific_completion") != "COMPLETED"):
            raise ValueError("reanalysis requires a complete original classical-series run")
        payloads, products, plane = kwargs["payloads"], kwargs["products"], kwargs["artifact_writer"]
        original = decode_canonical_bytes(payloads["experiment-specification.json"], SeriesSpecification, maximum_bytes=None)
        if original.mode != "new-development":
            raise ValueError("select the original native run as reanalysis parent; reanalyses do not own native bytes")
        if original.assignments != assignments:
            raise ValueError("reanalysis cannot add, drop, reseed or relabel original independent roots")
        previous, current = original.settings, settings.copy()
        previous.pop("phases", None)
        current.pop("phases", None)
        if previous != current:
            raise ValueError("reanalysis cannot change the original numerical acquisition or assessment settings")
        for task_records in products["records"].values():
            for record in task_records.values():
                if type(record) is Calibration:
                    if "calibration" in records:
                        raise ValueError("original run has multiple frozen calibration products")
                    records["calibration"] = record
                elif type(record) is Acquisition and record.config.assignments[0].role == "confirmation":
                    key = record.config.assignments[0].unit_id
                    records[key] = record
                    identity = record.array_artifact
                    manifest = products["outputs"].get(identity.artifact_id)
                    if (manifest is None or manifest.logical.content_sha256 != identity.sha256
                            or manifest.materialization.size_bytes != identity.size_bytes
                            or manifest.logical.payload_schema != identity.payload_schema):
                        raise ValueError("original root lacks its exact binary operand receipt")
                    relative = "arrays." + key + ".bin"
                    path = plane.root.resolve(manifest.materialization.relative_path, for_write=False)
                    with (destination / relative).open("xb") as stream:
                        for block in iter_exact_custody_file_chunks(path, size_bytes=identity.size_bytes,
                                expected_sha256=identity.sha256, read_guard=plane.require_verification_snapshot):
                            stream.write(block)
                    files["arrays." + key] = (identity, relative)
        provenance.update({"parent_specification":original.identity.to_document(),
            "parent_packet_sha256":kwargs["report"]["packet_sha256"],
            "parent_execution_plan_sha256":kwargs["report"]["execution_plan_sha256"],
            "parent_producing_source_sha256":kwargs["report"]["producing_code_sha256"],
            "original_calibration":records["calibration"].identity.to_document(),
            "native_work_repeated":False,"calibration_repeated":False,"evidence_scope":"EXPOSED_REANALYSIS"})
        return scientific

    _read_recursive_wave_with_retained_roots(directory=Path(parent_directory), artifact_writer=parent_service.artifact_writer,
        include_products=True, terminal_product_format="references", _scientific_consumer=consume)
    specification = _specification(label, assignments, settings, mode="reanalysis", records=tuple(records.items()),
        arrays=tuple((key, value[0]) for key, value in files.items()))
    experiment.bind_inputs(specification, records)
    return _write_inputs(destination=destination, project_root=project_root, raw_definition=raw,
        specification=specification, records=records, files=files,
        extra={"parent-custody.json":(json.dumps(provenance, indent=2, sort_keys=True)+"\n").encode()})


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    """Present only authenticated original products; no numerical reconstruction."""
    if type(specification) is not SeriesSpecification or instance.specification != specification.identity:
        raise PermissionError("classical reader substitutes its original authored definition")
    configs = design.configs_for(specification)
    if set(t.task_id for t in plan.tasks) != {c.node_id for c in configs} or report.get("run_id") != plan.source_plan.object_id:
        raise PermissionError("classical reader changes the original complete operation census")
    confirmation = tuple(r for r in specification.assignments if r.role == "confirmation")
    base = {"namespace":NAMESPACE,"mode":specification.mode,"study_label":specification.study_label,
        "evidence_scope":specification.evidence_scope,"qualification":"NOT_ESTABLISHED",
        "assigned_roots":len(specification.assignments),"assigned_confirmation_roots":len(confirmation),
        "root_roles":{role:[r.seed for r in specification.assignments if r.role==role] for role in ("training","calibration","confirmation")},
        "historical_qualification_changed":False,"scientific_reconstruction_performed":False,
        "native_acquisition_performed":False,"selected_phases":specification.settings["phases"]}
    if allow_partial or report.get("typed_product_validation") == "DEFERRED":
        return {**base,"scientific_completion":"DEFERRED","population_summary":None}
    expected = {"acquire":Acquisition,"analyse":Analysis,"calibrate":Calibration,"synthesise":PopulationSummary}
    from empirical_lawhood.domains.matrix.classical_series.records import RootSummary
    expected["summarise"] = RootSummary
    found = {}
    for config in configs:
        receipt = products["receipts"].get(config.node_id)
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            continue
        record = products["records"].get(config.node_id, {}).get(config.node_id + ".product")
        if type(record) is not expected[config.phase] or record.config != config:
            raise PermissionError("classical reader substitutes an actual original scientific result")
        found[config.node_id] = record
    root_reports = {p.config.assignments[0].seed:p.payload for p in found.values() if type(p) is Analysis}
    population = next((p for p in found.values() if type(p) is PopulationSummary), None)
    frozen = next((p for p in found.values() if type(p) is Calibration), None)
    if population is not None:
        pins = tuple(sorted((p.identity for p in found.values() if type(p) is Analysis), key=lambda p:p.object_id))
        if population.analyses != pins:
            raise PermissionError("population summary omits or substitutes an original root readout")
    return {**base,"scientific_completion":"COMPLETED" if len(found)==len(configs) and population is not None else "INCOMPLETE",
        "completed_operations":len(found),"assigned_operations":len(configs),
        "population_summary":None if population is None else population.payload,
        "population_summary_identity":None if population is None else population.identity.to_document(),
        "frozen_calibration":None if frozen is None else {"identity":frozen.identity.to_document(),"result":frozen.payload},
        "roots":[{"seed":r.seed,"unit_id":r.unit_id,"status":"AVAILABLE" if r.seed in root_reports else "UNAVAILABLE",
            "result":root_reports.get(r.seed)} for r in confirmation],
        "array_custody":{"containers":sum(type(p) is Acquisition for p in found.values()),
            "physical_bytes":sum(p.array_artifact.size_bytes for p in found.values() if type(p) is Acquisition),
            "full_populations_are_chunked":True},
        "cost_policy":"Include original shared task/attempt receipts, TRAIN/CAL, failed cases and all preparation arms; no realised saving inferred."}


__all__ = ["create_inputs", "create_reanalysis_inputs", "load_definition"]
