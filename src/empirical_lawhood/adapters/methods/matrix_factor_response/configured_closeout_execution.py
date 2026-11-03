# SPDX-License-Identifier: MPL-2.0
"""A separate CAL closeout contract which never completes a native contact.

The original execution remains immutable. Missing products belong to a new
assessment, while successful products retain their actual producing receipts.
The API authenticates every pin before this contract can select later work.
"""
from empirical_lawhood.kernel.decoding import validate_record_fields
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseScore, has_response_measurements
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.evidence import VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id, validate_sha256
from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.recovery import RunRecoveryIndex

from .configured_continued_response import ConfiguredE3ContinuedResponseConfig
from .configured_protected_methods import ConfiguredProtectedE3PairedOutcome
from .configured_protected_response_preparation import response_task_id
from .configured_protected_unknown_response import ConfiguredProtectedE3UnknownResponseAvailability
from .configured_unfinished_execution import ConfiguredE3UnfinishedExecution


def _reference(pin, kind):
    if (type(pin) is not ObjectIdentity
            or (pin.object_schema, pin.object_version) != (kind.SCHEMA, kind.VERSION)):
        raise ValueError('CAL closeout changes an exact original record type')
    validate_record_fields(pin)


@dataclass(frozen=True, slots=True)
class ConfiguredE3MissingOutcomeProducts(CanonicalRecord):
    """PURE missingness products, with their actual assessment provenance."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-missing-outcome-products'
    record_id: str
    assessment_provenance: NumericalProducingProvenance
    original_config: ConfiguredE3ContinuedResponseConfig
    availability: ConfiguredProtectedE3UnknownResponseAvailability
    score: ScheduledResponseScore
    outcome: ConfiguredProtectedE3PairedOutcome
    visibility_ceiling: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.assessment_provenance, NumericalProducingProvenance),
                (self.original_config, ConfiguredE3ContinuedResponseConfig),
                (self.availability, ConfiguredProtectedE3UnknownResponseAvailability),
                (self.score, ScheduledResponseScore), (self.outcome, ConfiguredProtectedE3PairedOutcome)):
            if type(value) is not kind:
                raise TypeError('CAL closeout requires its exact original contact and typed missing products')
            validate_record_fields(value)
        if (type(self.visibility_ceiling) is not VisibilityCeiling
                or self.visibility_ceiling not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY)):
            raise ValueError('CAL closeout requires the original unrevealed outcome visibility')
        config, availability, score, outcome = self.original_config, self.availability, self.score, self.outcome
        root = config.source.root.root
        if (config.operation != 'responses' or root.role.value != 'CALIBRATION'
                or availability.parent_contact.task_id != response_task_id(root.root_id, 'responses')
                or score.responses != availability.identity
                or score.source != config.source.identity or score.root_id != root.root_id
                or score.independent_group_id != root.independent_group_id
                or score.role != 'CALIBRATION' or score.disposition != 'UNEVALUABLE'
                or score.reason_codes != ('UNKNOWN_CONTACT',)
                or score.numerical_pass or score.controls or has_response_measurements(score)
                or any(value is not None for value in score.cumulative_log_errors)
                or outcome.original_score != ObjectIdentity.from_record(score.score_id, score)
                or outcome.forecast != score.error_forecast or outcome.numerical_disposition != 'UNEVALUABLE'
                or outcome.original_cells_sha256 != sha256(canonical_json_bytes(score.cells)).hexdigest()
                or any(any(value is not None for value in view.errors)
                    or view.dispositions != ('UNKNOWN_CONTACT',) * len(view.errors) for view in outcome.views)
                or outcome.feature.unit_id != root.independent_group_id):
            raise ValueError('CAL closeout changes its original independent root or missing-outcome joins')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class ConfiguredE3CALRootCloseout(CanonicalRecord):
    """One original CAL root; receipt absence remains explicit."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-cal-root-closeout'
    root_id: str
    unit_id: str
    native_configuration: ObjectIdentity
    contact: ObjectIdentity
    response_receipt: ObjectIdentity | None
    outcome_receipt: ObjectIdentity | None
    missing_products: ObjectIdentity | None
    missing_products_bytes: int | None
    outcome_visibility: VisibilityCeiling

    def __post_init__(self):
        validate_stable_id(self.root_id)
        validate_stable_id(self.unit_id)
        _reference(self.native_configuration, ConfiguredE3ContinuedResponseConfig)
        _reference(self.contact, NativeEffectContact)
        if (type(self.outcome_visibility) is not VisibilityCeiling
                or self.outcome_visibility not in (VisibilityCeiling.PROSPECTIVE, VisibilityCeiling.DEVELOPMENT_ONLY)):
            raise ValueError('CAL closeout changes its original outcome visibility')
        if self.missing_products is None:
            if self.missing_products_bytes is not None:
                raise ValueError('completed CAL work cannot acquire a missing-outcome payload')
            _reference(self.response_receipt, CanonicalTaskReceipt)
            _reference(self.outcome_receipt, CanonicalTaskReceipt)
        elif self.response_receipt is not None or self.outcome_receipt is not None:
            raise ValueError('CAL closeout cannot manufacture a successful receipt for missing native work')
        else:
            _reference(self.missing_products, ConfiguredE3MissingOutcomeProducts)
            if type(self.missing_products_bytes) is not int or self.missing_products_bytes <= 0:
                raise ValueError('CAL closeout requires the exact bounded missing-outcome payload size')

    @property
    def native_task_id(self):
        return response_task_id(self.root_id, 'responses')

    @property
    def outcome_task_id(self):
        return response_task_id(self.root_id, 'response-score')


@dataclass(frozen=True, slots=True)
class ConfiguredE3ClosedExecution(ConfiguredE3UnfinishedExecution):
    """The whole CAL census and a disjoint, never-entered execution suffix.

This is a distinct schema. It is never accepted by the original no-contact
transition, and contains no replacement for an original terminal or receipt.
"""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-closed-execution'
    predecessor_terminal: ObjectIdentity | None
    predecessor_recovery_index: ObjectIdentity
    predecessor_custody_sha256: str
    original_boundary: ConfiguredE3UnfinishedExecution
    calibration_units: tuple[str, ...]
    calibration_roots: tuple[ConfiguredE3CALRootCloseout, ...]

    def __post_init__(self):
        self._validate_boundary(allow_absent_terminal=True)
        _reference(self.predecessor_recovery_index, RunRecoveryIndex)
        validate_sha256(self.predecessor_custody_sha256)
        if type(self.original_boundary) is not ConfiguredE3UnfinishedExecution:
            raise TypeError('CAL closeout requires the exact original unfinished execution')
        validate_record_fields(self.original_boundary)
        old = self.original_boundary
        if (old.retention.continued_run_id != self.predecessor_run_id
                or (old.retention.specification, old.retention.allocation, old.retention.model_freeze,
                    old.retention.completed_receipts, old.retention.retained_arrays) != (
                    self.retention.specification, self.retention.allocation, self.retention.model_freeze,
                    self.retention.completed_receipts, self.retention.retained_arrays)):
            raise ValueError('CAL closeout changes original science, prefix receipts or fitted products')
        roots = self.calibration_roots
        if (type(roots) is not tuple or not roots or any(type(row) is not ConfiguredE3CALRootCloseout for row in roots)
                or tuple(row.root_id for row in roots) != tuple(sorted({row.root_id for row in roots}))
                or self.calibration_units != tuple(sorted({row.unit_id for row in roots}))):
            raise ValueError('CAL closeout changes its complete independent-root denominator')
        completed = dict(self.completed_receipts)
        pending = set(self.unfinished_task_ids)
        if any(completed.get(task) != receipt for task, receipt in old.completed_receipts):
            raise ValueError('CAL closeout changes a successful predecessor receipt')
        for row in roots:
            validate_record_fields(row)
            if row.native_task_id in pending:
                raise ValueError('CAL closeout cannot redispatch any entered CAL native task')
            if row.missing_products is None:
                if (completed.get(row.native_task_id), completed.get(row.outcome_task_id)) != (
                        row.response_receipt, row.outcome_receipt):
                    raise ValueError('CAL closeout loses an actual completed response or outcome')
            elif row.native_task_id in completed or row.outcome_task_id not in pending:
                raise ValueError('CAL closeout replaces an unknown contact with completion or drops its assessment')
        if not self.excluded_native_task_ids:
            raise ValueError('CAL closeout requires entered missing outcomes')
        if set(self.excluded_native_task_ids) & pending:
            raise ValueError('CAL closeout selects an uncertain call for execution')

    @property
    def excluded_native_task_ids(self):
        return tuple(sorted(row.native_task_id for row in self.calibration_roots if row.missing_products is not None))


@dataclass(frozen=True, slots=True)
class ConfiguredE3MissingOutcomeConfig(ConfiguredE3ContinuedResponseConfig):
    """Publish authenticated missingness through a PURE assessment operation."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-missing-outcome-config'
    closeout: ObjectIdentity
    products: ObjectIdentity

    def __post_init__(self):
        super(ConfiguredE3MissingOutcomeConfig, self).__post_init__()
        _reference(self.closeout, ConfiguredE3ClosedExecution)
        _reference(self.products, ConfiguredE3MissingOutcomeProducts)
        if self.operation != 'response-score' or self.source.root.root.role.value != 'CALIBRATION':
            raise ValueError('CAL closeout missingness is a PURE CAL assessment only')


def closeout_port():
    from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract
    return RecursivePortContract('closeout', ConfiguredE3ClosedExecution.SCHEMA,
        'application/json', None, minimum_count=0, maximum_count=1)
