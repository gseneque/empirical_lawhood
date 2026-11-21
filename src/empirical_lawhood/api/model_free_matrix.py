# SPDX-License-Identifier: MPL-2.0
"""Public authoring, retained reanalysis and compact reading for M0–M7."""
from hashlib import sha256
import json
from pathlib import Path

from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.design.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection, ExperimentFileInputBinding, ExperimentFileInputSelection
from empirical_lawhood.domains.matrix.classical_series.records import _pairs
from empirical_lawhood.domains.matrix.model_free import design, experiment
from empirical_lawhood.domains.matrix.model_free.records import NAMESPACE, PROTOCOL_ID, ParentLineage, Product, RootAssignment, RetainedInput, RetainedArray, Specification, json_text, selection_key, audit_assignments, restrict_assignment

DEFINITION_SCHEMA = "model-free-matrix-definition.v1"


def parent_readout_sha256(scientific_result):
    """Canonical parent fingerprint shown by the public read command.

This calculation supplies no authentication. The successor route independently
reads original custody and compares this exact digest before publication.
"""
    if type(scientific_result) is not dict:
        raise TypeError('Select the complete scientific result object')
    return sha256(json_text(scientific_result).encode()).hexdigest()


def select_sci02c_instrument(*, directory, artifact_writer):
    """Read the original design and assay bytes through the caller's current custody profile."""
    from empirical_lawhood.api.recursive_authoring import load_authored_wave
    from empirical_lawhood.api.matrix_sci02 import _source_record
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_experiment import Sci02CSpecification
    from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import Sci02CDesign
    from empirical_lawhood.domains.matrix.model_free.receiver_preparation import instrument_operands
    from empirical_lawhood.adapters.matrix_storage.matrix_array_io import NPZMemberSelection, decode_matrix_arrays
    import zlib

    with artifact_writer.verification_scope() as verified:
        packet, _, _, payloads = load_authored_wave(directory=directory, artifact_writer=verified, lazy_payloads=True)
        raw_spec = payloads['experiment-specification.json']
        spec = decode_canonical_bytes(raw_spec, Sci02CSpecification, maximum_bytes=len(raw_spec))
        study = _source_record(payloads, spec.study, Sci02CDesign)
        artifact = study.physical.assay.template_artifact
        name = 'external-' + sha256(('external.templates.' + artifact.sha256).encode()).hexdigest()[:24] + '.npz'
        raw = payloads[name]
        arrays = decode_matrix_arrays(raw, NPZMemberSelection(artifact, study.physical.assay.template_members))
        selection = {'packet_sha256': packet.fingerprint(), 'sci02c_study_sha256': study.fingerprint(),
                     'physical_design': study.physical.canonical_bytes().decode(),
                     'physical_design_sha256': study.physical.fingerprint(), 'template_hex': raw.hex(),
                     'template_members': {name: zlib.compress(array.tobytes(order='C')).hex()
                                          for name, array in arrays.items()}}
        instrument_operands(selection)
        return selection


def load_definition(path):
    from empirical_lawhood.domains.matrix.model_free.science import normalise_settings
    from empirical_lawhood.domains.matrix.model_free.settings import require_assigned_receiver_inputs
    raw = Path(path).read_bytes()
    def invalid(value):
        raise ValueError("nonfinite authored value: " + value)
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=invalid)
    if type(value) is not dict or set(value) != {"schema", "label", "roots", "settings"} or value["schema"] != DEFINITION_SCHEMA:
        raise ValueError("model-free definition needs schema, label, roots and settings only")
    if type(value["label"]) is not str or not value["label"].strip() or type(value["roots"]) is not list or not value["roots"]:
        raise ValueError("a study label and complete assigned-root census are required")
    assigned = []
    for row in value["roots"]:
        if type(row) is not dict or set(row) != {"seed", "modules", "role"} or type(row["modules"]) is not list:
            raise ValueError("each root declares seed, modules and role")
        assigned.append(RootAssignment(row["seed"], tuple(row["modules"]), row["role"]))
    assigned = tuple(sorted(assigned, key=lambda r: r.seed))
    if len({r.seed for r in assigned}) != len(assigned):
        raise ValueError("independent-root seeds overlap across assigned cohorts")
    settings = normalise_settings(value["settings"])
    require_assigned_receiver_inputs(settings, assigned)
    if len({r.role for r in assigned}) != 1:
        raise ValueError("development and confirmation belong to separately frozen inquiries")
    expected_scope = "FRESH_CONFIRMATION" if assigned[0].role == "confirmation" else "EXPOSED_DEVELOPMENT"
    if settings["evidence_scope"] != expected_scope:
        raise ValueError("root roles and scientific exposure scope disagree")
    return raw, value["label"], assigned, settings


def specification_for(label, assignments, settings, *, mode="new-development", records=(), arrays=(), parent_lineage=None):
    from empirical_lawhood.domains.matrix.model_free.science import normalise_settings
    # Freeze the complete normalized choices, including defaults, before their
    # fingerprints become operation identities or an authenticated cutoff.
    settings = normalise_settings(settings)
    assignments = audit_assignments(assignments, settings)
    pins = tuple(sorted((RetainedInput(key, value.identity) for key, value in records), key=lambda r: r.key))
    binary = tuple(sorted((RetainedArray(key, value) for key, value in arrays), key=lambda r: r.key))
    selected = {"label": label, "roots": [r.to_document() for r in assignments], "settings": settings, "mode": mode,
        "retained": [r.to_document() for r in pins], "arrays": [r.to_document() for r in binary],
        "parent_lineage": None if parent_lineage is None else parent_lineage.to_document()}
    identifier = "specification." + NAMESPACE + "." + sha256(json_text(selected).encode()).hexdigest()
    return Specification(identifier, json_text(settings), assignments, label, mode,
        "PREDECLARED_DEVELOPMENT" if mode == "new-development" else "EXPOSED_REANALYSIS", pins, binary, parent_lineage)


def _parent_lineage(*, original, result, products, report, settings, purpose):
    """Called only while the existing retained-root owner authenticates a read."""
    summaries = [p for rows in products["records"].values() for p in rows.values()
                 if type(p) is Product and p.config.phase == "synthesise"]
    modules = {m for r in original.assignments for m in r.modules}
    if (len(summaries) != len(modules) or {p.config.module for p in summaries} != modules
            or any(p.config.specification != original.identity for p in summaries)):
        raise ValueError("authenticated parent lacks its complete original population summaries")
    exposed = {r.seed for r in original.assignments}
    if original.parent_lineage is not None:
        exposed.update(original.parent_lineage.exposed_seeds)
    exposed = tuple(sorted(exposed))
    fields = ("packet_sha256", "execution_plan_sha256", "producing_code_sha256")
    if any(type(report.get(key)) is not str for key in fields):
        raise ValueError("parent lacks complete authenticated packet, plan or producing-source provenance")
    return ParentLineage(purpose, original.identity,
        tuple(sorted((p.identity for p in summaries), key=lambda p: p.object_id)),
        original.assignments, *(report[key] for key in fields),
        sha256(json_text(result).encode()).hexdigest(), exposed,
        sha256(json_text({"seeds": list(exposed)}).encode()).hexdigest(),
        sha256(json_text(settings).encode()).hexdigest())


def _exposure_readout(specification):
    """Keep a scientific root declaration distinct from framework authority."""
    role = specification.assignments[0].role
    freshness = "EXPOSED_DEVELOPMENT"
    if specification.mode == "reanalysis":
        freshness = "EXPOSED_REANALYSIS"
    elif role == "confirmation":
        freshness = "DISJOINT_FROM_DECLARED_PARENT_EXPOSURE"
    return {"evidence_scope": specification.evidence_scope,
        "declared_population_scope": specification.settings["evidence_scope"],
        "population_role": role, "freshness_claim": freshness,
        "framework_outcome_access": "DEVELOPMENT_VISIBLE",
        "framework_evidence_ceiling": "NON_PROMOTABLE",
        "parent_authentication_scope": "PUBLIC_SUCCESSOR_AND_DEPLOYMENT_CREATORS_AUTHENTICATE_LIVE_PARENT_CUSTODY; DECLARED_LINEAGE_ALONE_IS_NOT_AUTHORITY",
        "global_freshness_established": False, "outcome_blind_authority_granted": False}


def _write_inputs(*, destination, project_root, raw_definition, specification, records, files, extra=None, parent_authentication_performed=False):
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    source = implementation_binding(Path(project_root))
    bindings = []
    payloads = {"definition.json": raw_definition, "specification.json": specification.canonical_bytes(), "source-snapshot.json": source.canonical_bytes()}
    for key, record in sorted(records.items()):
        name = key + ".json"
        raw = record.canonical_bytes()
        payloads[name] = raw
        bindings.append(ExperimentInputBinding(key, record.identity, name, len(raw)))
    file_bindings = tuple(ExperimentFileInputBinding(key, identity, "1.0.0", name, max(1, identity.size_bytes)) for key, (identity, name) in sorted(files.items()))
    if file_bindings:
        sources = ExperimentFileInputSelection("inputs." + NAMESPACE + "." + specification.fingerprint(), PROTOCOL_ID, tuple(bindings), file_bindings)
    else:
        sources = ExperimentInputSelection("inputs." + NAMESPACE + "." + specification.fingerprint(), PROTOCOL_ID, tuple(bindings))
    payloads["sources.json"] = sources.canonical_bytes()
    payloads.update(extra or {})
    for name, raw in sorted(payloads.items()):
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    return {"specification": str(destination / "specification.json"), "sources": str(destination / "sources.json"),
        "source_snapshot": str(destination / "source-snapshot.json"), "definition": str(destination / "definition.json"),
        "assigned_roots": len(specification.assignments), "mode": specification.mode, "qualification": "NOT_ESTABLISHED", "native_acquisition_performed": False,
        **_exposure_readout(specification),
        'parent_authentication_performed': parent_authentication_performed,
        'parent_authentication_time_scope': 'THIS_PUBLIC_AUTHORING_INVOCATION_ONLY' if parent_authentication_performed else 'NOT_PERFORMED'}


def create_inputs(*, definition_path, project_root, output_directory):
    raw, label, assignments, settings = load_definition(definition_path)
    if any(r.role == "confirmation" for r in assignments):
        raise ValueError("confirmation must use create_successor_inputs with an authenticated development parent")
    if any('M5' in r.modules for r in assignments) and settings['population']['mode'] == 'sparse':
        raise ValueError('sparse deployment must use create_population_deployment_inputs with an authenticated reveal-all benchmark')
    specification = specification_for(label, assignments, settings)
    experiment.bind_inputs(specification, {})
    destination = Path(output_directory).absolute()
    destination.mkdir(parents=True, exist_ok=False)
    return _write_inputs(destination=destination, project_root=project_root, raw_definition=raw,
        specification=specification, records={}, files={})


def _read_parent(parent_directory, parent_service, consumer):
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_retained_roots
    def consume(**kwargs):
        result = read_result(**{k: v for k, v in kwargs.items() if k in ("directory", "artifact_writer", "payloads", "report", "products", "draft", "plan", "allow_partial")},
            specification=decode_canonical_bytes(kwargs["payloads"]["experiment-specification.json"], Specification, maximum_bytes=None),
            instance=_instance(kwargs["payloads"]))
        if result["scientific_completion"] != "COMPLETED":
            raise ValueError("successor requires complete authenticated parent custody")
        consumer(result=result, **kwargs)
        return result
    return _read_recursive_wave_with_retained_roots(directory=Path(parent_directory), artifact_writer=parent_service.artifact_writer,
        include_products=True, terminal_product_format="references", _scientific_consumer=consume)


def _instance(payloads):
    from empirical_lawhood.execution.experiment_preparation import ExperimentInstanceBinding
    return decode_canonical_bytes(payloads["experiment-instance.json"], ExperimentInstanceBinding, maximum_bytes=None)


def create_reanalysis_inputs(*, definition_path, project_root, output_directory, parent_directory, parent_service):
    from empirical_lawhood.storage.recursive_custody import iter_exact_custody_file_chunks
    from empirical_lawhood.domains.matrix.model_free.retained_analysis import validate_reanalysis_settings
    raw, label, assignments, settings = load_definition(definition_path)
    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError("reanalysis requires a fresh explicit destination")
    records, files, provenance, lineage = {}, {}, {}, []
    wanted = {selection_key(m, r) for r in assignments for m in r.modules}
    assigned = audit_assignments(assignments, settings)
    def consume(*, result, payloads, products, artifact_writer, report, **kwargs):
        original = decode_canonical_bytes(payloads["experiment-specification.json"], Specification, maximum_bytes=None)
        if original.mode != "new-development":
            raise ValueError("reanalysis needs the original native run")
        changed = validate_reanalysis_settings(original.settings, settings, {m for r in assignments for m in r.modules})
        for module in {m for r in assignments for m in r.modules}:
            if {r.seed for r in assignments if module in r.modules} != {r.seed for r in original.assignments if module in r.modules}:
                raise ValueError("phase selection cannot discard assigned or failed roots")
        previous = {r.seed: r for r in original.assignments}
        for current in assigned:
            old = previous.get(current.seed)
            if old is None or not set(current.modules) <= set(old.modules) or restrict_assignment(old, current.modules) != current:
                raise ValueError("reanalysis changes the original role, module or sampling assignment")
        lineage.append(_parent_lineage(original=original, result=result, products=products,
            report=report, settings=settings, purpose="retained-reanalysis"))
        destination.mkdir(parents=True, exist_ok=False)
        for row in products["records"].values():
            for record in row.values():
                if type(record) is not Product or record.config.phase != "acquire":
                    continue
                key = selection_key(record.config.module, record.config.assignments[0])
                if key not in wanted:
                    continue
                if key in records:
                    raise ValueError("parent repeats an assigned native product")
                if record.config.specification != original.identity:
                    raise ValueError("parent acquisition comes from another scientific specification")
                records[key] = record
                identity = record.array_artifact
                if identity is None:
                    raise ValueError("parent acquisition lacks its required original binary companion")
                manifest = products["outputs"].get(identity.artifact_id)
                if (manifest is None or manifest.logical.logical_artifact_id != identity.artifact_id
                        or manifest.logical.content_sha256 != identity.sha256
                        or manifest.logical.payload_schema != identity.payload_schema
                        or manifest.logical.media_type != identity.media_type
                        or manifest.materialization.size_bytes != identity.size_bytes
                        or manifest.materialization.physical_sha256 != identity.sha256):
                    raise ValueError("parent native product lacks its exact binary receipt")
                relative = "arrays." + key + ".bin"
                path = artifact_writer.root.resolve(manifest.materialization.relative_path, for_write=False)
                with (destination / relative).open("xb") as stream:
                    for block in iter_exact_custody_file_chunks(path, size_bytes=identity.size_bytes,
                            expected_sha256=identity.sha256, read_guard=artifact_writer.require_verification_snapshot):
                        stream.write(block)
                files["arrays." + key] = (identity, relative)
        provenance.update(parent_specification=original.identity.to_document(), selected_modules=sorted({m for r in assignments for m in r.modules}), parent_scientific_completion=result["scientific_completion"],
            analysis_settings_changed=changed, acquisition_settings_sha256=sha256(original.settings_json.encode()).hexdigest(),
            assessment_settings_sha256=sha256(json_text(settings).encode()).hexdigest(),
            interpretation="EXPOSED_POST_HOC_ANALYSIS" if changed else "EXACT_AS_AUTHORED_REANALYSIS")
    _read_parent(parent_directory, parent_service, consume)
    if set(records) != wanted:
        raise ValueError("parent lacks an originally assigned native acquisition")
    if len(lineage) != 1:
        raise ValueError("reanalysis did not authenticate exactly one original parent")
    specification = specification_for(label, assignments, settings, mode="reanalysis", records=tuple(records.items()), arrays=tuple((k, v[0]) for k, v in files.items()), parent_lineage=lineage[0])
    experiment.bind_inputs(specification, records)
    return _write_inputs(destination=destination, project_root=project_root, raw_definition=raw, specification=specification,
        records=records, files=files, parent_authentication_performed=True,
        extra={"parent-custody.json": (json.dumps(provenance, sort_keys=True, indent=2) + "\n").encode()})


def create_successor_inputs(*, definition_path, project_root, output_directory, parent_directory, parent_service):
    """Freeze chosen scientific settings after development, before fresh outcomes."""
    raw, label, assignments, settings = load_definition(definition_path)
    if any(r.role != "confirmation" for r in assignments):
        raise ValueError("the frozen successor declares a fresh confirmation population")
    from empirical_lawhood.domains.matrix.model_free.confirmation import validate_confirmation
    validate_confirmation(settings, assignments)
    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError("confirmation requires a fresh explicit destination")
    parent, lineage = {}, []
    def consume(*, result, payloads, products, report, **kwargs):
        original = decode_canonical_bytes(payloads["experiment-specification.json"], Specification, maximum_bytes=None)
        if original.mode != "new-development":
            raise ValueError("confirmation freezes the original development acquisition and assessment")
        exposed = {r.seed for r in original.assignments}
        if original.parent_lineage is not None:
            exposed.update(original.parent_lineage.exposed_seeds)
        if {r.seed for r in assignments} & exposed:
            raise ValueError("exposed development roots cannot become fresh confirmation")
        if any(r.role != "development" for r in original.assignments):
            raise ValueError("select the original development parent for this confirmation")
        readiness = validate_confirmation(settings, assignments, parent_readout=result,
            parent_modules={m for row in original.assignments for m in row.modules})
        if any('M5' in row.modules for row in assignments):
            _revealed_population_summary(original, products)
        lineage.append(_parent_lineage(original=original, result=result, products=products,
            report=report, settings=settings, purpose="development-freeze"))
        parent.update(specification=original.identity.to_document(), readout=result, confirmation_readiness=readiness,
            population_summaries=[p.identity.to_document() for rows in products["records"].values() for p in rows.values() if type(p) is Product and p.config.phase == "synthesise"])
    _read_parent(parent_directory, parent_service, consume)
    if len(lineage) != 1:
        raise ValueError("confirmation did not authenticate exactly one original development parent")
    specification = specification_for(label, assignments, settings, parent_lineage=lineage[0])
    experiment.bind_inputs(specification, {})
    destination.mkdir(parents=True, exist_ok=False)
    return _write_inputs(destination=destination, project_root=project_root, raw_definition=raw, specification=specification,
        records={}, files={}, parent_authentication_performed=True,
        extra={"development-parent.json": (json.dumps(parent, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()})


def _revealed_population_summary(original, products):
    """Validate the actual complete benchmark within the caller's live read."""
    if (original.mode != 'new-development' or original.settings['population']['mode'] != 'reveal_all'
            or not any('M5' in row.modules for row in original.assignments)
            or any(row.role != 'development' for row in original.assignments)):
        raise ValueError('Select the original reveal-all development benchmark')
    summaries = [p for rows in products['records'].values() for p in rows.values()
        if type(p) is Product and p.config.phase == 'synthesise' and p.config.module == 'M5']
    if len(summaries) != 1:
        raise ValueError('Original benchmark lacks its complete M5 population summary')
    from empirical_lawhood.domains.matrix.classical_series.records import json_object
    body = json_object(summaries[0].payload_json)
    benchmark = body.get('modules', {}).get('M5', {})
    if 'receiver_study' in original.settings:
        from empirical_lawhood.domains.matrix.model_free.receiver_campaign import REVISION
        from empirical_lawhood.domains.matrix.model_free.receiver_population import CASE
        comparisons = benchmark.get('finite_frame_comparisons', {})
        assigned = [r.seed for r in original.assignments if 'M5' in r.modules]
        sampled = [r.seed for r in original.assignments if 'M5' in r.modules and r.audit_selected]
        size = original.settings['population']['frame_size']
        if (benchmark.get('receiver_revision') != REVISION or benchmark.get('signed_receiver') != CASE
                or benchmark.get('acquisition_mode') != 'reveal_all'
                or benchmark.get('root_seeds') != assigned or benchmark.get('assigned_root_seeds') != assigned
                or benchmark.get('sampled_root_seeds') != sampled or benchmark.get('assigned_roots') != size
                or benchmark.get('frame_size') != size or benchmark.get('assigned_cases') != size
                or benchmark.get('audit_size') != original.settings['population']['audit_size']
                or set(comparisons) != {'auxiliary', 'one_coefficient', 'zero'}):
            raise ValueError('Reveal-all benchmark lacks the declared signed receiver, comparator or root census')
        for comparison in comparisons.values():
            exact = comparison.get('full_frame_benchmark') or {}
            if (comparison.get('status') != 'ESTIMATED' or exact.get('status') != 'ENUMERATED'
                    or exact.get('missing_frame_indices') != [] or exact.get('full_frame_mean') is None
                    or exact.get('actual_native_calls_omitted') != 0):
                raise ValueError('Reveal-all comparison must retain every native frame outcome before deployment')
        return summaries[0]
    rows = benchmark.get('finite_population', ())
    recipes = original.settings['native']['preparation_arms'] + original.settings['formation']['exposure_matched_recipes']
    expected_rows = {(coordinate['id'], recipe) for coordinate in original.settings['native']['coordinates'] for recipe in recipes}
    contrast_rows = benchmark.get('paired_finite_population_contrasts', [])
    expected_contrasts = {(coordinate, recipe) for coordinate, recipe in expected_rows
        if recipe != 'baseline' and 'baseline' in recipes}
    if (not isinstance(rows, list) or len(rows) != len(expected_rows)
            or {(row.get('coordinate'), row.get('recipe')) for row in rows} != expected_rows
            or not isinstance(contrast_rows, list) or len(contrast_rows) != len(expected_contrasts)
            or {(row.get('coordinate'), row.get('recipe')) for row in contrast_rows} != expected_contrasts
            or benchmark.get('assigned_roots') != original.settings['population']['frame_size']):
        raise ValueError('Reveal-all benchmark must retain the exact complete coordinate/recipe/contrast and root census')
    if (not isinstance(rows, list) or not rows or benchmark.get('acquisition_mode') != 'reveal_all'
            or any(row.get('full_frame_mean') is None or row.get('estimator_comparison', {}).get('status') != 'ESTIMATED'
                or row.get('estimator_comparison', {}).get('full_frame_benchmark', {}).get('status') != 'ENUMERATED' for row in rows)
            or any(row.get('estimator_comparison', {}).get('full_frame_benchmark', {}).get('status') != 'ENUMERATED'
                for row in contrast_rows)):
        raise ValueError('Reveal-all comparison must retain every native frame outcome before deployment')
    return summaries[0]


def create_population_deployment_inputs(*, definition_path, project_root, output_directory, parent_directory, parent_service):
    """Freeze a sparse native deployment after an authenticated reveal-all run.

New root seeds prevent previously paid-for outcomes becoming claimed savings.
The parent supplies benchmark evidence, never the deployment's native targets.
"""
    raw, label, assignments, settings = load_definition(definition_path)
    if (any(r.role != 'development' for r in assignments)
            or not any('M5' in r.modules for r in assignments) or settings['population']['mode'] != 'sparse'):
        raise ValueError('Select a development M5 frame in sparse acquisition mode')
    destination = Path(output_directory).absolute()
    if destination.exists():
        raise FileExistsError('sparse deployment requires a fresh explicit destination')
    lineage, parent = [], {}
    def consume(*, result, payloads, products, report, **kwargs):
        original = decode_canonical_bytes(payloads['experiment-specification.json'], Specification, maximum_bytes=None)
        if (original.mode != 'new-development' or original.settings['population']['mode'] != 'reveal_all'
                or not any('M5' in row.modules for row in original.assignments)
                or any(row.role != 'development' for row in original.assignments)):
            raise ValueError('Sparse deployment requires the original revealed development frame')
        if result.get('scientific_completion') != 'COMPLETED':
            raise ValueError('Complete the reveal-all benchmark before sparse deployment')
        exposed = {row.seed for row in original.assignments}
        if original.parent_lineage is not None:
            exposed.update(original.parent_lineage.exposed_seeds)
        if exposed & {row.seed for row in assignments}:
            raise ValueError('Sparse deployment cannot claim avoided work on previously revealed roots')
        for key in ('native', 'formation', 'response'):
            if original.settings[key] != settings[key]:
                raise ValueError('Sparse deployment changes the frozen benchmark receiver/auxiliary policy: ' + key)
        previous_study = original.settings.get('receiver_study')
        selected_study = settings.get('receiver_study')
        if previous_study is not None and selected_study is not None:
            # The revealed development frame evaluates all three competitors.
            # A prospective use can select one of those priced suppliers before
            # the disjoint audit. Its physical and statistical policy stays fixed.
            previous_study = {**previous_study, 'M5': {**previous_study['M5'],
                'sparse_use': selected_study['M5']['sparse_use'],
                'sparse_supplier': selected_study['M5']['sparse_supplier']}}
        if previous_study != selected_study:
            raise ValueError('Sparse deployment changes the signed receiver, source or benchmark decision rule')
        for key in original.settings['population']:
            if key not in {'mode', 'sampling_seed'} and original.settings['population'][key] != settings['population'][key]:
                raise ValueError('Sparse deployment changes its benchmark finite-frame target: ' + key)
        summary = _revealed_population_summary(original, products)
        if 'receiver_study' in settings:
            from empirical_lawhood.domains.matrix.classical_series.records import json_object
            benchmark = json_object(summary.payload_json)['modules']['M5']
            intent = settings['receiver_study']['M5']['sparse_use']
            supplier = settings['receiver_study']['M5']['sparse_supplier']
            supported = benchmark.get('economically_supported_suppliers', {}).get(supplier) is True
            parent.update(sparse_use=intent, sparse_supplier=supplier, benchmark_decision=benchmark['decision'],
                          benchmark_supports_selected_supplier=supported)
            if intent == 'ECONOMIC_DELIVERY' and not supported:
                raise ValueError('Economic sparse delivery requires a complete benchmark meeting the precision and cost rule')
        lineage.append(_parent_lineage(original=original, result=result, products=products,
            report=report, settings=settings, purpose='population-deployment'))
        parent.update(specification=original.identity.to_document(), benchmark_summary=summary.identity.to_document(),
            benchmark_readout_sha256=sha256(json_text(result).encode()).hexdigest(),
            interpretation='FROZEN_POLICY_ON_NEW_ROOTS; ACTUAL_OMISSIONS_CHARGED_FROM_DEPLOYMENT_RECEIPTS')
    _read_parent(parent_directory, parent_service, consume)
    if len(lineage) != 1:
        raise ValueError('Sparse deployment requires exactly one authenticated benchmark')
    specification = specification_for(label, assignments, settings, parent_lineage=lineage[0])
    experiment.bind_inputs(specification, {})
    destination.mkdir(parents=True, exist_ok=False)
    return _write_inputs(destination=destination, project_root=project_root, raw_definition=raw, specification=specification,
        records={}, files={}, parent_authentication_performed=True,
        extra={'population-benchmark.json': (json.dumps(parent, sort_keys=True, indent=2) + '\n').encode()})


def read_result(*, directory, artifact_writer, specification, instance, payloads, report, products, draft, plan, allow_partial=False):
    if type(specification) is not Specification or instance.specification != specification.identity:
        raise PermissionError("scientific reader substitutes the original authored definition")
    configs = design.configs_for(specification)
    if {t.task_id for t in plan.tasks} != {c.node_id for c in configs} or report.get("run_id") != plan.source_plan.object_id:
        raise PermissionError("scientific reader changes the complete original operation census")
    base = {"namespace": NAMESPACE, "mode": specification.mode, "study_label": specification.study_label,
        "qualification": "NOT_ESTABLISHED", **_exposure_readout(specification),
        "assigned_roots": len(specification.assignments), "selected_modules": sorted({m for r in specification.assignments for m in r.modules}),
        "scientific_reconstruction_performed": False, "native_acquisition_performed": False, "historical_qualification_changed": False,
        "assigned_operations": len(configs), "cost_policy": "Complete preparation, native work, failed attempts, acquisition, assessment and custody; no savings inferred from model-free naming."}
    if specification.parent_lineage is not None:
        base["parent_lineage"] = specification.parent_lineage.to_document()
        base["information_cutoff"] = "DECLARED_PARENT_IDENTITIES_BOUND_IN_SPECIFICATION"
    if allow_partial or report.get("typed_product_validation") == "DEFERRED":
        return {**base, "scientific_completion": "DEFERRED", "population_summaries": {}}
    found = {}
    for config in configs:
        receipt = products["receipts"].get(config.node_id)
        if receipt is None or receipt.operational_status is not OperationalStatus.SUCCEEDED:
            continue
        record = products["records"].get(config.node_id, {}).get(config.node_id + ".product")
        if type(record) is not Product or record.config != config:
            raise PermissionError("reader changes an original scientific result")
        found[config.node_id] = record
    summaries = {}
    for product in found.values():
        if product.config.phase != "synthesise":
            continue
        pins = tuple(sorted((p.identity for p in found.values() if p.config.phase == "analyse" and p.config.module == product.config.module), key=lambda p: p.object_id))
        if product.dependencies != pins:
            raise PermissionError("population synthesis loses an original assigned outcome")
        summaries[product.config.module] = {"identity": product.identity.to_document(), "result": product.payload}
    analyses = {(p.config.module, p.config.assignments[0].seed): p for p in found.values() if p.config.phase == "analyse"}
    return {**base, "scientific_completion": "COMPLETED" if len(found) == len(configs) else "INCOMPLETE",
        "completed_operations": len(found), "population_summaries": summaries,
        "roots": [{"seed": r.seed, "unit_id": r.unit_id, "role": r.role, "modules": {m:
            {"status": "AVAILABLE" if (m, r.seed) in analyses else "UNAVAILABLE",
             "identity": analyses[(m, r.seed)].identity.to_document() if (m, r.seed) in analyses else None}
            for m in r.modules}} for r in specification.assignments],
        "array_custody": {"containers": sum(p.array_artifact is not None for p in found.values()),
            "physical_bytes": sum(p.array_artifact.size_bytes for p in found.values() if p.array_artifact is not None), "full_populations_are_chunked": True}}
