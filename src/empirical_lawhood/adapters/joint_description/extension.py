# SPDX-License-Identifier: MPL-2.0
"""Single authoritative declaration of the new R01--R22 recursive experiment."""
from hashlib import sha256
from empirical_lawhood.design.joint_description import PROTOCOL_ID,JointSpecification,SelectedInputs
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.joint_description import MAX_BYTES
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.execution.extensions import ExtensionDeclaration
from empirical_lawhood.execution.extension_bundles import ExtensionProfileKind,ExtensionProfileRegistration
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration,ExperimentProtocolDeclaration
from empirical_lawhood.execution.workflow_descriptors import Workflow,WorkflowDeclaration,WorkflowOperation
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import WorkflowInstallationDeclaration,WorkerEnvironment
from empirical_lawhood.execution.remote.worker_profiles import JAX_TORAX_WORKER
from . import experiment
from .bindings import operation_declarations

_OPERATIONS=operation_declarations()
_PROFILE=ExtensionProfileRegistration("profile-registration.joint-description.workflow","joint-description.workflow",
    "1.0.0",ExtensionProfileKind.OBJECTIVE_TERMINAL,ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(o.manifest().fingerprint() for o in _OPERATIONS))).hexdigest())
_WORKFLOW=WorkflowDeclaration(Workflow(workflow_id="joint-description-experiments",
    title="New R01--R22 finite joint-description experiments",kind="declarative recursive development experiment",
    substrates=("circuits","six-matrix dynamics","recorded physical cohorts","PyBaMM","TORAX","reactor"),
    methods=("calibration-root crossfit","causal forecast and action selection","finite-menu economic and dependence audit"),environment="base",
    operations=tuple(WorkflowOperation("campaign experiment-"+name,meaning,()) for name,meaning in (
        ("prepare","resolve the authored finite scientific menu and copied exact inputs"),
        ("author","compile six causal stages and nine assessed supplier requirements"),
        ("run","execute declared native and pure operations through shared custody"),
        ("read","read retained scientific results without recalculation"),
        ("recover","recover completed native roots without repeating uncertain work"))),
    inputs=(),input_availability="All22 editable new recipes; physical families additionally require explicitly supplied raw cohorts.",
    scientific_ceiling="Held-out development within a finite authored menu; no universal minimality or physical prospective-control claim.",
    first_missing_prerequisite="Select a new recipe, raw cohorts where applicable, locked native environment and explicit storage.",
    guide="docs/v1.0/joint-description-experiments.md",verification_owners=("tests/test_joint_description_contracts.py","tests/test_joint_description_controls.py")),
    "Editable recursive studies with family-specific inputs, environments and retained assessments",catalogue_order=60)

EXTENSION=ExtensionDeclaration(extension_id="joint-description",version="1.0.0",operations=_OPERATIONS,profiles=(_PROFILE,),
    protocols=(ExperimentProtocolDeclaration(PROTOCOL_ID,JointSpecification,experiment.prepare,"joint-description-experiment",
        maximum_config_bytes=MAX_BYTES,input_record_types=(SelectedInputs,NumericalProducingProvenance),
        bind_inputs=experiment.bind_inputs,validate_instance=experiment.validate_instance,
        configuration_inputs=(ExperimentInputConfigurationDeclaration("joint-description-selected",SelectedInputs,MAX_BYTES),)),),
    workflows=(_WORKFLOW,),
    environments=(EnvironmentDeclaration("joint-description-torax-gpu","3.11.14",
        tuple((name,version) for name,version in JAX_TORAX_WORKER.required_versions if version is not None),
        dependency_groups=("open-simulators","open-simulators-gpu")),),
    installations=tuple(WorkflowInstallationDeclaration("joint-description-experiments",profile,
        "empirical_lawhood.adapters.joint_description","1.0.0",environment,
        workers=(WorkerEnvironment("acquisition",environment),),
        source_prerequisites=(scope,"Select a new recipe, exact clean source, explicit storage and authentic raw cohort where required."))
        for profile,environment,scope in (
            ("standard","base","CPU analytical, matrix, recorded-cohort and packaged reactor families; no external native engine."),
            ("battery-cpu","battery-recursion","R18/R19 require the exact pinned PyBaMM worker."),
            ("torax-cpu","open-simulators","R17/R22 require the exact pinned CPU JAX/TORAX worker."),
            ("torax-gpu","joint-description-torax-gpu","R17/R22 require the exact pinned CUDA12 JAX/TORAX worker and actual GPU acceptance."))))

__all__=["EXTENSION"]
