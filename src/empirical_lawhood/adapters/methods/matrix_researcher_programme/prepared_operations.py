# SPDX-License-Identifier: MPL-2.0
"""Explicit operational selections for the ordinary C-backed prepared phases.

Scientific choices belong to D and actual source reservations belong to C.
These records contain no nominee, qualification verdict or authority grant.
"""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_operational_resources import MatrixSelectedOperationalResources
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.time import InformationCutoff
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import StudyDraft


def _exact(value, kind):
    if type(value) is not kind:
        raise TypeError('prepared operations require their exact current operational owners')
    value.__post_init__()


@dataclass(frozen=True, slots=True)
class MatrixProgrammePreparedOperations(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/prepared-operations'
    record_id: str
    campaign: CampaignSpec
    cutoff: InformationCutoff
    operator_id: str
    maximum_source_bytes: int
    opportunity_resources: MatrixSelectedOperationalResources
    protected_resources: MatrixSelectedOperationalResources

    def __post_init__(self):
        validate_stable_id(self.record_id)
        validate_stable_id(self.operator_id)
        for value, kind in ((self.campaign, CampaignSpec), (self.cutoff, InformationCutoff),
                (self.opportunity_resources, MatrixSelectedOperationalResources),
                (self.protected_resources, MatrixSelectedOperationalResources)):
            _exact(value, kind)
        self.opportunity_resources.for_family('OPPORTUNITY')
        self.protected_resources.for_family('PROTECTED')
        if type(self.maximum_source_bytes) is not int or self.maximum_source_bytes < 1:
            raise ValueError('prepared operations require an explicit positive complete source bound')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammePreparedAccess(CanonicalRecord):
    """A later actual prospective entry selection, without invented source proof."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/prepared-access'
    record_id: str
    phase: str
    root: StudyDraft
    entry: ExperimentEntryPackage
    formal_methods: FormalMethodCatalog
    formal_source_inventories: tuple[FormalGapSourceCapabilityInventory, ...]

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if self.phase not in ('e5.confirmation', 'e6'):
            raise ValueError('prepared access selects only current protected CONF or E6')
        for value, kind in ((self.root, StudyDraft), (self.entry, ExperimentEntryPackage),
                (self.formal_methods, FormalMethodCatalog)):
            _exact(value, kind)
        if self.root.system is None or self.root.experiment is None:
            raise ValueError('prepared access requires its actual scientific root and experiment')
        rows = self.formal_source_inventories
        if (type(rows) is not tuple or not rows
                or any(type(value) is not FormalGapSourceCapabilityInventory for value in rows)
                or tuple(value.denominator_id for value in rows) != tuple(sorted({value.denominator_id for value in rows}))):
            raise ValueError('prepared access requires its exact sorted formal denominator inventories')
        for value in rows:
            value.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
