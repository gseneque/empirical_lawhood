# SPDX-License-Identifier: MPL-2.0
"""Current E1/E2/TRAIN/E3 input projection, without allocation or acquisition."""
from hashlib import sha256

from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest


def project_initial_phase(context, phase):
    operations = context.plan.specification.operations
    namespace = context.namespace
    if phase == 'e1':
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_assembly import MatrixProgrammeE1AssemblySpecification
        selection = operations.e1
        specification = MatrixProgrammeE1AssemblySpecification('assembly.' + namespace + '.e1', selection.identity,
            context.plan.specification.input_commitments)
        return context.derive(phase, specification, {'selection': selection}, output_name='sources.json')
    if phase == 'e2':
        from empirical_lawhood.adapters.methods.matrix_researcher_programme.e2_assembly import MatrixProgrammeE2AssemblySpecification
        request = operations.e2
        specification = MatrixProgrammeE2AssemblySpecification('assembly.' + namespace + '.e2', request.identity,
            context.plan.specification.input_commitments)
        return context.derive(phase, specification, {'request': request})
    if phase == 'train':
        from empirical_lawhood.adapters.methods.matrix_factor_response.native_training_assembly import NativeTrainingAssemblySpecification
        request = operations.training
        specification = NativeTrainingAssemblySpecification('assembly.' + namespace + '.train', namespace,
            context.design.e3.identity, request.identity, context.plan.specification.input_commitments)
        return context.derive(phase, specification, {'request': request})
    if phase == 'e3':
        if context.retained_e3:
            from .configured_e3_retained_assembly import project_retained_e3
            return project_retained_e3(context)
        from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_assembly import (
            ConfiguredProtectedE3AssemblyRequest, ConfiguredProtectedE3AssemblySpecification,
        )
        actual = operations.e3
        artifact = context.design.training_protocol.full_factor_rule.scalar_closure.normalization_owner
        publication, = (publication for selected, publication in context.commitments.support_files if selected == artifact)
        with context.writer.verification_scope() as reading:
            manifest = reading.read_manifest(publication.materialization.relative_path)
            reading.verify_manifest(manifest)
            if (manifest.logical, manifest.materialization) != (publication.logical, publication.materialization):
                raise PermissionError('programme E3 changes C\'s actual normalization publication')
            raw = read_bounded_bytes(reading.root.resolve(publication.materialization.relative_path, for_write=False),
                maximum_bytes=artifact.size_bytes)
            if (len(raw), sha256(raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
                raise PermissionError('programme E3 changes the actual original normalization bytes')
            relative = (context.metadata_directory(phase) / 'original-inputs/normalization.py').relative_to(
                context.writer.root.contract.canonical_path).as_posix()
            copied = context.writer.write(ArtifactWriteRequest(artifact.artifact_id, relative, artifact.payload_schema,
                ArtifactProfile.RAW_SOURCE_BYTES, artifact.media_type, namespace + '.programme',
                context.metadata_directory(phase).relative_to(context.writer.root.contract.canonical_path).as_posix(), raw,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
            if copied.logical.content_sha256 != artifact.sha256:
                raise PermissionError('programme E3 normalization copy changes original custody')
            file = ExperimentFileInputBinding('normalization', artifact, '1.0.0', 'normalization.py', artifact.size_bytes)
            train_sources = context.writer.root.resolve(context.binding('train').sources.relative_path, for_write=False)
            request = ConfiguredProtectedE3AssemblyRequest('request.' + namespace + '.e3', namespace,
                context.design.training_protocol.identity,
                train_sources.parent.relative_to(context.writer.root.contract.canonical_path).as_posix(),
                context.native_training_locator(), actual.resources, actual.authority_policy,
                actual.computability_envelope, actual.computability_evidence, actual.operator_id,
                'export.' + namespace + '.train',
                (context.metadata_directory('train') / 'bank-export').relative_to(
                    context.writer.root.contract.canonical_path).as_posix(), file)
            specification = ConfiguredProtectedE3AssemblySpecification('assembly.' + namespace + '.e3', request.identity)
            records = {'request': request, 'scientific-protocol': context.design.training_protocol}
            from empirical_lawhood.adapters.methods.matrix_researcher_programme.retained_training_continuation import (
                CONTINUATION_FILENAME, MatrixProgrammeRetainedTrainingContinuation,
            )
            retained = tuple(value for value in context.continuation_records
                if type(value) is MatrixProgrammeRetainedTrainingContinuation)
            if retained:
                from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammePublishedInput
                from empirical_lawhood.api.selected_e4_bank_recipe import _publication_from_manifest
                record, = retained
                relative = (context.directory / CONTINUATION_FILENAME).relative_to(
                    context.writer.root.contract.canonical_path).as_posix()
                records['retained-training-continuation'] = MatrixProgrammePublishedInput(record.identity,
                    _publication_from_manifest(context.writer, context.writer.read_manifest(relative)))
                records['native-training-export-adoption'] = record.retained_training.export_adoption
            return context.derive(phase, specification, records)
    raise ValueError('unsupported current initial Matrix phase')
