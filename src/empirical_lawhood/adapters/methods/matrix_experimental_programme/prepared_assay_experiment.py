# SPDX-License-Identifier: MPL-2.0
"""Researcher specification and preparation for the complete development assay.

This exposes the existing experiment/ProgrammeService contracts, not another
compiler or execution framework. A completed assay is not E5 confirmation, E6
transfer, a cross-preparation error bound or scientific qualification.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.planning.campaigns import CampaignSpec
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs

from .preparation_experiment import source_allocation
from .prepared_assay_composition import SCOPE, MatrixPreparedAssayProgramme, contracts, lower_prepared_assay
from .prepared_prediction_bindings import ALL_PHASES


PROTOCOL_ID = "matrix.prepared-assay.development"


@dataclass(frozen=True, slots=True)
class MatrixPreparedAssaySpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-assay-experiment"
    specification_id: str
    programme: ObjectIdentity
    campaign: ObjectIdentity
    expected_groups: int
    expected_sources: int
    scope: str = SCOPE

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (self.scope != SCOPE or type(self.expected_groups) is not int or self.expected_groups < 1
                or type(self.expected_sources) is not int or self.expected_sources < self.expected_groups):
            raise ValueError("prepared assay specification changes complete original source/group scope")
        for value, kind in ((self.programme, MatrixPreparedAssayProgramme), (self.campaign, CampaignSpec)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("prepared assay specification substitutes its exact immutable programme or campaign")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.specification_id, self)


@dataclass(frozen=True, slots=True)
class MatrixPreparedAssayInputs:
    programme: MatrixPreparedAssayProgramme | None
    campaign: CampaignSpec | None
    files: tuple[tuple[str, PreparedExperimentFile], ...]

    def __post_init__(self):
        if (self.programme is not None and type(self.programme) is not MatrixPreparedAssayProgramme
                or self.campaign is not None and type(self.campaign) is not CampaignSpec
                or type(self.files) is not tuple or tuple(key for key, _ in self.files) != tuple(sorted({key for key, _ in self.files}))
                or any(type(value) is not PreparedExperimentFile for _, value in self.files)):
            raise TypeError("prepared assay inputs require exact original records and immutable selected operational files")


def input_record_types():
    return MatrixPreparedAssayProgramme, CampaignSpec


def bind_assay_inputs(specification, records, *, files):
    if (type(specification) is not MatrixPreparedAssaySpecification or not isinstance(records, Mapping)
            or set(records) - {"programme", "campaign"} or not isinstance(files, Mapping)):
        raise TypeError("prepared assay binding requires exact declared record and external file roles")
    inputs = MatrixPreparedAssayInputs(records.get("programme"), records.get("campaign"), tuple(sorted(files.items())))
    return PreparedExperimentInputs({} if inputs.programme is None else {"programme": source_allocation(inputs.programme.prediction.sources)}, inputs)


def prepare_assay_experiment(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    if type(specification) is not MatrixPreparedAssaySpecification or type(execution) is not ExecutionSelection:
        raise TypeError("prepared assay preparation requires separate immutable science and operational selections")
    specification.__post_init__()
    execution.__post_init__()
    inputs = MatrixPreparedAssayInputs(None, None, ()) if method_inputs is None else method_inputs
    if type(inputs) is not MatrixPreparedAssayInputs or not isinstance(scientific_inputs, Mapping):
        raise TypeError("prepared assay preparation requires its exact original bound inputs")
    inputs.__post_init__()
    dependencies = []

    def missing(code, kind, detail, key=None):
        dependencies.append(ExperimentDependency("matrix.prepared-assay." + code, kind, detail, key))

    for key in ("programme", "campaign"):
        value = getattr(inputs, key)
        if value is None:
            missing(key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply the actual original " + key + " record.", key)
        else:
            value.__post_init__()
            selected = value.identity if key == "programme" else ObjectIdentity.from_record(value.campaign_id, value)
            if selected != getattr(specification, key):
                missing(key + ".identity", DependencyKind.SCIENTIFIC_EVIDENCE, "The actual selected " + key + " identity differs.", key)
    allocation = None if inputs.programme is None else source_allocation(inputs.programme.prediction.sources)
    if (set(scientific_inputs) != (set() if allocation is None else {"programme"})
            or allocation is not None and scientific_inputs.get("programme") != allocation):
        missing("allocation", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain the exact complete original whole-group allocation.", "programme")
    if allocation is not None and (len(allocation.units) != specification.expected_groups
            or len(inputs.programme.prediction.sources.sources) != specification.expected_sources):
        missing("census", DependencyKind.SCIENTIFIC_EVIDENCE, "Retain every assigned source/group; nested recipes/views/branches add no units.", "programme")
    artifacts = {} if inputs.programme is None else dict(contracts(inputs.programme)[4])
    files = dict(inputs.files)
    for key, artifact in artifacts.items():
        role = "matched initial state" if key.startswith("external.initial-state.") else "frozen instrument templates"
        if key not in files:
            missing("file." + key + ".missing", DependencyKind.EXTERNAL_INPUT, "Supply exact original " + role + " bytes.", key)
        elif files[key].identity != artifact or files[key].record_version != "1.0.0" or files[key].maximum_bytes != artifact.size_bytes:
            missing("file." + key + ".identity", DependencyKind.EXTERNAL_INPUT, "The selected " + role + " identity/revision/bound differs.", key)
    if set(files) - set(artifacts):
        missing("file.unselected", DependencyKind.EXTERNAL_INPUT, "Selected files add roles outside the exact complete original assay census.")
    for key, attribute, kind in (("environment", "environment_id", DependencyKind.ENVIRONMENT),
            ("source-snapshot", "source_snapshot", DependencyKind.ENVIRONMENT), ("output-root", "output_root", DependencyKind.STORAGE)):
        if getattr(execution, attribute) is None:
            missing(key, kind, "Select the actual " + key + " before authoring; no environment is synchronized.")
    if protocol_bytes is not None:
        missing("protocol", DependencyKind.EXTERNAL_INPUT, "Original explicit recipe/feature/physical protocols cannot be overridden.")
    lowered = None if dependencies else lower_prepared_assay(inputs.programme, campaign=inputs.campaign,
        draft_id="draft.matrix-prepared-assay." + specification.fingerprint())
    n = specification.expected_sources
    phase_counts = tuple(sorted((("design", 1),) + tuple((phase, n) for phase in (*ALL_PHASES, "responses", "response-score"))))
    census = ExperimentCensus((("groups", specification.expected_groups), ("sources", n)),
        (("groups", 0 if allocation is None else len(allocation.units)),
         ("sources", 0 if inputs.programme is None else len(inputs.programme.prediction.sources.sources))),
        phase_counts,
        (("array-products", 5 * n), ("canonical-products", 1 + 9 * n)), 2 * n)
    design = tuple(sorted(((specification.programme.object_id, inputs.programme), (specification.campaign.object_id, inputs.campaign)))) if inputs.programme is not None and inputs.campaign is not None else ()
    return ExperimentPreparation(specification.identity, census, tuple(sorted(dependencies, key=lambda row: row.code)), allocation,
        None if lowered is None else lowered.draft, () if lowered is None else lowered.input_records, execution, specification, design,
        () if lowered is None else inputs.files)


def validate_assay_instance(*, specification, allocation, draft, source_records):
    if type(specification) is not MatrixPreparedAssaySpecification:
        raise TypeError("prepared assay instance requires its exact concise specification")
    records = dict(source_records)
    if len(records) != 2 or set(records) != {specification.programme.object_id, specification.campaign.object_id}:
        raise ValueError("prepared assay instance changes its exact original scientific record census")
    programme, campaign = records[specification.programme.object_id], records[specification.campaign.object_id]
    if (type(programme) is not MatrixPreparedAssayProgramme or type(campaign) is not CampaignSpec
            or programme.identity != specification.programme or ObjectIdentity.from_record(campaign.campaign_id, campaign) != specification.campaign
            or allocation != source_allocation(programme.prediction.sources) or len(programme.prediction.sources.sources) != specification.expected_sources
            or len(allocation.units) != specification.expected_groups):
        raise ValueError("prepared assay instance substitutes its original programme/campaign/source/group selection")
    expected = lower_prepared_assay(programme, campaign=campaign, draft_id="draft.matrix-prepared-assay." + specification.fingerprint())
    if draft != expected.draft:
        raise ValueError("prepared assay instance changes its complete actual source/prediction/native future/independent assay graph")
