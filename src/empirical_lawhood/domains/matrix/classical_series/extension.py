# SPDX-License-Identifier: MPL-2.0
"""One authoritative declaration for the complete classical matrix series."""
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
from .records import Acquisition, Calibration, NAMESPACE, PROTOCOL_ID, SeriesSpecification

_OPERATIONS = operation_declarations()
_PROFILE = ExtensionProfileRegistration("profile-registration." + NAMESPACE + ".workflow", NAMESPACE + ".workflow",
    "1.0.0", ExtensionProfileKind.OBJECTIVE_TERMINAL, ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(operation.manifest().fingerprint() for operation in _OPERATIONS))).hexdigest())
_WORKFLOW = WorkflowDeclaration(Workflow(
    workflow_id="classical-matrix-series", title="Consolidated classical matrix dynamics series",
    kind="authored native matrix development and retained reanalysis", substrates=("six 4x4 Hermitian matrices; classical BAOAB",),
    methods=("frozen forecast/calibration supply", "paired signed response contrasts", "preparation and transfer alternatives", "joint response calculus"),
    environment="base",
    operations=tuple(WorkflowOperation("campaign experiment-" + name, boundary, ()) for name, boundary in (
        ("explain", "describe the authored choices and complete TRAIN/CAL/CONF root census"),
        ("prepare", "derive recursive dependencies and authenticate retained reanalysis inputs"),
        ("author", "freeze source and numerical settings before any new roots"),
        ("run", "acquire TRAIN/CAL, freeze their supplier, then acquire and assess CONF"),
        ("read", "read actual retained findings and every failed or unavailable root without recalculation"),
        ("recover", "resume unfinished work through the ordinary shared owner"))),
    inputs=tuple(WorkflowInput("programmes/foundations/emergent-structure/workflows/classical-series/" + filename,
        role, "classical-series-definition.v1") for filename, role in (("experiment.json", "complete scientific definition"),
        ("smoke.json", "explicitly small software and native control"))), input_availability="Choose experiment.json or the explicitly smaller smoke.json; reanalysis selects original retained products.",
    scientific_ceiling="Numerical development only; historical results retain their original identity and qualification remains NOT_ESTABLISHED.",
    first_missing_prerequisite="Select an authored definition, current source, locked base environment and a fresh explicit workspace.",
    guide="docs/v1.0/classical-matrix-series.md", verification_owners=("tests/test_classical_series_workflow.py",)),
    "Authored development, frozen TRAIN/CAL supplier, complete CONF census and retained reanalysis", catalogue_order=49)

EXTENSION = ExtensionDeclaration(extension_id=NAMESPACE, version="1.0.0", operations=_OPERATIONS, profiles=(_PROFILE,),
    protocols=(ExperimentProtocolDeclaration(PROTOCOL_ID, SeriesSpecification, experiment.prepare,
        NAMESPACE + "-experiment", maximum_config_bytes=None, input_record_types=(Acquisition, Calibration),
        bind_inputs=experiment.bind_inputs, validate_instance=experiment.validate_instance, input_storage_codecs=(MATRIX_FRAMED_CODEC,)),), workflows=(_WORKFLOW,),
    environments=(EnvironmentDeclaration(route_id=NAMESPACE, python_version="3.11.14", distribution_versions=(("numpy", "2.4.6"), ("scipy", "1.17.1")),
        lock_path="uv.lock", python_implementation="CPython", descriptor_version="1.0.0", dependency_groups=(),
        supported_platforms=(("Linux", "x86_64"),)),),
    installations=(WorkflowInstallationDeclaration(workflow_id="classical-matrix-series", profile_id="standard",
        adapter_module="empirical_lawhood.domains.matrix.classical_series", adapter_version="1.0.0",
        controller_environment=NAMESPACE, workers=(), external_software=(),
        source_prerequisites=("Select the authored native matrix definition and an explicit workspace.",),
        continuing_source_prerequisites=(), descriptor_version="1.0.0"),))

__all__ = ["EXTENSION"]
