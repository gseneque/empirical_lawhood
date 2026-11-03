# SPDX-License-Identifier: MPL-2.0
"""Configured native-source selection; original physical manifests stay exact."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ResolvedScheduledSource, ScheduledSourceIndex
from .configured_protected_specification import ConfiguredProtectedE3Specification as MatrixResponseErrorSpecification
from .configured_protected_tasks import NAMESPACE
def _selected(specification):
    if type(specification) is not MatrixResponseErrorSpecification:
        raise TypeError("configured source needs its exact prospective specification")
    specification.__post_init__()

from .protected_source_records import ProtectedE3NativeSourceManifest, ProtectedE3SourcePhase, _reference, identity

def source_task_id(root_id: str, phase: ProtectedE3SourcePhase) -> str:
    validate_stable_id(root_id)
    if type(phase) is not ProtectedE3SourcePhase:
        raise TypeError("protected E3 source task requires its closed phase")
    return NAMESPACE + "." + root_id + "." + phase.value

def prefix_native_operation_id() -> str:
    return NAMESPACE + ".prefix-before-continuation.v2"

@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3SourceConfig(CanonicalRecord):
    """Native/source phases only; contains one root's actual four streams."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/configured-protected-source-config"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    phase: ProtectedE3SourcePhase
    specification: ObjectIdentity
    source_manifest: ObjectIdentity
    source: ScheduledSource

    def __post_init__(self):
        _reference(self.specification, MatrixResponseErrorSpecification)
        _reference(self.source_manifest, ProtectedE3NativeSourceManifest)
        if type(self.source) is not ScheduledSource:
            raise TypeError("protected E3 config requires an exact compact original source")
        self.source.__post_init__()
        if (self.source.root.root.role not in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION)
                or self.record_id != "config." + source_task_id(self.source.root_id, self.phase)):
            raise ValueError("protected E3 config changes its declaration-owned root/phase identity")

def bind_protected_e3_source(config: ConfiguredProtectedE3SourceConfig, manifest: ProtectedE3NativeSourceManifest,
        *, specification: MatrixResponseErrorSpecification) -> ResolvedScheduledSource:
    """Resolve the bounded source against its exact shared scientific parents.

    The complete candidate/role projection is a separate root validation. This
    local join establishes exact supplied originals, not their qualification.
    """
    _selected(specification)
    if type(config) is not ConfiguredProtectedE3SourceConfig or type(manifest) is not ProtectedE3NativeSourceManifest:
        raise TypeError("protected E3 source binding requires exact compact config and manifest")
    config.__post_init__()
    manifest.__post_init__()
    if config.specification != specification.identity or config.source_manifest != identity(manifest):
        raise ValueError("protected E3 source binding changes selected specification or shared manifest")
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    return index.resolve(config.source)

from .configured_protected_response_selection import ConfiguredProtectedE3ResponseSelection as ConfiguredProtectedE3ResponseSelection
