# SPDX-License-Identifier: MPL-2.0
"""Disclosed declaration/callback and exact-evidence codec fixture for the starter."""

from empirical_lawhood.methods.mass_balance_starter.bindings import operation_declarations
from empirical_lawhood.methods.mass_balance_starter.examples import example_evidence
from empirical_lawhood.methods.mass_balance_starter.extension import EXTENSION as _extension_owner_1
EXPERIMENT_PROTOCOL_DECLARATIONS = _extension_owner_1.protocols
from empirical_lawhood.methods.mass_balance_starter.records import NAMESPACE, PREFIX, MassEvidence
from empirical_lawhood.api.domain_composition.mass_balance_starter.experiment_binding import EXPERIMENT_RUNTIME_BINDING
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceCase, ConformanceProfile, ExtensionConformanceSelection

original = example_evidence("positive")
CONFORMANCE_SELECTION = ExtensionConformanceSelection(
    namespace=NAMESPACE, schema_prefix=PREFIX + "/", operations=operation_declarations(),
    protocols=EXPERIMENT_PROTOCOL_DECLARATIONS, bindings=(EXPERIMENT_RUNTIME_BINDING,),
    profile=ConformanceProfile.ORDINARY_DEVELOPMENT,
    cases=(ConformanceCase(NAMESPACE + ".exact-evidence", ConformanceCall.CODEC_ROUNDTRIP,
                           {"record": original, "codec": MassEvidence}, original),),
)
