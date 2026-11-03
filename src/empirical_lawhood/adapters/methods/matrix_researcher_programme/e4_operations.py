# SPDX-License-Identifier: MPL-2.0
"""Once-selected E4 operational budgets and later genuine access operands."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_followup_records import ScheduledFullFactorResources
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_experiment import SelectedE3E4OperationalSelection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_declarative import SelectedE4RootSelection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_method_bindings import SelectedE4MethodResources
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4NativeBudgets
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_operational_resources import SelectedE4OperationalResources
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory, FormalMethodCatalog
from empirical_lawhood.planning.study_authoring import MaterializationQualificationReceipt
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE4Operations(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e4-operations'
    record_id: str
    campaign: CampaignSpec
    development_resources: SelectedE3E4OperationalSelection
    method_resources: SelectedE4MethodResources
    structural_resources: ScheduledFullFactorResources
    native_budgets: SelectedE4NativeBudgets
    protected_resources: SelectedE4OperationalResources

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.campaign, CampaignSpec),
                (self.development_resources, SelectedE3E4OperationalSelection),
                (self.method_resources, SelectedE4MethodResources),
                (self.structural_resources, ScheduledFullFactorResources),
                (self.native_budgets, SelectedE4NativeBudgets),
                (self.protected_resources, SelectedE4OperationalResources)):
            if type(value) is not kind:
                raise TypeError('programme E4 requires each exact current operational owner')
            value.__post_init__()
        if not {'revision-fit', 'revision-freeze'} <= dict(self.method_resources.phase_budgets).keys():
            raise ValueError('programme E4 must reserve its actual revision fit and freeze methods')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


@dataclass(frozen=True, slots=True)
class MatrixProgrammeE4Access(CanonicalRecord):
    """Real later entry and produced-input admissions; no generated wave roster."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-programme/e4-access'
    record_id: str
    phase: str
    root: SelectedE4RootSelection
    entry: ExperimentEntryPackage
    formal_methods: FormalMethodCatalog
    formal_source_inventory: FormalGapSourceCapabilityInventory
    produced_qualifications: tuple[MaterializationQualificationReceipt, ...] = ()
    produced_source_configs: tuple[SourceMaterializationConfig, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.record_id)
        if self.phase not in ('e4.calibration', 'e4.confirmation'):
            raise ValueError('programme E4 access selects one actual protected CAL or CONF phase')
        for value, kind in ((self.root, SelectedE4RootSelection), (self.entry, ExperimentEntryPackage),
                (self.formal_methods, FormalMethodCatalog),
                (self.formal_source_inventory, FormalGapSourceCapabilityInventory)):
            if type(value) is not kind:
                raise TypeError('programme E4 access requires its exact actual entry operands')
            value.__post_init__()
        for values, kind, key in ((self.produced_qualifications, MaterializationQualificationReceipt, 'receipt_id'),
                (self.produced_source_configs, SourceMaterializationConfig, 'source_id')):
            if (type(values) is not tuple or any(type(value) is not kind for value in values)
                    or tuple(getattr(value, key) for value in values) != tuple(sorted({getattr(value, key) for value in values}))):
                raise ValueError('programme E4 produced admissions must preserve exact sorted original records')
            for value in values:
                value.__post_init__()
        if bool(self.produced_qualifications) != bool(self.produced_source_configs):
            raise ValueError('programme E4 produced admissions require both actual qualifications and source configs')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)
