# SPDX-License-Identifier: MPL-2.0
"""Single authoritative M0–M7 scientific and workflow declaration."""
from hashlib import sha256
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.execution.extension_bundles import ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration
from empirical_lawhood.execution.extensions import ExtensionDeclaration
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import WorkflowInstallationDeclaration
from empirical_lawhood.execution.workflow_descriptors import Workflow, WorkflowDeclaration, WorkflowOperation, WorkflowInput
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_FRAMED_CODEC
from . import experiment
from .bindings import operation_declarations
from .records import NAMESPACE, PROTOCOL_ID, Product, Specification

_OPERATIONS = operation_declarations()
_PROFILE = ExtensionProfileRegistration("profile-registration." + NAMESPACE + ".workflow", NAMESPACE + ".workflow",
    "1.0.0", ExtensionProfileKind.OBJECTIVE_TERMINAL, ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(o.manifest().fingerprint() for o in _OPERATIONS))).hexdigest())
_WORKFLOW = WorkflowDeclaration(Workflow(workflow_id="model-free-matrix-programme",
    title="Classical matrix programme with model-free methods", kind="authored native acquisition and independent assessment",
    substrates=("six 4x4 Hermitian matrices; physical BAOAB clock",),
    methods=("observed memory", "native receiver certificates", "paired preparation", "finite-population audit", "retained equilibrium", "finite-horizon events"),
    environment="base", operations=tuple(WorkflowOperation("campaign experiment-" + name, boundary, ()) for name, boundary in (
        ("explain", "show independent roots, M0–M7 selections and actual supplier prerequisites"),
        ("prepare", "freeze scientific choices and derive the recursive graph without native work"),
        ("author", "bind the current source and complete original inputs"),
        ("run", "execute direct acquisition, independent root assessment and population synthesis"),
        ("read", "read authenticated compact results without simulation or estimator replay"),
        ("recover", "resume through the existing shared execution owner"))),
    inputs=tuple(WorkflowInput("programmes/foundations/emergent-structure/workflows/model-free/" + name,
        role, schema) for name, role, schema in (
        ("smoke.json", "small native software control", "model-free-matrix-definition.v1"),
        ("pilot.json", "bounded formation/response and memory pilot", "model-free-matrix-definition.v1"),
        ("matched-exposure.json", "separate development recipes with equal integrated coupling exposure", "model-free-matrix-definition.v1"),
        ("transfer.json", "nominal and destination response development", "model-free-matrix-definition.v1"),
        ("population-reveal-all.json", "complete native reveal-all benchmark before sparse deployment", "model-free-matrix-definition.v1"),
        ("population.json", "fresh-root sparse deployment requiring an authenticated reveal-all benchmark", "model-free-matrix-definition.v1"),
        ("equilibrium-events.json", "separate equilibrium and event feasibility", "model-free-matrix-definition.v1"),
        ("programme.json", "union of pilot, reveal-all population and equilibrium/event roots; not additional replication", "model-free-matrix-definition.v1"),
        ("confirmation.json", "planning response confirmation allocation requiring an authenticated parent", "model-free-matrix-definition.v1"),
        ("memory-reanalysis.json", "exposed retained-memory analysis requiring the complete original parent", "model-free-matrix-definition.v1"),
        ("memory-confirmation.json", "planning memory confirmation allocation requiring an authenticated parent", "model-free-matrix-definition.v1"),
        ("receiver-memory-reanalysis.json", "exposed reanalysis of the common H64 future on original pilot M2 roots", "model-free-matrix-definition.v1"),
        ("receiver-foundations.json", "structural service, common finite-age future, restrained contrast and subsequent passage", "model-free-matrix-definition.v1"),
        ("receiver-response.json", "bounded fresh signed H64 response and shifted resolvent transport with original SCI02-C ports", "model-free-matrix-definition.v1"),
        ("receiver-benchmark.json", "complete signed H64 finite frame for equal-precision cost and error comparisons", "model-free-matrix-definition.v1"),
        ("receiver-audit.json", "disjoint development audit of the signed finite-frame mean after the complete benchmark", "model-free-matrix-definition.v1"),
        ("relation-benchmark.json", "optional learned comparator owned by the classical-series workflow", "classical-series-definition.v1"),
        ("programme-index.json", "documentary definition inventory; not an execution engine", "matrix-model-free-programme-index.v1"),
        ("gap-coverage.json", "implementation mapping and outstanding empirical closure evidence", "matrix-model-free-gap-coverage.v1"),
        ("historical-operands.json", "documentary historical inventory; no native operand authentication", "matrix-model-free-historical-inventory.v1"))),
    input_availability="Select the definition and explicit workspace. Bind the original SCI02-C instrument for the signed receiver. Reanalysis, confirmation and sparse audits require their authenticated parents.",
    scientific_ceiling="Numerical development; each result retains its exact physical and statistical scope. Molecular qualification NOT_ESTABLISHED.",
    first_missing_prerequisite="Current committed source, locked base environment and an explicit writable workspace.",
    guide="docs/v1.0/model-free-matrix-programme.md", verification_owners=("tests/test_model_free_workflow.py",)),
    "Direct and certified suppliers with explicit statistical and physical prerequisites", catalogue_order=50)

EXTENSION = ExtensionDeclaration(extension_id=NAMESPACE, version="1.0.0", operations=_OPERATIONS, profiles=(_PROFILE,),
    protocols=(ExperimentProtocolDeclaration(PROTOCOL_ID, Specification, experiment.prepare, NAMESPACE + "-experiment",
        maximum_config_bytes=None, input_record_types=(Product,), bind_inputs=experiment.bind_inputs,
        validate_instance=experiment.validate_instance, input_storage_codecs=(MATRIX_FRAMED_CODEC,)),), workflows=(_WORKFLOW,),
    environments=(EnvironmentDeclaration(route_id=NAMESPACE, python_version="3.11.14",
        distribution_versions=(("numpy", "2.4.6"), ("scipy", "1.17.1")), lock_path="uv.lock",
        python_implementation="CPython", descriptor_version="1.0.0", dependency_groups=(), supported_platforms=(("Linux", "x86_64"),)),),
    installations=(WorkflowInstallationDeclaration(workflow_id="model-free-matrix-programme", profile_id="standard",
        adapter_module="empirical_lawhood.domains.matrix.model_free", adapter_version="1.0.0", controller_environment=NAMESPACE,
        workers=(), external_software=(), source_prerequisites=("Select the source-bound scientific definition and explicit workspace.",),
        continuing_source_prerequisites=(), descriptor_version="1.0.0"),))
