# SPDX-License-Identifier: MPL-2.0
"""Scientific operations using existing execution, framed arrays and custody."""
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
from .records import NAMESPACE, PREREQUISITES, PAYLOAD_SCHEMAS, OperationConfig, Product, Specification, json_text, selection_key
from .settings import require_current_settings


def units(config):
    return tuple(r.unit_id for r in config.assignments)


def operands(config):
    return (config.specification.object_fingerprint,)


def prepare_root(context):
    configs = tuple(row.record for row in context.config_inputs)
    if not configs or any(type(c) is not OperationConfig for c in configs):
        raise ValueError("model-free graph needs its exact complete operation census")
    first = configs[0]
    require_current_settings(first.settings_json)
    if any((c.specification, c.settings_json, c.evidence_scope) != (first.specification, first.settings_json, first.evidence_scope) for c in configs):
        raise ValueError("model-free graph mixes scientific definitions")
    root = context.root
    if (root.study_id != "study." + NAMESPACE + "." + first.specification.object_fingerprint or root.world_id != design.WORLD
            or first.specification not in root.scientific_operands or root.system.object_fingerprint != sha256(first.settings_json.encode()).hexdigest()
            or root.access_pair != (design.ACCESS, design.VISIBILITY)):
        raise ValueError("model-free graph changes its scientific root")
    by_node = {c.node_id: c for c in configs}
    if len(by_node) != len(configs):
        raise ValueError("duplicate scientific operation")
    acquired = {(c.module, c.assignments[0].seed): c for c in configs if c.phase == "acquire"}
    analyses = {(c.module, c.assignments[0].seed): c for c in configs if c.phase == "analyse"}
    summaries = {c.module: c for c in configs if c.phase == "synthesise"}
    if len(summaries) != sum(c.phase == "synthesise" for c in configs) or set(summaries) != {m for m, _ in analyses}:
        raise ValueError("module synthesis loses a scientific population")
    all_units = {r.unit_id for c in summaries.values() for r in c.assignments}
    if tuple(sorted(all_units)) != root.assigned_unit_ids:
        raise ValueError("model-free graph changes the independent-root denominator")
    expected = set()
    for module, summary in summaries.items():
        if {(module, r.seed) for r in summary.assignments} != {k for k in analyses if k[0] == module}:
            raise ValueError("module synthesis omits an assigned outcome")
        for row in summary.assignments:
            analysis = analyses[(module, row.seed)]
            if analysis.assignments != (row,):
                raise ValueError("module analysis changes a root's assigned role")
            expected.add((summary.node_id, "analyses." + row.unit_id, analysis.node_id, "product", None))
    new = first.evidence_scope == "PREDECLARED_DEVELOPMENT"
    if new and (set(acquired) != set(analyses) or context.external_inputs):
        raise ValueError("new model-free graph changes its native acquisition census")
    if not new and acquired:
        raise ValueError("reanalysis must never reacquire native work")
    for key, analysis in analyses.items():
        if new:
            acquisition = acquired[key]
            if acquisition.assignments != analysis.assignments:
                raise ValueError("native acquisition changes its actual assigned root")
            expected.add((analysis.node_id, "acquisition", acquisition.node_id, "product", None))
            expected.add((analysis.node_id, "arrays.acquisition", acquisition.node_id, "arrays", None))
            for upstream in PREREQUISITES.get(key[0], ()):
                supplier = acquired.get((upstream, key[1]))
                if supplier is None:
                    raise ValueError("native response lacks its original checkpoint supplier")
                expected.add((acquisition.node_id, "prerequisites." + upstream.lower(), supplier.node_id, "product", None))
                expected.add((acquisition.node_id, "arrays.prerequisites." + upstream.lower(), supplier.node_id, "arrays", None))
        else:
            name = selection_key(key[0], analysis.assignments[0])
            expected.add((analysis.node_id, "acquisition", None, None, "external." + name))
            expected.add((analysis.node_id, "arrays.acquisition", None, None, "external.arrays." + name))
    actual = {(l.consumer_node_id, l.consumer_input_id, l.producer_node_id, l.producer_output_id, l.external_input_id) for l in context.links}
    if actual != expected or len(actual) != len(context.links):
        raise ValueError("model-free causal dependency graph differs from its declared science")
    external_ids = {row[-1] for row in expected if row[-1] is not None}
    if {x.input_id for x in context.external_inputs} != external_ids:
        raise ValueError("reanalysis adds or loses an original operand")
    internal = tuple(l for l in context.links if l.producer_node_id is not None and l.producer_output_id == "product")
    requirements = {r.requirement_id: r for r in context.requirements}
    connections = {r.connection_id: r for r in context.connections}
    if len(requirements) != len(internal) or len(connections) != len(internal):
        raise ValueError("every scientific supply needs its own consumer assessment")
    for link in internal:
        req, conn = requirements.get(link.requirement_id), connections.get(link.connection_id)
        if req is None or conn is None or req.consumer_operation_id != link.consumer_node_id or req.assessment_operation_id != link.consumer_node_id or conn.requirement_id != req.requirement_id or conn.supplier_operation_id != link.producer_node_id or conn.supplier_output_id != "product" or conn.consumer_input_id != link.consumer_input_id or conn.assessment_operation_id != link.consumer_node_id:
            raise ValueError("scientific requirement changes its actual consuming operation")
    return MappingProxyType(by_node)


def root_validator(config, context):
    if context.scientific_preparation.get(context.node_id) != config or context.node_id != config.node_id or context.unit_ids != units(config) or not set(context.unit_ids) <= set(context.selected_unit_ids) or context.stage is not design.stage(config.phase) or context.complete_unit_census or context.outcome_access is not design.ACCESS or context.visibility_ceiling is not design.VISIBILITY:
        raise ValueError("worker changes its exact original scientific contract")


def assessment_projector(record, requirement, connection):
    if type(record) is not Product:
        return ()
    if record.config.node_id != connection.assessment_operation_id:
        raise ValueError("supply assessment belongs to another operation")
    selected = tuple(p for p in record.dependencies if p.object_id == connection.supplier_operation_id + ".product")
    if len(selected) != 1:
        raise ValueError("consumer failed to retain its actual original supplier")
    return (RequirementSupplyAssessment("assessment." + connection.connection_id,
        ObjectIdentity.from_record(requirement.requirement_id, requirement), ObjectIdentity.from_record(connection.connection_id, connection),
        AssessmentPhase.INSTANCE, AssessmentDisposition.SATISFIED, record.config.node_id,
        tuple(sorted((*selected, record.identity), key=lambda p: p.object_id)), ()),)


def calculate(config, products=(), *, acquired_payloads=None):
    from threadpoolctl import threadpool_limits
    from .science import acquire_root, analyse_root, synthesise_roots
    from .retained_analysis import validate_reanalysis_settings
    config.__post_init__()
    require_current_settings(config.settings_json)
    if any(type(p) is not Product for p in products):
        raise ValueError("scientific supplier requires an exact original product")
    for product in products:
        if product.config.settings_json != config.settings_json:
            if config.evidence_scope != "EXPOSED_REANALYSIS" or config.phase != "analyse" or product.config.phase != "acquire":
                raise ValueError("scientific supplier changes its original settings")
            validate_reanalysis_settings(product.config.settings, config.settings, (config.module,))
    if config.evidence_scope != "EXPOSED_REANALYSIS" and any(p.config.specification != config.specification for p in products):
        raise ValueError("new development substitutes a previously exposed supplier")
    def body(product):
        return product.payload if acquired_payloads is None or product.config.phase != "acquire" else acquired_payloads[product.identity.object_fingerprint]
    started = perf_counter()
    with threadpool_limits(limits=1):
        if config.phase == "acquire":
            required = set(PREREQUISITES.get(config.module, ()))
            if len(products) != len(required) or {p.config.module for p in products} != required or any(p.config.phase != "acquire" or p.config.assignments[0].seed != config.assignments[0].seed for p in products):
                raise ValueError("native acquisition changes its declared checkpoint prerequisites")
            assigned = config.assignments[0]
            sampling = None if config.module != "M5" else {key: getattr(assigned, key) for key in
                ("audit_selected", "inclusion_probability", "frame_id", "frame_size", "audit_size")}
            payload = acquire_root(config.settings, assigned.seed, config.module,
                prerequisite_payloads={p.config.module: body(p) for p in products}, sampling=sampling,
                assigned_modules=assigned.modules)
        elif config.phase == "analyse":
            if len(products) != 1:
                raise ValueError("root assessment needs exactly its original native acquisition")
            acquired, = products
            if acquired.config.phase != "acquire" or acquired.config.module != config.module or (acquired.config.assignments[0].seed, acquired.config.assignments[0].role) != (config.assignments[0].seed, config.assignments[0].role):
                raise ValueError("root assessment changes physical operands or population")
            retained_settings = acquired.config.settings if config.module == "M2" and config.evidence_scope == "EXPOSED_REANALYSIS" else None
            payload = analyse_root(config.settings, body(acquired), retained_settings=retained_settings)
        else:
            expected = {r.seed for r in config.assignments}
            if len(products) != len(expected) or {p.config.assignments[0].seed for p in products} != expected or any(p.config.phase != "analyse" or p.config.module != config.module for p in products):
                raise ValueError("population assessment loses assigned roots or mixes modules")
            payload = synthesise_roots(config.settings, [p.payload for p in sorted(products, key=lambda p: p.config.assignments[0].seed)])
    payload = dict(payload, schema=PAYLOAD_SCHEMAS[config.phase], module=config.module)
    payload["evidence_scope"] = config.evidence_scope
    if config.phase != "synthesise":
        payload["seed"] = config.assignments[0].seed
    payload["execution_metrics"] = {"numerical_seconds": perf_counter() - started, "numerical_threads": 1}
    return Product(config.node_id + ".product", config, json_text(payload), tuple(sorted((p.identity for p in products), key=lambda p: p.object_id)))


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def _calculate(self, context):
        from empirical_lawhood.domains.matrix.matrix_array_chunks import FRAMED_ARRAY_SCHEMA
        from empirical_lawhood.domains.matrix.classical_series.arrays import decode_acquisition, encode_acquisition
        configs, products, binary = [], [], {}
        for port in context.input_ports:
            if port.payload_schema == FRAMED_ARRAY_SCHEMA:
                if port.artifact_id in binary:
                    raise ValueError("duplicate native binary companion")
                binary[port.artifact_id] = port
            elif port.payload_schema in (OperationConfig.SCHEMA, Product.SCHEMA) and port.media_type == "application/json":
                kind = OperationConfig if port.payload_schema == OperationConfig.SCHEMA else Product
                (configs if kind is OperationConfig else products).append(port.decode_canonical_record(kind, maximum_bytes=port.size_bytes))
            else:
                raise ValueError("undeclared scientific input")
        if len(configs) != 1:
            raise ValueError("worker needs exactly one declared configuration")
        config, = configs
        require_current_settings(config.settings_json)
        if config.node_id != context.task_id or config.config_id != context.config.config_id or config.fingerprint() != context.config.content_sha256 or context.resource_budget != design.budget_for(config) or context.permissions != design.PERMISSIONS or context.outcome_access is not design.ACCESS:
            raise ValueError("worker changes its compiled scientific configuration")
        acquired = [p for p in products if p.config.phase == "acquire"]
        if any(p.array_artifact is None for p in acquired) or set(binary) != {p.array_artifact.artifact_id for p in acquired}:
            raise ValueError("worker loses an original native array companion")
        decoded = {p.identity.object_fingerprint: decode_acquisition(p, binary[p.array_artifact.artifact_id]) for p in acquired}
        product = calculate(config, tuple(products), acquired_payloads=decoded)
        expected = (context.task_id + ".arrays", context.task_id + ".product") if config.phase == "acquire" else (context.task_id + ".product",)
        if tuple(p.output_id for p in context.output_ports) != expected:
            raise ValueError("worker changes its exact output census")
        if config.phase == "acquire":
            port = next(p for p in context.output_ports if p.output_id.endswith(".arrays"))
            return encode_acquisition(product, artifact_id=port.logical_artifact_id, allow_empty=True)
        return product, None

    def execute_streaming(self, context, emitter, progress=None):
        from empirical_lawhood.domains.matrix.classical_series.arrays import iter_encoded_bytes
        try:
            product, arrays = self._calculate(context)
            if arrays is not None:
                emitter.write(context.task_id + ".arrays", b"")
                for block in iter_encoded_bytes(product, arrays):
                    emitter.write(context.task_id + ".arrays", block)
            raw = product.canonical_bytes()
            for offset in range(0, len(raw), 1024**2):
                emitter.write(context.task_id + ".product", raw[offset:offset + 1024**2])
            return (ReceiptCheck("model-free-complete-original-inputs", True, ()),)
        finally:
            for port in context.input_ports:
                port.close()

    def execute(self, context):
        from empirical_lawhood.domains.matrix.classical_series.arrays import iter_encoded_bytes
        try:
            product, arrays = self._calculate(context)
            outputs = []
            if arrays is not None:
                outputs.append(TaskOutputPayload(context.task_id + ".arrays", b"".join(iter_encoded_bytes(product, arrays))))
            outputs.append(TaskOutputPayload(context.task_id + ".product", product.canonical_bytes()))
            return RunnerResult(tuple(outputs), (ReceiptCheck("model-free-complete-original-inputs", True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


@lru_cache(maxsize=1)
def operation_declarations():
    from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_FRAMED_CODEC, MATRIX_FRAMED_ARRAY_SCHEMA
    rows = []
    codecs = {c.SCHEMA: c for c in (Specification, OperationConfig, Product)}
    for phase in ("acquire", "analyse", "synthesise"):
        if phase == "acquire":
            ports = (RecursivePortContract("arrays", MATRIX_FRAMED_ARRAY_SCHEMA, "application/octet-stream", None, 0, None),
                RecursivePortContract("prerequisites", Product.SCHEMA, "application/json", None, 0, None))
        elif phase == "analyse":
            ports = (RecursivePortContract("acquisition", Product.SCHEMA, "application/json", None),
                RecursivePortContract("arrays", MATRIX_FRAMED_ARRAY_SCHEMA, "application/octet-stream", None, 1, None))
        else:
            ports = (RecursivePortContract("analyses", Product.SCHEMA, "application/json", None, 1, None),)
        declaration = RecursiveOperationDeclaration(capability_key=NAMESPACE + "." + phase, capability_version="1.0.0",
            implementation_id=NAMESPACE + "." + phase + ".v1", kind={"acquire": CapabilityKind.SIMULATOR, "analyse": CapabilityKind.FALSIFIER, "synthesise": CapabilityKind.ANALYSIS}[phase],
            config_record_type=OperationConfig, stage=design.stage(phase), input_ports=ports,
            outputs=((OutputTemplate("arrays", MATRIX_FRAMED_ARRAY_SCHEMA, ArtifactProfile.RAW_SOURCE_BYTES, "application/octet-stream", ".bin"),) if phase == "acquire" else ()) +
                (OutputTemplate("product", Product.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
            permissions=design.PERMISSIONS, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=design.ACCESS,
            visibility_ceiling=design.VISIBILITY, resources=design.BUDGET,
            conformance_check_ids=("model-free.complete-root-census", "model-free.exact-physical-prerequisites"),
            runner_factory=Runner, record_codecs=codecs, storage_codecs=(MATRIX_FRAMED_CODEC,),
            execution_properties=RecursiveExecutionProperties(deterministic=False),
            scientific_hooks=RecursiveScientificHooks(assessment_projector=assessment_projector, scientific_operand_sha256s=operands,
                scientific_unit_ids=units, scientific_root_preparer=prepare_root, scientific_root_validator=root_validator))
        rows.append(replace(declaration, runner_factory=partial(Runner, manifest=declaration.manifest())))
    return tuple(rows)
