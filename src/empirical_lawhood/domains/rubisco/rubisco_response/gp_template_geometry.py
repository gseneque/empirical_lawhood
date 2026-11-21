# SPDX-License-Identifier: MPL-2.0
"""Pure terminal construction for an explicitly unrelaxed common Gp parent.

The original native receipt describes only the original parent. The new heavy
coordinates have a separate pure derivation and structural assessment. Neither
record supplies a minimized endpoint, an equilibrium ensemble or physical rates.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence, SourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.geometry_reuse import GeometryReuseSupply
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preamber_geometry_integrity import PreAmberGeometryIntegrity, validate_geometry_origins
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.preparation_integrity import source_disulfide_partners
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.contracts import ORIGINALS, StructuralSourceMember
from empirical_lawhood.domains.rubisco.rubisco_insilico_structure.independent_assessment import original_assembly
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.gp_constructed_geometry import origin_mobility
from empirical_lawhood.domains.rubisco.rubisco_response.gp_heavy_geometry import inspect_heavy_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


TEMPLATE_NAMES = ("amino12.lib", "aminont12.lib", "aminoct12.lib", "parm10.dat", "frcmod.ff14SB")
SCOPE = "PURE_UNRELAXED_TERMINAL_CONSTRUCTION_NO_MINIMIZATION_ENSEMBLE_OR_RATE_ADMISSION"
METHOD = ObjectIdentity("method.gp-terminal-template-integrity",
    "empirical-lawhood/rubisco-response/gp-terminal-template-integrity-method", "1.0.0",
    sha256(b"Complete original source/origin and heavy identity census; exact fixed coordinates and noncoordinate bytes; "
           b"all heavy contacts, backbone geometry and stereo; every affected non-Pro peptide; no native replay.").hexdigest())


def _source_id(source):
    return ObjectIdentity.from_record(source.member_id, source)


def _template_sources(sources):
    if type(sources) is not tuple or len(sources) != len(TEMPLATE_NAMES):
        raise ValueError("terminal template construction requires its complete selected stock")
    for source, name in zip(sources, TEMPLATE_NAMES, strict=True):
        exact(source, SourceMember)
        if source.member_id != "source.gp-terminal-template." + name.lower():
            raise ValueError("terminal template construction changes the selected source order")
    return tuple(_source_id(s) for s in sources)


def _matches(raw, evidence):
    return type(raw) is bytes and (len(raw), sha256(raw).hexdigest()) == (evidence.byte_count, evidence.sha256)


@dataclass(frozen=True, slots=True)
class GpTemplateGeometryIntegrity(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-template-geometry-integrity"
    product_id: str
    original_assessment: PreAmberGeometryIntegrity
    gp_source: ObjectIdentity
    template_sources: tuple[ObjectIdentity, ...]
    heavy_file: FileEvidence
    origin_file: FileEvidence
    atom_count: int
    inherited_atom_count: int
    constructed_atom_count: int
    affected_nonpro_peptides: int
    short_contact_count: int
    backbone_anomaly_count: int
    stereo_anomaly_count: int
    nontrans_peptide_count: int
    structural_disposition: A
    method: ObjectIdentity = METHOD
    scope: str = SCOPE
    minimization_disposition: A = A.UNEVALUABLE
    ensemble_disposition: A = A.UNEVALUABLE
    rate_disposition: A = A.UNEVALUABLE
    new_native_calls: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        exact(self.original_assessment, PreAmberGeometryIntegrity)
        exact(self.gp_source, ObjectIdentity)
        if (self.gp_source.object_schema != StructuralSourceMember.SCHEMA
                or type(self.template_sources) is not tuple or len(self.template_sources) != len(TEMPLATE_NAMES)):
            raise ValueError("template geometry loses its complete original and template sources")
        for identity, name in zip(self.template_sources, TEMPLATE_NAMES, strict=True):
            exact(identity, ObjectIdentity)
            if identity.object_schema != SourceMember.SCHEMA or identity.object_id != "source.gp-terminal-template." + name.lower():
                raise ValueError("template geometry substitutes its template identities")
        exact(self.heavy_file, FileEvidence)
        exact(self.origin_file, FileEvidence)
        old = self.original_assessment
        if (old.construct.construct_id != "gp.wt.m1" or self.origin_file != old.origin_file
                or self.heavy_file.relative_path != "template.gp.wt.m1/complete-heavy.pdb"
                or (self.atom_count, self.inherited_atom_count, self.constructed_atom_count) !=
                   (old.atom_count, old.inherited_atom_count, old.constructed_atom_count)):
            raise ValueError("template geometry changes the original material or complete atom denominator")
        counts = (self.atom_count, self.inherited_atom_count, self.constructed_atom_count,
            self.affected_nonpro_peptides, self.short_contact_count, self.backbone_anomaly_count,
            self.stereo_anomaly_count, self.nontrans_peptide_count)
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("template geometry requires complete integer diagnostic counts")
        failures = counts[-4:]
        if (self.structural_disposition is not (A.FALSIFIED if any(failures) else A.SATISFIED)
                or self.method != METHOD or self.scope != SCOPE
                or any(v is not A.UNEVALUABLE for v in (self.minimization_disposition,
                    self.ensemble_disposition, self.rate_disposition))
                or type(self.new_native_calls) is not int or self.new_native_calls != 0):
            raise ValueError("pure template geometry cannot claim native minimization or physical admission")

    @property
    def construct(self):
        return self.original_assessment.construct


@dataclass(frozen=True, slots=True)
class GpTemplateGeometrySupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/gp-template-geometry-supply"
    supply_id: str
    parent: GeometryReuseSupply
    original_heavy_pdb: str
    template_sources: tuple[SourceMember, ...]
    integrity: GpTemplateGeometryIntegrity

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        exact(self.parent, GeometryReuseSupply)
        exact(self.integrity, GpTemplateGeometryIntegrity)
        old = self.integrity.original_assessment
        if (self.parent.independent_integrity != ObjectIdentity.from_record(old.product_id, old)
                or self.parent.geometry_receipt != old.geometry_receipt
                or self.parent.definition.identity != old.geometry_definition
                or type(self.original_heavy_pdb) is not str
                or not _matches(self.original_heavy_pdb.encode(), old.heavy_file)
                or _template_sources(self.template_sources) != self.integrity.template_sources):
            raise ValueError("template supply changes its original native ancestry or pure construction operands")
        stock = {s.member_id: s for s in self.parent.original_source.source_members}
        for source, original in zip(self.template_sources[-2:], ("source.parm10-dat", "source.ff14sb-frcmod"), strict=True):
            if original not in stock or stock[original].sha256 != source.sha256:
                raise ValueError("terminal construction changes the original selected peptide parameter stock")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.supply_id, self)

    @property
    def independent_integrity(self):
        return ObjectIdentity.from_record(self.integrity.product_id, self.integrity)


def check_construction_invariants(original_heavy, heavy, origin):
    """Independent byte and complete-identity checks; no coordinate constructor."""
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_geometry_repair_assessment import _omega_degrees
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import heavy_pdb_rows
    before, permitted = origin_mobility(original_heavy, origin)
    after, actual_permitted = origin_mobility(heavy, origin)
    if permitted != actual_permitted or len(before) != len(after):
        raise ValueError("template construction changes original mobile or fixed atom membership")
    allowed = set(permitted)
    old_lines, new_lines = original_heavy.splitlines(keepends=True), heavy.splitlines(keepends=True)
    if len(old_lines) != len(new_lines):
        raise ValueError("template construction changes the original serialized record census")
    for old, new in zip(old_lines, new_lines, strict=True):
        if old.startswith(("ATOM  ", "HETATM")):
            key = old[21], int(old[22:26]), old[12:16].strip()
            if old[:30] != new[:30] or old[54:] != new[54:]:
                raise ValueError("template construction changes original noncoordinate atom bytes")
            if key not in allowed and old != new:
                raise ValueError("template construction moves an observed fixed atom")
        elif old != new:
            raise ValueError("template construction changes original non-atom records")
    geometry = inspect_heavy_geometry(heavy_pdb_rows(heavy))
    atoms = {(a['chain'], a['position'], a['atom']): a for a in after}
    peptides = []
    for chain, position, name in atoms:
        if chain == "Z" or name != "C":
            continue
        keys = ((chain, position, "CA"), (chain, position, "C"),
                (chain, position+1, "N"), (chain, position+1, "CA"))
        if (all(k in atoms for k in keys) and allowed.intersection(keys)
                and atoms[keys[2]]["component"] != "PRO"):
            peptides.append(_omega_degrees([atoms[k]["xyz"] for k in keys]))
    return geometry, len(peptides), sum(abs(angle) < 150 for angle in peptides)


def assess_template_parent(*, product_id, parent_assessment, original_heavy, heavy, origin_bytes, gp_source, template_sources):
    """Reassess source, identity and structural integrity without template replay."""
    exact(parent_assessment, PreAmberGeometryIntegrity)
    exact(gp_source, StructuralSourceMember)
    selected_sources = _template_sources(template_sources)
    if gp_source.sha256 != dict(ORIGINALS)["1bwv.cif"]:
        raise ValueError("terminal construction requires the exact full original Gp source")
    if (not _matches(original_heavy, parent_assessment.heavy_file)
            or not _matches(origin_bytes, parent_assessment.origin_file) or type(heavy) is not bytes):
        raise ValueError("template assessment substitutes original geometry or atom-origin bytes")
    origin = json.loads(origin_bytes)
    atoms, chains, _, _, _ = original_assembly("1BWV", gp_source.raw_utf8)
    atoms = tuple(decode_canonical_bytes(a.canonical_bytes(), type(a), maximum_bytes=4096) for a in atoms)
    counts = validate_geometry_origins(parent_assessment.construct, parent_assessment.joint_view_id,
        origin, heavy.decode("ascii"), atoms, chains,
        source_disulfide_partners("1BWV", gp_source.raw_utf8, atoms, chains))
    if any(getattr(parent_assessment, name) != value for name, value in counts.items()):
        raise ValueError("template construction changes its complete original source denominator")
    geometry, peptides, nontrans = check_construction_invariants(original_heavy.decode("ascii"), heavy.decode("ascii"), origin)
    failures = tuple(len(geometry[name]) for name in ("short_contacts_squared_angstrom",
        "backbone_anomalies_squared_angstrom", "stereochemistry_anomalies_angstrom3")) + (nontrans,)
    return GpTemplateGeometryIntegrity(product_id, parent_assessment,
        ObjectIdentity.from_record("source.scaffold." + gp_source.sha256, gp_source), selected_sources,
        FileEvidence("template.gp.wt.m1/complete-heavy.pdb", len(heavy), sha256(heavy).hexdigest()),
        parent_assessment.origin_file, counts["atom_count"], counts["inherited_atom_count"],
        counts["constructed_atom_count"], peptides, *failures, A.FALSIFIED if any(failures) else A.SATISFIED)


def prepare_template_parent(*, parent, parent_assessment, heavy, origin_bytes, gp_source, template_sources):
    """Derive a pure common starting parent and retain its separate assessment."""
    from empirical_lawhood.domains.rubisco.rubisco_response.terminal_templates import build_terminals, peptide_parameters, read_templates
    exact(parent, GeometryReuseSupply)
    exact(parent_assessment, PreAmberGeometryIntegrity)
    _template_sources(template_sources)
    if parent.independent_integrity != ObjectIdentity.from_record(parent_assessment.product_id, parent_assessment):
        raise ValueError("terminal construction changes its original independent parent assessment")
    if not _matches(heavy, parent_assessment.heavy_file) or not _matches(origin_bytes, parent_assessment.origin_file):
        raise ValueError("terminal construction substitutes original input bytes")
    templates = {}
    for source in template_sources[:3]:
        templates.update(read_templates(source.raw_utf8))
    parameters = peptide_parameters(*(s.raw_utf8 for s in template_sources[-2:]))
    result, _, _ = build_terminals(heavy.decode("ascii"), json.loads(origin_bytes), templates, **parameters)
    current = result.encode("ascii")
    key = sha256(parent.canonical_bytes() + current + origin_bytes
                 + b"".join(s.canonical_bytes() for s in template_sources)).hexdigest()
    integrity = assess_template_parent(product_id="assessment.gp-template-parent." + key,
        parent_assessment=parent_assessment, original_heavy=heavy, heavy=current,
        origin_bytes=origin_bytes, gp_source=gp_source, template_sources=template_sources)
    supply = GpTemplateGeometrySupply("supply.gp-template-parent." + key, parent, heavy.decode("ascii"), template_sources, integrity)
    return supply, current
