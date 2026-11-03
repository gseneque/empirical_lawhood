# SPDX-License-Identifier: MPL-2.0
"""Existing public preparation seam for the complete prepared opportunity.

Protected source/entry composition is named unfinished software. It cannot be
obtained by relabelling this exposed development source bank or its receipts.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs

from . import prepared_functional_bindings as method
from .prepared_assay_composition import MatrixPreparedAssayProgramme
from .source_selection_metadata import _source_allocation


PROTOCOL_ID = "matrix.prepared-functional.opportunity"


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalExperimentSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-functional-experiment"
    specification_id: str
    selection: ObjectIdentity
    assay: ObjectIdentity
    campaign: ObjectIdentity
    expected_groups: int
    expected_sources: int
    scope: str = method.SCOPE

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (self.scope != method.SCOPE or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.expected_sources) is not int or self.expected_sources < self.expected_groups):
            raise ValueError("prepared functional experiment changes its complete selected development source/group scope")
        for value, kind in ((self.selection, method.MatrixPreparedFunctionalSelection), (self.assay, MatrixPreparedAssayProgramme), (self.campaign, CampaignSpec)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("prepared functional experiment substitutes its exact immutable scientific record owners")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixPreparedFunctionalInputs:
    selection: method.MatrixPreparedFunctionalSelection | None
    assay: MatrixPreparedAssayProgramme | None
    campaign: CampaignSpec | None
    files: tuple[tuple[str, PreparedExperimentFile], ...]

    def __post_init__(self):
        if (self.selection is not None and type(self.selection) is not method.MatrixPreparedFunctionalSelection
                or self.assay is not None and type(self.assay) is not MatrixPreparedAssayProgramme
                or self.campaign is not None and type(self.campaign) is not CampaignSpec
                or type(self.files) is not tuple or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or any(type(value) is not PreparedExperimentFile for _, value in self.files)):
            raise TypeError("prepared functional inputs require exact original records and separate immutable selected file handles")


def input_record_types():
    return method.MatrixPreparedFunctionalSelection, MatrixPreparedAssayProgramme, CampaignSpec


def _allocation(selection):
    selection.__post_init__()
    return _source_allocation(phase=selection.specification.phase, selection_sha256=selection.specification.fingerprint(), roster=selection.roster)


def bind_functional_inputs(specification, records, *, files=None):
    files = {} if files is None else files
    if (type(specification) is not MatrixPreparedFunctionalExperimentSpecification or not isinstance(records, Mapping)
            or set(records) - {"selection", "assay", "campaign"} or not isinstance(files, Mapping)):
        raise TypeError("prepared functional binding requires its exact declared scientific and operational input roles")
    inputs = MatrixPreparedFunctionalInputs(records.get("selection"), records.get("assay"), records.get("campaign"), tuple(sorted(files.items())))
    return PreparedExperimentInputs({} if inputs.selection is None else {"selection": _allocation(inputs.selection)}, inputs)


def prepare_functional_experiment(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if type(specification) is not MatrixPreparedFunctionalExperimentSpecification or type(execution) is not ExecutionSelection:
        raise TypeError("prepared functional preparation needs its exact separate scientific/operational selections")
    specification.__post_init__()
    execution.__post_init__()
    inputs = MatrixPreparedFunctionalInputs(None, None, None, ()) if method_inputs is None else method_inputs
    if type(inputs) is not MatrixPreparedFunctionalInputs or not isinstance(scientific_inputs, Mapping):
        raise TypeError("prepared functional preparation requires its actual declared bound inputs")
    inputs.__post_init__()
    dependencies = []

    def missing(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.prepared-functional." + code, kind, detail, key))

    for key in ("selection", "assay", "campaign"):
        value = getattr(inputs, key)
        if value is None:
            missing(key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual original " + key + " record.", key)
        else:
            value.__post_init__()
            reference = ObjectIdentity.from_record(value.campaign_id, value) if key == "campaign" else value.identity
            if reference != getattr(specification, key):
                missing(key + ".identity", DependencyKind.SCIENTIFIC_EVIDENCE, "The selected original " + key + " differs from its frozen identity.", key)
    allocation = None if inputs.selection is None else _allocation(inputs.selection)
    if (set(scientific_inputs) != (set() if allocation is None else {"selection"})
            or allocation is not None and scientific_inputs.get("selection") != allocation):
        missing("allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain the complete original assigned group allocation.", "selection")
    if allocation is not None and (len(allocation.units) != specification.expected_groups
            or len(inputs.selection.roster.cases) != specification.expected_sources):
        missing("census", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain every selected case/group; nested recipes and views create no new independent units.", "selection")
    if inputs.selection is not None:
        if inputs.selection.specification.phase != "E5_OPPORTUNITY":
            missing("protected.source-owner", DependencyKind.SOFTWARE,
                "Implement the protected confirmation/transfer prepared source and complete root owner; the development route cannot be relabelled.", "selection")
            missing("protected.entry-owner", DependencyKind.SOFTWARE,
                "Compose original pre-fit reservation, publication and protected issue/entry/reveal methods for the actual phase before native use.", "selection")
            missing("protected.authority", DependencyKind.AUTHORITY,
                "Actual source qualification and protected issue/reveal authority remain required; a source or completion label supplies none.", "selection")
        elif inputs.assay is not None and not dependencies:
            selected_allocation, _ = method.validate_selection(inputs.selection, inputs.assay)
            if selected_allocation != allocation:
                missing("matched-allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain the actual complete original matched source allocation.", "selection")
    artifacts = {} if inputs.assay is None else dict(method.assay.contracts(inputs.assay)[4])
    files = dict(inputs.files)
    for key, artifact in artifacts.items():
        if key not in files:
            missing("file." + key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the exact original matched initial state or frozen instrument template bytes.", key)
        elif files[key].identity != artifact or files[key].record_version != "1.0.0" or files[key].maximum_bytes != artifact.size_bytes:
            missing("file." + key + ".identity", DependencyKind.EXTERNAL_INPUT, "The original selected file identity/revision/bound differs.", key)
    if set(files) - set(artifacts):
        missing("file.unselected", DependencyKind.EXTERNAL_INPUT, "Selected files add roles outside the exact complete assay census.")
    for key, attribute, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, attribute) is None:
            missing(key, kind, "Select the actual " + key + " before authoring; no environment is synchronized.")
    if protocol_bytes is not None:
        missing("protocol", DependencyKind.EXTERNAL_INPUT, "The original selected method/criterion/recipes cannot be overridden.")
    if inputs.selection is not None and inputs.assay is not None and inputs.campaign is not None:
        if len({inputs.selection.record_id, inputs.assay.record_id, inputs.campaign.campaign_id}) != 3:
            missing("record-alias", DependencyKind.SCIENTIFIC_EVIDENCE, "Original scientific roles cannot alias different record bytes under one ID.")
    lowered = None if dependencies else method.lower_prepared_functional(inputs.selection, inputs.assay, campaign=inputs.campaign,
        draft_id="draft.matrix-prepared-functional." + specification.fingerprint())
    n = specification.expected_sources
    phases = tuple(sorted((("design", 1), ("nominate", 1), *((phase, n) for phase in (*method.prediction.ALL_PHASES, "responses", "response-score")))))
    census = ExperimentCensus((("groups", specification.expected_groups), ("sources", n)),
        (("groups", 0 if allocation is None else len(allocation.units)), ("sources", 0 if inputs.selection is None else len(inputs.selection.roster.cases))),
        phases, (("array-products", 5 * n), ("canonical-products", 3 + 9 * n)), 2 * n)
    design = tuple(sorted(((specification.selection.object_id, inputs.selection), (specification.assay.object_id, inputs.assay),
        (specification.campaign.object_id, inputs.campaign)))) if all(getattr(inputs, key) is not None for key in ("selection", "assay", "campaign")) else ()
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)), allocation,
        None if lowered is None else lowered.draft, () if lowered is None else lowered.input_records, execution, specification, design,
        () if lowered is None else inputs.files)


def validate_functional_instance(*, specification, allocation, draft, source_records):
    if type(specification) is not MatrixPreparedFunctionalExperimentSpecification:
        raise TypeError("prepared functional instance needs its exact scientific experiment specification")
    specification.__post_init__()
    records = dict(source_records)
    if len(records) != 3 or set(records) != {specification.selection.object_id, specification.assay.object_id, specification.campaign.object_id}:
        raise ValueError("prepared functional instance changes its exact complete original source record census")
    selection, programme, campaign = (records[value.object_id] for value in (specification.selection, specification.assay, specification.campaign))
    if (type(selection) is not method.MatrixPreparedFunctionalSelection or type(programme) is not MatrixPreparedAssayProgramme or type(campaign) is not CampaignSpec
            or selection.identity != specification.selection or programme.identity != specification.assay
            or ObjectIdentity.from_record(campaign.campaign_id, campaign) != specification.campaign or allocation != _allocation(selection)
            or len(allocation.units) != specification.expected_groups or len(selection.roster.cases) != specification.expected_sources):
        raise ValueError("prepared functional instance changes its exact selected original scientific records/assigned census")
    method.validate_selection(selection, programme)
    expected = method.lower_prepared_functional(selection, programme, campaign=campaign,
        draft_id="draft.matrix-prepared-functional." + specification.fingerprint())
    if draft != expected.draft:
        raise ValueError("prepared functional instance changes its complete source/future/prediction/outcome graph")
