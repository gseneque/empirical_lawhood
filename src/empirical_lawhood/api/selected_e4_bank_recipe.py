# SPDX-License-Identifier: MPL-2.0
"""Guarded current publication of declared E4 scientific bank metadata.

Original E3 products and publications are replayed before new metadata is
published. These publications contain no new source qualification or authority.
"""
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import re

from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_bank_recipe as domain
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from .matrix_selected_e3_e4_runtime import authenticate_selected_e3_public_package, authenticate_selected_e3_assay
from empirical_lawhood.infrastructure.numerical_provenance import observe_implementation_source
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane
from empirical_lawhood.infrastructure.source_closure import capture_admitted_target_source, capture_target_closure, require_admitted_target_source_current
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactPublicationCommit, ArtifactPublicationIntent, ArtifactPublicationScope, ArtifactWriteRequest, ArtifactWriteResult, artifact_custody_limits
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection, ExperimentDependency
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding


def _current_selection(*, project_root, artifact_writer, execution, _admitted_source=None):
    if type(execution) is not ExecutionSelection or not isinstance(artifact_writer, ExternalArtifactPlane):
        raise TypeError("selected E4 recipe publication requires actual declared execution and guarded custody")
    execution.__post_init__()
    if (execution.workers is None or execution.environment_id is None or execution.source_snapshot is None
            or execution.output_root is None):
        raise ValueError("selected E4 recipe requires explicit concurrency, environment, source and output selections")
    root = Path(project_root).resolve(strict=True)
    if Path(execution.output_root).resolve(strict=True) != Path(artifact_writer.root.contract.canonical_path).resolve(strict=True):
        raise ValueError("selected E4 recipe output selection differs from actual guarded custody")
    if _admitted_source is None:
        admitted = capture_admitted_target_source(root)
    else:
        admitted = _admitted_source
        require_admitted_target_source_current(root, admitted)
    if execution.source_snapshot.object_schema == RecursiveImplementationBinding.SCHEMA:
        binding = RecursiveImplementationBinding(*observe_implementation_source(root, _admitted_source=admitted))
        if execution.source_snapshot != ObjectIdentity.from_record("recursive-member.implementation", binding):
            raise ValueError("selected E4 recipe changes its current declared implementation source")
    else:
        from .prospective_experiment import _selected_source_closure
        captured = capture_target_closure(root, "selected-e4.bank-recipe.current-source", _admitted_source=admitted)
        _selected_source_closure(captured.closure, execution.source_snapshot)
        require_admitted_target_source_current(root, admitted)
    return root, admitted



def authenticate_selected_e4_bank_recipe_inputs(*, inputs, project_root, artifact_writer, execution, summary_record_id=None,
        _admitted_source=None):
    """Replay actual original science/custody and current source; publish nothing."""
    if type(inputs) is not domain.SelectedE4BankRecipeSourceInputs:
        raise TypeError("selected E4 recipe authentication requires its exact typed source bundle")
    inputs.__post_init__()
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution,
        _admitted_source=_admitted_source)
    from empirical_lawhood.api.recursive_operations import operation_catalog
    summary = authenticate_selected_e3_public_package(writer=artifact_writer, public=inputs.original_public_package,
        upstream_products=inputs.original_products, codecs=operation_catalog()[2], summary_record_id=summary_record_id,
        response_criterion=inputs.original_preparation.mathematical_protocol,
        prefix_policies=tuple(value for value in inputs.original_preparation.manifest.native_specification.selection.prefix_policies
            if old.identity(value) == inputs.recipe.prefix_policy), original_preparation=inputs.original_preparation)
    authenticate_selected_e3_assay(public=inputs.original_public_package, upstream_products=inputs.original_products,
        assay=inputs.assay, assay_publication=inputs.assay_publication, template_publication=inputs.template_publication,
        criterion=inputs.original_preparation.mathematical_protocol, writer=artifact_writer)
    for publication, record in ((inputs.preparation_publication, inputs.original_preparation),
            (inputs.assay_publication, inputs.assay)):
        authenticate_publication(artifact_writer, publication, record)
    authenticate_publication(artifact_writer, inputs.template_publication)
    original = inputs.original_preparation.manifest
    for record, publication in ((original.reservation.allocation, original.reservation.publication),
            (original.native_specification.selection, original.native_specification.publication),
            (original.audit, original.audit_publication)):
        authenticate_publication(artifact_writer, publication, record)
    for publication in original.audit.prior_corpus:
        authenticate_publication(artifact_writer, publication)
    # Complete allocation and stream collisions refuse before publication.
    domain.recipe_allocation(inputs)
    require_admitted_target_source_current(root, admitted)
    return summary


@dataclass(frozen=True, slots=True)
class SelectedE4BankRecipePublicationResult:
    recipe: domain.SelectedE4BankRecipe
    source_inputs: domain.SelectedE4BankRecipeSourceInputs
    provenance: NumericalProducingProvenance
    banks: tuple
    programmes: tuple
    index: domain.SelectedE4BankRecipePublicationIndex
    publications: tuple
    record_paths: tuple
    requirements: tuple[ExperimentDependency, ...]

    def __post_init__(self):
        if (type(self.banks) is not tuple or type(self.programmes) is not tuple
                or type(self.publications) is not tuple or type(self.record_paths) is not tuple
                or type(self.requirements) is not tuple):
            raise TypeError("selected E4 metadata publication result requires immutable outer collections")
        if tuple(key for key, _ in self.banks) != domain.PHASES or tuple(key for key, _ in self.programmes) != domain.PHASES:
            raise ValueError("selected E4 metadata result omits a declared full phase")
        for rows in (self.publications, self.record_paths):
            if any(type(row) is not tuple or len(row) != 2 for row in rows):
                raise TypeError("selected E4 metadata result requires immutable named rows")
            if tuple(key for key, _ in rows) != tuple(sorted({key for key, _ in rows})):
                raise ValueError("selected E4 metadata result aliases its publication census")
        if tuple(key for key, _ in self.publications) != tuple(key for key, _ in self.record_paths):
            raise ValueError("selected E4 metadata result paths differ from actual publication census")


def _metadata_keys():
    return tuple(sorted(("allocation", "selection", "criterion", "recipe", "source-inputs", "provenance", "index",
        *(phase + "." + key for phase in domain.PHASES for key in ("responses", "bank", "programme")))))


def _metadata_scope(inputs, writer, relative):
    return ArtifactPublicationScope("selected-e4.bank-recipe." + inputs.recipe.record_id,
        writer.root.contract.storage_root_id, relative, VisibilityCeiling.PROSPECTIVE, OutcomeAccess.OUTCOME_BLIND)


def _metadata_namespace(*, inputs, writer, directory):
    """Admit only finite metadata names and the existing owner's controls.

    This preliminary inspection grants no custody verdict. The ordinary
    immutable write/replay owner reauthenticates each exact expected payload
    and completes an interrupted exact publication intent.
    """
    if not directory.exists():
        return
    plane = Path(writer.root.contract.canonical_path).resolve(strict=True)
    relative = directory.relative_to(plane).as_posix()
    scope = _metadata_scope(inputs, writer, relative)
    names = {key + ".json" for key in _metadata_keys()}
    top = names | {name + ".manifest.json" for name in names} | {".publication-batches"}
    locks = {".artifact-pair." + sha256((name + "\0" + name + ".manifest.json").encode()).hexdigest()[:24] + ".lock"
        for name in names}
    count = 0
    for path in directory.iterdir():
        count += 1
        if count > 3 * len(names) + 1 or path.is_symlink():
            raise PermissionError("selected E4 recipe metadata has a foreign, symbolic or oversized namespace")
        writer.root.resolve(path.relative_to(plane).as_posix(), for_write=False)
        if path.name in locks:
            if not path.is_file() or path.stat().st_size != 0:
                raise PermissionError("selected E4 recipe substitutes an operational publication lock")
        elif path.name not in top or (path.name != ".publication-batches" and not path.is_file()):
            raise PermissionError("selected E4 recipe metadata contains a foreign or orphan path")
    controls = directory / ".publication-batches"
    if not controls.exists():
        return
    if not controls.is_dir() or controls.is_symlink():
        raise PermissionError("selected E4 recipe publication controls are not an ordinary guarded directory")
    selected = controls / scope.fingerprint()[:24]
    if any(path != selected or path.is_symlink() or not path.is_dir() for path in controls.iterdir()):
        raise PermissionError("selected E4 recipe metadata includes another publication scope")
    if not selected.exists():
        return
    from .recursive_qualified_parents import MAX_PARENT_BYTES
    count = 0
    for path in selected.iterdir():
        count += 1
        if count > 3 * len(names) or path.is_symlink() or not path.is_file():
            raise PermissionError("selected E4 recipe publication control census is foreign or unbounded")
        writer.root.resolve(path.relative_to(plane).as_posix(), for_write=False)
        if re.fullmatch(r"\.publication-batch\.[a-f0-9]{24}\.lock", path.name):
            if path.stat().st_size != 0:
                raise PermissionError("selected E4 recipe publication lock carries foreign bytes")
            continue
        kind = ArtifactPublicationCommit if path.name.endswith(".commit.json") else (
            ArtifactPublicationIntent if path.name.endswith(".intent.json") else None)
        if kind is None:
            raise PermissionError("selected E4 recipe has an unowned publication control")
        maximum = writer.custody_limits.publication_marker_bytes or MAX_PARENT_BYTES
        raw = read_bounded_bytes(path, maximum_bytes=maximum)
        record = decode_canonical_bytes(raw, kind, maximum_bytes=maximum)
        if (record.canonical_bytes() != raw or record.publication_scope != scope or len(record.members) != 1
                or path.name != record.publication_batch_id + (".commit.json" if kind is ArtifactPublicationCommit else ".intent.json")):
            raise PermissionError("selected E4 recipe substitutes its exact existing publication control")
        member, = record.members
        leaf = Path(member.relative_path).name
        key = leaf.removesuffix(".json")
        if (leaf not in names or member.relative_path != relative + "/" + leaf
                or member.logical_artifact_id != "selected-e4.bank-recipe." + key.lower() + "." + member.physical_sha256):
            raise PermissionError("selected E4 recipe publication control contains a foreign or orphan payload")


def _selected_metadata_directory(*, inputs, writer, project_root, metadata_directory):
    if not isinstance(writer, ExternalArtifactPlane):
        raise TypeError("selected E4 metadata requires the actual guarded artifact plane")
    directory = Path(metadata_directory)
    plane = Path(writer.root.contract.canonical_path).resolve(strict=True)
    root = Path(project_root).resolve(strict=True)
    if (not directory.is_absolute() or directory != directory.resolve(strict=False)
            or not directory.is_relative_to(plane) or directory == plane or directory.is_relative_to(root)):
        raise ValueError("selected E4 metadata needs its exact separate guarded directory outside the checkout")
    relative = directory.relative_to(plane).as_posix()
    writer.root.verify(for_write=True)
    writer.root.resolve(relative + "/allocation.json", for_write=True)
    if directory.exists():
        if not directory.is_dir():
            raise ValueError("selected E4 metadata destination is not an ordinary guarded directory")
        _metadata_namespace(inputs=inputs, writer=writer, directory=directory)
    else:
        preflight_authoring_output_directory(directory=directory, repo_root=root, artifact_writer=writer)
    return directory


def _publication_from_manifest(writer, manifest):
    """Current read observation; never rewrite retained embedded created flags."""
    from empirical_lawhood.runtime.artifacts import ArtifactManifest
    from empirical_lawhood.runtime.execution import VerifiedArtifactInput
    if type(manifest) not in (ArtifactManifest, VerifiedArtifactInput):
        raise TypeError("publication replay requires its exact manifest or verified input")
    relative = manifest.materialization.relative_path + ".manifest.json"
    raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False),
        maximum_bytes=writer.custody_limits.manifest_bytes)
    actual = writer.read_manifest(manifest.materialization.relative_path, maximum_bytes=writer.custody_limits.manifest_bytes)
    expected = (manifest.logical, manifest.materialization)
    if ((actual.logical, actual.materialization) != expected
            or type(manifest) is ArtifactManifest and actual != manifest):
        raise PermissionError("selected E4 recipe metadata manifest changed during replay")
    sidecar = writer._manifest_materialization(logical_artifact_id=actual.logical.logical_artifact_id,
        relative_path=relative, payload=raw)
    writer.verify_manifest(actual)
    writer.verify(sidecar)
    return ArtifactWriteResult(actual.logical, actual.materialization, sidecar, False)


def _metadata_record_size(writer, size_bytes, *, maximum_bytes=None):
    """Keep exact record sizes and explicit owning allowances across boundaries."""
    if type(size_bytes) is not int or size_bytes < 1:
        raise ValueError("selected E4 metadata needs its positive exact declared record size")
    if maximum_bytes is not None and (type(maximum_bytes) is not int or maximum_bytes < 1):
        raise ValueError("selected E4 owning metadata maximum_bytes must be positive or None")
    if maximum_bytes is not None and size_bytes > maximum_bytes:
        raise ValueError(f"selected E4 metadata record has {size_bytes} bytes; owning maximum_bytes is {maximum_bytes}")
    limits = artifact_custody_limits(writer)
    if limits.exceeds("in_memory_payload_bytes", size_bytes):
        raise ValueError(f"selected E4 metadata record has {size_bytes} bytes; selected in_memory_payload_bytes is {limits.in_memory_payload_bytes}")
    return size_bytes


def _read_exact_record(writer, publication, kind, *, maximum_bytes=None):
    # Publication authentication refreshes body, sidecar and commit marker.
    # Parent grant metadata has a separate role and supplies no record ceiling.
    from empirical_lawhood.infrastructure.publication_metadata import read_published_canonical_record
    _metadata_record_size(writer, publication.materialization.size_bytes, maximum_bytes=maximum_bytes)
    record = read_published_canonical_record(writer, publication, kind,
        maximum_bytes=publication.materialization.size_bytes)
    if (type(publication) is not ArtifactWriteResult or publication.logical.payload_schema != record.SCHEMA
            or publication.logical.profile is not ArtifactProfile.CANONICAL_JSON
            or publication.logical.media_type != "application/json"
            or publication.logical.content_sha256 != record.fingerprint()
            or publication.materialization.physical_sha256 != record.fingerprint()
            or publication.materialization.size_bytes != record.canonical_size_bytes()
            or publication.logical.logical_artifact_id != publication.materialization.logical_artifact_id
            or publication.materialization.compression != "none"):
        raise ValueError("selected E4 metadata requires its exact original uncompressed canonical publication")
    return record


def _requirements():
    # Exposed DEV acquisition requires no invented issue/source-qualification
    # ceremony. Its ordinary actual source/parent/native validation remains.
    return tuple(ExperimentDependency("source-qualification-required." + phase.lower(), DependencyKind.SCIENTIFIC_EVIDENCE,
        "New " + phase + " source bank requires its own exact independently produced source qualifications before entry; original E3 qualifiers are retained originals only.",
        "source-qualification") for phase in domain.PHASES if phase != "DEVELOPMENT")


def load_selected_e4_bank_recipe(*, inputs, project_root, artifact_writer, metadata_directory, execution):
    """Replay the exact completed immutable index; no new publications or flags."""
    if type(inputs) is not domain.SelectedE4BankRecipeSourceInputs:
        raise TypeError("selected E4 recipe authentication requires its exact typed source bundle")
    inputs.__post_init__()
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution)
    authenticate_selected_e4_bank_recipe_inputs(inputs=inputs, project_root=project_root,
        artifact_writer=artifact_writer, execution=execution, _admitted_source=admitted)
    directory = Path(metadata_directory)
    plane = Path(artifact_writer.root.contract.canonical_path).resolve(strict=True)
    if not directory.is_absolute() or directory != directory.resolve(strict=True) or not directory.is_relative_to(plane):
        raise ValueError("selected E4 retained recipe directory must be its exact guarded canonical path")
    relative = directory.relative_to(plane).as_posix()
    _metadata_namespace(inputs=inputs, writer=artifact_writer, directory=directory)
    if relative in ("", "."):
        raise ValueError("selected E4 retained recipe needs its own metadata directory")
    manifest = artifact_writer.read_manifest(relative + "/index.json", maximum_bytes=artifact_writer.custody_limits.manifest_bytes)
    index_publication = _publication_from_manifest(artifact_writer, manifest)
    index = _read_exact_record(artifact_writer, index_publication, domain.SelectedE4BankRecipePublicationIndex)
    if (index.record_id != "bank-recipe-index." + inputs.recipe.record_id
            or index.recipe != inputs.recipe.identity or index.source_inputs != inputs.identity):
        raise PermissionError("selected E4 retained index belongs to another exact recipe/source bundle")
    publications = dict(index.publications)
    for key, publication in index.publications:
        expected_path = relative + "/" + key + ".json"
        if (publication.materialization.relative_path != expected_path
                or publication.logical.logical_artifact_id != "selected-e4.bank-recipe." + key.lower() + "." + publication.logical.content_sha256):
            raise PermissionError("selected E4 retained index substitutes its original selected publication namespace")
    if _read_exact_record(artifact_writer, publications["recipe"], domain.SelectedE4BankRecipe) != inputs.recipe:
        raise PermissionError("selected E4 retained recipe differs from the original immutable selection")
    if _read_exact_record(artifact_writer, publications["source-inputs"], domain.SelectedE4BankRecipeSourceInputs) != inputs:
        raise PermissionError("selected E4 retained source bundle differs from original exact input custody")
    provenance = _read_exact_record(artifact_writer, publications["provenance"], NumericalProducingProvenance)
    current = capture_matrix_provenance(project_root=root, expected_code_sha256=provenance.code_sources_sha256,
        expected_lock_sha256=provenance.dependency_lock_sha256, _admitted_source=admitted)
    if provenance.identity != index.provenance or provenance.observed_git_head != current.observed_git_head:
        raise PermissionError("selected E4 retained bank changes its frozen actual producing source")
    allocation = _read_exact_record(artifact_writer, publications["allocation"], old.ScheduledAllocation)
    selection = _read_exact_record(artifact_writer, publications["selection"], old.ScheduledSelection)
    criterion = _read_exact_record(artifact_writer, publications["criterion"], type(inputs.original_preparation.mathematical_protocol))
    if allocation != domain.recipe_allocation(inputs) or criterion != inputs.original_preparation.mathematical_protocol:
        raise PermissionError("selected E4 retained allocation/criterion differs from complete original recipe")
    banks, programmes = [], []
    for phase in domain.PHASES:
        kind = domain.SelectedE3E4DevelopmentBank if phase == "DEVELOPMENT" else domain.SelectedE4PhaseBank
        programme_kind = domain.SelectedE3E4DevelopmentProgramme if phase == "DEVELOPMENT" else domain.SelectedE4PhaseProgramme
        bank = _read_exact_record(artifact_writer, publications[phase + ".bank"], kind)
        programme = _read_exact_record(artifact_writer, publications[phase + ".programme"], programme_kind)
        responses = _read_exact_record(artifact_writer, publications[phase + ".responses"], domain.ScheduledResponseSelection)
        # Embedded original publication descriptors, including created, remain
        # exactly the committed index values. Only index's new read observation
        # has created=False.
        if (bank.reservation.publication != publications["allocation"] or bank.specification.publication != publications["selection"]
                or bank.specification.selection != selection or bank.forecast_design.criterion_publication != publications["criterion"]
                or bank.response_selection_publication != publications[phase + ".responses"] or bank.response_selection != responses
                or bank.provenances != (provenance,) or dict(index.banks)[phase] != bank.identity
                or dict(index.programmes)[phase] != programme.identity or domain.recipe_programme(bank, phase) != programme):
            raise PermissionError("selected E4 retained bank substitutes its original complete publication joins")
        domain.validate_selected_e4_recipe_bank(inputs, bank, phase)
        banks.append((phase, bank))
        programmes.append((phase, programme))
    require_admitted_target_source_current(root, admitted)
    publications["index"] = index_publication
    paths = tuple((key, artifact_writer.root.resolve(value.materialization.relative_path, for_write=False))
        for key, value in sorted(publications.items()))
    return SelectedE4BankRecipePublicationResult(inputs.recipe, inputs, provenance, tuple(banks), tuple(programmes), index,
        tuple(sorted(publications.items())), paths, _requirements())


def publish_selected_e4_bank_recipe(*, inputs, project_root, artifact_writer, metadata_directory, execution,
        _admitted_source=None):
    """Publish a complete immutable three-phase bank, retaining missing new gates.

    Every generated descriptor is the actual immutable owner's replay result.
    Exact partial publications resume at the same destination. Foreign bytes,
    scopes or payloads refuse, and the completed index is published last.
    """
    if type(inputs) is not domain.SelectedE4BankRecipeSourceInputs:
        raise TypeError("selected E4 bank publisher requires exact recipe source inputs")
    inputs.__post_init__()
    directory = _selected_metadata_directory(inputs=inputs, writer=artifact_writer,
        project_root=project_root, metadata_directory=metadata_directory)
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution,
        _admitted_source=_admitted_source)
    authenticate_selected_e4_bank_recipe_inputs(inputs=inputs, project_root=project_root,
        artifact_writer=artifact_writer, execution=execution, _admitted_source=admitted)
    provenance = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    if provenance.observed_git_head != admitted.implementation_commit:
        raise ValueError("selected E4 metadata must retain actual current producing provenance")
    plane = Path(artifact_writer.root.contract.canonical_path)
    relative = directory.relative_to(plane).as_posix()
    publications, paths = {}, {}
    # This full original carrier is known before the first new publication.
    # Reuse its exact immutable bytes within this invocation, not an authority verdict.
    source_inputs_raw = inputs.canonical_bytes()
    _metadata_record_size(artifact_writer, len(source_inputs_raw))

    def publish(key, record, *, payload=None):
        raw = record.canonical_bytes() if payload is None else payload
        _metadata_record_size(artifact_writer, len(raw))
        path = relative + "/" + key + ".json"
        request = ArtifactWriteRequest("selected-e4.bank-recipe." + key.lower() + "." + record.fingerprint(),
            path, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
            "selected-e4.bank-recipe." + inputs.recipe.record_id, relative, raw,
            VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
        artifact_writer.write(request)
        # Embed a real replay observation on both first and resumed calls.
        # Never synthesize/normalize a historical created flag.
        result = artifact_writer.write(request)
        if result.created is not False:
            raise PermissionError("selected E4 immutable publication did not produce its actual replay result")
        old._publication(result, record)
        publications[key], paths[key] = result, artifact_writer.root.resolve(path, for_write=False)
        return result

    allocation = domain.recipe_allocation(inputs)
    reservation = old.ScheduledReservation("reservation." + inputs.recipe.record_id, allocation, publish("allocation", allocation))
    selection = domain.recipe_selection(inputs, reservation)
    specification = old.ScheduledSpecification("specification." + inputs.recipe.record_id, selection, publish("selection", selection))
    criterion = publish("criterion", inputs.original_preparation.mathematical_protocol)
    publish("recipe", inputs.recipe)
    publish("source-inputs", inputs, payload=source_inputs_raw)
    publish("provenance", provenance)
    banks, programmes = [], []
    for phase in domain.PHASES:
        # One full scientific source is live at a time; the resulting records
        # retain only original compact subjects and the complete source census.
        descriptors, responses = domain.recipe_responses(inputs, reservation, specification, provenance, phase)
        response_publication = publish(phase + ".responses", responses)
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_records import (
            SelectedE3E4DevelopmentBank, SelectedE3E4ForecastDesign, selected_e3_fit_target,
        )
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PhaseBank
        design = SelectedE3E4ForecastDesign("forecast-design." + inputs.recipe.record_id, inputs.original_public_package,
            old.identity(allocation), inputs.original_preparation.mathematical_protocol, criterion,
            fit_target=selected_e3_fit_target(inputs.original_public_package))
        values = ("bank." + inputs.recipe.record_id + "." + phase.lower(), reservation, specification, (provenance,),
            descriptors, inputs.original_preparation.manifest.audit, inputs.original_preparation.manifest.audit_publication,
            design, responses, response_publication, dict(inputs.recipe.population_designs)[phase])
        bank = SelectedE3E4DevelopmentBank(*values) if phase == "DEVELOPMENT" else SelectedE4PhaseBank(*values, phase)
        programme = domain.recipe_programme(bank, phase)
        publish(phase + ".bank", bank)
        publish(phase + ".programme", programme)
        banks.append((phase, bank))
        programmes.append((phase, programme))
    index = domain.SelectedE4BankRecipePublicationIndex("bank-recipe-index." + inputs.recipe.record_id,
        inputs.recipe.identity, inputs.identity, provenance.identity,
        tuple((phase, bank.identity) for phase, bank in banks),
        tuple((phase, programme.identity) for phase, programme in programmes), tuple(sorted(publications.items())))
    require_admitted_target_source_current(root, admitted)
    _metadata_namespace(inputs=inputs, writer=artifact_writer, directory=directory)
    publish("index", index)
    _metadata_namespace(inputs=inputs, writer=artifact_writer, directory=directory)
    requirements = _requirements()
    return SelectedE4BankRecipePublicationResult(inputs.recipe, inputs, provenance, tuple(banks), tuple(programmes), index,
        tuple(sorted(publications.items())), tuple(sorted(paths.items())), requirements)


def authenticate_selected_e4_bank_recipe_publication_index(*, inputs, bank, phase, index, artifact_writer):
    """Authenticate retained exact generated bank custody without republishing it."""
    if type(index) is not domain.SelectedE4BankRecipePublicationIndex:
        raise TypeError("selected E4 recipe requires its exact retained publication index")
    index.__post_init__()
    domain.validate_selected_e4_recipe_bank(inputs, bank, phase)
    if (index.recipe != inputs.recipe.identity or index.source_inputs != inputs.identity
            or dict(index.banks).get(phase) != bank.identity or index.provenance != bank.provenances[0].identity):
        raise PermissionError("selected E4 recipe index differs from actual retained source lineage")
    for key, publication in index.publications:
        authenticate_publication(artifact_writer, publication)
    return None
