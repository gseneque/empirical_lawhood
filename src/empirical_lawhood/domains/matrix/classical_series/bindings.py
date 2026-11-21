# SPDX-License-Identifier: MPL-2.0
"""Typed workers using shared scheduling, custody, resources and recovery."""
from dataclasses import replace
from functools import lru_cache, partial
from hashlib import sha256
from time import perf_counter
from types import MappingProxyType

from empirical_lawhood.science.evidence.evidence import EvidenceCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition, AssessmentPhase, RequirementSupplyAssessment
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload
from empirical_lawhood.execution.plans import OutputTemplate
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_provider import RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties

from . import design
from .records import Acquisition, Analysis, Calibration, RootSummary, PopulationSummary, NAMESPACE, SeriesOperationConfig, SeriesSpecification, json_text


def units(config):
    return tuple(r.unit_id for r in config.assignments)


def operands(config):
    return (config.specification.object_fingerprint,)


def prepare_root(context):
    """Validate the complete graph once, with constant-size per-root checks."""
    configs = tuple(row.record for row in context.config_inputs)
    if not configs or any(type(c) is not SeriesOperationConfig for c in configs):
        raise ValueError("classical series requires its exact complete operation census")
    first = configs[0]
    if any((c.specification, c.settings_json, c.evidence_scope) !=
            (first.specification, first.settings_json, first.evidence_scope) for c in configs):
        raise ValueError("classical operations cannot mix scientific definitions")
    root = context.root
    if (root.study_id != "study." + NAMESPACE + "." + first.specification.object_fingerprint
            or root.world_id != design.WORLD or first.specification not in root.scientific_operands
            or root.system.object_fingerprint != sha256(first.settings_json.encode()).hexdigest()
            or root.access_pair != (design.ACCESS, design.VISIBILITY)):
        raise ValueError("classical operations change their declared scientific root")
    by_node = {c.node_id: c for c in configs}
    if len(by_node) != len(configs):
        raise ValueError("duplicate classical operation")
    acquire = {c.assignments[0].unit_id: c for c in configs if c.phase == "acquire"}
    analyses = {c.assignments[0].unit_id: c for c in configs if c.phase == "analyse"}
    summaries = {c.assignments[0].unit_id: c for c in configs if c.phase == "summarise"}
    calibrators = tuple(c for c in configs if c.phase == "calibrate")
    synthesis = tuple(c for c in configs if c.phase == "synthesise")
    if len(synthesis) != 1 or tuple(r.unit_id for r in synthesis[0].assignments) != tuple(sorted(analyses)):
        raise ValueError("synthesis must preserve every assigned CONF root")
    expected = set()
    if first.evidence_scope == "PREDECLARED_DEVELOPMENT":
        if len(calibrators) != 1 or not acquire or context.external_inputs:
            raise ValueError("new series requires native roots and one frozen calibration supplier")
        calibration, = calibrators
        training = {r.unit_id: r for r in calibration.assignments}
        confirmation = {key: c for key, c in acquire.items() if c.assignments[0].role == "confirmation"}
        if (set(acquire) != set(training) | set(confirmation) or set(analyses) != set(confirmation)
                or set(summaries) != set(training)
                or tuple(sorted(acquire)) != root.assigned_unit_ids):
            raise ValueError("classical graph loses its complete disjoint root allocation")
        for key, assigned in training.items():
            if acquire[key].assignments != (assigned,):
                raise ValueError("TRAIN/CAL roles differ between acquisition and frozen supplier")
            if summaries[key].assignments != (assigned,):
                raise ValueError("training summary changes its root role")
            expected.add((calibration.node_id, "summaries." + key, summaries[key].node_id, None))
            expected.add((summaries[key].node_id, "acquisition", acquire[key].node_id, None))
            expected.add((summaries[key].node_id, "arrays", acquire[key].node_id, None))
        for key, config in confirmation.items():
            expected.add((config.node_id, "calibration", calibration.node_id, None))
            expected.add((analyses[key].node_id, "calibration", calibration.node_id, None))
            expected.add((analyses[key].node_id, "acquisition", config.node_id, None))
            expected.add((analyses[key].node_id, "arrays", config.node_id, None))
    else:
        if calibrators or acquire or summaries or not analyses:
            raise ValueError("reanalysis may not reacquire roots or recalibrate the original supplier")
        if not set(analyses) <= set(root.assigned_unit_ids):
            raise ValueError("reanalysis changes its original root census")
        external_ids = {p.input_id for p in context.external_inputs}
        if external_ids != {"external.calibration"} | {"external." + key for key in analyses} | {"external.arrays." + key for key in analyses}:
            raise ValueError("reanalysis loses its original frozen model or CONF acquisitions")
        for key, config in analyses.items():
            expected.add((config.node_id, "calibration", None, "external.calibration"))
            expected.add((config.node_id, "acquisition", None, "external." + key))
            expected.add((config.node_id, "arrays", None, "external.arrays." + key))
    for key, config in analyses.items():
        expected.add((synthesis[0].node_id, "analyses." + key, config.node_id, None))
    actual = {(p.consumer_node_id, p.consumer_input_id, p.producer_node_id, p.external_input_id) for p in context.links}
    if actual != expected or len(actual) != len(context.links):
        raise ValueError("classical graph changes causal TRAIN/CAL/CONF dependencies")
    internal = {p.edge_id: p for p in context.links if p.producer_node_id is not None and p.requirement_id is not None}
    reqs = {p.requirement_id: p for p in context.requirements}
    conns = {p.connection_id: p for p in context.connections}
    if len(reqs) != len(internal) or len(conns) != len(internal):
        raise ValueError("every recursive supply requires its explicit assessment")
    for link in internal.values():
        req, conn = reqs.get(link.requirement_id), conns.get(link.connection_id)
        if (req is None or conn is None or req.consumer_operation_id != link.consumer_node_id
                or req.assessment_operation_id != link.consumer_node_id
                or conn.requirement_id != req.requirement_id or conn.supplier_operation_id != link.producer_node_id
                or conn.consumer_input_id != link.consumer_input_id or conn.supplier_output_id != "product"
                or conn.assessment_operation_id != link.consumer_node_id):
            raise ValueError("classical scientific consumer differs from its artifact dependency")
    return MappingProxyType(by_node)


def root_validator(config, context):
    if (context.scientific_preparation.get(context.node_id) != config
            or context.node_id != config.node_id or context.unit_ids != units(config)
            or not set(context.unit_ids) <= set(context.selected_unit_ids)
            or context.stage is not design.stage(config.phase) or context.complete_unit_census
            or context.outcome_access is not design.ACCESS or context.visibility_ceiling is not design.VISIBILITY):
        raise ValueError("classical worker changes its exact assigned operation contract")


def assessment_projector(record, requirement, connection):
    if type(record) not in (Acquisition, Calibration, Analysis, RootSummary, PopulationSummary):
        return ()
    if record.config.node_id != connection.assessment_operation_id:
        raise ValueError("supply assessment changes its actual consuming operation")
    dependencies = (record.analyses if type(record) is PopulationSummary else
        record.acquisition_inputs if type(record) is Calibration else
        (record.acquisition, record.calibration) if type(record) is Analysis else
        (record.acquisition,) if type(record) is RootSummary else
        (() if record.calibration is None else (record.calibration,)))
    expected_id = connection.supplier_operation_id + ".product"
    selected = tuple(pin for pin in dependencies if pin.object_id == expected_id)
    if len(selected) != 1:
        raise ValueError("consumer did not retain the selected original supplier")
    # This checks supplied operands, not the numerical hypothesis or forecast.
    return (RequirementSupplyAssessment("assessment." + connection.connection_id,
        ObjectIdentity.from_record(requirement.requirement_id, requirement),
        ObjectIdentity.from_record(connection.connection_id, connection), AssessmentPhase.INSTANCE,
        AssessmentDisposition.SATISFIED, record.config.node_id,
        tuple(sorted((*selected, record.identity), key=lambda p: p.object_id)), ()),)


def _same_settings(left, right, *, phases_may_differ=False):
    left, right = left.copy(), right.copy()
    if phases_may_differ:
        left.pop("phases", None)
        right.pop("phases", None)
    return left == right


def calculate(config, acquisitions, calibration, *, summaries=(), analyses=(), acquired_payloads=None):
    """Dispatch pure in-memory simulator computations; no hidden engine contact."""
    from threadpoolctl import threadpool_limits
    from .science import acquire_native_root, analyse_native_root, calibrate_native_roots, summarise_native_root
    started = perf_counter()
    def native_payload(product):
        if acquired_payloads is None:
            return product.payload
        return acquired_payloads[product.identity.object_fingerprint]
    with threadpool_limits(limits=1):
        if config.phase == "synthesise":
            if acquisitions or summaries or calibration is not None:
                raise ValueError("population synthesis receives only assigned root readouts")
            assigned = {r.seed: r for r in config.assignments}
            if len(analyses) != len(assigned) or {p.config.assignments[0].seed for p in analyses} != set(assigned):
                raise ValueError("population synthesis loses an assigned root")
            if any(p.config.specification != config.specification or p.config.settings_json != config.settings_json
                    or p.config.assignments != (assigned[p.config.assignments[0].seed],) for p in analyses):
                raise ValueError("population synthesis substitutes a root or scientific definition")
            from .aggregate import aggregate_readouts
            payload = aggregate_readouts([p.payload for p in analyses], assigned_seeds=tuple(sorted(assigned)),
                alpha=config.settings["calibration_alpha"], win_margin=config.settings["strict_win_margin"],
                scientific_settings=config.settings)
            return PopulationSummary(config.node_id + ".product", config,
                tuple(sorted((p.identity for p in analyses), key=lambda p: p.object_id)), json_text(payload))
        if analyses:
            raise ValueError("root calculation cannot inspect downstream root readouts")
        if config.phase == "acquire":
            if acquisitions:
                raise ValueError("acquisition cannot receive an already observed native root")
            role = config.assignments[0].role
            if (role == "confirmation") != (calibration is not None):
                raise ValueError("CONF must wait for the frozen supplier, TRAIN/CAL must not read it")
            if calibration is not None and (calibration.config.specification != config.specification
                    or calibration.config.settings_json != config.settings_json):
                raise ValueError("CONF acquisition substitutes its original frozen supplier")
            payload = acquire_native_root(config.settings, config.assignments[0].seed,
                calibration=None if calibration is None else calibration.payload)
            payload["execution_metrics"] = {"numerical_seconds": perf_counter() - started, "numerical_threads": 1}
            return Acquisition(config.node_id + ".product", config, json_text(payload),
                None if calibration is None else calibration.identity)
        if config.phase == "summarise":
            if calibration is not None or summaries or len(acquisitions) != 1:
                raise ValueError("training summary requires exactly one original TRAIN/CAL root")
            acquired, = acquisitions
            if (acquired.config.assignments != config.assignments or acquired.config.specification != config.specification
                    or acquired.config.settings_json != config.settings_json or acquired.calibration is not None):
                raise ValueError("training summary changes original native operands or reads CONF")
            payload = summarise_native_root(config.settings, native_payload(acquired))
            return RootSummary(config.node_id + ".product", config, acquired.identity, json_text(payload))
        if config.phase == "calibrate":
            if calibration is not None or acquisitions:
                raise ValueError("calibration requires compact acquired-root summaries, not CONF or another fitted supplier")
            assigned = {r.seed: r for r in config.assignments}
            if len(summaries) != len(assigned) or {p.config.assignments[0].seed for p in summaries} != set(assigned):
                raise ValueError("calibration requires the complete original TRAIN/CAL census")
            for product in summaries:
                if (product.config.assignments != (assigned[product.config.assignments[0].seed],)
                        or product.config.specification != config.specification
                        or product.config.settings_json != config.settings_json):
                    raise ValueError("calibration changes a TRAIN/CAL root or leaks CONF")
            settings = config.settings
            settings["training_seeds"] = [r.seed for r in config.assignments if r.role == "training"]
            settings["calibration_seeds"] = [r.seed for r in config.assignments if r.role == "calibration"]
            # The supplier seals the complete scientific payload. Never append fields after its freeze.
            payload = calibrate_native_roots(settings, {p.config.assignments[0].unit_id: p.payload for p in summaries})
            return Calibration(config.node_id + ".product", config,
                tuple(sorted((p.identity for p in summaries), key=lambda p: p.object_id)), json_text(payload))
        if len(acquisitions) != 1 or calibration is None:
            raise ValueError("analysis requires one native root and its original frozen supplier")
        acquired, = acquisitions
        if (acquired.config.assignments != config.assignments or acquired.calibration != calibration.identity
                or not _same_settings(acquired.config.settings, config.settings,
                    phases_may_differ=config.evidence_scope == "EXPOSED_REANALYSIS")
                or not _same_settings(calibration.config.settings, config.settings,
                    phases_may_differ=config.evidence_scope == "EXPOSED_REANALYSIS")
                or config.evidence_scope != "EXPOSED_REANALYSIS" and acquired.config.specification != config.specification):
            raise ValueError("analysis changes its native operands, numerical settings or frozen calibration")
        payload = analyse_native_root(config.settings, native_payload(acquired), calibration=calibration.payload)
        payload["execution_metrics"] = {"numerical_seconds": perf_counter() - started, "numerical_threads": 1}
        return Analysis(config.node_id + ".product", config, acquired.identity, calibration.identity, json_text(payload))


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def _calculate(self, context):
        from empirical_lawhood.domains.matrix.matrix_array_chunks import FRAMED_ARRAY_SCHEMA
        from .arrays import decode_acquisition, encode_acquisition
        codecs = {c.SCHEMA: c for c in (SeriesOperationConfig, Acquisition, Calibration, RootSummary, Analysis)}
        received = {kind: [] for kind in codecs.values()}
        binary = {}
        for port in context.input_ports:
            if port.payload_schema == FRAMED_ARRAY_SCHEMA:
                if port.artifact_id in binary:
                    raise ValueError("classical worker duplicates an array companion")
                binary[port.artifact_id] = port
                continue
            kind = codecs.get(port.payload_schema)
            if kind is None or port.media_type != "application/json":
                raise ValueError("classical worker receives an undeclared scientific input")
            received[kind].append(port.decode_canonical_record(kind, maximum_bytes=port.size_bytes))
        if len(received[SeriesOperationConfig]) != 1 or len(received[Calibration]) > 1:
            raise ValueError("classical worker input roles are ambiguous")
        config, = received[SeriesOperationConfig]
        if (config.node_id != context.task_id or config.config_id != context.config.config_id
                or config.fingerprint() != context.config.content_sha256
                or context.resource_budget != design.budget_for(config) or context.permissions != design.PERMISSIONS
                or context.outcome_access is not design.ACCESS):
            raise ValueError("classical worker changes its compiled configuration or numerical semantics")
        acquisitions = received[Acquisition]
        if any(p.array_artifact is None for p in acquisitions):
            raise ValueError("native acquisition lacks its required binary operand companion")
        if set(binary) != {p.array_artifact.artifact_id for p in acquisitions if p.array_artifact is not None}:
            raise ValueError("classical worker loses or adds a binary operand companion")
        decoded = {p.identity.object_fingerprint: decode_acquisition(p, binary[p.array_artifact.artifact_id])
            for p in acquisitions}
        product = calculate(config, acquisitions, received[Calibration][0] if received[Calibration] else None,
            summaries=received[RootSummary], analyses=received[Analysis], acquired_payloads=decoded)
        arrays = None
        expected = (context.task_id + ".arrays", context.task_id + ".product") if config.phase == "acquire" else (context.task_id + ".product",)
        if tuple(p.output_id for p in context.output_ports) != expected:
            raise ValueError("classical worker changes its exact output census")
        if config.phase == "acquire":
            array_port = next(p for p in context.output_ports if p.output_id.endswith(".arrays"))
            product, arrays = encode_acquisition(product, artifact_id=array_port.logical_artifact_id)
        return product, arrays

    def execute_streaming(self, context, emitter, progress=None):
        from .arrays import iter_encoded_bytes
        try:
            product, arrays = self._calculate(context)
            if arrays is not None:
                for block in iter_encoded_bytes(product, arrays):
                    emitter.write(context.task_id + ".arrays", block)
            raw = product.canonical_bytes()
            for offset in range(0, len(raw), 1024**2):
                emitter.write(context.task_id + ".product", raw[offset:offset + 1024**2])
            return (ReceiptCheck("classical-series-complete-input-census", True, ()),)
        finally:
            for port in context.input_ports:
                port.close()

    def execute(self, context):
        from .arrays import iter_encoded_bytes
        try:
            product, arrays = self._calculate(context)
            outputs = []
            if arrays is not None:
                outputs.append(TaskOutputPayload(context.task_id + ".arrays", b"".join(iter_encoded_bytes(product, arrays))))
            outputs.append(TaskOutputPayload(context.task_id + ".product", product.canonical_bytes()))
            return RunnerResult(tuple(outputs), (ReceiptCheck("classical-series-complete-input-census", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


@lru_cache(maxsize=1)
def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_FRAMED_CODEC, MATRIX_FRAMED_ARRAY_SCHEMA
    codecs = {c.SCHEMA: c for c in (SeriesSpecification, SeriesOperationConfig, Acquisition, Calibration, Analysis, RootSummary, PopulationSummary)}
    rows = []
    for phase in ("acquire", "analyse", "calibrate", "summarise", "synthesise"):
        if phase == "acquire":
            ports = (RecursivePortContract("calibration", Calibration.SCHEMA, "application/json", None, 0, 1),)
        elif phase == "synthesise":
            ports = (RecursivePortContract("analyses", Analysis.SCHEMA, "application/json", None, 1, None),)
        elif phase == "calibrate":
            ports = (RecursivePortContract("summaries", RootSummary.SCHEMA, "application/json", None, 2, None),)
        else:
            ports = (RecursivePortContract("acquisition", Acquisition.SCHEMA, "application/json", None),
                RecursivePortContract("arrays", MATRIX_FRAMED_ARRAY_SCHEMA, "application/octet-stream", None))
            if phase == "analyse":
                ports += (RecursivePortContract("calibration", Calibration.SCHEMA, "application/json", None),)
        output = {"acquire": Acquisition, "calibrate": Calibration, "analyse": Analysis, "summarise": RootSummary, "synthesise": PopulationSummary}[phase]
        declaration = RecursiveOperationDeclaration(capability_key=NAMESPACE + "." + phase, capability_version="1.0.0",
            implementation_id=NAMESPACE + "." + phase + ".v1",
            kind={"acquire": CapabilityKind.SIMULATOR, "calibrate": CapabilityKind.ANALYSIS, "analyse": CapabilityKind.FALSIFIER, "summarise": CapabilityKind.TRANSFORM, "synthesise": CapabilityKind.ANALYSIS}[phase],
            config_record_type=SeriesOperationConfig, stage=design.stage(phase), input_ports=ports,
            outputs=((OutputTemplate("arrays", MATRIX_FRAMED_ARRAY_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES,
                "application/octet-stream", ".bin"),) if phase == "acquire" else ()) +
                (OutputTemplate("product", output.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
            permissions=design.PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
            outcome_access=design.ACCESS, visibility_ceiling=design.VISIBILITY, resources=design.BUDGET,
            conformance_check_ids=("classical-series.complete-census", "classical-series.frozen-before-confirmation"),
            runner_factory=Runner, record_codecs=codecs, storage_codecs=(MATRIX_FRAMED_CODEC,),
            execution_properties=RecursiveExecutionProperties(deterministic=False),
            scientific_hooks=RecursiveScientificHooks(assessment_projector=assessment_projector,
                scientific_operand_sha256s=operands, scientific_unit_ids=units,
                scientific_root_preparer=prepare_root, scientific_root_validator=root_validator))
        rows.append(replace(declaration, runner_factory=partial(Runner, manifest=declaration.manifest())))
    return tuple(rows)
