# SPDX-License-Identifier: MPL-2.0
"""Live original E3 products and actual E4 revision observations for C26."""
from contextlib import contextmanager
from dataclasses import dataclass

from empirical_lawhood.kernel.provenance import ObjectIdentity


@contextmanager
def programme_e3_originals(context, *, publish=False):
    """Hold genuine current protected custody through dependent publications.

    A normal metadata projection may materialize the ordinary five-member E3
    export. Inspect-only callers require that exact retained edition and never
    publish or recover it. Neither path makes a blind copy of protected models.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_exports import ConfiguredProtectedE3ProductExportSelection
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeProducedInput, MatrixProgrammePublishedInput
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.product_export import _PRODUCTS, _original_product, _write_request
    from empirical_lawhood.api.domain_composition.matrix_configured_protected_response.scientific_read import ConfiguredE3OriginalProducts
    from empirical_lawhood.api.matrix_programme_projection import MatrixProgrammeE3Originals, MatrixProgrammePrerequisite
    from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
    output = context.directory / 'derived' / 'e3-originals'
    relative = output.relative_to(context.writer.root.contract.canonical_path).as_posix()
    with context.programme_e3_products() as read:
        selection = ConfiguredProtectedE3ProductExportSelection('export.' + context.namespace + '.e3',
            read.package.run_plan_id, ObjectIdentity.from_record(read.package.package_id, read.package),
            read.reveal_authority.object_id, 'original.' + context.namespace + '.e3', relative)
        # Inspect-only joins reuse the live original bytes. Keep access fresh
        # between handles and the complete byte guards before/after the yield.
        # Publication and custom reader policies retain every eager checkpoint.
        checkpoint = (read.require_access if not publish and type(read) is ConfiguredE3OriginalProducts
            else read.require_current)
        if read.specification != context.design.e3:
            raise PermissionError('programme original E3 changes the scientific design pinned by C')
        full = ConfiguredMatrixSelectedFrozenPackage(selection.frozen_package_record_id,
            read.specification, read.allocation, read.prefit, read.models, read.model_freeze,
            read.calibration, read.calibrated_freeze, tuple(sorted((*read.allocation.unit_ids('calibration'),
                *read.allocation.unit_ids('evaluation')))))
        public = ConfiguredMatrixSelectedPublicPackage.from_package(full)
        products = tuple((name, *_original_product(read, selection, name, operation, mode))
            for name, operation, mode in _PRODUCTS)
        parents = tuple(parent for _, _, rows in products for parent in rows)
        writes = (_write_request(selection, 'package.json', public, parents, logical_id=public.record_id),
            *(_write_request(selection, name + '.locator.json', locator, parents,
                logical_id=locator.prior_execution.binding_id) for name, locator, _ in products))
        checkpoint()
        if publish:
            actual = context.writer.write_batch(writes)
            publications = tuple(_publication_from_manifest(context.writer,
                context.writer.read_manifest(value.materialization.relative_path)) for value in actual)
        else:
            publications = []
            for request in writes:
                path = context.writer.root.resolve(request.relative_path, for_write=False)
                if not path.exists() and not path.is_symlink():
                    raise MatrixProgrammePrerequisite('e4.development', 'ORIGINAL_E3_EXPORT_REQUIRED',
                        'Derive the actual current E3 original-product export before reading its dependent phase.')
                manifest = context.writer.read_manifest(request.relative_path)
                context.writer.verify_manifest(manifest)
                publication = _publication_from_manifest(context.writer, manifest)
                if (publication.logical.payload_schema, publication.logical.content_sha256,
                        publication.logical.lineage_parents, publication.logical.outcome_access,
                        publication.logical.visibility_ceiling) != (request.payload_schema,
                        __import__('hashlib').sha256(request.payload).hexdigest(), request.lineage_parents,
                        request.outcome_access, request.visibility_ceiling):
                    raise PermissionError('programme original E3 export changes actual scientific lineage/access')
                publications.append(publication)
        public_handle = MatrixProgrammeProducedInput(public.identity, publications[0])
        # The full original reader already authenticated and decoded this
        # exact source member. Use its original preparation through the same
        # current read instead of reopening the entire E3 input graph per use.
        preparation = read.preparation
        if preparation is None or preparation.manifest.reservation != context.inputs.phase('e3.calibration').reservation:
            raise PermissionError('programme original E3 preparation changes C\'s original future reservation')
        # This is an original pre-outcome scientific input, not a model/outcome
        # projection. Preserve its exact current bytes, with no invented fields.
        assay = preparation.protocols[0]
        handles = []
        for name, record, pin in (('preparation', preparation,
                ObjectIdentity.from_record(preparation.selection_id, preparation)),
                ('assay', assay, ObjectIdentity.from_record(assay.protocol_id, assay))):
            path = 'e3-originals/' + name + '.json'
            relative_input = (context.directory / 'derived' / path).relative_to(
                context.writer.root.contract.canonical_path).as_posix()
            checkpoint()
            if publish:
                from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
                from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
                publication = context.writer.write(ArtifactWriteRequest(pin.object_id, relative_input, record.SCHEMA,
                    ArtifactProfile.CANONICAL_JSON, 'application/json', selection.record_id, relative,
                    record.canonical_bytes(), VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
                publication = _publication_from_manifest(context.writer,
                    context.writer.read_manifest(publication.materialization.relative_path))
            else:
                manifest = context.writer.read_manifest(relative_input)
                context.writer.verify_manifest(manifest)
                publication = _publication_from_manifest(context.writer, manifest)
            handle = MatrixProgrammePublishedInput(pin, publication)
            handle.require_record(record, pin)
            handles.append(handle)
        read.require_current()
        yield MatrixProgrammeE3Originals(public, public_handle, preparation, handles[0], assay, handles[1],
            tuple(sorted((locator for _, locator, _ in products), key=lambda row: row.record.object_id)),
            read.require_current,
            read.require_access if type(read) is ConfiguredE3OriginalProducts else read.require_current)
        read.require_current()


@dataclass(frozen=True, slots=True)
class MatrixProgrammeRevisionRead:
    nomination_locator: object
    frozen_locator: object
    development: object
    nomination: object
    frozen: object
    decision: object


def programme_revision_products(context):
    read = programme_revision_read(context)
    return read.nomination_locator, read.frozen_locator, read.decision


def programme_revision_read(context):
    """Read both original DEV revision producers, keeping adverse decisions."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_records import SelectedE4DevelopmentProduct
    from empirical_lawhood.api.matrix_researcher_programme_prepared_lineage import retained_development_products
    nomination, frozen = retained_development_products(context, 'e4.revision',
        (methods.SelectedE4RevisionNomination, methods.SelectedE4FrozenRevision),
        locator_type=SelectedE4DevelopmentProduct)
    from empirical_lawhood.api.selected_e4_native_runtime import development_products
    from empirical_lawhood.api.recursive_operations import operation_catalog
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_programme import SelectedE4PublicRevisionDecision
    (development, selected), (original, freeze) = development_products(context.writer,
        ((nomination, 'revision-fit'), (frozen, 'revision-freeze')), operation_catalog()[2])
    if development != original:
        raise PermissionError('programme revision combines different actual original DEV populations')
    decision = SelectedE4PublicRevisionDecision.from_products(development, selected, freeze,
        record_id='decision.' + context.namespace + '.revision')
    return MatrixProgrammeRevisionRead(nomination, frozen, development, selected, freeze, decision)


def programme_downstream_choice(context):
    """Project complete original CONF science, retaining an actual absent choice."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_methods as methods
    from empirical_lawhood.api.matrix_researcher_programme_lineage import _issued_e4_record
    record, _ = _issued_e4_record(context, 'e4.confirmation', methods.SelectedE4DownstreamNomination.SCHEMA)
    scope = context.method_inputs('e4.confirmation').plan.tail.confirmation
    if (type(record) is not methods.SelectedE4DownstreamNomination or scope is None
            or record.specification != scope.specification.identity
            or record.rule_product != scope.specification.nomination_rule
            or record.frozen_product != scope.revision.decision
            or record.calibration_product != scope.calibration):
        raise PermissionError('programme downstream decision substitutes its actual original CONF scope or frozen products')
    record.__post_init__()
    return 'UNSELECTED' if record.selected is None else record.selected
