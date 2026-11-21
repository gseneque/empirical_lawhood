# SPDX-License-Identifier: MPL-2.0
"""Independent numerical and geometric reading of original gas-start endpoints."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_assessment import assess_coupled_relaxation_trace, assess_endpoint_trace, endpoint_geometry, read_endpoint_arrays
from empirical_lawhood.domains.rubisco.rubisco_response.gas_relaxation_selection import validate_gas_relaxation_model
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


@dataclass(frozen=True, slots=True)
class GasRelaxationAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-relaxation-assessment'
    selection: ObjectIdentity
    assessor_source: ObjectIdentity
    disposition: str
    findings: tuple[str, ...]
    complete_reference_evaluations: int
    physical_atoms: int
    maximum_gradient_kj_mol_nm: Decimal
    initial_energy_hartree: Decimal
    final_energy_hartree: Decimal
    nearest_water_magnesium_angstrom: Decimal
    stereocentres_checked: int
    host_state_retained: bool
    # Every unordered gas pair: native first index, second index, distance.
    gas_internal_distances_angstrom: tuple[tuple[int, int, Decimal], ...]
    # Each gas atom: native index, nearest host/distance, nearest heavy host/distance.
    gas_host_contacts_angstrom: tuple[tuple[int, int, Decimal, int, Decimal], ...]
    # Each gas atom's separation from the selected substrate C2.
    gas_c2_distances_angstrom: tuple[tuple[int, int, Decimal], ...]
    gas_basin_admission: str = 'UNEVALUABLE'
    electronic_character_admission: str = 'UNEVALUABLE'
    equilibrium_population: str = 'UNEVALUABLE'
    force_accuracy: str = 'UNEVALUABLE'
    rate_admission: str = 'UNEVALUABLE'

    def __post_init__(self):
        for value in (self.selection, self.assessor_source):
            exact(value, ObjectIdentity)
        if (type(self.findings) is not tuple or self.findings != tuple(sorted(set(self.findings)))
                or self.disposition != ('FALSIFIED' if self.findings else 'SATISFIED')
                or any(type(n) is not int or n < 0 for n in (
                    self.complete_reference_evaluations, self.physical_atoms, self.stereocentres_checked))
                or self.complete_reference_evaluations < 2 or self.physical_atoms < 3
                or type(self.host_state_retained) is not bool
                or self.host_state_retained != (not bool(set(self.findings) & {
                    'proton-allocation-escaped', 'magnesium-water-state-escaped', 'catalytic-heavy-bond-broken'}))
                or any(getattr(self, name) != 'UNEVALUABLE' for name in ('gas_basin_admission',
                    'electronic_character_admission', 'equilibrium_population', 'force_accuracy', 'rate_admission'))):
            raise ValueError('gas endpoint changes its complete findings, state retention or scientific scope')
        for finding in self.findings:
            validate_stable_id(finding)
        for name in ('maximum_gradient_kj_mol_nm', 'nearest_water_magnesium_angstrom'):
            validate_decimal(getattr(self, name), field_name=name, minimum=Decimal(0))
        for name in ('initial_energy_hartree', 'final_energy_hartree'):
            validate_decimal(getattr(self, name), field_name=name)
        contacts = self.gas_host_contacts_angstrom
        if type(contacts) is not tuple or len(contacts) not in (2, 3):
            raise ValueError('gas endpoint loses its complete gas contact census')
        n = self.physical_atoms-len(contacts)
        expected = tuple(range(n, self.physical_atoms))
        if tuple(row[0] for row in contacts) != expected:
            raise ValueError('gas endpoint substitutes an appended physical gas atom')
        for gas, nearest, distance, heavy, heavy_distance in contacts:
            if any(type(i) is not int or not 0 <= i < n for i in (nearest, heavy)):
                raise ValueError('gas endpoint contact does not select an original host atom')
            for value in (distance, heavy_distance):
                validate_decimal(value, field_name='gas_host_distance_angstrom', minimum=Decimal(0))
        if (type(self.gas_internal_distances_angstrom) is not tuple
                or tuple((a, b) for a, b, _ in self.gas_internal_distances_angstrom)
                    != tuple((a, b) for a in expected for b in expected if a < b)
                or type(self.gas_c2_distances_angstrom) is not tuple
                or tuple(row[0] for row in self.gas_c2_distances_angstrom) != expected
                or len({row[1] for row in self.gas_c2_distances_angstrom}) != 1):
            raise ValueError('gas endpoint omits an internal or reaction-coordinate distance')
        for _, c2, distance in self.gas_c2_distances_angstrom:
            if type(c2) is not int or not 0 <= c2 < n:
                raise ValueError('gas endpoint substitutes the host reactive centre')
        for _, _, distance in (*self.gas_internal_distances_angstrom, *self.gas_c2_distances_angstrom):
            validate_decimal(distance, field_name='gas_distance_angstrom', minimum=Decimal(0))


def observe_gas_endpoint_geometry(*, selection, representation, final):
    """Report complete periodic contacts without inventing gas-basin thresholds."""
    import numpy as np

    n = selection.augmentation.original_atom_count
    gas = selection.prototype.path.gas_atom_indices
    box = np.asarray(tuple(map(float, selection.prototype.cell.lengths_angstrom)))
    heavy = np.asarray([i for i, atom in enumerate(representation.atoms[:n]) if atom.atomic_number != 1])
    graph = next(g for g in selection.protocol.graphs if g.identity == selection.seed.graph)
    c2 = next(selection.site.core_atom_indices[i] for i, atom in enumerate(graph.atoms) if atom.label == 'ligand.C2')

    def distance(a, b):
        delta = a-b
        return np.linalg.norm(delta-box*np.floor(delta/box+.5), axis=-1)

    contacts = []
    for i in gas:
        distances = distance(final[:n], final[i])
        nearest, nearest_heavy = int(np.argmin(distances)), int(heavy[np.argmin(distances[heavy])])
        contacts.append((i, nearest, Decimal(str(float(distances[nearest]))),
            nearest_heavy, Decimal(str(float(distances[nearest_heavy])))))
    internal = tuple((a, b, Decimal(str(float(distance(final[a], final[b]))))) for a in gas for b in gas if a < b)
    reactive = tuple((i, c2, Decimal(str(float(distance(final[i], final[c2]))))) for i in gas)
    return internal, tuple(contacts), reactive


def assess_gas_relaxation_endpoint(*, selection, representation, files, assessor_source):
    """Use retained arrays and original selections; perform no force or minimization."""
    validate_gas_relaxation_model(selection, representation)
    prototype, settings = selection.prototype, selection.settings
    initial, final, gradient, energy = read_endpoint_arrays(files, atom_count=len(representation.atoms))
    if (files['gas-selection.json'] != selection.canonical_bytes()
            or sha256(initial.tobytes()).hexdigest() != prototype.coordinates.members[0].sha256):
        raise ValueError('gas endpoint substitutes its complete initial coordinates or prospective selection')
    bindings = json.loads(files['source-bindings.json'])
    if bindings != dict(selection=selection.identity.to_document(), representation=representation.identity.to_document(),
            prototype=prototype.identity.to_document(), original_host=selection.augmentation.original_representation.to_document(),
            selected_seed=selection.seed.identity.to_document(), topology_sha256=representation.raw_topology.object_fingerprint,
            coordinate_source_sha256=representation.raw_coordinates.object_fingerprint,
            initial_coordinate_sha256=prototype.coordinates.members[0].sha256,
            physical_atoms=len(initial), gas_atom_indices=list(prototype.path.gas_atom_indices),
            cell=prototype.cell.to_document(), scope=selection.scope):
        raise ValueError('gas endpoint changes its exact original source and electronic selection')
    count, maximum, first, findings = assess_endpoint_trace(files, initial=initial, final=final,
        gradient=gradient, energy=energy, settings=settings,
        electronic_energy_tolerance_hartree=prototype.electronic.energy_tolerance_hartree)
    findings |= assess_coupled_relaxation_trace(prototype=prototype, files=files,
        physical_atoms=len(initial), evaluations=count)
    geometry, water, stereo = endpoint_geometry(representation=representation, site=selection.site,
        protocol=selection.protocol, seed=selection.seed, original=initial, final=final, cell=prototype.cell, settings=settings)
    findings |= geometry
    internal, contacts, reactive = observe_gas_endpoint_geometry(selection=selection, representation=representation, final=final)
    return GasRelaxationAssessment(selection.identity, assessor_source, 'FALSIFIED' if findings else 'SATISFIED',
        tuple(sorted(findings)), count, len(initial), Decimal(str(maximum)), Decimal(str(first)), Decimal(str(float(energy))),
        Decimal(str(water)), stereo, not bool(findings & {
            'proton-allocation-escaped', 'magnesium-water-state-escaped', 'catalytic-heavy-bond-broken'}), internal, contacts, reactive)
