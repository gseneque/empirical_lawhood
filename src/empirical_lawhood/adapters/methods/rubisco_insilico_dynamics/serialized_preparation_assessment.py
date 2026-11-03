# SPDX-License-Identifier: MPL-2.0
"""Explicit TER-aware successors using unchanged independent assessment math.

Legacy records, readers and module globals remain untouched. Each selected
function has its original code and an isolated globals dictionary containing
only the named reader/record/method substitutions. No producer or native module
is imported. The caller authenticates original complete source and raw custody.
"""

from dataclasses import dataclass, replace
from hashlib import sha256
from types import FunctionType, SimpleNamespace
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes

from . import physical_preparation_geometry as geometry_math
from . import preparation_integrity as assignment_math
from .serialized_heavy_pdb import METHOD as READER_METHOD, read_heavy_pdb


ASSIGNMENT_DESCRIPTION = (
    "Unchanged independent preparation assignment/source-origin math with an "
    "explicit serialized-heavy-PDB reader preserving every original ATOM/TER "
    "serial and directed CONECT term. Full original24 outcome denominator. "
    "Legacy canonical methods/records remain unchanged. Assignment consistency "
    "does not establish geometry, chemistry, native coverage, dynamics or kinetics."
)
ASSIGNMENT_METHOD = ObjectIdentity(
    "method.rubisco-dynamics.serialized-preparation-integrity",
    assignment_math.METHOD.object_schema, "1.1.0",
    sha256(canonical_json_bytes((ASSIGNMENT_DESCRIPTION,
        assignment_math.METHOD, READER_METHOD))).hexdigest(),
)
GEOMETRY_DESCRIPTION = (
    "Unchanged independent exact lexical retained-input geometry math with an "
    "explicit serialized-heavy-PDB reader and explicit TER-aware assignment "
    "parent. Original serials, all original atom/bond/pair operands and full24 "
    "outcome denominator remain complete. No physical/chemical/native/dynamic "
    "or kinetic admission follows from this mathematical diagnostic."
)
GEOMETRY_METHOD = ObjectIdentity(
    "method.rubisco-dynamics.serialized-preparation-geometry",
    geometry_math.METHOD.object_schema, "1.1.0",
    sha256(canonical_json_bytes((GEOMETRY_DESCRIPTION,
        geometry_math.METHOD, READER_METHOD, ASSIGNMENT_METHOD))).hexdigest(),
)


def _selected(function, **named_globals):
    """Domain-local exact code reuse; never alter the historical function."""
    selected = FunctionType(function.__code__, dict(function.__globals__, **named_globals),
        function.__name__, function.__defaults__, function.__closure__)
    selected.__kwdefaults__ = function.__kwdefaults__
    return selected


@dataclass(frozen=True, slots=True)
class SerializedPreparationIntegrity(assignment_math.PreparationIntegrity):
    """New revision; the original 1.0.0 class cannot decode this record."""

    VERSION: ClassVar[str] = "1.1.0"
    legacy_math_method: ObjectIdentity = assignment_math.METHOD
    pdb_reader_method: ObjectIdentity = READER_METHOD

    def __post_init__(self):
        _selected(assignment_math.PreparationIntegrity.__post_init__,
            METHOD=ASSIGNMENT_METHOD)(self)
        if (self.legacy_math_method != assignment_math.METHOD
                or self.pdb_reader_method != READER_METHOD):
            raise ValueError("serialized assignment changes its exact legacy math/reader methods")


@dataclass(frozen=True, slots=True)
class SerializedPreparationGeometry(geometry_math.PhysicalPreparationGeometry):
    """New revision; diagnostics retain their unchanged exact arithmetic."""

    VERSION: ClassVar[str] = "1.1.0"
    method: ObjectIdentity = GEOMETRY_METHOD
    legacy_math_method: ObjectIdentity = geometry_math.METHOD
    pdb_reader_method: ObjectIdentity = READER_METHOD

    def __post_init__(self):
        _selected(geometry_math.PhysicalPreparationGeometry.__post_init__,
            METHOD=GEOMETRY_METHOD)(self)
        if (self.legacy_math_method != geometry_math.METHOD
                or self.pdb_reader_method != READER_METHOD):
            raise ValueError("serialized geometry changes its exact legacy math/reader methods")


def validate_origins(model, census, origin, heavy_text, source_atoms, source_chains,
                     expected_disulfides):
    """Same complete raw Amber/source origin math, justified TER serials."""
    return _selected(assignment_math.validate_origins, read_heavy_pdb=read_heavy_pdb)(
        model, census, origin, heavy_text, source_atoms, source_chains, expected_disulfides)


def assess(source, preparation, assets, source_atoms, source_chains, disulfides):
    """Full24 assignment assessment with an explicit successor method/record."""
    result = _selected(assignment_math.assess, validate_origins=validate_origins,
        METHOD=ASSIGNMENT_METHOD, PreparationIntegrity=SerializedPreparationIntegrity)(
        source, preparation, assets, source_atoms, source_chains, disulfides)
    return replace(result, product_id="product.rubisco-dynamics.serialized-preparation-integrity")


def diagnose_geometry(raw_prmtop, raw_inpcrd, heavy_pdb, origins):
    """Same exact mathematical diagnostic with the explicit serialized reader."""
    selected_join = _selected(geometry_math._origin_join, read_heavy_pdb=read_heavy_pdb)
    return _selected(geometry_math.diagnose_geometry, _origin_join=selected_join)(
        raw_prmtop, raw_inpcrd, heavy_pdb, origins)


COORDINATE_ORIGIN_DESCRIPTION = (
    "Unchanged complete independent Fraction coordinate-origin/candidate and source/genotype/addition/disulfide math; "
    "explicit authentic serialized-heavy-PDB reader preserves all ATOM/TER serials and directed CONECT terms. "
    "No original native-unit or model outcome relabelling and no physical/chemical/kinetic admission."
)
COORDINATE_ORIGIN_METHOD = ObjectIdentity(assignment_math.COORDINATE_ORIGIN_METHOD.object_id,
    assignment_math.COORDINATE_ORIGIN_METHOD.object_schema,"1.1.0",
    sha256(canonical_json_bytes((COORDINATE_ORIGIN_DESCRIPTION,
        assignment_math.COORDINATE_ORIGIN_METHOD,READER_METHOD))).hexdigest())
SUPPORTED_INACTIVE14_GEOMETRY_DESCRIPTION = (
    "Unchanged supported inactive14 full exact geometry math with an explicit serialized-heavy-PDB reader; "
    "complete pair/bond/atom denominators and original outcome history remain; no physical adequacy admission."
)
SUPPORTED_INACTIVE14_GEOMETRY_METHOD = ObjectIdentity(geometry_math.SUPPORTED_INACTIVE14_METHOD.object_id,
    geometry_math.SUPPORTED_INACTIVE14_METHOD.object_schema,"1.2.0",
    sha256(canonical_json_bytes((SUPPORTED_INACTIVE14_GEOMETRY_DESCRIPTION,
        geometry_math.SUPPORTED_INACTIVE14_METHOD,READER_METHOD))).hexdigest())


def validate_coordinate_origins_supported_serialized(model,census,origin,heavy_text,raw_inpcrd,
                                                    source_atoms,source_chains,expected_disulfides):
    """Explicit TER-aware successor; no normalization or module mutation."""
    selected_join = _selected(geometry_math._origin_join,read_heavy_pdb=read_heavy_pdb)
    selected_lower = _selected(assignment_math.validate_origins,read_heavy_pdb=read_heavy_pdb)
    result = _selected(assignment_math.validate_origins_from_coordinates,
        read_heavy_pdb=read_heavy_pdb,validate_origins=selected_lower,
        _coordinate_origin_readers=lambda:(selected_join,geometry_math.read_inpcrd))(
            model,census,origin,heavy_text,raw_inpcrd,source_atoms,source_chains,expected_disulfides)
    return replace(result,method=COORDINATE_ORIGIN_METHOD)


@dataclass(frozen=True, slots=True)
class SerializedSupportedInactive14Geometry(geometry_math.SupportedInactive14Geometry):
    """Explicit method1.2; original method1.1 cannot claim this reader scope."""

    legacy_support_method: ObjectIdentity = geometry_math.SUPPORTED_INACTIVE14_METHOD
    pdb_reader_method: ObjectIdentity = READER_METHOD

    def __post_init__(self):
        _selected(geometry_math.SupportedInactive14Geometry.__post_init__,
            SUPPORTED_INACTIVE14_METHOD=SUPPORTED_INACTIVE14_GEOMETRY_METHOD)(self)
        if self.legacy_support_method!=geometry_math.SUPPORTED_INACTIVE14_METHOD or self.pdb_reader_method!=READER_METHOD:
            raise ValueError("serialized supported geometry changes its exact original math/reader methods")


def diagnose_geometry_supported_inactive14_serialized(raw_prmtop,raw_inpcrd,heavy_pdb,origins):
    """Only named reader/census/result substitutions in unchanged geometry math."""
    from .amber_parameters import assigned_census_supported_inactive14

    selected_join = _selected(geometry_math._origin_join,read_heavy_pdb=read_heavy_pdb)
    diagnostic = _selected(geometry_math.diagnose_geometry,
        assigned_census=assigned_census_supported_inactive14,_origin_join=selected_join)(
            raw_prmtop,raw_inpcrd,heavy_pdb,origins)
    return SerializedSupportedInactive14Geometry(SUPPORTED_INACTIVE14_GEOMETRY_METHOD,diagnostic)


def assess_geometry(source, preparation, assets, integrity):
    """Full24 exact-custody mathematical assessment, physical scope unchanged."""
    result = _selected(geometry_math.assess_geometry,
        PreparationIntegrity=SerializedPreparationIntegrity,
        PhysicalPreparationGeometry=SerializedPreparationGeometry,
        diagnose_geometry=diagnose_geometry)(source, preparation, assets, integrity)
    return replace(result, product_id="product.rubisco-dynamics.serialized-preparation-geometry")


def assess_preparation_integrity(source, nomination, inventory, coordinates,
                                 preparation, assets):
    """Independently rebuild original sources before the selected raw assessor."""
    import json

    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.independent_assessment import (
        original_assembly, validate_coordinate_export,
    )
    from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A

    from . import contracts as c
    from .science import validate_inputs

    validate_inputs(source, nomination, inventory, coordinates)
    preparation.__post_init__()
    if (preparation.source != c.identity(source)
            or preparation.structural_inventory != source.structural_inventory
            or preparation.structural_coordinates != source.structural_coordinates
            or preparation.nomination != source.nomination):
        raise ValueError("serialized preparation changes original source lineage")
    atoms, chains, disulfides = (), (), {}
    if any(model.disposition is A.SATISFIED for model in preparation.models):
        members = {row.member_id: row.raw_utf8 for row in source.source_members}
        engine = {row["path"]: row["sha256"] for row in json.loads(
            members["source.engine-inventory"])["entries"] if row["kind"] == "file"}
        if any(engine.get(".venv/lib/python3.11/site-packages/" + path) != digest
               for path, digest in assignment_math.SOURCE_CONVERSIONS):
            raise ValueError("serialized assignment substitutes pinned Amber conversions")
        pieces = [original_assembly(pdb, members["source.original-" + pdb.lower() + "-cif"])
            for pdb in ("1BWV", "3ZXW")]
        atoms, chains, operators = (tuple(row for piece in pieces for row in piece[index])
            for index in (0, 1, 2))
        if inventory.atoms != atoms or inventory.chains != chains or inventory.operators != operators:
            raise ValueError("serialized preparation substitutes independent original structure")
        view = SimpleNamespace(source_members=tuple(SimpleNamespace(
            filename=pdb.lower() + ".cif", raw_utf8=members["source.original-" + pdb.lower() + "-cif"])
            for pdb in ("1BWV", "3ZXW")))
        validate_coordinate_export(view, inventory, coordinates)
        disulfides = {pdb: assignment_math.source_disulfide_partners(pdb,
            members["source.original-" + pdb.lower() + "-cif"], atoms, chains)
            for pdb in ("1BWV", "3ZXW")}
    return assess(source, preparation, assets, atoms, chains, disulfides)
