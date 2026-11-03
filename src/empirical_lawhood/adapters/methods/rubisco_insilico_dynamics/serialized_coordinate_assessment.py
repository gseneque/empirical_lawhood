# SPDX-License-Identifier: MPL-2.0
"""Explicit composition of serialized origins and supported inactive scales.

Original bytes and historical assessor namespaces remain unchanged. This
successor joins the complete raw coordinates independently of the producer.
It establishes neither physical adequacy nor native preparation success.
"""

from dataclasses import dataclass
from hashlib import sha256
from types import FunctionType

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes

from . import amber_parameters as parameters
from . import physical_preparation_geometry as geometry
from . import preparation_integrity as assignment
from .serialized_heavy_pdb import METHOD as READER_METHOD, read_heavy_pdb


ORIGIN_METHOD = ObjectIdentity(
    assignment.COORDINATE_ORIGIN_METHOD.object_id,
    assignment.COORDINATE_ORIGIN_METHOD.object_schema,
    "1.1.0",
    sha256(canonical_json_bytes((assignment.COORDINATE_ORIGIN_METHOD, READER_METHOD,
        "Complete independent coordinate proof and lower source guards use original ATOM/TER serials."))).hexdigest(),
)
GEOMETRY_METHOD = ObjectIdentity(
    "method.rubisco-dynamics.serialized-supported-inactive14-geometry",
    geometry.METHOD.object_schema,
    "1.0.0",
    sha256(canonical_json_bytes((geometry.SUPPORTED_INACTIVE14_METHOD, READER_METHOD,
        "Complete retained-input geometry with original ATOM/TER serials and supported inactive scales."))).hexdigest(),
)


def _selected(function, **substitutions):
    selected = FunctionType(function.__code__, dict(function.__globals__, **substitutions),
        function.__name__, function.__defaults__, function.__closure__)
    selected.__kwdefaults__ = function.__kwdefaults__
    return selected


def _origin_join(census, coordinates, heavy_pdb, origins):
    return _selected(geometry._origin_join, read_heavy_pdb=read_heavy_pdb)(
        census, coordinates, heavy_pdb, origins)


def _coordinate_origin_readers():
    return _origin_join, geometry.read_inpcrd


def validate_origins_from_coordinates(model, census, origin, heavy_text, raw_inpcrd,
                                     source_atoms, source_chains, expected_disulfides):
    """Select the serialized reader at every level of the independent proof."""
    lower = _selected(assignment.validate_origins, read_heavy_pdb=read_heavy_pdb)
    return _selected(assignment.validate_origins_from_coordinates,
        _coordinate_origin_readers=_coordinate_origin_readers,
        read_heavy_pdb=read_heavy_pdb, validate_origins=lower,
        COORDINATE_ORIGIN_METHOD=ORIGIN_METHOD)(model, census, origin, heavy_text,
            raw_inpcrd, source_atoms, source_chains, expected_disulfides)


@dataclass(frozen=True, slots=True)
class SerializedCoordinateGeometry:
    method: ObjectIdentity
    diagnostic: geometry.GeometryDiagnostic

    def __post_init__(self):
        if self.method != GEOMETRY_METHOD or type(self.diagnostic) is not geometry.GeometryDiagnostic:
            raise ValueError("serialized geometry changes its explicit method or complete diagnostic")
        self.diagnostic.__post_init__()


def diagnose_geometry_supported_inactive14(raw_prmtop, raw_inpcrd, heavy_pdb, origins):
    """Compose both supported input readers before the complete geometry math."""
    diagnostic = _selected(geometry.diagnose_geometry,
        assigned_census=parameters.assigned_census_supported_inactive14,
        _origin_join=_origin_join)(raw_prmtop, raw_inpcrd, heavy_pdb, origins)
    return SerializedCoordinateGeometry(GEOMETRY_METHOD, diagnostic)
