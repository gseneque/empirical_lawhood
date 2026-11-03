# SPDX-License-Identifier: MPL-2.0
"""Narrow deferred seam to the existing ethane total-Hamiltonian construction.

Nothing in this module launches a process, grants authority or constructs a
native object on import. The selected caller owns entry, full apparatus/raw
custody, source/stock authentication and physical resource accounting.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import ClassVar
import xml.etree.ElementTree as ET

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256

from . import derivative_controls as d
from . import prospective_xtb

_MUTABLE_CALLBACK_WITNESSES = frozenset(("point_field_materialized", "realized_nonzero_point_charge_atoms", "verified_callback_entries"))


def _intrinsic_audit(audit):
    return json.dumps({key: value for key, value in audit.items() if key not in _MUTABLE_CALLBACK_WITNESSES},
                      sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class EthaneDerivativePreparation(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/ethane-derivative-preparation"
    preparation_id: str
    baseline: d.CartesianPoint
    source_members: tuple[ObjectIdentity, ...]
    native_stock: ObjectIdentity
    intrinsic_native_construction_json: str
    derived_prmtop_sha256: str
    realized_classical_system_xml: str
    callback_model_id: str = prospective_xtb.MODEL_ID
    real_qm_indices: tuple[int, ...] = (0, 2, 3, 4)
    physical_atom_roles: tuple[str, ...] = ("BOUNDARY_QM", "BOUNDARY_MM", "QM", "QM", "QM", "MM", "MM", "MM")
    claim_scope: str = "SYNTHETIC_ETHANE_CONSTRUCTION_NOT_GP_REACTIVE_OR_PHYSICAL_QUALIFICATION"

    def __post_init__(self):
        from empirical_lawhood.kernel.serialization import validate_stable_id
        validate_stable_id(self.preparation_id)
        self.baseline.__post_init__()
        if (self.baseline.atom_ids != tuple("ethane:"+str(i) for i in range(8))
                or self.real_qm_indices != (0, 2, 3, 4)
                or self.physical_atom_roles != ("BOUNDARY_QM", "BOUNDARY_MM", "QM", "QM", "QM", "MM", "MM", "MM")
                or self.callback_model_id != prospective_xtb.MODEL_ID
                or self.claim_scope != "SYNTHETIC_ETHANE_CONSTRUCTION_NOT_GP_REACTIVE_OR_PHYSICAL_QUALIFICATION"):
            raise ValueError("ethane derivative preparation changes its explicit synthetic whole physical scope")
        for row in (*self.source_members, self.native_stock): d._identity(row)
        if not self.source_members or tuple(row.object_id for row in self.source_members) != tuple(sorted(set(row.object_id for row in self.source_members))):
            raise ValueError("ethane derivative preparation drops complete selected source bindings")
        validate_sha256(self.derived_prmtop_sha256)
        system = ET.fromstring(self.realized_classical_system_xml)
        particles = system.find('Particles')
        if (system.tag != 'System' or particles is None or len(particles) != 8
                or system.find('Forces') is None):
            raise ValueError("ethane preparation omits actual complete serialized classical Hamiltonian")
        audit = json.loads(self.intrinsic_native_construction_json)
        if (self.intrinsic_native_construction_json != _intrinsic_audit(audit)
                or audit.get("physical_atoms") != 8 or audit.get("real_qm_atoms") != 4
                or audit.get("generated_links") != 1 or audit.get("qm_charge") != 0
                or audit.get("derived_prmtop_sha256") != self.derived_prmtop_sha256
                or audit.get("classical_charge_policy") != "unshifted-source-MM;QM-particle-and-exception-zero"
                or audit.get("quantum_field_policy") != "ASH-CAcharge-shift-only;no-dipole-correction"
                or audit.get("expected_nonzero_point_charge_atoms") != 2):
            raise ValueError("ethane derivative preparation substitutes actual selected Hamiltonian audit")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.preparation_id, self)


def prepare_ethane_derivatives(qm_callback, *, preparation_id, source_members, native_stock,
                              scratch_directory, protocol_sha256, native_system_serializer,
                              native_libraries=None, site_packages=None):
    """Explicit already-authorized native construction; never called by PURE code.

    Reuses build_ethane_control unchanged. Its complete audit and derived native
    topology remain original scientific operands, separately from the frozen
    prospective numerical derivative protocol. It evaluates no native objective.
    """
    from . import native_coupling
    if type(qm_callback) is not prospective_xtb.StrictQmmmXtbTheoryV1:
        raise ValueError("prospective derivative preparation needs its actual disclosed callback successor")
    if not callable(native_system_serializer):
        raise ValueError("native derivative preparation needs its explicitly selected actual System serializer")
    for row in (*source_members, native_stock): d._identity(row)
    from empirical_lawhood.kernel.serialization import validate_stable_id
    validate_stable_id(preparation_id)
    validate_sha256(protocol_sha256)
    if not source_members or tuple(row.object_id for row in source_members) != tuple(sorted(set(row.object_id for row in source_members))):
        raise ValueError("derivative native preparation omits complete selected source roster")
    session = native_coupling.build_ethane_control(qm_callback, scratch_directory=scratch_directory,
        protocol_sha256=protocol_sha256, native_libraries=native_libraries, site_packages=site_packages)
    coordinates = session.fragment.coords
    if getattr(getattr(coordinates, "dtype", None), "kind", None) != "f" or coordinates.dtype.itemsize != 8 or coordinates.shape != (8, 3):
        raise ValueError("ethane constructor did not return its original complete binary64 physical coordinates")
    baseline = d.CartesianPoint(preparation_id+".baseline", tuple("ethane:"+str(i) for i in range(8)),
        tuple(tuple(float(value).hex() for value in row) for row in coordinates))
    preparation = EthaneDerivativePreparation(preparation_id, baseline, source_members, native_stock,
        _intrinsic_audit(session.audit), session.audit['derived_prmtop_sha256'],
        native_system_serializer(session.theory.mm_theory.system))
    return preparation, session


def profile_for_preparation(preparation, *, profile_id):
    preparation.__post_init__()
    return d.PointFieldHamiltonian(profile_id, preparation.source_members, preparation.native_stock,
        preparation.identity, "SYNTHETIC_ETHANE_CONTROL")


def evaluate_ethane_point(protocol, point, preparation, session, *, producing_provenance, progress, entry,
                          native_system_serializer):
    """One genuine existing ASH total E/G operator, then pre-guard raw capture.

    Full reference MM movement remains unsupported by its historical fixed-MM
    owner. This seam deliberately supplies only the existing movable ethane
    control; it cannot relabel that result as Gp/reactive or enzyme adequacy.
    """
    from . import native_coupling
    import numpy as np
    preparation.__post_init__()
    protocol.__post_init__()
    request = d.request_for_point(protocol, point, producing_provenance=producing_provenance)
    if (type(session) is not native_coupling.CouplingSession
            or protocol.profile != profile_for_preparation(preparation, profile_id=protocol.profile.profile_id)
            or protocol.prepared_material != preparation.identity or protocol.baseline != preparation.baseline
            or protocol.physical_atom_roles != preparation.physical_atom_roles
            or _intrinsic_audit(session.audit) != preparation.intrinsic_native_construction_json
            or getattr(session.theory.qm_theory, 'theorynamelabel', None) != prospective_xtb.MODEL_ID
            or native_system_serializer(session.theory.mm_theory.system) != preparation.realized_classical_system_xml):
        raise ValueError("derivative operator substitutes genuine ethane construction or realized point-field Hamiltonian")
    if sha256((session.scratch_directory/'ethane-control.prmtop').read_bytes()).hexdigest() != preparation.derived_prmtop_sha256:
        raise ValueError("derivative operator changes original complete prepared topology bytes")
    coordinates = np.asarray([[float.fromhex(value) for value in row] for row in point.coordinates_angstrom_hex], dtype=np.float64)
    return d.evaluate_then_capture(request, lambda: session.theory.run(current_coords=coordinates, Grad=True), progress, entry)
