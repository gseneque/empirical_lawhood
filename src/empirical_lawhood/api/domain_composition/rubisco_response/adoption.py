# SPDX-License-Identifier: MPL-2.0
"""Authenticate original portable custody before deriving current-use authoring."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.domains.rubisco.rubisco_response.adoption import CAPABILITY, ResponseAdoptionConfig
from empirical_lawhood.domains.rubisco.rubisco_response.adoption_translation import response_adoption_draft, response_adoption_origins
from empirical_lawhood.domains.rubisco.rubisco_response.experiment_specification import RubiscoResponseExperimentSpecification, select_response_study
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.operation_bindings import MAX_INPUT_BYTES
from empirical_lawhood.domains.rubisco.rubisco_response.recursive_translation import selected_configs
from empirical_lawhood.domains.rubisco.rubisco_response.study import RubiscoResponseStudy
from empirical_lawhood.domains.rubisco.rubisco_response.study_science import ResponseAssessment, ResponsePredictions
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.design.recursive_authoring import RecursiveStudyDraft
from empirical_lawhood.design.recursive_input_origins import RecursiveInputOrigins
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, load_authored_wave
from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution


@dataclass(frozen=True, slots=True)
class PreparedResponseAdoption:
    draft: RecursiveStudyDraft
    origins: RecursiveInputOrigins
    parent_directory: Path


def prepare_response_adoption(*, parent_directory, specification, artifact_writer):
    """Read exact original custody and derive a distinct criterion-bound use.

    The current source/custody guards run again at authoring and execution.
    This pure read supplies no execution authority or fresh observations.
    """
    exact(specification, RubiscoResponseExperimentSpecification)
    if specification.evidence_scope != "EXPOSED_CONDITIONAL":
        raise ValueError("retained exposed predictions require the separate exposed current-use lane")
    selected, transport, manifest, _, products, view = authenticate_recursive_contribution(
        directory=parent_directory, artifact_writer=artifact_writer)
    _, parent_draft, _, payloads = load_authored_wave(
        directory=selected / "custody" / transport.authoring_relative_path, artifact_writer=view, lazy_payloads=True)
    original_config = selected_configs(parent_draft)["assess"]
    external, = parent_draft.external_inputs
    filename = "external-" + sha256(external.input_id.encode()).hexdigest()[:24] + ".json"
    original = decode_canonical_bytes(payloads[filename], RubiscoResponseStudy, maximum_bytes=MAX_INPUT_BYTES)
    if original.identity != original_config.original_study:
        raise ValueError("retained response parent substitutes its exact immutable original study")
    current = select_response_study(specification, original)
    selected_products = {}
    for name, kind in (("prediction", ResponsePredictions), ("assessment", ResponseAssessment)):
        matches = tuple(row for row in manifest.products if row.record.object_schema == kind.SCHEMA)
        if len(matches) != 1:
            raise ValueError("retained response parent omits or duplicates an original product")
        product, = matches
        records = tuple(record for task in products["records"].values() for record in task.values()
                        if type(record) is kind and record.fingerprint() == product.record.object_fingerprint)
        if len(records) != 1:
            raise ValueError("retained response parent lacks its exact authenticated original bytes")
        selected_products[name] = product
    config = ResponseAdoptionConfig("config." + CAPABILITY, original_config.science, current, manifest,
        selected_products["prediction"], selected_products["assessment"], original_config.permitted_refinement_id,
        specification.permitted_refinement_id)
    draft = response_adoption_draft(config)
    return PreparedResponseAdoption(draft, response_adoption_origins(draft), selected)


def author_response_adoption(*, parent_directory, specification, project_root, artifact_writer, output_dir):
    """Use the supported portable-parent author; never execute or replay here."""
    prepared = prepare_response_adoption(parent_directory=parent_directory, specification=specification,
                                         artifact_writer=artifact_writer)
    return author_recursive_wave(draft=prepared.draft, origins=prepared.origins,
        contribution_dir=prepared.parent_directory, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir)
