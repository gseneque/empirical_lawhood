# SPDX-License-Identifier: MPL-2.0
"""The existing experiment seam for exposed coupling-source development.

This is an independently usable source checkpoint. It does not stand in for
E5 nomination/confirmation, protected prospective entry or the prepared tail.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledAllocation, identity as original_identity
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import (
    DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation,
    PreparedExperimentFile, PreparedExperimentInputs,
)

from .preparation_bindings import external_id, lower_preparation_sources
from .preparation_records import MatrixPreparationSource


PROTOCOL_ID = "matrix.coupling-preparation.development"


@dataclass(frozen=True, slots=True)
class MatrixPreparationSourceBank(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-source-bank"
    bank_id: str
    allocations: tuple[ScheduledAllocation, ...]
    sources: tuple[MatrixPreparationSource, ...]

    def __post_init__(self):
        validate_stable_id(self.bank_id)
        if (type(self.allocations) is not tuple or not self.allocations or any(type(row) is not ScheduledAllocation for row in self.allocations)
                or tuple(row.allocation_id for row in self.allocations) != tuple(sorted({row.allocation_id for row in self.allocations}))
                or type(self.sources) is not tuple or not self.sources or any(type(row) is not MatrixPreparationSource for row in self.sources)
                or tuple(row.source_id for row in self.sources) != tuple(sorted({row.source_id for row in self.sources}))):
            raise ValueError("preparation source bank requires complete unique original allocation/source censuses")
        by_allocation = {original_identity(row): row for row in self.allocations}
        if set(by_allocation) != {row.original.allocation for row in self.sources}:
            raise ValueError("preparation source bank adds or omits an original allocation")
        names, streams = {}, {}
        for source in self.sources:
            source.__post_init__()
            source.validate_allocation(by_allocation[source.original.allocation])
            if source.root.root.role is not MatrixProgrammeRole.DEVELOPMENT:
                raise ValueError("exposed source checkpoint cannot relabel a protected prospective role")
            for value in (source.initial, source.recipe):
                if names.setdefault(value.identity.object_id, value) != value:
                    raise ValueError("preparation source bank aliases differing initial state or fixed recipe bytes")
            for stream in source.root.streams:
                owner = source.root.root.independent_group_id, stream.purpose
                if streams.setdefault(stream.effective_seed, owner) != owner:
                    raise ValueError("prepared independent groups or purposes collide in original consumed streams")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.bank_id, self)

    @property
    def input_artifacts(self):
        result = {}
        for source in self.sources:
            key, artifact = external_id(source, "initial-state"), source.initial.array_artifact
            if result.setdefault(key, artifact) != artifact:
                raise ValueError("prepared sources alias different original initial artifact identities")
        return tuple(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class MatrixPreparationExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/preparation-experiment"
    specification_id: str
    bank: ObjectIdentity
    campaign: ObjectIdentity
    expected_groups: int
    expected_sources: int
    scope: str = "EXPOSED_SOURCE_METHOD_DEVELOPMENT_NOT_E5_CONFIRMATION"

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for value, kind in ((self.bank, MatrixPreparationSourceBank), (self.campaign, CampaignSpec)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("preparation specification changes its exact original record type/revision")
        if (type(self.expected_groups) is not int or self.expected_groups < 1 or type(self.expected_sources) is not int
                or self.expected_sources < self.expected_groups or self.scope != "EXPOSED_SOURCE_METHOD_DEVELOPMENT_NOT_E5_CONFIRMATION"):
            raise ValueError("preparation specification loses its complete development source/group scope")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


def source_allocation(bank):
    groups = {}
    for source in bank.sources:
        root = source.root.root
        groups.setdefault(root.independent_group_id, []).append(source)
    units = tuple(IndependentUnit(group, bank.bank_id, rows[0].root.root.regime_id,
        tuple(sorted({view.view_id for source in rows for view in (source.primary_view, source.fine_view)})), True)
        for group, rows in sorted(groups.items()))
    return UnitAllocation("allocation." + bank.fingerprint(), (bank.identity,), units,
        tuple(UnitRoleAssignment(row.unit_id, "prepared-source-development") for row in units))


@dataclass(frozen=True, slots=True)
class MatrixPreparationInputs:
    bank: MatrixPreparationSourceBank | None
    campaign: CampaignSpec | None
    files: tuple[tuple[str, PreparedExperimentFile], ...]

    def __post_init__(self):
        if (self.bank is not None and type(self.bank) is not MatrixPreparationSourceBank
                or self.campaign is not None and type(self.campaign) is not CampaignSpec
                or type(self.files) is not tuple or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or any(type(value) is not PreparedExperimentFile for _, value in self.files)):
            raise TypeError("prepared source inputs need exact original records and immutable operational file handles")


def input_record_types():
    return MatrixPreparationSourceBank, CampaignSpec


def bind_preparation_inputs(specification, records, *, files):
    if type(specification) is not MatrixPreparationExperimentSpecification or not isinstance(records, Mapping) or set(records) - {"bank", "campaign"}:
        raise TypeError("prepared source binding needs its exact specification and declared record roles")
    if not isinstance(files, Mapping):
        raise TypeError("prepared source file bindings need their exact selected external IDs")
    inputs = MatrixPreparationInputs(records.get("bank"), records.get("campaign"), tuple(sorted(files.items())))
    allocation = {} if inputs.bank is None else {"bank": source_allocation(inputs.bank)}
    return PreparedExperimentInputs(allocation, inputs)


def prepare_preparation_experiment(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if type(specification) is not MatrixPreparationExperimentSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("prepared source preparation needs its exact scientific/operational selections")
    specification.__post_init__()
    execution.__post_init__()
    inputs = MatrixPreparationInputs(None, None, ()) if method_inputs is None else method_inputs
    if type(inputs) is not MatrixPreparationInputs or not isinstance(scientific_inputs, Mapping):
        raise TypeError("prepared source preparation needs its bound scientific inputs")
    inputs.__post_init__()
    dependencies = []

    def missing(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.preparation." + code, kind, detail, key))

    for key, kind in (("bank", MatrixPreparationSourceBank), ("campaign", CampaignSpec)):
        value = getattr(inputs, key)
        if value is None:
            missing(key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual original " + key + " record.", key)
        else:
            value.__post_init__()
            record_id = value.bank_id if kind is MatrixPreparationSourceBank else value.campaign_id
            if ObjectIdentity.from_record(record_id, value) != getattr(specification, key):
                missing(key + ".identity", DependencyKind.SCIENTIFIC_EVIDENCE, "The original " + key + " differs from its selected identity.", key)
    allocation = None if inputs.bank is None else source_allocation(inputs.bank)
    if set(scientific_inputs) != (set() if allocation is None else {"bank"}) or allocation is not None and scientific_inputs.get("bank") != allocation:
        missing("allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain the actual original whole-group source allocation.", "bank")
    if allocation is not None and (len(allocation.units) != specification.expected_groups or len(inputs.bank.sources) != specification.expected_sources):
        missing("census", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain every selected original group/source; nested views create no new units.", "bank")
    originals = {} if inputs.bank is None else dict(inputs.bank.input_artifacts)
    files = dict(inputs.files)
    for key, artifact in originals.items():
        if key not in files:
            missing("file." + key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the exact authenticated original matched initial state bytes.", key)
        elif (files[key].identity != artifact or files[key].record_version != "1.0.0" or files[key].maximum_bytes != artifact.size_bytes):
            missing("file." + key + ".identity", DependencyKind.EXTERNAL_INPUT, "The selected initial state identity/revision/bound differs.", key)
    if set(files) - set(originals):
        missing("file.unselected", DependencyKind.EXTERNAL_INPUT, "Initial state files add roles outside the complete selected source census.")
    for key, attribute, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, attribute) is None:
            missing(key, kind, "Select the actual " + key + " before authoring; no environment is synchronized.")
    if protocol_bytes is not None:
        missing("protocol", DependencyKind.EXTERNAL_INPUT, "The supplied original recipes own the coupling schedule; no protocol override is selected.")
    lowered = None if dependencies else lower_preparation_sources(inputs.bank.sources, allocations=inputs.bank.allocations,
        campaign=inputs.campaign, draft_id="draft.matrix-preparation." + specification.fingerprint())
    n = specification.expected_sources
    census = ExperimentCensus((("groups", specification.expected_groups), ("sources", n)),
        (("groups", 0 if allocation is None else len(allocation.units)), ("sources", 0 if inputs.bank is None else len(inputs.bank.sources))),
        (("assess", n), ("history", n)), (("array-products", n), ("assessments", n), ("native-histories", n)), n)
    design = tuple(sorted(((specification.bank.object_id, inputs.bank), (specification.campaign.object_id, inputs.campaign)))) if inputs.bank is not None and inputs.campaign is not None else ()
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)), allocation,
        None if lowered is None else lowered.draft, () if lowered is None else lowered.input_records, execution, specification, design,
        () if lowered is None else inputs.files)


def validate_preparation_instance(*, specification, allocation, draft, source_records):
    if type(specification) is not MatrixPreparationExperimentSpecification:
        raise TypeError("prepared instance needs its exact source specification")
    records = dict(source_records)
    if len(records) != 2 or set(records) != {specification.bank.object_id, specification.campaign.object_id}:
        raise ValueError("prepared instance changes its complete original scientific record census")
    bank, campaign = records[specification.bank.object_id], records[specification.campaign.object_id]
    if type(bank) is not MatrixPreparationSourceBank or type(campaign) is not CampaignSpec or bank.identity != specification.bank:
        raise ValueError("prepared instance substitutes original source bank/campaign")
    bank.__post_init__()
    if (ObjectIdentity.from_record(campaign.campaign_id, campaign) != specification.campaign or allocation != source_allocation(bank)
            or len(bank.sources) != specification.expected_sources or len(allocation.units) != specification.expected_groups):
        raise ValueError("prepared instance changes scientific source/group/campaign selection")
    expected = lower_preparation_sources(bank.sources, allocations=bank.allocations, campaign=campaign,
        draft_id="draft.matrix-preparation." + specification.fingerprint())
    if draft != expected.draft:
        raise ValueError("prepared instance changes the complete actual native/independent source graph")
