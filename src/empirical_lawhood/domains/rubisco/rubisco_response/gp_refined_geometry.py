# SPDX-License-Identifier: MPL-2.0
"""A successful source-bound parent repair retains its own native provenance."""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair import GEOMETRY_ID, REPAIR_INPUT_TYPES, GpAmberFragmentRepairInput, GpCarboxylateRepairInput, GpGeometryRepairInput
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import GpAmberFragmentRepairAssessment, GpCarboxylateRepairAssessment
from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_operation import GpGeometryRepairResult
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


def require_repaired_endpoint(source, result):
    """Require the source-bound, independently assessed actual repair result."""
    if type(source) not in REPAIR_INPUT_TYPES:
        raise ValueError("refined geometry requires its original selected parent input")
    exact(result,GpGeometryRepairResult)
    assessment=result.assessment
    if (result.returned.source!=source.identity or result.definition.configuration!=source.identity
            or result.returned.error is not None or result.assessment_error is not None
            or assessment is None or assessment.repair_disposition is not A.SATISFIED):
        raise ValueError("refined geometry requires a successful independently assessed original repair")
    refined_kind = GpAmberFragmentRepairAssessment if type(source) is GpAmberFragmentRepairInput else GpCarboxylateRepairAssessment
    if (isinstance(source, GpCarboxylateRepairInput)
            and (type(assessment) is not refined_kind
                 or assessment.largest_refined_displacement_angstrom > source.maximum_refined_displacement_angstrom)):
        raise ValueError("refined geometry changes the selected inherited-coordinate displacement limit")
    if (assessment.findings or assessment.short_heavy_contacts or assessment.gross_backbone_anomalies
            or assessment.stereo_anomalies or assessment.peptide_anomalies
            or assessment.maximum_mobile_gradient_kj_mol_nm>source.maximum_gradient_kj_mol_nm
            or assessment.maximum_mobile_bond_error_angstrom>source.maximum_mobile_bond_error_angstrom
            or assessment.minimum_mobile_nonbonded_heavy_distance_angstrom<source.minimum_mobile_nonbonded_heavy_distance_angstrom
            or (assessment.heavy_atoms,assessment.fixed_heavy_atoms+assessment.refined_heavy_count,assessment.constructed_heavy_atoms)
                !=(source.parent_assessment.atom_count,source.parent_assessment.inherited_atom_count,
                   source.parent_assessment.constructed_atom_count)):
        raise ValueError("refined geometry changes the actual force/geometry acceptance or atom denominator")


@dataclass(frozen=True, slots=True)
class GpRefinedGeometrySupply(CanonicalRecord):
    SCHEMA: ClassVar[str]="empirical-lawhood/rubisco-response/gp-refined-geometry-supply"
    supply_id: str
    source: GpGeometryRepairInput | GpCarboxylateRepairInput | GpAmberFragmentRepairInput
    result: GpGeometryRepairResult
    integrity: PreAmberGeometryIntegrity

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        require_repaired_endpoint(self.source,self.result)
        exact(self.integrity,PreAmberGeometryIntegrity)
        old=self.source.parent_assessment
        actual=self.integrity
        files={row.relative_path:row for row in self.result.returned.files.files}
        if any(PurePosixPath(path).parts!=(GEOMETRY_ID,PurePosixPath(path).name) for path in files):
            raise ValueError("refined geometry loses its actual raw unit scope")
        if (actual.source!=old.source or actual.construct!=old.construct or actual.joint_view_id!=old.joint_view_id
                or actual.geometry_definition!=self.result.definition.identity
                or actual.geometry_completion!=ObjectIdentity.from_record(self.result.receipt.task_id+".completion",self.result.completion)
                or actual.geometry_receipt!=self.geometry_receipt
                or actual.heavy_file!=files.get(GEOMETRY_ID+"/complete-heavy.pdb")
                or actual.origin_file!=files.get(GEOMETRY_ID+"/atom-origin-provenance.json")
                or actual.origin_file!=old.origin_file
                or any(getattr(actual,name)!=getattr(old,name) for name in (
                    "atom_count","protein_residue_count","residue_count","inherited_atom_count",
                    "constructed_atom_count","ter_count","conect_row_count","directed_conect_term_count",
                    "source_disulfide_count"))):
            raise ValueError("refined geometry substitutes its source/origin assessment or original native receipt")

    @property
    def identity(self):return ObjectIdentity.from_record(self.supply_id,self)

    @property
    def independent_integrity(self):
        return ObjectIdentity.from_record(self.integrity.product_id,self.integrity)

    @property
    def geometry_receipt(self):
        return ObjectIdentity.from_record(self.result.receipt.receipt_id,self.result.receipt)
