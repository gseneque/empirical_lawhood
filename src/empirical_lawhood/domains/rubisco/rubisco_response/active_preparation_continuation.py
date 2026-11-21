# SPDX-License-Identifier: MPL-2.0
"""Continuation from receipted prefix operands, never from uncertain scratch."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import PurePosixPath
import re
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import ActivePreparationPrefixConfig, AcceleratedActivePreparationPrefixConfig
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact

CAPABILITY = 'rubisco-response.continue-active-preparation-prefix'
GPU_CAPABILITY = 'rubisco-response.accelerated-continue-active-preparation-prefix'


@dataclass(frozen=True, slots=True)
class ActivePreparationContinuation(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-continuation'
    continuation_id: str
    previous: (ActivePreparationPrefixConfig | AcceleratedActivePreparationPrefixConfig |
               ContinuedActivePreparationPrefixConfig | AcceleratedContinuedActivePreparationPrefixConfig)
    readout: ActivePreparationPrefixReadout
    archive: ArtifactManifest
    remaining_allowance: int
    parent: ContributionManifest | None = None
    electronic_initialization: str = 'RESTARTED_INITIALIZATION'

    def __post_init__(self):
        validate_stable_id(self.continuation_id)
        if type(self.previous) not in (*base_config_types(), *continuation_config_types()):
            raise TypeError('preparation continuation requires its exact previous configuration')
        exact(self.readout, ActivePreparationPrefixReadout)
        exact(self.archive, ArtifactManifest)
        original = self.readout.original_result
        assessment = self.readout.assessment
        if (original.configuration != original_configuration(self.previous) or original.prefix != self.previous.prefix
                or original.model_name != self.previous.original.model_name
                or self.previous.identity not in original.unit.definition.sources
                or assessment is None or self.readout.assessment_error is not None
                or assessment.configuration != original.configuration
                or not assessment.complete_native_return_ledger or not assessment.evaluations):
            raise ValueError('preparation continuation requires an authenticated complete return ledger; unknown contact stays unresolved')
        expected = (0 if original.unit.returned.error is None else
                    self.previous.prefix.allowance_for(original.model_name) - len(assessment.evaluations))
        if (type(self.remaining_allowance) is not int or self.remaining_allowance != expected or expected < 0
                or self.electronic_initialization != 'RESTARTED_INITIALIZATION'):
            raise ValueError('preparation continuation changes remaining original allowance or electronic initialization')
        receipt = original.unit.receipt
        if (self.archive.logical not in receipt.output_logical_artifacts
                or self.archive.materialization not in receipt.output_materializations
                or not self.archive.logical.logical_artifact_id.endswith('.output.files.raw')
                or self.archive.logical.media_type != 'application/gzip'
                or not self.archive.materialization.size_bytes > 0):
            raise ValueError('preparation continuation lacks the complete original receipt-bound native archive')
        if self.parent is not None:
            exact(self.parent, ContributionManifest)
            if len([p for p in self.parent.products if p.record == self.readout.identity]) != 1:
                raise ValueError('preparation continuation changes the original supplier contribution')
        if self.previous.scientific_context is not None and self.parent is None:
            raise ValueError('rooted preparation continuation requires its actual original contribution')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.continuation_id, self)

    @property
    def archive_identity(self):
        logical = self.archive.logical
        return ObjectIdentity(logical.logical_artifact_id, logical.payload_schema, '1.0.0',
                              self.archive.materialization.physical_sha256)


def _validate_continued_config(config):
    exact(config.continuation, ActivePreparationContinuation)
    previous = config.continuation.previous
    expected = replace(previous.original, work_directory=config.original.work_directory)
    if (config.original != expected or config.prefix != previous.prefix
            or config.scientific_context != previous.scientific_context
            or config.ACCELERATED != previous.ACCELERATED
            or config.original.work_directory == previous.original.work_directory):
        raise ValueError('preparation continuation changes original state, source, threads, allowance or custody')


@dataclass(frozen=True, slots=True, kw_only=True)
class ContinuedActivePreparationPrefixConfig(ActivePreparationPrefixConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/continued-active-preparation-prefix-config'
    continuation: ActivePreparationContinuation

    def __post_init__(self):
        ActivePreparationPrefixConfig.__post_init__(self)
        _validate_continued_config(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class AcceleratedContinuedActivePreparationPrefixConfig(AcceleratedActivePreparationPrefixConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/accelerated-continued-active-preparation-prefix-config'
    continuation: ActivePreparationContinuation

    def __post_init__(self):
        ActivePreparationPrefixConfig.__post_init__(self)
        _validate_continued_config(self)


def base_config_types():
    return ActivePreparationPrefixConfig, AcceleratedActivePreparationPrefixConfig


def continuation_config_types():
    return ContinuedActivePreparationPrefixConfig, AcceleratedContinuedActivePreparationPrefixConfig


def original_prefix_config(config):
    """Return the unchanged first configuration beneath explicit continuations."""
    while type(config) in continuation_config_types():
        config = config.continuation.previous
    return config


def original_configuration(config):
    """Keep every evaluation and checkpoint bound to the frozen original prefix."""
    return original_prefix_config(config).identity


def prepare_continuation(*, previous, readout, archive, parent=None):
    if readout.assessment is None:
        raise ValueError('preparation continuation requires its original independent readout')
    remaining = (0 if readout.original_result.unit.returned.error is None else
                 previous.prefix.allowance_for(previous.original.model_name) - len(readout.assessment.evaluations))
    record = ActivePreparationContinuation('continuation.active-prefix.pending', previous, readout, archive, remaining, parent)
    return replace(record, continuation_id='continuation.active-prefix.' + record.fingerprint())


def read_continuation_files(continuation, raw, *, representation, prepared, coordinate_bytes):
    """Authenticate complete captured bytes before reconstructing optimizer state."""
    import numpy  # noqa: F401 -- Load the numerical backend before restoring its original setting.
    from threadpoolctl import threadpool_limits
    exact(continuation, ActivePreparationContinuation)
    with threadpool_limits(limits=continuation.previous.original.prototype.engine.numerical_threads):
        return _read_continuation_files(continuation, raw, representation=representation,
            prepared=prepared, coordinate_bytes=coordinate_bytes)


def _read_continuation_files(continuation, raw, *, representation, prepared, coordinate_bytes):
    from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_read import authenticate_relaxation_archive
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import assess_preparation_files
    exact(continuation, ActivePreparationContinuation)
    materialization = continuation.archive.materialization
    if (type(raw) is not bytes or len(raw) != materialization.size_bytes
            or sha256(raw).hexdigest() != materialization.physical_sha256):
        raise ValueError('preparation continuation substitutes complete original archive bytes')
    original = continuation.readout.original_result
    names = frozenset(PurePosixPath(row.relative_path).name for row in original.unit.returned.files.files)
    files, _, exceeds = authenticate_relaxation_archive(
        (raw[offset:offset + 2**20] for offset in range(0, len(raw), 2**20)),
        original.unit.definition, original.unit.returned, original.unit.returned.files.canonical_bytes(),
        endpoint_members=names, maximum_endpoint_bytes=None, retain_failed_members=True)
    if exceeds:
        raise ValueError('preparation continuation exceeds its complete original operand envelope')
    assessment, arrays, evaluations = assess_preparation_files(config=continuation.previous,
        representation=representation, prepared=prepared, coordinate_bytes=coordinate_bytes, files=files,
        assessor_source=continuation.readout.assessment.assessor_source)
    if assessment != continuation.readout.assessment or not assessment.complete_native_return_ledger:
        raise ValueError('preparation continuation disagrees with its original independent readout')
    state = None
    if assessment.checkpoints:
        from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import read_checkpoint_arrays
        checkpoint = assessment.checkpoints[-1].checkpoint
        state = read_checkpoint_arrays(checkpoint, arrays[checkpoint.identity],
            configuration=original_configuration(continuation.previous), seed=checkpoint.seed, prototype=checkpoint.prototype)
    # Preserve the entire original archive as an input. Only sealed evaluations
    # and checkpoints become mutable work-directory copies. An unsealed
    # checkpoint tail has no accepted-state meaning and is reconstructed by replay.
    stems = {f'evaluation-{r.ordinal:08d}' for r in assessment.evaluations}
    stems.update(f'accepted-{r.checkpoint.iterations:08d}' for r in assessment.checkpoints)
    retained = {name: body for name, body in files.items()
        if name in ('native-observations.jsonl', 'relaxation-evaluations.jsonl')
        or re.fullmatch(r'(accepted|evaluation)-\d{8}(\.[a-z-]+\.npy|\.json)', name)
        and name.split('.')[0] in stems}
    return dict(state=state, evaluations=evaluations, files=retained, continuation=continuation)
