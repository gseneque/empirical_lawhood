# SPDX-License-Identifier: MPL-2.0
"""Exact original geometry supply for a distinct, fresh parameterisation attempt.

No old contact is resumed. The entire original archive is authenticated; only
the two declared consumer operands are materialized. Native entry is composed
locally through the existing compiler, isolated runner and custody owners.
"""

from dataclasses import dataclass, fields, replace
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_stable_id
from empirical_lawhood.kernel.status import OperationalStatus
from empirical_lawhood.runtime.artifacts import ArtifactManifest, ArtifactProfile, CanonicalTaskReceipt
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition,
)

from . import contracts as c
from .durable_contracts import DurablePreparationPlan, DurableRawFileCensus, DurableUnitReturn, geometry_id
from .durable_preparation import (
    CHUNK_BYTES, RAW_MAGIC, DurablePreparationRunner, _ChunkReader, file_chunks, uncompressed_archive_chunks,
)
from .durable_roster import RAW_SCHEMA

REQUIRED_FILES = ("atom-origin-provenance.json", "complete-heavy.pdb")
INTEGRITY_SCHEMA = "empirical-lawhood/rubisco-insilico-dynamics/pre-amber-geometry-integrity"


@dataclass(frozen=True, slots=True)
class GeometryReuseSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/geometry-reuse-supply"
    supply_id: str
    original_source: c.PreparationSelection
    original_plan: DurablePreparationPlan
    definition: NativeSubworkDefinition
    begin: NativeSubworkBegin
    contact: NativeSubworkContact
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    returned: DurableUnitReturn
    census: DurableRawFileCensus
    control_manifests: tuple[ArtifactManifest, ...]
    output_manifests: tuple[ArtifactManifest, ...]
    completion_manifest: ArtifactManifest
    independent_integrity: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        kinds = ((self.original_source, c.PreparationSelection), (self.original_plan, DurablePreparationPlan),
                 (self.definition, NativeSubworkDefinition), (self.completion, NativeSubworkCompletion),
                 (self.begin, NativeSubworkBegin), (self.contact, NativeSubworkContact),
                 (self.receipt, CanonicalTaskReceipt), (self.returned, DurableUnitReturn),
                 (self.census, DurableRawFileCensus), (self.completion_manifest, ArtifactManifest))
        for record, kind in kinds:
            if type(record) is not kind:
                raise ValueError("geometry reuse substitutes original typed custody")
            record.__post_init__()
        definition, plan = self.definition, self.original_plan
        if (plan.source != c.identity(self.original_source)
                or (plan.nomination, plan.inventory, plan.coordinates) != (self.original_source.nomination,
                    self.original_source.structural_inventory, self.original_source.structural_coordinates)
                or plan.workdir != self.original_source.native_workdir
                or definition.subwork_id not in {geometry_id(*key) for key in plan.geometry_census}
                or definition.subwork_id not in plan.attempted_geometry_ids
                or definition.operation_id != "rubisco.durable-preparation.unit"
                or definition.configuration != plan.identity
                or definition.code_sources_sha256 != sha256(canonical_json_bytes(plan.code_sources)).hexdigest()
                or definition.dependency_lock_sha256 != plan.dependency_lock_sha256
                or not {plan.source, plan.nomination, plan.inventory, plan.coordinates}.issubset(set(definition.sources))
                or self.completion.definition != definition.identity
                or self.completion.operational_status is not OperationalStatus.SUCCEEDED
                or self.completion.omitted_output_ids or self.completion.unknown_streams
                or self.completion.output_ids != ("files.census", "files.raw", "unit.return")
                or self.returned.unit_id != definition.subwork_id or self.returned.plan != plan.identity
                or not self.returned.known_return or not self.returned.preparation_succeeded
                or self.returned.geometry is not None or self.returned.geometry_receipt is not None
                or self.returned.files != self.census.files):
            raise ValueError("geometry reuse loses successful original source/unit/completion/census joins")
        key = sha256((definition.parent_contact.task_id + ":" + definition.subwork_id).encode()).hexdigest()
        prefix = "native-subwork." + key
        expected_task = prefix
        parent = definition.parent_contact
        controls = tuple(zip(("definition", "begin", "contact"),
                             (definition, self.begin, self.contact), self.control_manifests, strict=True))
        if (self.begin.definition != definition.identity
                or self.contact.begin != ObjectIdentity.from_record(prefix + ".begin", self.begin)
                or self.completion.contact != ObjectIdentity.from_record(prefix + ".contact", self.contact)):
            raise ValueError("geometry reuse substitutes its actual original begin/contact chain")
        if (self.receipt.run_id != parent.run_id or self.receipt.task_id != expected_task
                or self.receipt.attempt_id != parent.run_id + "." + expected_task + ".attempt-001"
                or self.receipt.receipt_id != "receipt." + self.receipt.attempt_id
                or self.receipt.implementation_commit != parent.implementation_commit
                or self.receipt.input_materialization_ids != tuple(sorted((*definition.input_materialization_ids,
                    *(row.materialization.materialization_id for row in self.control_manifests))))
                or self.receipt.operational_status is not OperationalStatus.SUCCEEDED):
            raise ValueError("geometry reuse substitutes original complete receipt")
        if (type(self.independent_integrity) is not ObjectIdentity
                or self.independent_integrity.object_schema != INTEGRITY_SCHEMA):
            raise ValueError("geometry reuse lacks its genuine independent source/origin assessment")
        self.independent_integrity.__post_init__()
        manifests = (*self.output_manifests, self.completion_manifest)
        if tuple(row.logical.logical_artifact_id for row in self.output_manifests) != tuple(
                prefix + ".output." + name for name in ("files.census", "files.raw", "unit.return")):
            raise ValueError("geometry reuse changes original complete output denominator")
        for row in (*manifests, *self.control_manifests):
            if type(row) is not ArtifactManifest:
                raise ValueError("geometry reuse substitutes authentic original manifest")
            row.__post_init__()
            row.logical.__post_init__()
            row.materialization.__post_init__()
        archive_root = "runs/" + parent.run_id + "/native-subwork/" + key
        locators = (*((manifest, archive_root + "/" + name + ".json")
                     for name, _, manifest in controls),
                    (self.completion_manifest, archive_root + "/completion.json"),
                    *((manifest, archive_root + "/outputs/" + name)
                      for manifest, name in zip(self.output_manifests,
                                               ("files.census", "files.raw", "unit.return"), strict=True)))
        if (len({row.materialization.storage_root_id for row in (*manifests, *self.control_manifests)}) != 1
                or any(manifest.materialization.relative_path != path for manifest, path in locators)):
            raise ValueError("geometry reuse changes original immutable storage custody scope")
        if (tuple(sorted((row.materialization for row in manifests), key=lambda row: row.materialization_id))
                != self.receipt.output_materializations
                or tuple(sorted((row.logical for row in manifests), key=lambda row: row.logical_artifact_id))
                != self.receipt.output_logical_artifacts):
            raise ValueError("geometry reuse changes original receipt/output identities")
        for manifest, record, name in ((self.output_manifests[0], self.census, "output.files.census"),
                (self.output_manifests[2], self.returned, "output.unit.return"),
                (self.completion_manifest, self.completion, "completion"),
                *((manifest, record, name) for name, record, manifest in controls)):
            if (manifest.logical.logical_artifact_id != prefix + "." + name
                    or manifest.logical.payload_schema != record.SCHEMA
                    or manifest.logical.content_sha256 != record.fingerprint()
                    or manifest.logical.profile is not ArtifactProfile.CANONICAL_JSON
                    or manifest.materialization.physical_sha256 != record.fingerprint()
                    or manifest.materialization.size_bytes != len(record.canonical_bytes())
                    or manifest.materialization.compression != "none"):
                raise ValueError("geometry reuse changes original canonical custody bytes")
        raw = self.output_manifests[1]
        if (raw.logical.payload_schema != RAW_SCHEMA or raw.logical.profile is not ArtifactProfile.RAW_SOURCE_BYTES
                or raw.logical.content_sha256 != raw.materialization.physical_sha256
                or raw.materialization.compression != "none"):
            raise ValueError("geometry reuse substitutes complete original raw archive")
        selected = {Path(row.relative_path).name: row for row in self.census.files}
        if (len(selected) != len(self.census.files) or any(Path(row.relative_path).parts != (
                definition.subwork_id, Path(row.relative_path).name) for row in self.census.files)
                or not set(REQUIRED_FILES).issubset(selected)):
            raise ValueError("geometry reuse changes original path scope or omits required files")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.supply_id, self)

    @property
    def geometry_receipt(self):
        return ObjectIdentity.from_record(self.receipt.receipt_id, self.receipt)

    @property
    def archive_evidence(self):
        raw = self.output_manifests[1].materialization
        return c.FileEvidence(raw.relative_path, raw.size_bytes, raw.physical_sha256)


@dataclass(frozen=True, slots=True, kw_only=True)
class GeometryReusePlan(DurablePreparationPlan):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-insilico-dynamics/geometry-reuse-plan"
    geometry_supplies: tuple[ObjectIdentity, ...]
    reused_geometry_ids: tuple[str, ...]
    archive_inputs: tuple[tuple[ObjectIdentity, str], ...]

    def __post_init__(self):
        # Reuse retains the existing closed full12/24 recipe. Only model units
        # are newly attempted; original geometry remains its original episode.
        base = {field.name: getattr(self, field.name) for field in fields(DurablePreparationPlan)}
        base["attempted_geometry_ids"] = self.reused_geometry_ids
        DurablePreparationPlan(**base)
        needed = tuple(sorted({"geometry." + unit[len("model."):].rsplit(".", 1)[0]
                               for unit in self.attempted_model_ids}))
        if (self.attempted_geometry_ids or not self.attempted_model_ids
                or self.reused_geometry_ids != needed
                or len(self.geometry_supplies) != len(needed)
                or any(type(row) is not ObjectIdentity for row in self.geometry_supplies)
                or tuple(row.object_id for row in self.geometry_supplies)
                    != tuple(sorted(set(row.object_id for row in self.geometry_supplies)))
                or any(type(row) is not ObjectIdentity or row.object_schema != GeometryReuseSupply.SCHEMA
                       for row in self.geometry_supplies)):
            raise ValueError("geometry reuse plan changes selected authentic supplier/model dependencies")
        for row in self.geometry_supplies:
            row.__post_init__()
        if (tuple(identity for identity, _ in self.archive_inputs) != self.geometry_supplies
                or any(Path(path).parent != Path(self.workdir).parent / "inputs"
                       or not Path(path).is_absolute() or ".." in Path(path).parts
                       for _, path in self.archive_inputs)
                or len({path for _, path in self.archive_inputs}) != len(self.archive_inputs)):
            raise ValueError("geometry reuse changes exact selected ordinary raw input paths")


def validate_reuse_assessment(plan, source, supply, assessment):
    """Exact independently assessed original parents; no downstream admission."""
    from .preamber_geometry_integrity import PreAmberGeometryIntegrity

    plan.__post_init__()
    supply.__post_init__()
    if type(assessment) is not PreAmberGeometryIntegrity:
        raise ValueError("geometry reuse requires actual typed independent assessment")
    assessment.__post_init__()
    selected = {Path(row.relative_path).name: row for row in supply.census.files}
    prefix = supply.completion_manifest.logical.logical_artifact_id
    construct_id, joint = supply.definition.subwork_id[len("geometry."):].rsplit(".", 1)
    if (ObjectIdentity.from_record(assessment.product_id, assessment) != supply.independent_integrity
            or assessment.source != c.identity(supply.original_source)
            or assessment.geometry_definition != supply.definition.identity
            or assessment.geometry_completion != ObjectIdentity.from_record(prefix, supply.completion)
            or assessment.geometry_receipt != supply.geometry_receipt
            or assessment.construct != next(row for row in supply.original_source.constructs if row.construct_id == construct_id)
            or assessment.joint_view_id != joint
            or assessment.heavy_file != selected["complete-heavy.pdb"]
            or assessment.origin_file != selected["atom-origin-provenance.json"]
            or supply.identity not in plan.geometry_supplies
            or supply.definition.subwork_id not in plan.reused_geometry_ids
            or source != replace(supply.original_source, native_workdir=plan.workdir)
            or plan.source != c.identity(source)
            or plan.engine_inventory_sha256 != supply.original_source.engine_inventory_sha256):
        raise ValueError("geometry reuse substitutes original genotype/source/assessment/geometry bytes")


def invocation_bytes(plan, source, nomination, inventory, coordinates, definitions, source_root,
                     supplies, assessments, *, implementation=None):
    """Build and decode the exact complete invocation before parent contact."""
    from . import science

    science.validate_source(source, nomination, inventory, coordinates)
    return _invocation_transport(plan, source, nomination, inventory, coordinates, definitions,
        source_root, supplies, assessments, implementation=implementation)


def _invocation_transport(plan, source, nomination, inventory, coordinates, definitions, source_root,
                          supplies, assessments, *, implementation=None):
    """Bind complete original bytes so the actual child can assess all stock.

    Serialization grants no readiness. The installed child always calls the
    strict public builder before it can report Ready or receive native progress.
    """
    from empirical_lawhood.adapters.methods.rubisco_insilico_structure.contracts import AssemblyCoordinates, StructuralInventory
    from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import NominationDossier
    from empirical_lawhood.kernel.serialization import canonical_json_bytes
    from .preamber_geometry_integrity import PreAmberGeometryIntegrity

    if (type(plan) is not GeometryReusePlan or type(source) is not c.PreparationSelection
            or type(nomination) is not NominationDossier or type(inventory) is not StructuralInventory
            or type(coordinates) is not AssemblyCoordinates):
        raise ValueError("geometry reuse requires its exact original typed source and model-only plan")
    for record in (source, nomination, inventory, coordinates):
        record.__post_init__()
    plan.__post_init__()
    if ((plan.source, plan.nomination, plan.inventory, plan.coordinates)
            != tuple(c.identity(row) for row in (source, nomination, inventory, coordinates))
            or tuple(row.identity for row in supplies) != plan.geometry_supplies
            or tuple(sorted(row.definition.subwork_id for row in supplies)) != plan.reused_geometry_ids
            or len(supplies) != len(assessments)):
        raise ValueError("geometry reuse invocation substitutes real scientific operands")
    for supply, assessment in zip(supplies, assessments, strict=True):
        validate_reuse_assessment(plan, source, supply, assessment)
    expected_ids = tuple(sorted((*[geometry_id(*key) for key in plan.geometry_census],
                                *["model." + ".".join(key) for key in plan.model_census],
                                "preparation.metadata")))
    expected_sources = {plan.source, plan.nomination, plan.inventory, plan.coordinates,
                        *plan.geometry_supplies, *(row.independent_integrity for row in supplies)}
    if (tuple(row.subwork_id for row in definitions) != expected_ids
            or any(type(row) is not NativeSubworkDefinition or row.configuration != plan.identity
                   or row.parent_contact != definitions[0].parent_contact
                   or not expected_sources.issubset(set(row.sources)) for row in definitions)):
        raise ValueError("geometry reuse invocation changes actual full37 parent/source/roster joins")
    from .durable_roster import definitions as preparation_definitions
    if definitions != preparation_definitions(plan, definitions[0].parent_contact,
            sources=definitions[0].sources,
            input_materialization_ids=definitions[0].parent_contact.input_materialization_ids,
            implementation=implementation, source_root=source_root):
        raise ValueError("geometry reuse invocation changes exact declared owner/code/lock/input/output contracts")
    for record in (plan, source, nomination, inventory, coordinates, *definitions, *supplies, *assessments):
        raw = record.canonical_bytes()
        if decode_canonical_bytes(raw, type(record), maximum_bytes=len(raw)) != record:
            raise ValueError("geometry reuse loses exact invocation canonical roundtrip")
    if any(type(row) is not PreAmberGeometryIntegrity for row in assessments):
        raise ValueError("geometry reuse substitutes original independent assessment type")
    selected_root = Path(source_root)
    if not selected_root.is_absolute() or ".." in selected_root.parts:
        raise ValueError("geometry reuse source root is not exactly selected")
    # The arrays/large original records stay original canonical text; tuples are
    # kernel-serializable and produce JSON arrays without a precontact list bug.
    return canonical_json_bytes(dict(plan=plan.canonical_bytes().decode(),
        source=source.canonical_bytes().decode(), nomination=nomination.canonical_bytes().decode(),
        inventory=inventory.canonical_bytes().decode(), coordinates=coordinates.canonical_bytes().decode(),
        definitions=tuple(row.canonical_bytes().decode() for row in definitions),
        source_root=str(selected_root), supplies=tuple(row.canonical_bytes().decode() for row in supplies),
        assessments=tuple(row.canonical_bytes().decode() for row in assessments)))


def _scan_archive(path, definition, census, raw_evidence, destination=None):
    chunks = file_chunks(path, expected=raw_evidence)
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError("geometry reuse substitutes original archive format")
        size = int.from_bytes(reader.take(8), "big")
        from empirical_lawhood.infrastructure.bounded_io import MAX_CONTROL_PLANE_JSON_BYTES
        if not 0 < size <= MAX_CONTROL_PLANE_JSON_BYTES:
            raise ValueError("geometry reuse changes finite original census envelope")
        header = reader.take(size)
        if decode_canonical_bytes(header, DurableRawFileCensus, maximum_bytes=size) != census or header != census.canonical_bytes():
            raise ValueError("geometry reuse substitutes original complete archive census")
        for row in census.files:
            name = Path(row.relative_path).name
            if Path(row.relative_path).parts != (definition.subwork_id, name):
                raise ValueError("geometry reuse changes original exact member path scope")
            digest, remaining = sha256(), row.byte_count
            output = (Path(destination) / name).open("xb") if destination is not None and name in REQUIRED_FILES else None
            try:
                while remaining:
                    block = reader.take(min(remaining, CHUNK_BYTES))
                    digest.update(block)
                    if output is not None:
                        output.write(block)
                    remaining -= len(block)
            finally:
                if output is not None:
                    import os
                    output.flush()
                    os.fsync(output.fileno())
                    output.close()
            if digest.hexdigest() != row.sha256:
                raise ValueError("geometry reuse changes any original archive member bytes")
        reader.finish()
    finally:
        chunks.close()


def materialize_geometry_inputs(archive_path, definition, census, raw_evidence, destination):
    """First authenticate ALL original members, then copy only consumer operands.

    Both passes preserve bounded chunk memory and verify the exact original raw
    compressed byte denominator. Any failure is retained; it grants no retry of
    a native operator. The immutable original archive/census remains untouched.
    """
    if type(definition) is not NativeSubworkDefinition or type(census) is not DurableRawFileCensus:
        raise ValueError("geometry reuse needs original typed definition and complete census")
    definition.__post_init__()
    census.__post_init__()
    if type(raw_evidence) is not c.FileEvidence:
        raise ValueError("geometry reuse needs the exact original raw archive byte binding")
    raw_evidence.__post_init__()
    expected = {Path(row.relative_path).name for row in census.files}
    if not set(REQUIRED_FILES).issubset(expected):
        raise ValueError("geometry reuse omits a required original consumer operand")
    destination = Path(destination)
    if not destination.is_dir() or destination.is_symlink():
        raise ValueError("geometry reuse requires an actual selected fresh directory")
    if any((destination / name).exists() for name in REQUIRED_FILES):
        raise ValueError("geometry reuse refuses an existing operand; inspect retained custody")
    _scan_archive(archive_path, definition, census, raw_evidence)
    _scan_archive(archive_path, definition, census, raw_evidence, destination)
    return tuple(row for row in census.files if Path(row.relative_path).name in REQUIRED_FILES)


class GeometryReuseRunner(DurablePreparationRunner):
    """Use the unchanged isolated launcher/whole36 census for fresh models only."""

    def _entry_target(self):
        path = Path(__file__).with_name("geometry_reuse_native_entry.py")
        module = "empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse_native_entry"
        return module, "selected_child", path, "src/" + module.replace(".", "/") + ".py"

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        contract = context.prepared_invocation
        if (contract is None or contract.native_work is None or contract.native_work.isolated_selection is None
                or contract.native_work.definitions != self.selected_definitions
                or contract.native_work.isolated_selection.entry_module != self._entry_target()[0]):
            raise ValueError("SOFTWARE: geometry reuse requires its exact complete actual specialist preparation before contact")
        contract.validate_context(context)
        return super().execute_streaming_with_native_subwork(context, native_subwork, emitter, progress)
