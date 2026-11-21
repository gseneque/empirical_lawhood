# SPDX-License-Identifier: MPL-2.0
"""Independent retained geometry/force checks for selected molecular endpoints."""

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
import math
import struct
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.physical_preparation_geometry import GeometryDiagnostic, read_inpcrd
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.serialized_coordinate_assessment import GEOMETRY_METHOD, diagnose_geometry_supported_inactive14
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledNumericalIntegrity, assess_native_return
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_decimal, validate_relative_locator, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_atoms import MolecularRepresentation, validate_amber_atom_correspondence
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_chemistry import validate_ligand_correspondence
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_native import MolecularForceProbe, MolecularProbeOutcome


@dataclass(frozen=True, slots=True)
class RetainedMolecularGeometry(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/retained-molecular-geometry"
    input_id: str
    representation: ObjectIdentity
    topology: FileEvidence
    coordinates: FileEvidence
    heavy_atoms: FileEvidence
    origins: FileEvidence

    def __post_init__(self):
        validate_stable_id(self.input_id)
        exact(self.representation, ObjectIdentity)
        files = (self.topology, self.coordinates, self.heavy_atoms, self.origins)
        for row in files:
            exact(row, FileEvidence)
            validate_relative_locator(row.relative_path)
            if type(row.byte_count) is not int or row.byte_count <= 0:
                raise ValueError("retained geometry needs actual positive byte counts")
        if len({row.relative_path for row in files}) != 4:
            raise ValueError("retained geometry aliases distinct raw scientific operands")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.input_id, self)


@dataclass(frozen=True, slots=True)
class MolecularPreparationCriteria(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-preparation-criteria"
    criteria_id: str
    maximum_positive_lj_pair_kcal_mol: Decimal
    maximum_gradient_component_eh_per_ash_bohr: Decimal
    criterion_source: ObjectIdentity
    unresolved_requirement_ids: tuple[str, ...]
    interpretation: str = "SELECTED_NUMERICAL_LIMITS_NOT_SCIENTIFIC_CALIBRATION"

    def __post_init__(self):
        validate_stable_id(self.criteria_id)
        for name in ("maximum_positive_lj_pair_kcal_mol", "maximum_gradient_component_eh_per_ash_bohr"):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0:
                raise ValueError("preparation numerical limits must be explicitly positive")
        exact(self.criterion_source, ObjectIdentity)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids")
        if self.interpretation != "SELECTED_NUMERICAL_LIMITS_NOT_SCIENTIFIC_CALIBRATION":
            raise ValueError("selected preparation limits cannot establish scientific calibration")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.criteria_id, self)


def _raw(evidence, value):
    if type(value) is not bytes or (len(value), sha256(value).hexdigest()) != (evidence.byte_count, evidence.sha256):
        raise ValueError("retained molecular raw bytes differ from the selected complete file custody")
    return value.decode("ascii")


def _json_pairs(rows):
    result = {}
    for key, value in rows:
        if key in result:
            raise ValueError("retained molecular origin repeats a JSON key")
        result[key] = value
    return result


def _json_constant(value):
    raise ValueError("retained molecular origin contains nonfinite JSON: " + value)


def assess_retained_geometry(representation, selected, *, topology, coordinates, heavy_atoms, origins):
    """Recompute complete native parameters and lexical geometry; never a producer.

    Source access and publication authentication are owned by the calling port.
    Exact selected sizes/digests are checked before parsing. The original
    diagnostic retains every logical pair and every original interaction class.
    """
    exact(representation, MolecularRepresentation)
    exact(selected, RetainedMolecularGeometry)
    if (selected.representation != representation.identity
            or selected.topology.sha256 != representation.raw_topology.object_fingerprint
            or selected.coordinates.sha256 != representation.raw_coordinates.object_fingerprint):
        raise ValueError("retained geometry substitutes the actual molecular raw source selection")
    top = _raw(selected.topology, topology)
    xyz = _raw(selected.coordinates, coordinates)
    heavy = _raw(selected.heavy_atoms, heavy_atoms)
    origin = json.loads(_raw(selected.origins, origins), object_pairs_hook=_json_pairs, parse_constant=_json_constant)
    census = validate_amber_atom_correspondence(representation, topology)
    points, _box, _time = read_inpcrd(xyz, len(representation.atoms))
    # Authenticate the shared binary64 coordinate array without making a second
    # full array. Every exact lexical coordinate is projected once in C order.
    digest = sha256()
    for point in points:
        values = tuple(float(value) for value in point)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("retained coordinates cannot supply a finite binary64 array")
        digest.update(struct.pack("<ddd", *values))
    if digest.hexdigest() != representation.arrays.members[0].sha256:
        raise ValueError("retained lexical coordinates differ from the complete selected coordinate array")
    realized = origin.get("amber_realization", {}).get("atoms") if type(origin) is dict else None
    if type(realized) is not list or len(realized) != len(representation.atoms):
        raise ValueError("retained origins omit the full physical atom population")
    residues = {row.residue_id: row for row in representation.residues}
    for atom, row in zip(representation.atoms, realized, strict=True):
        residue = residues[atom.residue_id]
        if type(row) is not dict:
            raise ValueError("retained origin atom is not an exact mapping")
        if residue.author_number is not None and (row.get("chain"), row.get("position")) != (
                residue.author_chain, residue.author_number):
            raise ValueError("retained original author numbering differs from the complete molecular mapping")
    result = diagnose_geometry_supported_inactive14(top, xyz, heavy, origin)
    if result.diagnostic.atom_count != census["term_census"]["atoms"]:
        raise ValueError("independent geometry changes the full parsed atom denominator")
    return result.diagnostic


def _geometry_gate(diagnostic, criteria):
    if diagnostic.hard_geometry_disposition is A.FALSIFIED:
        return A.FALSIFIED
    if diagnostic.maximum_lj_pair is not None and Fraction(*diagnostic.maximum_lj_pair[-1]) > Fraction(criteria.maximum_positive_lj_pair_kcal_mol):
        return A.FALSIFIED
    return A.SATISFIED


def _force_gate(integrity, criteria, outcome):
    if integrity is None:
        return A.UNEVALUABLE
    if integrity.disposition is not A.SATISFIED:
        return integrity.disposition
    if outcome is None or integrity.request != outcome.request.identity:
        raise ValueError("force assessment loses its original native unit selection")
    # Keep original returned arrays unchanged. Compare exact rational physical
    # gradients in Eh/Angstrom against the retained ASH-unit criterion.
    actual = Fraction(integrity.operands[1].absolute_maximum) / Fraction(outcome.request.gradient_length_angstrom)
    selected = Fraction(criteria.maximum_gradient_component_eh_per_ash_bohr) / Fraction(Decimal("0.5291772109303"))
    return A.FALSIFIED if actual > selected else A.SATISFIED


def _remaining_requirements(criteria, probe, outcome, ligands, geometry, integrity):
    required = {"requirement.molecular.independent-chemical-admission", "requirement.molecular.physical-ensemble-admission",
                "requirement.molecular.source-origin-admission", *criteria.unresolved_requirement_ids}
    if not ligands:
        required.add("requirement.molecular.complete-ligand-graphs")
    if probe is None:
        required.add("requirement.molecular.total-force-return")
    else:
        required.update(probe.unresolved_requirement_ids)
        if integrity is None or outcome.completion is None:
            required.add("requirement.molecular.completed-force-custody")
        if outcome.completion is not None and outcome.completion.operational_status is not OperationalStatus.SUCCEEDED:
            required.add("requirement.molecular.successful-force-call")
        if outcome.call_return is not None and (
                outcome.call_return.error_type is not None or outcome.call_return.return_code not in (None, 0)):
            required.add("requirement.molecular.successful-force-call")
    if _geometry_gate(geometry, criteria) is not A.SATISFIED:
        required.add("requirement.molecular.resolve-severe-contacts")
    if _force_gate(integrity, criteria, outcome) is not A.SATISFIED:
        required.add("requirement.molecular.resolve-force-assessment")
    return tuple(sorted(required))


@dataclass(frozen=True, slots=True)
class MolecularPreparationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/molecular-preparation-assessment"
    assessment_id: str
    representation: ObjectIdentity
    retained_geometry: RetainedMolecularGeometry
    criteria: MolecularPreparationCriteria
    geometry: GeometryDiagnostic
    geometry_gate: A
    probe: MolecularForceProbe | None
    probe_outcome: MolecularProbeOutcome | None
    force_integrity: CoupledNumericalIntegrity | None
    force_gate: A
    ligand_graph_findings: tuple[tuple[str, ObjectIdentity, int, int], ...]
    assessor_source: ObjectIdentity
    unresolved_requirement_ids: tuple[str, ...]
    geometry_method: ObjectIdentity = GEOMETRY_METHOD
    physical_and_chemical_admission: A = A.UNEVALUABLE
    independent_biological_units: int = 0
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        exact(self.representation, ObjectIdentity)
        exact(self.retained_geometry, RetainedMolecularGeometry)
        exact(self.criteria, MolecularPreparationCriteria)
        exact(self.geometry, GeometryDiagnostic)
        exact(self.assessor_source, ObjectIdentity)
        if self.retained_geometry.representation != self.representation or self.geometry_method != GEOMETRY_METHOD:
            raise ValueError("preparation assessment changes its exact original geometry operands/method")
        if (type(self.geometry_gate) is not A or self.geometry_gate != _geometry_gate(self.geometry, self.criteria)
                or type(self.force_gate) is not A or self.force_gate != _force_gate(self.force_integrity, self.criteria, self.probe_outcome)):
            raise ValueError("preparation assessment contradicts its independent numerical limits")
        if (self.probe is None) != (self.probe_outcome is None):
            raise ValueError("force assessment cannot detach its original probe outcome")
        if self.probe is not None:
            exact(self.probe, MolecularForceProbe)
            exact(self.probe_outcome, MolecularProbeOutcome)
            request = self.probe_outcome.request
            if (self.probe.representation != self.representation or request.protocol != self.probe.identity
                    or request.prepared_material != self.representation or request.physical_coordinates != self.probe.coordinates
                    or request.physical_atom_count != self.geometry.atom_count):
                raise ValueError("preparation force assessment changes its actual molecular/coordinate scope")
        if self.force_integrity is not None:
            exact(self.force_integrity, CoupledNumericalIntegrity)
            if (self.probe_outcome is None or self.probe_outcome.returned is None
                    or self.force_integrity.request != self.probe_outcome.request.identity
                    or self.force_integrity.raw_return != ObjectIdentity.from_record(
                        self.probe_outcome.returned.return_id, self.probe_outcome.returned)
                    or self.force_integrity.assessor_source != self.assessor_source):
                raise ValueError("force integrity loses its actual raw return or independent assessor")
        elif self.probe_outcome is not None and self.probe_outcome.returned is not None:
            raise ValueError("preparation assessment drops an available complete force return")
        if type(self.ligand_graph_findings) is not tuple or len(self.ligand_graph_findings) not in (0, 8):
            raise ValueError("preparation ligand assessment must retain all eight sites or remain unavailable")
        for site, graph, count, charge in self.ligand_graph_findings:
            validate_stable_id(site)
            exact(graph, ObjectIdentity)
            if type(count) is not int or count < 0 or type(charge) is not int:
                raise ValueError("preparation ligand graph census changes actual atoms/charge")
        if tuple(row[0] for row in self.ligand_graph_findings) != tuple(sorted(set(row[0] for row in self.ligand_graph_findings))):
            raise ValueError("preparation ligand findings duplicate or reorder a selected site")
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name="unresolved_requirement_ids", allow_empty=False)
        required = _remaining_requirements(self.criteria, self.probe, self.probe_outcome,
            self.ligand_graph_findings, self.geometry, self.force_integrity)
        if required != self.unresolved_requirement_ids:
            raise ValueError("preparation assessment changes its exact remaining scientific prerequisites")
        if (self.physical_and_chemical_admission is not A.UNEVALUABLE
                or type(self.new_native_calls) is not int or self.new_native_calls != 0
                or type(self.independent_biological_units) is not int or self.independent_biological_units != 0):
            raise ValueError("retained numerical/graph assessment cannot invent physical or biological admission")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.assessment_id, self)


def assess_molecular_preparation(representation, selected, criteria, *, raw_files, assessor_source,
                                 assessment_id, ligand_graphs=None, ligand_bindings=None,
                                 probe=None, probe_outcome=None, reader_for_manifest=None):
    """Independent current-use reduction; all original files/returns stay intact."""
    exact(criteria, MolecularPreparationCriteria)
    if type(raw_files) is not dict or set(raw_files) != {"topology", "coordinates", "heavy_atoms", "origins"}:
        raise ValueError("molecular preparation requires its exact four retained geometry inputs")
    geometry = assess_retained_geometry(representation, selected, **raw_files)
    if (ligand_graphs is None) != (ligand_bindings is None):
        raise ValueError("ligand assessment cannot drop its selected graphs or full site bindings")
    ligands = () if ligand_graphs is None else validate_ligand_correspondence(representation, ligand_graphs, ligand_bindings)
    if (probe is None) != (probe_outcome is None):
        raise ValueError("molecular force assessment needs its probe and actual retained outcome together")
    integrity = None
    if probe_outcome is not None:
        exact(probe_outcome, MolecularProbeOutcome)
        if probe_outcome.returned is not None:
            if not callable(reader_for_manifest):
                raise ValueError("force assessment needs an authenticated read port for actual captured bytes")
            integrity = assess_native_return(probe_outcome.request, probe_outcome.returned,
                reader_for_manifest, assessor_source=assessor_source)
    requirements = _remaining_requirements(criteria, probe, probe_outcome, ligands, geometry, integrity)
    return MolecularPreparationAssessment(assessment_id, representation.identity, selected, criteria, geometry,
        _geometry_gate(geometry, criteria), probe, probe_outcome, integrity, _force_gate(integrity, criteria, probe_outcome), ligands,
        assessor_source, requirements)
