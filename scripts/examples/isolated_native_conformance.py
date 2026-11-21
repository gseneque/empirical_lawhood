# SPDX-License-Identifier: MPL-2.0
"""Disclosed declarations and codec checks, separate from actual worker entry."""

from empirical_lawhood.adapters.isolated_native_starter.bindings import operation_declaration
from empirical_lawhood.adapters.isolated_native_starter.extension import EXTENSION as _extension_owner_1
EXPERIMENT_PROTOCOL_DECLARATIONS = _extension_owner_1.protocols
from empirical_lawhood.adapters.isolated_native_starter.records import NAMESPACE, PREFIX, SquareInput
from empirical_lawhood.api.domain_composition.isolated_native_starter.experiment_binding import EXPERIMENT_RUNTIME_BINDING
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.storage.contracts.artifacts import ExternalRootContract
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceCase, ConformanceProfile, ExtensionConformanceSelection

original = SquareInput("exposed.isolated-starter.integer-sequence", 64)
CONFORMANCE_SELECTION = ExtensionConformanceSelection(
    namespace=NAMESPACE, schema_prefix=PREFIX + "/", operations=(operation_declaration(),),
    protocols=EXPERIMENT_PROTOCOL_DECLARATIONS, bindings=(EXPERIMENT_RUNTIME_BINDING,),
    imported_record_types=(ExternalRootContract, NumericalProducingProvenance), profile=ConformanceProfile.ISOLATED_NATIVE_CONTRACTS,
    cases=(ConformanceCase(NAMESPACE + ".exact-input", ConformanceCall.CODEC_ROUNDTRIP,
        {"record": original, "codec": SquareInput}, original),),
)
