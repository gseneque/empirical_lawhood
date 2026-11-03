# SPDX-License-Identifier: MPL-2.0
"""Held release-validation E4 input builder over actual completed E3 custody.

Every new group, stream, source gate and approval selected by this module is
exposed software-conformance material. It establishes no scientific freshness,
sampling warrant, transport applicability or real qualification. Existing E3
products, grants, receipts, source bytes and infinite calibration stay unchanged.
"""

from tests.matrix_e4_structure_support import disclosed_structure, publish_secondary
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from itertools import product
import json
import os
from pathlib import Path
from types import SimpleNamespace

from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_preparation import ProtectedE3PreparationSelection
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as bridge
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as dev
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as development
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as e4
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledCalibrationCriterion, ScheduledResponseSelection
from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
from empirical_lawhood.api.matrix_selected_runtime import _published_input
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256, read_bounded_bytes
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.prospective_experiment import source_filename
from tests.matrix_selected_original_public_fixture import EL_ROOT, actual_publication, original_selected_package, read_selection

ROOT = Path(__file__).resolve().parents[1]
DISCLOSURE = "EXPOSED_RELEASE_VALIDATION_NEW_TEST_AUTHORITY_NOT_SCIENTIFIC_QUALIFICATION"
SELECTION_KEYS = frozenset(("record_id", "original_e3_selection", "namespace", "output_relative_path",
    "workers", "numerical_threads", "memory_bytes_per_task", "source_bytes_per_task", "output_bytes_per_task",
    "minimum_free_bytes", "development_groups", "calibration_groups", "confirmation_groups",
    "wave_group_count", "confidence", "factor_levels", "revision_specification_path", "confirmation_selection_path",
    "preparation_recipe_path"))


def held_selection(path):
    """Select copied release parameters; omitted choices never gain defaults."""
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to(EL_ROOT):
        raise ValueError("E4 held launch selection must be explicitly retained on EL")
    value = json.loads(read_bounded_bytes(path, maximum_bytes=128 * 1024))
    if type(value) is not dict or set(value) != SELECTION_KEYS:
        raise ValueError("E4 held selection changes its closed declared input census")
    from empirical_lawhood.kernel.serialization import validate_relative_locator, validate_stable_id
    validate_stable_id(value["record_id"])
    validate_stable_id(value["namespace"])
    validate_relative_locator(value["output_relative_path"])
    for key in ("workers", "numerical_threads", "memory_bytes_per_task", "source_bytes_per_task",
            "output_bytes_per_task", "minimum_free_bytes", "development_groups", "calibration_groups",
            "confirmation_groups", "wave_group_count"):
        if type(value[key]) is not int or value[key] < 1:
            raise ValueError("E4 operational and population choices require explicit positive integers")
    if value["workers"] < 4 or value["numerical_threads"] != 1:
        raise ValueError("new E4 release launches require at least four selected workers and one numerical thread")
    if tuple(value[key] for key in ("development_groups", "calibration_groups", "confirmation_groups")) != (32, 64, 64):
        raise ValueError("this release-validation harness preserves the selected32/64/64 acceptance populations")
    if not 1 <= value["wave_group_count"] <= 8:
        raise ValueError("the supported protected acquisition component holds one to eight whole groups")
    levels = value["factor_levels"]
    if type(levels) is not dict or set(levels) != {"temperature", "friction", "coupling"}:
        raise ValueError("release factors require the supported three explicit physical axes")
    if any(type(rows) is not list or len(rows) != 3 or not all(type(v) is str for v in rows) for rows in levels.values()):
        raise ValueError("release factor levels require exact low/center/high Decimal text")
    for rows in levels.values():
        low, center, high = map(D, rows)
        if not 0 < low < center < high:
            raise ValueError("release physical axes must be positive and strictly ordered")
    confidence = D(value["confidence"])
    if not 0 < confidence < 1:
        raise ValueError("release confidence must be explicitly declared in (0,1)")
    for key in ("original_e3_selection", "revision_specification_path", "confirmation_selection_path", "preparation_recipe_path"):
        member = Path(value[key])
        if not member.is_absolute() or not member.resolve(strict=True).is_relative_to(EL_ROOT):
            raise ValueError("E4 source/settings paths must name actual retained EL files")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        if os.environ.get(name) != "1":
            raise ValueError("select one numerical thread explicitly before importing/running the acceptance harness: " + name)
    affinity = os.sched_getaffinity(0) if hasattr(os, "sched_getaffinity") else range(os.cpu_count() or 1)
    if len(affinity) < value["workers"]:
        raise ValueError("selected E4 launch exceeds current usable CPU slots")
    return SimpleNamespace(**value)


def publication(writer, record, name, *, lineage_parents=()):
    """Publish new disclosed metadata through the actual guarded owner."""
    from empirical_lawhood.runtime.artifacts import derived_outcome_access
    from empirical_lawhood.kernel.evidence import inherited_visibility
    access=derived_outcome_access(old.OutcomeAccess.OUTCOME_BLIND,*(value.outcome_access for value in lineage_parents))
    ceilings=tuple(value.visibility_ceiling for value in lineage_parents)
    return writer.write(ArtifactWriteRequest(name, "release-validation/" + name + ".json",
        record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", "publication." + name,
        "release-validation", record.canonical_bytes(), inherited_visibility(ceilings,access),
        ceilings,access,lineage_parents=lineage_parents))


def original_preparation(originals):
    rows = tuple(reference for reference in originals.retained.instance.sources
        if reference.object_schema == ProtectedE3PreparationSelection.SCHEMA)
    if len(rows) != 1:
        raise PermissionError("original E3 authoring lacks its exact retained scientific preparation")
    reference, = rows
    raw = originals.retained.payloads[source_filename(reference)]
    record = decode_canonical_bytes(raw, ProtectedE3PreparationSelection, maximum_bytes=len(raw))
    if (record.canonical_bytes() != raw or record.fingerprint() != reference.object_fingerprint
):
        raise PermissionError("original E3 scientific preparation changed")
    return record


def original_assay(originals):
    task = next(row for row in originals.original_plan.tasks
        if row.capability.capability_key == "matrix-e3-protected.physical-forecast")
    spec, = (row for row in task.external_inputs if row.expected_payload_schema == ScheduledResponseProtocol.SCHEMA)
    protocol = _published_input(originals.writer, originals.issued_package.run_plan_id, spec, ScheduledResponseProtocol)
    from empirical_lawhood.infrastructure.provider_input_custody import provider_input_location
    relative, _, _ = provider_input_location(originals.writer, originals.issued_package.run_plan_id,
        protocol.templates.array_artifact.artifact_id)
    manifest = originals.writer.read_manifest(relative, maximum_bytes=originals.writer.custody_limits.manifest_bytes)
    stored = actual_publication(originals.writer, manifest)
    if (manifest.logical.content_sha256, manifest.materialization.size_bytes) != (
            sha256(originals.template_raw).hexdigest(), len(originals.template_raw)):
        raise PermissionError("actual original E3 four-action instrument loses its authenticated bytes")
    return protocol, stored


def selected_populations(originals, selected):
    """Build new declared sources; every immutable E3 scientific operand is actual."""
    original = original_preparation(originals)
    from empirical_lawhood.api.matrix_selected_e3_e4_runtime import _authenticate_selected_projection
    # Check the bounded producer-pinned join before publishing new populations;
    # the original full closure was authenticated by this operation already.
    model_binding, = (value.prior_execution for value in originals.bindings
        if value.record == old.identity(originals.package.models))
    _authenticate_selected_projection(frozen=MatrixSelectedPublicPackage.from_package(originals.package),
        criterion=original.mathematical_protocol,
        policies=original.manifest.native_specification.selection.prefix_policies, preparation=original,
        binding=model_binding, package=originals.issued_package,
        execution_plan=originals.original_plan, writer=originals.writer)
    prototype, templates_publication = original_assay(originals)
    provenance = capture_matrix_provenance(project_root=ROOT)
    current = original.manifest
    from tests.matrix_selected_e4_preparation_recipe import load_preparation_recipe
    recipe = load_preparation_recipe(selected.preparation_recipe_path, original)
    families = tuple(value.family_id for value in recipe.coordinates)
    axes = tuple(tuple(map(D, selected.factor_levels[name])) for name in ("temperature", "friction", "coupling"))
    factors = tuple(ScheduledProgrammeFactor(name, "LINEAR", *values)
        for name, values in zip(("temperature", "friction", "coupling"), axes, strict=True))
    corners = (*product(*((values[0], values[2]) for values in axes)), tuple(values[1] for values in axes))
    nominal = current.reservation.allocation
    coordinates, policies = [], {}
    for fi, family in enumerate(families):
        base = next(value for value in recipe.coordinates if value.family_id == family)
        policy_pin = dict(current.native_specification.selection.coordinate_policies)[recipe.prototype]
        policy = next(value for value in current.native_specification.selection.prefix_policies if old.identity(value) == policy_pin)
        for ci, (temperature, friction, coupling) in enumerate(corners):
            name = selected.namespace + "." + str(fi) + "." + str(ci)
            coordinate = replace(base, coordinate_id="coordinate." + name,
                member=replace(base.member, member_id="member." + name, cross_coupling_gamma=coupling),
                primary_view=replace(base.primary_view, view_id="view.primary." + name,
                    bath_temperature=temperature, friction_gamma=friction),
                fine_view=replace(base.fine_view, view_id="view.fine." + name,
                    bath_temperature=temperature, friction_gamma=friction))
            coordinates.append(coordinate)
            policies[coordinate.coordinate_id] = policy
    coordinates = tuple(sorted(coordinates, key=lambda row: row.coordinate_id))
    populations = (("DEV", MatrixProgrammeRole.DEVELOPMENT, selected.development_groups),
        ("CAL", MatrixProgrammeRole.CALIBRATION, selected.calibration_groups),
        ("CONF", MatrixProgrammeRole.CONFIRMATION, selected.confirmation_groups))
    roots, scopes = [], []
    for label, role, count in populations:
        for fi, family in enumerate(families):
            local = tuple(row for row in coordinates if row.family_id == family)
            groups = tuple("group." + selected.namespace + "." + label.lower() + "." + str(fi) + "." + str(index).zfill(2)
                for index in range(count // len(families)))
            for group in groups:
                streams = tuple(MatrixHistorySeed(purpose, sha256((DISCLOSURE + "." + group + purpose).encode()).hexdigest())
                    for purpose in HISTORY_PURPOSES)
                for ci, coordinate in enumerate(local):
                    root = old.MatrixProgrammeRoot("root." + group + "." + str(ci), group, "regime." + coordinate.coordinate_id,
                        coordinate.coordinate_id, role, coordinate.clock_id)
                    roots.append(old.ScheduledRoot(root, old.coordinate_identity(coordinate), streams))
            scopes.append(old.ScheduledMatchedScope("scope." + selected.namespace + "." + label.lower() + "." + str(fi),
                role, groups, tuple(old.coordinate_identity(row) for row in local),
                "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"))
    allocation = replace(nominal, allocation_id="allocation." + selected.namespace, coordinates=coordinates,
        roots=tuple(sorted(roots, key=lambda row: row.root.root_id)),
        matched_scopes=tuple(sorted(scopes, key=lambda row: row.scope_id)))
    reservation = old.ScheduledReservation("reservation." + selected.namespace, allocation,
        publication(originals.writer, allocation, selected.namespace + ".allocation"))
    unique_policies = {old.identity(value).object_id: value for value in policies.values()}
    selection = old.ScheduledSelection("selection." + selected.namespace, old.identity(reservation),
        current.native_specification.selection.numerical_design,
        tuple(unique_policies[key] for key in sorted(unique_policies)),
        tuple((old.coordinate_identity(value), old.identity(policies[value.coordinate_id])) for value in coordinates))
    specification = old.ScheduledSpecification("specification." + selected.namespace, selection,
        publication(originals.writer, selection, selected.namespace + ".native-selection"))
    criterion = original.mathematical_protocol
    design = bridge.SelectedE3E4ForecastDesign("forecast-design." + selected.namespace,
        MatrixSelectedPublicPackage.from_package(originals.package), old.identity(allocation), criterion,
        publication(originals.writer, criterion, selected.namespace + ".actual-original-criterion"))
    banks, programmes = {}, {}
    index=ScheduledSourceIndex.from_shared(reservation=reservation,specification=specification,provenances=(provenance,))
    for label, role, count in populations:
        subjects=tuple(index.resolve(index.reference(source_id="source."+value.root.root_id,
            root_id=value.root.root_id,provenance=provenance.identity))
            for value in allocation.roots if value.root.role is role)
        protocols = []
        for subject in subjects:
            templates = replace(prototype.templates, operand_id="templates." + subject.root_id,
                source=old.identity(subject), producers=(old.identity(subject),))
            protocols.append(replace(prototype, protocol_id="protocol." + subject.root_id,
                public_source=ScheduledPublicSource.from_source(subject), templates=templates))
        panels = []
        for group in sorted({value.root.root.independent_group_id for value in subjects}):
            root = next(value for value in allocation.roots if value.root.independent_group_id == group)
            pair = tuple(ScheduledResponsePanel("panel." + group + "." + str(index), group, panel_role,
                "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES" if index == 0 else "FRESH_DECLARED_FUTURE_START_AT_CUTOFF",
                root.streams if index == 0 else tuple(MatrixHistorySeed(purpose,
                    sha256((DISCLOSURE + ".FUTURE." + group + purpose).encode()).hexdigest()) for purpose in HISTORY_PURPOSES))
                for index, panel_role in enumerate(("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")))
            panels.append((group, pair))
        calibration_criterion = None if label != "CAL" else ScheduledCalibrationCriterion(
            "criterion." + selected.namespace + ".native-calibration", "unit.selected-e4.whole-group", count,
            D(0), families, "COMPLETE_MATCHED_GROUP_MAX_ALL15_POSITIVE_LOG_ERROR_MINUS_PRE_FUTURE_POINT_NONUSE_INFINITY")
        responses = ScheduledResponseSelection("responses." + selected.namespace + "." + label.lower(), ObjectIdentity.from_record(allocation.allocation_id, allocation),
            tuple(protocols), tuple(panels), (templates_publication,), calibration_criterion)
        responses.validate_allocation(allocation)
        population_design = bridge.SelectedE3E4Design("design." + selected.namespace + "." + label.lower(),
            count, D(selected.confidence), factors, selected.wave_group_count)
        values = ("bank." + selected.namespace + "." + label.lower(), reservation, specification, (provenance,),
            tuple(value.reference for value in subjects), current.audit, current.audit_publication,
            design, responses, publication(originals.writer, responses, selected.namespace + "." + label.lower() + ".responses"),
            population_design)
        bank = bridge.SelectedE3E4DevelopmentBank(*values) if label == "DEV" else e4.SelectedE4PhaseBank(
            *values, "CALIBRATION" if label == "CAL" else "CONFIRMATION")
        programme = (bridge.SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id="programme." + selected.namespace + ".dev")
            if label == "DEV" else e4.SelectedE4PhaseProgramme.from_bank(bank,
                programme_id="programme." + selected.namespace + "." + label.lower()))
        banks[label], programmes[label] = bank, programme
    target, secondary = publish_secondary(originals.writer, banks["DEV"],
        Path(originals.writer.root.contract.canonical_path) / "release-validation" / selected.namespace / "early-secondary")
    return SimpleNamespace(banks=banks, programmes=programmes, original=original,
        provenance=provenance, template_raw=originals.template_raw,
        secondary_target=target, secondary_readout=secondary)


def task_budget(selected):
    # Explicit release-validation operational selection, not a claimed measured
    # science minimum or a production default. Actual admission still applies.
    return ResourceBudget(1, selected.memory_bytes_per_task, 0, None,
        selected.source_bytes_per_task, selected.output_bytes_per_task)


def write_selection(directory, *, protocol_id, records, fields, files=()):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    bindings = []
    for key, record in sorted(records.items()):
        raw = record.canonical_bytes()
        path = directory / (key + ".json")
        with path.open("xb") as stream:
            stream.write(raw)
        bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record(getattr(record, fields[key]), record),
            path.name, len(raw)))
    selection = ExperimentFileInputSelection("sources." + sha256(str(directory).encode()).hexdigest(),
        protocol_id, tuple(bindings), tuple(files))
    path = directory / "sources.json"
    path.write_bytes(selection.canonical_bytes())
    return path


def development_inputs(originals, populations, selected, directory):
    programme, bank = populations.programmes["DEV"], populations.banks["DEV"]
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    parents=selected_produced_input_parents(originals.writer,originals=originals.bindings)
    evidence = bridge.SelectedE3E4Evidence("evidence." + selected.namespace + ".dev", programme.identity, originals.bindings,parents)
    campaign = originals.retained.draft.campaign
    specification = development.SelectedE3E4ExperimentSpecification("experiment." + selected.namespace + ".dev",
        programme.identity, bank.identity, evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        *disclosed_structure(bank, budget=task_budget(selected)))
    resources = development.SelectedE3E4OperationalSelection("resources." + selected.namespace + ".dev",
        tuple((phase, task_budget(selected)) for phase in sorted(dev.PHASES)))
    directory.mkdir(parents=True, exist_ok=False)
    artifacts = dict(dev.contracts(programme, bank, evidence.identity, len(evidence.canonical_bytes()), produced_input_parents=evidence.produced_input_parents, secondary_readout=populations.secondary_readout)[4])
    sources = write_selection(directory / "sources", protocol_id=development.PROTOCOL_ID,
        records={"programme": programme, "bank": bank, "evidence": evidence, "campaign": campaign, "resources": resources, "secondary_readout": populations.secondary_readout},
        fields={"programme": "programme_id", "bank": "bank_id", "evidence": "record_id", "campaign": "campaign_id", "resources": "record_id", "secondary_readout": "record_id"},
        files=())
    # File selections may not escape their selected directory. Copy only the
    # authenticated immutable instrument, never original E3 run products.
    source_dir = sources.parent
    array_path = source_dir / "actual-original-e3-templates.npz"
    array_path.write_bytes(originals.template_raw)
    original_selection = decode_canonical_bytes(sources.read_bytes(), ExperimentFileInputSelection, maximum_bytes=None)
    selection = replace(original_selection, files=tuple(ExperimentFileInputBinding(key, artifact, "1.0.0",
        array_path.name, artifact.size_bytes) for key, artifact in sorted(artifacts.items())))
    sources.write_bytes(selection.canonical_bytes())
    assert all((artifact.sha256, artifact.size_bytes) == (sha256(originals.template_raw).hexdigest(), len(originals.template_raw))
        for artifact in artifacts.values())
    return specification, sources


def authenticate_originals(selected):
    return original_selected_package(project_root=ROOT, selection=read_selection(selected.original_e3_selection))


def retained_census(writer, run_ids):
    """Bounded streaming hashes of actual primary files; never reacquire native."""
    root = Path(writer.root.contract.canonical_path)
    values = {}
    for run_id in sorted(set(run_ids)):
        directory = root / "runs" / run_id
        for path in sorted(value for value in directory.rglob("*") if value.is_file()):
            if path.is_symlink():
                raise ValueError("retained acceptance custody refuses symlink")
            size, digest = bounded_file_sha256(path, maximum_bytes=path.stat().st_size)
            values[path.relative_to(root).as_posix()] = (size, digest, path.stat().st_mtime_ns)
    if not values:
        raise ValueError("actual original/phase run custody is absent")
    return values


# The helpers below are test orchestration only. The installed API still owns
# every load/prepare/author/run/read/recover operation and all native admission.

def execution_selection(originals, selected):
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
    return ExecutionSelection(workers=selected.workers, environment_id="main-locked",
        source_snapshot=ObjectIdentity.from_record("recursive-member.implementation", implementation_binding(ROOT)),
        output_root=originals.writer.root.contract.canonical_path)


def authored_plan(directory, writer):
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.recursive_execution import _retained_plans
    _, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=writer, lazy_payloads=True)
    run, plan, _ = _retained_plans(payloads, draft)
    return run, draft, plan


def method_products(directory, writer):
    from empirical_lawhood.api.recursive_execution import read_recursive_wave
    from empirical_lawhood.api.matrix_selected_e3_e4_read import _record
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    report, products, draft, plan = read_recursive_wave(directory=directory, artifact_writer=writer,
        include_products=True, terminal_product_format="compact", allow_partial=False)
    records, locators = {}, {}
    for operation, kind in (("revision-fit", science.SelectedE4RevisionNomination),
            ("revision-freeze", science.SelectedE4FrozenRevision)):
        task, = (row for row in plan.tasks if row.capability.capability_key == methods.NAMESPACE + "." + operation)
        value = _record(writer, products, task.task_id, kind)
        if value is None:
            raise PermissionError("actual DEV revision lacks its successful original typed product: " + operation)
        receipt = products["receipts"][task.task_id]
        logical, = (row for row in receipt.output_logical_artifacts
            if (row.payload_schema, row.content_sha256) == (kind.SCHEMA, value.fingerprint()))
        manifest = products["outputs"][logical.logical_artifact_id]
        locators[operation] = native.SelectedE4DevelopmentProduct(value.identity,
            Path(directory).relative_to(writer.root.contract.canonical_path).as_posix(), report["run_id"],
            ObjectIdentity.from_record(plan.execution_plan_id, plan), task.task_id,
            ObjectIdentity.from_record(receipt.receipt_id, receipt), actual_publication(writer, manifest))
        records[operation] = value
    return SimpleNamespace(nomination=records["revision-fit"], frozen=records["revision-freeze"],
        nomination_locator=locators["revision-fit"], frozen_locator=locators["revision-freeze"],
        report=report, run_id=report["run_id"], draft=draft, plan=plan)


def revision_inputs(originals, populations, selected, directory, acquisition_directory):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_revision_transition as transition
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from empirical_lawhood.kernel.experimental_selection import WholeUnitFold
    raw = read_bounded_bytes(Path(selected.revision_specification_path), maximum_bytes=1024**2)
    template = decode_canonical_bytes(raw, transition.SelectedE4RevisionAcquisitionSpecification, maximum_bytes=len(raw))
    groups = populations.programmes["DEV"].group_ids
    if len(template.revision.folds) != len(groups):
        raise ValueError("copied release fold selection changes the complete32 assigned DEV group census")
    # Only actual immutable input references/group labels are rebound. Every
    # declared scientific choice and each preselected fold number is preserved.
    revision = replace(template.revision, programme=populations.programmes["DEV"].identity,
        target=replace(template.revision.target, criterion=populations.programmes["DEV"].criterion),
        folds=tuple(WholeUnitFold(group, chosen.fold) for group, chosen in zip(groups, template.revision.folds, strict=True)))
    if type(revision) is not science.SelectedE4RevisionExperimentSpecification:
        raise TypeError("release revision selection loses its exact typed scientific owner")
    specification = transition.SelectedE4RevisionAcquisitionSpecification("experiment." + selected.namespace + ".revision", revision)
    resources = methods.SelectedE4MethodResources("resources." + selected.namespace + ".revision",
        tuple((phase, task_budget(selected)) for phase in ("revision-fit", "revision-freeze")))
    source = transition.SelectedE4RevisionAcquisitionSource("source." + selected.namespace + ".actual-acquisition",
        acquisition_directory.relative_to(originals.writer.root.contract.canonical_path).as_posix(), False)
    campaign = originals.retained.draft.campaign
    records = {"allocation": development.allocation(populations.programmes["DEV"]), "campaign": campaign,
        "source": source, "resources": resources}
    path = write_selection(directory, protocol_id=transition.PROTOCOL_ID, records=records,
        fields={"allocation": "allocation_id", "campaign": "campaign_id", "source": "record_id", "resources": "record_id"})
    return specification, path


def _planned_publication(writer, directory, name, record):
    """Exact owner-derived preview, authenticated only after public authoring.

    This descriptor is not evidence of publication. It freezes source configs
    for the deterministic future publication; the actual author/parent checks
    must prove equality before any worker entry.
    """
    from empirical_lawhood.api.selected_e4_declarative import expected_declaration_publication
    if name != "native-declaration.json":
        raise ValueError("protected E4 fixture previews only its exact declaration")
    return expected_declaration_publication(writer,Path(directory),record)


def _source_admissions(draft, records, arrays, *, root, prefix, observation_operator, retained_history_ids=()):
    """New disclosed materialization receipts, never reused historical grants."""
    from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
    from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
    from tests.runtime_platform.test_candidate_compiler import _fixture
    _, context = _fixture()
    template = context.qualifications[0]
    records = dict(records)
    arrays = dict(arrays)
    versions = {external.logical_artifact_id: records[external.input_id].VERSION
        if external.input_id in records else "1.0.0" for external in draft.external_inputs}
    retained = set(retained_history_ids)
    if (len(retained) != len(retained_history_ids) or not retained <= {value.input_id for value in draft.external_inputs}
            or any(value.scientific_role != "HISTORY" for value in draft.external_inputs if value.input_id in retained)):
        raise ValueError("disclosed retained exclusions require their exact HISTORY roster")
    configs, qualifications = [], []
    for index, external in enumerate(draft.external_inputs):
        if external.input_id in retained:
            continue
        if external.input_id not in records and external.input_id not in arrays:
            raise ValueError("release source admission lacks its exact native/canonical external payload")
        pin = ObjectIdentity(external.logical_artifact_id, external.payload_schema,
            versions[external.logical_artifact_id], external.expected_content_sha256)
        role = (SourceMaterializationRole.RETAINED_HISTORY if external.scientific_role == "HISTORY"
            else SourceMaterializationRole.CALIBRATION if external.scientific_role == "QUALIFICATION"
            else SourceMaterializationRole.OBSERVATION_STREAM)
        configs.append(SourceMaterializationConfig("source-config." + sha256((external.input_id + pin.object_fingerprint).encode()).hexdigest(),
            external.input_id, role, pin.object_fingerprint,
            external.maximum_size_bytes, external.maximum_size_bytes, external.payload_schema, external.media_type,
            SourceReadMode.ORDINARY_BOUNDED, external.outcome_access, external.visibility_ceiling))
        qualifications.append(replace(template, receipt_id="qualification." + prefix + "." + str(index),
            source_id=external.input_id, materialization=pin, content_sha256=pin.object_fingerprint,
            evidence_world_id=root.system.world.world_id, observation_operator=observation_operator,
            numerical_view_ids=tuple(value.view_id for value in root.system.numerical_views),
            native_unit_ids=tuple(sorted({value.native_unit for value in root.system.quantities})),
            frame_ids=tuple(sorted({value.coordinate_frame for value in root.system.quantities})),
            clock_ids=tuple(value.clock_id for value in root.system.clocks),
            receiver_semantics_id=root.system.relation.relation_id,
            validity_contract_id=root.experiment.obligations.validity.validity_id,
            uncertainty_contract_id=root.experiment.obligations.uncertainty.uncertainty_id,
            outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling))
    return tuple(sorted(configs,key=lambda value:value.source_id)), tuple(sorted(qualifications,key=lambda value:value.receipt_id))


def _phase_root(originals, programme, bank, evidence, revision, original_summary, calibration, budget):
    from empirical_lawhood.kernel.time import CausalPhase, InformationCutoff
    from empirical_lawhood.kernel.evidence import EvidenceCeiling
    from empirical_lawhood.kernel.obligations import ObligationStatus
    from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole
    root = original_preparation(originals).root
    index=bank.source_index()
    clock = programme.cases[0].information_cutoff.clock_id
    cutoff = InformationCutoff("cutoff." + programme.programme_id + ".before-entry", clock, CausalPhase.PREPARATION, D(0))
    pins = {programme.identity, bank.identity, programme.reservation, programme.allocation, programme.specification,
        programme.forecast_design, programme.response_selection, programme.criterion, evidence.identity,
        revision.decision.identity, original_summary.identity, *programme.source_census}
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    for descriptor in bank.sources:
        source = native.SelectedE4ProtectedNativeSourceReference.from_bank(programme,bank,descriptor,index=index)
        pins.update((source.identity, source.reference.identity, source.provenance,
            ObjectIdentity.from_record("public." + source.root_id, source.public)))
    pins.update(ObjectIdentity.from_record(value.protocol_id, value) for value in bank.response_selection.protocols)
    pins.update(ObjectIdentity.from_record(value.panel_id, value) for _, rows in bank.response_selection.panels for value in rows)
    if len({value.object_id for value in pins}) != len(pins):
        raise ValueError("selected native release design aliases distinct local scientific operands")
    if revision.models is not None:
        pins.add(revision.models.identity)
    if calibration is not None:
        pins.add(calibration.identity)
    designs = tuple(sorted((DesignInputRecord("design." + programme.programme_id + "." + str(index), pin,
        pin.object_fingerprint, cutoff, DesignInputRole.READINESS_METADATA, old.OutcomeAccess.OUTCOME_BLIND,
        old.VisibilityCeiling.PROSPECTIVE, "human.release-validation-explicit-test-authority")
        for index, pin in enumerate(sorted(pins, key=lambda value: value.object_id))), key=lambda value: value.input_id))
    clocks = {value.clock_id: value for value in root.system.clocks}
    for clock_id in {case.information_cutoff.clock_id for case in programme.cases}:
        clocks[clock_id] = replace(root.system.clocks[0], clock_id=clock_id)
    policy = replace(root.system.authority_policy, budget_ceiling=budget)
    numerical_views = {value.view_id: value for value in root.system.numerical_views}
    for descriptor in bank.sources:
        coordinate = bank.source(descriptor.root_id,index=index).coordinate
        for view in (coordinate.primary_view, coordinate.fine_view):
            numerical_views[view.view_id] = replace(root.system.numerical_views[0], view_id=view.view_id)
    system = replace(root.system, clocks=tuple(clocks[key] for key in sorted(clocks)), authority_policy=policy,
        numerical_views=tuple(numerical_views[key] for key in sorted(numerical_views)))
    # The new TEST phase has its own full assigned denominator. Original E3
    # support, confidence and derivation links never certify these new groups.
    obligations = root.experiment.obligations
    support = replace(obligations.support, support_id="support." + programme.programme_id,
        physical_unit_count=len(programme.group_ids),
        nested_numerical_view_count=len({view.view_id for descriptor in bank.sources
            for view in (bank.source(descriptor.root_id,index=index).coordinate.primary_view,bank.source(descriptor.root_id,index=index).coordinate.fine_view)}),
        information_cutoff_id=programme.cases[0].information_cutoff.cutoff_id,
        chart_ids=("chart." + programme.programme_id + ".complete-matched-factorial",),
        denominator_cell_ids=tuple(sorted(case.root_id for case in programme.cases)),
        status=ObligationStatus.REQUIRED, evidence_link_ids=())
    uncertainty = replace(obligations.uncertainty, uncertainty_id="uncertainty." + programme.programme_id,
        confidence_level=programme.design.confidence, status=ObligationStatus.REQUIRED, evidence_link_ids=(),
        limitation_codes=tuple(sorted({*obligations.uncertainty.limitation_codes, "SAMPLING_ASSUMPTION_NOT_AUTHENTICATED"})))
    obligations = replace(obligations, obligations_id="obligations." + programme.programme_id,
        support=support, uncertainty=uncertainty)
    claims = tuple(replace(value, claim_id="claim." + programme.programme_id + "." + str(index),
        proposition="Disclosed full selected E4 release conformance; real qualification is not established.",
        estimand="Complete declared " + bank.phase + " whole matched groups, all nine coordinate cases and all30 paired primary/fine endpoints; retain every adverse or unevaluable result.",
        requested_rung=None, evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        promotion_rule="EXPOSED_TEST_CONFORMANCE_ONLY_NO_SCIENTIFIC_QUALIFICATION_OR_E3_APPLICABILITY",
        derivation_parent_ids=(), parent_visibility_ceilings=())
        for index, value in enumerate(root.experiment.claims))
    experiment = replace(root.experiment, experiment_id="experiment." + programme.programme_id,
        claims=claims, obligations=obligations, information_cutoffs=tuple(case.information_cutoff for case in programme.cases))
    substitutions = {ObjectIdentity.from_record(root.experiment.experiment_id, root.experiment):
        ObjectIdentity.from_record(experiment.experiment_id, experiment)}
    substitutions.update((ObjectIdentity.from_record(before.claim_id, before), ObjectIdentity.from_record(after.claim_id, after))
        for before, after in zip(root.experiment.claims, claims, strict=True))
    campaign = replace(root.campaign, nodes=tuple(replace(value, object_identity=substitutions.get(value.object_identity, value.object_identity))
        for value in root.campaign.nodes), campaign_id="campaign." + programme.programme_id, budget=budget,
        authority_policy=ObjectIdentity.from_record(policy.policy_id, policy),
        target_claim_ids=tuple(value.claim_id for value in claims))
    return replace(root, draft_id="draft." + programme.programme_id,
        question="Execute the full declared E4 paired factorial programme and retain all adverse outcomes.",
        system=system, experiment=experiment, campaign=campaign, design_inputs=designs,
        design_origin=replace(root.design_origin, declared_input_ids=tuple(value.input_id for value in designs)),
        development_unit_ids=(), evaluation_unit_ids=programme.group_ids, development_seed_ids=(), evaluation_seed_ids=(),
        unresolved_decisions=(), source_materializations=(), resource_ceiling=budget)


def confirmation_choices(selected, populations, originals, revision, calibration, *, build_scope=True):
    """Copied settings choose inference; actual predecessor identities are joined."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as science
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial as factorial
    from empirical_lawhood.kernel.decoding import decode_canonical_record
    raw = read_bounded_bytes(Path(selected.confirmation_selection_path), maximum_bytes=1024**2)
    document = json.loads(raw)
    if type(document) is not dict or set(document) != {"calibration_alpha", "nomination_rule", "factorial"}:
        raise ValueError("release confirmation requires explicit alpha, full nomination and complete factorial choices")
    rule = decode_canonical_record(document["nomination_rule"], science.SelectedE4NominationRule)
    factorial_template = decode_canonical_record(document["factorial"], science.SelectedE4FactorialSpecification)
    if rule.confirmation_group_count != len(populations.programmes["CONF"].group_ids):
        raise ValueError("copied rule changes full declared CONF denominator")
    specification = science.SelectedE4ProgrammeSpecification("specification." + selected.namespace + ".downstream",
        originals.package.identity, old.identity(originals.package.models), populations.programmes["DEV"].identity,
        populations.programmes["CAL"].identity, populations.programmes["CONF"].identity, rule, factorial.FAMILY_IDS)
    target = replace(factorial_template.target, criterion=populations.programmes["CONF"].criterion)
    factor = replace(factorial_template, programme=populations.programmes["CONF"].identity, target=target)
    scope = None if not build_scope else methods.SelectedE4ConfirmationScope("scope." + selected.namespace + ".confirmation",
        specification, revision, calibration, factor)
    return scope, D(document["calibration_alpha"])


def protected_plan(originals, populations, selected, *, label, products, predecessor, directory,
        public_calibration=None, calibration_product=None, disclosed_parent_metadata=None):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_records as native
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_bindings as bindings
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_native_preparation as public
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_operational_resources as resources
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_method_bindings as methods
    from empirical_lawhood.runtime.experiment_resources import ExecutionResourceSelection
    from empirical_lawhood.runtime.execution_envelope import ChildResourceTokenLimit, ProgressHeartbeat, ProgressLivenessContract
    from tests.experiment_entry_support import entry_package_for_draft
    from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture
    from empirical_lawhood.planning.formal_analysis import derive_formal_gap_applicability
    programme, bank = populations.programmes[label], populations.banks[label]
    revision = e4.SelectedE4RevisionExport.from_products(populations.programmes["DEV"], products.nomination, products.frozen,
        record_id="export." + selected.namespace)
    source = predecessor.source
    from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
    from empirical_lawhood.api.selected_prepared_access import selected_e4_original_input_access
    if disclosed_parent_metadata is None:
        original_parents=selected_produced_input_parents(originals.writer,originals=originals.bindings)
        parents=selected_e4_original_input_access(artifact_writer=originals.writer,
            upstream_products=originals.bindings,calibration_product=calibration_product,
            development=(products.nomination_locator,products.frozen_locator)).parents
    else:
        # Explicit unsigned structural inputs confer no real producer custody.
        # Public authentication and authoring below still own their refusals.
        original_parents,parents=disclosed_parent_metadata
    evidence = native.SelectedE4ProtectedEvidence("evidence." + selected.namespace + "." + label.lower(),
        programme.identity, originals.bindings, products.nomination_locator, products.frozen_locator, source, calibration_product,parents)
    summary = e4.SelectedE4OriginalCalibrationSummary.from_package(originals.package,
        record_id="original-summary." + selected.namespace)
    budgets = native.SelectedE4NativeBudgets("budgets." + selected.namespace + "." + label.lower(),
        tuple((phase, task_budget(selected)) for phase in sorted(bindings.PHASES)), task_budget(selected))
    budget = ResourceBudget.aggregate(task_budget(selected) for _ in range(
        sum(len(wave.root_ids) * (len(bindings.PHASES) - 2) + 3 for wave in programme.waves)
        + 3 + len(methods.operations_for_programme(programme))))
    root = _phase_root(originals, programme, bank, evidence, revision, summary, public_calibration, budget)
    declaration = native.SelectedE4NativeProgrammeDeclaration("declaration." + selected.namespace + "." + label.lower(),
        programme, bank.identity, publication(originals.writer, bank, selected.namespace + "." + label.lower() + ".bank",lineage_parents=original_parents),
        root, evidence.identity, revision.decision, revision.models, public_calibration, budgets, selected.workers, summary,parents)
    scope, alpha = confirmation_choices(selected, populations, originals, revision, public_calibration, build_scope=(label == "CONF"))
    method_phases = ("revision-calibrate",) if label == "CAL" else ("factorial-assess", "confirmation-assess", "downstream-nominate")
    tail_resources = methods.SelectedE4MethodResources("resources." + selected.namespace + "." + label.lower() + ".methods",
        tuple((phase, task_budget(selected)) for phase in sorted(method_phases)))
    calibration = None if label != "CAL" else e4.SelectedE4CalibrationSpecification("specification." + selected.namespace + ".calibration",
        populations.programmes["DEV"].identity, programme.identity, products.nomination.identity, products.frozen.identity,
        alpha, e4.SCORE_RULE)
    tail = public.SelectedE4ProtectedTailSelection("tail." + selected.namespace + "." + label.lower(),
        revision, tail_resources, calibration, scope if label == "CONF" else None)
    child = ChildResourceTokenLimit("child." + selected.namespace + "." + label.lower(), len(programme.cases) * len(bindings.NATIVE), 0)
    controls = ExecutionResourceSelection("resources." + selected.namespace + "." + label.lower(), (), (child,), (), (), (), None, None,
        selected.workers, selected.workers * selected.memory_bytes_per_task, (), (), sha256(
            Path(selected.confirmation_selection_path).read_bytes()).hexdigest(), True, True, True, True)
    operational = resources.SelectedE4OperationalResources("operational." + selected.namespace + "." + label.lower(), controls,
        tuple((phase, 100) for phase in sorted({*bindings.PHASES, "phase-collect", *methods.operations_for_programme(programme)})),
        ProgressLivenessContract("progress." + selected.namespace + "." + label.lower(), ProgressHeartbeat.SCHEMA,
            "exposed-release-validation-selected-e4-native-work", D(30), True, True), 1)
    formal = _standard_fixture()[1]
    entry = entry_package_for_draft(root)
    # Public authoring will create this exact descriptor. Until it does, this
    # remains only a frozen expected source operand, never custody evidence.
    preview_publication = _planned_publication(originals.writer, directory, "native-declaration.json", declaration)
    configs, qualifications = {}, {}
    for wave in programme.waves:
        lowered = bindings.lower_selected_e4_protected_wave(declaration, bank, evidence=evidence,
            declaration_publication=preview_publication, wave_id=wave.wave_id, campaign=root.campaign,
            draft_id="draft." + public.component_specification.__name__ + "." + wave.wave_id, secondary_target=populations.secondary_target, secondary_readout=populations.secondary_readout)
        cc, qq = _source_admissions(lowered.draft, lowered.input_records, lowered.input_artifacts,
            root=lowered.draft.prospective_draft, prefix=selected.namespace + "." + label.lower() + "." + wave.wave_id,
            observation_operator=source.pipeline.pipeline_config.profile.observation_operator)
        for value in cc:
            if value.source_id in configs and configs[value.source_id] != value:
                # Shared bank/assay inputs retain one code-owned source ID and
                # the same exact bytes across predeclared wave components.
                if replace(value, config_id=configs[value.source_id].config_id) != configs[value.source_id]:
                    raise ValueError("shared phase source configurations disagree across waves")
            else:
                configs[value.source_id] = value
        for value in qq:
            if value.receipt_id in qualifications and qualifications[value.receipt_id] != value:
                raise ValueError("phase qualification ID aliases distinct local source semantics")
            qualifications[value.receipt_id] = value
    materializations = {value.materialization for value in qualifications.values()}
    if len({value.object_id for value in materializations}) != len(materializations):
        raise ValueError("phase source materializations alias distinct byte identities")
    inventory = replace(formal.source_inventories[0], denominator_id=root.system.system_id,
        evidence_world=entry.checklist.portfolio_world,
        source_materializations=tuple(sorted(materializations, key=lambda value: value.object_id)),
        independent_unit_ids=programme.group_ids, denominator_inapplicable_gap_ids=tuple(value.gap_id for value in entry.register.gaps))
    coverage = replace(entry.coverage, denominator_id=root.system.system_id,
        applicability=derive_formal_gap_applicability(entry.register, inventory))
    entry = replace(entry, coverage=coverage, checklist=replace(entry.checklist,
        formal_gap_coverage=ObjectIdentity.from_record(coverage.coverage_id, coverage)))
    preparation = public.SelectedE4ProgrammePreparationSelectionV2("preparation." + selected.namespace + "." + label.lower(),
        entry, formal.formal_methods, (inventory,), tuple(sorted(qualifications.values(), key=lambda value: value.receipt_id)),
        tuple(sorted(configs.values(), key=lambda value: value.source_id)), operational)
    specification = public.SelectedE4ProtectedProgrammeSpecification("experiment." + selected.namespace + "." + label.lower(),
        declaration.identity, declaration.bank_phase, len(programme.group_ids), programme.design.cases_per_group, root.question)
    structure, structural_resources = disclosed_structure(bank, budget=task_budget(selected))
    plan = public.SelectedE4ProtectedProgrammePlan("plan." + selected.namespace + "." + label.lower(),
        specification, declaration, bank, evidence, preparation, tail,
        structure, populations.secondary_readout, structural_resources)
    return plan, preview_publication


def selected_settings_census(selected):
    """Actual immutable bytes selected before the first E4 observation."""
    paths = (selected.original_e3_selection, selected.revision_specification_path, selected.confirmation_selection_path,
        selected.preparation_recipe_path)
    return {str(Path(value).resolve(strict=True)): bounded_file_sha256(Path(value), maximum_bytes=1024**2)
        for value in sorted(paths)}
