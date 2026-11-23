# SPDX-License-Identifier: MPL-2.0
"""The scientific and public registration for matched waveform preparation."""

from hashlib import sha256
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.domains.matrix.finite_response_law.authoring.rerun_input import (
    FiniteResponseLawCurrentExposure,
)
from empirical_lawhood.domains.matrix.finite_response_law.original_f import (
    OriginalFiniteResponseLaw,
)
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_FRAMED_CODEC
from empirical_lawhood.domains.matrix.preparation_reuse_manifests import (
    MANIFEST_FORMAT,
    MANIFEST_SCHEMA,
    RELEASE_MANIFESTS,
    WORKFLOW as GUIDE_DIRECTORY,
)
from empirical_lawhood.domains.matrix.preparation_applicability.waveform_evaluation import (
    WaveformCohort,
)
from empirical_lawhood.execution.experiment_preparation import (
    ExperimentProtocolDeclaration,
)
from empirical_lawhood.execution.discovery_descriptors import EnvironmentDeclaration
from empirical_lawhood.execution.installation_descriptors import (
    WorkflowInstallationDeclaration,
)
from empirical_lawhood.execution.extension_bundles import (
    ExtensionProfileKind,
    ExtensionProfileRegistration,
)
from empirical_lawhood.execution.extensions import ExtensionDeclaration
from empirical_lawhood.execution.workflow_descriptors import (
    RetainedManifestInput,
    Workflow,
    WorkflowDeclaration,
    WorkflowOperation,
)
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from . import experiment
from .bindings import declarations
from .records import NAMESPACE, PROTOCOL_ID, WaveformSpecification

OPERATIONS = declarations()
PROFILE = ExtensionProfileRegistration(
    "profile-registration." + NAMESPACE + ".workflow",
    NAMESPACE + ".workflow",
    "1.0.0",
    ExtensionProfileKind.OBJECTIVE_TERMINAL,
    ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(
        canonical_json_bytes(tuple(r.manifest().fingerprint() for r in OPERATIONS))
    ).hexdigest(),
)
WORKFLOW = WorkflowDeclaration(
    Workflow(
        workflow_id=NAMESPACE,
        title="Fixed-law preparation on new bath waveforms",
        kind="paired numerical population experiment",
        substrates=("six driven Hermitian matrices",),
        methods=(
            "fixed-law response",
            "matched preparation",
            "pre-handoff ridge forecast",
            "whole-waveform inference",
        ),
        environment="base",
        operations=tuple(
            WorkflowOperation("campaign experiment-" + name, purpose, ())
            for name, purpose in (
                (
                    "prepare",
                    "verify the selected law, producer, exposure and independent roots",
                ),
                ("author", "freeze the split and every causal predecessor"),
                ("run", "measure and assess the complete assigned cohort"),
                ("read", "read retained root and population findings"),
                ("recover", "resume the authored graph from its receipts"),
            )
        ),
        inputs=tuple(
            RetainedManifestInput(
                (GUIDE_DIRECTORY / "operands" / f"{study}.json").as_posix(),
                f"Released {study.upper()} operand manifest for offline reproduction",
                MANIFEST_SCHEMA, MANIFEST_FORMAT, digest,
            )
            for study, digest in RELEASE_MANIFESTS.items()
        ),
        input_availability="The guide supplies R23–R27 replay operands. Fresh waveform work requires the original F export, exposure census and allocation.",
        scientific_ceiling="Paired service, risk and forecast losses on this finite numerical population.",
        first_missing_prerequisite="Confirmation requires a complete passing 32-waveform development screen.",
        guide=(GUIDE_DIRECTORY / "guide.md").as_posix(),
        verification_owners=("tests/test_matrix_waveform_preparation.py", "tests/test_preparation_reuse_reproduction.py"),
    ),
    "R25 waveform experiment and R23–R27 reproduction guide",
    catalogue_order=61,
)
EXTENSION = ExtensionDeclaration(
    extension_id=NAMESPACE,
    version="1.0.0",
    operations=OPERATIONS,
    profiles=(PROFILE,),
    protocols=(
        ExperimentProtocolDeclaration(
            PROTOCOL_ID,
            WaveformSpecification,
            experiment.prepare,
            NAMESPACE + "-experiment",
            maximum_config_bytes=None,
            input_record_types=(
                OriginalFiniteResponseLaw,
                FiniteResponseLawCurrentExposure,
                WaveformCohort,
            ),
            bind_inputs=experiment.bind_inputs,
            validate_instance=experiment.validate_instance,
            input_storage_codecs=(MATRIX_FRAMED_CODEC,),
        ),
    ),
    workflows=(WORKFLOW,),
    environments=(
        EnvironmentDeclaration(
            route_id=NAMESPACE,
            python_version="3.11.14",
            distribution_versions=(("numpy", "2.4.6"), ("scipy", "1.17.1")),
            lock_path="uv.lock",
            python_implementation="CPython",
            descriptor_version="1.0.0",
            dependency_groups=(),
            supported_platforms=(("Linux", "x86_64"),),
        ),
    ),
    installations=(
        WorkflowInstallationDeclaration(
            workflow_id=NAMESPACE,
            profile_id="standard",
            adapter_module="empirical_lawhood.domains.matrix.waveform_preparation",
            adapter_version="1.0.0",
            controller_environment=NAMESPACE,
            workers=(),
            external_software=(),
            source_prerequisites=(
                "Select verified original-law files and the complete known prior-exposure census.",
            ),
            continuing_source_prerequisites=(),
            descriptor_version="1.0.0",
        ),
    ),
)
