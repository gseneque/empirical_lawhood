# SPDX-License-Identifier: MPL-2.0
"""Cold prepared-source recipe preserving explicit original E3 custody."""
from dataclasses import replace

from empirical_lawhood.domains.matrix.matrix_prepared_source_assembly import CONTINUED_PROTOCOL_ID, MatrixPreparedRetainedE3AssemblyRequest, DEVELOPMENT_TYPES
from empirical_lawhood.api.domain_composition.matrix_prepared_source_assembly.experiment_binding import EXPERIMENT_RUNTIME_BINDING as ORIGINAL

EXPERIMENT_RUNTIME_BINDING = replace(ORIGINAL, protocol_id=CONTINUED_PROTOCOL_ID,
    development_bootstrap_record_types=(MatrixPreparedRetainedE3AssemblyRequest, *DEVELOPMENT_TYPES))
