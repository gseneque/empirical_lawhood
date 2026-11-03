# SPDX-License-Identifier: MPL-2.0
"""Current type projections for explicitly unwritten zero-digest example pins.

No actual publication, scientific record body or nonzero identity is migrated.
Runtime decoders continue to require the exact original record edition.
"""
import json

from empirical_lawhood.kernel.serialization import canonical_json_document_bytes


def example_input_bytes(path):
    from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as protected
    from empirical_lawhood.adapters.methods.matrix_factor_response import native_training_records as native
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_specification import ConfiguredProtectedE3Specification
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_package import ConfiguredMatrixSelectedFrozenPackage
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.configured_selected_public import ConfiguredMatrixSelectedPublicPackage
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import MatrixProgrammeInputCommitments
    kinds = (ConfiguredProtectedE3Specification, ConfiguredMatrixSelectedFrozenPackage,
        ConfiguredMatrixSelectedPublicPackage, protected.ConfiguredProtectedE3ModelSet,
        protected.ConfiguredProtectedE3FrozenProducts, protected.ConfiguredProtectedE3Forecast,
        protected.ConfiguredProtectedE3Calibration, protected.ConfiguredProtectedE3Assessment,
        native.NativeTrainingFeatureBank, native.NativeTrainingOutcomeBank, MatrixProgrammeInputCommitments)
    editions = {kind.SCHEMA: kind.VERSION for kind in kinds}
    document = json.loads(path.read_bytes())
    def visit(value):
        if type(value) is list:
            for item in value:
                visit(item)
        elif type(value) is dict:
            if value.get('schema') == 'empirical-lawhood/kernel/object-identity':
                body = value['value']
                if body['object_schema'] in editions and body['object_fingerprint'] == '0' * 64:
                    if not any(marker in body['object_id'] for marker in ('unwritten', 'replace-with-original')):
                        raise ValueError('example generator cannot revise an undeclared original identity')
                    body['object_version'] = editions[body['object_schema']]
            for item in value.values():
                visit(item)
    visit(document)
    return canonical_json_document_bytes(document)
