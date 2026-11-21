# SPDX-License-Identifier: MPL-2.0
"""Authenticate matched Amber endpoints and export their MolProbity projections."""

from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_projection import project_material
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_molecular import UnmappableDiagnosticEndpoint, map_initial_amber_diagnostic
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import MODEL_NAMES
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import read_initial_amber_files
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.status import OperationalStatus


def export_models(source, original, scaffolds, native, directory):
    if original.source != source.identity or tuple(m.name for m in source.models) != MODEL_NAMES:
        raise ValueError("Independent structural validation requires the original complete matched construction")
    units = {u.returned.model: u for u in original.units}
    if set(units) != {m.identity for m in source.models} or len(scaffolds) != len(MODEL_NAMES):
        raise ValueError("Construction result substitutes or omits a material in the matched roster")
    rows = []
    for model, scaffold in zip(source.models, scaffolds, strict=True):
        unit = units[model.identity]
        observed = native.recover(unit.definition)
        if (observed is None or observed.completion != unit.completion or observed.receipt != unit.receipt
                or unit.definition.configuration != model.identity or source.identity not in unit.definition.sources
                or b"".join(native.iter_completed_output(unit.definition, "build.return")) != unit.returned.canonical_bytes()):
            raise ValueError("Original model, native return, completion or task receipt changed")
        if scaffold.identity != model.scaffold:
            raise ValueError("Independent structural validation substitutes a matched scaffold")
        row = dict(name=model.name, model=model.identity.to_document(), scaffold=scaffold.identity.to_document(),
                   material=model.material.identity.to_document(), definition=unit.definition.identity.to_document(),
                   completion_sha256=unit.completion.fingerprint(), receipt_sha256=unit.receipt.fingerprint(),
                   assessment_sha256=unit.assessment.fingerprint() if unit.assessment else None,
                   construction_disposition=unit.assessment.construction_disposition.value if unit.assessment else None,
                   construction_findings=list(unit.assessment.findings) if unit.assessment else None,
                   validated_material_eligible=bool(unit.assessment and unit.assessment.construction_disposition is AssessmentDisposition.SATISFIED))
        rows.append(row)
        if (unit.completion.operational_status != OperationalStatus.SUCCEEDED or unit.returned.return_code != 0
                or unit.returned.error or unit.returned.timed_out or unit.assessment_error or not unit.assessment):
            row.update(status="CONSTRUCTION_UNAVAILABLE", operational_status=unit.completion.operational_status.value,
                       assessment_error=unit.assessment_error, native_error=unit.returned.error,
                       construction_disposition=unit.assessment.construction_disposition.value if unit.assessment else None)
            continue
        files = read_initial_amber_files(native, unit.definition, unit.returned, maximum_bytes=source.maximum_model_output_bytes)
        try:
            mapped = map_initial_amber_diagnostic(source=source, model=model, scaffold=scaffold, unit=unit, files=files)
        except UnmappableDiagnosticEndpoint as error:
            row.update(status="CONSTRUCTION_UNAVAILABLE", diagnostic_mapping_error=str(error))
            continue
        rep = mapped["representation"]
        dest = directory / model.name
        dest.mkdir()
        row.update(status="EXPORTED", topology=rep.raw_topology.to_document(), relaxed_restart=rep.raw_coordinates.to_document(),
                   chemical_graph=mapped["chemical_graph"].identity.to_document(), **project_material(mapped, dest))
        del mapped, files, rep
    return dict(schema="el-molprobity-export-1", roster="MATCHED_ACTIVE_CHILDREN", source=source.identity.to_document(),
                construction_sha256=original.fingerprint(), models=rows, independent_biological_units=0)
