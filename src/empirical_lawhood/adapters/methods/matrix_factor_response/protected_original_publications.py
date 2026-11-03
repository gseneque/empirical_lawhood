# SPDX-License-Identifier: MPL-2.0
"""Explicit original E3 byte custody, separate from source eligibility.

The three explicit canonical publications carry no population, signer or
authority. The current census retains content-pinned external factual provenance;
its custody does not certify completeness, independence or qualification.
"""
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import exposure_census_publication

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.time import AvailabilitySpec, InformationCutoff
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteResult
from empirical_lawhood.runtime.recursive_compiler import RegisteredPublicationRequirement

from .experiment_specification import MatrixResponseErrorSpecification
from .protected_source_records import ProtectedE3NativeSourceManifest, _reference, identity

from .protected_input_custody import authenticate_original_artifact, require_original_publication_metadata

from .protected_input_custody import read_protected_e3_original_publication as _canonical_original

PUBLICATION_KEYS = ("allocation", "native-selection", "reservation", "roles")


def _publication_metadata(publication):
    return require_original_publication_metadata(publication)


def _canonical_reference(publication, reference):
    _publication_metadata(publication)
    if (publication.logical.payload_schema, publication.logical.content_sha256, publication.logical.profile,
            publication.logical.media_type) != (reference.object_schema, reference.object_fingerprint,
                ArtifactProfile.CANONICAL_JSON, "application/json"):
        raise ValueError("protected E3 original locator changes its exact canonical reference")


@dataclass(frozen=True, slots=True)
class ProtectedE3OriginalPublications(CanonicalRecord):
    VERSION: ClassVar[str] = "2.0.0"
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-original-publications"
    record_id: str
    specification: ObjectIdentity
    source_manifest: ObjectIdentity
    training_allocation: ObjectIdentity
    manifest_publication: ArtifactWriteResult
    training_allocation_publication: ArtifactWriteResult
    exposure_census_publication: ArtifactWriteResult

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for reference, kind in ((self.specification, MatrixResponseErrorSpecification),
                (self.source_manifest, ProtectedE3NativeSourceManifest), (self.training_allocation, UnitAllocation)):
            _reference(reference, kind)
        _canonical_reference(self.manifest_publication, self.source_manifest)
        _canonical_reference(self.training_allocation_publication, self.training_allocation)
        _publication_metadata(self.exposure_census_publication)




def load_protected_e3_originals(plane, originals):
    """Resolve only the two explicit canonical metadata publications, never TRAIN."""
    if type(originals) is not ProtectedE3OriginalPublications:
        raise TypeError("protected E3 original loading requires its exact global custody carrier")
    originals.__post_init__()
    manifest = _canonical_original(plane, originals.manifest_publication, ProtectedE3NativeSourceManifest)
    training = _canonical_original(plane, originals.training_allocation_publication, UnitAllocation)
    if identity(manifest) != originals.source_manifest or training.identity != originals.training_allocation:
        raise ValueError("protected E3 original publications substitute their actual record identities")
    return manifest, training


def _authenticate_artifact(plane, artifact, custody):
    return authenticate_original_artifact(plane, artifact, custody)


def authenticate_protected_e3_fit_originals(plane, originals, *, specification, allocation,
        source_manifest, training_allocation, publications, fit_cutoff):
    """Authenticate complete declared original byte custody before any TRAIN loader.

    Availability/cutoff values are frozen declarations, not filesystem-time
    certificates. Full source truth, current qualification and authority still
    belong to the owning candidate/current-task services.
    """
    if (type(originals) is not ProtectedE3OriginalPublications or
            (originals.specification, originals.source_manifest, originals.training_allocation) !=
            (specification, source_manifest, training_allocation)):
        raise ValueError("protected E3 fit substitutes its global original-publication references")
    _reference(allocation, UnitAllocation)
    if (type(publications) is not tuple or tuple(row[0] for row in publications) != PUBLICATION_KEYS
            or type(fit_cutoff) is not InformationCutoff):
        raise ValueError("protected E3 original custody requires all four exact fit publications and cutoff")
    fit_cutoff.__post_init__()
    for _, publication, availability in publications:
        _publication_metadata(publication)
        if type(availability) is not AvailabilitySpec:
            raise TypeError("protected E3 fit requires exact frozen publication availability")
        availability.__post_init__()
        fit_cutoff.require_allows(availability)
        if availability.outcome_access is not publication.logical.outcome_access:
            raise ValueError("protected E3 fit availability relabels original publication access")
    manifest, training = load_protected_e3_originals(plane, originals)
    expected = {"allocation": (manifest.reservation.allocation, manifest.reservation.publication),
        "native-selection": (manifest.native_specification.selection, manifest.native_specification.publication),
        "reservation": (manifest.reservation, manifest.reservation_publication)}
    for key, publication, _ in publications:
        if key == "roles":
            roles = _canonical_original(plane, publication, UnitAllocation)
            if roles.identity != allocation:
                raise ValueError("protected E3 fit roles publication changes its exact selected allocation")
        else:
            record, original = expected[key]
            if publication != original:
                raise ValueError("protected E3 fit substitutes its actual original manifest publication")
            authenticate_publication(plane, publication, record)
    authenticate_publication(plane, manifest.audit_publication, manifest.audit)
    for publication in manifest.audit.prior_corpus:
        record, = (row for row in (manifest.audit.census, *manifest.audit.prior_scheduled_coordinates)
            if (row.SCHEMA, row.fingerprint()) == (publication.logical.payload_schema, publication.logical.content_sha256))
        authenticate_publication(plane, publication, record)
    authenticate_publication(plane, manifest.scalar_definition_publication, manifest.scalar_definition)
    census = manifest.reservation.allocation.exposure.census
    if originals.exposure_census_publication != exposure_census_publication(manifest.audit):
        raise ValueError("protected E3 substitutes its exact current census publication")
    authenticate_publication(plane, originals.exposure_census_publication, census)
    return manifest, training


def authenticate_protected_e3_fit_config(plane, config):
    """Resolve the current typed fit's explicit global original metadata carrier."""
    from .protected_statistical_bindings import ProtectedE3FitConfig

    if type(config) is not ProtectedE3FitConfig:
        raise TypeError("protected E3 original custody requires its actual current fit configuration")
    originals = getattr(config, "original_publications", None)
    if type(originals) is not ProtectedE3OriginalPublications:
        raise ValueError("SOFTWARE: protected E3 fit has no bound global original-publication custody carrier")
    config.__post_init__()
    return authenticate_protected_e3_fit_originals(plane, originals, specification=config.specification,
        allocation=config.allocation, source_manifest=config.source_manifest,
        training_allocation=config.training_allocation, publications=config.publications, fit_cutoff=config.fit_cutoff)


def authenticate_protected_e3_original_publications(plane, config_inputs):
    """Cold registered callback; no API authentication callable enters a worker."""
    from .protected_statistical_bindings import ProtectedE3FitConfig

    configs = tuple(row.record for row in config_inputs if type(row.record) is ProtectedE3FitConfig)
    if not configs:
        return
    if len(configs) != 1:
        raise ValueError("protected E3 requires one global original fit publication binding")
    authenticate_protected_e3_fit_config(plane, configs[0])


ORIGINAL_PUBLICATION_REQUIREMENT = RegisteredPublicationRequirement(
    "matrix-e3-protected.original-publication-custody.v1", authenticate_protected_e3_original_publications)
