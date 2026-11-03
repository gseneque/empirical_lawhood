# SPDX-License-Identifier: MPL-2.0
"""Public calibrated-model metadata, excluding original sealed CAL scores.

This shape retains a reference to the original calibration. It authenticates
neither that record nor its producer. The actual parent custody owner must
replay the original calibration before allowing dependent confirmation work.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.runtime.experimental_statistics import split_upper_calibration

from .programme_selection import ScheduledRevisionFittedModel, ScheduledRevisionTarget
from .revision_calibration import ScheduledRevisionCalibration, ScheduledRevisionCalibrationSpecification


@dataclass(frozen=True, slots=True)
class ScheduledRevisionPublicCalibration(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-scheduled-programme/revision-public-calibration"
    record_id: str
    original: ObjectIdentity
    specification: ScheduledRevisionCalibrationSpecification
    target: ObjectIdentity
    revision_model: ObjectIdentity
    baseline_model: ObjectIdentity
    group_ids: tuple[str, ...]
    rank: int
    revision_radius: Decimal | None
    baseline_radius: Decimal | None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if type(self.specification) is not ScheduledRevisionCalibrationSpecification:
            raise TypeError("public revision calibration requires its exact frozen scientific specification")
        self.specification.__post_init__()
        for value, kind in ((self.original, ScheduledRevisionCalibration), (self.target, ScheduledRevisionTarget),
                (self.revision_model, ScheduledRevisionFittedModel), (self.baseline_model, ScheduledRevisionFittedModel)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("public revision calibration substitutes an original scientific reference")
        if (type(self.group_ids) is not tuple or len(self.group_ids) != 64
                or self.group_ids != tuple(sorted(set(self.group_ids))) or type(self.rank) is not int
                or self.rank != split_upper_calibration((Decimal(0),) * 64, self.specification.alpha).rank
                or any(value is not None and (type(value) is not Decimal or not value.is_finite() or value < 0)
                    for value in (self.revision_radius, self.baseline_radius))):
            raise ValueError("public revision calibration changes its complete population, rank or finite/unbounded model metadata")
        for group in self.group_ids:
            validate_stable_id(group)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)

    @classmethod
    def from_calibration(cls, calibration):
        if type(calibration) is not ScheduledRevisionCalibration:
            raise TypeError("public revision calibration projects its exact original calibration only")
        calibration.__post_init__()
        return cls("public." + calibration.record_id, calibration.identity, calibration.specification, calibration.target,
            calibration.revision_model.identity, calibration.baseline_model.identity, calibration.group_ids, calibration.rank,
            calibration.revision_radius, calibration.baseline_radius)


def validate_public_revision_calibration(public, development, nomination, frozen, programme):
    if type(public) is not ScheduledRevisionPublicCalibration:
        raise TypeError("confirmation future requires public calibration metadata, with original scores retained by the parent")
    public.__post_init__()
    if ((public.specification.development_programme, public.specification.calibration_programme,
            public.specification.nomination, public.specification.frozen_models) !=
            (development.identity, programme.identity, nomination.identity, frozen.identity)
            or public.group_ids != programme.group_ids or public.revision_model != nomination.revision_model.identity
            or public.baseline_model != nomination.baseline_model.identity or public.target != nomination.specification.target.identity):
        raise ValueError("public revision calibration substitutes an assigned population, frozen model, target or original nomination")
