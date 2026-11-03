"""The already exposed twelve-query R1 fixture, under successor identities.

No historical receipt, issued authority or scientific status is recreated.
The exact supplied float values and conversion are retained from the source
configuration; the calibration summaries are three observations and assumed
KO/derived kcat,O do not create a fourth independent kinetic observation.

SPDX-License-Identifier: MPL-2.0
"""

from decimal import Decimal

from .core import compatible_kinetics, reference_rates
from .records import AssayCase, AssayConfig, AssayQuery, PREFIX

LEGACY_SOURCE_COMMIT = "ec4f7ad3c81ffb2d9734babd866f933c794398cc"
LEGACY_EXECUTION_COMMIT = "5db3d13fc0255131f780da650519c4b405908be4"
LEGACY_CONFIG_PATH = "src/icf_yolo/adapters/composition/rubisco_assay_v1/configuration.py"
LEGACY_RESULT_PATH = "docs/programmes/rubisco-el/results/r02s-conditional-assay-r1-results-2026-09-23.md"
CURATION_SHA256 = "56764b44d0397e650c88c16b0e0de556860a54ee8eb8f7cf495f93addc5f87ce"


def historical_r1_config(*, plan_sha256: str) -> AssayConfig:
    """Build an exposed conformance fixture, without historical-byte relabeling."""
    queries = tuple(AssayQuery(Decimal(c), Decimal(o), Decimal(1))
                    for c, o in ((10, 50), (200, 50), (10, 1000), (200, 1000)))
    cases = []
    for name, kcat, kc_air, specificity, row in (
        ("chi11", 6.0833899999999996, 85.582329999999999, 63.519590000000001, 16),
        ("wt", 3.7838500000000002, 71.718530000000001, 59.483759999999997, 5),
    ):
        parameters = compatible_kinetics(kcat_c=kcat, kc_air=kc_air, specificity=specificity,
                                         air_o2_um=250.0, ko=750.0)
        rates = reference_rates(parameters, queries[0].native())
        cases.append(AssayCase(f"{PREFIX}.conditional-rs-{name}", Decimal(str(parameters.kcat_c)),
                               Decimal(str(parameters.kc)), Decimal(str(parameters.kcat_o)),
                               Decimal(str(parameters.ko)),
                               tuple(sorted(f"zhou2023.fig3.summary.{col}{row}" for col in ("m", "x", "ai"))),
                               queries[0], (Decimal(str(rates[0])), Decimal(str(rates[1])))))
    return AssayConfig(f"{PREFIX}.r1-exposed.source-config", tuple(cases), CURATION_SHA256,
                       plan_sha256, queries, Decimal(250), Decimal(750))
