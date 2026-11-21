# SPDX-License-Identifier: MPL-2.0
"""Independent geometry assessment from bounded authenticated retained operands."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import io
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import (
    MolecularGeometryPolicy, assess_molecular_geometry, bound_geometry_terms,
)


@dataclass(frozen=True, slots=True)
class RetainedMolecularGeometryAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/retained-molecular-geometry-assessment'
    representation: ObjectIdentity
    source_topology: ObjectIdentity
    physical_atom_count: int
    coordinate_sha256: str | None
    policy: MolecularGeometryPolicy
    disposition: str
    findings: tuple[str, ...]
    census: tuple[tuple[str, int], ...]
    metrics: tuple[tuple[str, Decimal], ...]
    wholly_qm_bonded_atoms: tuple[int, ...]
    scope: str = 'INDEPENDENT_GROSS_GEOMETRY_SCREEN_WITHOUT_CHEMICAL_OR_EQUILIBRIUM_ADMISSION'

    def __post_init__(self):
        if (type(self.representation) is not ObjectIdentity or type(self.source_topology) is not ObjectIdentity
                or type(self.policy) is not MolecularGeometryPolicy
                or type(self.physical_atom_count) is not int or self.physical_atom_count <= 0
                or self.disposition not in ('SCREEN_PASSED', 'REJECTED', 'UNEVALUABLE')
                or self.scope != 'INDEPENDENT_GROSS_GEOMETRY_SCREEN_WITHOUT_CHEMICAL_OR_EQUILIBRIUM_ADMISSION'):
            raise ValueError('retained geometry changes its complete source, policy or scope')
        if (self.coordinate_sha256 is not None and (type(self.coordinate_sha256) is not str
                or len(self.coordinate_sha256) != 64
                or any(c not in '0123456789abcdef' for c in self.coordinate_sha256))):
            raise ValueError('retained geometry has no exact original coordinate fingerprint')
        if (type(self.findings) is not tuple or self.findings != tuple(sorted(set(self.findings)))
                or (not self.findings) != (self.disposition == 'SCREEN_PASSED')
                or type(self.census) is not tuple or type(self.metrics) is not tuple
                or any(type(n) is not int or n < 0 for _, n in self.census)
                or any(type(v) is not Decimal or not v.is_finite() for _, v in self.metrics)
                or len(dict(self.census)) != len(self.census) or len(dict(self.metrics)) != len(self.metrics)
                or self.census != tuple(sorted(self.census)) or self.metrics != tuple(sorted(self.metrics))
                or type(self.wholly_qm_bonded_atoms) is not tuple
                or self.wholly_qm_bonded_atoms != tuple(sorted(set(self.wholly_qm_bonded_atoms)))
                or any(type(i) is not int or not 0 <= i < self.physical_atom_count for i in self.wholly_qm_bonded_atoms)):
            raise ValueError('retained geometry changes its assessment denominator or findings')
        for finding in self.findings:
            validate_stable_id(finding)
        if self.disposition != 'UNEVALUABLE' and (self.coordinate_sha256 is None
                or dict(self.census).get('atoms') != self.physical_atom_count):
            raise ValueError('retained geometry cannot assess an absent complete coordinate array')


class RetainedGeometryReader:
    """Capture only bounded original topology/coordinate files; ignore producer verdicts."""
    def __init__(self, *, representation, policy, cell, qm_atoms, expected_coordinate_sha256):
        self.representation, self.policy, self.cell = representation, policy, cell
        self.qm_atoms = tuple(qm_atoms)
        self.expected_coordinate_sha256 = expected_coordinate_sha256
        self.members = {}

    def validators(self, returned, existing=None):
        validators = {} if existing is None else dict(existing)
        names = {PurePosixPath(row.relative_path).name for row in returned.files.files}
        required = {'original.prmtop': 256*2**20,
                    'coordinate-array.npy': len(self.representation.atoms)*24+4096}
        if returned.error is None and set(required)-names:
            raise ValueError('successful periodic return omits complete geometry operands')
        for name, maximum in required.items():
            if name not in names:
                continue
            previous = validators.get(name)
            def capture(raw, name=name, previous=previous):
                if previous is not None:
                    previous[1](raw)
                self.members[name] = raw
            validators[name] = (maximum if previous is None else min(maximum, previous[0]), capture)
        return validators

    def assess(self):
        import numpy as np
        model, members = self.representation, self.members
        digest = None
        if 'original.prmtop' in members and sha256(members['original.prmtop']).hexdigest() != model.raw_topology.object_fingerprint:
            raise ValueError('retained geometry substitutes original topology bytes')
        if 'coordinate-array.npy' in members:
            stream = io.BytesIO(members['coordinate-array.npy'])
            xyz = np.load(stream, allow_pickle=False)
            if (stream.read(1) or xyz.dtype.str != '<f8' or xyz.shape != (len(model.atoms), 3)
                    or not np.isfinite(xyz).all()):
                raise ValueError('retained geometry omits complete finite physical coordinates')
            digest = sha256(xyz.tobytes(order='C')).hexdigest()
            if digest != self.expected_coordinate_sha256:
                raise ValueError('retained geometry substitutes selected physical coordinates')
        if {'original.prmtop', 'coordinate-array.npy'} - set(members):
            return RetainedMolecularGeometryAssessment(model.identity, model.raw_topology, len(model.atoms), digest, self.policy,
                'UNEVALUABLE', ('missing-whole-molecule-geometry-operands',), (), (), self.qm_atoms)
        try:
            terms = bound_geometry_terms(model, members['original.prmtop'])
        except ValueError:
            return RetainedMolecularGeometryAssessment(model.identity, model.raw_topology, len(model.atoms), digest, self.policy,
                'UNEVALUABLE', ('unsupported-whole-molecule-geometry-source',), (), (), self.qm_atoms)
        report = assess_molecular_geometry(xyz, terms, policy=self.policy,
            cell_angstrom=tuple(map(float, self.cell.lengths_angstrom)), exempt_bonded_atoms=self.qm_atoms)
        census = dict(report['counts'], gross_contact_pairs=report['gross_contact_pairs'],
            contact_candidates=report['contact_candidates'])
        return RetainedMolecularGeometryAssessment(model.identity, model.raw_topology, len(model.atoms), digest, self.policy,
            report['disposition'], tuple(report['findings']), tuple(sorted(census.items())),
            tuple(sorted((name, Decimal(str(value))) for name, value in report['metrics'].items())), self.qm_atoms)
