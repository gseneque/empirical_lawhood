# SPDX-License-Identifier: MPL-2.0
"""Shared installed Matrix source metadata effects and candidate preparation.

Scientific declarations remain in their source owners. These functions reuse
ordinary dataset authorization, guarded publication, source verification and
prospective compilation; configuration cannot choose implementation callbacks.
"""
from dataclasses import replace
from datetime import datetime,timedelta
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace


def publish_source_input_record(*, writer, prefix, namespace, name, record, relative=None, logical=None, lineage_parents=(), model_input=False):
    """Publish through the ordinary writer and return its stable read observation.

    The write's created flag is retained separately as operational information;
    embedding it in another immutable scientific record would change replay.
    """
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, ArtifactProfile, ArtifactWriteRequest, derived_outcome_access, lineage_parent_sort_key

    if type(lineage_parents) is not tuple or any(type(value) is not ArtifactLineageParent for value in lineage_parents):
        raise TypeError("source publication requires exact actual lineage parents")
    if type(model_input) is not bool or model_input and not lineage_parents:
        raise ValueError("model input publication requires its explicit nonempty actual parent census")
    parents = tuple(sorted(set(lineage_parents), key=lineage_parent_sort_key))
    if model_input:
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
        from empirical_lawhood.kernel.evidence import VisibilityCeiling
        access, visibility = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
            declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=parents)
    else:
        access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(value.outcome_access for value in parents))
        visibility = inherited_visibility(tuple(value.visibility_ceiling for value in parents), access)
    ceilings = tuple(value.visibility_ceiling for value in parents)
    path = prefix + "/" + name + ".json" if relative is None else relative
    identifier = logical or "finite-dt-input." + namespace + "." + name.replace("/", ".")
    request = ArtifactWriteRequest(identifier, path, record.SCHEMA, ArtifactProfile.CANONICAL_JSON,
        "application/json", "finite-dt-inputs." + namespace, str(Path(path).parent), record.canonical_bytes(),
        visibility, ceilings, access, lineage_parents=parents)
    writer.preflight_write(request)
    result = writer.write(request)
    return result, _publication_from_manifest(writer, writer.read_manifest(path))


def materialize_source_input_rows(*,writer,project,prefix,namespace,selected,key_path,selected_start,seconds,reasons,
        implementation,publication,retained,rows,rule,bank,programme,cutoff,envelope,root,rows_owner,r,assay_identity,certificate,verification_kind):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity
    from empirical_lawhood.api import matrix_finite_dt_dataset_metadata as metadata_owner
    from empirical_lawhood.api.matrix_finite_dt_source_pipeline import (
        MatrixFiniteDtDatasetClock, MatrixFiniteDtSourceMaterialization,
        materialize_finite_dt_source)
    from empirical_lawhood.api.selected_e4_bank_recipe import _read_exact_record
    from empirical_lawhood.infrastructure import authority as authority_owner
    from empirical_lawhood.kernel.authority import AuthorityAction
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.kernel.references import ArtifactIdentity
    from empirical_lawhood.kernel.worlds import WorldKind
    from empirical_lawhood.planning import dataset_authority as grants
    from empirical_lawhood.planning.datasets import DatasetEvidenceClass, DatasetMaterializationClass
    from empirical_lawhood.planning.evidence_profiles import (
        EvidenceWorldKind, bind_profile_selection, build_observation_evidence_world_registry)
    from empirical_lawhood.planning.source_pipelines import (
        SourcePipelineArtifactProfile, SourcePipelineChangeSemantics, SourcePipelineCoordinate,
        SourcePipelineMode, SourcePipelineProfile, SourcePipelineTransformEdge)
    from empirical_lawhood.planning.study_authoring import CapabilitySelection
    from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult
    from empirical_lawhood.adapters.methods.matrix_source_evidence import MatrixSourcePipelineConfig

    if (envelope.files.max_single_file_bytes < len(rows.canonical_bytes())
            or envelope.resources.source_scan_bytes < len(rows.canonical_bytes())
            or envelope.resources.output_bytes < len(rows.canonical_bytes())
            or envelope.files.max_source_files < 1 or envelope.files.max_destination_files < 1):
        raise ValueError("selected dataset envelope cannot contain the complete actual pending-source rows")
    source = publication("source/rows", rows)
    contract = ObjectIdentity.from_record(writer.root.contract.storage_root_id, writer.root.contract)
    source_scope = grants.DatasetStorageScope("scope." + namespace + ".source", contract, prefix + "/source")
    destination_scope = grants.DatasetStorageScope("scope." + namespace + ".destination", contract, prefix + "/derived")
    control_scope = grants.DatasetStorageScope("scope." + namespace + ".control", contract, prefix + "/dataset-controls")
    def raw_identity(name, raw):
        relative = prefix + "/source/" + name
        stored = writer.write(ArtifactWriteRequest("finite-dt-runtime." + namespace + "." + name,
            relative, "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", ArtifactProfile.RAW_SOURCE_BYTES,
            "text/plain", "finite-dt-runtime." + namespace, str(Path(relative).parent), raw, r.PROSPECTIVE, (), r.BLIND))
        return ArtifactIdentity(stored.logical.logical_artifact_id, "actual-selected-source-runtime-or-environment",
            stored.logical.payload_schema, stored.logical.content_sha256, stored.logical.media_type, stored.materialization.size_bytes)
    runtime = raw_identity("metadata-runtime.py", Path(metadata_owner.__file__).read_bytes())
    environment = raw_identity("uv.lock", (project / "uv.lock").read_bytes())
    manifest, metadata = metadata_owner.make_dataset_manifest(namespace=namespace, source_publication=source,
        output_relative_path=prefix + "/derived/rows.json", rows=rows, rule=rule, cutoff=cutoff,
        source_scope=source_scope, destination_scope=destination_scope, control_scope=control_scope,
        envelope=envelope, runtime=runtime, environment=environment)
    for reference, record in metadata:
        publication("dataset-controls/objects/" + reference.object_fingerprint, record, logical=reference.object_id)
    publication("dataset-controls/manifest", manifest,
        relative=control_scope.relative_prefix + "/" + metadata_owner.MANIFEST_FILENAME, logical=manifest.manifest_id)
    capabilities, datasets = metadata_owner.dataset_registries(envelope.resources, maximum_rows=len(rows.rows), row_kind=type(rows))
    transform = rows_owner.transform_capability(envelope.resources)
    source_adapter = rows_owner.source_capability(envelope.resources)
    coordinates = tuple(SourcePipelineCoordinate("coordinate." + namespace + "." + name, name, unit, frame, cutoff.clock_id)
        for name, unit, frame in (("invalid-disposition", "status", "declared-native-acquisition-status"),
            ("physical-unit", "identity", "matrix-original-independent-group-id"),
            ("root", "identity", "matrix-original-scheduled-root-id")))
    preserved = SourcePipelineChangeSemantics.PRESERVED
    edge = SourcePipelineTransformEdge("edge." + namespace, 0, transform.registry_id,
        CapabilitySelection(transform.capability_key, transform.capability_version, transform.implementation_sha256),
        rule.identity, rows.SCHEMA, rows.SCHEMA, "application/json", "application/json", rows_owner.FORMAT_ID,
        rows_owner.FORMAT_ID, coordinates, coordinates, preserved, None, preserved, None, preserved, None,
        preserved, None, True, True, rule.identity, envelope.resources)
    pipeline_profile = SourcePipelineProfile("profile." + namespace, "1.0.0", SourcePipelineMode.SIMULATED,
        CapabilitySelection(source_adapter.capability_key, source_adapter.capability_version, source_adapter.implementation_sha256),
        rule.identity, source.logical.logical_artifact_id, ObjectIdentity.from_record(source.materialization.materialization_id, source.materialization),
        rows.fingerprint(), len(rows.canonical_bytes()), selected["licence_id"], writer.root.contract.storage_root_id,
        source.materialization.relative_path, rows.SCHEMA, "application/json", rows_owner.FORMAT_ID, coordinates,
        (edge,), rows.SCHEMA, "application/json", ".json", SourcePipelineArtifactProfile.CANONICAL_JSON, coordinates,
        (rule.identity,), "physical-unit", "invalid-disposition", r.pin(cutoff, "cutoff_id"),
        ObjectIdentity.from_record(manifest.manifest_id, manifest), envelope.resources, len(rows.rows), len(programme.group_ids),
        selected["scratch_namespace"], prefix + "/derived/rows.json", root.system.world.world_id,
        assay_identity, (identity(bank.specification.selection.numerical_design).object_id,),
        "receiver." + namespace, root.experiment.obligations.validity.validity_id,
        root.experiment.obligations.uncertainty.uncertainty_id, r.BLIND, r.PROSPECTIVE)
    clock = MatrixFiniteDtDatasetClock("clock." + namespace + ".dataset-authorizer")
    retained_policy = retained("dataset-controls/policy", grants.DatasetOperationPolicy)
    # Unselected validity starts retain their original actual-clock edition;
    # every selected coordinate is nevertheless compared on exact replay.
    start_text = selected_start or (retained_policy.valid_from_utc if retained_policy is not None else clock.now_utc())
    start = datetime.fromisoformat(start_text.replace("Z", "+00:00"))
    until = start + timedelta(seconds=seconds)
    policy = grants.DatasetOperationPolicy("policy." + namespace, r.pin(manifest, "manifest_id"),
        AuthorityAction.DATASET_TRANSFORMATION, (source_scope,), destination_scope, control_scope, envelope,
        DatasetEvidenceClass.METADATA_ONLY, DatasetMaterializationClass.METADATA_OBSERVATION,
        WorldKind.NUMERICAL_SIMULATOR, r.BLIND, r.PROSPECTIVE, implementation.observed_git_head,
        selected["metadata_issuer_id"], selected["metadata_approver_id"], start.isoformat().replace("+00:00", "Z"),
        until.isoformat().replace("+00:00", "Z"), reasons)
    if retained_policy is not None and retained_policy != policy:
        raise PermissionError("selected metadata policy changes its retained exact approver, validity, scope or source edition")
    if retained_policy is None:
        publication("dataset-controls/policy", policy)
    request = grants.DatasetOperationRequest("request." + namespace, r.pin(policy, "policy_id"), policy.manifest,
        AuthorityAction.DATASET_TRANSFORMATION, (source_scope,), destination_scope, control_scope, envelope,
        DatasetEvidenceClass.METADATA_ONLY, DatasetMaterializationClass.METADATA_OBSERVATION, WorldKind.NUMERICAL_SIMULATOR,
        r.BLIND, r.PROSPECTIVE, implementation.observed_git_head, selected["metadata_requester_id"],
        policy.valid_from_utc, policy.valid_until_utc, False, False, False, tuple(selected["metadata_reason_codes"]))
    publication("dataset-controls/request", request)
    if not key_path.parent.exists():
        key_path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
    signer = (authority_owner.Ed25519DatasetAuthorizationSigner.from_private_key_file(key_path) if key_path.exists()
        else authority_owner.Ed25519DatasetAuthorizationSigner.create_private_key_file(key_path))
    import empirical_lawhood.planning.dataset_authority as authority_implementation
    issuer = grants.DatasetAuthorizationIssuerRegistration("issuer-registration." + namespace,
        selected["metadata_issuer_id"], frozenset((AuthorityAction.DATASET_TRANSFORMATION,)),
        sha256(Path(authority_implementation.__file__).read_bytes()).hexdigest(), "1.0.0", signer.signature_algorithm,
        signer.signature_version, signer.verification_key_hex, r.BLIND)
    publication("dataset-controls/issuer", issuer)
    authorization = retained("dataset-controls/authorization", grants.DatasetOperationAuthorization)
    if authorization is None:
        authorization = grants.issue_dataset_operation_authorization(policy=policy, request=request,
            authorization_id="authorization." + namespace, approved_by=selected["metadata_approver_id"],
            issuer_registration=issuer, signer=signer, clock=clock)
        publication("dataset-controls/authorization", authorization)
    publication("certificate", certificate)
    pipeline_config = retained("pipeline-config", MatrixSourcePipelineConfig)
    if pipeline_config is None:
        materialized = materialize_finite_dt_source(writer=writer, programme=programme, bank=bank, rows=rows, rule=rule,
            source_publication=source, profile=pipeline_profile, source_manifest=source_adapter,
            capability_registry=capabilities, dataset_registry=datasets, dataset_operation_request=request,
            policy=policy, authorization=authorization, issuer_registration=issuer, decision_clock=clock,
            verification_relative_path=control_scope.relative_prefix + "/verification.json", record_id=namespace)
        for name, value in (("source", materialized.source_publication), ("output", materialized.output_publication),
                ("verification", materialized.verification_publication)):
            publication("dataset-controls/" + name + "-publication", value)
        # This marker is last, after every original handle is durable.
        publication("pipeline-config", materialized.config)
    else:
        if (pipeline_config.profile != pipeline_profile or pipeline_config.dataset_operation_request != request
                or pipeline_config.execution_evidence.dataset_operation_policy != policy
                or pipeline_config.execution_evidence.dataset_operation_authorization != authorization
                or pipeline_config.execution_evidence.dataset_authorization_issuer != issuer):
            raise PermissionError("retained source materializer changes this exact current input/grant edition")
        source_pub = retained("dataset-controls/source-publication", ArtifactWriteResult)
        output_pub = retained("dataset-controls/output-publication", ArtifactWriteResult)
        verification_pub = retained("dataset-controls/verification-publication", ArtifactWriteResult)
        if None in (source_pub, output_pub, verification_pub):
            raise PermissionError("retained pipeline is incomplete; recover its original publication handles before retry")
        verification = _read_exact_record(writer, verification_pub, verification_kind)
        materialized = MatrixFiniteDtSourceMaterialization(pipeline_config, rows, source_pub, output_pub, verification, verification_pub)
    registry = build_observation_evidence_world_registry()
    world, = (value for value in registry.world_profiles if value.world_kind is EvidenceWorldKind.DETERMINISTIC_SIMULATOR)
    evidence_profile = bind_profile_selection(selection_id="evidence-profile." + namespace,
        draft_id="draft." + namespace, registry=registry, world_profile_id=world.profile_id,
        objective_profile_id="objective.observation-order", requested_rungs=())
    return materialized,evidence_profile


def _bind_source_scope(root,scope):
    """Bind the actual installed source scope as a declared scientific operand."""
    from empirical_lawhood.adapters.methods.matrix_finite_dt_source_records import MatrixFiniteDtSourceScope
    from empirical_lawhood.adapters.methods.matrix_prepared_source_records import MatrixPreparedSourceScope
    from empirical_lawhood.kernel.evidence import OutcomeAccess,VisibilityCeiling
    from empirical_lawhood.planning.study_authoring import DesignInputRecord,DesignInputRole,StudyDraft
    if type(root) is not StudyDraft or type(scope) not in (MatrixFiniteDtSourceScope,MatrixPreparedSourceScope):
        raise TypeError('source scope binding requires exact installed draft and source-scope owners')
    root.__post_init__();scope.__post_init__()
    if root.system is None or root.experiment is None or scope.cutoff not in root.experiment.information_cutoffs:
        raise ValueError('source scope changes the actual scientific root cutoff')
    binding=DesignInputRecord(root.draft_id+'.source-scope',scope.identity,scope.fingerprint(),scope.cutoff,
        DesignInputRole.READINESS_METADATA,OutcomeAccess.OUTCOME_BLIND,VisibilityCeiling.PROSPECTIVE,
        root.system.authority_policy.delegate_id)
    existing={value.input_id:value for value in root.design_inputs}
    if binding.input_id in existing and existing[binding.input_id]!=binding:
        raise PermissionError('source scope conflicts with its retained exact design binding')
    if any(value.object_identity.object_id==scope.identity.object_id and value.object_identity!=scope.identity
            for value in root.design_inputs):
        raise PermissionError('source scope substitutes an existing scientific identity')
    existing[binding.input_id]=binding
    return replace(root,design_inputs=tuple(existing[key] for key in sorted(existing)),
        design_origin=replace(root.design_origin,
            declared_input_ids=tuple(sorted({*root.design_origin.declared_input_ids,binding.input_id}))))


def prepare_source_candidate(*,writer,project,namespace,publication,domain,bindings,scope,operands,materialized,
        root,budget,operational,implementation,programme,operand_lineage,model_input_names=frozenset()):
    from empirical_lawhood.adapters.composition.experiment_authoring import formal_entry
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_preparation import _source_projection
    from empirical_lawhood.api.derived_metadata_access import derive_canonical_metadata_access
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.api.recursive_prospective_authoring import preview_recursive_prospective_candidate
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.formal_gaps import FormalGapEvidenceWorld
    from empirical_lawhood.runtime.experiment_resources import bind_execution_resources
    from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
    from empirical_lawhood.runtime.recursive_prospective import RecursiveProspectiveDesignInputs, RecursiveProspectiveOperand
    from empirical_lawhood.kernel.evidence import OutcomeAccess, inherited_visibility
    from empirical_lawhood.runtime.artifacts import derived_outcome_access

    if set(operand_lineage) != set(operands):
        raise ValueError("source preparation requires the complete actual operand lineage census")
    if type(model_input_names) is not frozenset or not model_input_names <= set(operands):
        raise ValueError("source preparation changes its explicit model input role census")
    operand_access = {}
    for name, parents in operand_lineage.items():
        if name in model_input_names:
            from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import produced_access
            from empirical_lawhood.kernel.evidence import VisibilityCeiling
            if not parents:
                raise ValueError("source model input omits its complete actual parent census")
            operand_access[name] = produced_access(declared_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
                declared_visibility=VisibilityCeiling.DEVELOPMENT_ONLY, parents=parents)
        else:
            access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(value.outcome_access for value in parents))
            operand_access[name] = (access, inherited_visibility(tuple(value.visibility_ceiling for value in parents), access))
    root=_bind_source_scope(root,scope)
    terminals = tuple((name, budget) for name in ("adjudicate", "pipeline", "qualification"))
    lowered, records, _, _ = domain.compose_source_draft(scope=scope, scientific_operands=operands,
        pipeline=materialized.config, root=root, campaign=root.campaign, draft_id="draft." + namespace,
        terminal_budgets=terminals, operand_access=operand_access)
    from empirical_lawhood.api.derived_array_access import DerivedInputAccess, derive_matrix_input_access_batch, supports_derived_input_access_batch
    from empirical_lawhood.infrastructure.publication_metadata import (
        checkpoint_publication_access,
    )
    configs, qualifications, input_bindings = [], [], []
    batch_access = supports_derived_input_access_batch(writer, len(lowered.external_inputs))
    pending = []
    record_index = dict(records)
    parent_index = {(value.SCHEMA, value.fingerprint()): operand_lineage[name] for name, value in operands.items()}
    if batch_access:
        checkpoint_publication_access(writer)
    for external in lowered.external_inputs:
        record = record_index[external.input_id] if batch_access else dict(records)[external.input_id]
        stored = publication("inputs/" + sha256(external.input_id.encode()).hexdigest(), record,
            logical=external.logical_artifact_id, lineage_parents=parent_index[(record.SCHEMA, record.fingerprint())])
        if batch_access:
            pending.append(DerivedInputAccess(stored, record, external))
        else:
            config, qualification = derive_canonical_metadata_access(writer=writer, publication=stored, record=record,
                external=external, root=root, source_profile=materialized.config.profile)
            configs.append(config)
            qualifications.append(qualification)
        input_bindings.append((external.logical_artifact_id, writer.root.resolve(stored.materialization.relative_path, for_write=False)))
    if pending:
        for config, qualification in derive_matrix_input_access_batch(writer=writer, inputs=tuple(pending),
                root=root, source_profile=materialized.config.profile):
            configs.append(config)
            qualifications.append(qualification)
    # External inputs are ordered by input ID; hashed receipt IDs have their
    # own canonical order. Preserve every receipt and let the compiler reject
    # duplicate identities rather than collapsing them here.
    qualifications=tuple(sorted(qualifications,key=lambda value:value.receipt_id))
    controls = SimpleNamespace(source_configs=tuple(configs), qualifications=qualifications)
    lowered = _source_projection(lowered, controls,
        {value.logical_artifact_id: dict(records)[value.input_id].VERSION for value in lowered.external_inputs})
    registrations, capability_registry, codecs = operation_catalog()
    compiled = compile_recursive_wave(draft=lowered, registrations=registrations, registry=capability_registry,
        implementation_commit=implementation.observed_git_head, qualifications=qualifications,
        known_design_inputs=lowered.prospective_draft.design_inputs, output_codecs=codecs,
        implementation_sha256=implementation.code_sources_sha256)
    if compiled.candidate_context is None or compiled.candidate_draft is None:
        raise ValueError("actual source candidate retains unresolved requirements: " + str(compiled.candidate_report))
    authoring, standard = formal_entry(compiled.candidate_draft, compiled.candidate_context, scope.identity,
        prefix=namespace, minimum_units=len(programme.group_ids),
        operand_description="Actual finite-dt source {domain}; sampling/continuum/transport NOT_ESTABLISHED",
        estimator="complete-source-contract", uncertainty="global-qualification-not-established",
        ceiling=bindings.closeout_declaration().manifest().maximum_evidence_ceiling,
        evaluator=bindings.closeout_declaration().manifest(), input_schema=scope.SCHEMA,
        output_schema=bindings.closeout_declaration().outputs[0].payload_schema,
        world=FormalGapEvidenceWorld.NUMERICAL_SIMULATOR, minimum_views=len(root.system.numerical_views),
        evidence_unit_ids=programme.group_ids)
    lowered, records, _, _ = domain.compose_source_draft(scope=scope, scientific_operands=operands,
        pipeline=materialized.config, root=authoring.draft, campaign=authoring.draft.campaign,
        draft_id="draft." + namespace, terminal_budgets=terminals, operand_access=operand_access)
    lowered = _source_projection(lowered, controls,
        {value.logical_artifact_id: dict(records)[value.input_id].VERSION for value in lowered.external_inputs})
    entry = replace(authoring.entry_package, checklist=replace(authoring.entry_package.checklist,
        draft=ObjectIdentity.from_record(lowered.prospective_draft.draft_id, lowered.prospective_draft)))
    for config in configs:
        stored = publication("inputs/config." + config.fingerprint(), config)
        input_bindings.append((config.fingerprint(), writer.root.resolve(stored.materialization.relative_path, for_write=False)))
    design = RecursiveProspectiveDesignInputs("prospective." + namespace, lowered, entry, standard.formal_methods,
        standard.source_inventories, qualifications,
        lowered.prospective_draft.design_inputs, tuple(sorted((RecursiveProspectiveOperand(value.logical_artifact_id,
            value.expected_content_sha256, value.maximum_size_bytes, value.payload_schema, value.media_type,
            value.outcome_access, value.visibility_ceiling) for value in lowered.external_inputs),
            key=lambda value: value.logical_artifact_id)))
    preview = preview_recursive_prospective_candidate(design_inputs=design, project_root=project,
        artifact_writer=writer, input_bindings=tuple(sorted(input_bindings)))
    budgets = {operation.node_id: operation.resource_budget for operation in lowered.operations}
    phases = {node: node.rsplit(".", 1)[-1] for node in budgets}
    resource_selection = operational.for_component(component_id=namespace, budgets=budgets, phases=phases, native_groups={})
    resources = bind_execution_resources(resource_selection, issued_extensions=preview.issued_extensions)
    prospective = design.bind_resources(resources)
    return prospective,tuple(configs),authoring,lowered,entry,terminals
