# SPDX-License-Identifier: MPL-2.0
"""Fresh receipt-bound reconstruction of an original native TRAIN bank export.

This transition authenticates original producing tasks and bytes. It performs no
independent array mathematics and asserts no prior exporter or derivation success.
Generic completion documents and restored failed-scope outputs grant no trust.
The ordinary exporter retains its complete independent mathematical replay.
"""
from contextlib import ExitStack, contextmanager
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile, artifact_publication_member
from empirical_lawhood.runtime.native_training_export import NativeTrainingExportAdoptionSelection

def _require_stock_export_plane(plane):
    from empirical_lawhood.api.recursive_execution import _read_only_custody_policy
    from empirical_lawhood.infrastructure.publication_metadata import supports_closed_publication_access
    if (_read_only_custody_policy(plane) is None or not supports_closed_publication_access(plane)):
        raise TypeError('export adoption requires the actual stock read-only custody composition')


@contextmanager
def _export_scope(plane):
    _require_stock_export_plane(plane)
    with plane.read_context() as view:
        view.require_verification_snapshot()
        try:
            yield view
        finally:
            view.require_verification_snapshot()


@contextmanager
def _adoption_lock(plane, selection):
    """Keep existing native nonentry observations stable through final scope exit."""
    _require_stock_export_plane(plane)
    from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
    path = plane.root.resolve('runs/'+selection.run_id+'/.native-execution.lock', for_write=False)
    if not path.is_file() or path.stat().st_size != 0:
        raise PermissionError('export adoption requires the original existing native execution lock')
    contacts = ExternalNativeEffectContactStore(plane=plane, execution_plan=selection.execution_plan,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE)
    with contacts.execution_lock(selection.run_id):
        yield


def _source_now(project_root):
    from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    project = Path(project_root).resolve(strict=True)
    require_selected_implementation(project)
    return implementation_binding(project)


def _receipt_pins(receipts):
    return tuple(sorted((ObjectIdentity.from_record(value.receipt_id, value) for value in receipts),
        key=lambda value: value.object_id))


def _receipt_product_contracts(specification):
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as owner
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
    contracts = [('entry', owner.entry_task_id(specification), r.NativeTrainingAcquisitionSeal, 'product')]
    kinds = (('prefix', r.NativeTrainingPrefixHistory, 'product'), ('prefix', r.ScheduledCheckpoint, 'checkpoint'),
        ('numerical', r.NativeTrainingNumericalAssessment, 'product'), ('measure', r.NativeTrainingPrefixWitness, 'product'),
        ('check', r.NativeTrainingFrameAssessment, 'product'), ('project', r.NativeTrainingCausalPrefix, 'product'),
        ('physical-forecast', r.NativeTrainingPhysicalForecast, 'product'), ('responses', r.NativeTrainingResponse, 'product'),
        ('response-score', r.NativeTrainingScore, 'score'), ('response-score', r.NativeTrainingOutcome, 'product'),
        ('feature', r.NativeTrainingFeature, 'product'))
    for root_id in specification.root_ids:
        contracts.extend((root_id, owner.task_id(root_id, phase), kind, label) for phase, kind, label in kinds)
    contracts.append(('terminal', owner.terminal_task_id(specification), r.NativeTrainingSummary, 'product'))
    return tuple(contracts)


def _consume_receipt_products(*, writer, products, plan, specification, consume):
    """Decode one exact closed JSON roster under the existing plural owner."""
    from hashlib import sha256
    from empirical_lawhood.api.native_training_banks import _receipt_product_binding
    from empirical_lawhood.infrastructure.publication_metadata import consume_published_materializations
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    from empirical_lawhood.kernel.decoding import decode_canonical_bytes
    from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
    contracts = _receipt_product_contracts(specification)
    selected = {}
    writer.require_verification_snapshot()
    for _, task_id, kind, label in contracts:
        receipt, logical, material = _receipt_product_binding(products, plan, task_id, kind, label)
        if (material.storage_root_id != writer.root.contract.storage_root_id or material.compression != 'none'
                or material.partition_selector is not None or material.physical_sha256 != logical.content_sha256):
            raise PermissionError('export adoption changes the exact canonical producer materialization')
        actual = writer.read_manifest(material.relative_path, maximum_bytes=writer.custody_limits.manifest_bytes)
        if (actual.logical, actual.materialization) != (logical, material) or actual.publication is None:
            raise PermissionError('export adoption changes its original selected receipt-product sidecar')
        relative = material.relative_path+'.manifest.json'
        raw = read_bounded_bytes(writer.root.resolve(relative, for_write=False), maximum_bytes=writer.custody_limits.manifest_bytes)
        sidecar = writer._manifest_materialization(logical_artifact_id=logical.logical_artifact_id, relative_path=relative, payload=raw)
        selected[(task_id, label)] = (kind, receipt, ArtifactWriteResult(logical, material, sidecar, False))
    def decode(authenticated):
        decoded, publications = {}, {}
        for key, (kind, receipt, publication) in selected.items():
            material, logical = publication.materialization, publication.logical
            actual = authenticated[material.relative_path]
            if (actual.logical, actual.materialization) != (logical, material):
                raise PermissionError('export adoption batch changes its selected receipt-product binding')
            raw = read_bounded_bytes(writer.root.resolve(material.relative_path, for_write=False), maximum_bytes=material.size_bytes)
            value = decode_canonical_bytes(raw, kind, maximum_bytes=material.size_bytes)
            if (len(raw) != material.size_bytes or sha256(raw).hexdigest() != material.physical_sha256
                    or value.canonical_bytes() != raw or value.fingerprint() != logical.content_sha256):
                raise PermissionError('export adoption changes actual canonical producer bytes')
            decoded[key], publications[key] = (value, receipt), publication
        def get_product(task_id, kind, label='product'):
            value, receipt = decoded[(task_id, label)]
            if type(value) is not kind:
                raise PermissionError('export adoption substitutes its exact freshly decoded producer type')
            return value, receipt
        return consume(get_product, publications)
    return consume_published_materializations(writer, tuple(row[2] for row in selected.values()), consume=decode)


def _authenticate_receipt_reconstruction(*, writer, specification, request, draft, plan, products, acquisition, get_product, custody_scopes):
    """Use the same metadata guards as full reads, then inspect actual native stores."""
    from empirical_lawhood.api.matrix_native_read_custody import _graph
    from empirical_lawhood.api.matrix_native_training_read import _authenticate_root_records, _validate_complete_root_results
    from empirical_lawhood.api.matrix_native_acquisition_replay import authenticate_native_custody
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_acquisition as owner
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as r
    configs, tasks = _graph(specification, request, draft, plan)
    run_id = plan.source_plan.object_id
    if acquisition != r.acquisition_seal(specification, request):
        raise PermissionError('export adoption changes the original pre-contact acquisition seal')
    source_index = ScheduledSourceIndex.from_shared(reservation=request.train_manifest.reservation,
        specification=request.train_manifest.native_specification, provenances=request.train_manifest.provenances)
    source_index.require_roster(request.sources, expected_root_ids=specification.root_ids)
    pairs, native_checks = [], []
    for root_id in specification.root_ids:
        def get(phase, kind, label='product'):
            return get_product(owner.task_id(root_id, phase), kind, label)[0]
        source, protocol, panels, values = _authenticate_root_records(specification, request, acquisition,
            root_id, configs, products, tasks, run_id, source_index=source_index, get=get)
        native_writer = custody_scopes.enter_context(writer.verification_scope())
        check = dict(artifact_writer=native_writer, specification=specification, request=request,
            seal=acquisition, source=source, protocol=protocol, panels=panels,
            configurations=configs, products=products, tasks=tasks, plan=plan, records=values)
        authenticate_native_custody(**check)
        native_checks.append(check)
        pairs.append((values['feature'], values['outcome']))
    features, outcomes, _ = _validate_complete_root_results(specification, request, acquisition, tuple(pairs),
        get_summary=lambda: get_product(owner.terminal_task_id(specification), r.NativeTrainingSummary)[0])
    def require_native_custody():
        # Existing snapshots cannot represent absent native slots. Reinspect
        # every original definition/nonentry after the last bank/body consumer.
        for arguments in native_checks:
            authenticate_native_custody(**arguments)
        for arguments in native_checks:
            arguments['artifact_writer'].require_verification_snapshot()
    return features, outcomes, require_native_custody


def _authenticate_reconstructed_banks(writer, publications, values, parents):
    """Require the complete original atomic edition, exact bytes and producer lineage."""
    from empirical_lawhood.infrastructure.publication_metadata import authenticate_published_materialization
    from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
    manifests = []
    for value, publication in zip(values, publications, strict=True):
        actual = authenticate_published_materialization(writer, publication)
        body = read_bounded_bytes(writer.root.resolve(actual.materialization.relative_path,
            for_write=False), maximum_bytes=actual.materialization.size_bytes)
        if (body != value.canonical_bytes() or actual.logical.logical_artifact_id != value.identity.object_id
                or actual.logical.payload_schema != value.SCHEMA
                or actual.logical.content_sha256 != value.fingerprint()
                or actual.materialization.physical_sha256 != value.fingerprint()
                or actual.logical.lineage_parents != parents
                or actual.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or actual.logical.media_type != 'application/json'
                or actual.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or actual.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise PermissionError('export adoption changes exact reconstructed original bank bytes/lineage')
        manifests.append(actual)
    binding = manifests[0].publication
    expected = {artifact_publication_member(value.logical, value.materialization) for value in manifests}
    if (binding is None or len(expected) != 3 or len(binding.members) != 3
            or set(binding.members) != expected or any(value.publication != binding for value in manifests)):
        raise PermissionError('export adoption requires the original exact atomic three-bank publication')
    writer.require_verification_snapshot()


def adopt_native_training_bank_export(*, directory, artifact_writer, output_directory, record_id,
        selection, expected_locator, project_root):
    """Reconstruct retained banks from fresh original producer custody, without math.

    The selection is untrusted metadata. Only the complete current receipt and
    native custody checks authorize the returned reconstruction. No completion
    marker, saved report, filename, or former full-read assertion is accepted.
    Current-source migration and subsequent scientific qualification stay separate.
    """
    from empirical_lawhood.api.native_training_banks import (
        NativeTrainingBankExport, _collect_export_records, _export_authored_preflight,
    )
    from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import export_training_banks
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent, lineage_parent_sort_key
    if type(selection) is not NativeTrainingExportAdoptionSelection:
        raise TypeError('export adoption requires its explicit typed receipt-bound reconstruction selection')
    selection.__post_init__()
    if expected_locator is None:
        raise TypeError('export adoption requires its exact original public native TRAIN locator')
    before = _source_now(project_root)
    with _adoption_lock(artifact_writer, selection):
        with _export_scope(artifact_writer) as writer:
            root = Path(writer.root.contract.canonical_path)
            if (Path(directory).resolve(strict=True).relative_to(root).as_posix() != selection.authored_directory
                    or record_id != selection.bank_record_id):
                raise PermissionError('export adoption changes original authored directory or bank edition')
            target = Path(output_directory)
            if (not target.is_absolute() or target != target.resolve(strict=True)
                    or tuple(pub.materialization.relative_path for pub in selection.bank_publications) !=
                        tuple(target.relative_to(root).as_posix()+'/'+name+'.json' for name in ('allocation', 'features', 'outcomes'))):
                raise PermissionError('export adoption changes original immutable export destinations')
            result, roots, values = _read_recursive_wave_with_roots(directory=directory, artifact_writer=writer,
                include_products=True, terminal_product_format='compact', allow_partial=False,
                validate_authored=_export_authored_preflight(directory=directory, artifact_writer=writer,
                    expected_locator=expected_locator))
            report, products, draft, plan = result
            packet, original_draft, source, run, original_plan, _ = roots
            specification, request, instance = values
            if (source != selection.producer_implementation or draft != original_draft or plan != original_plan
                    or selection.packet != ObjectIdentity.from_record(packet.packet_id, packet)
                    or selection.execution_plan != ObjectIdentity.from_record(plan.execution_plan_id, plan)
                    or selection.specification != specification.identity or selection.request != request.identity
                    or selection.run_id != run.run_plan_id
                    or report.get('status') != 'SUCCEEDED' or report.get('run_id') != run.run_plan_id
                    or report.get('packet_sha256') != packet.fingerprint()
                    or set(products['receipts']) != {task.task_id for task in plan.tasks}):
                raise PermissionError('export adoption changes original source, complete graph or actual winning receipt census')
            with ExitStack() as custody_scopes:
                def consume(get_product, publications):
                    from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_acquisition import entry_task_id
                    acquisition, acquisition_pub, acquisition_receipt, receipts, features, outcomes = _collect_export_records(
                        writer=writer, products=products, plan=plan, specification=specification,
                            get_product=get_product, acquisition_publication=publications[(entry_task_id(specification), 'product')])
                    authenticated_features, authenticated_outcomes, require_native_custody = _authenticate_receipt_reconstruction(
                        writer=writer, specification=specification, request=request, draft=draft, plan=plan,
                        products=products, acquisition=acquisition, get_product=get_product, custody_scopes=custody_scopes)
                    if (tuple(sorted(features, key=lambda value: value.unit_id)) != authenticated_features
                            or tuple(sorted(outcomes, key=lambda value: value.unit_id)) != authenticated_outcomes):
                        raise PermissionError('export adoption substitutes its exact authenticated whole-root bank producers')
                    allocation, feature_bank, outcome_bank = export_training_banks(specification, request,
                        acquisition=acquisition, features=features, outcomes=outcomes, record_id=record_id)
                    if allocation.identity != instance.allocation:
                        raise PermissionError('export adoption changes original authored complete allocation')
                    references = (ObjectIdentity.from_record(packet.packet_id, packet), specification.identity,
                        request.identity, acquisition.identity, *_receipt_pins(receipts))
                    parents = tuple(sorted((ArtifactLineageParent(value, VisibilityCeiling.DEVELOPMENT_ONLY,
                        OutcomeAccess.DEVELOPMENT_VISIBLE) for value in set(references)), key=lineage_parent_sort_key))
                    _authenticate_reconstructed_banks(writer, selection.bank_publications,
                        (allocation, feature_bank, outcome_bank), parents)
                    returned = NativeTrainingBankExport(allocation, feature_bank, outcome_bank, selection.bank_publications,
                        run.run_plan_id, acquisition, acquisition_pub, acquisition_receipt,
                        validation_origin='RECEIPT_BOUND_BANK_RECONSTRUCTION', locator=expected_locator)
                    if _source_now(project_root) != before:
                        raise PermissionError("export adoption reader source changed during fresh authentication")
                    require_native_custody()
                    writer.require_verification_snapshot()
                    return returned
                returned = _consume_receipt_products(writer=writer, products=products, plan=plan,
                    specification=specification, consume=consume)
                if _source_now(project_root) != before:
                    raise PermissionError('export adoption reader source changed during fresh authentication')
                writer.require_verification_snapshot()
            writer.require_verification_snapshot()
        if _source_now(project_root) != before:
            raise PermissionError('export adoption reader source changed before return')
        return returned
