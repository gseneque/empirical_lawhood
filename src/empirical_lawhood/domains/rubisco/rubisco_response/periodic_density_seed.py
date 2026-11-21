"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import CoupledEvaluationRequest
from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.execution.native_subwork import NativeSubworkDefinition
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection


DENSITY_SCHEMA = 'empirical-lawhood/rubisco-response/checkpoint-density-f64'


MAX_DENSITY_BYTES = 128 * 2**20


MAX_CHECKPOINT_BYTES = 256 * 2**20


SCOPE = 'INITIAL_DENSITY_ONLY_WITHOUT_CONVERGENCE_OR_ORIGINAL_COMPLETION'


@dataclass(frozen=True, slots=True)
class PeriodicDensitySeed(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-density-seed'
    seed_id: str
    source_configuration: ObjectIdentity
    prototype: PeriodicProbeSelection
    source_provenance: NumericalProducingProvenance
    source_definition: NativeSubworkDefinition
    checkpoint: FileEvidence
    checkpoint_energy_hartree: Decimal
    molecule_sha256: str
    arrays: ArrayDatasetManifest
    density_bytes: ObjectIdentity
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.seed_id)
        for value, kind in ((self.source_configuration, ObjectIdentity), (self.prototype, PeriodicProbeSelection),
                (self.source_provenance, NumericalProducingProvenance), (self.source_definition, NativeSubworkDefinition),
                (self.checkpoint, FileEvidence), (self.arrays, ArrayDatasetManifest), (self.density_bytes, ObjectIdentity)):
            exact(value, kind)
        validate_sha256(self.molecule_sha256)
        prototype, provenance, definition = self.prototype, self.source_provenance, self.source_definition
        request = CoupledEvaluationRequest(prototype.probe.probe_id+'.evaluation', prototype.probe.identity,
            prototype.representation, prototype.coordinates.identity, provenance.identity,
            prototype.physical_atom_count, gradient_unit='Eh/PySCF-Bohr-0.52917721092-A')
        if (self.source_configuration.object_schema != 'empirical-lawhood/rubisco-response/periodic-probe-config'
                or self.source_configuration.object_version != '1.0.0'
                or definition.configuration != request.identity
                or definition.operation_id != 'rubisco-response.molecular-force-probe'
                or definition.code_sources_sha256 != provenance.code_sources_sha256
                or definition.dependency_lock_sha256 != provenance.dependency_lock_sha256
                or not {self.source_configuration, prototype.probe.identity, prototype.representation,
                    prototype.coordinates.identity, provenance.identity}.issubset(definition.sources)
                or type(self.checkpoint_energy_hartree) is not Decimal or not self.checkpoint_energy_hartree.is_finite()
                or type(self.checkpoint.byte_count) is not int or not 0 < self.checkpoint.byte_count <= MAX_CHECKPOINT_BYTES
                or len(self.arrays.members) != 1 or self.scope != SCOPE):
            raise ValueError('density seed changes its complete original attempt, source or initial-guess scope')
        member = self.arrays.members[0]
        dimensions = 2 if prototype.electronic.ks_flavour == 'RKS' else 3
        if (member.name != 'initial-density' or member.dtype != '<f8' or not member.finite_required
                or len(member.shape) != dimensions or member.shape[-1] != member.shape[-2]
                or member.shape[-1] <= 0 or dimensions == 3 and member.shape[0] != 2
                or not 0 < self.arrays.size_bytes <= MAX_DENSITY_BYTES
                or self.arrays.scientific_references != tuple(sorted(
                    {prototype.identity, self.source_configuration, definition.identity}, key=lambda row:row.object_id))
                or self.density_bytes.object_schema != DENSITY_SCHEMA or self.density_bytes.object_version != '1.0.0'
                or member.sha256 != self.density_bytes.object_fingerprint):
            raise ValueError('density seed changes its complete binary64 AO density contract')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.seed_id, self)


def validate_density_prototype(seed, prototype, *, allow_backend_change=False):
    """Only producing software and the selected thread count may differ."""
    exact(seed, PeriodicDensitySeed)
    exact(prototype, PeriodicProbeSelection)
    prior = seed.prototype
    if any(getattr(prototype, key) != getattr(prior, key) for key in (
            'representation', 'coordinates', 'physical_atom_count', 'path', 'cell', 'electronic', 'molecular')):
        raise ValueError('density seed belongs to a changed molecular, coordinate or physical operator context')
    if type(allow_backend_change) is not bool:
        raise TypeError('density backend migration requires an explicit boolean')
    if allow_backend_change:
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
        if not accelerated_engine(prototype.engine):
            raise ValueError('density backend migration requires the explicit accelerated numerical engine')
        # The original engine remains bound in the seed. Actual entry still
        # checks exact geometry, basis, ordered AO signature and populations.
        return
    if any(getattr(prototype.engine, key) != getattr(prior.engine, key) for key in (
            'site_packages', 'files', 'interpreter', 'interpreter_sha256')):
        raise ValueError('density seed belongs to a changed numerical engine stock')


def read_density_bytes(seed, raw):
    """Use one immutable binary backing allocation, without JSON numeric copies."""
    import numpy as np
    exact(seed, PeriodicDensitySeed)
    if (type(raw) is not bytes or len(raw) != seed.arrays.size_bytes
            or sha256(raw).hexdigest() != seed.density_bytes.object_fingerprint):
        raise ValueError('density seed substitutes its exact original binary array')
    member = seed.arrays.members[0]
    density = np.frombuffer(raw, dtype=member.dtype).reshape(member.shape)
    if (not np.isfinite(density).all()
            or float(np.max(np.abs(density-density.swapaxes(-1, -2)))) > 1e-10):
        raise ValueError('density seed must be complete, finite and symmetric')
    return density


def density_electron_populations(density, overlap, expected):
    """Validate selected spin populations in supplied AO density and overlap arrays."""
    import numpy as np
    populations = np.einsum('...ij,ji->...', density, overlap)
    if not np.isfinite(populations).all() or float(np.max(np.abs(populations-expected))) > 1e-7:
        raise ValueError('density seed changes the selected electron or spin population')
    return np.atleast_1d(populations).tolist()
