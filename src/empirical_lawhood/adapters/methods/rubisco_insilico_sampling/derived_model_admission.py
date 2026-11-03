# SPDX-License-Identifier: MPL-2.0
"""Explicit derived-model input condition; original failed preparation is history.

The caller authenticates primary receipts and the retained phase/source files.
This reader joins those complete bytes without loading a native model or rerunning
an assessment. A derived condition never changes the original24/36 outcomes.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import (
    DurablePreparationPlan, geometry_keys,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import GeometryReusePlan
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import GeometryDiagnostic
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_coordinate_assessment import (
    GEOMETRY_METHOD, ORIGIN_METHOD,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_preparation_assessment import (
    SerializedPreparationGeometry, SerializedPreparationIntegrity,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.native_subwork import NativeSubworkState

from . import control_contracts as c


RAW_NAMES = ("complete-heavy.pdb", "model.inpcrd", "model.prmtop")
ASSET_NAMES = frozenset((*RAW_NAMES, "atom-origin-provenance.json", "complete-assigned-parameters.json"))
INDEPENDENT_OWNERS = tuple("src/empirical_lawhood/adapters/methods/rubisco_insilico_dynamics/" + name + ".py"
    for name in ("amber_parameters", "preparation_integrity", "physical_preparation_geometry",
                 "serialized_heavy_pdb", "serialized_coordinate_assessment"))


def _document(record):
    if type(record) is not p.NativeTextFile:
        raise ValueError("derived supply needs complete typed retained phase/source bytes")
    record.__post_init__()
    value = json.loads(record.raw_utf8)
    if type(value) is not dict:
        raise ValueError("derived phase/source must be a complete object")
    return value


def _binding_matches(binding, evidence):
    return (type(binding) is dict and set(binding) == {"path", "bytes", "sha256"}
        and type(binding["path"]) is str and PurePosixPath(binding["path"]).is_absolute()
        and ".." not in PurePosixPath(binding["path"]).parts
        and type(binding["bytes"]) is int
        and (binding["bytes"], binding["sha256"]) == (evidence.byte_count, evidence.sha256))


def _canonical(record):
    return json.loads(record.canonical_bytes())


@dataclass(frozen=True, slots=True)
class DerivedModelSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-sampling/derived-model-supply"
    supply_id: str
    model_id: str
    assets: ObjectIdentity
    historical_readout: p.NativeTextFile
    postprocessing_readout: p.NativeTextFile
    assignment_readout: p.NativeTextFile
    geometry_readout: p.NativeTextFile
    producer_source_manifest: p.NativeTextFile
    independent_source_manifest: p.NativeTextFile
    geometry_diagnostic: p.NativeTextFile
    historical_scope: str = "ORIGINAL_PREPARATION_AND_FULL24_36_ASSESSMENTS_HISTORICAL"
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        if (self.model_id not in tuple(c.model_id(key) for key in p.model_roster())
                or type(self.assets) is not ObjectIdentity or self.assets.object_schema != p.ModelAssets.SCHEMA
                or self.historical_scope != "ORIGINAL_PREPARATION_AND_FULL24_36_ASSESSMENTS_HISTORICAL"
                or self.physical_independent_units != 0):
            raise ValueError("derived supply changes its selected model or historical scope")
        self.assets.__post_init__()
        historical, produced, assignment, geometry, producer, independent = tuple(_document(row) for row in (
            self.historical_readout, self.postprocessing_readout, self.assignment_readout,
            self.geometry_readout, self.producer_source_manifest, self.independent_source_manifest))
        if type(self.geometry_diagnostic) is not p.NativeTextFile:
            raise ValueError("derived supply needs complete retained canonical geometry bytes")
        self.geometry_diagnostic.__post_init__()
        diagnostic = decode_canonical_bytes(self.geometry_diagnostic.raw_utf8.encode(), GeometryDiagnostic,
            maximum_bytes=self.geometry_diagnostic.evidence.byte_count)
        if (produced.get("schema") != "el.rubisco.scoped-wt.derived-postprocessing.v1"
                or produced.get("derived_postprocessing") != "PRODUCTS_PRODUCED"
                or produced.get("error") is not None or produced.get("new_postprocess_load_count") != 1
                or any(produced.get(name) != 0 for name in ("molecular_acquisition_count", "native_solver_count", "tleap_count"))
                or produced.get("historical_original_unit_preparation_success") is not False
                or produced.get("historical_original_assignment_disposition") != "UNEVALUABLE"
                or produced.get("historical_original_known_model_native_call_count") != 2
                or produced.get("historical_original_unit_operational_status") != "FAILED"
                or not _binding_matches(produced.get("original_readout"), self.historical_readout.evidence)
                or not _binding_matches(produced.get("source_manifest"), self.producer_source_manifest.evidence)
                or producer.get("schema") != "el.rubisco.scoped-wt.additive-postprocessing-source.v1"
                or independent.get("schema") != "el.rubisco.scoped-wt.independent-composition-source.v1"
                or not _binding_matches(independent.get("derived_producer_source_manifest"), self.producer_source_manifest.evidence)):
            raise ValueError("derived supply lacks its exact completed separate postprocessing/source custody")
        histories = (historical.get("assignment_dispositions"), historical.get("full36states"))
        expected_models = tuple(c.model_id(key) for key in p.model_roster())
        expected_units = {*expected_models, *("geometry." + ".".join(key) for key in geometry_keys())}
        if (type(histories[0]) is not list or tuple(row[0] for row in histories[0]) != expected_models
                or type(histories[1]) is not dict or set(histories[1]) != expected_units
                or any(value not in {state.value for state in NativeSubworkState} for value in histories[1].values())
                or histories[1].get(self.model_id) != NativeSubworkState.COMPLETED.value
                or dict((row[0], row[1]) for row in histories[0])[self.model_id] != "UNEVALUABLE"):
            raise ValueError("derived supply omits original complete24/36 outcome history")
        for phase, value in (("assignment-origin", assignment), ("geometry", geometry)):
            if (value.get("schema") != "el.rubisco.scoped-wt.derived-independent-phase.v1"
                    or value.get("phase") != phase or value.get("phase_state") != "COMPLETED"
                    or value.get("assessment_error") is not None or value.get("native_calls") != 0
                    or value.get("producer_reexecution") is not False
                    or value.get("original_unit_preparation_success") is not False
                    or value.get("physical_independent_units") != 0 or value.get("qualification") is not False
                    or value.get("matched_I95M_admission") is not False
                    or not _binding_matches(value.get("original_readout"), self.historical_readout.evidence)
                    or not _binding_matches(value.get("derived_products"), self.postprocessing_readout.evidence)
                    or not _binding_matches(value.get("source_manifest"), self.independent_source_manifest.evidence)
                    or not _binding_matches(value.get("historical_producer_source_manifest"), self.producer_source_manifest.evidence)
                    or value.get("original_raw_operands") != produced.get("original_raw_operands")
                    or any(value.get(name) != produced.get(name) for name in ("derived_origin", "derived_parameter_audit"))):
                raise ValueError("derived supply lacks complete same-product independent phase custody")
        for value in (produced, assignment, geometry):
            if (value.get("original_full24_assignment_dispositions"), value.get("original_full36_unit_states")) != histories:
                raise ValueError("derived condition relabels original complete outcome history")
        result = assignment.get("result")
        if type(result) is not dict or type(geometry.get("result")) is not dict:
            raise ValueError("derived condition lacks complete independent result objects")
        counts = result.get("complete_parameter_term_census")
        proof = result.get("coordinate_origin_validation")
        support = result.get("inactive14_support")
        if (type(counts) is not dict or set(counts) != {"atoms", "bonds", "angles", "dihedrals"}
                or any(type(value) is not int or value < 0 for value in counts.values())
                or counts["atoms"] != diagnostic.atom_count or type(proof) is not dict
                or proof.get("method") != asdict(ORIGIN_METHOD)
                or proof.get("complete_heavy_atom_count") != diagnostic.heavy_atom_count
                or type(proof.get("complete_source_group_count")) is not int
                or not 0 < proof["complete_source_group_count"] <= diagnostic.heavy_atom_count
                or type(support) is not dict or support.get("dihedral_count") != counts["dihedrals"]
                or any(type(support.get(name)) is not int or support[name] < 0
                    for name in ("active14_term_count", "inactive14_term_count"))
                or support.get("active14_term_count", -1) + support.get("inactive14_term_count", -1) != counts["dihedrals"]):
            raise ValueError("derived condition omits complete independent atom/origin/term denominators or method")
        geometry_result = geometry["result"]
        if (geometry_result.get("method") != _canonical(GEOMETRY_METHOD)
                or not _binding_matches(geometry_result.get("diagnostic"), self.geometry_diagnostic.evidence)
                or not _binding_matches(geometry_result.get("independent_assignment_origin_parent"), self.assignment_readout.evidence)
                or geometry_result.get("hard_geometry_disposition") != diagnostic.hard_geometry_disposition.value
                or geometry_result.get("pair_counts") != [list(row) for row in diagnostic.pair_counts]
                or geometry_result.get("bonded_counts") != [list(row) for row in diagnostic.bonded_counts]
                or any(dict(diagnostic.bonded_counts)[name] != counts[name] for name in ("bonds", "angles", "dihedrals"))):
            raise ValueError("derived condition substitutes independently assessed complete geometry bytes/counts")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.supply_id, self)


@dataclass(frozen=True, slots=True, kw_only=True)
class DerivedChemicalForcePlan(c.ChemicalForcePlan):
    VERSION: ClassVar[str] = "1.3.0"
    preparation_plan: GeometryReusePlan | DurablePreparationPlan
    derived_supplies: tuple[DerivedModelSupply, ...]
    preparation_operand_scope: str = "HISTORICAL_ORIGINAL_NOT_DERIVED_ADMISSION"

    def __post_init__(self):
        c.ChemicalForcePlan.__post_init__(self)
        if (type(self.preparation_plan) not in (GeometryReusePlan, DurablePreparationPlan)
                or type(self.derived_supplies) is not tuple
                or any(type(row) is not DerivedModelSupply for row in self.derived_supplies)
                or tuple((row.model_id, row.assets) for row in self.derived_supplies) != self.selected_assets
                or self.preparation_plan.source != self.source
                or self.preparation_plan.engine_inventory_sha256 != self.engine_inventory_sha256
                or self.preparation_operand_scope != "HISTORICAL_ORIGINAL_NOT_DERIVED_ADMISSION"
                or any(name not in self.preparation_plan.attempted_model_ids for name, _ in self.selected_assets)):
            raise ValueError("derived chemical plan changes original source/plan or explicit separate supplies")
        self.preparation_plan.__post_init__()
        for supply in self.derived_supplies:
            supply.__post_init__()
            manifest = _document(supply.independent_source_manifest)
            members = manifest.get("members", ())
            if (tuple(row.get("relative_path") for row in members) != INDEPENDENT_OWNERS
                    or any(dict(self.code_sources).get(row["relative_path"]) != row["frozen"]["sha256"] for row in members)):
                raise ValueError("derived chemical plan omits exact independent five-owner producing source pins")


def validate_derived_operands(plan, source, preparation, integrity, geometry, assets, custody):
    """Separate derived condition, preserving every canonical historical operand."""
    if (type(integrity) is not SerializedPreparationIntegrity
            or type(geometry) is not SerializedPreparationGeometry):
        raise ValueError("derived control needs its exact historical independent assessment revisions")
    for record in (plan, source, preparation, integrity, geometry, *assets):
        record.__post_init__()
    if ((plan.source, plan.preparation, plan.assignment_integrity, plan.mathematical_geometry)
            != tuple(p.identity(row) for row in (source, preparation, integrity, geometry))
            or (preparation.source, preparation.structural_inventory, preparation.structural_coordinates, preparation.nomination)
            != (plan.source, source.structural_inventory, source.structural_coordinates, source.nomination)
            or (integrity.source, integrity.preparation) != (plan.source, plan.preparation)
            or (geometry.source, geometry.preparation, geometry.assignment_integrity)
            != (plan.source, plan.preparation, plan.assignment_integrity)):
        raise ValueError("derived control substitutes canonical original source/assessment history")
    selected = tuple((c.model_id((row.construct_id, row.joint_view_id, row.parameter_view)), p.identity(row)) for row in assets)
    if selected != plan.selected_assets or tuple(row[0] for row in custody) != tuple(name for name, _ in selected):
        raise ValueError("derived control changes its explicit model/assets/custody subset")
    actual_custody = []
    for supply, asset, row in zip(plan.derived_supplies, assets, custody, strict=True):
        name, definition, completion_identity, completion, return_identity, returned = row
        for record in (definition, completion, returned):
            record.__post_init__()
        if any(type(identity) is not ObjectIdentity or ObjectIdentity.from_record(identity.object_id, record) != identity
                for identity, record in ((completion_identity, completion), (return_identity, returned))):
            raise ValueError("derived control substitutes canonical original completion/return")
        historical = _document(supply.historical_readout)
        original = next((value for value in historical.get("actual_selected_model_custody", ()) if value.get("model_id") == name), None)
        if (original is None or original.get("state") != NativeSubworkState.COMPLETED.value
                or any(original.get(key) != _canonical(value) for key, value in (
                ("definition", definition), ("completion_identity", completion_identity), ("completion", completion),
                ("return_identity", return_identity), ("returned", returned)))
                or definition.subwork_id != name or definition.operation_id != "rubisco.durable-preparation.unit"
                or definition.configuration != plan.preparation_plan.identity
                or definition.code_sources_sha256 != sha256(canonical_json_bytes(plan.preparation_plan.code_sources)).hexdigest()
                or definition.dependency_lock_sha256 != plan.preparation_plan.dependency_lock_sha256
                or plan.source not in definition.sources or completion.definition != definition.identity
                or completion.operational_status is not OperationalStatus.FAILED
                or completion.omitted_output_ids or completion.unknown_streams
                or completion.output_ids != tuple(sorted(value.output_id for value in definition.outputs))
                or returned.unit_id != name or returned.plan != definition.configuration
                or not returned.known_return or returned.preparation_succeeded is not False or returned.error_text is None):
            raise ValueError("derived control loses the exact known failed original preparation custody")
        model = next(value for value in preparation.models if value.model_id == name)
        diagnostic = next(value for value in geometry.models if value.model_id == name)
        native_calls = tuple(value for value in preparation.native_calls if value.model_id == name)
        if (asset.source != plan.source or asset.product_id == model.assets.object_id
                or dict((value[0], value[1]) for value in integrity.model_dispositions)[name] is not A.UNEVALUABLE
                or model.disposition is not A.UNEVALUABLE or diagnostic.assets != model.assets
                or len(native_calls) != 2 or tuple(value.call_id for value in native_calls) != model.native_call_ids
                or tuple(value.call_id for value in native_calls) != tuple(value.object_id for value in returned.native_calls)
                or any(value.termination != "COMPLETED" or value.error_text is not None for value in native_calls)
                or historical.get("assignment_dispositions") != [[n, value.value, list(reasons)] for n, value, reasons in integrity.model_dispositions]):
            raise ValueError("derived control relabels failed original model/assets/assignment history")
        for key, record in (("preparation-projection", preparation), ("assignment-integrity", integrity), ("physical-geometry", geometry)):
            evidence = p.FileEvidence("historical/" + key + ".json", len(record.canonical_bytes()), record.fingerprint())
            if not _binding_matches(historical.get("assessment_products", {}).get(key), evidence):
                raise ValueError("derived control replaces exact historical independent assessment bytes")
        produced = _document(supply.postprocessing_readout)
        original_origin = produced.get("original_raw_operands", {}).get("atom-origin-provenance.json")
        if not any(PurePosixPath(value.relative_path).name == "atom-origin-provenance.json"
                and value in model.files and _binding_matches(original_origin, value) for value in returned.files):
            raise ValueError("derived supply loses the historical original origin bytes")
        by_name = {PurePosixPath(value.evidence.relative_path).name: value for value in asset.files}
        if len(by_name) != len(asset.files) or set(by_name) != ASSET_NAMES:
            raise ValueError("derived model needs its five complete selected raw/derived assets")
        for key in RAW_NAMES:
            evidence = by_name[key].evidence
            if (evidence not in returned.files or evidence not in model.files
                    or not _binding_matches(produced.get("original_raw_operands", {}).get(key), evidence)):
                raise ValueError("derived model substitutes original topology/restart/heavy bytes")
        for key, binding in (("atom-origin-provenance.json", "derived_origin"),
                             ("complete-assigned-parameters.json", "derived_parameter_audit")):
            if not _binding_matches(produced.get(binding), by_name[key].evidence):
                raise ValueError("derived model substitutes independently assessed new audit/origin bytes")
        result = decode_canonical_bytes(supply.geometry_diagnostic.raw_utf8.encode(), GeometryDiagnostic, maximum_bytes=None)
        if result.hard_geometry_disposition is not A.SATISFIED:
            raise ValueError("derived model has an adverse independent hard geometry result")
        actual_custody.append((name, definition.identity, completion_identity, return_identity))
    if tuple(actual_custody) != plan.preparation_custody:
        raise ValueError("derived control relabels original independent native custody")
    return plan
