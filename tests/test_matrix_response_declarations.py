# SPDX-License-Identifier: MPL-2.0
"""Current declaration identities and obsolete retained-source withdrawal."""



from empirical_lawhood.adapters.methods.matrix_factor_response.extension_bundle import (
    OPERATION_DECLARATIONS,
)
from empirical_lawhood.adapters.methods.matrix_factor_response.executable_binding import (
    EXECUTABLE_BINDING_FACTORIES,
)

# Exact pre-migration implementation digests from the explicitly preserved
# handwritten metadata; these labels pin operations, not scientific authority.
EXPECTED_IMPLEMENTATIONS = {
    "matrix-response-error-development-pooled-v1.forecast": "fd746aeff60468db84784e2cf6d538f721b685ddccd4005b077c536695b5f117",
    "matrix-response-error-development-v2.forecast": "8684896fc54f1ef2bcd4a8ff35108e125d20db418f99f928fc515eb2b249f256",
    "matrix-response-error-pooled-v1.forecast": "68dbe71b0a37b07049ec23bca43cd2f35a4d7735138ba61af874cfe9d2534304",
    "matrix-response-error-v2.forecast": "694fe6dec2ae09ff215a9914a76d527c9c4c607e8b218716e1f1e82b1d5bd703"
}


def test_current_response_declarations_preserve_surviving_implementation_identities():
    manifests = {row.capability_key: row.manifest() for row in OPERATION_DECLARATIONS}
    assert len(manifests) == len(OPERATION_DECLARATIONS)
    assert {
        key: manifests[key].implementation_sha256 for key in EXPECTED_IMPLEMENTATIONS
    } == EXPECTED_IMPLEMENTATIONS
    factories = {
        factory.manifest.capability_key: factory
        for factory in EXECUTABLE_BINDING_FACTORIES
    }
    assert set(factories) == set(manifests)
    for declaration in OPERATION_DECLARATIONS:
        factory = factories[declaration.capability_key]
        assert factory.manifest == declaration.manifest()
        assert factory.registration == declaration.registration()








def test_retired_scalar_retained_source_operations_are_absent_from_current_declarations_and_factories():
    retired_prefixes = ("matrix-factor-response.", "matrix-factor-response-development.",
        "matrix-factor-response-development-refinement.", "matrix-factor-response-refinement.",
        "matrix-factor-response-refined.", "matrix-factor-response-compact-development.",
        "matrix-factor-response-batch-development-v2.", "matrix-factor-response-chunked-development-v1.",
        "matrix-factor-response-chunked-development-refinement-v1.", "matrix-response-e3-chunked-development-v1.")
    keys = tuple(value.capability_key for value in OPERATION_DECLARATIONS)
    assert keys and not any(key.startswith(retired_prefixes) for key in keys)
    assert not any(value.manifest.capability_key.startswith(retired_prefixes) for value in EXECUTABLE_BINDING_FACTORIES)
