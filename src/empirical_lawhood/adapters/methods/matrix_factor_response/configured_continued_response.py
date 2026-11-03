# SPDX-License-Identifier: MPL-2.0
"""New response contracts with explicit original-prefix and current-source joins."""
from dataclasses import dataclass, replace
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile

from .configured_protected_feature_bindings import ConfiguredProtectedE3FeatureConfig
from .configured_protected_response_records import ConfiguredProtectedE3NativeResponse, ConfiguredProtectedE3ResponseConfig
from .configured_protected_source_records import _reference
from .configured_retained_execution import ConfiguredE3RetainedExecution, source_binding


@dataclass(frozen=True, slots=True)
class ConfiguredE3ContinuedResponseConfig(ConfiguredProtectedE3ResponseConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-continued-response-config'
    continuation: ObjectIdentity

    def __post_init__(self):
        super(ConfiguredE3ContinuedResponseConfig, self).__post_init__()
        _reference(self.continuation, ConfiguredE3RetainedExecution)


@dataclass(frozen=True, slots=True)
class ConfiguredE3ContinuedNativeResponse(ConfiguredProtectedE3NativeResponse):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-continued-native-responses'
    CONFIGURATION_TYPE: ClassVar[type] = ConfiguredE3ContinuedResponseConfig
    continuation: ObjectIdentity

    def __post_init__(self):
        super(ConfiguredE3ContinuedNativeResponse, self).__post_init__()
        _reference(self.continuation, ConfiguredE3RetainedExecution)


@dataclass(frozen=True, slots=True)
class ConfiguredE3ContinuedFeatureConfig(ConfiguredProtectedE3FeatureConfig):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-continued-feature-config'
    continuation: ObjectIdentity

    def __post_init__(self):
        super(ConfiguredE3ContinuedFeatureConfig, self).__post_init__()
        _reference(self.continuation, ConfiguredE3RetainedExecution)


def original_config(config):
    """Return only the original frozen science, without discarding the carrier."""
    from .configured_retained_execution import ConfiguredE3RetainedTaskConfig
    from .configured_closeout_execution import ConfiguredE3MissingOutcomeConfig
    if type(config) is ConfiguredE3RetainedTaskConfig:
        return config.original_config
    base = (ConfiguredProtectedE3ResponseConfig if type(config) in (ConfiguredE3ContinuedResponseConfig, ConfiguredE3MissingOutcomeConfig) else
        ConfiguredProtectedE3FeatureConfig if type(config) is ConfiguredE3ContinuedFeatureConfig else None)
    if base is None:
        return config
    from dataclasses import fields
    return base(**{field.name: getattr(config, field.name) for field in fields(base)})


def require_response_retention(config, retention, *, source=None, run_id=None, response=None):
    """A strict new contract; the original edition never accepts a transition."""
    if type(config) is ConfiguredProtectedE3ResponseConfig:
        if retention is not None or response is not None and type(response) is not ConfiguredProtectedE3NativeResponse:
            raise ValueError('original E3 response cannot acquire a source continuation')
        return None
    if type(config) is not ConfiguredE3ContinuedResponseConfig or type(retention) is not ConfiguredE3RetainedExecution:
        raise TypeError('continued E3 response requires its exact config and retained execution')
    if (config.continuation != retention.identity or config.specification != retention.specification
            or source is not None and source_binding(source.provenance) != retention.original_source
            or run_id is not None and run_id != retention.continued_run_id):
        raise ValueError('continued E3 response substitutes original science/source or continued run')
    if response is not None and (type(response) is not ConfiguredE3ContinuedNativeResponse
            or response.continuation != retention.identity):
        raise ValueError('continued E3 response drops its exact source continuation')
    return retention


def retained_array_port(port, original, *, producer, retention, context):
    """Verify a current copy, then expose its original ID only to the reader.

    The prepared invocation and dependency ports retain their current IDs. The
    private read view preserves the exact original canonical array record.
    """
    if type(retention) is not ConfiguredE3RetainedExecution or context.run_id != retention.continued_run_id:
        raise ValueError('retained E3 array read requires its explicit continued execution')
    artifact = original.array_artifact
    if (dict(retention.retained_arrays).get(producer) != artifact
            or port.artifact_id != 'artifact.' + context.run_id + '.' + producer + '.arrays'
            or (port.payload_schema, port.media_type, port.size_bytes, port.outcome_access, port.visibility_ceiling) !=
                (artifact.payload_schema, artifact.media_type, artifact.size_bytes,
                    original.outcome_access, original.visibility_ceiling)):
        raise ValueError('retained E3 array copy changes its original producer, bytes or access')
    prepared = context.prepared_invocation
    if prepared is not None:
        contract, = (row for row in prepared.inputs if row.artifact_id == port.artifact_id)
        if (contract.logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or (contract.logical.content_sha256, contract.physical_sha256) != (artifact.sha256, artifact.sha256)):
            raise ValueError('retained E3 array copy changes its exact original archive digest')
    return replace(port, binding=replace(port.binding, artifact_id=artifact.artifact_id))
