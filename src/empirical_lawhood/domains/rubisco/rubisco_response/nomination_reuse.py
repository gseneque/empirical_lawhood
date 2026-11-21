# SPDX-License-Identifier: MPL-2.0
"""Read a retained nomination and its receipt into distinct current case selections.

This verifies declared original bytes and sequence correspondence. It never
replays the historical producer or changes the original evidence ceiling.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_nomination_preparation.contracts import NominationDossier, SOURCE_CENSUS
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import WilsonMutantRowV1
from empirical_lawhood.science.records.decoding import decode_canonical_record
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt

from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoCaseSet, exact, homogeneous_material, paired_case


@dataclass(frozen=True, slots=True)
class NominationReuseAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/nomination-reuse-assessment"
    assessment_id: str
    dossier: ObjectIdentity
    receipt: ObjectIdentity
    cases: RubiscoCaseSet
    source_member_sha256s: tuple[tuple[str, str], ...]
    disposition: AssessmentDisposition = AssessmentDisposition.SATISFIED
    evidence_scope: str = "CURRENT_SEQUENCE_USE_ORIGINAL_EXPOSURE_AND_RECEIPT_RETAINED"
    assembly_and_kinetic_admission: str = "NOT_ESTABLISHED"

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        for value, schema, version in (
            (self.dossier, NominationDossier.SCHEMA, NominationDossier.VERSION),
            (self.receipt, CanonicalTaskReceipt.SCHEMA, CanonicalTaskReceipt.VERSION),
        ):
            exact(value, ObjectIdentity)
            if value.object_schema != schema or value.object_version != version:
                raise ValueError("nomination reuse substitutes its original typed ancestry")
        exact(self.cases, RubiscoCaseSet)
        if (self.cases.sources != tuple(sorted((self.dossier, self.receipt), key=lambda row: row.object_id))
                or type(self.source_member_sha256s) is not tuple
                or any(type(row) is not tuple or len(row) != 2 for row in self.source_member_sha256s)
                or tuple(name for name, _ in self.source_member_sha256s)
                != tuple(sorted(name for _, name in SOURCE_CENSUS))):
            raise ValueError("nomination reuse loses complete original source/receipt membership")
        for _, digest in self.source_member_sha256s:
            validate_sha256(digest)
        if (self.disposition is not AssessmentDisposition.SATISFIED
                or self.evidence_scope != "CURRENT_SEQUENCE_USE_ORIGINAL_EXPOSURE_AND_RECEIPT_RETAINED"
                or self.assembly_and_kinetic_admission != "NOT_ESTABLISHED"):
            raise ValueError("sequence reuse cannot admit assembly or biological kinetics")


def _source(dossier, name):
    selected = tuple(row for row in dossier.preparation.source_members if row.filename == name)
    if len(selected) != 1:
        raise ValueError("nomination omits its exact selected source member")
    selected[0].__post_init__()
    return json.loads(selected[0].raw_utf8)


def _protein(document, name):
    record = document["proteins"][name]
    sequence = record["sequence"]
    if record["length"] != len(sequence) or record["sha256_ascii"] != sha256(sequence.encode("ascii")).hexdigest():
        raise ValueError("nomination changes the complete source protein bytes")
    return sequence


def nomination_donor_rows(dossier):
    """Decode the original matched donor operands; never use the proposed Gp transfer."""
    exact(dossier, NominationDossier)
    donor = _source(dossier, "donor-contrast-authentication.json")
    before, after = (decode_canonical_record(donor[key], WilsonMutantRowV1) for key in ("before", "after"))
    if (before.native_rbcl_edits != "P415A" or after.native_rbcl_edits != "P415A"
            or before.native_rbcs_edits != "None" or after.native_rbcs_edits != "V98M"):
        raise ValueError("donor SSU effect requires the same Te-P415A LSU background")
    return before, after


def derive_nomination_cases(dossier, *, sources):
    """Derive Gp M1/V1, no-change and matched Te-P415A cases from original bytes."""
    exact(dossier, NominationDossier)
    construct = _source(dossier, "construct-options.json")
    if (construct["stoichiometry"] != {"LSU": 8, "SSU": 8}
            or construct["numbering"] != "linear I95M in BOTH full138-aa M1/V1; 1BWV author I112"
            or construct["lsu_sequence"] != dossier.preparation.lsu_sequence
            or construct["proposed_material_id"] != dossier.preparation.proposed_material_id):
        raise ValueError("nomination changes full assembly, I95/author-I112 or original material")
    cases = []
    for view in ("m1", "v1"):
        lsu = _protein(construct, "gp.lsu")
        wt, mutant = (_protein(construct, f"gp.ssu.{kind}.{view}") for kind in ("wt", "i95m"))
        if (len(lsu) != 493 or len(wt) != 138 or len(mutant) != 138
                or wt[94] != "I" or mutant != wt[:94] + "M" + wt[95:]
                or wt[0] != {"m1": "M", "v1": "V"}[view]):
            raise ValueError("nomination changes the source-defined Gp intervention or processing view")
        parent = homogeneous_material(material_id=f"material.gp-wt.{view}.tag-free.v2",
            organism="Galdieria partita", processing_view=view, lsu=lsu, ssu=wt, sources=sources)
        child = homogeneous_material(material_id=f"material.gp-i95m.{view}.tag-free.v2",
            organism="Galdieria partita", processing_view=view, lsu=lsu, ssu=mutant, sources=sources)
        cases.append(paired_case(case_id=f"case.gp-i95m.{view}", parent=parent, mutant=child,
            case_role="CANDIDATE", exposure_group="exposure.gp-i95m-development", sources=sources))
        cases.append(paired_case(case_id=f"case.gp-no-change.{view}", parent=parent, mutant=parent,
            case_role="NO_CHANGE", exposure_group="exposure.gp-i95m-development", sources=sources))
    before, after = nomination_donor_rows(dossier)
    donor_materials = []
    for row in (before, after):
        protein = row.te_protein_specification
        if protein is None:
            raise ValueError("donor lacks its original complete protein specification")
        donor_materials.append(homogeneous_material(material_id="material." + row.sample_id,
            organism="Thermosynechococcus elongatus", processing_view="reported",
            lsu=protein.large_subunit_sequence, ssu=protein.small_subunit_sequence, sources=sources))
    donor_case = paired_case(case_id="case.te-p415a-ssu-v98m", parent=donor_materials[0], mutant=donor_materials[1],
        case_role="DONOR", exposure_group="exposure.wilson2017-development", sources=sources)
    if (len(donor_case.substitutions) != 8 or any(
            row.position_1based != 98 or row.before != "V" or row.after != "M"
            or not row.chain_id.startswith("ssu.") for row in donor_case.substitutions)):
        raise ValueError("donor contrast changes more than the eight matched SSU V98M substitutions")
    cases.append(donor_case)
    return RubiscoCaseSet("selection.rubisco-response.nomination." + dossier.fingerprint(),
        tuple(sorted(cases, key=lambda row: row.case_id)), sources)


def assess_retained_nomination(dossier, receipt, *, assessment_id):
    """Use current typed readers; original receipt remains the producing custody."""
    exact(dossier, NominationDossier)
    exact(receipt, CanonicalTaskReceipt)
    outputs = tuple(row for row in receipt.output_logical_artifacts
                    if row.payload_schema == dossier.SCHEMA and row.content_sha256 == dossier.fingerprint())
    if (receipt.operational_status is not OperationalStatus.SUCCEEDED or len(outputs) != 1
            or receipt.task_id != "rubisco-nomination-preparation.prepare"
            or len(receipt.output_logical_artifacts) != 1):
        raise ValueError("retained nomination lacks its exact successful original producer receipt")
    logical = outputs[0]
    materializations = tuple(row for row in receipt.output_materializations
                             if row.logical_artifact_id == logical.logical_artifact_id)
    if (len(materializations) != 1 or materializations[0].physical_sha256 != dossier.fingerprint()
            or materializations[0].size_bytes != len(dossier.canonical_bytes())
            or materializations[0].compression != "none"):
        raise ValueError("retained nomination receipt does not bind the complete original canonical bytes")
    dossier_identity = ObjectIdentity.from_record(dossier.product_id, dossier)
    receipt_identity = ObjectIdentity.from_record(receipt.receipt_id, receipt)
    sources = tuple(sorted((dossier_identity, receipt_identity), key=lambda row: row.object_id))
    cases = derive_nomination_cases(dossier, sources=sources)
    members = tuple(sorted((row.filename, row.source_sha256) for row in dossier.preparation.source_members))
    return NominationReuseAssessment(assessment_id, dossier_identity, receipt_identity, cases, members)
